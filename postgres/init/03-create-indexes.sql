-- Performance optimization indexes for propiedades table
-- These are more advanced indexes that require the tables to exist first

-- Full-text search indexes using gin
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_propiedades_poblacion_gin ON propiedades USING gin(poblacion gin_trgm_ops);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_propiedades_nombre_search ON propiedades USING gin(nombre gin_trgm_ops);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_propiedades_descripcion_search ON propiedades USING gin(descripcion gin_trgm_ops);

-- Additional performance indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_propiedades_fecha_crawl_desc ON propiedades (fecha_crawl DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_propiedades_habitaciones ON propiedades (habitaciones);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_propiedades_ascensor ON propiedades (ascensor);

-- Composite indexes for common filter combinations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_propiedades_precio_range ON propiedades (precio, fecha_crawl DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_propiedades_location_price ON propiedades (poblacion, precio);

-- Statistics update for better query planning
ANALYZE propiedades;
ANALYZE crawl_jobs;
ANALYZE users;
ANALYZE job_executions;
ANALYZE audit_logs;