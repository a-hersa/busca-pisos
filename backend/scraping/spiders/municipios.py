# -*- coding: utf-8 -*-
import os
import pickle
import shutil
import scrapy
import logging
import re
import glob
import time
import signal
import sys
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
    
    # State management files
    state_dir = './scraping/crawls/municipios'
    pending_file = './scraping/crawls/municipios/pending_urls.pkl'
    state_file = './scraping/crawls/municipios/spider_state.pkl'
    checkpoint_file = './scraping/crawls/municipios/checkpoint.pkl'
    
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'scraping.middlewares.ScrapingAntProxyMiddleware': 100,
        },
        'ITEM_PIPELINES': {
            'scraping.pipelines.MunicipiosPipeline': 300,
            'scraping.pipelines.UrlToCSVPipeline': 400,
        },
        'LOG_FILE': f'./logs/scraping-municipios.log',
        # JOBDIR disabled - using custom state management instead
        
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
        
        # Initialize state tracking variables
        self.processed_count = 0
        self.last_processed_url = None
        self.quota_exhausted = False
        self.start_time = time.time()
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Clean corrupted cache files on startup
        self._clean_corrupted_cache()
        # Ensure state directory exists
        os.makedirs(self.state_dir, exist_ok=True)

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
        Inicia las solicitudes con la configuración de impersonate y manejo de estado
        """
        # Ensure browsers list is available
        if not hasattr(self, 'browsers') or not self.browsers:
            self.browsers = ['chrome110']  # Fallback
            self.logger.warning("Browsers not loaded, using fallback: chrome110")
        
        self.logger.info(f"Starting requests with browsers: {self.browsers}")
        
        # Check for previous state and decide whether to resume or start fresh
        if self._should_resume():
            self.logger.info("Resuming from previous interrupted crawl")
            self._load_state()
            
            # Load pending URLs if they exist
            if os.path.exists(self.pending_file):
                with open(self.pending_file, 'rb') as f:
                    pending_urls = pickle.load(f)
                self.logger.info(f'Resuming with {len(pending_urls)} pending URLs')
                for url in pending_urls:
                    yield scrapy.Request(url, callback=self.parse, dont_filter=True, 
                                       meta={'impersonate': random.choice(self.browsers)})
                return
        else:
            self.logger.info("Starting fresh crawl")
            self._clean_state_files()
        
        # Normal start
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse, 
                               meta={'impersonate': random.choice(self.browsers)})
        
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
        Procesa la respuesta extrayendo y siguiendo enlaces relevantes con seguimiento de estado.
        """
        # Check if quota is exhausted
        if self.quota_exhausted:
            self.logger.info("Quota exhausted, stopping processing")
            return
            
        self.logger.info(f"Parseando página: {response.url}")
        
        # Update state tracking
        self.processed_count += 1
        self.last_processed_url = response.url
        
        # Save checkpoint every 50 processed URLs
        if self.processed_count % 50 == 0:
            self._save_checkpoint()
        
        # Extraer todos los enlaces de la página
        links = response.css('a::attr(href)').getall()
        discovered_urls = []
        
        for link in links:
            url = normalize_url(response.urljoin(link), self.target_url_pattern)

            # Excluir URLS que no aportan valor
            if is_no_visit(url, self.target_url_pattern, self.excluded_url_patterns):
                continue

            # Evaluar si es una URL target para guardar
            if is_target_url(url, self.target_url_pattern, self.excluded_url_endings, self.excluded_url_patterns):
                url_item = UrlItem()
                url_item['url'] = url
                yield url_item
                discovered_urls.append(url)
            
            # Seguir la URL 
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                    'impersonate': random.choice(self.browsers) if self.browsers else 'chrome110',
                }
            )
        
        # Log progress
        if self.processed_count % 10 == 0:
            self.logger.info(f"Progress: {self.processed_count} pages processed, "
                           f"{len(discovered_urls)} URLs discovered from this page")

    def spider_closed(self, spider, reason):
        """
        Handle spider closure with proper state management and cleanup
        """
        end_time = time.time()
        duration = end_time - self.start_time
        
        self.logger.info(f"Spider closed with reason: {reason}")
        self.logger.info(f"Total pages processed: {self.processed_count}")
        self.logger.info(f"Crawl duration: {duration:.2f} seconds")
        
        if reason == 'finished':
            # Successful completion - clean up all state files
            self._clean_state_files()
            self.logger.info("Successful completion - all state files cleaned")
            
        elif reason in ['quota_exhausted', 'user_interrupt', 'shutdown']:
            # Interrupted - preserve state for resume
            self._save_final_state(reason)
            self._save_pending_requests()
            self.logger.info(f"Spider interrupted ({reason}), state preserved for resume")
            
        else:
            # Other reasons (errors, etc.)
            self.logger.warning(f"Spider closed unexpectedly with reason: {reason}")
            self._save_final_state(reason)
    
    def _signal_handler(self, signum, frame):
        """
        Handle interrupt signals (CTRL+C) gracefully
        """
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        if hasattr(self, 'crawler') and self.crawler.engine:
            self.crawler.engine.close_spider(self, 'user_interrupt')
        else:
            sys.exit(0)
    
    def _should_resume(self):
        """
        Check if we should resume from a previous interrupted crawl
        """
        if not os.path.exists(self.state_file):
            return False
            
        try:
            with open(self.state_file, 'rb') as f:
                last_state = pickle.load(f)
            
            # If last run completed successfully, don't resume
            if last_state.get('reason') == 'finished':
                self.logger.info("Previous crawl completed successfully, starting fresh")
                return False
                
            # Check if state is recent (within 7 days)
            state_age = time.time() - last_state.get('timestamp', 0)
            if state_age > 7 * 24 * 3600:  # 7 days
                self.logger.info("State file too old, starting fresh")
                return False
                
            return True
            
        except Exception as e:
            self.logger.warning(f"Could not load state file: {e}, starting fresh")
            return False
    
    def _load_state(self):
        """
        Load previous spider state
        """
        try:
            with open(self.state_file, 'rb') as f:
                state = pickle.load(f)
            
            self.processed_count = state.get('processed_count', 0)
            self.last_processed_url = state.get('last_processed_url')
            self.start_time = state.get('start_time', time.time())
            
            self.logger.info(f"Loaded state: {self.processed_count} pages processed, "
                           f"last URL: {self.last_processed_url}")
                           
        except Exception as e:
            self.logger.error(f"Failed to load state: {e}")
    
    def _save_checkpoint(self):
        """
        Save current progress checkpoint
        """
        try:
            checkpoint = {
                'processed_count': self.processed_count,
                'last_processed_url': self.last_processed_url,
                'timestamp': time.time(),
                'start_time': self.start_time
            }
            
            with open(self.checkpoint_file, 'wb') as f:
                pickle.dump(checkpoint, f)
                
            self.logger.debug(f"Checkpoint saved: {self.processed_count} pages processed")
            
        except Exception as e:
            self.logger.error(f"Failed to save checkpoint: {e}")
    
    def _save_final_state(self, reason):
        """
        Save final state when spider is interrupted or closes
        """
        try:
            state = {
                'reason': reason,
                'processed_count': self.processed_count,
                'last_processed_url': self.last_processed_url,
                'timestamp': time.time(),
                'start_time': self.start_time,
                'quota_exhausted': self.quota_exhausted
            }
            
            with open(self.state_file, 'wb') as f:
                pickle.dump(state, f)
                
            self.logger.info(f"Final state saved: reason={reason}, processed={self.processed_count}")
            
        except Exception as e:
            self.logger.error(f"Failed to save final state: {e}")
    
    def _save_pending_requests(self):
        """
        Save pending requests from the scheduler for resume
        """
        try:
            if not hasattr(self, 'crawler') or not self.crawler.engine:
                return
                
            # Get pending requests from scheduler
            pending_urls = []
            scheduler = self.crawler.engine.slot.scheduler
            
            # Extract URLs from different queue types
            if hasattr(scheduler, 'mqs'):
                for queue in scheduler.mqs.values():
                    for request in queue:
                        pending_urls.append(request.url)
            
            if pending_urls:
                with open(self.pending_file, 'wb') as f:
                    pickle.dump(pending_urls, f)
                self.logger.info(f"Saved {len(pending_urls)} pending URLs for resume")
            
        except Exception as e:
            self.logger.error(f"Failed to save pending requests: {e}")
    
    def _clean_state_files(self):
        """
        Clean up all state files for a fresh start
        """
        files_to_clean = [
            self.pending_file,
            self.state_file,
            self.checkpoint_file
        ]
        
        for file_path in files_to_clean:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    self.logger.debug(f"Cleaned state file: {file_path}")
                except Exception as e:
                    self.logger.warning(f"Could not clean state file {file_path}: {e}")