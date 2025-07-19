from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio
from datetime import datetime

class ConnectionManager:
    """
    Manages WebSocket connections for real-time job monitoring
    """
    
    def __init__(self):
        # Store connections by user_id
        self.active_connections: Dict[int, List[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        
    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def send_personal_message(self, message: dict, user_id: int):
        """
        Send message to all connections for a specific user
        """
        if user_id in self.active_connections:
            message_str = json.dumps({
                **message,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Send to all user's connections
            disconnected = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message_str)
                except:
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for conn in disconnected:
                self.active_connections[user_id].remove(conn)
    
    async def broadcast_to_admins(self, message: dict, admin_user_ids: List[int]):
        """
        Broadcast message to all admin users
        """
        for admin_id in admin_user_ids:
            await self.send_personal_message(message, admin_id)

# Global connection manager instance
manager = ConnectionManager()

async def send_job_update(user_id: int, job_id: int, status: str, details: dict = None):
    """
    Send job status update to user via WebSocket
    """
    message = {
        "type": "job_update",
        "job_id": job_id,
        "status": status,
        "details": details or {}
    }
    await manager.send_personal_message(message, user_id)

async def send_job_progress(user_id: int, job_id: int, progress: dict):
    """
    Send job progress update to user via WebSocket
    """
    message = {
        "type": "job_progress",
        "job_id": job_id,
        "progress": progress
    }
    await manager.send_personal_message(message, user_id)