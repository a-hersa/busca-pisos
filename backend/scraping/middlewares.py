import http.client
from urllib.parse import quote
from scrapy import signals
import scrapy
import os
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()


class ScrapingAntProxyMiddleware:
    def __init__(self):
        self.api_key = f'{os.getenv("SCRAPINGANT_API_KEY")}'  # Reemplaza con tu clave API
        self.base_url = "api.scrapingant.com"
        self.browser = "&browser=false"
        self.proxy_country = "&proxy_country=ES"
        self.extra_params = "&return_page_source=true"

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Only process requests to idealista.com through ScrapingAnt
        if 'idealista.com' not in request.url:
            spider.logger.debug(f"Skipping ScrapingAnt for non-idealista URL: {request.url}")
            return None
            
        spider.logger.info(f"Processing request through ScrapingAnt: {request.url}")
        
        # Codifica la URL original
        encoded_url = quote(request.url, safe='')

        # Crea la conexión HTTPS con ScrapingAnt
        conn = http.client.HTTPSConnection(self.base_url)
        
        try:
            # Construye la nueva URL con el proxy y otros parámetros
            api_request_path = f"/v2/general?url={encoded_url}&x-api-key={self.api_key}{self.browser}{self.proxy_country}{self.extra_params}"

            spider.logger.debug(f"ScrapingAnt API request: {api_request_path}")

            # Realiza la solicitud al proxy
            conn.request("GET", api_request_path)
            res = conn.getresponse()
            
            # Si la respuesta es exitosa, reemplazamos el cuerpo de la respuesta en Scrapy
            if res.status == 200:
                response_data = res.read()
                spider.logger.info(f"Successfully received response from ScrapingAnt for {request.url}")
                # Crea una nueva respuesta con los datos obtenidos del proxy
                new_response = scrapy.http.HtmlResponse(
                    url=request.url,
                    body=response_data,
                    encoding='utf-8',
                    request=request
                )
                return new_response
            else:
                spider.logger.error(f"ScrapingAnt proxy request failed: {res.status} {res.reason}")
                spider.logger.error(f"Response body: {res.read()}")
                return None
        except Exception as e:
            spider.logger.error(f"Exception in ScrapingAnt middleware: {e}")
            return None
        finally:
            # Asegurar que la conexión se cierre
            conn.close()

    def process_exception(self, request, exception, spider):
        # Manejo de excepciones para reintentar la solicitud en caso de error
        spider.logger.error(f"Exception occurred: {exception}")
        return None  # Return None to trigger retry mechanism

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)
