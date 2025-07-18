# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from inmobiliario.items import PropertyItem
import re
import psycopg2
from scrapy.exceptions import DropItem
from datetime import datetime


class PropertyItemPipeline:
    def process_item(self, item, spider):
        # Verifica si el item es una instancia de PropertyItem
        if isinstance(item, PropertyItem):
            # Aquí puedes añadir las modificaciones que desees hacer al item.
            # Por ejemplo, puedes limpiar los datos, calcular nuevos valores, etc.

            # Ejemplo: Convertir el precio a un formato numérico
            item['p_id'] = self.convert_to_p_id(item['p_id'])

            item['nombre'] = self.trim_name(item['nombre'])

            item['fecha_new'] = datetime.today().strftime('%Y-%m-%d')
            # item['fecha_new'] = self.convert_str_to_date(item['fecha_new'])
            
            item['fecha_updated'] = datetime.today().strftime('%Y-%m-%d')

            item['precio'] = self.convert_price_to_number(item['precio'])

            item['metros'] = self.convert_meters_to_number(item['metros'])

            item['habitaciones'] = self.convert_rooms_to_number(item['habitaciones'])

            item['planta'] = self.convert_floor_to_number(item['planta'])

            item['ascensor'] = self.convert_lift_to_number(item['ascensor'], item['descripcion'])

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

        # Crear la tabla si no existe
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS propiedades (
                p_id INT PRIMARY KEY,
                nombre VARCHAR(255),
                fecha_new DATE,
                fecha_updated DATE,
                precio INT,
                metros INT,
                habitaciones INT,
                planta INT,
                ascensor INT,
                poblacion VARCHAR(255),
                url VARCHAR(255),
                descripcion VARCHAR(4000),
                estatus VARCHAR(255)            
            )
        ''')
        self.connection.commit()

    def close_spider(self, spider):
        # Cerrar la conexión cuando el spider se cierra
        self.cursor.close()
        self.connection.close()

    def process_item(self, item, spider):
        # Extract p_id from URL and convert to int safely
        try:
            p_id_str = item['p_id'].split('/')[-2] if isinstance(item['p_id'], str) else str(item['p_id'])
            p_id = int(p_id_str)
        except (ValueError, IndexError, AttributeError):
            spider.logger.error(f"Could not extract valid p_id from: {item['p_id']}")
            raise DropItem(f"Invalid p_id: {item['p_id']}")
        
        print(f"p_id value being processed: {p_id}")

        # Verificar condiciones para excluir
        planta = item.get('planta')
        ascensor = item.get('ascensor')

        # Condición para excluir la propiedad
        if planta > 3 and ascensor == 0:
            print(f"Property excluded: {p_id}, Planta: {planta}, Ascensor: {ascensor}")
            return
            
        try:
            # Verificar si el item ya existe en la base de datos
            self.cursor.execute("SELECT 1 FROM propiedades WHERE p_id = %s", (p_id,))
            result = self.cursor.fetchone()
            # fecha_updated = datetime.today().strftime('%Y-%m-%d')  # Fecha actual

            if result:
                # Si ya existe el registro, actualizamos el contenido
                print(f"Item already exists. Updating item: {p_id}")

                self.cursor.execute('''
                    UPDATE propiedades
                    SET nombre = %s,
                        fecha_updated = %s,
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
                    item.get('fecha_updated'),
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
                    INSERT INTO propiedades (p_id, nombre, fecha_new, fecha_updated, precio, metros, habitaciones, planta, ascensor, poblacion, url, descripcion, estatus)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    p_id,
                    item.get('nombre'),
                    item.get('fecha_new'),
                    item.get('fecha_updated'),
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
