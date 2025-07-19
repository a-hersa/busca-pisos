from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from app.database import Base

class CrawlJob(Base):
    __tablename__ = "crawl_jobs"
    
    job_id = Column(Integer, primary_key=True, index=True)
    job_name = Column(String(100), nullable=False)
    spider_name = Column(String(50), nullable=False)
    start_urls = Column(ARRAY(Text), nullable=False)
    created_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    schedule_type = Column(String(20), default="manual", nullable=False)
    cron_expression = Column(String(100))
    job_config = Column(JSONB, default={})
    next_run = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    created_by_user = relationship("User", back_populates="crawl_jobs")
    executions = relationship("JobExecution", back_populates="job", cascade="all, delete-orphan")

class JobExecution(Base):
    __tablename__ = "job_executions"
    
    execution_id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("crawl_jobs.job_id"), nullable=False)
    status = Column(String(20), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    items_scraped = Column(Integer, default=0)
    error_message = Column(Text)
    execution_log = Column(JSONB, default={})
    celery_task_id = Column(String(255))
    
    # Relationships
    job = relationship("CrawlJob", back_populates="executions")