# -*- coding: utf-8 -*-
"""
AI Translation Service
Provides AI-powered translation capabilities using multiple providers.
"""

import asyncio
import logging
import json
import time
import os
from typing import Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import aiohttp

try:
    from DrissionPage import ChromiumPage, ChromiumOptions
    DRISSION_AVAILABLE = True
except ImportError:
    DRISSION_AVAILABLE = False
    ChromiumPage = None
    ChromiumOptions = None

from enum import Enum
from typing import List

logger = logging.getLogger(__name__)


class AIProvider(str, Enum):
    """Supported AI providers."""
    OPENAI = "openai"
    CLAUDE = "claude"
    GEMINI = "gemini"
    CUSTOM = "custom"


class TranslationResult:
    """Result of a translation operation."""
    
    def __init__(self, success: bool, translated_text: str = "", error: str = "", metadata: Dict[str, Any] = None):
        self.success = success
        self.translated_text = translated_text
        self.error = error
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()


class AITranslationService:
    """AI translation service with multiple provider support."""
    
    def __init__(self):
        self.logger = logger
        self.providers = {
            AIProvider.OPENAI: self._translate_with_openai,
            AIProvider.CLAUDE: self._translate_with_claude,
            AIProvider.GEMINI: self._translate_with_gemini,
            AIProvider.CUSTOM: self._translate_with_custom
        }
        self.default_prompt_template = self._get_default_prompt_template()
    
    async def translate_article(
        self,
        content: str,
        source_language: str = "en",
        target_language: str = "zh",
        provider: AIProvider = AIProvider.OPENAI,
        prompt_template: str = None,
        article_metadata: Dict[str, Any] = None
    ) -> TranslationResult:
        """
        Translate article content using AI services.
        
        Args:
            content: Original article content
            source_language: Source language code
            target_language: Target language code
            provider: AI provider to use
            prompt_template: Custom prompt template
            article_metadata: Additional article metadata
            
        Returns:
            Translation result
        """
        try:
            self.logger.info(f"Starting translation with provider: {provider}")
            
            if not content.strip():
                return TranslationResult(False, error="Content is empty")
            
            # Prepare prompt
            prompt = self._prepare_prompt(
                content, 
                source_language, 
                target_language, 
                prompt_template or self.default_prompt_template,
                article_metadata or {}
            )
            
            # Execute translation
            if provider in self.providers:
                result = await self.providers[provider](prompt, content)
                
                if result.success:
                    self.logger.info(f"Translation completed successfully with {provider}")
                else:
                    self.logger.error(f"Translation failed with {provider}: {result.error}")
                
                return result
            else:
                return TranslationResult(False, error=f"Unsupported provider: {provider}")
                
        except Exception as e:
            self.logger.error(f"Translation error: {e}")
            return TranslationResult(False, error=str(e))
    
    async def translate_with_fallback(
        self,
        content: str,
        providers: List[AIProvider] = None,
        **kwargs
    ) -> TranslationResult:
        """
        Translate content with fallback to other providers if the first one fails.
        
        Args:
            content: Content to translate
            providers: List of providers to try in order
            **kwargs: Additional translation parameters
            
        Returns:
            Translation result
        """
        if providers is None:
            providers = [AIProvider.OPENAI, AIProvider.CLAUDE, AIProvider.GEMINI]
        
        last_error = ""
        
        for provider in providers:
            try:
                result = await self.translate_article(content, provider=provider, **kwargs)
                
                if result.success:
                    result.metadata["provider_used"] = provider
                    result.metadata["fallback_attempted"] = len(providers) > 1
                    return result
                else:
                    last_error = result.error
                    self.logger.warning(f"Provider {provider} failed, trying next: {result.error}")
                    
            except Exception as e:
                last_error = str(e)
                self.logger.warning(f"Provider {provider} error, trying next: {e}")
                continue
        
        return TranslationResult(False, error=f"All providers failed. Last error: {last_error}")
    
    def _prepare_prompt(
        self, 
        content: str, 
        source_lang: str, 
        target_lang: str, 
        template: str,
        metadata: Dict[str, Any]
    ) -> str:
        """Prepare the translation prompt."""
        
        # Replace template variables
        prompt = template.format(
            source_language=source_lang,
            target_language=target_lang,
            content=content,
            title=metadata.get('title', ''),
            author=metadata.get('author', ''),
            platform=metadata.get('platform', ''),
            word_count=len(content.split())
        )
        
        return prompt
    
    async def _translate_with_openai(self, prompt: str, content: str) -> TranslationResult:
        """Translate using real OpenAI API."""
        try:
            # 使用真正的AI API调用
            from .real_ai_api_call import get_real_ai_api_call
            
            api_service = get_real_ai_api_call()
            self.logger.info("🚀 使用真正的AI API进行翻译...")
            
            # 调用翻译API
            result = await api_service.translate_text(content, "中文")
            
            if result["success"]:
                self.logger.info("✅ 真实API翻译成功!")
                return TranslationResult(
                    success=True,
                    translated_text=result["translated_text"],
                    metadata={
                        "provider": "openai",
                        "model": "gpt-3.5-turbo",
                        "method": "real_api",
                        "usage": result.get("usage", {})
                    }
                )
            else:
                self.logger.error(f"❌ API翻译失败: {result['error']}")
                return TranslationResult(False, error=f"Real API translation failed: {result['error']}")
                
        except Exception as e:
            self.logger.error(f"💥 真实API翻译异常: {e}")
            return TranslationResult(False, error=f"Real API translation exception: {e}")
    
    async def _translate_with_claude(self, prompt: str, content: str) -> TranslationResult:
        """Translate using Claude API."""
        try:
            # TODO: Implement actual Claude API call
            self.logger.info("Translating with Claude (mock)")
            await asyncio.sleep(2)  # Simulate API call
            
            # Mock translation
            translated_text = f"[Claude翻译] {content[:100]}..."
            
            return TranslationResult(
                success=True,
                translated_text=translated_text,
                metadata={
                    "provider": "claude",
                    "model": "claude-3-sonnet",
                    "tokens_used": len(content.split()) * 2
                }
            )
            
        except Exception as e:
            return TranslationResult(False, error=f"Claude translation failed: {e}")
    
    async def _translate_with_gemini(self, prompt: str, content: str) -> TranslationResult:
        """Translate using Gemini API."""
        try:
            # TODO: Implement actual Gemini API call
            self.logger.info("Translating with Gemini (mock)")
            await asyncio.sleep(2)  # Simulate API call
            
            # Mock translation
            translated_text = f"[Gemini翻译] {content[:100]}..."
            
            return TranslationResult(
                success=True,
                translated_text=translated_text,
                metadata={
                    "provider": "gemini",
                    "model": "gemini-pro",
                    "tokens_used": len(content.split()) * 2
                }
            )
            
        except Exception as e:
            return TranslationResult(False, error=f"Gemini translation failed: {e}")
    
    async def _translate_with_custom(self, prompt: str, content: str) -> TranslationResult:
        """Translate using custom provider."""
        try:
            # TODO: Implement custom provider logic
            self.logger.info("Translating with custom provider (mock)")
            await asyncio.sleep(1)  # Simulate API call
            
            # Mock translation
            translated_text = f"[自定义翻译] {content[:100]}..."
            
            return TranslationResult(
                success=True,
                translated_text=translated_text,
                metadata={
                    "provider": "custom",
                    "model": "custom-model",
                    "tokens_used": len(content.split()) * 2
                }
            )
            
        except Exception as e:
            return TranslationResult(False, error=f"Custom translation failed: {e}")
    
    def _create_browser_options(self):
        """创建浏览器配置选项"""
        options = ChromiumOptions()
        
        # 指定Chrome浏览器路径
        chrome_path = r"C:\Users\asus\AppData\Local\Chromium\Application\chrome.exe"
        self.logger.info(f"🔧 使用Chrome路径: {chrome_path}")
        options.set_browser_path(chrome_path)
        
        # 用户数据目录
        current_dir = os.getcwd()
        user_data_dir = os.path.join(current_dir, "chro")
        os.makedirs(user_data_dir, exist_ok=True)
        self.logger.info(f"📁 用户数据目录: {user_data_dir}")
        options.set_user_data_path(user_data_dir)
        
        # 指纹参数
        options.set_argument("--fingerprint=1000")
        options.set_argument("--fingerprint-platform=windows")
        options.set_argument("--fingerprint-brand=Chrome")
        options.set_argument("--lang=zh-CN")
        options.set_argument("--timezone=Asia/Shanghai")
        
        # 反检测配置
        options.set_argument("--disable-blink-features=AutomationControlled")
        options.set_argument("--disable-dev-shm-usage")
        options.set_argument("--no-sandbox")
        options.set_argument("--disable-web-security")
        options.set_argument("--disable-features=VizDisplayCompositor")
        
        # 窗口配置 - 强制可视化模式
        options.set_argument("--window-size=1200,800")
        options.set_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # 禁用无头模式
        # options.set_argument("--headless")  # 注释掉确保不使用无头模式
        
        self.logger.info("🔧 浏览器配置: 可视化模式，1200x800窗口")
        return options
    
    async def _mock_translation(self, content: str, provider_name: str) -> TranslationResult:
        """模拟翻译（当浏览器不可用时）"""
        self.logger.info(f"Using mock translation for {provider_name}")
        await asyncio.sleep(2)  # Simulate processing time
        
        translated_text = f"[{provider_name}模拟翻译] {content[:100]}..."
        
        return TranslationResult(
            success=True,
            translated_text=translated_text,
            metadata={
                "provider": provider_name.lower(),
                "method": "mock",
                "tokens_used": len(content.split()) * 2
            }
        )
    
    def _get_default_prompt_template(self) -> str:
        """Get the default translation prompt template."""
        return """你是一位专业的AI技术文章翻译专家，请将以下英文技术文章翻译成中文。

翻译要求：
1. 保持技术术语的准确性
2. 语言流畅自然，符合中文表达习惯
3. 保留原文的结构和格式
4. 对于专业术语，在首次出现时可以保留英文原文并加上中文翻译
5. 保持原文的语气和风格

原文内容：
{content}

请提供高质量的中文翻译："""


# Global service instance
_translation_service = None


def get_ai_translation_service() -> AITranslationService:
    """Get the global AI translation service instance."""
    global _translation_service
    if _translation_service is None:
        _translation_service = AITranslationService()
    return _translation_service
