"""
Processing configuration service for managing article processing workflows.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from ..models.processing_config import (
    ProcessingRule, ContentClassificationRule, ProcessingHistory,
    ContentCategory, ProcessingStrategy, ProviderLoadBalancing
)
from ..models.article import Article
from ..models.prompt import PromptTemplate
from ..models.config import APIProvider
from ..core.database import get_db_session

logger = logging.getLogger(__name__)


class ProcessingConfigService:
    """Service for managing processing configurations and rules."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def classify_article(self, article: Article) -> Tuple[ContentCategory, float]:
        """
        Classify article into content category based on classification rules.
        
        Args:
            article: Article to classify
            
        Returns:
            Tuple of (category, confidence_score)
        """
        try:
            # Use direct database connection for synchronous operation
            from ..core.database import get_db_connection
            conn = get_db_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM content_classification_rules
                    WHERE is_active = 1
                    ORDER BY priority
                """)
                rules = cursor.fetchall()
                
                if not rules:
                    self.logger.warning("No classification rules found, using GENERAL category")
                    return ContentCategory.GENERAL, 0.5
                
                # Calculate scores for each category
                category_scores = {}
                
                for rule in rules:
                    # Create a simple rule object for compatibility
                    rule_obj = type('Rule', (), {
                        'classification_threshold': rule['classification_threshold'],
                        'target_category': rule['target_category'],
                        'keywords': rule['keywords'],
                        'weight': rule['weight']
                    })()

                    score = self._calculate_classification_score(article, rule_obj)

                    if score >= rule_obj.classification_threshold:
                        category = ContentCategory(rule_obj.target_category)
                        if category not in category_scores or score > category_scores[category]:
                            category_scores[category] = score

                # Return the category with highest score
                if category_scores:
                    best_category = max(category_scores.items(), key=lambda x: x[1])
                    self.logger.info(f"Article classified as {best_category[0]} with confidence {best_category[1]:.2f}")
                    return best_category
                else:
                    self.logger.info("No category met threshold, using GENERAL")
                    return ContentCategory.GENERAL, 0.3
            finally:
                conn.close()

        except Exception as e:
            self.logger.error(f"Error classifying article: {e}")
            return ContentCategory.GENERAL, 0.0
    
    def _calculate_classification_score(self, article: Article, rule: ContentClassificationRule) -> float:
        """Calculate classification score for an article against a rule."""
        total_score = 0.0
        
        # Title keyword matching
        if rule.title_keywords and article.title:
            title_score = self._calculate_keyword_score(
                article.title.lower(), rule.title_keywords
            )
            total_score += title_score * rule.title_weight
        
        # Content keyword matching
        if rule.content_keywords and article.content_original:
            content_score = self._calculate_keyword_score(
                article.content_original.lower()[:1000], rule.content_keywords  # First 1000 chars
            )
            total_score += content_score * rule.content_weight
        
        # URL pattern matching
        if rule.url_patterns and article.source_url:
            url_score = self._calculate_pattern_score(
                article.source_url.lower(), rule.url_patterns
            )
            total_score += url_score * rule.url_weight
        
        # Domain matching
        if rule.source_domains and article.source_url:
            domain_score = self._calculate_domain_score(
                article.source_url, rule.source_domains
            )
            total_score += domain_score * rule.domain_weight
        
        return min(total_score, 1.0)  # Cap at 1.0
    
    def _calculate_keyword_score(self, text: str, keywords: List[str]) -> float:
        """Calculate keyword matching score."""
        if not keywords or not text:
            return 0.0
        
        matches = sum(1 for keyword in keywords if keyword.lower() in text)
        return matches / len(keywords)
    
    def _calculate_pattern_score(self, text: str, patterns: List[str]) -> float:
        """Calculate pattern matching score."""
        if not patterns or not text:
            return 0.0
        
        matches = sum(1 for pattern in patterns if re.search(pattern, text, re.IGNORECASE))
        return matches / len(patterns)
    
    def _calculate_domain_score(self, url: str, domains: List[str]) -> float:
        """Calculate domain matching score."""
        if not domains or not url:
            return 0.0
        
        matches = sum(1 for domain in domains if domain.lower() in url.lower())
        return 1.0 if matches > 0 else 0.0
    
    def get_processing_rule(
        self, 
        content_category: ContentCategory,
        source_platform: str = None,
        target_platform: str = None
    ) -> Optional[ProcessingRule]:
        """
        Get the best matching processing rule for given criteria.
        
        Args:
            content_category: Content category
            source_platform: Source platform (optional)
            target_platform: Target platform (optional)
            
        Returns:
            Best matching ProcessingRule or None
        """
        try:
            with get_db_session() as session:
                query = session.query(ProcessingRule).filter(
                    ProcessingRule.is_active == True,
                    ProcessingRule.content_category == content_category.value
                )
                
                # Add platform filters if provided
                if source_platform:
                    query = query.filter(
                        or_(
                            ProcessingRule.source_platform == source_platform,
                            ProcessingRule.source_platform.is_(None)
                        )
                    )
                
                if target_platform:
                    query = query.filter(
                        or_(
                            ProcessingRule.target_platform == target_platform,
                            ProcessingRule.target_platform.is_(None)
                        )
                    )
                
                # Order by priority (lower number = higher priority)
                rules = query.order_by(ProcessingRule.priority).all()
                
                if rules:
                    rule = rules[0]  # Get highest priority rule
                    self.logger.info(f"Selected processing rule: {rule.name}")
                    return rule
                else:
                    # Try to get default rule
                    default_rule = session.query(ProcessingRule).filter(
                        ProcessingRule.is_active == True,
                        ProcessingRule.is_default == True
                    ).first()
                    
                    if default_rule:
                        self.logger.info(f"Using default processing rule: {default_rule.name}")
                        return default_rule
                    else:
                        self.logger.warning("No processing rule found")
                        return None
                        
        except Exception as e:
            self.logger.error(f"Error getting processing rule: {e}")
            return None
    
    def get_processing_configuration(self, article: Article) -> Dict[str, Any]:
        """
        Get complete processing configuration for an article.
        
        Args:
            article: Article to process
            
        Returns:
            Dictionary containing processing configuration
        """
        try:
            # Classify the article
            content_category, confidence = self.classify_article(article)
            
            # Get processing rule
            processing_rule = self.get_processing_rule(
                content_category=content_category,
                source_platform=article.source_platform,
                target_platform="toutiao"  # Default target platform
            )
            
            if not processing_rule:
                self.logger.error("No processing rule found, using defaults")
                return self._get_default_configuration(content_category)
            
            # Build configuration
            config = {
                "content_category": content_category.value,
                "classification_confidence": confidence,
                "processing_rule_id": processing_rule.id,
                "processing_strategy": processing_rule.processing_strategy,
                "ai_detection_threshold": processing_rule.ai_detection_threshold,
                "max_optimization_rounds": processing_rule.max_optimization_rounds,
                "quality_threshold": processing_rule.quality_threshold,
                "prompts": {
                    "translation": processing_rule.translation_prompt_id,
                    "optimization": processing_rule.optimization_prompt_id,
                    "title_generation": processing_rule.title_generation_prompt_id
                },
                "providers": {
                    "primary": processing_rule.primary_provider_id,
                    "fallback": processing_rule.fallback_provider_id
                }
            }
            
            self.logger.info(f"Generated processing configuration for article {article.id}")
            return config
            
        except Exception as e:
            self.logger.error(f"Error generating processing configuration: {e}")
            return self._get_default_configuration(ContentCategory.GENERAL)
    
    def _get_default_configuration(self, content_category: ContentCategory) -> Dict[str, Any]:
        """Get default processing configuration."""
        return {
            "content_category": content_category.value,
            "classification_confidence": 0.0,
            "processing_rule_id": None,
            "processing_strategy": ProcessingStrategy.STANDARD.value,
            "ai_detection_threshold": 25.0,
            "max_optimization_rounds": 3,
            "quality_threshold": 0.8,
            "prompts": {
                "translation": None,
                "optimization": None,
                "title_generation": None
            },
            "providers": {
                "primary": None,
                "fallback": None
            }
        }
    
    def record_processing_history(
        self,
        article_id: int,
        config: Dict[str, Any],
        result: Dict[str, Any]
    ):
        """Record processing history for analytics."""
        try:
            with get_db_session() as session:
                history = ProcessingHistory(
                    article_id=article_id,
                    processing_rule_id=config.get("processing_rule_id"),
                    content_category=config.get("content_category"),
                    classification_confidence=config.get("classification_confidence"),
                    used_prompts=config.get("prompts"),
                    used_providers=config.get("providers"),
                    processing_steps=result.get("steps", []),
                    success=result.get("success", False),
                    error_message=result.get("error"),
                    processing_time=result.get("processing_time", 0.0),
                    final_ai_probability=result.get("final_ai_probability"),
                    optimization_rounds=result.get("optimization_rounds", 0),
                    quality_score=result.get("quality_score", 0.0)
                )
                
                session.add(history)
                session.commit()
                
                self.logger.info(f"Recorded processing history for article {article_id}")
                
        except Exception as e:
            self.logger.error(f"Error recording processing history: {e}")


# Global service instance
_processing_config_service = None

def get_processing_config_service() -> ProcessingConfigService:
    """Get global processing config service instance."""
    global _processing_config_service
    if _processing_config_service is None:
        _processing_config_service = ProcessingConfigService()
    return _processing_config_service
