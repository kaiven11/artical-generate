"""
Processing configuration models for article processing workflows.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, List

from ..core.database import Base


class ContentCategory(str, Enum):
    """Content categories for article classification."""
    TECHNICAL = "technical"          # 技术类文章
    TUTORIAL = "tutorial"            # 教程类文章
    NEWS = "news"                    # 新闻类文章
    BUSINESS = "business"            # 商业类文章
    LIFESTYLE = "lifestyle"          # 生活类文章
    ENTERTAINMENT = "entertainment"  # 娱乐类文章
    GENERAL = "general"              # 通用类文章


class ProcessingStrategy(str, Enum):
    """Processing strategies for different content types."""
    CONSERVATIVE = "conservative"    # 保守策略：轻度优化
    STANDARD = "standard"           # 标准策略：中度优化
    AGGRESSIVE = "aggressive"       # 激进策略：重度优化
    CUSTOM = "custom"              # 自定义策略


class ProcessingRule(Base):
    """Processing rules that define how different content types should be processed."""
    
    __tablename__ = "processing_rules"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Rule identification
    name = Column(String(200), nullable=False, unique=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Content matching criteria
    content_category = Column(String(50), nullable=False, index=True)  # ContentCategory
    source_platform = Column(String(50))  # 来源平台过滤 (medium, toutiao, etc.)
    target_platform = Column(String(50))  # 目标平台 (toutiao, weixin, etc.)
    
    # Processing configuration
    processing_strategy = Column(String(50), default="standard")  # ProcessingStrategy
    
    # Prompt template bindings
    translation_prompt_id = Column(Integer, ForeignKey("prompt_templates.id"))
    optimization_prompt_id = Column(Integer, ForeignKey("prompt_templates.id"))
    title_generation_prompt_id = Column(Integer, ForeignKey("prompt_templates.id"))
    
    # LLM API provider bindings
    primary_provider_id = Column(Integer, ForeignKey("api_providers.id"))
    fallback_provider_id = Column(Integer, ForeignKey("api_providers.id"))
    
    # Processing parameters
    ai_detection_threshold = Column(Float, default=25.0)  # AI检测阈值
    max_optimization_rounds = Column(Integer, default=3)   # 最大优化轮数
    quality_threshold = Column(Float, default=0.8)        # 质量阈值
    
    # Rule priority and status
    priority = Column(Integer, default=100)  # 优先级，数字越小优先级越高
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)  # 是否为默认规则
    
    # Performance tracking
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    average_processing_time = Column(Float, default=0.0)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(100), default="system")
    
    # Relationships
    translation_prompt = relationship("PromptTemplate", foreign_keys=[translation_prompt_id])
    optimization_prompt = relationship("PromptTemplate", foreign_keys=[optimization_prompt_id])
    title_generation_prompt = relationship("PromptTemplate", foreign_keys=[title_generation_prompt_id])
    primary_provider = relationship("APIProvider", foreign_keys=[primary_provider_id])
    fallback_provider = relationship("APIProvider", foreign_keys=[fallback_provider_id])


class ContentClassificationRule(Base):
    """Rules for automatically classifying content into categories."""
    
    __tablename__ = "content_classification_rules"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Rule identification
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Classification criteria
    target_category = Column(String(50), nullable=False)  # ContentCategory
    
    # Matching rules (JSON format)
    title_keywords = Column(JSON)      # 标题关键词列表
    content_keywords = Column(JSON)    # 内容关键词列表
    url_patterns = Column(JSON)        # URL模式列表
    source_domains = Column(JSON)      # 来源域名列表
    
    # Scoring weights
    title_weight = Column(Float, default=0.4)     # 标题匹配权重
    content_weight = Column(Float, default=0.3)   # 内容匹配权重
    url_weight = Column(Float, default=0.2)       # URL匹配权重
    domain_weight = Column(Float, default=0.1)    # 域名匹配权重
    
    # Threshold for classification
    classification_threshold = Column(Float, default=0.6)  # 分类阈值
    
    # Rule status
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=100)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ProcessingHistory(Base):
    """History of processing rule applications."""
    
    __tablename__ = "processing_history"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # References
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    processing_rule_id = Column(Integer, ForeignKey("processing_rules.id"))
    
    # Processing details
    content_category = Column(String(50))
    classification_confidence = Column(Float)  # 分类置信度
    
    # Applied configurations
    used_prompts = Column(JSON)      # 使用的提示词ID列表
    used_providers = Column(JSON)    # 使用的API Provider ID列表
    
    # Processing results
    processing_steps = Column(JSON)   # 执行的处理步骤
    success = Column(Boolean)
    error_message = Column(Text)
    processing_time = Column(Float)   # 处理耗时（秒）
    
    # Quality metrics
    final_ai_probability = Column(Float)  # 最终AI概率
    optimization_rounds = Column(Integer) # 优化轮数
    quality_score = Column(Float)         # 质量评分
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    article = relationship("Article")
    processing_rule = relationship("ProcessingRule")


class ProviderLoadBalancing(Base):
    """Load balancing configuration for API providers."""
    
    __tablename__ = "provider_load_balancing"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Provider reference
    provider_id = Column(Integer, ForeignKey("api_providers.id"), nullable=False)
    
    # Load balancing settings
    weight = Column(Integer, default=1)           # 权重
    max_concurrent = Column(Integer, default=5)   # 最大并发数
    current_load = Column(Integer, default=0)     # 当前负载
    
    # Rate limiting
    requests_per_minute = Column(Integer, default=60)
    requests_per_hour = Column(Integer, default=1000)
    current_minute_count = Column(Integer, default=0)
    current_hour_count = Column(Integer, default=0)
    
    # Health status
    is_healthy = Column(Boolean, default=True)
    last_health_check = Column(DateTime)
    consecutive_failures = Column(Integer, default=0)
    
    # Performance metrics
    average_response_time = Column(Float, default=0.0)
    success_rate = Column(Float, default=100.0)
    total_requests = Column(Integer, default=0)
    
    # Metadata
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    provider = relationship("APIProvider")
