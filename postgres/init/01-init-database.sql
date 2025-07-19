-- Initialize inmobiliario database with required tables

-- Create propiedades table
CREATE TABLE IF NOT EXISTS propiedades (
    p_id INT PRIMARY KEY,
    nombre VARCHAR(255),
    fecha_new DATE,
    fecha_updated DATE,
    precio INT,
    metros INT,
    habitaciones INT,
    planta INT,
    ascensor INT,
    poblacion VARCHAR(255),
    url VARCHAR(255),
    descripcion VARCHAR(4000),
    estatus VARCHAR(255),
    fecha_crawl TIMESTAMP
);

-- Create municipios table for URL storage
CREATE TABLE IF NOT EXISTS municipios (
    id SERIAL PRIMARY KEY,
    url VARCHAR(500) UNIQUE NOT NULL,
    fecha_found DATE DEFAULT CURRENT_DATE,
    spider_name VARCHAR(100),
    processed BOOLEAN DEFAULT FALSE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_propiedades_fecha_updated ON propiedades(fecha_updated);
CREATE INDEX IF NOT EXISTS idx_propiedades_poblacion ON propiedades(poblacion);
CREATE INDEX IF NOT EXISTS idx_propiedades_precio ON propiedades(precio);
CREATE INDEX IF NOT EXISTS idx_municipios_spider ON municipios(spider_name);
CREATE INDEX IF NOT EXISTS idx_municipios_processed ON municipios(processed);