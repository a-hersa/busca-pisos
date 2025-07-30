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
        # Enable browser rendering to avoid detection
        self.browser = "&browser=false"
        # self.proxy_country = "&proxy_country=ES"
        # Add stealth mode and other anti-detection features (remove invalid block_resources)
        # self.extra_params = "&return_page_source=true&stealth_mode=true"

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
        
        # Try different configurations if detection occurs
        configs = [
            # Config 1: Browser mode with stealth + Spain
            "&browser=true&proxy_country=ES&return_page_source=true&stealth_mode=true",
            # Config 2: Browser mode without stealth + Spain
            "&browser=true&proxy_country=ES&return_page_source=true",
            # Config 3: Browser + stealth with different country
            "&browser=true&proxy_country=FR&return_page_source=true&stealth_mode=true",
            # Config 4: Basic browser mode with UK proxy
            "&browser=true&proxy_country=GB&return_page_source=true",
            # Config 5: No browser mode (last resort)
            "&browser=false&proxy_country=ES&return_page_source=true"
        ]
        
        # Codifica la URL original
        encoded_url = quote(request.url, safe='')

        for i, config in enumerate(configs):
            conn = http.client.HTTPSConnection(self.base_url)
            
            try:
                # Construye la nueva URL con el proxy y otros parámetros
                api_request_path = f"/v2/general?url={encoded_url}&x-api-key={self.api_key}{config}"

                if i > 0:  # Log retry attempts
                    spider.logger.info(f"Retrying with config {i+1}: {request.url}")
                spider.logger.info(f"Using ScrapingAnt config {i+1}: {config}")
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
                elif res.status == 423:  # Locked - try next config
                    spider.logger.warning(f"ScrapingAnt config {i+1} detected (423 Locked), trying next config")
                    res.read()  # consume response body
                    continue
                elif res.status == 409:  # Concurrency limit reached - wait and retry once
                    error_body = res.read()
                    spider.logger.warning(f"ScrapingAnt concurrency limit reached (409): {error_body}")
                    if not hasattr(request, '_scrapingant_409_retry'):
                        spider.logger.info("Waiting 60 seconds for concurrency limit to reset...")
                        import time
                        time.sleep(60)  # Wait 60 seconds for limit to reset
                        request._scrapingant_409_retry = True  # Mark that we've retried once
                        # Retry the same configuration after waiting
                        continue
                    else:
                        spider.logger.error("ScrapingAnt concurrency limit persists after retry, skipping request")
                        continue  # Try next config if available
                elif res.status == 422:  # Invalid parameters - try next config
                    error_body = res.read()
                    spider.logger.warning(f"ScrapingAnt config {i+1} invalid parameters (422): {error_body}")
                    continue
                elif res.status == 404:  # Site unreachable - try next config
                    error_body = res.read()
                    spider.logger.warning(f"ScrapingAnt config {i+1} site unreachable (404): {error_body}")
                    continue
                else:
                    spider.logger.error(f"ScrapingAnt proxy request failed: {res.status} {res.reason}")
                    error_body = res.read()
                    spider.logger.error(f"Response body: {error_body}")
                    if i == len(configs) - 1:  # Last config failed
                        return None
                    continue
            except Exception as e:
                spider.logger.error(f"Exception in ScrapingAnt middleware: {e}")
                if i == len(configs) - 1:  # Last config failed
                    return None
                continue
            finally:
                # Asegurar que la conexión se cierre
                conn.close()
        
        return None

    def process_exception(self, request, exception, spider):
        # Manejo de excepciones para reintentar la solicitud en caso de error
        spider.logger.error(f"Exception occurred: {exception}")
        return None  # Return None to trigger retry mechanism

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)
