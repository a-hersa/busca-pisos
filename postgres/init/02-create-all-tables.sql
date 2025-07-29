-- Complete database schema for busca-pisos application

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create municipios table for URL storage
CREATE TABLE IF NOT EXISTS municipios (
    id SERIAL PRIMARY KEY,
    url VARCHAR(500) UNIQUE NOT NULL,
    fecha_found DATE DEFAULT CURRENT_DATE,
    spider_name VARCHAR(100),
    processed BOOLEAN DEFAULT FALSE
);

-- Create crawl_jobs table
CREATE TABLE IF NOT EXISTS crawl_jobs (
    job_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    spider_name VARCHAR(100) NOT NULL,
    start_urls TEXT[],
    schedule_type VARCHAR(50) DEFAULT 'manual',
    cron_expression VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    next_run TIMESTAMP,
    job_config JSONB DEFAULT '{}'::jsonb
);

-- Create job_executions table
CREATE TABLE IF NOT EXISTS job_executions (
    execution_id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES crawl_jobs(job_id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'pending',
    celery_task_id VARCHAR(255),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    items_scraped INTEGER DEFAULT 0,
    error_message TEXT,
    execution_details JSONB DEFAULT '{}'::jsonb
);

-- Create user_sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id UUID PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    ip_address INET,
    user_agent TEXT
);

-- Create audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(100),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users (is_active);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions (expires_at);

CREATE INDEX IF NOT EXISTS idx_municipios_spider ON municipios(spider_name);
CREATE INDEX IF NOT EXISTS idx_municipios_processed ON municipios(processed);

CREATE INDEX IF NOT EXISTS idx_crawl_jobs_status ON crawl_jobs (status);
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_created_at ON crawl_jobs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_next_run ON crawl_jobs (next_run) WHERE schedule_type != 'manual';

CREATE INDEX IF NOT EXISTS idx_job_executions_job_id ON job_executions (job_id);
CREATE INDEX IF NOT EXISTS idx_job_executions_status ON job_executions (status);
CREATE INDEX IF NOT EXISTS idx_job_executions_started_at ON job_executions (started_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs (action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs (created_at DESC);