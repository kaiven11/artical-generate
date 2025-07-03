"""
Task model for managing processing tasks.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any

from ..core.database import Base


class TaskType(str, Enum):
    """Task types."""
    EXTRACT = "extract"          # Content extraction
    TRANSLATE = "translate"      # Translation
    OPTIMIZE = "optimize"        # Content optimization
    DETECT = "detect"           # Detection (originality/AI)
    PUBLISH = "publish"         # Publishing
    BACKUP = "backup"           # Backup operations


class TaskStatus(str, Enum):
    """Task status."""
    PENDING = "pending"         # Waiting to be processed
    RUNNING = "running"         # Currently being processed
    COMPLETED = "completed"     # Successfully completed
    FAILED = "failed"          # Failed with error
    CANCELLED = "cancelled"    # Cancelled by user
    RETRYING = "retrying"      # Retrying after failure


class TaskPriority(int, Enum):
    """Task priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class Task(Base):
    """Task model for managing processing tasks."""
    
    __tablename__ = "tasks"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Task identification
    task_id = Column(String(100), unique=True, nullable=False, index=True)  # UUID
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Task type and priority
    type = Column(String(50), nullable=False, index=True)
    priority = Column(Integer, default=TaskPriority.NORMAL, index=True)
    
    # Task status
    status = Column(String(20), default=TaskStatus.PENDING, index=True)
    progress = Column(Float, default=0.0)  # Progress percentage (0-100)
    
    # Related article
    article_id = Column(Integer, ForeignKey("articles.id"), index=True)
    
    # Task parameters and results
    parameters = Column(JSON)  # Input parameters
    result = Column(JSON)      # Task result
    
    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Timing information
    estimated_duration = Column(Float)  # Estimated duration in seconds
    actual_duration = Column(Float)     # Actual duration in seconds
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Worker information
    worker_id = Column(String(100))  # ID of worker processing the task
    
    # Dependencies
    depends_on = Column(JSON)  # List of task IDs this task depends on
    
    # Relationship
    article = relationship("Article", back_populates="tasks")
    
    def __repr__(self):
        return f"<Task(id={self.id}, task_id='{self.task_id}', type='{self.type}', status='{self.status}')>"
    
    @property
    def is_pending(self) -> bool:
        """Check if task is pending."""
        return self.status == TaskStatus.PENDING
    
    @property
    def is_running(self) -> bool:
        """Check if task is running."""
        return self.status == TaskStatus.RUNNING
    
    @property
    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.status == TaskStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Check if task failed."""
        return self.status == TaskStatus.FAILED
    
    @property
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.is_failed and self.retry_count < self.max_retries
    
    def start_task(self, worker_id: Optional[str] = None):
        """Mark task as started."""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.worker_id = worker_id
        self.updated_at = datetime.utcnow()
    
    def complete_task(self, result: Optional[Dict] = None):
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.progress = 100.0
        
        if result:
            self.result = result
        
        # Calculate actual duration
        if self.started_at:
            duration = (self.completed_at - self.started_at).total_seconds()
            self.actual_duration = duration
        
        self.updated_at = datetime.utcnow()
    
    def fail_task(self, error_message: str, can_retry: bool = True):
        """Mark task as failed."""
        self.error_message = error_message
        self.updated_at = datetime.utcnow()
        
        if can_retry and self.retry_count < self.max_retries:
            self.status = TaskStatus.RETRYING
            self.retry_count += 1
        else:
            self.status = TaskStatus.FAILED
            self.completed_at = datetime.utcnow()
    
    def cancel_task(self):
        """Cancel task."""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def update_progress(self, progress: float):
        """Update task progress."""
        self.progress = max(0.0, min(100.0, progress))
        self.updated_at = datetime.utcnow()
    
    def get_duration(self) -> Optional[float]:
        """Get task duration in seconds."""
        if self.actual_duration:
            return self.actual_duration
        elif self.started_at:
            if self.completed_at:
                return (self.completed_at - self.started_at).total_seconds()
            else:
                return (datetime.utcnow() - self.started_at).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "priority": self.priority,
            "status": self.status,
            "progress": self.progress,
            "article_id": self.article_id,
            "parameters": self.parameters,
            "result": self.result,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "estimated_duration": self.estimated_duration,
            "actual_duration": self.actual_duration,
            "duration": self.get_duration(),
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "updated_at": self.updated_at.isoformat(),
            "worker_id": self.worker_id,
            "depends_on": self.depends_on,
        }


# Add relationship to Article model
from .article import Article
Article.tasks = relationship("Task", back_populates="article")
