from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

class CrawlJobCreate(BaseModel):
    job_name: str
    spider_name: str
    start_urls: List[str]
    schedule_type: str = "manual"
    cron_expression: Optional[str] = None
    job_config: Dict[str, Any] = {}

class CrawlJobUpdate(BaseModel):
    job_name: Optional[str] = None
    start_urls: Optional[List[str]] = None
    schedule_type: Optional[str] = None
    cron_expression: Optional[str] = None
    job_config: Optional[Dict[str, Any]] = None

class CrawlJobResponse(BaseModel):
    job_id: int
    job_name: str
    spider_name: str
    start_urls: List[str]
    created_by: int
    status: str
    schedule_type: str
    cron_expression: Optional[str]
    job_config: Dict[str, Any]
    next_run: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True