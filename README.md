# Inmobiliario Tools

Modern property analysis and crawl job management platform built with Next.js, FastAPI, and PostgreSQL.

## Features

- **Job Management**: Create, schedule, and monitor web scraping jobs
- **Property Analysis**: Advanced filtering, search, and visualization of property data
- **Real-time Updates**: WebSocket integration for live job status monitoring
- **Analytics Dashboard**: Comprehensive charts and metrics for property trends
- **Data Export**: Export data in CSV, Excel, and JSON formats
- **Email Notifications**: Automated job completion and weekly summary emails
- **Performance Optimized**: Redis caching, database indexing, and bundle optimization

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Primary database with async support
- **SQLAlchemy**: ORM with async capabilities
- **Celery**: Distributed task queue for background jobs
- **Redis**: Caching and message broker
- **Scrapy**: Web scraping framework

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **React Query**: Server state management
- **Recharts**: Data visualization
- **WebSocket**: Real-time communication

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 18+
- PostgreSQL 13+
- Redis 6+ (optional, for caching)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd inmobiliario-tools
   ```

2. **Start PostgreSQL and Redis**
   ```bash
   # PostgreSQL (Ubuntu/Debian)
   sudo service postgresql start
   
   # Redis (Ubuntu/Debian)  
   sudo service redis-server start
   
   # macOS with Homebrew
   brew services start postgresql
   brew services start redis
   ```

3. **Create database**
   ```bash
   sudo -u postgres createuser -s inmobiliario_user
   sudo -u postgres createdb inmobiliario_db -O inmobiliario_user
   sudo -u postgres psql -c "ALTER USER inmobiliario_user PASSWORD 'inmobiliario_pass';"
   ```

4. **Run the application**
   ```bash
   python run_local.py
   ```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Docker Development

```bash
# Copy environment file
cp backend/.env.example backend/.env

# Start with Docker Compose
docker-compose up --build

# For performance-optimized setup
docker-compose -f docker-compose.performance.yml up --build
```

## Project Structure

```
inmobiliario-tools/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── core/           # Core functionality (auth, deps)
│   │   ├── models/         # SQLAlchemy models
│   │   ├── routers/        # API endpoints
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   ├── tasks/          # Celery tasks
│   │   └── middleware/     # Custom middleware
│   ├── main.py            # FastAPI app entry point
│   └── requirements.txt   # Python dependencies
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── app/           # App Router pages
│   │   ├── components/    # React components
│   │   ├── hooks/         # Custom hooks
│   │   └── lib/           # Utility functions
│   ├── package.json       # Node.js dependencies
│   └── next.config.js     # Next.js configuration
├── scrapy/                # Scrapy spiders
└── docker-compose.yml     # Docker services
```

## API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user

### Jobs
- `GET /api/jobs` - List crawl jobs
- `POST /api/jobs` - Create new job
- `POST /api/jobs/{id}/run` - Run job
- `PUT /api/jobs/{id}` - Update job
- `DELETE /api/jobs/{id}` - Delete job

### Properties
- `GET /api/properties` - List properties with filtering
- `GET /api/properties/{id}` - Get property details

### Analytics
- `GET /api/analytics/overview` - Dashboard statistics
- `GET /api/analytics/trends` - Property trends data

### Export
- `GET /api/export/csv` - Export data as CSV
- `GET /api/export/excel` - Export data as Excel
- `GET /api/export/json` - Export data as JSON

## Environment Variables

### Backend (.env)
```env
POSTGRES_USER=inmobiliario_user
POSTGRES_PASSWORD=inmobiliario_pass
POSTGRES_DB=inmobiliario_db
SECRET_KEY=your-secret-key
REDIS_URL=redis://localhost:6379/0

# Email (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Performance Optimizations

- **Redis Caching**: API responses cached for 5 minutes
- **Database Indexes**: Optimized queries with proper indexing
- **Bundle Splitting**: Code splitting for faster loading
- **Lazy Loading**: Components loaded on demand
- **Connection Pooling**: Optimized database connections

## Development

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Database Migrations
```bash
cd backend
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Production Deployment

### Database Optimization
Run the provided SQL script for production indexes:
```bash
psql -d inmobiliario_db -f backend/database_indexes.sql
```

### Performance Configuration
Use the performance-optimized Docker Compose:
```bash
docker-compose -f docker-compose.performance.yml up -d
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.