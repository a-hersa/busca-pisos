# -*- coding: utf-8 -*-
import os
import pickle
import shutil
import scrapy
import logging
import re
import glob
from scrapy import signals
from scrapy.signalmanager import dispatcher
from urllib.parse import urlparse, urlunparse, parse_qs
from scraping.items import UrlItem
from scraping.utils import is_target_url, is_no_visit, normalize_url
import random

logger = logging.getLogger(__name__)

class MunicipiosSpider(scrapy.Spider):
    name = 'municipios'
    allowed_domains = ['idealista.com']
    start_urls = ['https://www.idealista.com/venta-viviendas/']
    pending_file = './scraping/crawls/municipios/pending_urls.pkl'
    
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'scraping.middlewares.ScrapingAntProxyMiddleware': 100,
        },
        'ITEM_PIPELINES': {
            'scraping.pipelines.MunicipiosPipeline': 300,
            'scraping.pipelines.UrlToCSVPipeline': 400,
        },
        'LOG_FILE': f'./logs/scraping-municipios.log',
        # 'JOBDIR': f'scraping/crawls/municipios',  # Temporarily disabled due to queue corruption
        
        # Anti-detection and rate limiting settings for free tier
        'DOWNLOAD_DELAY': 10,  # 10 second delay between requests to avoid hitting limits
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,  # Randomize delay (5-15 seconds)
        'CONCURRENT_REQUESTS': 1,  # Only one concurrent request
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 10,
        'AUTOTHROTTLE_MAX_DELAY': 30,  # Max 30 second delay
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 0.5,  # Very conservative concurrency
        'AUTOTHROTTLE_DEBUG': True,  # Enable to see throttling stats
        
        # Retry settings
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 522, 524, 408, 429, 403, 423, 409],
    }

    # Conjunto para almacenar las URLs ya visitadas
    # visited_urls = set()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        dispatcher.connect(self.spider_closed, signals.spider_closed)
        self.logger.info("Spider de Municipios inicializado")
        
        # Clean corrupted cache files on startup
        self._clean_corrupted_cache()
        # En este punto NO hay acceso a settings todavía

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)

        # Cargar aquí las settings
        spider.target_url_pattern = crawler.settings.get('TARGET_URL_PATTERN')
        spider.excluded_url_patterns = crawler.settings.get('EXCLUDED_URL_PATTERNS')
        spider.excluded_url_endings = crawler.settings.get('EXCLUDED_URL_ENDINGS')
        spider.browsers = crawler.settings.get('BROWSERS', ['chrome110'])  # Default fallback

        # Log loaded settings for debugging
        spider.logger.info(f"Target URL pattern: {spider.target_url_pattern}")
        spider.logger.info(f"Browsers loaded: {spider.browsers}")

        # Señales como spider_closed para ejecutar código cuando el spider termina.
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        
        return spider
    
    def _clean_corrupted_cache(self):
        """
        Clean corrupted cache files that cause OSError: Invalid argument
        """
        try:
            # Clean corrupted queue files
            crawls_dir = './scraping/crawls/municipios/'
            if os.path.exists(crawls_dir):
                # Remove .seen and .state files that can cause corruption
                for pattern in ['*.seen', '*.state', 'requests.queue/*']:
                    for file_path in glob.glob(os.path.join(crawls_dir, pattern)):
                        try:
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                                self.logger.info(f"Removed corrupted cache file: {file_path}")
                            elif os.path.isdir(file_path):
                                shutil.rmtree(file_path)
                                self.logger.info(f"Removed corrupted cache directory: {file_path}")
                        except Exception as e:
                            self.logger.warning(f"Could not remove cache file {file_path}: {e}")
                
                # Recreate clean directory structure
                os.makedirs(crawls_dir, exist_ok=True)
                self.logger.info(f"Cleaned cache directory: {crawls_dir}")
        except Exception as e:
            self.logger.warning(f"Cache cleanup failed: {e}")
    
    def start_requests(self):
        """
        Inicia las solicitudes con la configuración de impersonate
        """
        # Ensure browsers list is available
        if not hasattr(self, 'browsers') or not self.browsers:
            self.browsers = ['chrome110']  # Fallback
            self.logger.warning("Browsers not loaded, using fallback: chrome110")
        
        self.logger.info(f"Starting requests with browsers: {self.browsers}")

        if os.path.exists(self.pending_file):
            with open(self.pending_file, 'rb') as f:
                pending_urls = pickle.load(f)
            self.logger.info(f'Cargadas {len(pending_urls)} URLs pendientes')
            for url in pending_urls:
                yield scrapy.Request(url, callback=self.parse, dont_filter=True, meta={'impersonate': random.choice(self.browsers)})
        else:
            for url in self.start_urls:
                yield scrapy.Request(url, callback=self.parse, meta={'impersonate': random.choice(self.browsers)})       
        
        # for url in self.start_urls:
        #     yield scrapy.Request(
        #         url=url,
        #         callback=self.parse,
        #         # dont_filter=True,
        #         meta={
        #             'impersonate': random.choice(self.browsers),  # Usar el navegador seleccionado al azar
        #         }
        #     )
            # Añadir la URL inicial al conjunto de visitadas
            # self.visited_urls.add(url)
    
    def parse(self, response):
        """
        Procesa la respuesta extrayendo y siguiendo enlaces relevantes.
        """
        # Extraer todas las URLs
        self.logger.info(f"Parseando página: {response.url}")
        
        # Extraer todos los enlaces de la página
        links = response.css('a::attr(href)').getall()
        
        for link in links:
            url = normalize_url(response.urljoin(link), self.target_url_pattern)

            # Excluir URLS que no aportan valor
            if is_no_visit(url, self.target_url_pattern, self.excluded_url_patterns):
                continue

            # self.logger.info(f"URL: {url} ha pasado el filtro de is_no_visit.")

            # Evaluar si es una URL target para guardar (sin importar si fue visitada o no)
            # Excluye páginas que no deben ser guardadas pero si visitadas
            if is_target_url(url, self.target_url_pattern, self.excluded_url_endings, self.excluded_url_patterns):
                # self.logger.debug(f"URL: {url} guardada como target url.")
                url_item = UrlItem()
                url_item['url'] = url
                yield url_item
            
            # Si no fue visitada, seguir la URL
            # if url not in self.visited_urls:
            #     self.logger.info(f"URL: {url} se procede a visitarla y se marcada como visitada.")
            #     self.visited_urls.add(url)
            
            #     # Seguir la URL 
            #     yield scrapy.Request(
            #         url=url,
            #         callback=self.parse,
            #         # dont_filter=True,
            #         meta={
            #             'impersonate': random.choice(self.browsers),  # Usar el navegador seleccionado al azar
            #         }
                # )
            # Seguir la URL 
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                # dont_filter=True,
                meta={
                    'impersonate': random.choice(self.browsers) if self.browsers else 'chrome110',
                }
            )

    def spider_closed(self, spider, reason):
        self.logger.info(f"Spider Closed")
        # with open('visited_urls.csv', 'w', encoding='utf-8') as f:
        #     for url in self.visited_urls:
        #         f.write(f"{url}\n")
        # self.logger.info(f"Se guardaron {len(self.visited_urls)} URLs visitadas.")

        # # Solo borra JOBDIR si el spider terminó correctamente
        # if reason == 'finished':
        #     jobdir = self.settings.get('JOBDIR')
        #     if jobdir and os.path.exists(jobdir):
        #         shutil.rmtree(jobdir)
        #         self.logger.info(f"JOBDIR eliminado: {jobdir}")