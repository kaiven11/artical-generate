"""
Prompt template model for managing AI prompts.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON
from sqlalchemy.sql import func
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, List

from ..core.database import Base


class PromptType(str, Enum):
    """Prompt template types."""
    TRANSLATION = "translation"      # Translation prompts
    OPTIMIZATION = "optimization"    # Content optimization prompts
    TITLE_GENERATION = "title_generation"  # Title generation prompts
    SUMMARY = "summary"             # Summary generation prompts
    KEYWORD_EXTRACTION = "keyword_extraction"  # Keyword extraction prompts
    CUSTOM = "custom"               # Custom prompts


class PromptTemplate(Base):
    """Prompt template model for storing AI prompts."""
    
    __tablename__ = "prompt_templates"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic information
    name = Column(String(200), nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Template content
    template = Column(Text, nullable=False)
    
    # Template metadata
    type = Column(String(50), nullable=False, index=True)
    version = Column(String(20), default="1.0")
    language = Column(String(10), default="zh-CN")
    
    # Performance metrics
    success_rate = Column(Float, default=0.0)
    usage_count = Column(Integer, default=0)
    average_quality_score = Column(Float, default=0.0)
    
    # Template parameters
    variables = Column(JSON)  # List of template variables
    parameters = Column(JSON)  # Default parameters for AI models
    
    # Usage settings
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    priority = Column(Integer, default=0)  # Higher priority templates used first
    
    # A/B testing
    test_group = Column(String(50))  # For A/B testing
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_used_at = Column(DateTime)
    
    def __repr__(self):
        return f"<PromptTemplate(id={self.id}, name='{self.name}', type='{self.type}')>"
    
    def render(self, **kwargs) -> str:
        """
        Render template with provided variables.
        
        Args:
            **kwargs: Template variables
            
        Returns:
            str: Rendered template
        """
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")
    
    def get_variables(self) -> List[str]:
        """
        Extract variables from template.
        
        Returns:
            List[str]: List of variable names
        """
        import re
        variables = re.findall(r'\{(\w+)\}', self.template)
        return list(set(variables))
    
    def validate_template(self) -> bool:
        """
        Validate template syntax.
        
        Returns:
            bool: True if template is valid
        """
        try:
            # Try to format with dummy variables
            variables = self.get_variables()
            dummy_vars = {var: f"dummy_{var}" for var in variables}
            self.template.format(**dummy_vars)
            return True
        except Exception:
            return False
    
    def update_metrics(self, success: bool, quality_score: Optional[float] = None):
        """
        Update template performance metrics.
        
        Args:
            success: Whether the template usage was successful
            quality_score: Quality score of the result
        """
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
        
        # Update success rate
        if self.usage_count == 1:
            self.success_rate = 1.0 if success else 0.0
        else:
            current_successes = (self.success_rate * (self.usage_count - 1))
            if success:
                current_successes += 1
            self.success_rate = current_successes / self.usage_count
        
        # Update average quality score
        if quality_score is not None:
            if self.average_quality_score == 0.0:
                self.average_quality_score = quality_score
            else:
                # Weighted average
                total_score = self.average_quality_score * (self.usage_count - 1) + quality_score
                self.average_quality_score = total_score / self.usage_count
        
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert prompt template to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "template": self.template,
            "type": self.type,
            "version": self.version,
            "language": self.language,
            "success_rate": self.success_rate,
            "usage_count": self.usage_count,
            "average_quality_score": self.average_quality_score,
            "variables": self.variables,
            "parameters": self.parameters,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "priority": self.priority,
            "test_group": self.test_group,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }
    
    @classmethod
    def create_default_templates(cls) -> List['PromptTemplate']:
        """Create default prompt templates."""
        templates = [
            cls(
                name="technical_translation_v1",
                display_name="技术文章翻译模板 v1.0",
                description="专业的AI技术文章翻译模板",
                template="""你是一位专业的AI技术文章翻译专家。请将以下英文文章翻译成中文，要求：

1. 保持技术术语的准确性
2. 语言风格符合中文技术文章习惯
3. 保持原文的逻辑结构和段落划分
4. 适当本土化表达方式

原文：
{original_text}

请提供高质量的中文翻译：""",
                type=PromptType.TRANSLATION,
                variables=["original_text"],
                is_active=True,
                is_default=True,
                priority=10
            ),
            cls(
                name="originality_optimization_v1",
                display_name="原创性优化模板 v1.0",
                description="提高文章原创性的优化模板",
                template="""你是一位专业的内容优化专家。请对以下文章进行优化，使其：

1. 提高原创性，避免AI检测
2. 保持技术内容的准确性
3. 符合今日头条平台的内容规范
4. 增强可读性和用户体验

检测反馈：{detection_feedback}
原文章：{article_content}

请提供优化后的文章：""",
                type=PromptType.OPTIMIZATION,
                variables=["detection_feedback", "article_content"],
                is_active=True,
                is_default=True,
                priority=10
            )
        ]
        return templates
