"""
API endpoints for processing configuration management.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.processing_config import (
    ProcessingRule, ContentClassificationRule, ProcessingHistory,
    ContentCategory, ProcessingStrategy
)
from ..services.processing_config_service import get_processing_config_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/processing-config", tags=["Processing Configuration"])


# Pydantic models for API requests/responses
class ProcessingRuleCreate(BaseModel):
    name: str = Field(..., description="Rule name")
    display_name: str = Field(..., description="Display name")
    description: Optional[str] = None
    content_category: str = Field(..., description="Content category")
    source_platform: Optional[str] = None
    target_platform: Optional[str] = None
    processing_strategy: str = Field(default="standard", description="Processing strategy")
    translation_prompt_id: Optional[int] = None
    optimization_prompt_id: Optional[int] = None
    title_generation_prompt_id: Optional[int] = None
    primary_provider_id: Optional[int] = None
    fallback_provider_id: Optional[int] = None
    ai_detection_threshold: float = Field(default=25.0, description="AI detection threshold")
    max_optimization_rounds: int = Field(default=3, description="Max optimization rounds")
    quality_threshold: float = Field(default=0.8, description="Quality threshold")
    priority: int = Field(default=100, description="Rule priority")
    is_active: bool = Field(default=True, description="Is rule active")
    is_default: bool = Field(default=False, description="Is default rule")


class ProcessingRuleUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    processing_strategy: Optional[str] = None
    translation_prompt_id: Optional[int] = None
    optimization_prompt_id: Optional[int] = None
    title_generation_prompt_id: Optional[int] = None
    primary_provider_id: Optional[int] = None
    fallback_provider_id: Optional[int] = None
    ai_detection_threshold: Optional[float] = None
    max_optimization_rounds: Optional[int] = None
    quality_threshold: Optional[float] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class ProcessingRuleResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: Optional[str]
    content_category: str
    source_platform: Optional[str]
    target_platform: Optional[str]
    processing_strategy: str
    translation_prompt_id: Optional[int]
    optimization_prompt_id: Optional[int]
    title_generation_prompt_id: Optional[int]
    primary_provider_id: Optional[int]
    fallback_provider_id: Optional[int]
    ai_detection_threshold: float
    max_optimization_rounds: int
    quality_threshold: float
    priority: int
    is_active: bool
    is_default: bool
    usage_count: int
    success_rate: float
    created_at: str
    updated_at: str


class ClassificationRuleCreate(BaseModel):
    name: str = Field(..., description="Rule name")
    description: Optional[str] = None
    target_category: str = Field(..., description="Target category")
    title_keywords: Optional[List[str]] = None
    content_keywords: Optional[List[str]] = None
    url_patterns: Optional[List[str]] = None
    source_domains: Optional[List[str]] = None
    title_weight: float = Field(default=0.4, description="Title weight")
    content_weight: float = Field(default=0.3, description="Content weight")
    url_weight: float = Field(default=0.2, description="URL weight")
    domain_weight: float = Field(default=0.1, description="Domain weight")
    classification_threshold: float = Field(default=0.6, description="Classification threshold")
    is_active: bool = Field(default=True, description="Is rule active")
    priority: int = Field(default=100, description="Rule priority")


class ArticleClassificationRequest(BaseModel):
    article_id: int = Field(..., description="Article ID to classify")


class ArticleClassificationResponse(BaseModel):
    article_id: int
    content_category: str
    confidence: float
    processing_rule_id: Optional[int]
    configuration: Dict[str, Any]


class ClassificationRuleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    target_category: str
    title_keywords: Optional[List[str]]
    content_keywords: Optional[List[str]]
    url_patterns: Optional[List[str]]
    source_domains: Optional[List[str]]
    title_weight: float
    content_weight: float
    url_weight: float
    domain_weight: float
    classification_threshold: float
    is_active: bool
    priority: int
    created_at: str
    updated_at: str


# Processing Rules endpoints
@router.get("/rules", response_model=List[ProcessingRuleResponse])
async def get_processing_rules(
    category: Optional[str] = None,
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """Get all processing rules."""
    try:
        query = db.query(ProcessingRule)
        
        if category:
            query = query.filter(ProcessingRule.content_category == category)
        
        if active_only:
            query = query.filter(ProcessingRule.is_active == True)
        
        rules = query.order_by(ProcessingRule.priority).all()
        
        return [
            ProcessingRuleResponse(
                id=rule.id,
                name=rule.name,
                display_name=rule.display_name,
                description=rule.description,
                content_category=rule.content_category,
                source_platform=rule.source_platform,
                target_platform=rule.target_platform,
                processing_strategy=rule.processing_strategy,
                translation_prompt_id=rule.translation_prompt_id,
                optimization_prompt_id=rule.optimization_prompt_id,
                title_generation_prompt_id=rule.title_generation_prompt_id,
                primary_provider_id=rule.primary_provider_id,
                fallback_provider_id=rule.fallback_provider_id,
                ai_detection_threshold=rule.ai_detection_threshold,
                max_optimization_rounds=rule.max_optimization_rounds,
                quality_threshold=rule.quality_threshold,
                priority=rule.priority,
                is_active=rule.is_active,
                is_default=rule.is_default,
                usage_count=rule.usage_count,
                success_rate=rule.success_rate,
                created_at=rule.created_at.isoformat() if rule.created_at else "",
                updated_at=rule.updated_at.isoformat() if rule.updated_at else ""
            )
            for rule in rules
        ]
        
    except Exception as e:
        logger.error(f"Failed to get processing rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules", response_model=ProcessingRuleResponse)
async def create_processing_rule(
    rule: ProcessingRuleCreate,
    db: Session = Depends(get_db)
):
    """Create a new processing rule."""
    try:
        # Check if name already exists
        existing = db.query(ProcessingRule).filter(ProcessingRule.name == rule.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Rule name already exists")
        
        # Create new rule
        new_rule = ProcessingRule(
            name=rule.name,
            display_name=rule.display_name,
            description=rule.description,
            content_category=rule.content_category,
            source_platform=rule.source_platform,
            target_platform=rule.target_platform,
            processing_strategy=rule.processing_strategy,
            translation_prompt_id=rule.translation_prompt_id,
            optimization_prompt_id=rule.optimization_prompt_id,
            title_generation_prompt_id=rule.title_generation_prompt_id,
            primary_provider_id=rule.primary_provider_id,
            fallback_provider_id=rule.fallback_provider_id,
            ai_detection_threshold=rule.ai_detection_threshold,
            max_optimization_rounds=rule.max_optimization_rounds,
            quality_threshold=rule.quality_threshold,
            priority=rule.priority,
            is_active=rule.is_active,
            is_default=rule.is_default
        )
        
        db.add(new_rule)
        db.commit()
        db.refresh(new_rule)
        
        return ProcessingRuleResponse(
            id=new_rule.id,
            name=new_rule.name,
            display_name=new_rule.display_name,
            description=new_rule.description,
            content_category=new_rule.content_category,
            source_platform=new_rule.source_platform,
            target_platform=new_rule.target_platform,
            processing_strategy=new_rule.processing_strategy,
            translation_prompt_id=new_rule.translation_prompt_id,
            optimization_prompt_id=new_rule.optimization_prompt_id,
            title_generation_prompt_id=new_rule.title_generation_prompt_id,
            primary_provider_id=new_rule.primary_provider_id,
            fallback_provider_id=new_rule.fallback_provider_id,
            ai_detection_threshold=new_rule.ai_detection_threshold,
            max_optimization_rounds=new_rule.max_optimization_rounds,
            quality_threshold=new_rule.quality_threshold,
            priority=new_rule.priority,
            is_active=new_rule.is_active,
            is_default=new_rule.is_default,
            usage_count=new_rule.usage_count,
            success_rate=new_rule.success_rate,
            created_at=new_rule.created_at.isoformat() if new_rule.created_at else "",
            updated_at=new_rule.updated_at.isoformat() if new_rule.updated_at else ""
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create processing rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/classify", response_model=ArticleClassificationResponse)
async def classify_article(
    request: ArticleClassificationRequest,
    db: Session = Depends(get_db)
):
    """Classify an article and get processing configuration."""
    try:
        config_service = get_processing_config_service()
        
        # Get article
        from ..models.article import Article
        article = db.query(Article).filter(Article.id == request.article_id).first()
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Get processing configuration
        config = config_service.get_processing_configuration(article)
        
        return ArticleClassificationResponse(
            article_id=request.article_id,
            content_category=config.get("content_category", "general"),
            confidence=config.get("classification_confidence", 0.0),
            processing_rule_id=config.get("processing_rule_id"),
            configuration=config
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to classify article: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules/{rule_id}", response_model=ProcessingRuleResponse)
async def get_processing_rule(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific processing rule."""
    try:
        rule = db.query(ProcessingRule).filter(ProcessingRule.id == rule_id).first()
        if not rule:
            raise HTTPException(status_code=404, detail="Processing rule not found")

        return ProcessingRuleResponse(
            id=rule.id,
            name=rule.name,
            display_name=rule.display_name,
            description=rule.description,
            content_category=rule.content_category,
            source_platform=rule.source_platform,
            target_platform=rule.target_platform,
            processing_strategy=rule.processing_strategy,
            translation_prompt_id=rule.translation_prompt_id,
            optimization_prompt_id=rule.optimization_prompt_id,
            title_generation_prompt_id=rule.title_generation_prompt_id,
            primary_provider_id=rule.primary_provider_id,
            fallback_provider_id=rule.fallback_provider_id,
            ai_detection_threshold=rule.ai_detection_threshold,
            max_optimization_rounds=rule.max_optimization_rounds,
            quality_threshold=rule.quality_threshold,
            priority=rule.priority,
            is_active=rule.is_active,
            is_default=rule.is_default,
            usage_count=rule.usage_count,
            success_rate=rule.success_rate,
            created_at=rule.created_at.isoformat() if rule.created_at else "",
            updated_at=rule.updated_at.isoformat() if rule.updated_at else ""
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get processing rule {rule_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rules/{rule_id}", response_model=ProcessingRuleResponse)
async def update_processing_rule(
    rule_id: int,
    rule_update: ProcessingRuleCreate,
    db: Session = Depends(get_db)
):
    """Update a processing rule."""
    try:
        rule = db.query(ProcessingRule).filter(ProcessingRule.id == rule_id).first()
        if not rule:
            raise HTTPException(status_code=404, detail="Processing rule not found")

        # Check if name already exists (excluding current rule)
        if rule_update.name != rule.name:
            existing = db.query(ProcessingRule).filter(
                ProcessingRule.name == rule_update.name,
                ProcessingRule.id != rule_id
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="Rule name already exists")

        # Update rule fields
        for field, value in rule_update.model_dump().items():
            if hasattr(rule, field):
                setattr(rule, field, value)

        db.commit()
        db.refresh(rule)

        return ProcessingRuleResponse(
            id=rule.id,
            name=rule.name,
            display_name=rule.display_name,
            description=rule.description,
            content_category=rule.content_category,
            source_platform=rule.source_platform,
            target_platform=rule.target_platform,
            processing_strategy=rule.processing_strategy,
            translation_prompt_id=rule.translation_prompt_id,
            optimization_prompt_id=rule.optimization_prompt_id,
            title_generation_prompt_id=rule.title_generation_prompt_id,
            primary_provider_id=rule.primary_provider_id,
            fallback_provider_id=rule.fallback_provider_id,
            ai_detection_threshold=rule.ai_detection_threshold,
            max_optimization_rounds=rule.max_optimization_rounds,
            quality_threshold=rule.quality_threshold,
            priority=rule.priority,
            is_active=rule.is_active,
            is_default=rule.is_default,
            usage_count=rule.usage_count,
            success_rate=rule.success_rate,
            created_at=rule.created_at.isoformat() if rule.created_at else "",
            updated_at=rule.updated_at.isoformat() if rule.updated_at else ""
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update processing rule {rule_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rules/{rule_id}")
async def delete_processing_rule(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """Delete a processing rule."""
    try:
        rule = db.query(ProcessingRule).filter(ProcessingRule.id == rule_id).first()
        if not rule:
            raise HTTPException(status_code=404, detail="Processing rule not found")

        # Check if it's a default rule
        if rule.is_default:
            raise HTTPException(status_code=400, detail="Cannot delete default rule")

        db.delete(rule)
        db.commit()

        return {"message": "Processing rule deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete processing rule {rule_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# Classification Rules endpoints
@router.get("/classification-rules", response_model=List[ClassificationRuleResponse])
async def get_classification_rules(
    category: Optional[str] = None,
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """Get all classification rules."""
    try:
        query = db.query(ContentClassificationRule)

        if category:
            query = query.filter(ContentClassificationRule.target_category == category)

        if active_only:
            query = query.filter(ContentClassificationRule.is_active == True)

        rules = query.order_by(ContentClassificationRule.priority).all()

        return [
            ClassificationRuleResponse(
                id=rule.id,
                name=rule.name,
                description=rule.description,
                target_category=rule.target_category,
                title_keywords=rule.title_keywords,
                content_keywords=rule.content_keywords,
                url_patterns=rule.url_patterns,
                source_domains=rule.source_domains,
                title_weight=rule.title_weight,
                content_weight=rule.content_weight,
                url_weight=rule.url_weight,
                domain_weight=rule.domain_weight,
                classification_threshold=rule.classification_threshold,
                is_active=rule.is_active,
                priority=rule.priority,
                created_at=rule.created_at.isoformat() if rule.created_at else "",
                updated_at=rule.updated_at.isoformat() if rule.updated_at else ""
            )
            for rule in rules
        ]

    except Exception as e:
        logger.error(f"Failed to get classification rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_content_categories():
    """Get available content categories."""
    return {
        "categories": [
            {"value": category.value, "label": category.value.title()}
            for category in ContentCategory
        ]
    }


@router.get("/strategies")
async def get_processing_strategies():
    """Get available processing strategies."""
    return {
        "strategies": [
            {"value": strategy.value, "label": strategy.value.title()}
            for strategy in ProcessingStrategy
        ]
    }
