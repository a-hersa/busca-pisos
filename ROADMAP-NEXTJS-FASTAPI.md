# Roadmap: Next.js + FastAPI + PostgreSQL Implementation

## Overview
Modernize the inmobiliario-tools platform with a decoupled architecture using Next.js for the frontend, FastAPI for the backend API, and PostgreSQL for data persistence. This approach provides better scalability, maintainability, and user experience.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js       │    │   FastAPI       │    │  PostgreSQL     │
│   Frontend      │◄──►│   Backend API   │◄──►│   Database      │
│                 │    │                 │    │                 │
│ - React UI      │    │ - REST API      │    │ - Users         │
│ - Auth Context  │    │ - JWT Auth      │    │ - Crawl Jobs    │
│ - Job Mgmt      │    │ - Job Scheduler │    │ - Properties    │
│ - Real-time     │    │ - WebSockets    │    │ - Audit Logs    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   Scrapy        │
                    │   Workers       │
                    │                 │
                    │ - Celery Tasks  │
                    │ - Spider Exec   │
                    │ - Data Pipeline │
                    └─────────────────┘
```

## Database Schema

### Users & Authentication
```sql
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'user')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE user_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(user_id),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);
```

### Independent Crawl Jobs System
```sql
CREATE TABLE crawl_jobs (
    job_id SERIAL PRIMARY KEY,
    job_name VARCHAR(100) NOT NULL,
    spider_name VARCHAR(50) NOT NULL,
    start_urls TEXT[] NOT NULL,
    created_by INTEGER REFERENCES users(user_id),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    schedule_type VARCHAR(20) DEFAULT 'manual' CHECK (schedule_type IN ('manual', 'daily', 'weekly', 'monthly')),
    cron_expression VARCHAR(100),
    job_config JSONB DEFAULT '{}',
    next_run TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE job_executions (
    execution_id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES crawl_jobs(job_id),
    status VARCHAR(20) NOT NULL CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    items_scraped INTEGER DEFAULT 0,
    error_message TEXT,
    execution_log JSONB DEFAULT '{}',
    celery_task_id VARCHAR(255)
);
```

### Audit & Logging
```sql
CREATE TABLE audit_logs (
    log_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INTEGER,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Implementation Phases

### Phase 1: FastAPI Backend Setup (Week 1-2)
- [x] Design database schema
- [ ] Set up FastAPI project structure
- [ ] Implement JWT authentication system
- [ ] Create user management endpoints
- [ ] Set up PostgreSQL with new schema
- [ ] Implement basic CRUD for crawl jobs
- [ ] Add audit logging middleware

### Phase 2: Scrapy Integration (Week 3)
- [ ] Integrate Celery for async job execution
- [ ] Create Scrapy job runner service
- [ ] Implement job status tracking
- [ ] Add real-time job monitoring via WebSockets
- [ ] Migrate existing spiders to new system

### Phase 3: Next.js Frontend (Week 4-5)
- [ ] Set up Next.js 14 with TypeScript
- [ ] Implement authentication context
- [ ] Create job management dashboard
- [ ] Build property visualization components
- [ ] Add real-time job status updates
- [ ] Implement responsive design

### Phase 4: Advanced Features (Week 6-7)
- [ ] Job scheduling with cron expressions
- [ ] Advanced filtering and search
- [ ] Data export functionality
- [ ] User role management
- [ ] Analytics dashboard
- [ ] Email notifications

### Phase 5: Production Deployment (Week 8)
- [ ] Docker containerization
- [ ] CI/CD pipeline setup
- [ ] Environment configuration
- [ ] Security hardening
- [ ] Performance optimization
- [ ] Monitoring and logging

## Tech Stack Details

### Backend (FastAPI)
```python
# Core dependencies
fastapi[all]==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.13.0
asyncpg==0.29.0
pydantic==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
celery[redis]==5.3.4
redis==5.0.1
```

### Frontend (Next.js)
```json
{
  "dependencies": {
    "next": "14.0.3",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "@next/font": "14.0.3",
    "typescript": "5.3.2",
    "@types/react": "18.2.42",
    "tailwindcss": "3.3.6",
    "axios": "1.6.2",
    "react-query": "3.39.3",
    "react-hook-form": "7.48.2",
    "recharts": "2.8.0",
    "socket.io-client": "4.7.4"
  }
}
```

## API Design

### Authentication Endpoints
```python
POST /auth/register      # User registration
POST /auth/login         # User login (returns JWT)
POST /auth/refresh       # Refresh JWT token
POST /auth/logout        # Invalidate session
GET  /auth/me           # Get current user info
```

### Job Management Endpoints
```python
GET    /api/jobs                 # List user's crawl jobs
POST   /api/jobs                 # Create new crawl job
GET    /api/jobs/{job_id}        # Get job details
PUT    /api/jobs/{job_id}        # Update job configuration
DELETE /api/jobs/{job_id}        # Delete job
POST   /api/jobs/{job_id}/run    # Execute job manually
GET    /api/jobs/{job_id}/logs   # Get execution logs
```

### Data Endpoints
```python
GET /api/properties             # List properties with filters
GET /api/properties/{id}        # Get property details
GET /api/municipios            # List available municipalities
GET /api/analytics             # Get analytics data
```

### Admin Endpoints
```python
GET /api/admin/users           # User management
GET /api/admin/audit-logs      # System audit trail
GET /api/admin/system-stats    # System statistics
```

## Key Features

### 1. Modern Authentication
- JWT-based authentication
- Role-based access control
- Session management
- Password reset functionality

### 2. Job Management Dashboard
- Visual job creation interface
- Real-time execution monitoring
- Scheduling with cron expressions
- Execution history and logs

### 3. Enhanced Property Analysis
- Interactive data visualization
- Advanced filtering options
- Export to Excel/CSV
- Rental yield calculator

### 4. Real-time Updates
- WebSocket connections for live updates
- Job status notifications
- System health monitoring

### 5. Responsive Design
- Mobile-first approach
- Dark/light theme support
- Accessibility compliance
- Progressive Web App features

## Security Considerations

### Authentication & Authorization
- JWT tokens with short expiration
- Refresh token rotation
- Rate limiting on auth endpoints
- Password strength requirements

### API Security
- CORS configuration
- Request validation with Pydantic
- SQL injection prevention
- XSS protection

### Data Protection
- Password hashing with bcrypt
- Sensitive data encryption
- Audit trail for all actions
- GDPR compliance considerations

## Development Workflow

### 1. Local Development
```bash
# Backend
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm run dev

# Database
docker-compose up postgres redis
```

### 2. Testing Strategy
- Unit tests for API endpoints
- Integration tests for database operations
- E2E tests for critical user flows
- Load testing for job execution

### 3. Deployment
- Docker containers for all services
- Kubernetes orchestration
- CI/CD with GitHub Actions
- Environment-based configuration

## Migration Strategy

### From Current Flask App
1. **Data Migration**: Export existing data, transform to new schema
2. **Parallel Development**: Build new system alongside current one
3. **Gradual Cutover**: Migrate users and features incrementally
4. **Rollback Plan**: Maintain ability to revert to Flask system

### Timeline
- **Week 1-2**: Backend foundation
- **Week 3-4**: Core functionality migration
- **Week 5-6**: Frontend development
- **Week 7**: Testing and optimization
- **Week 8**: Production deployment

## Success Metrics

### Performance
- API response time < 200ms
- Job execution time improvement
- Frontend loading time < 2s
- 99.9% uptime

### User Experience
- Reduced clicks to complete tasks
- Mobile responsiveness score > 95
- User satisfaction surveys
- Feature adoption rates

### Developer Experience
- Reduced deployment time
- Improved code maintainability
- Better error tracking
- Simplified debugging

## Risk Mitigation

### Technical Risks
- **API Breaking Changes**: Versioned API endpoints
- **Data Loss**: Comprehensive backup strategy
- **Performance Issues**: Load testing and monitoring
- **Security Vulnerabilities**: Regular security audits

### Business Risks
- **User Adoption**: Gradual migration with training
- **Feature Parity**: Comprehensive testing against current system
- **Downtime**: Blue-green deployment strategy
- **Budget Overrun**: Phased development approach

## Conclusion

This roadmap provides a comprehensive plan for modernizing the inmobiliario-tools platform with Next.js, FastAPI, and PostgreSQL. The decoupled architecture ensures scalability, maintainability, and an enhanced user experience while maintaining all current functionality and adding powerful new features for crawl job management and property analysis.