# Scrapy settings for scraping project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import os
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

BOT_NAME = "scraping"

SPIDER_MODULES = ["scraping.spiders"]
NEWSPIDER_MODULE = "scraping.spiders"

# Configuración de conexión a PostgreSQL
# DATABASE_URL = os.environ.get('DATABASE_URL')
POSTGRES_HOST = 'postgres'
POSTGRES_PORT = '5432'
POSTGRES_DB = os.getenv("POSTGRES_DB", 'busca_pisos_db')
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configura los reintentos
RETRY_ENABLED = True
RETRY_TIMES = 10  # Número de reintentos para errores de solicitud
RETRY_HTTP_CODES = [403, 409, 423, 500, 502, 503, 504]  # Agrega el código 423 a los reintentos

LOG_LEVEL = 'DEBUG'  # O 'DEBUG' para más detalles

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 1

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 5
# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 1
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = True

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "scraping.middlewares.ScrapingSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    "scraping.middlewares.ScrapingAntProxyMiddleware": 100,  # High priority to ensure it runs first
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   "scraping.pipelines.PropertyItemPipeline": 300,
   "scraping.pipelines.PostgresPipeline": 400,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay
AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5
# Enable showing throttling stats for every response received:
AUTOTHROTTLE_DEBUG = True

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# Configuración del spider
TARGET_URL_PATTERN = 'https://www.idealista.com/venta-viviendas/'
EXCLUDED_URL_ENDINGS = [
    "/municipios",
    "/mapa",
]
EXCLUDED_URL_PATTERNS = [
    "/con-", 
    "/pagina-", 
    "/mapa-",
    "/news/",
    "/es/",
    "/it/", 
    "/en/", 
    "/fr/",
    "/pt/",
    "/de/",
    "/ru/",
    "/uk/",
    "/ro/",
    "/nl/",
    "/pl/",
    "/se/",
    "/dk/",
    "/fi/",
    "/no/",
    "/cz/",
    "/hu/",
    "/sk/",
    "/bg/",
    "/da/",
    "/sv/",
    "/zh/",
    "/el/",
    "/ca/",
    "/el/",
    "/geo/",
    "/energy/",
    "/cursos/",
    "/ayuda/",
    "/pro/",
    "/info/",
    "/data/",
    "/blog/",
    "/noticias/",
    "/contacto/",
    "/legal/",
    "/aviso-legal/",
    "/politica-privacidad/",
    "/politica-cookies/",
    "/condiciones-uso/",
    "/tools/",
    "inmobiliaria",
    "inquilinos",
    "habitaciones",
]

BROWSERS = ['chrome110']