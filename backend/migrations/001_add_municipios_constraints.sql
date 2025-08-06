-- Migration script to ensure municipios table exists with proper structure
-- Run this after the initial database creation

-- Ensure municipios table exists with correct structure
CREATE TABLE IF NOT EXISTS municipios (
    id SERIAL PRIMARY KEY,
    url VARCHAR(500) UNIQUE NOT NULL,
    fecha_found DATE DEFAULT CURRENT_DATE,
    spider_name VARCHAR(100),
    processed BOOLEAN DEFAULT FALSE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_municipios_url ON municipios(url);
CREATE INDEX IF NOT EXISTS idx_municipios_spider ON municipios(spider_name);
CREATE INDEX IF NOT EXISTS idx_municipios_processed ON municipios(processed);
CREATE INDEX IF NOT EXISTS idx_municipios_fecha_found ON municipios(fecha_found);

-- Add a composite index for common queries
CREATE INDEX IF NOT EXISTS idx_municipios_spider_processed ON municipios(spider_name, processed);

-- Add a partial index for unprocessed municipios (more efficient for queries)
CREATE INDEX IF NOT EXISTS idx_municipios_unprocessed ON municipios(id) WHERE processed = FALSE;

-- Update table comment for documentation
COMMENT ON TABLE municipios IS 'Storage for discovered municipality URLs from scraping, used as allowed starting URLs for crawl jobs';
COMMENT ON COLUMN municipios.url IS 'Full URL of the municipality page from idealista.com';
COMMENT ON COLUMN municipios.spider_name IS 'Name of the spider that discovered this URL (usually "municipios")';
COMMENT ON COLUMN municipios.processed IS 'Whether this municipality has been processed/crawled for properties';
COMMENT ON COLUMN municipios.fecha_found IS 'Date when this municipality URL was first discovered';