from flask import Flask, send_file, request, render_template, flash
from src.scraper import scraper
from src.calculadora import DatosCalculadora
from src.calculadora import calculadora
import tempfile
from openpyxl import load_workbook
from dotenv import load_dotenv
import psycopg2
import os
from unidecode import unidecode


app=Flask(__name__)
app.secret_key = 'your_secret_key'

# Registra la función para usarla en la plantilla
app.jinja_env.globals.update(calculadora=calculadora)

# DATABASE_URL = os.getenv('DATABASE_URL')

# Configurar la conexión a la base de datos PostgreSQL
def get_db_connection():
    # conn = psycopg2.connect(DATABASE_URL)
    conn = psycopg2.connect(
        host='postgres',
        port='5432',
        dbname='inmobiliario_db',
        user= f'{os.getenv("POSTGRES_USER")}',
        password= f'{os.getenv("POSTGRES_PASSWORD")}'
    )
    return conn

@app.route('/')
def home_page():
    # Obtener el número de página actual desde los parámetros de consulta
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Elementos por página
    offset = (page - 1) * per_page

    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtener los datos paginados incluyendo la columna 'descripcion'
    cursor.execute("""
        SELECT nombre, fecha_updated, precio, metros, poblacion, url, p_id, estatus 
        FROM propiedades 
        WHERE p_id IN (
            SELECT p_id 
            FROM propiedades 
            ORDER BY fecha_updated DESC 
            LIMIT 100
        )
        ORDER BY fecha_updated DESC 
        LIMIT %s OFFSET %s
    """, (per_page, offset))
    propiedades = cursor.fetchall()

    # Obtener el número total de registros
    cursor.execute("SELECT COUNT(*) FROM propiedades")
    total = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    # Calcular el número total de páginas
    total_pages = (total + per_page - 1) // per_page

    # Pasar las propiedades procesadas a la plantilla
    return render_template('index.html', propiedades=propiedades, page=page, total_pages=total_pages, site_key=os.getenv("TURNSTILE_SITE_KEY"))


@app.route('/calculadora', methods=['GET', 'POST'])
def calculadora():
    if request.method == 'POST':
        # Caso: Solicitud POST con URL del scraper
        url = request.form['url']

        # try:
        scrape = scraper(url)
        datos = DatosCalculadora(scrape[0], scrape[1], scrape[2], scrape[3]) # nombre, precio, metros, poblacion
        return render_template('calculadora.html', url=url, datos=datos)
        
        # except Exception as e:
        # #    flash(f"Hubo un problema al procesar la URL: {str(e)}, vuelva a intentarlo más tarde.", "error")
        #     return render_template('calculadora.html', url=url, datos=None)
    
    elif request.method == 'GET':
        # Caso: Solicitud GET con p_id de la base de datos
        p_id = request.args.get('p_id', type=int)
        if p_id is not None:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT nombre, precio, metros, poblacion, url FROM propiedades WHERE p_id = %s", (p_id,))
            propiedad = cursor.fetchone()
            
            conn.close()
            
            if propiedad:
                datos = DatosCalculadora(propiedad[0], propiedad[1], propiedad[2], propiedad[3]) # nombre, precio, metros, poblacion
                return render_template('calculadora.html', url=propiedad[4], datos=datos)
            else:
                return "Propiedad no encontrada", 404
        else:
            return "Parámetro p_id no proporcionado", 400


@app.route('/descargar', methods=['POST'])
def descargar():
    wb = load_workbook('src/plantilla.xlsx')
    ws = wb.active
    ws['D5'] = request.form['nombre']
    ws['D6'] = request.form['url']
    ws['D10'] = int(request.form['p_compra'])
    ws['D11'] = int(request.form['itp'])
    ws['D12'] = int(request.form['reforma'])
    ws['D13'] = int(request.form['notaria'])
    ws['D14'] = int(request.form['registro'])
    ws['D15'] = int(request.form['agencia'])
    ws['D16'] = int(request.form['tasacion'])
    ws['E20'] = int(request.form['ibi'])
    ws['E21'] = int(request.form['basuras'])
    ws['E22'] = int(request.form['comunidad'])
    ws['E23'] = int(request.form['seguros'])
    ws['E24'] = 0
    ws['H5'] = int(request.form['alquiler'])
    ws['H8'] = float(float(request.form['financiado'])/100)
    ws['H11'] = int(request.form['plazo'])
    ws['H12'] = float(float(request.form['intereses_anuales'])/100)
    temp_excel_file = tempfile.NamedTemporaryFile(prefix='calculadora-', suffix='.xlsx', delete=False)
    wb.save(temp_excel_file.name)
    # path = "src/plantilla.xlsx"
    return send_file(temp_excel_file.name, as_attachment=True)


if __name__=='__main__':
    load_dotenv()
    # app.run(host='0.0.0.0',debug=True)
    # app.run(host='0.0.0.0',port=8080)
    app.run(debug = False, host='0.0.0.0', port=5000)