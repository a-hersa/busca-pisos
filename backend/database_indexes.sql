-- Database performance optimization indexes
-- Run these commands in your PostgreSQL database to improve query performance

-- Index for property filtering and sorting
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_poblacion ON properties USING gin(poblacion gin_trgm_ops);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_precio ON properties (precio);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_fecha_crawl ON properties (fecha_crawl DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_habitaciones ON properties (habitaciones);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_ascensor ON properties (ascensor);

-- Composite indexes for common filter combinations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_precio_range ON properties (precio, fecha_crawl DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_location_price ON properties (poblacion, precio);

-- Full-text search indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_nombre_search ON properties USING gin(nombre gin_trgm_ops);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_descripcion_search ON properties USING gin(descripcion gin_trgm_ops);

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
ANALYZE properties;
ANALYZE crawl_jobs;
ANALYZE users;