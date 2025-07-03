# -*- coding: utf-8 -*-
"""
真正的AI API调用服务
使用HTTP请求调用实际的API接口
"""

import asyncio
import logging
import json
import aiohttp
from typing import Dict, Any, Optional


class RealAIAPICall:
    """真正的AI API调用服务"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = "http://localhost:8000/v1/chat/completions"
        self.api_key = "sk-dummy-f4689c69ad5746a8bb5b5e897b4033c7"
        self.timeout = aiohttp.ClientTimeout(total=60)
    
    async def call_ai_api(
        self,
        messages: list,
        model: str = "Claude-4-Sonnet",
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        调用AI API接口
        
        Args:
            messages: 消息列表，格式如 [{"role": "user", "content": "..."}]
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            API响应结果
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        try:
            self.logger.info("🚀 开始调用AI API...")
            self.logger.info(f"🌐 API地址: {self.base_url}")
            self.logger.info(f"🔑 API Key: {self.api_key[:10]}...***")
            self.logger.info(f"🤖 模型: {model}")
            self.logger.info(f"📝 消息数量: {len(messages)}")
            self.logger.info(f"💬 用户消息预览: {messages[-1]['content'][:100]}..." if messages else "无消息")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    self.base_url,
                    headers=headers,
                    json=payload
                ) as response:
                    
                    self.logger.info(f"📡 HTTP状态码: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        self.logger.info("✅ API调用成功!")
                        
                        # 提取AI回复
                        if "choices" in result and len(result["choices"]) > 0:
                            ai_response = result["choices"][0]["message"]["content"]
                            self.logger.info(f"🎯 AI回复长度: {len(ai_response)} 字符")
                            self.logger.info(f"🎯 AI回复预览: {ai_response[:200]}...")
                            
                            # 记录token使用情况
                            if "usage" in result:
                                usage = result["usage"]
                                self.logger.info(f"📊 Token使用: 提示={usage.get('prompt_tokens', 0)}, 完成={usage.get('completion_tokens', 0)}, 总计={usage.get('total_tokens', 0)}")
                        
                        return {
                            "success": True,
                            "response": result,
                            "ai_reply": ai_response if "choices" in result and len(result["choices"]) > 0 else "",
                            "usage": result.get("usage", {})
                        }
                    else:
                        error_text = await response.text()
                        self.logger.error(f"❌ API调用失败: HTTP {response.status}")
                        self.logger.error(f"❌ 错误详情: {error_text}")
                        
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text}",
                            "ai_reply": ""
                        }
                        
        except asyncio.TimeoutError:
            error_msg = "API调用超时"
            self.logger.error(f"⏰ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "ai_reply": ""
            }
            
        except Exception as e:
            error_msg = f"API调用异常: {str(e)}"
            self.logger.error(f"💥 {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "ai_reply": ""
            }
    
    async def translate_text(self, text: str, target_language: str = "中文") -> Dict[str, Any]:
        """
        翻译文本
        
        Args:
            text: 要翻译的文本
            target_language: 目标语言
            
        Returns:
            翻译结果
        """
        messages = [
            {
                "role": "system",
                "content": f"你是一位专业的翻译专家，请将用户提供的文本翻译成{target_language}。要求翻译准确、流畅、自然。"
            },
            {
                "role": "user", 
                "content": f"请将以下文本翻译成{target_language}：\n\n{text}"
            }
        ]
        
        self.logger.info(f"🌐 开始翻译文本（目标语言：{target_language}）...")
        result = await self.call_ai_api(messages)
        
        if result["success"]:
            self.logger.info("✅ 翻译完成!")
            return {
                "success": True,
                "translated_text": result["ai_reply"],
                "original_text": text,
                "target_language": target_language,
                "usage": result.get("usage", {})
            }
        else:
            self.logger.error(f"❌ 翻译失败: {result['error']}")
            return {
                "success": False,
                "error": result["error"],
                "translated_text": "",
                "original_text": text
            }
    
    async def optimize_content(self, content: str, requirements: str = "") -> Dict[str, Any]:
        """
        优化内容
        
        Args:
            content: 要优化的内容
            requirements: 优化要求
            
        Returns:
            优化结果
        """
        default_requirements = "请优化以下内容，使其更加流畅、自然、易读，保持原意不变"
        actual_requirements = requirements or default_requirements
        
        messages = [
            {
                "role": "system",
                "content": "你是一位专业的内容编辑专家，擅长优化文章内容，使其更加流畅、自然、易读。"
            },
            {
                "role": "user",
                "content": f"{actual_requirements}：\n\n{content}"
            }
        ]
        
        self.logger.info("✨ 开始优化内容...")
        result = await self.call_ai_api(messages)
        
        if result["success"]:
            self.logger.info("✅ 内容优化完成!")
            return {
                "success": True,
                "optimized_content": result["ai_reply"],
                "original_content": content,
                "requirements": actual_requirements,
                "usage": result.get("usage", {})
            }
        else:
            self.logger.error(f"❌ 内容优化失败: {result['error']}")
            return {
                "success": False,
                "error": result["error"],
                "optimized_content": "",
                "original_content": content
            }

    async def translate_and_classify_article(
        self,
        title: str,
        content: str,
        source_url: str = "",
        target_language: str = "中文"
    ) -> Dict[str, Any]:
        """
        翻译文章并同时进行智能分类

        Args:
            title: 文章标题
            content: 文章内容
            source_url: 文章来源URL
            target_language: 目标语言

        Returns:
            包含翻译结果和分类结果的字典
        """

        # 构建智能分类和翻译的提示词
        classification_prompt = f"""
请完成以下两个任务：

1. **文章翻译**：将文章翻译成{target_language}，保持原文的语气、风格和专业术语的准确性。

2. **文章分类**：基于文章的标题、内容和来源，将文章分类到以下类别之一：
   - technical: 技术类文章（编程、开发、API、算法、软件工程等）
   - tutorial: 教程类文章（如何做、步骤指南、学习教程等）
   - news: 新闻类文章（最新消息、发布公告、行业动态等）
   - business: 商业类文章（商业分析、市场趋势、企业管理等）
   - lifestyle: 生活类文章（生活方式、健康、旅行等）
   - entertainment: 娱乐类文章（娱乐新闻、影视、游戏等）
   - general: 通用类文章（不属于以上任何类别的文章）

请按照以下JSON格式返回结果：
```json
{{
    "translated_title": "翻译后的标题",
    "translated_content": "翻译后的内容",
    "classification": {{
        "category": "分类类别（如technical、tutorial等）",
        "confidence": 0.95,
        "reasoning": "分类理由的简短说明"
    }}
}}
```

**原文信息：**
标题：{title}
来源：{source_url}

内容：
{content[:2000]}{"..." if len(content) > 2000 else ""}
"""

        messages = [
            {
                "role": "system",
                "content": "你是一位专业的翻译专家和内容分析师，能够准确翻译文章并智能分类内容类型。请严格按照JSON格式返回结果。"
            },
            {
                "role": "user",
                "content": classification_prompt
            }
        ]

        self.logger.info(f"🤖 开始智能翻译和分类（目标语言：{target_language}）...")
        result = await self.call_ai_api(messages, max_tokens=4000)

        if result["success"]:
            try:
                # 尝试解析JSON响应
                import json
                import re

                ai_response = result["ai_reply"]
                self.logger.info(f"🔍 AI响应内容: {ai_response[:200]}...")

                # 提取JSON部分
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    # 如果没有找到代码块，尝试查找JSON对象
                    json_match = re.search(r'(\{[^{}]*"translated_title"[^{}]*\})', ai_response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                    else:
                        # 最后尝试直接解析整个响应
                        json_str = ai_response.strip()

                # 清理JSON字符串，但保留字符串内容中的换行符
                # 只清理JSON结构外的多余空格和换行符
                json_str = json_str.strip()

                # 尝试修复常见的JSON格式问题
                # 1. 确保字符串值中的换行符被正确转义
                # 2. 移除JSON结构外的多余空格
                lines = json_str.split('\n')
                cleaned_lines = []
                in_string = False
                escape_next = False

                for line in lines:
                    if not in_string:
                        # 在JSON结构外，清理多余空格
                        line = line.strip()

                    # 检查是否在字符串内部
                    for char in line:
                        if escape_next:
                            escape_next = False
                            continue
                        if char == '\\':
                            escape_next = True
                        elif char == '"' and not escape_next:
                            in_string = not in_string

                    if line:  # 只添加非空行
                        cleaned_lines.append(line)

                json_str = '\n'.join(cleaned_lines)

                parsed_result = json.loads(json_str)

                self.logger.info("✅ 智能翻译和分类完成!")
                return {
                    "success": True,
                    "translated_title": parsed_result.get("translated_title", title),
                    "translated_content": parsed_result.get("translated_content", content),
                    "classification": {
                        "category": parsed_result.get("classification", {}).get("category", "general"),
                        "confidence": parsed_result.get("classification", {}).get("confidence", 0.8),
                        "reasoning": parsed_result.get("classification", {}).get("reasoning", "AI智能分析"),
                        "method": "ai_llm"
                    },
                    "original_title": title,
                    "original_content": content,
                    "source_url": source_url,
                    "target_language": target_language,
                    "usage": result.get("usage", {}),
                    "raw_response": ai_response
                }

            except json.JSONDecodeError as e:
                self.logger.error(f"❌ JSON解析失败: {e}")
                self.logger.error(f"原始响应: {result['ai_reply']}")

                # 尝试从失败的JSON响应中提取翻译内容
                ai_response = result["ai_reply"]
                extracted_title = title
                extracted_content = content

                try:
                    # 尝试提取JSON中的翻译内容
                    import re

                    # 提取translated_title
                    title_match = re.search(r'"translated_title":\s*"([^"]*)"', ai_response)
                    if title_match:
                        extracted_title = title_match.group(1)
                        self.logger.info(f"✅ 从失败JSON中提取到标题: {extracted_title}")

                    # 提取translated_content
                    content_match = re.search(r'"translated_content":\s*"([^"]*)"', ai_response, re.DOTALL)
                    if content_match:
                        extracted_content = content_match.group(1)
                        # 处理转义字符
                        extracted_content = extracted_content.replace('\\n', '\n').replace('\\"', '"')
                        self.logger.info(f"✅ 从失败JSON中提取到内容，长度: {len(extracted_content)} 字符")
                    else:
                        # 如果无法提取，尝试查找中文内容
                        chinese_content = re.findall(r'[\u4e00-\u9fff]+[^"]*', ai_response)
                        if chinese_content:
                            extracted_content = ' '.join(chinese_content)
                            self.logger.info(f"✅ 从失败JSON中提取到中文内容，长度: {len(extracted_content)} 字符")
                        else:
                            self.logger.warning("⚠️ 无法从失败JSON中提取翻译内容，使用原文")
                            extracted_content = content

                except Exception as extract_error:
                    self.logger.error(f"❌ 内容提取失败: {extract_error}")
                    extracted_content = content

                # 降级处理：返回提取的翻译结果
                return {
                    "success": True,
                    "translated_title": extracted_title,
                    "translated_content": extracted_content,
                    "classification": {
                        "category": "general",
                        "confidence": 0.5,
                        "reasoning": "JSON解析失败，使用内容提取",
                        "method": "fallback_extraction"
                    },
                    "original_title": title,
                    "original_content": content,
                    "source_url": source_url,
                    "target_language": target_language,
                    "usage": result.get("usage", {}),
                    "raw_response": result["ai_reply"],
                    "parse_error": str(e)
                }

        else:
            self.logger.error(f"❌ 智能翻译和分类失败: {result['error']}")
            return {
                "success": False,
                "error": result["error"],
                "translated_title": title,
                "translated_content": content,
                "classification": {
                    "category": "general",
                    "confidence": 0.0,
                    "reasoning": "API调用失败",
                    "method": "error"
                }
            }


# Service instance
_real_ai_api_call = None

def get_real_ai_api_call() -> RealAIAPICall:
    """Get real AI API call service instance."""
    global _real_ai_api_call
    if _real_ai_api_call is None:
        _real_ai_api_call = RealAIAPICall()
    return _real_ai_api_call
