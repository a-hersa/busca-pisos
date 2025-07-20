from celery import current_task
from app.celery_app import celery_app
import subprocess
import sys
import os
import json
from datetime import datetime
import asyncio
import asyncpg
from typing import Dict, Any

@celery_app.task(bind=True)
def run_spider(self, job_id: int, spider_name: str, start_urls: list, job_config: Dict[str, Any]):
    """
    Run a Scrapy spider as a Celery task
    """
    try:
        # Update job execution status to running
        asyncio.run(update_job_execution_status(job_id, "running", self.request.id))
        
        # Build scrapy command
        scrapy_cmd = [
            sys.executable, "-m", "scrapy", "crawl", spider_name,
            "-s", f"START_URLS={'|||'.join(start_urls)}",
            "-s", f"JOB_ID={job_id}",
            "-s", f"JOB_CONFIG={json.dumps(job_config)}"
        ]
        
        # Set working directory to scrapy project (now integrated in backend)
        scrapy_project_dir = "/app/inmobiliario"
        
        # Update task progress
        self.update_state(
            state="PROGRESS",
            meta={"status": "Starting spider", "spider": spider_name, "urls_count": len(start_urls)}
        )
        
        # Run the spider
        result = subprocess.run(
            scrapy_cmd,
            cwd=scrapy_project_dir,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        if result.returncode == 0:
            # Parse output for scraped items count
            items_scraped = parse_scrapy_output(result.stdout)
            
            # Update job execution status to completed
            asyncio.run(update_job_execution_status(
                job_id, "completed", self.request.id, 
                items_scraped=items_scraped,
                execution_log={"stdout": result.stdout, "stderr": result.stderr}
            ))
            
            # Send completion notification
            from app.services.notifications import notification_manager
            asyncio.run(notification_manager.notify_job_completion(
                job_id, "completed", items_scraped
            ))
            
            return {
                "status": "completed",
                "items_scraped": items_scraped,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        else:
            # Update job execution status to failed
            error_message = f"Spider failed with exit code {result.returncode}: {result.stderr}"
            asyncio.run(update_job_execution_status(
                job_id, "failed", self.request.id,
                error_message=error_message,
                execution_log={"stdout": result.stdout, "stderr": result.stderr}
            ))
            
            # Send failure notification
            from app.services.notifications import notification_manager
            asyncio.run(notification_manager.notify_job_completion(
                job_id, "failed", 0, error_message
            ))
            
            raise Exception(error_message)
            
    except subprocess.TimeoutExpired:
        error_message = "Spider execution timed out"
        asyncio.run(update_job_execution_status(
            job_id, "failed", self.request.id, error_message=error_message
        ))
        raise Exception(error_message)
        
    except Exception as e:
        error_message = str(e)
        asyncio.run(update_job_execution_status(
            job_id, "failed", self.request.id, error_message=error_message
        ))
        raise

def parse_scrapy_output(output: str) -> int:
    """
    Parse Scrapy output to extract the number of scraped items
    """
    lines = output.split('\n')
    for line in lines:
        if 'item_scraped_count' in line:
            try:
                # Extract number from scrapy stats - handle different formats
                if ':' in line:
                    parts = line.split(':')
                    if len(parts) > 1:
                        # Handle format like "'item_scraped_count': 8,"
                        value_part = parts[-1].strip().rstrip(',').strip()
                        return int(value_part)
            except (ValueError, IndexError):
                continue
    return 0

async def update_job_execution_status(
    job_id: int, 
    status: str, 
    celery_task_id: str,
    items_scraped: int = 0,
    error_message: str = None,
    execution_log: Dict = None
):
    """
    Update job execution status in the database
    """
    DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@postgres:5432/{os.getenv('POSTGRES_DB', 'inmobiliario_db')}"
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        if status == "running":
            # Create new job execution record
            await conn.execute("""
                INSERT INTO job_executions (job_id, status, celery_task_id)
                VALUES ($1, $2, $3)
            """, job_id, status, celery_task_id)
            
            # Update job status
            await conn.execute("""
                UPDATE crawl_jobs SET status = $1 WHERE job_id = $2
            """, status, job_id)
            
        else:
            # Update existing execution record
            await conn.execute("""
                UPDATE job_executions 
                SET status = $1, completed_at = $2, items_scraped = $3, 
                    error_message = $4, execution_log = $5
                WHERE job_id = $6 AND celery_task_id = $7
            """, status, datetime.utcnow(), items_scraped, error_message, 
                json.dumps(execution_log) if execution_log else None, job_id, celery_task_id)
            
            # Update job status
            await conn.execute("""
                UPDATE crawl_jobs SET status = $1 WHERE job_id = $2
            """, status, job_id)
        
        await conn.close()
        
    except Exception as e:
        print(f"Error updating job execution status: {e}")
        # Don't raise here to avoid breaking the main task