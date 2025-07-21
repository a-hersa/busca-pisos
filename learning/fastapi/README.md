# FastAPI Learning Guide

A comprehensive guide to learning FastAPI using the **inmobiliario-tools** project as a practical example.

## Overview

This learning guide covers all essential FastAPI concepts with real-world examples from our Spanish real estate data scraping and analysis platform. Each guide builds upon previous concepts and includes practical exercises.

## Prerequisites

- **Python 3.7+** experience
- Basic understanding of **web APIs** and **HTTP**
- Familiarity with **databases** (helpful but not required)
- **Docker** knowledge (for running the project)

## Learning Path

### Core Concepts (Essential)

1. **[FastAPI Basics](01-fastapi-basics.md)** ⭐
   - What is FastAPI and why use it
   - Application setup and configuration
   - Basic routing and responses
   - Automatic documentation
   - Environment setup

2. **[Routing and Endpoints](02-routing-and-endpoints.md)** ⭐
   - HTTP methods (GET, POST, PUT, DELETE)
   - Path and query parameters
   - Request/response models
   - Router organization
   - Error handling

3. **[Dependency Injection](03-dependency-injection.md)** ⭐
   - Understanding dependency injection
   - Creating and using dependencies
   - Dependency chains
   - Security dependencies
   - Testing with dependency overrides

4. **[Database Integration](04-database-integration.md)** ⭐
   - SQLAlchemy with async support
   - Database models and relationships
   - CRUD operations
   - Query optimization
   - Pydantic schemas for validation

5. **[Authentication & Security](05-authentication-security.md)** ⭐
   - JWT token authentication
   - Password hashing
   - Role-based access control
   - Email confirmation
   - Security best practices

### Advanced Topics

6. **[Async Programming](06-async-programming.md)**
   - Understanding async/await
   - Async database operations
   - Concurrent request handling
   - Background tasks with Celery
   - Performance optimization

7. **[Middleware & CORS](07-middleware-cors.md)**
   - Understanding middleware
   - CORS configuration
   - Custom middleware creation
   - Request/response processing
   - Security headers

8. **[WebSockets & Real-time](08-websockets-realtime.md)**
   - WebSocket implementation
   - Real-time job monitoring
   - Connection management
   - Broadcasting messages
   - Client-side integration

9. **[Testing & Validation](09-testing-validation.md)**
   - Comprehensive testing strategies
   - Async testing
   - Pydantic validation
   - Error handling
   - Performance testing

## Project Structure

The guides use examples from this real estate platform:

```
inmobiliario-tools/
├── backend/                 # FastAPI application
│   ├── main.py             # Application entry point
│   ├── app/
│   │   ├── routers/        # API routes
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic models
│   │   ├── core/           # Security, dependencies
│   │   └── services/       # Business logic
│   └── inmobiliario/       # Scrapy spiders
├── frontend/               # Next.js frontend
└── learning/              # This learning guide
```

## How to Use This Guide

### Option 1: Sequential Learning
Follow the guides in order from 1-9 for comprehensive coverage.

### Option 2: Topic-Focused
Jump to specific topics based on your needs:
- **API Development**: Guides 1-3
- **Database Work**: Guide 4
- **Security**: Guide 5
- **Advanced Features**: Guides 6-9

### Option 3: Project-Based
Use the real project to practice:
1. Clone and set up the project
2. Read the relevant guide
3. Experiment with the existing code
4. Complete the practice exercises

## Getting Started

### 1. Set Up the Project
```bash
# Clone the repository
git clone https://github.com/your-repo/inmobiliario-tools.git
cd inmobiliario-tools

# Create environment file
cp .env.example .env

# Start the development environment
docker compose up -d
```

### 2. Explore the API
- **API Documentation**: http://localhost:8001/docs
- **Alternative Docs**: http://localhost:8001/redoc
- **Frontend**: http://localhost:3000

### 3. Start Learning
Begin with **[FastAPI Basics](01-fastapi-basics.md)** and follow along with the running project.

## Code Examples

Each guide includes:
- ✅ **Real code** from the project
- ✅ **Working examples** you can test
- ✅ **Best practices** and patterns
- ✅ **Common pitfalls** to avoid
- ✅ **Practice exercises** for hands-on learning

## Key Features Covered

### 🔐 Authentication & Security
- JWT token authentication
- Password hashing with bcrypt
- Role-based access control
- Email confirmation system
- Security middleware

### 🗄️ Database Operations
- Async SQLAlchemy with PostgreSQL
- Complex queries and relationships
- Database migrations
- Performance optimization
- Connection pooling

### ⚡ Real-time Features
- WebSocket connections
- Live job monitoring
- Real-time notifications
- Connection management
- Broadcasting systems

### 🧪 Testing & Quality
- Comprehensive test suites
- Async testing patterns
- Validation with Pydantic
- Error handling strategies
- Performance testing

### 🚀 Production Ready
- Docker containerization
- Environment configuration
- Logging and monitoring
- CORS and security headers
- Background task processing

## Practice Projects

Build these features as you learn:

### Beginner Projects
1. **Property Favorites System** - Users can save favorite properties
2. **Basic Search API** - Search properties by location and price
3. **User Profile Management** - Update user information

### Intermediate Projects
1. **Property Comparison Tool** - Compare multiple properties
2. **Price Alert System** - Notify users of price changes
3. **Admin Dashboard** - Manage users and properties

### Advanced Projects
1. **Real-time Property Updates** - Live property data streaming
2. **Advanced Analytics API** - Complex property market analysis
3. **Multi-tenant System** - Support multiple real estate agencies

## Learning Resources

### Official Documentation
- **[FastAPI Documentation](https://fastapi.tiangolo.com/)**
- **[Pydantic Documentation](https://pydantic-docs.helpmanual.io/)**
- **[SQLAlchemy Documentation](https://docs.sqlalchemy.org/)**

### Video Tutorials
- FastAPI Tutorial Series on YouTube
- Real Python FastAPI Course
- TechWithTim FastAPI Playlist

### Books
- "FastAPI Web Development" by Bill Lubanovic
- "Building APIs with Python and FastAPI"

## Getting Help

### Common Issues
- **Database connection errors**: Check Docker containers are running
- **Authentication problems**: Verify JWT token format
- **CORS issues**: Check frontend/backend URL configuration
- **Import errors**: Ensure Python virtual environment is activated

### Community Support
- **Stack Overflow**: Tag your questions with `fastapi`
- **GitHub Issues**: Report bugs in the FastAPI repository  
- **Discord**: Join the FastAPI community server
- **Reddit**: r/FastAPI subreddit

## Contributing

Found an error or want to improve the guides?

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Submit a pull request**

## Next Steps

After completing this guide, you'll be able to:

- ✅ **Build production-ready APIs** with FastAPI
- ✅ **Implement authentication** and security features
- ✅ **Work with databases** efficiently using async operations
- ✅ **Create real-time applications** with WebSockets
- ✅ **Write comprehensive tests** for your applications
- ✅ **Deploy and scale** FastAPI applications

### Advanced Topics to Explore
- **Microservices architecture** with FastAPI
- **GraphQL integration** with Strawberry
- **Event-driven architecture** with message queues
- **API versioning** strategies
- **Performance optimization** and caching
- **Monitoring and observability** with OpenTelemetry

---

**Happy Learning!** 🚀

Start with **[FastAPI Basics](01-fastapi-basics.md)** and build your way up to creating sophisticated web APIs with FastAPI.