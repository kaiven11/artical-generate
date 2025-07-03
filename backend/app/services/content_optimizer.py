# -*- coding: utf-8 -*-
"""
Content Optimization Service
Optimizes article content for publishing on Chinese platforms.
"""

import logging
import re
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class OptimizationResult:
    """Result of content optimization."""
    
    def __init__(self, success: bool, optimized_content: str = "", metadata: Dict[str, Any] = None, error: str = ""):
        self.success = success
        self.optimized_content = optimized_content
        self.metadata = metadata or {}
        self.error = error
        self.timestamp = datetime.utcnow()


class ContentOptimizer:
    """Content optimization service for Chinese platforms."""
    
    def __init__(self):
        self.logger = logger
        self.optimization_rules = {
            'format_cleanup': self._format_cleanup,
            'title_optimization': self._optimize_title,
            'paragraph_optimization': self._optimize_paragraphs,
            'tag_generation': self._generate_tags,
            'seo_optimization': self._seo_optimization,
            'platform_adaptation': self._adapt_for_platform
        }
    
    async def optimize_content(
        self,
        content: str,
        title: str = "",
        platform: str = "toutiao",
        optimization_level: str = "standard",
        custom_rules: List[str] = None
    ) -> OptimizationResult:
        """
        Optimize article content for publishing.
        
        Args:
            content: Article content to optimize
            title: Article title
            platform: Target platform (toutiao, weixin, zhihu, etc.)
            optimization_level: Level of optimization (basic, standard, advanced)
            custom_rules: Custom optimization rules to apply
            
        Returns:
            Optimization result
        """
        try:
            self.logger.info(f"Starting content optimization for platform: {platform}")
            
            if not content.strip():
                return OptimizationResult(False, error="Content is empty")
            
            # Determine optimization rules to apply
            rules_to_apply = self._get_optimization_rules(optimization_level, custom_rules)
            
            optimized_content = content
            optimized_title = title
            metadata = {
                "original_length": len(content),
                "optimization_level": optimization_level,
                "platform": platform,
                "rules_applied": rules_to_apply
            }
            
            # Apply optimization rules
            for rule_name in rules_to_apply:
                if rule_name in self.optimization_rules:
                    self.logger.debug(f"Applying optimization rule: {rule_name}")
                    
                    if rule_name == 'title_optimization':
                        optimized_title = await self.optimization_rules[rule_name](optimized_title, platform)
                    else:
                        optimized_content = await self.optimization_rules[rule_name](optimized_content, platform)
            
            # Generate final metadata
            metadata.update({
                "optimized_length": len(optimized_content),
                "title_optimized": optimized_title != title,
                "compression_ratio": len(optimized_content) / len(content) if content else 1.0,
                "word_count": len(optimized_content.split()),
                "estimated_reading_time": self._calculate_reading_time(optimized_content)
            })
            
            # Combine title and content if title was optimized
            if optimized_title and optimized_title != title:
                final_content = f"# {optimized_title}\n\n{optimized_content}"
            else:
                final_content = optimized_content
            
            self.logger.info(f"Content optimization completed successfully")
            
            return OptimizationResult(
                success=True,
                optimized_content=final_content,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Content optimization failed: {e}")
            return OptimizationResult(False, error=str(e))
    
    def _get_optimization_rules(self, level: str, custom_rules: List[str] = None) -> List[str]:
        """Get optimization rules based on level and custom rules."""
        
        rule_sets = {
            "basic": ["format_cleanup"],
            "standard": ["format_cleanup", "paragraph_optimization", "tag_generation"],
            "advanced": ["format_cleanup", "title_optimization", "paragraph_optimization", 
                        "tag_generation", "seo_optimization", "platform_adaptation"]
        }
        
        rules = rule_sets.get(level, rule_sets["standard"])
        
        if custom_rules:
            # Add custom rules if they exist in our optimization_rules
            for rule in custom_rules:
                if rule in self.optimization_rules and rule not in rules:
                    rules.append(rule)
        
        return rules
    
    async def _format_cleanup(self, content: str, platform: str) -> str:
        """Clean up content formatting."""
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        content = re.sub(r'[ \t]+', ' ', content)
        
        # Fix common formatting issues
        content = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', content)
        content = re.sub(r'([，。！？])\s+', r'\1', content)
        
        # Remove markdown artifacts that don't work well on Chinese platforms
        content = re.sub(r'\*\*(.*?)\*\*', r'【\1】', content)  # Bold to Chinese brackets
        content = re.sub(r'\*(.*?)\*', r'"\1"', content)  # Italic to quotes
        
        return content.strip()
    
    async def _optimize_title(self, title: str, platform: str) -> str:
        """Optimize title for Chinese platforms."""
        if not title:
            return title
        
        # Platform-specific title optimization
        if platform == "toutiao":
            # 今日头条喜欢有吸引力的标题
            if not any(char in title for char in "！？【】"):
                # Add emphasis if not already present
                if "AI" in title or "人工智能" in title:
                    title = f"【AI前沿】{title}"
                elif "技术" in title or "开发" in title:
                    title = f"【技术分享】{title}"
        
        elif platform == "weixin":
            # 微信公众号标题优化
            if len(title) > 30:
                title = title[:27] + "..."
        
        elif platform == "zhihu":
            # 知乎标题优化，更学术化
            if not title.endswith("？") and "如何" not in title and "什么" not in title:
                if "AI" in title:
                    title = f"如何理解{title}？"
        
        return title
    
    async def _optimize_paragraphs(self, content: str, platform: str) -> str:
        """Optimize paragraph structure for readability."""
        paragraphs = content.split('\n\n')
        optimized_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Split overly long paragraphs
            if len(para) > 300 and platform in ["toutiao", "weixin"]:
                sentences = re.split(r'([。！？])', para)
                current_para = ""
                
                for i in range(0, len(sentences), 2):
                    if i + 1 < len(sentences):
                        sentence = sentences[i] + sentences[i + 1]
                    else:
                        sentence = sentences[i]
                    
                    if len(current_para + sentence) > 200:
                        if current_para:
                            optimized_paragraphs.append(current_para.strip())
                        current_para = sentence
                    else:
                        current_para += sentence
                
                if current_para:
                    optimized_paragraphs.append(current_para.strip())
            else:
                optimized_paragraphs.append(para)
        
        return '\n\n'.join(optimized_paragraphs)
    
    async def _generate_tags(self, content: str, platform: str) -> str:
        """Generate relevant tags for the content."""
        # Extract potential tags from content
        tech_keywords = [
            "AI", "人工智能", "机器学习", "深度学习", "神经网络",
            "Python", "JavaScript", "React", "Vue", "Node.js",
            "数据科学", "算法", "编程", "开发", "技术",
            "区块链", "云计算", "大数据", "物联网"
        ]
        
        found_tags = []
        content_lower = content.lower()
        
        for keyword in tech_keywords:
            if keyword.lower() in content_lower or keyword in content:
                found_tags.append(keyword)
                if len(found_tags) >= 5:  # Limit to 5 tags
                    break
        
        if found_tags:
            tags_section = f"\n\n---\n标签: {' '.join([f'#{tag}' for tag in found_tags])}"
            return content + tags_section
        
        return content
    
    async def _seo_optimization(self, content: str, platform: str) -> str:
        """Apply SEO optimization for better discoverability."""
        # Add keyword density optimization
        # Add internal linking suggestions
        # Add meta description equivalent
        
        # For now, just add a summary at the beginning for long articles
        if len(content) > 1000:
            # Extract first meaningful paragraph as summary
            paragraphs = content.split('\n\n')
            first_para = next((p for p in paragraphs if len(p.strip()) > 50), "")
            
            if first_para and not content.startswith("摘要"):
                summary = f"**摘要**: {first_para[:100]}...\n\n"
                return summary + content
        
        return content
    
    async def _adapt_for_platform(self, content: str, platform: str) -> str:
        """Adapt content for specific platform requirements."""
        
        if platform == "toutiao":
            # 今日头条适配
            # 添加互动元素
            if not content.endswith("你怎么看？"):
                content += "\n\n你对这个话题有什么看法？欢迎在评论区分享你的观点！"
        
        elif platform == "weixin":
            # 微信公众号适配
            # 添加关注提醒
            if "关注" not in content:
                content += "\n\n---\n如果觉得这篇文章对你有帮助，请点赞并关注我们，获取更多优质内容！"
        
        elif platform == "zhihu":
            # 知乎适配
            # 添加专业性声明
            content += "\n\n---\n以上内容仅代表个人观点，欢迎理性讨论。"
        
        return content
    
    def _calculate_reading_time(self, content: str) -> int:
        """Calculate estimated reading time in minutes."""
        # Chinese reading speed: approximately 300-400 characters per minute
        char_count = len(content)
        reading_time = max(1, round(char_count / 350))
        return reading_time


# Global optimizer instance
_optimizer_instance = None


def get_content_optimizer() -> ContentOptimizer:
    """Get the global content optimizer instance."""
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = ContentOptimizer()
    return _optimizer_instance
