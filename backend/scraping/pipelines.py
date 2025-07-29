# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from scraping.items import PropertyItem, UrlItem
import re
import psycopg2
import sqlite3
import csv
import os
import logging
from scrapy.exceptions import DropItem
from datetime import datetime, date

logger = logging.getLogger(__name__)


class PropertyItemPipeline:
    def process_item(self, item, spider):
        # Verifica si el item es una instancia de PropertyItem
        if isinstance(item, PropertyItem):
            # Aquí puedes añadir las modificaciones que desees hacer al item.
            # Por ejemplo, puedes limpiar los datos, calcular nuevos valores, etc.

            # Ejemplo: Convertir el precio a un formato numérico
            # p_id is already an integer from the spider, no conversion needed

            item['nombre'] = self.trim_name(item['nombre'])

            # fecha_crawl is already set in spider with current timestamp

            item['precio'] = self.convert_price_to_number(item['precio'])

            item['metros'] = self.convert_meters_to_number(item['metros'])

            item['habitaciones'] = self.convert_rooms_to_number(item['habitaciones'])

            item['planta'] = self.convert_floor_to_number(item['planta'])

            # ascensor is already set in spider based on item-detail extraction

            item['poblacion'] = self.extract_city(item['poblacion'])

            item['descripcion'] = self.smooth_text(item['descripcion'])

            item['estatus'] = self.get_status(item['descripcion'])
            

        return item  # Devuelve el item modificado
    
    def convert_to_p_id(self, url):
        try:
            p_id = url.split('/')[-2]
            return int(p_id)
        except:
            return
        
    def trim_name(self, name):
        if name is None:
            return "Propiedad sin título"
        if "en venta en " in name:
            nombre = name.capitalize().split("en venta en ", 1)[-1]
        else:
            nombre = name.capitalize()
        # Capitalizar el nombre
        nombre = nombre.capitalize()
        return nombre
        
    def convert_str_to_date(self, date_str):
        date_str = date_str.replace('Anuncio actualizado el ', '')
        year = datetime.now().year
        full_date_str = f"{date_str} {year}"

        month_translation = {
            "enero": "January",
            "febrero": "February",
            "marzo": "March",
            "abril": "April",
            "mayo": "May",
            "junio": "June",
            "julio": "July",
            "agosto": "August",
            "septiembre": "September",
            "octubre": "October",
            "noviembre": "November",
            "diciembre": "December"
        }

        for spanish_month, english_month in month_translation.items():
            if spanish_month in full_date_str.lower():
                full_date_str = full_date_str.lower().replace(spanish_month, english_month)
                break

        # Convertir el string a objeto datetime
        try:
            date_obj = datetime.strptime(full_date_str, "%d de %B %Y")
        except ValueError as e:
            print(f"Error converting date: {e}")

        # Convertir el objeto datetime a formato PostgreSQL
        postgres_date = date_obj.strftime("%Y-%m-%d")
        return postgres_date

    def convert_price_to_number(self, price_str):
        if price_str is None:
            return None
        # Ejemplo: convertir una cadena de precio en un número
        # Elimina símbolos de moneda y comas, luego convierte a float
        price_str = price_str.replace('$', '').replace('.', '').strip()
        try:
            return int(price_str)
        except ValueError:
            return None
        
    def convert_meters_to_number(self, meters_str):
        if meters_str is None or meters_str == "":
            return None
        meters_str = meters_str.replace('\n', '').replace(' m²', '')
        try:
            return int(meters_str)
        except ValueError:
            return None
        
    def convert_rooms_to_number(self, rooms_str):
        if rooms_str is None or rooms_str == "":
            return None
        rooms_str = rooms_str.replace('\n', '').replace('hab.', '').strip()
        try:
            return int(rooms_str)
        except ValueError:
            return None
        
    def convert_floor_to_number(self, floor_str):
        if floor_str is None:
            return 0
        floor_match = re.search(r'\d+', floor_str)

        if floor_match:
            floor_num = int(floor_match.group())
            return floor_num
        else:
            return 0
        
    def convert_lift_to_number(self, lift_str, desc_str):
        if lift_str and 'con ascensor' in lift_str:
            return 1
        elif lift_str and 'sin ascensor' in lift_str:
            return 0
        elif desc_str and 'con ascensor' in desc_str:
            return 1
        elif desc_str and 'sin ascensor' in desc_str:
            return 0
        else:
            return 2
        
    def extract_city(self, city_str):
        if city_str is None or city_str.strip() == "":
            return "Ubicación no especificada"
        # City is now extracted directly from title, just clean it up
        city = city_str.strip()
        return city

    def smooth_text(self, text):
        if text is None:
            return ""
        text = text.replace('\n', '')
        # Reemplazar múltiples espacios con uno solo y eliminar saltos de línea
        text = re.sub(r'\s+', ' ', text)
        
        # Eliminar espacios al principio y al final
        text = text.strip()
        
        return text
    
    def get_status(self, description):
        if description is None:
            return ""
            
        ocupado_list = ["ocupado por persona", "inmueble sin posesi", "ocupada por"]
        subasta_list = ["subasta"]
        arrendado_list = ["arrendado a tercero"]

        if any(ocupado in description.lower() for ocupado in ocupado_list):
            status = "Ocupado"
        elif any(subasta in description.lower() for subasta in subasta_list):
            status = 'Subasta'
        elif any(arrendado in description.lower() for arrendado in arrendado_list):
            status = 'Arrendado'
        else:
            status = ""
        
        return status
    
class PostgresPipeline:
    def open_spider(self, spider):
        #Este método se ejecuta cuando el spider se abre.
        #self.connection = psycopg2.connect(DATABASE_URL = os.getenv('DATABASE_URL'))
        self.connection = psycopg2.connect(
            host=spider.settings.get('POSTGRES_HOST'),
            port=spider.settings.get('POSTGRES_PORT'),
            dbname=spider.settings.get('POSTGRES_DB'),
            user=spider.settings.get('POSTGRES_USER'),
            password=spider.settings.get('POSTGRES_PASSWORD')
        )
        self.cursor = self.connection.cursor()

        # Tables are now created via postgres init scripts
        # Just ensure fecha_crawl column exists for migration
        self.cursor.execute('''
            ALTER TABLE propiedades 
            ADD COLUMN IF NOT EXISTS fecha_crawl TIMESTAMP
        ''')
        self.connection.commit()

    def close_spider(self, spider):
        # Cerrar la conexión cuando el spider se cierra
        self.cursor.close()
        self.connection.close()

    def process_item(self, item, spider):
        # Handle UrlItem for municipios spider
        if isinstance(item, UrlItem):
            try:
                url = item['url']
                spider_name = spider.name
                
                # Insert URL into municipios table (ignore if already exists)
                self.cursor.execute("""
                    INSERT INTO municipios (url, spider_name) 
                    VALUES (%s, %s) 
                    ON CONFLICT (url) DO NOTHING
                """, (url, spider_name))
                
                self.connection.commit()
                spider.logger.debug(f"URL saved to municipios table: {url}")
                
            except psycopg2.Error as e:
                spider.logger.error(f"Database error saving URL: {e}")
                self.connection.rollback()
                raise DropItem(f"Database error: {e}")
            
            return item
        
        # Handle PropertyItem for property spiders
        elif isinstance(item, PropertyItem):
            # p_id is already an integer from the spider
            try:
                p_id = int(item['p_id'])
            except (ValueError, TypeError):
                spider.logger.error(f"Could not extract valid p_id from: {item['p_id']}")
                raise DropItem(f"Invalid p_id: {item['p_id']}")
            
            print(f"p_id value being processed: {p_id}")

            # Verificar condiciones para excluir
            planta = item.get('planta')
            ascensor = item.get('ascensor')

            # Condición para excluir la propiedad (fix type checking)
            try:
                planta_num = int(planta) if planta and str(planta).strip() else 0
                ascensor_num = int(ascensor) if ascensor is not None else 0
                
                if planta_num > 3 and ascensor_num == 0:
                    print(f"Property excluded: {p_id}, Planta: {planta_num}, Ascensor: {ascensor_num}")
                    raise DropItem(f"Property excluded due to floor/elevator criteria: {p_id}")
            except (ValueError, TypeError):
                # If we can't convert to int, don't exclude based on this criteria
                print(f"Could not parse planta/ascensor for {p_id}: planta={planta}, ascensor={ascensor}")
                
            try:
                # Verificar si el item ya existe en la base de datos
                self.cursor.execute("SELECT 1 FROM propiedades WHERE p_id = %s", (p_id,))
                result = self.cursor.fetchone()

                if result:
                    # Si ya existe el registro, actualizamos el contenido
                    print(f"Item already exists. Updating item: {p_id}")

                    self.cursor.execute('''
                        UPDATE propiedades
                        SET nombre = %s,
                            fecha_updated = %s,
                            fecha_crawl = %s,
                            precio = %s,
                            metros = %s,
                            habitaciones = %s,
                            planta = %s,
                            ascensor = %s,
                            poblacion = %s,
                            url = %s,
                            descripcion = %s,
                            estatus = %s
                        WHERE p_id = %s
                    ''', (
                        item.get('nombre'),
                        item.get('fecha_crawl'),  # Use fecha_crawl for fecha_updated to maintain compatibility
                        item.get('fecha_crawl'),
                        item.get('precio'),
                        item.get('metros'),
                        item.get('habitaciones'),
                        item.get('planta'),
                        item.get('ascensor'),
                        item.get('poblacion'),
                        item.get('url'),
                        item.get('descripcion'),
                        item.get('estatus'),
                        p_id
                    ))

                    # Confirmar cambios después de la actualización
                    self.connection.commit()
                    print(f"Item updated successfully: {p_id}")

                else:
                    # Insert item into database
                    self.cursor.execute("""
                        INSERT INTO propiedades (p_id, nombre, fecha_updated, fecha_crawl, precio, metros, habitaciones, planta, ascensor, poblacion, url, descripcion, estatus)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        p_id,
                        item.get('nombre'),
                        item.get('fecha_crawl'),  # Use fecha_crawl for fecha_updated to maintain compatibility
                        item.get('fecha_crawl'),
                        item.get('precio'),
                        item.get('metros'),
                        item.get('habitaciones'),
                        item.get('planta'),
                        item.get('ascensor'),
                        item.get('poblacion'),
                        item.get('url'),
                        item.get('descripcion'),
                        item.get('estatus')
                    ))

                    # Confirmar cambios en la base de datos
                    self.connection.commit()
                    print(f"Item inserted successfully: {p_id}")

            except psycopg2.Error as e:
                print(f"Database error: {e}")
                self.connection.rollback()
                raise DropItem(f"Database error: {e}")
            
            except Exception as e:
                print(f"Unexpected error: {e}")
                raise DropItem(f"Unexpected error: {e}")

        return item

class MunicipiosPipeline:
    """
    Dedicated pipeline for municipios spider - saves URLs only to municipios table and CSV
    """
    
    def open_spider(self, spider):
        if spider.name != 'municipios':
            return
            
        # Database connection for municipios
        self.connection = psycopg2.connect(
            host=spider.settings.get('POSTGRES_HOST'),
            port=spider.settings.get('POSTGRES_PORT'),
            dbname=spider.settings.get('POSTGRES_DB'),
            user=spider.settings.get('POSTGRES_USER'),
            password=spider.settings.get('POSTGRES_PASSWORD')
        )
        self.cursor = self.connection.cursor()
        spider.logger.info("MunicipiosPipeline: Database connection established")

    def close_spider(self, spider):
        if spider.name != 'municipios':
            return
            
        if hasattr(self, 'cursor'):
            self.cursor.close()
        if hasattr(self, 'connection'):
            self.connection.close()
        spider.logger.info("MunicipiosPipeline: Database connection closed")

    def process_item(self, item, spider):
        # Only process items from municipios spider
        if spider.name != 'municipios':
            return item
            
        # Only process UrlItem instances
        if not isinstance(item, UrlItem):
            return item
            
        try:
            url = item['url']
            spider_name = spider.name
            
            # Insert URL into municipios table only (ignore if already exists)
            self.cursor.execute("""
                INSERT INTO municipios (url, spider_name) 
                VALUES (%s, %s) 
                ON CONFLICT (url) DO NOTHING
            """, (url, spider_name))
            
            self.connection.commit()
            spider.logger.debug(f"MunicipiosPipeline: URL saved to municipios table: {url}")
            
        except psycopg2.Error as e:
            spider.logger.error(f"MunicipiosPipeline: Database error saving URL: {e}")
            self.connection.rollback()
            raise DropItem(f"Database error: {e}")
        
        return item

class UrlToCSVPipeline:
    """
    Pipeline para exportar URLs a un archivo CSV durante la ejecución
    para no perder datos en caso de interrupción.
    """
    
    def __init__(self):
        # Create output directory if it doesn't exist
        os.makedirs('./scraping/output', exist_ok=True)
        self.csv_file = './scraping/output/municipios.csv'
        self.file = None
        self.writer = None
        self.urls_processed = set()

    def open_spider(self, spider):
        # Only process municipios spider
        if spider.name != 'municipios':
            return
            
        # Crear el archivo CSV si no existe
        file_exists = os.path.isfile(self.csv_file)
        
        # Si el archivo ya existe, cargar las URLs ya procesadas
        if file_exists:
            try:
                with open(self.csv_file, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if row and len(row) > 0:
                            self.urls_processed.add(row[0])
                logger.info(f"Cargadas {len(self.urls_processed)-1} URLs ya procesadas")
            except Exception as e:
                logger.error(f"Error al cargar URLs existentes: {str(e)}")
        
        # Abrir el archivo en modo append
        self.file = open(self.csv_file, 'a', newline='', encoding='utf-8')
        self.writer = csv.writer(self.file)
        
        # Si es un archivo nuevo, escribir la cabecera
        if not file_exists:
            self.writer.writerow(['url'])
    
    def close_spider(self, spider):
        # Only process municipios spider
        if spider.name != 'municipios':
            return
            
        if self.file:
            self.file.close()
        logger.info(f"Total de URLs procesadas: {len(self.urls_processed)}")
    
    def process_item(self, item, spider):
        # Only process municipios spider and UrlItem instances
        if spider.name != 'municipios' or not isinstance(item, UrlItem):
            return item
            
        url = item['url']
        
        # Si la URL no ha sido procesada aún, escribirla en el archivo
        if url not in self.urls_processed:
            self.writer.writerow([url])
            self.file.flush()  # Asegurar que se escribe inmediatamente
            self.urls_processed.add(url)
            logger.debug(f"URL guardada: {url}")
        
        return item
    
class SQLitePipeline:

    def open_spider(self, spider):
        # Create backend directory if it doesn't exist
        os.makedirs('./scraping/backend', exist_ok=True)
        self.conn = sqlite3.connect("./scraping/backend/inmuebles.db")
        self.cursor = self.conn.cursor()
        
        # Create tables if they don't exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS municipios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS propiedades (
                p_id INTEGER PRIMARY KEY,
                nombre TEXT,
                fecha_crawl TIMESTAMP,
                precio INTEGER,
                metros INTEGER,
                habitaciones INTEGER,
                planta INTEGER,
                ascensor INTEGER,
                poblacion TEXT,
                url TEXT,
                descripcion TEXT
            )
        ''')
        self.conn.commit()

    def close_spider(self, spider):
        self.conn.commit()
        self.conn.close()

    def process_item(self, item, spider):
        if isinstance(item, UrlItem) and spider.name == "municipios":
            try:
                self.cursor.execute("""
                    INSERT OR IGNORE INTO municipios (url) VALUES (?)
                """, (item['url'],))
            except sqlite3.Error as e:
                logger.error(f"SQLite error inserting URL: {e}")
                
        elif isinstance(item, PropertyItem):
            try:
                self.cursor.execute("""
                    INSERT OR REPLACE INTO propiedades (
                        p_id, nombre, fecha_crawl, precio, metros, habitaciones,
                        planta, ascensor, poblacion, url, descripcion
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.get('p_id'),
                    item.get('nombre'),
                    item.get('fecha_crawl'),
                    item.get('precio'),
                    item.get('metros'),
                    item.get('habitaciones'),
                    item.get('planta'),
                    item.get('ascensor'),
                    item.get('poblacion'),
                    item.get('url'),
                    item.get('descripcion'),
                ))
            except sqlite3.Error as e:
                logger.error(f"SQLite error inserting property: {e}")

        return item