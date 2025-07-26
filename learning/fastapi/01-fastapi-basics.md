# FastAPI Basics - Getting Started

## What is FastAPI?

FastAPI is a modern, fast (high-performance) web framework for building APIs with Python 3.7+ based on standard Python type hints. It's designed to be easy to use and learn while being production-ready.

## Key Features

- **Fast**: Very high performance, on par with NodeJS and Go
- **Fast to code**: Increase development speed by 200% to 300%
- **Fewer bugs**: Reduce about 40% of human-induced errors
- **Intuitive**: Great editor support with auto-completion
- **Easy**: Designed to be easy to use and learn
- **Short**: Minimize code duplication
- **Robust**: Get production-ready code with automatic interactive API documentation

## Project Structure Overview

Let's look at how FastAPI is organized in our busca-pisos project:

```
backend/
├── main.py              # Application entry point
├── app/
│   ├── __init__.py
│   ├── database.py      # Database configuration
│   ├── models/          # SQLAlchemy models
│   ├── routers/         # API route handlers
│   ├── schemas/         # Pydantic models for validation
│   ├── core/            # Core functionality (deps, security)
│   ├── services/        # Business logic
│   └── middleware/      # Custom middleware
└── requirements.txt     # Dependencies
```

## Basic FastAPI Application

Here's how our main application is structured in `backend/main.py`:

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Lifespan management - runs during startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()  # Initialize database
    yield
    # Shutdown
    pass

# Create FastAPI application instance
app = FastAPI(
    title="Inmobiliario Tools API",
    description="Backend API for property analysis and crawl job management",
    version="2.0.0",
    lifespan=lifespan
)

# Add middleware for CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic route
@app.get("/")
async def root():
    return {"message": "Inmobiliario Tools API", "version": "2.0.0"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

## Key Concepts Explained

### 1. Application Instance
```python
app = FastAPI(title="My API", version="1.0.0")
```
Creates the main FastAPI application with metadata for automatic documentation.

### 2. Route Decorators
```python
@app.get("/")          # GET request
@app.post("/items")    # POST request
@app.put("/items/{id}") # PUT request with path parameter
@app.delete("/items/{id}") # DELETE request
```

### 3. Async Support
FastAPI is built with async/await support:
```python
@app.get("/async-endpoint")
async def async_function():
    # Can use await here
    result = await some_async_operation()
    return result
```

### 4. Automatic Documentation
FastAPI automatically generates:
- **Swagger UI**: Available at `/docs`
- **ReDoc**: Available at `/redoc`
- **OpenAPI Schema**: Available at `/openapi.json`

## Running the Application

In our project, the application runs through Docker, but you can also run it directly:

```bash
# Install dependencies
pip install -r requirements.txt

# Run with uvicorn (ASGI server)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Environment and Configuration

Our project uses environment variables for configuration:

```python
import os
from dotenv import load_dotenv

load_dotenv()  # Load .env file

# Access environment variables
database_url = os.getenv("DATABASE_URL")
secret_key = os.getenv("SECRET_KEY")
```

## Next Steps

In the next guides, we'll cover:
- Creating API routes and handling requests
- Request/response models with Pydantic
- Database integration with SQLAlchemy
- Authentication and security
- Dependency injection system

## Practice Exercise

Try modifying the basic route in `main.py`:
1. Add a new GET endpoint `/api/info` that returns project information
2. Add query parameters to filter the response
3. Visit `/docs` to see your changes in the interactive documentation