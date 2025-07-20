from app.celery_app import celery_app
from app.models.audit_log import AuditLog
import asyncio
import asyncpg
import os
import json
from datetime import datetime

@celery_app.task
def log_audit_async(audit_data: dict):
    """
    Asynchronously log audit events without blocking API responses
    """
    try:
        asyncio.run(save_audit_log(audit_data))
    except Exception as e:
        # Log error but don't fail - audit logging shouldn't break the app
        print(f"Failed to log audit event: {e}")

async def save_audit_log(audit_data: dict):
    """
    Save audit log to database using direct asyncpg connection for speed
    """
    DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@postgres:5432/{os.getenv('POSTGRES_DB', 'inmobiliario_db')}"
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        await conn.execute("""
            INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details, ip_address, user_agent, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, 
            audit_data.get("user_id"),
            audit_data.get("action"),
            audit_data.get("resource_type"),
            audit_data.get("resource_id"),
            json.dumps(audit_data.get("details")) if audit_data.get("details") else None,
            audit_data.get("ip_address"),
            audit_data.get("user_agent"),
            datetime.utcnow()
        )
        
        await conn.close()
        
    except Exception as e:
        print(f"Error saving audit log: {e}")