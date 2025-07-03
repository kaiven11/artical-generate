"""
OpenAI adapter for AI translation and content optimization.
"""

import logging
import time
from typing import Dict, Any, Optional
import requests
import json

from ..base import BaseAIAdapter, TranslationResult, PlatformInfo, AdapterType

logger = logging.getLogger(__name__)


class OpenAIAdapter(BaseAIAdapter):
    """OpenAI adapter for AI services."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize OpenAI adapter."""
        super().__init__(config)
        self.api_key = config.get('api_key') if config else None
        self.base_url = config.get('base_url', 'https://api.openai.com/v1') if config else 'https://api.openai.com/v1'
        self.model = config.get('model', 'gpt-3.5-turbo') if config else 'gpt-3.5-turbo'
        self.max_tokens = config.get('max_tokens', 4000) if config else 4000
        self.temperature = config.get('temperature', 0.7) if config else 0.7
        
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })
    
    def get_platform_info(self) -> PlatformInfo:
        """Get OpenAI platform information."""
        return PlatformInfo(
            name="openai",
            display_name="OpenAI",
            type=AdapterType.AI,
            features=["translation", "optimization", "chat", "completion"],
            requires_auth=True,
            description="OpenAI's GPT models for text generation and translation",
            version="1.0.0",
            website="https://openai.com"
        )
    
    async def test_connection(self) -> bool:
        """Test connection to OpenAI API."""
        try:
            if not self.api_key:
                return False
            
            response = self.session.get(f"{self.base_url}/models", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to connect to OpenAI: {e}")
            return False
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for OpenAI adapter."""
        return {
            "type": "object",
            "properties": {
                "api_key": {
                    "type": "string",
                    "description": "OpenAI API key"
                },
                "base_url": {
                    "type": "string",
                    "default": "https://api.openai.com/v1",
                    "description": "OpenAI API base URL"
                },
                "model": {
                    "type": "string",
                    "default": "gpt-3.5-turbo",
                    "enum": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"],
                    "description": "OpenAI model to use"
                },
                "max_tokens": {
                    "type": "integer",
                    "default": 4000,
                    "description": "Maximum tokens per request"
                },
                "temperature": {
                    "type": "number",
                    "default": 0.7,
                    "minimum": 0,
                    "maximum": 2,
                    "description": "Sampling temperature"
                }
            },
            "required": ["api_key"]
        }
    
    async def translate(self, text: str, prompt: str, **kwargs) -> TranslationResult:
        """
        Translate text using OpenAI.
        
        Args:
            text: Text to translate
            prompt: Translation prompt
            **kwargs: Additional parameters
            
        Returns:
            Translation result
        """
        try:
            start_time = time.time()
            
            # Prepare messages
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ]
            
            # Prepare request data
            request_data = {
                "model": kwargs.get('model', self.model),
                "messages": messages,
                "max_tokens": kwargs.get('max_tokens', self.max_tokens),
                "temperature": kwargs.get('temperature', self.temperature),
                "top_p": kwargs.get('top_p', 1.0),
                "frequency_penalty": kwargs.get('frequency_penalty', 0.0),
                "presence_penalty": kwargs.get('presence_penalty', 0.0)
            }
            
            # Make API request
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                json=request_data,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Extract translated text
            translated_text = result['choices'][0]['message']['content'].strip()
            
            # Calculate metrics
            processing_time = time.time() - start_time
            tokens_used = result.get('usage', {}).get('total_tokens', 0)
            cost = self._calculate_cost(tokens_used, request_data['model'])
            
            return TranslationResult(
                translated_text=translated_text,
                original_text=text,
                source_language="auto",
                target_language="zh-CN",
                quality_score=self._estimate_quality(translated_text),
                provider="openai",
                model=request_data['model'],
                tokens_used=tokens_used,
                cost=cost,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"OpenAI translation failed: {e}")
            raise
    
    async def optimize_content(self, content: str, optimization_prompt: str, **kwargs) -> str:
        """
        Optimize content using OpenAI.
        
        Args:
            content: Content to optimize
            optimization_prompt: Optimization prompt
            **kwargs: Additional parameters
            
        Returns:
            Optimized content
        """
        try:
            # Prepare messages
            messages = [
                {"role": "system", "content": optimization_prompt},
                {"role": "user", "content": content}
            ]
            
            # Prepare request data
            request_data = {
                "model": kwargs.get('model', self.model),
                "messages": messages,
                "max_tokens": kwargs.get('max_tokens', self.max_tokens),
                "temperature": kwargs.get('temperature', self.temperature)
            }
            
            # Make API request
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                json=request_data,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            optimized_content = result['choices'][0]['message']['content'].strip()
            
            return optimized_content
            
        except Exception as e:
            logger.error(f"OpenAI content optimization failed: {e}")
            raise
    
    def get_pricing_info(self) -> Dict[str, float]:
        """Get pricing information for OpenAI models."""
        return {
            "gpt-3.5-turbo": {
                "input_per_1k_tokens": 0.0015,
                "output_per_1k_tokens": 0.002
            },
            "gpt-4": {
                "input_per_1k_tokens": 0.03,
                "output_per_1k_tokens": 0.06
            },
            "gpt-4-turbo-preview": {
                "input_per_1k_tokens": 0.01,
                "output_per_1k_tokens": 0.03
            }
        }
    
    def estimate_cost(self, text: str, model: str = None) -> float:
        """Estimate cost for processing given text."""
        try:
            model = model or self.model
            pricing = self.get_pricing_info().get(model, {})
            
            if not pricing:
                return 0.0
            
            # Rough token estimation (1 token ≈ 4 characters for English)
            estimated_tokens = len(text) // 4
            
            # Assume input and output tokens are roughly equal
            input_cost = (estimated_tokens / 1000) * pricing.get("input_per_1k_tokens", 0)
            output_cost = (estimated_tokens / 1000) * pricing.get("output_per_1k_tokens", 0)
            
            return input_cost + output_cost
            
        except Exception as e:
            logger.warning(f"Failed to estimate cost: {e}")
            return 0.0
    
    def _calculate_cost(self, tokens_used: int, model: str) -> float:
        """Calculate actual cost based on tokens used."""
        try:
            pricing = self.get_pricing_info().get(model, {})
            if not pricing:
                return 0.0
            
            # For simplicity, assume equal input/output tokens
            input_tokens = tokens_used // 2
            output_tokens = tokens_used // 2
            
            input_cost = (input_tokens / 1000) * pricing.get("input_per_1k_tokens", 0)
            output_cost = (output_tokens / 1000) * pricing.get("output_per_1k_tokens", 0)
            
            return input_cost + output_cost
            
        except Exception:
            return 0.0
    
    def _estimate_quality(self, text: str) -> float:
        """Estimate translation quality (simple heuristic)."""
        try:
            # Simple quality estimation based on text characteristics
            if not text or len(text) < 10:
                return 0.0
            
            # Check for common translation issues
            quality_score = 100.0
            
            # Penalize very short translations
            if len(text) < 50:
                quality_score -= 20
            
            # Penalize repetitive content
            words = text.split()
            if len(set(words)) < len(words) * 0.5:
                quality_score -= 30
            
            # Penalize if contains too many English words (for Chinese translation)
            english_words = sum(1 for word in words if word.isascii() and word.isalpha())
            if english_words > len(words) * 0.3:
                quality_score -= 25
            
            return max(0.0, min(100.0, quality_score))
            
        except Exception:
            return 75.0  # Default score
