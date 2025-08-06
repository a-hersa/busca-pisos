export interface User {
  user_id: number
  username: string
  email: string
  role: string
  created_at: string
  last_login?: string
  is_active: boolean
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface CrawlJob {
  job_id: number
  job_name: string
  spider_name: string
  start_urls: string[]
  created_by: number
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  schedule_type: 'manual' | 'daily' | 'weekly' | 'monthly'
  cron_expression?: string
  job_config: Record<string, any>
  next_run?: string
  created_at: string
  updated_at: string
}

export interface CrawlJobCreate {
  job_name: string
  spider_name: string
  start_urls: string[]
  schedule_type?: string
  cron_expression?: string
  job_config?: Record<string, any>
}

export interface CrawlJobUpdate {
  job_name?: string
  start_urls?: string[]
  schedule_type?: string
  cron_expression?: string
  job_config?: Record<string, any>
}

export interface JobExecution {
  execution_id: number
  status: string
  started_at: string
  completed_at?: string
  items_scraped: number
  error_message?: string
  execution_log?: Record<string, any>
}

export interface JobStatus {
  job_id: number
  job_name: string
  status: string
  latest_execution?: {
    execution_id?: number
    status?: string
    started_at?: string
    completed_at?: string
    items_scraped: number
    error_message?: string
    celery_task_id?: string
  }
  celery_status?: {
    state: string
    info: Record<string, any>
  }
}

export interface Property {
  p_id: number
  nombre?: string
  url?: string
  precio?: number
  metros?: string
  habitaciones?: string
  planta?: string
  ascensor: number
  descripcion?: string
  poblacion?: string
  estatus: string
  fecha_crawl?: string
  fecha_updated?: string
}

export interface WebSocketMessage {
  type: 'job_update' | 'job_progress'
  job_id: number
  status?: string
  progress?: Record<string, any>
  details?: Record<string, any>
  timestamp: string
}

export interface MunicipioSelect {
  id: number
  url: string
  municipality_name: string
}

export interface URLValidationResult {
  valid: boolean
  valid_urls: Array<{
    url: string
    municipio_id: number
    municipality_name: string
  }>
  invalid_urls: string[]
  total_urls: number
  valid_count: number
  invalid_count: number
}