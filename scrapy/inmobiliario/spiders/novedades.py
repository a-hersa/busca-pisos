import scrapy
from ..items import PropertyItem


class NovedadesSpider(scrapy.Spider):
    name = "novedades"
    allowed_domains = ["idealista.com", "api.scrapingant.com"]
    
    # Puedes agregar más URLs a esta lista
    start_urls = [
        'https://www.idealista.com/venta-viviendas/premia-de-mar-barcelona/con-precio-hasta_120000,de-dos-dormitorios,de-tres-dormitorios,de-cuatro-cinco-habitaciones-o-mas,ultimas-plantas,plantas-intermedias/',
        'https://www.idealista.com/venta-viviendas/argentona-barcelona/con-precio-hasta_120000,de-dos-dormitorios,de-tres-dormitorios,de-cuatro-cinco-habitaciones-o-mas,publicado_ultimas-48-horas,ultimas-plantas,plantas-intermedias/',
        'https://www.idealista.com/venta-viviendas/sant-pol-de-mar-barcelona/con-precio-hasta_120000,de-dos-dormitorios,de-tres-dormitorios,de-cuatro-cinco-habitaciones-o-mas,publicado_ultimas-48-horas,ultimas-plantas,plantas-intermedias/',
        'https://www.idealista.com/venta-viviendas/canet-de-mar-barcelona/con-precio-hasta_120000,de-dos-dormitorios,de-tres-dormitorios,de-cuatro-cinco-habitaciones-o-mas,publicado_ultimas-48-horas,ultimas-plantas,plantas-intermedias/',
        'https://www.idealista.com/venta-viviendas/caldes-d-estrac-barcelona/con-precio-hasta_120000,de-dos-dormitorios,de-tres-dormitorios,de-cuatro-cinco-habitaciones-o-mas,publicado_ultimas-48-horas,ultimas-plantas,plantas-intermedias/',
        'https://www.idealista.com/venta-viviendas/arenys-de-mar-barcelona/con-precio-hasta_120000,de-dos-dormitorios,de-tres-dormitorios,de-cuatro-cinco-habitaciones-o-mas,publicado_ultimas-48-horas,ultimas-plantas,plantas-intermedias/',
        'https://www.idealista.com/venta-viviendas/mataro-barcelona/con-precio-hasta_120000,de-dos-dormitorios,de-tres-dormitorios,de-cuatro-cinco-habitaciones-o-mas,publicado_ultimas-48-horas,ultimas-plantas,plantas-intermedias/',
        'https://www.idealista.com/venta-viviendas/granollers-barcelona/con-precio-hasta_120000,de-dos-dormitorios,de-tres-dormitorios,de-cuatro-cinco-habitaciones-o-mas,publicado_ultimas-48-horas,ultimas-plantas,plantas-intermedias/'
    ]


    def parse(self, response):
        # Selecciona todos los divs con la clase 'item-info-container'
        containers = response.css('div.item-info-container')
        print(f'number of properties in this page is {len(containers)}')

        for container in containers:
            # Extrae los datos directamente del listado
            propiedad = PropertyItem()
            
            # URL del enlace de la propiedad
            relative_url = container.css('a.item-link::attr(href)').get()
            if relative_url:
                full_url = response.urljoin(relative_url)
                propiedad['p_id'] = full_url
                propiedad['url'] = full_url
            
            # Nombre/título de la propiedad
            raw_title = container.css('a.item-link::text').get()
            
            # Extract location from title and clean title
            if raw_title:
                # Split by comma and take the last part as location
                title_parts = raw_title.split(',')
                if len(title_parts) > 1:
                    propiedad['poblacion'] = title_parts[-1].strip()
                    # Remove location from title (keep all parts except the last one)
                    propiedad['nombre'] = ','.join(title_parts[:-1]).strip()
                else:
                    propiedad['nombre'] = raw_title.strip()
                    propiedad['poblacion'] = ""
            else:
                propiedad['nombre'] = ""
                propiedad['poblacion'] = ""
            
            # Precio
            propiedad['precio'] = container.css('span.item-price::text').get()
            
            # Información adicional (metros, habitaciones, etc.)
            detail_items = container.css('span.item-detail::text').getall()
            propiedad['metros'] = ""
            propiedad['habitaciones'] = ""
            propiedad['planta'] = ""
            
            if detail_items:
                # Buscar metros cuadrados
                for detail in detail_items:
                    if 'm²' in detail:
                        propiedad['metros'] = detail.replace('m²', '').strip()
                    elif 'hab.' in detail:
                        propiedad['habitaciones'] = detail.replace('hab.', '').strip()
                    elif 'planta' in detail.lower():
                        propiedad['planta'] = detail.strip()
            
            # Descripción (si está disponible en el listado)
            propiedad['descripcion'] = container.css('p.item-description::text').get()
            
            # Campos adicionales con valores por defecto
            propiedad['ascensor'] = ""
            propiedad['fecha_new'] = ""
            propiedad['fecha_updated'] = ""
            propiedad['estatus'] = "activo"
            
            yield propiedad

        # Opcional: Si la página tiene paginación, puedes seguir los enlaces a las páginas siguientes
        next_page = response.css('a.icon-arrow-right-after::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse)

