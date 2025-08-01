from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from app.database import init_db
from app.routers import auth, users, jobs, properties, admin
from app.websocket import manager
from app.core.deps import get_current_user
from app.models.user import User
from app.middleware.cache_middleware import CacheMiddleware

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    pass

app = FastAPI(
    title="Inmobiliario Tools API",
    description="Backend API for property analysis and crawl job management",
    version="2.0.0",
    lifespan=lifespan
)

# Add middlewares
app.add_middleware(CacheMiddleware, cache_ttl=300)  # 5 minutes cache

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["crawl-jobs"])
app.include_router(properties.router, prefix="/api/properties", tags=["properties"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

# Import and include additional routers
from app.routers import export, analytics
app.include_router(export.router, prefix="/api/export", tags=["export"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """
    WebSocket endpoint for real-time job monitoring
    Note: In production, you'd want to validate the user_id against the JWT token
    """
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()
            # Echo back for connection testing
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

@app.get("/")
async def root():
    return {"message": "Inmobiliario Tools API", "version": "2.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/debug-auth")
async def debug_auth():
    """Debug endpoint to check current auth status"""
    from app.core.deps import get_current_user
    from app.database import get_async_session
    from fastapi import Depends
    
    try:
        # This will require auth, which is what we want to test
        current_user = Depends(get_current_user)
        session = Depends(get_async_session)
        return {"message": "This endpoint requires auth - if you see this, auth is working"}
    except Exception as e:
        return {"error": str(e), "message": "Auth not working"}