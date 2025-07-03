"""
Detection result model for storing detection results.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any

from ..core.database import Base


class DetectionType(str, Enum):
    """Detection types."""
    ORIGINALITY = "originality"      # Originality detection
    AI_GENERATED = "ai_generated"    # AI-generated content detection
    PLAGIARISM = "plagiarism"        # Plagiarism detection
    QUALITY = "quality"              # Content quality detection


class DetectionResult(Base):
    """Detection result model for storing detection results."""
    
    __tablename__ = "detection_results"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to article
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False, index=True)
    
    # Detection information
    detection_type = Column(String(50), nullable=False, index=True)
    platform = Column(String(50), nullable=False)  # Detection platform (e.g., "zhuque")
    
    # Detection results
    score = Column(Float)  # Detection score (0-100)
    is_passed = Column(Boolean, nullable=False)  # Whether detection passed
    confidence = Column(Float)  # Confidence level of the result
    
    # Detailed results
    details = Column(JSON)  # Detailed detection results
    feedback = Column(Text)  # Feedback or suggestions
    
    # Processing information
    processing_time = Column(Float)  # Time taken for detection (seconds)
    retry_count = Column(Integer, default=0)
    error_message = Column(Text)
    
    # Content information
    content_hash = Column(String(64), index=True)  # Hash of detected content
    content_length = Column(Integer)  # Length of detected content
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationship
    article = relationship("Article", back_populates="detection_results")
    
    def __repr__(self):
        return f"<DetectionResult(id={self.id}, type='{self.detection_type}', score={self.score})>"
    
    @property
    def status(self) -> str:
        """Get detection status as string."""
        if self.is_passed:
            return "passed"
        else:
            return "failed"
    
    def get_grade(self) -> str:
        """
        Get detection grade based on score.
        
        Returns:
            str: Grade (A, B, C, D, F)
        """
        if self.score is None:
            return "N/A"
        
        if self.score >= 90:
            return "A"
        elif self.score >= 80:
            return "B"
        elif self.score >= 70:
            return "C"
        elif self.score >= 60:
            return "D"
        else:
            return "F"
    
    def get_recommendation(self) -> str:
        """
        Get recommendation based on detection result.
        
        Returns:
            str: Recommendation text
        """
        if self.is_passed:
            return "检测通过，可以继续下一步处理"
        
        recommendations = {
            DetectionType.ORIGINALITY: "原创性不足，建议进行内容优化和改写",
            DetectionType.AI_GENERATED: "AI特征明显，建议增加人工润色和个性化表达",
            DetectionType.PLAGIARISM: "存在抄袭风险，建议重新创作或大幅修改",
            DetectionType.QUALITY: "内容质量有待提升，建议优化结构和表达"
        }
        
        return recommendations.get(self.detection_type, "检测未通过，建议优化内容")
    
    def update_result(self, score: float, is_passed: bool, details: Optional[Dict] = None,
                     feedback: Optional[str] = None, processing_time: Optional[float] = None):
        """
        Update detection result.
        
        Args:
            score: Detection score
            is_passed: Whether detection passed
            details: Detailed results
            feedback: Feedback message
            processing_time: Processing time in seconds
        """
        self.score = score
        self.is_passed = is_passed
        
        if details:
            self.details = details
        
        if feedback:
            self.feedback = feedback
        
        if processing_time:
            self.processing_time = processing_time
        
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert detection result to dictionary."""
        return {
            "id": self.id,
            "article_id": self.article_id,
            "detection_type": self.detection_type,
            "platform": self.platform,
            "score": self.score,
            "is_passed": self.is_passed,
            "confidence": self.confidence,
            "details": self.details,
            "feedback": self.feedback,
            "processing_time": self.processing_time,
            "retry_count": self.retry_count,
            "error_message": self.error_message,
            "content_hash": self.content_hash,
            "content_length": self.content_length,
            "status": self.status,
            "grade": self.get_grade(),
            "recommendation": self.get_recommendation(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# Add relationship to Article model
from .article import Article
Article.detection_results = relationship("DetectionResult", back_populates="article")
