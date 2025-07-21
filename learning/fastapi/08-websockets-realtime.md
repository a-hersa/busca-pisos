# FastAPI WebSockets and Real-time Communication

## What are WebSockets?

WebSockets provide full-duplex communication between client and server over a single TCP connection. Unlike HTTP requests, WebSockets maintain a persistent connection, enabling real-time bidirectional data exchange.

## WebSocket vs HTTP

| HTTP | WebSocket |
|------|-----------|
| Request-Response pattern | Full-duplex communication |
| Client initiates all communication | Both sides can send messages |
| New connection per request | Persistent connection |
| Higher latency for real-time apps | Low latency |
| Stateless | Stateful connection |

## Basic WebSocket Implementation

From our project's `backend/main.py`:

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json

app = FastAPI()

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """Basic WebSocket endpoint"""
    await websocket.accept()
    
    try:
        while True:
            # Wait for message from client
            data = await websocket.receive_text()
            
            # Echo back to client
            await websocket.send_text(f"Message received: {data}")
            
    except WebSocketDisconnect:
        print(f"User {user_id} disconnected")
```

## Connection Manager

From our project's `backend/app/websocket.py`:

```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Store active connections by user ID
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # Store user IDs by WebSocket for reverse lookup
        self.connection_user_map: Dict[WebSocket, int] = {}
        # Admin user IDs for broadcasting
        self.admin_users: Set[int] = set()
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept new WebSocket connection"""
        await websocket.accept()
        
        # Initialize user's connection list if needed
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        # Add connection
        self.active_connections[user_id].append(websocket)
        self.connection_user_map[websocket] = user_id
        
        logger.info(f"User {user_id} connected via WebSocket")
        
        # Send welcome message
        await self.send_personal_message(
            message=json.dumps({
                "type": "connection_established",
                "user_id": user_id,
                "message": "Connected to real-time updates"
            }),
            user_id=user_id
        )
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        """Remove WebSocket connection"""
        try:
            if user_id in self.active_connections:
                self.active_connections[user_id].remove(websocket)
                
                # Clean up empty lists
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            # Remove from reverse mapping
            if websocket in self.connection_user_map:
                del self.connection_user_map[websocket]
            
            logger.info(f"User {user_id} disconnected from WebSocket")
            
        except ValueError:
            # Connection was already removed
            pass
    
    async def send_personal_message(self, message: str, user_id: int):
        """Send message to all connections of a specific user"""
        if user_id in self.active_connections:
            # Get all connections for this user
            connections = self.active_connections[user_id][:]
            
            # Send to all connections (user might have multiple tabs/devices)
            failed_connections = []
            
            for connection in connections:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.warning(f"Failed to send message to user {user_id}: {e}")
                    failed_connections.append(connection)
            
            # Clean up failed connections
            for failed_conn in failed_connections:
                self.disconnect(failed_conn, user_id)
    
    async def send_personal_json(self, data: dict, user_id: int):
        """Send JSON data to specific user"""
        await self.send_personal_message(json.dumps(data), user_id)
    
    async def broadcast_to_all(self, message: str):
        """Broadcast message to all connected users"""
        if not self.active_connections:
            return
        
        # Collect all connections
        all_connections = []
        for connections in self.active_connections.values():
            all_connections.extend(connections)
        
        # Send to all connections
        await self._send_to_connections(all_connections, message)
    
    async def broadcast_to_admins(self, message: str):
        """Broadcast message only to admin users"""
        admin_connections = []
        
        for user_id in self.admin_users:
            if user_id in self.active_connections:
                admin_connections.extend(self.active_connections[user_id])
        
        if admin_connections:
            await self._send_to_connections(admin_connections, message)
    
    async def _send_to_connections(self, connections: List[WebSocket], message: str):
        """Helper method to send message to multiple connections"""
        if not connections:
            return
        
        # Send concurrently to all connections
        tasks = []
        for connection in connections:
            tasks.append(self._safe_send(connection, message))
        
        # Wait for all sends to complete
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _safe_send(self, connection: WebSocket, message: str):
        """Safely send message to a connection"""
        try:
            await connection.send_text(message)
        except Exception as e:
            # Connection failed, will be cleaned up in disconnect()
            logger.warning(f"Failed to send to connection: {e}")
    
    def get_user_count(self) -> int:
        """Get number of connected users"""
        return len(self.active_connections)
    
    def get_connection_count(self) -> int:
        """Get total number of connections"""
        return sum(len(connections) for connections in self.active_connections.values())
    
    def is_user_connected(self, user_id: int) -> bool:
        """Check if user has active connections"""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0

# Global connection manager instance
manager = ConnectionManager()
```

## Enhanced WebSocket Endpoint

```python
from app.websocket import manager
from app.core.deps import get_current_user_from_token
from app.models.user import User

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """Enhanced WebSocket endpoint with authentication and message handling"""
    
    # Optional: Authenticate WebSocket connection
    # In production, you'd verify the user_id against a token
    
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                # Parse JSON message
                message_data = json.loads(data)
                message_type = message_data.get("type")
                
                # Handle different message types
                if message_type == "ping":
                    # Heartbeat/keepalive
                    await manager.send_personal_json({
                        "type": "pong",
                        "timestamp": time.time()
                    }, user_id)
                
                elif message_type == "subscribe":
                    # Subscribe to specific updates
                    subscription = message_data.get("subscription")
                    await handle_subscription(user_id, subscription)
                
                elif message_type == "request_status":
                    # Send current status
                    await send_current_status(user_id)
                
                else:
                    # Unknown message type
                    await manager.send_personal_json({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    }, user_id)
                    
            except json.JSONDecodeError:
                # Invalid JSON
                await manager.send_personal_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                }, user_id)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

async def handle_subscription(user_id: int, subscription: str):
    """Handle subscription requests"""
    valid_subscriptions = ["job_updates", "property_updates", "system_alerts"]
    
    if subscription in valid_subscriptions:
        # In a real app, you'd store subscriptions in database or memory
        await manager.send_personal_json({
            "type": "subscription_confirmed",
            "subscription": subscription
        }, user_id)
    else:
        await manager.send_personal_json({
            "type": "subscription_error",
            "message": f"Invalid subscription: {subscription}"
        }, user_id)

async def send_current_status(user_id: int):
    """Send current system status to user"""
    # This would typically fetch from database
    status_data = {
        "type": "status_update",
        "active_jobs": 3,
        "total_properties": 15420,
        "server_time": time.time(),
        "user_connections": manager.get_connection_count()
    }
    
    await manager.send_personal_json(status_data, user_id)
```

## Real-time Job Updates

From our project's job management integration:

```python
# In services/job_runner.py
from app.websocket import manager
from app.models.crawl_job import CrawlJob, JobExecution

class JobUpdateNotifier:
    @staticmethod
    async def notify_job_started(job_id: int, user_id: int):
        """Notify when job starts"""
        await manager.send_personal_json({
            "type": "job_update",
            "event": "job_started",
            "job_id": job_id,
            "timestamp": time.time()
        }, user_id)
    
    @staticmethod
    async def notify_job_progress(job_id: int, user_id: int, items_scraped: int, status: str):
        """Notify job progress updates"""
        await manager.send_personal_json({
            "type": "job_update",
            "event": "job_progress",
            "job_id": job_id,
            "items_scraped": items_scraped,
            "status": status,
            "timestamp": time.time()
        }, user_id)
    
    @staticmethod
    async def notify_job_completed(job_id: int, user_id: int, total_items: int):
        """Notify when job completes"""
        await manager.send_personal_json({
            "type": "job_update",
            "event": "job_completed",
            "job_id": job_id,
            "total_items": total_items,
            "timestamp": time.time()
        }, user_id)
    
    @staticmethod
    async def notify_job_failed(job_id: int, user_id: int, error_message: str):
        """Notify when job fails"""
        await manager.send_personal_json({
            "type": "job_update",
            "event": "job_failed",
            "job_id": job_id,
            "error": error_message,
            "timestamp": time.time()
        }, user_id)

# Usage in Celery tasks
from app.tasks.scrapy_runner import celery_app

@celery_app.task
def run_spider_task(spider_name: str, job_id: int, target_urls: list):
    """Celery task that sends WebSocket updates"""
    
    # Get job details
    with get_db_session() as session:
        job = session.query(CrawlJob).filter(CrawlJob.job_id == job_id).first()
        user_id = job.created_by
    
    # Send start notification
    asyncio.run(JobUpdateNotifier.notify_job_started(job_id, user_id))
    
    try:
        # Run spider
        items_scraped = 0
        for item in run_scrapy_spider(spider_name, target_urls):
            items_scraped += 1
            
            # Send progress updates every 10 items
            if items_scraped % 10 == 0:
                asyncio.run(JobUpdateNotifier.notify_job_progress(
                    job_id, user_id, items_scraped, "running"
                ))
        
        # Send completion notification
        asyncio.run(JobUpdateNotifier.notify_job_completed(job_id, user_id, items_scraped))
        
    except Exception as e:
        # Send error notification
        asyncio.run(JobUpdateNotifier.notify_job_failed(job_id, user_id, str(e)))
```

## WebSocket Authentication

```python
from jose import jwt, JWTError
from app.core.security import SECRET_KEY, ALGORITHM

async def authenticate_websocket(websocket: WebSocket) -> Optional[User]:
    """Authenticate WebSocket connection using query parameter token"""
    
    # Get token from query parameters
    token = websocket.query_params.get("token")
    
    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        return None
    
    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            await websocket.close(code=1008, reason="Invalid token")
            return None
        
        # Get user from database
        async with get_async_session() as session:
            result = await session.execute(
                select(User).where(User.username == username)
            )
            user = result.scalar_one_or_none()
            
            if user is None or not user.is_active:
                await websocket.close(code=1008, reason="User not found or inactive")
                return None
            
            return user
            
    except JWTError:
        await websocket.close(code=1008, reason="Invalid token")
        return None

@app.websocket("/ws/authenticated")
async def authenticated_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint with authentication"""
    
    # Authenticate before accepting connection
    user = await authenticate_websocket(websocket)
    if not user:
        return  # Connection already closed in authenticate_websocket
    
    await manager.connect(websocket, user.user_id)
    
    # Mark admin users
    if user.role == "admin":
        manager.admin_users.add(user.user_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            # Handle authenticated user messages
            await handle_authenticated_message(user, data)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user.user_id)
        if user.role == "admin":
            manager.admin_users.discard(user.user_id)
```

## Broadcasting System Messages

```python
class SystemNotifier:
    @staticmethod
    async def broadcast_system_maintenance(message: str, start_time: str):
        """Broadcast system maintenance notification"""
        await manager.broadcast_to_all(json.dumps({
            "type": "system_notification",
            "category": "maintenance",
            "message": message,
            "start_time": start_time,
            "timestamp": time.time()
        }))
    
    @staticmethod
    async def notify_new_properties(count: int, location: str):
        """Notify about new properties found"""
        await manager.broadcast_to_all(json.dumps({
            "type": "property_notification",
            "event": "new_properties",
            "count": count,
            "location": location,
            "timestamp": time.time()
        }))
    
    @staticmethod
    async def notify_admins_only(message: str, category: str = "admin"):
        """Send notification only to admin users"""
        await manager.broadcast_to_admins(json.dumps({
            "type": "admin_notification",
            "category": category,
            "message": message,
            "timestamp": time.time()
        }))

# Usage in routes or background tasks
@router.post("/admin/broadcast")
async def broadcast_message(
    message: str,
    category: str = "general",
    admin_user: User = Depends(get_admin_user)
):
    """Admin endpoint to broadcast messages"""
    
    await SystemNotifier.broadcast_system_maintenance(
        message=message,
        start_time=datetime.utcnow().isoformat()
    )
    
    return {"message": "Broadcast sent successfully"}
```

## Client-Side WebSocket Implementation

Frontend JavaScript example:

```javascript
class WebSocketManager {
    constructor(userId, token) {
        this.userId = userId;
        this.token = token;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second
        this.messageHandlers = new Map();
    }
    
    connect() {
        const wsUrl = `ws://localhost:8001/ws/${this.userId}?token=${this.token}`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = (event) => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                this.reconnectDelay = 1000;
                this.onConnected();
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error);
                }
            };
            
            this.ws.onclose = (event) => {
                console.log('WebSocket disconnected:', event.code, event.reason);
                this.onDisconnected();
                this.attemptReconnect();
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
            
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.attemptReconnect();
        }
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close(1000, 'Client disconnect');
            this.ws = null;
        }
    }
    
    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            console.warn('WebSocket not connected, message not sent:', message);
        }
    }
    
    // Subscribe to specific message types
    onMessage(type, handler) {
        if (!this.messageHandlers.has(type)) {
            this.messageHandlers.set(type, []);
        }
        this.messageHandlers.get(type).push(handler);
    }
    
    handleMessage(data) {
        const type = data.type;
        
        if (this.messageHandlers.has(type)) {
            const handlers = this.messageHandlers.get(type);
            handlers.forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in message handler for type ${type}:`, error);
                }
            });
        }
        
        // Built-in handlers
        switch (type) {
            case 'job_update':
                this.handleJobUpdate(data);
                break;
            case 'system_notification':
                this.handleSystemNotification(data);
                break;
            case 'property_notification':
                this.handlePropertyNotification(data);
                break;
        }
    }
    
    handleJobUpdate(data) {
        // Update job status in UI
        const jobCard = document.querySelector(`[data-job-id="${data.job_id}"]`);
        if (jobCard) {
            const statusElement = jobCard.querySelector('.job-status');
            if (statusElement) {
                statusElement.textContent = data.event;
                statusElement.className = `job-status status-${data.event.replace('_', '-')}`;
            }
            
            if (data.items_scraped) {
                const itemsElement = jobCard.querySelector('.items-scraped');
                if (itemsElement) {
                    itemsElement.textContent = data.items_scraped;
                }
            }
        }
    }
    
    handleSystemNotification(data) {
        // Show toast notification
        showToast(data.message, data.category);
    }
    
    handlePropertyNotification(data) {
        if (data.event === 'new_properties') {
            showToast(`${data.count} new properties found in ${data.location}`, 'info');
            // Optionally refresh property list
            if (typeof refreshPropertyList === 'function') {
                refreshPropertyList();
            }
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            return;
        }
        
        this.reconnectAttempts++;
        console.log(`Attempting reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts}...`);
        
        setTimeout(() => {
            this.connect();
        }, this.reconnectDelay);
        
        // Exponential backoff
        this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000); // Max 30 seconds
    }
    
    onConnected() {
        // Send ping to keep connection alive
        this.pingInterval = setInterval(() => {
            this.send({ type: 'ping' });
        }, 30000); // Ping every 30 seconds
    }
    
    onDisconnected() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    }
}

// Usage in React component or vanilla JS
const wsManager = new WebSocketManager(userId, authToken);

// Set up message handlers
wsManager.onMessage('job_update', (data) => {
    console.log('Job update received:', data);
    updateJobInUI(data);
});

wsManager.onMessage('system_notification', (data) => {
    showSystemAlert(data.message, data.category);
});

// Connect
wsManager.connect();

// Subscribe to job updates
wsManager.send({
    type: 'subscribe',
    subscription: 'job_updates'
});
```

## Testing WebSockets

```python
import pytest
from fastapi.testclient import TestClient
import json

def test_websocket_connection():
    """Test basic WebSocket connection"""
    with TestClient(app).websocket_connect("/ws/1") as websocket:
        # Send test message
        websocket.send_text("Hello WebSocket")
        
        # Receive response
        data = websocket.receive_text()
        assert "Message received: Hello WebSocket" in data

def test_websocket_json_messages():
    """Test JSON message handling"""
    with TestClient(app).websocket_connect("/ws/1") as websocket:
        # Send JSON message
        test_message = {"type": "ping", "data": "test"}
        websocket.send_text(json.dumps(test_message))
        
        # Receive JSON response
        response = json.loads(websocket.receive_text())
        assert response["type"] == "pong"

@pytest.mark.asyncio
async def test_connection_manager():
    """Test connection manager functionality"""
    from app.websocket import ConnectionManager
    
    manager = ConnectionManager()
    
    # Test connection counting
    assert manager.get_user_count() == 0
    assert manager.get_connection_count() == 0
    
    # Test user connection status
    assert not manager.is_user_connected(1)

def test_websocket_authentication():
    """Test WebSocket authentication"""
    # Valid token
    valid_token = create_access_token(data={"sub": "testuser"})
    
    with TestClient(app).websocket_connect(f"/ws/authenticated?token={valid_token}") as websocket:
        websocket.send_text("authenticated message")
        response = websocket.receive_text()
        assert response  # Should receive response
    
    # Invalid token - should close connection
    with pytest.raises(WebSocketDisconnect):
        with TestClient(app).websocket_connect("/ws/authenticated?token=invalid") as websocket:
            pass  # Connection should be closed immediately
```

## Performance and Scaling Considerations

### 1. Connection Limits
```python
class ConnectionManager:
    def __init__(self, max_connections_per_user: int = 5):
        self.max_connections_per_user = max_connections_per_user
        # ... rest of initialization
    
    async def connect(self, websocket: WebSocket, user_id: int):
        # Check connection limit
        if user_id in self.active_connections:
            if len(self.active_connections[user_id]) >= self.max_connections_per_user:
                await websocket.close(code=1008, reason="Too many connections")
                return
        
        # Proceed with connection
        await websocket.accept()
        # ... rest of connect logic
```

### 2. Memory Management
```python
import asyncio
from collections import defaultdict
import time

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.connection_metadata: Dict[WebSocket, dict] = {}
        self.cleanup_task = None
    
    async def start_cleanup_task(self):
        """Start background task to clean up stale connections"""
        if not self.cleanup_task:
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self):
        """Periodically clean up stale connections"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                await self._cleanup_stale_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def _cleanup_stale_connections(self):
        """Remove connections that haven't been active"""
        current_time = time.time()
        stale_connections = []
        
        for connection, metadata in self.connection_metadata.items():
            last_activity = metadata.get('last_activity', 0)
            if current_time - last_activity > 300:  # 5 minutes
                stale_connections.append(connection)
        
        # Clean up stale connections
        for connection in stale_connections:
            user_id = self.connection_user_map.get(connection)
            if user_id:
                self.disconnect(connection, user_id)
```

## Best Practices

1. **Handle disconnections gracefully** - Always clean up resources
2. **Implement heartbeat/ping-pong** - Detect dead connections
3. **Limit connections per user** - Prevent resource exhaustion
4. **Authenticate WebSocket connections** - Secure your real-time features
5. **Use message queues for scaling** - Redis pub/sub for multi-server setups
6. **Handle exceptions in message handlers** - Don't crash the WebSocket
7. **Implement proper reconnection logic** - Handle network issues
8. **Monitor connection metrics** - Track active connections and performance

## Practice Exercises

1. **Create a chat system** with rooms and message broadcasting
2. **Implement live property price updates** when new data arrives
3. **Build a collaborative filtering system** where users can see what others are viewing
4. **Create real-time dashboard** with live metrics and charts

## Next Steps

In the final guide, we'll explore:
- Testing FastAPI applications
- Validation with Pydantic models
- Error handling and debugging techniques