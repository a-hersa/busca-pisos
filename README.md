# Inmobiliario Tools

Property analysis platform with Next.js frontend, FastAPI backend, and PostgreSQL database.

## Quick Start

```bash
# Clone and setup environment
git clone <repository>
cd inmobiliario-tools
cp .env.example .env
# Edit .env with your configuration
docker compose up -d
```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001

## First User Setup

The first user to register will automatically become the admin user and won't require email confirmation.

## Environment Configuration

All configuration is managed through environment variables in the `.env` file:

### Required Variables
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`: Database credentials
- `SECRET_KEY`: Application secret (change in production)
- `SCRAPINGANT_API_KEY`: API key for web scraping proxy service

### Optional Variables
- `TURNSTILE_SITE_KEY`, `TURNSTILE_SECRET_KEY`: Cloudflare bot protection
- `SMTP_*`: Email configuration for notifications
- `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_WS_URL`: Frontend-backend communication

### Production Security
- Generate a strong `SECRET_KEY`
- Use secure database passwords
- Configure proper SMTP credentials
- Set up firewall rules for container access

## Architecture

- **Frontend**: Next.js 14 with TypeScript
- **Backend**: FastAPI with async PostgreSQL
- **Database**: PostgreSQL 15 with performance optimizations
- **Cache**: Redis for Celery and API caching
- **Workers**: Celery for background tasks
- **Web Scraping**: Scrapy spiders integrated with Celery
- **Analytics**: Built-in dashboard with real-time updates

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