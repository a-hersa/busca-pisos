# Inmobiliario Tools

Property analysis platform with Next.js frontend, FastAPI backend, and PostgreSQL database.

## Quick Start

```bash
# Clone and start with Docker
git clone <repository>
cd inmobiliario-tools
docker compose up -d
```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- Flask Web: http://localhost:5000

## Development Credentials

**Test User:**
- Username: `testuser`
- Password: `testpass123`
- Email: `test@example.com`

## Production Setup

**SMTP Configuration:**
Update these environment variables in docker-compose.yml:
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
```

**Security:**
- Change SECRET_KEY in production
- Update SMTP credentials
- Create admin users via API
- Enable proper firewall rules

## Architecture

- **Frontend**: Next.js 14 with TypeScript
- **Backend**: FastAPI with async PostgreSQL
- **Database**: PostgreSQL 15 with health checks
- **Cache**: Redis for Celery and API caching
- **Workers**: Celery for background tasks
- **Web Scraping**: Scrapy spiders
- **Analytics**: Custom dashboard with charts

## Development

```bash
# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Database access
docker exec -it inmobiliario-postgres psql -U inmobiliario_user -d inmobiliario_db

# Run tests
docker exec inmobiliario-backend pytest
```