"""
Large Language Model API service integration.
"""

import asyncio
import logging
import json
import traceback
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from datetime import datetime
import aiohttp


@dataclass
class LLMResponse:
    """LLM API response."""
    content: str
    success: bool = True
    error: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None
    model: Optional[str] = None
    finish_reason: Optional[str] = None


class LLMAPIService:
    """Large Language Model API service."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = "http://localhost:8000/v1/chat/completions"
        self.api_key = "sk-dummy-f4689c69ad5746a8bb5b5e897b4033c7"
        self.timeout = aiohttp.ClientTimeout(total=300, connect=30, sock_read=60)  # 5 minutes total, 30s connect, 60s read
        self.default_model = "Claude-4-Sonnet"  # 使用Claude-4-Sonnet模型
        
    async def translate_content(
        self, 
        content: str, 
        title: str = "", 
        source_language: str = "en", 
        target_language: str = "zh",
        custom_prompt: str = ""
    ) -> LLMResponse:
        """
        Translate article content.
        
        Args:
            content: Content to translate
            title: Article title
            source_language: Source language code
            target_language: Target language code
            custom_prompt: Custom translation prompt
            
        Returns:
            LLMResponse with translated content
        """
        try:
            self.logger.info(f"Starting content translation from {source_language} to {target_language}")
            
            # Build translation prompt
            if custom_prompt:
                prompt = custom_prompt
            else:
                prompt = self._build_translation_prompt(content, title, source_language, target_language)
            
            # Call LLM API
            response = await self._call_api(prompt)
            
            if response.success:
                self.logger.info("Content translation completed successfully")
            else:
                self.logger.error(f"Content translation failed: {response.error}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Translation error: {e}")
            return LLMResponse(
                content="",
                success=False,
                error=str(e)
            )
    
    async def optimize_content(
        self, 
        content: str, 
        title: str = "", 
        platform: str = "toutiao",
        optimization_type: str = "standard",
        custom_prompt: str = ""
    ) -> LLMResponse:
        """
        Optimize article content for specific platform.
        
        Args:
            content: Content to optimize
            title: Article title
            platform: Target platform (toutiao, weixin, etc.)
            optimization_type: Type of optimization (standard, seo, engagement)
            custom_prompt: Custom optimization prompt
            
        Returns:
            LLMResponse with optimized content
        """
        try:
            self.logger.info(f"Starting content optimization for platform: {platform}")
            
            # Build optimization prompt
            if custom_prompt:
                prompt = custom_prompt
            else:
                prompt = self._build_optimization_prompt(content, title, platform, optimization_type)
            
            # Call LLM API
            response = await self._call_api(prompt)
            
            if response.success:
                self.logger.info("Content optimization completed successfully")
            else:
                self.logger.error(f"Content optimization failed: {response.error}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Optimization error: {e}")
            return LLMResponse(
                content="",
                success=False,
                error=str(e)
            )

    async def create_content_by_topic(
        self,
        topic: str,
        keywords: list = None,
        requirements: str = "",
        custom_prompt: str = None,
        model: str = None,
        target_length: str = "mini",
        **api_params
    ) -> LLMResponse:
        """Create content based on topic using LLM API."""
        try:
            self.logger.info(f"🎨 开始主题内容创作: {topic}")
            self.logger.info(f"📏 目标长度: {target_length}")

            # 定义目标长度映射
            length_mapping = {
                "mini": {"words": "300-500", "description": "简短文章"},
                "short": {"words": "500-800", "description": "短篇文章"},
                "medium": {"words": "800-1500", "description": "中等长度文章"},
                "long": {"words": "1500-3000", "description": "长篇文章"}
            }

            length_info = length_mapping.get(target_length, length_mapping["mini"])
            self.logger.info(f"📊 字数要求: {length_info['words']} 字 ({length_info['description']})")

            if custom_prompt:
                # 处理自定义提示词，添加长度要求
                self.logger.info("📝 使用自定义创作提示词")

                # 检查是否包含长度变量占位符
                if "{target_length}" in custom_prompt:
                    prompt = custom_prompt.format(target_length=length_info['words'])
                    self.logger.info("✅ 已填充目标长度变量")
                elif "字数" not in custom_prompt and "长度" not in custom_prompt:
                    # 如果自定义提示词没有长度要求，添加长度指导
                    prompt = custom_prompt + f"\n\n**字数要求：** 请控制文章字数在 {length_info['words']} 字之间。"
                    self.logger.info("✅ 已添加字数要求到自定义提示词")
                else:
                    prompt = custom_prompt
                    self.logger.info("ℹ️  自定义提示词已包含长度要求")
            else:
                # Build default creation prompt with target length
                self.logger.info("📝 使用默认创作提示词")
                prompt_parts = [
                    "你是一位专业的内容创作专家。请根据以下要求创作一篇高质量的文章：",
                    "",
                    f"主题：{topic}",
                ]

                if keywords:
                    prompt_parts.append(f"关键词：{', '.join(keywords)}")

                if requirements:
                    prompt_parts.append(f"创作要求：{requirements}")

                # 添加字数要求
                prompt_parts.append(f"字数要求：{length_info['words']} 字")

                prompt_parts.extend([
                    "",
                    "请确保文章：",
                    "1. 内容原创且有深度",
                    "2. 结构清晰，逻辑性强",
                    "3. 语言流畅，符合中文表达习惯",
                    "4. 包含实用价值和见解",
                    f"5. 字数严格控制在 {length_info['words']} 字之间",
                    "",
                    "请直接输出文章内容，不需要额外的说明。"
                ])

                prompt = "\n".join(prompt_parts)

            # Call LLM API with configurable parameters
            result = await self._call_api(prompt, model, **api_params)

            if result.success:
                self.logger.info("✅ 主题内容创作成功")
                self.logger.info(f"📝 创作内容长度: {len(result.content)} 字符")

                # Try to extract title from content if possible
                lines = result.content.strip().split('\n')
                potential_title = lines[0].strip() if lines else ""

                # Simple heuristic to detect if first line is a title
                if (len(potential_title) < 100 and
                    not potential_title.endswith('。') and
                    not potential_title.endswith('.') and
                    len(lines) > 1):
                    result.title = potential_title
                    result.content = '\n'.join(lines[1:]).strip()
                    self.logger.info(f"📰 提取到标题: {potential_title}")

            return result

        except Exception as e:
            self.logger.error(f"💥 主题内容创作异常: {str(e)}")
            return LLMResponse(
                success=False,
                content="",
                message=f"主题内容创作失败: {str(e)}"
            )

    async def _call_api(self, prompt: str, model: str = None, **kwargs) -> LLMResponse:
        """Call the LLM API with improved error handling and configurable parameters."""
        try:
            self.logger.info(f"🚀 开始调用LLM API...")
            self.logger.info(f"🔗 API地址: {self.base_url}")
            self.logger.info(f"🤖 使用模型: {model or self.default_model}")

            # 全量显示发送给API的提示词内容
            self.logger.info("📤 发送给LLM的完整提示词内容:")
            self.logger.info("=" * 80)
            self.logger.info(prompt)
            self.logger.info("=" * 80)

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # 可配置的API参数，支持通过kwargs传递
            # Claude的最大tokens限制约为200k，设置为较大值以避免截断
            default_max_tokens = 100000  # 使用较大的默认值

            payload = {
                "model": model or self.default_model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": kwargs.get('temperature', 0.7),
                "max_tokens": kwargs.get('max_tokens', default_max_tokens),
                "top_p": kwargs.get('top_p', 1.0),
                "frequency_penalty": kwargs.get('frequency_penalty', 0.0),
                "presence_penalty": kwargs.get('presence_penalty', 0.0)
            }

            self.logger.info(f"📊 请求参数:")
            self.logger.info(f"   🌡️  温度: {payload['temperature']}")
            self.logger.info(f"   📏 最大tokens: {payload['max_tokens']}")
            self.logger.info(f"   🎯 top_p: {payload['top_p']}")
            self.logger.info(f"   🔄 frequency_penalty: {payload['frequency_penalty']}")
            self.logger.info(f"   👥 presence_penalty: {payload['presence_penalty']}")

            self.logger.info(f"📦 请求载荷大小: {len(str(payload))} 字符")

            # Use connector with proper settings to avoid connection issues
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=5,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )

            async with aiohttp.ClientSession(
                timeout=self.timeout,
                connector=connector,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            ) as session:
                self.logger.info("🌐 正在发送API请求...")
                async with session.post(self.base_url, headers=headers, json=payload) as response:
                    self.logger.info(f"📡 收到响应，状态码: {response.status}")

                    if response.status == 200:
                        # Check content type to determine how to parse response
                        content_type = response.headers.get('content-type', '')
                        self.logger.info(f"📋 响应内容类型: {content_type}")

                        if 'text/event-stream' in content_type:
                            # Handle Server-Sent Events (SSE) streaming response
                            self.logger.info("🌊 检测到流式响应，开始处理SSE数据...")
                            content = await self._parse_sse_response(response)
                            return LLMResponse(
                                content=content,
                                success=True,
                                error=""
                            )
                        else:
                            # Handle standard JSON response
                            data = await response.json()
                            self.logger.info("✅ API调用成功，正在解析JSON响应...")
                            return self._parse_api_response(data)
                    else:
                        error_text = await response.text()
                        self.logger.error(f"❌ API请求失败，状态码: {response.status}")
                        self.logger.error(f"💬 错误详情: {error_text}")
                        return LLMResponse(
                            content="",
                            success=False,
                            error=f"API request failed: {response.status} - {error_text}"
                        )

        except asyncio.CancelledError:
            self.logger.error("⚠️ API调用被取消")
            return LLMResponse(
                content="",
                success=False,
                error="API call was cancelled"
            )
        except asyncio.TimeoutError:
            self.logger.error("⏰ API调用超时")
            return LLMResponse(
                content="",
                success=False,
                error="API call timed out"
            )
        except Exception as e:
            self.logger.error(f"💥 API调用异常: {e}")
            import traceback
            self.logger.error(f"💥 异常堆栈: {traceback.format_exc()}")
            return LLMResponse(
                content="",
                success=False,
                error=str(e)
            )

    async def _parse_sse_response(self, response) -> str:
        """Parse Server-Sent Events (SSE) streaming response."""
        try:
            self.logger.info("🔄 开始解析SSE流式响应...")
            content_parts = []

            async for line in response.content:
                line_str = line.decode('utf-8').strip()

                if line_str.startswith('data: '):
                    data_str = line_str[6:]  # Remove 'data: ' prefix

                    if data_str == '[DONE]':
                        self.logger.info("✅ SSE流结束")
                        break

                    try:
                        import json
                        data = json.loads(data_str)

                        # Extract content from the streaming response
                        if 'choices' in data and len(data['choices']) > 0:
                            choice = data['choices'][0]
                            if 'delta' in choice and 'content' in choice['delta']:
                                content_chunk = choice['delta']['content']
                                content_parts.append(content_chunk)
                                self.logger.debug(f"📝 收到内容块: {content_chunk[:50]}...")
                            elif 'message' in choice and 'content' in choice['message']:
                                # Handle non-streaming format
                                content_chunk = choice['message']['content']
                                content_parts.append(content_chunk)
                                self.logger.debug(f"📝 收到完整内容: {content_chunk[:50]}...")

                    except json.JSONDecodeError as e:
                        self.logger.debug(f"⚠️ 跳过非JSON行: {line_str[:100]}...")
                        continue

            full_content = ''.join(content_parts)
            self.logger.info(f"✅ SSE解析完成，总内容长度: {len(full_content)} 字符")
            return full_content

        except Exception as e:
            self.logger.error(f"💥 SSE解析异常: {e}")
            # Fallback: try to read as plain text
            try:
                text_content = await response.text()
                self.logger.info("🔄 尝试作为纯文本读取...")
                return text_content
            except Exception as fallback_e:
                self.logger.error(f"💥 纯文本读取也失败: {fallback_e}")
                return ""

    def _parse_api_response(self, data: Dict[str, Any]) -> LLMResponse:
        """Parse API response."""
        try:
            choices = data.get("choices", [])
            if not choices:
                return LLMResponse(
                    content="",
                    success=False,
                    error="No choices in API response"
                )
            
            choice = choices[0]
            message = choice.get("message", {})
            content = message.get("content", "").strip()
            
            usage = data.get("usage", {})
            model = data.get("model", "")
            finish_reason = choice.get("finish_reason", "")
            
            return LLMResponse(
                content=content,
                success=True,
                usage=usage,
                model=model,
                finish_reason=finish_reason
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing API response: {e}")
            return LLMResponse(
                content="",
                success=False,
                error=f"Error parsing response: {str(e)}"
            )
    
    def _build_translation_prompt(
        self, 
        content: str, 
        title: str, 
        source_lang: str, 
        target_lang: str
    ) -> str:
        """Build translation prompt."""
        lang_names = {
            "en": "英文",
            "zh": "中文",
            "ja": "日文",
            "ko": "韩文"
        }
        
        source_name = lang_names.get(source_lang, source_lang)
        target_name = lang_names.get(target_lang, target_lang)
        
        prompt = f"""请将以下{source_name}文章翻译成{target_name}，要求：

1. 保持原文的语义和语调
2. 使用自然流畅的{target_name}表达
3. 保留专业术语的准确性
4. 适当调整句式以符合{target_name}阅读习惯
5. 保持段落结构不变

"""
        
        if title:
            prompt += f"文章标题：{title}\n\n"
        
        prompt += f"文章内容：\n{content}\n\n请直接输出翻译结果，不要添加任何解释或说明。"
        
        return prompt
    
    def _build_optimization_prompt(
        self, 
        content: str, 
        title: str, 
        platform: str, 
        optimization_type: str
    ) -> str:
        """Build content optimization prompt."""
        platform_rules = {
            "toutiao": "今日头条平台特点：标题要吸引眼球，内容要有争议性和话题性，适合大众阅读",
            "weixin": "微信公众号平台特点：内容要有价值，标题要精准，适合分享传播",
            "zhihu": "知乎平台特点：内容要专业深入，逻辑清晰，有知识价值",
            "xiaohongshu": "小红书平台特点：内容要生活化，有实用价值，适合年轻用户"
        }
        
        optimization_rules = {
            "standard": "标准优化：提升可读性，优化结构，增强吸引力",
            "seo": "SEO优化：增加关键词密度，优化标题和段落结构",
            "engagement": "互动优化：增加互动元素，提升用户参与度"
        }
        
        platform_rule = platform_rules.get(platform, "通用平台优化")
        optimization_rule = optimization_rules.get(optimization_type, "标准优化")
        
        prompt = f"""请对以下文章内容进行优化，要求：

平台特点：{platform_rule}
优化类型：{optimization_rule}

优化要求：
1. 保持原文核心观点和信息不变
2. 优化语言表达，使其更符合平台特色
3. 调整段落结构，提升阅读体验
4. 增加适当的过渡词和连接词
5. 确保内容原创性，避免AI痕迹过重

"""
        
        if title:
            prompt += f"原标题：{title}\n\n"
        
        prompt += f"原文内容：\n{content}\n\n请直接输出优化后的内容，不要添加任何解释或说明。"
        
        return prompt


# Service instance
_llm_service = None

def get_llm_service() -> LLMAPIService:
    """Get LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMAPIService()
    return _llm_service
