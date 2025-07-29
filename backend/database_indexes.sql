-- Database performance optimization indexes
-- Run these commands in your PostgreSQL database to improve query performance

-- Index for property filtering and sorting
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_propiedades_poblacion ON propiedades USING gin(poblacion gin_trgm_ops);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_propiedades_precio ON propiedades (precio);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_propiedades_fecha_crawl ON propiedades (fecha_crawl DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_propiedades_habitaciones ON propiedades (habitaciones);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_propiedades_ascensor ON propiedades (ascensor);

-- Composite indexes for common filter combinations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_propiedades_precio_range ON propiedades (precio, fecha_crawl DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_propiedades_location_price ON propiedades (poblacion, precio);

-- Full-text search indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_propiedades_nombre_search ON propiedades USING gin(nombre gin_trgm_ops);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_propiedades_descripcion_search ON propiedades USING gin(descripcion gin_trgm_ops);

-- Job performance indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_crawl_jobs_status ON crawl_jobs (status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_crawl_jobs_created_at ON crawl_jobs (created_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_crawl_jobs_next_run ON crawl_jobs (next_run) WHERE schedule_type != 'manual';

-- User performance indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_is_active ON users (is_active);

-- Enable pg_trgm extension for trigram similarity searches
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Statistics update for better query planning
ANALYZE propiedades;
ANALYZE crawl_jobs;
ANALYZE users;