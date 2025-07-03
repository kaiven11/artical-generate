"""
Article model for storing article data and processing status.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON
from sqlalchemy.sql import func
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any

from ..core.database import Base


class ArticleStatus(str, Enum):
    """Article processing status."""
    PENDING = "pending"          # 待处理
    EXTRACTING = "extracting"    # 内容提取中
    EXTRACTED = "extracted"      # 已提取
    TRANSLATING = "translating"  # 翻译中
    TRANSLATED = "translated"    # 已翻译
    OPTIMIZING = "optimizing"    # 优化中
    OPTIMIZED = "optimized"      # 已优化
    DETECTING = "detecting"      # 检测中
    DETECTED = "detected"        # 已检测
    PUBLISHING = "publishing"    # 发布中
    PUBLISHED = "published"      # 已发布
    FAILED = "failed"           # 失败
    CANCELLED = "cancelled"     # 已取消


class Article(Base):
    """Article model for storing article data."""
    
    __tablename__ = "articles"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic information
    title = Column(String(500), nullable=False, index=True)
    source_url = Column(String(1000), nullable=False, unique=True)
    source_platform = Column(String(50), nullable=False, index=True)
    author = Column(String(200))
    publish_date = Column(DateTime)
    
    # Content versions
    content_original = Column(Text, nullable=False)  # Original content
    content_translated = Column(Text)                # Translated content
    content_optimized = Column(Text)                 # Optimized content
    content_final = Column(Text)                     # Final content for publishing
    
    # Processing status
    status = Column(String(20), default=ArticleStatus.PENDING, index=True)
    
    # Quality metrics
    originality_score = Column(Float)                # Originality detection score
    ai_detection_score = Column(Float)               # AI detection score
    quality_score = Column(Float)                    # Overall quality score
    
    # Processing metadata
    processing_attempts = Column(Integer, default=0)
    last_error = Column(Text)
    
    # Content metadata
    word_count = Column(Integer)
    estimated_reading_time = Column(Integer)         # In minutes
    tags = Column(JSON)                              # List of tags
    category = Column(String(100))
    
    # URL and content hashes for deduplication
    url_hash = Column(String(64), unique=True, index=True)
    content_hash = Column(String(64), index=True)
    
    # Publishing information
    published_url = Column(String(1000))
    published_platform = Column(String(50))
    published_at = Column(DateTime)
    
    # Creation type and topic-based creation fields
    creation_type = Column(String(20), default="url_import", index=True)  # url_import, topic_creation
    topic = Column(String(500))  # 创作主题
    keywords = Column(JSON)  # 关键词列表
    selected_creation_prompt_id = Column(Integer)  # 选择的创作提示词ID
    selected_model_id = Column(Integer)  # 选择的模型ID
    creation_requirements = Column(Text)  # 创作要求描述
    target_length = Column(String(20), default="medium")  # 目标长度: mini, short, medium, long
    writing_style = Column(String(100))  # 写作风格

    # Flags
    is_featured = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title[:50]}...', status='{self.status}')>"
    
    @property
    def is_processing(self) -> bool:
        """Check if article is currently being processed."""
        processing_statuses = [
            ArticleStatus.EXTRACTING,
            ArticleStatus.TRANSLATING,
            ArticleStatus.OPTIMIZING,
            ArticleStatus.DETECTING,
            ArticleStatus.PUBLISHING
        ]
        return self.status in processing_statuses
    
    @property
    def is_completed(self) -> bool:
        """Check if article processing is completed."""
        return self.status == ArticleStatus.PUBLISHED
    
    @property
    def is_failed(self) -> bool:
        """Check if article processing failed."""
        return self.status in [ArticleStatus.FAILED, ArticleStatus.CANCELLED]
    
    def get_current_content(self) -> str:
        """Get the most recent version of content based on status."""
        if self.content_final:
            return self.content_final
        elif self.content_optimized:
            return self.content_optimized
        elif self.content_translated:
            return self.content_translated
        else:
            return self.content_original
    
    def update_status(self, new_status: ArticleStatus, error_message: Optional[str] = None):
        """Update article status and handle error tracking."""
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        if new_status == ArticleStatus.FAILED and error_message:
            self.last_error = error_message
            self.processing_attempts += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert article to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "source_url": self.source_url,
            "source_platform": self.source_platform,
            "author": self.author,
            "publish_date": self.publish_date.isoformat() if self.publish_date else None,
            "status": self.status,
            "originality_score": self.originality_score,
            "ai_detection_score": self.ai_detection_score,
            "quality_score": self.quality_score,
            "word_count": self.word_count,
            "estimated_reading_time": self.estimated_reading_time,
            "tags": self.tags,
            "category": self.category,
            "published_url": self.published_url,
            "published_platform": self.published_platform,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "is_featured": self.is_featured,
            "is_archived": self.is_archived,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "processing_attempts": self.processing_attempts,
            "last_error": self.last_error,
        }
