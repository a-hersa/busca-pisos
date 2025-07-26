# 🏠 Busca Pisos

> **Educational Property Analysis Platform**  
> A learning-focused real estate data platform built with Next.js, FastAPI, and PostgreSQL

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-black?logo=next.js&logoColor=white)](https://nextjs.org/)

## 📚 About This Project

**Busca Pisos** is an educational project designed for learning modern web development practices through building a property analysis platform. This project demonstrates full-stack development with:

- **Frontend**: Next.js 14 with TypeScript and modern React patterns
- **Backend**: FastAPI with async/await and modern Python practices  
- **Database**: PostgreSQL with SQLAlchemy and async operations
- **DevOps**: Docker containerization and orchestration
- **Real-time**: WebSocket integration for live updates

### 🎓 Educational Purpose

This project was created for **educational purposes only** to learn and demonstrate:
- Modern full-stack development patterns
- API design and implementation
- Database modeling and optimization
- Docker containerization
- Real-time web applications
- Ethical web scraping practices

### 📜 Project Origins

Busca Pisos originated as a learning branch from [inmobiliario-tools](https://github.com/a-hersa/inmobiliario-tools) that evolved into its own project. During development sessions with Claude Code, we enhanced the original concept by:

- Migrating from a Python-only backend to FastAPI
- Adding a modern Next.js frontend with TypeScript
- Implementing real-time features with WebSockets
- Containerizing the entire application with Docker
- Adding comprehensive documentation and learning materials

The evolution from a simple scraping tool to a full-stack platform showcases the journey of learning modern web development practices.

### 🤝 Acknowledgments

- **[Idealista.com](https://www.idealista.com)**: Data source for educational scraping examples (minimal, respectful usage only)
- **[ScrapingAnt](https://scrapingant.com)**: Proxy service for ethical web scraping
- **[Claude Code](https://claude.ai/code)**: AI pair programming partner that helped enhance this project

## ⚠️ Important Disclaimers

### Web Scraping Ethics
- This project performs **minimal, educational-level scraping only**
- Always respects `robots.txt` and website terms of service
- Implements rate limiting and respectful crawling practices
- Uses proxy services to avoid overwhelming target servers
- **Not intended for commercial or large-scale data extraction**

### Legal Notice
- For educational and learning purposes only
- Users are responsible for complying with all applicable laws and website terms
- Respect intellectual property rights and data privacy regulations
- Always obtain proper permissions before scraping any website

## 🚀 Quick Start

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- [Git](https://git-scm.com/downloads)

### Installation

```bash
# Clone the repository
git clone https://github.com/a-hersa/busca-pisos.git
cd busca-pisos

# Copy and configure environment
cp .env.example .env
# Edit .env with your configuration (see Configuration section below)

# Start the application
docker compose up -d

# Check that all services are running
docker compose ps
```

### Access Points
- **Frontend Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8001/docs
- **Alternative API Docs**: http://localhost:8001/redoc

### First User Setup
The first user to register will automatically become the admin user and won't require email confirmation.

## ⚙️ Configuration

### Required Environment Variables

```bash
# Database Configuration
POSTGRES_DB=busca_pisos_db
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_secure_password

# Application Security
SECRET_KEY=your-long-random-secret-key-change-in-production

# ScrapingAnt API (for ethical scraping)
SCRAPINGANT_API_KEY=your-scrapingant-api-key
```

### Optional Configuration

```bash
# Email Configuration (for user notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=Busca Pisos

# Bot Protection (Cloudflare Turnstile)
TURNSTILE_SITE_KEY=your-turnstile-site-key
TURNSTILE_SECRET_KEY=your-turnstile-secret-key

# Frontend URLs (usually defaults work)
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_WS_URL=ws://localhost:8001
```

### Security Best Practices

- **Never use default credentials in production**
- Generate a strong `SECRET_KEY` (use `openssl rand -hex 32`)
- Use environment-specific `.env` files
- Enable firewall rules for database access
- Configure HTTPS in production
- Regular security updates for dependencies

## 🏗️ Architecture

### System Overview
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js       │    │    FastAPI      │    │   PostgreSQL    │
│   Frontend      │◄──►│    Backend      │◄──►│   Database      │
│   (Port 3000)   │    │   (Port 8001)   │    │   (Port 5432)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐             │
         │              │     Redis       │             │
         └──────────────│   Cache/Queue   │─────────────┘
                        │   (Port 6379)   │
                        └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Celery Workers │
                    │ Background Tasks│
                    └─────────────────┘
```

### Technology Stack

#### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **React Query**: Server state management
- **WebSockets**: Real-time communication

#### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: Async ORM for database operations
- **Pydantic**: Data validation and serialization
- **Celery**: Distributed task queue
- **Scrapy**: Web scraping framework

#### Infrastructure
- **PostgreSQL 15**: Primary database with optimizations
- **Redis**: Caching and message broker
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration

## 💻 Development

### Local Development Setup

```bash
# Start services in development mode
docker compose up --build

# View logs for specific services
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f celery-worker

# Access database directly
docker exec -it busca-pisos-postgres psql -U busca_pisos_user -d busca_pisos_db

# Run backend tests
docker exec busca-pisos-backend pytest

# Install new Python dependencies
docker exec busca-pisos-backend pip install package-name
docker exec busca-pisos-backend pip freeze > requirements.txt

# Frontend development
cd frontend
npm run dev  # Run Next.js in development mode
npm run build  # Build for production
npm run lint  # Run ESLint
```

### API Development

```bash
# Generate API client
curl http://localhost:8001/openapi.json > api-spec.json

# Test API endpoints
curl http://localhost:8001/health
curl http://localhost:8001/docs  # Interactive API documentation
```

### Database Operations

```bash
# Create database backup
docker exec busca-pisos-postgres pg_dump -U busca_pisos_user busca_pisos_db > backup.sql

# Restore database backup
docker exec -i busca-pisos-postgres psql -U busca_pisos_user busca_pisos_db < backup.sql

# View database logs
docker compose logs -f postgres
```

## 📖 Learning Resources

### Included Guides
This project includes comprehensive learning materials:

- **[FastAPI Learning Path](learning/fastapi/README.md)**: Complete guide to FastAPI development
- **[Database Integration](learning/fastapi/04-database-integration.md)**: SQLAlchemy and async patterns
- **[Authentication & Security](learning/fastapi/05-authentication-security.md)**: JWT and security best practices
- **[Testing & Validation](learning/fastapi/09-testing-validation.md)**: Comprehensive testing strategies

### External Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## 🤝 Contributing

We welcome contributions! This project is designed for learning, so all skill levels are encouraged to participate.

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**: Follow the coding standards
4. **Add tests**: Ensure your changes are tested
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to the branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**: Describe your changes

### Development Guidelines

- Follow TypeScript and Python best practices
- Add tests for new features
- Update documentation as needed
- Respect the educational nature of the project
- Maintain ethical scraping practices

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Responsible Usage

Please use this project responsibly:

- **Educational purposes only**
- Respect website terms of service
- Implement appropriate rate limiting
- Never overwhelm target servers
- Follow data privacy regulations
- Obtain necessary permissions for any commercial use

## 🙏 Acknowledgments

Special thanks to:
- The FastAPI and Next.js communities for excellent documentation
- Idealista.com for providing data for educational purposes
- ScrapingAnt for ethical scraping infrastructure
- Claude Code for pair programming assistance
- All contributors who help improve this educational resource

---

**Happy Learning!** 🚀

If you find this project helpful for learning, please consider giving it a ⭐ star on GitHub!