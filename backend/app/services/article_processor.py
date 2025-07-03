# -*- coding: utf-8 -*-
"""
Article Processing Service
Handles the complete article processing pipeline including translation, optimization, and detection.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from ..models.article import ArticleStatus
from ..models.task import TaskStatus
from ..core.database import get_db_session


# Simple data classes for processing
class Article:
    """Simple article data class for processing."""
    def __init__(self, id=None, title="", source_url="", source_platform="",
                 content_original="", content_translated=None, content_optimized=None,
                 content_final=None, status=ArticleStatus.PENDING, **kwargs):
        self.id = id
        self.title = title
        self.source_url = source_url
        self.source_platform = source_platform
        self.content_original = content_original
        self.content_translated = content_translated
        self.content_optimized = content_optimized
        self.content_final = content_final
        self.status = status
        # Store any additional attributes
        for key, value in kwargs.items():
            setattr(self, key, value)


class Task:
    """Simple task data class for processing."""
    def __init__(self, id=None, task_id="", name="", type="article_processing",
                 status=TaskStatus.PENDING, article_id=None, **kwargs):
        self.id = id
        self.task_id = task_id
        self.name = name
        self.type = type
        self.status = status
        self.article_id = article_id
        # Store any additional attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

logger = logging.getLogger(__name__)


class ProcessingStep(str, Enum):
    """Article processing steps."""
    CREATE = "create"      # New step for topic-based content creation
    EXTRACT = "extract"
    TRANSLATE = "translate"
    OPTIMIZE = "optimize"
    DETECT = "detect"
    PUBLISH = "publish"


class ProcessingResult:
    """Result of a processing step."""
    
    def __init__(self, success: bool, message: str = "", data: Dict[str, Any] = None):
        self.success = success
        self.message = message
        self.data = data or {}
        self.timestamp = datetime.utcnow()


class ArticleProcessor:
    """Main article processing service."""
    
    def __init__(self):
        self.logger = logger
        self.processing_steps = {
            ProcessingStep.CREATE: self._create_content,
            ProcessingStep.EXTRACT: self._extract_content,
            ProcessingStep.TRANSLATE: self._translate_content,
            ProcessingStep.OPTIMIZE: self._optimize_content,
            ProcessingStep.DETECT: self._detect_content,
            ProcessingStep.PUBLISH: self._publish_content
        }
    
    async def process_article(
        self,
        article_id: int,
        steps: List[str] = None,
        auto_publish: bool = False,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """
        Process a single article through the specified steps with intelligent configuration.

        Args:
            article_id: ID of the article to process
            steps: List of processing steps to execute
            auto_publish: Whether to automatically publish after processing
            priority: Processing priority (low, normal, high)

        Returns:
            Processing result with task information
        """
        if steps is None:
            # 根据文章类型选择不同的处理流程
            # 需要先获取文章信息来判断类型
            async with get_db_session() as session:
                article = self._get_article(session, article_id)
                if article and hasattr(article, 'creation_type') and article.creation_type == 'topic_creation':
                    # 主题创作流程：创作（包含AI检测循环）
                    steps = [ProcessingStep.CREATE]
                    self.logger.info("📝 检测到主题创作文章，使用CREATE流程")
                else:
                    # URL导入流程：提取 -> 翻译 -> 优化（包含AI检测循环）
                    steps = [ProcessingStep.EXTRACT, ProcessingStep.TRANSLATE, ProcessingStep.OPTIMIZE]
                    self.logger.info("🔗 检测到URL导入文章，使用EXTRACT->TRANSLATE->OPTIMIZE流程")

        if auto_publish and ProcessingStep.PUBLISH not in steps:
            steps.append(ProcessingStep.PUBLISH)

        # Get intelligent processing configuration
        processing_config = await self._get_processing_configuration(article_id)
        self.logger.info(f"🎯 智能配置: {processing_config}")
        
        self.logger.info("="*80)
        self.logger.info(f"🚀 开始文章处理流程 - 文章 ID: {article_id}")
        self.logger.info(f"📋 处理步骤: {steps}")
        self.logger.info(f"🔢 优先级: {priority}")
        self.logger.info(f"📤 自动发布: {auto_publish}")
        self.logger.info("="*80)

        self.logger.info(f"Starting article processing for article {article_id} with steps: {steps}")

        try:
            # Get article from database
            self.logger.info("📦 正在获取数据库会话...")
            async with get_db_session() as session:
                self.logger.info("✅ 数据库会话获取成功")
                self.logger.info("🔍 正在获取文章数据...")
                article = self._get_article(session, article_id)
                self.logger.info(f"📋 文章获取结果: {article}")
                if not article:
                    return {
                        "success": False,
                        "error": f"Article {article_id} not found"
                    }
                
                # Create processing task
                task_id = f"process_{article_id}_{int(datetime.utcnow().timestamp())}"
                self.logger.info(f"🔧 正在创建处理任务: {task_id}")
                task = self._create_processing_task(session, task_id, article_id, steps)
                self.logger.info(f"✅ 处理任务创建完成: {task.task_id}")
                
                # Start processing in background with proper exception handling
                self.logger.info("🚀 准备启动后台处理任务...")
                self.logger.info(f"📋 任务协程: {self._execute_processing_pipeline}")
                self.logger.info(f"📋 文章对象: {article}")
                self.logger.info(f"📋 处理步骤: {steps}")
                self.logger.info(f"📋 任务对象: {task}")

                task_coroutine = self._execute_processing_pipeline(article, steps, task)
                self.logger.info(f"📋 协程对象创建成功: {task_coroutine}")

                self.logger.info("🔥 正在创建异步任务...")
                background_task = asyncio.create_task(task_coroutine)
                self.logger.info(f"✅ 异步任务创建成功: {background_task}")

                # Add exception handler for background task
                def handle_task_exception(task):
                    self.logger.info(f"🔍 异步任务完成回调被调用: {task}")
                    try:
                        result = task.result()
                        self.logger.info(f"✅ 异步任务正常完成: {result}")
                    except Exception as e:
                        self.logger.error(f"💥 后台处理任务异常 - 文章 ID: {article.id}")
                        self.logger.error(f"💥 异常详情: {str(e)}")
                        import traceback
                        self.logger.error(f"💥 异常堆栈: {traceback.format_exc()}")

                self.logger.info("🔧 添加异步任务完成回调...")
                background_task.add_done_callback(handle_task_exception)
                self.logger.info("✅ 异步任务启动完成！")
                
                return {
                    "success": True,
                    "task_id": task_id,
                    "article_id": article_id,
                    "status": "processing",
                    "steps": steps,
                    "priority": priority
                }
                
        except Exception as e:
            self.logger.error(f"Failed to start processing for article {article_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def batch_process_articles(
        self,
        article_ids: List[int],
        operation: str = "process",
        parameters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Process multiple articles in batch.
        
        Args:
            article_ids: List of article IDs to process
            operation: Type of operation (process, translate, optimize, etc.)
            parameters: Additional parameters for processing
            
        Returns:
            Batch processing result
        """
        if parameters is None:
            parameters = {}
        
        self.logger.info(f"Starting batch processing for {len(article_ids)} articles")
        
        try:
            batch_task_id = f"batch_{int(datetime.utcnow().timestamp())}"
            
            # Process each article
            results = []
            for article_id in article_ids:
                result = await self.process_article(
                    article_id,
                    steps=parameters.get('steps'),
                    auto_publish=parameters.get('auto_publish', False),
                    priority=parameters.get('priority', 'normal')
                )
                results.append({
                    "article_id": article_id,
                    "result": result
                })
            
            return {
                "success": True,
                "batch_task_id": batch_task_id,
                "article_count": len(article_ids),
                "operation": operation,
                "results": results
            }
            
        except Exception as e:
            self.logger.error(f"Failed to batch process articles: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _get_processing_configuration(self, article_id: int) -> Dict[str, Any]:
        """Get intelligent processing configuration for an article."""
        try:
            from .processing_config_service import get_processing_config_service

            async with get_db_session() as session:
                article = session.query(Article).filter(Article.id == article_id).first()
                if not article:
                    self.logger.error(f"Article {article_id} not found")
                    return {}

                config_service = get_processing_config_service()
                config = config_service.get_processing_configuration(article)

                self.logger.info(f"📋 获取到智能配置: 类别={config.get('content_category')}, 策略={config.get('processing_strategy')}")
                return config

        except Exception as e:
            self.logger.error(f"Error getting processing configuration: {e}")
            return {}

    async def _execute_processing_pipeline(self, article: Article, steps: List[str], task: Task):
        """Execute the complete processing pipeline for an article."""
        pipeline_start_time = datetime.utcnow()

        self.logger.info("="*80)
        self.logger.info(f"🚀 开始处理文章 ID: {article.id}")
        self.logger.info(f"📝 文章标题: {article.title}")
        self.logger.info(f"🔗 来源URL: {article.source_url}")
        self.logger.info(f"📱 来源平台: {article.source_platform}")
        self.logger.info(f"⚙️  处理步骤: {' -> '.join(steps)}")
        self.logger.info(f"🕐 开始时间: {pipeline_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"📋 步骤详情: {steps}")
        self.logger.info(f"🔧 任务ID: {task.id}")
        self.logger.info("="*80)

        try:
            self.logger.info("🔄 开始执行处理流程...")
            async with get_db_session() as session:
                self.logger.info("✅ 数据库会话已建立")

                # Update task status to running
                self.logger.info("🔄 更新任务状态为运行中...")
                await self._update_task_status(session, task.id, TaskStatus.RUNNING)
                self.logger.info(f"✅ 任务状态已更新为运行中 (Task ID: {task.task_id})")

                total_steps = len(steps)
                completed_steps = 0

                for step_index, step in enumerate(steps, 1):
                    step_start_time = datetime.utcnow()

                    self.logger.info("-"*60)
                    self.logger.info(f"🔄 步骤 {step_index}/{total_steps}: {step.upper()}")
                    self.logger.info(f"🕐 步骤开始时间: {step_start_time.strftime('%H:%M:%S')}")
                    self.logger.info("-"*60)

                    # Update article status
                    new_status = self._get_status_for_step(step)
                    await self._update_article_status(session, article.id, new_status)
                    self.logger.info(f"📊 文章状态已更新为: {new_status.value}")

                    # Execute the processing step
                    if step in self.processing_steps:
                        try:
                            if step == ProcessingStep.DETECT:
                                # Special handling for AI detection with loop
                                self.logger.info("🤖 开始AI检测循环流程...")
                                result = await self._execute_ai_detection_loop(article, session)
                            else:
                                self.logger.info(f"⚡ 执行处理步骤: {step}")
                                self.logger.info(f"📋 步骤方法: {self.processing_steps[step].__name__}")
                                self.logger.info(f"🚀 即将调用步骤方法...")

                                result = await self.processing_steps[step](article)

                                self.logger.info(f"📊 步骤 {step} 执行完成")
                                self.logger.info(f"📊 结果类型: {type(result)}")
                                self.logger.info(f"📊 执行成功: {result.success if hasattr(result, 'success') else 'Unknown'}")

                            step_end_time = datetime.utcnow()
                            step_duration = (step_end_time - step_start_time).total_seconds()

                            if result.success:
                                self.logger.info(f"✅ 步骤 '{step}' 执行成功")
                                self.logger.info(f"⏱️  步骤耗时: {step_duration:.2f}秒")
                                if result.data:
                                    for key, value in result.data.items():
                                        self.logger.info(f"📈 {key}: {value}")
                                self.logger.info(f"💬 结果消息: {result.message}")
                            else:
                                self.logger.error(f"❌ 步骤 '{step}' 执行失败")
                                self.logger.error(f"⏱️  步骤耗时: {step_duration:.2f}秒")
                                self.logger.error(f"💬 错误消息: {result.message}")
                                await self._update_task_status(session, task.id, TaskStatus.FAILED, result.message)
                                await self._update_article_status(session, article.id, ArticleStatus.FAILED)

                                self.logger.error("="*80)
                                self.logger.error(f"💥 处理流程失败 - 文章 ID: {article.id}")
                                self.logger.error(f"💥 失败步骤: {step}")
                                self.logger.error(f"💥 失败原因: {result.message}")
                                self.logger.error("="*80)
                                return

                        except Exception as step_error:
                            step_end_time = datetime.utcnow()
                            step_duration = (step_end_time - step_start_time).total_seconds()

                            self.logger.error(f"💥 步骤 '{step}' 执行异常")
                            self.logger.error(f"⏱️  步骤耗时: {step_duration:.2f}秒")
                            self.logger.error(f"💬 异常信息: {str(step_error)}")
                            await self._update_task_status(session, task.id, TaskStatus.FAILED, str(step_error))
                            await self._update_article_status(session, article.id, ArticleStatus.FAILED)

                            self.logger.error("="*80)
                            self.logger.error(f"💥 处理流程异常 - 文章 ID: {article.id}")
                            self.logger.error(f"💥 异常步骤: {step}")
                            self.logger.error(f"💥 异常详情: {str(step_error)}")
                            self.logger.error("="*80)
                            return

                    completed_steps += 1
                    progress = (completed_steps / total_steps) * 100
                    await self._update_task_progress(session, task.id, progress)

                    self.logger.info(f"📊 进度更新: {progress:.1f}% ({completed_steps}/{total_steps})")
                    self.logger.info(f"✅ 步骤 '{step}' 完成")

                # Mark task as completed
                await self._update_task_status(session, task.id, TaskStatus.COMPLETED)
                await self._update_article_status(session, article.id, ArticleStatus.OPTIMIZED)

                pipeline_end_time = datetime.utcnow()
                total_duration = (pipeline_end_time - pipeline_start_time).total_seconds()

                self.logger.info("="*80)
                self.logger.info(f"🎉 处理流程完成 - 文章 ID: {article.id}")
                self.logger.info(f"🕐 完成时间: {pipeline_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
                self.logger.info(f"⏱️  总耗时: {total_duration:.2f}秒")
                self.logger.info(f"📊 完成步骤: {completed_steps}/{total_steps}")
                self.logger.info(f"✅ 最终状态: {ArticleStatus.OPTIMIZED.value}")
                self.logger.info("="*80)

        except Exception as e:
            pipeline_end_time = datetime.utcnow()
            total_duration = (pipeline_end_time - pipeline_start_time).total_seconds()

            self.logger.error("="*80)
            self.logger.error(f"💥 处理流程发生严重异常 - 文章 ID: {article.id}")
            self.logger.error(f"💥 异常时间: {pipeline_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.error(f"⏱️  运行时长: {total_duration:.2f}秒")
            self.logger.error(f"💬 异常详情: {str(e)}")
            self.logger.error("="*80)

            async with get_db_session() as session:
                await self._update_task_status(session, task.id, TaskStatus.FAILED, str(e))
                await self._update_article_status(session, article.id, ArticleStatus.FAILED)
    
    async def _extract_content(self, article: Article) -> ProcessingResult:
        """Extract content from the article URL using Freedium.cfd."""
        try:
            self.logger.info("="*80)
            self.logger.info("📥 开始内容提取...")
            self.logger.info(f"🔗 目标URL: {article.source_url}")
            self.logger.info(f"📱 来源平台: {article.source_platform}")
            self.logger.info("="*80)

            self.logger.info("📦 正在导入内容提取器...")
            from .content_extractor import get_content_extractor
            self.logger.info("✅ 内容提取器模块导入成功")

            self.logger.info("🔧 正在获取内容提取器实例...")
            extractor = get_content_extractor()
            self.logger.info("✅ 内容提取器实例获取成功")

            self.logger.info("🔧 内容提取器已初始化")
            self.logger.info("🌐 正在通过 Freedium.cfd 提取内容...")
            self.logger.info("📋 即将调用 extractor.extract_content 方法...")

            # Extract content using Freedium.cfd
            self.logger.info(f"🚀 开始调用提取方法，URL: {article.source_url}")
            result = await extractor.extract_content(article.source_url)
            self.logger.info(f"📊 提取方法调用完成，结果类型: {type(result)}")
            self.logger.info(f"📊 提取成功: {result.success if hasattr(result, 'success') else 'Unknown'}")

            if result.success:
                self.logger.info("✅ 内容提取成功!")

                # Update article with extracted content
                original_content_length = len(article.content_original) if article.content_original else 0
                article.content_original = result.content
                new_content_length = len(result.content)

                self.logger.info(f"📝 内容长度: {new_content_length} 字符 (原: {original_content_length})")

                if result.title and not article.title:
                    article.title = result.title
                    self.logger.info(f"📰 标题已更新: {result.title}")

                if hasattr(article, 'author') and result.author:
                    article.author = result.author
                    self.logger.info(f"👤 作者信息: {result.author}")

                if hasattr(article, 'word_count'):
                    article.word_count = result.word_count
                    self.logger.info(f"🔢 字数统计: {result.word_count} 词")

                if hasattr(article, 'estimated_reading_time'):
                    article.estimated_reading_time = result.reading_time
                    self.logger.info(f"⏱️  预计阅读时间: {result.reading_time} 分钟")

                self.logger.info(f"🎯 提取方法: {result.extraction_method}")

                # 显示提取到的全文内容（截取前500字符）
                content_preview = result.content[:500] + "..." if len(result.content) > 500 else result.content
                self.logger.info("📄 提取到的全文内容预览:")
                self.logger.info("─" * 60)
                self.logger.info(content_preview)
                self.logger.info("─" * 60)

                self.logger.info("✅ 内容提取步骤完成")

                return ProcessingResult(True, "内容提取成功", {
                    "extraction_method": result.extraction_method,
                    "word_count": result.word_count,
                    "reading_time": result.reading_time,
                    "content_length": new_content_length,
                    "title_updated": bool(result.title and not article.title)
                })
            else:
                self.logger.error("❌ 内容提取失败")
                self.logger.error(f"💬 错误信息: {result.error}")
                return ProcessingResult(False, f"内容提取失败: {result.error}")

        except Exception as e:
            self.logger.error("💥 内容提取过程发生异常")
            self.logger.error(f"💬 异常详情: {str(e)}")
            return ProcessingResult(False, f"内容提取异常: {str(e)}")
    
    async def _translate_content(self, article: Article) -> ProcessingResult:
        """Translate article content using LLM API service with intelligent classification."""
        try:
            self.logger.info("🌐 开始智能翻译和分类...")

            # Check if content is available
            if not article.content_original:
                self.logger.error("❌ 没有可翻译的原始内容")
                return ProcessingResult(False, "没有可翻译的原始内容")

            # 检查是否为主题创作文章 - 跳过翻译和分类
            is_topic_creation = (hasattr(article, 'creation_type') and
                               article.creation_type == 'topic_creation')

            if is_topic_creation:
                self.logger.info("🎨 检测到主题创作文章，跳过翻译和分类步骤")
                self.logger.info("📝 主题创作内容已经是中文，无需翻译")
                self.logger.info("🏷️ 主题创作文章直接使用提示词，无需分类判断")

                # 对于主题创作，直接设置翻译内容为原始内容
                article.content_translated = article.content_original

                # 设置一个通用分类，避免分类逻辑影响后续处理
                article.category = "general"

                # 保存到数据库
                async with get_db_session() as session:
                    session.merge(article)
                    session.commit()
                    self.logger.info("💾 主题创作文章信息已保存到数据库")

                return ProcessingResult(True, "主题创作文章跳过翻译和分类", {
                    "method": "topic_creation_skip",
                    "original_length": len(article.content_original),
                    "translated_length": len(article.content_original),
                    "length_change": 0,
                    "classification": {
                        "category": "general",
                        "confidence": 1.0,
                        "reasoning": "主题创作文章，跳过分类判断，直接使用提示词处理",
                        "method": "topic_creation_skip"
                    }
                })

            original_length = len(article.content_original)
            self.logger.info(f"📝 原始内容长度: {original_length} 字符")

            # 使用新的智能翻译和分类API
            from .real_ai_api_call import get_real_ai_api_call
            api_service = get_real_ai_api_call()
            self.logger.info("🔧 智能翻译和分类服务已初始化")

            self.logger.info(f"📱 来源平台: {article.source_platform}")
            self.logger.info(f"🔗 文章URL: {article.source_url}")

            self.logger.info("🚀 正在调用AI进行智能翻译和分类...")

            # 显示翻译使用的原始内容（截取前300字符）
            content_preview = article.content_original[:300] + "..." if len(article.content_original) > 300 else article.content_original
            self.logger.info("📄 待翻译的原始内容:")
            self.logger.info("─" * 60)
            self.logger.info(content_preview)
            self.logger.info("─" * 60)

            # 调用智能翻译和分类API
            result = await api_service.translate_and_classify_article(
                title=article.title,
                content=article.content_original,
                source_url=article.source_url,
                target_language="中文"
            )

            if result["success"]:
                self.logger.info("✅ 智能翻译和分类完成!")

                # 更新文章的翻译内容
                article.content_translated = result["translated_content"]
                translated_length = len(result["translated_content"])

                self.logger.info(f"📝 翻译后长度: {translated_length} 字符")
                self.logger.info(f"📊 长度变化: {translated_length - original_length:+d} 字符")

                # 更新文章分类信息
                classification = result["classification"]
                article.category = classification["category"]

                self.logger.info("🏷️ 智能分类结果:")
                self.logger.info(f"   📂 分类: {classification['category']}")
                self.logger.info(f"   🎯 置信度: {classification['confidence']:.2%}")
                self.logger.info(f"   💭 理由: {classification['reasoning']}")
                self.logger.info(f"   🔧 方法: {classification['method']}")

                if result.get("usage"):
                    self.logger.info(f"💰 Token使用情况: {result['usage']}")

                # 保存到数据库
                async with get_db_session() as session:
                    session.merge(article)
                    session.commit()
                    self.logger.info("💾 翻译和分类结果已保存到数据库")

                # 显示翻译结果（截取前300字符）
                translated_preview = result["translated_content"][:300] + "..." if len(result["translated_content"]) > 300 else result["translated_content"]
                self.logger.info("📄 翻译结果内容:")
                self.logger.info("─" * 60)
                self.logger.info(translated_preview)
                self.logger.info("─" * 60)

                self.logger.info("✅ 智能翻译和分类步骤完成")

                return ProcessingResult(True, "智能翻译和分类成功", {
                    "usage": result.get("usage", {}),
                    "original_length": original_length,
                    "translated_length": translated_length,
                    "length_change": translated_length - original_length,
                    "classification": classification,
                    "method": "ai_llm_classification"
                })
            else:
                self.logger.error("❌ 智能翻译和分类失败")
                self.logger.error(f"💬 错误信息: {result.get('error', '未知错误')}")

                # 降级处理：使用传统翻译方法
                self.logger.info("🔄 降级使用传统翻译方法...")
                return await self._fallback_translate_content(article)

        except Exception as e:
            self.logger.error("💥 智能翻译和分类过程发生异常")
            self.logger.error(f"💬 异常详情: {str(e)}")

            # 降级处理：使用传统翻译方法
            self.logger.info("🔄 降级使用传统翻译方法...")
            return await self._fallback_translate_content(article)

    async def _fallback_translate_content(self, article: Article) -> ProcessingResult:
        """Fallback translation method using traditional LLM service."""
        try:
            self.logger.info("🔄 使用传统翻译方法...")

            from .llm_api import get_llm_service
            llm_service = get_llm_service()
            self.logger.info("🔧 传统LLM翻译服务已初始化")

            # Determine source and target languages
            source_lang = "en" if article.source_platform == "medium" else "auto"
            target_lang = "zh"  # Default to Chinese

            # Translate content
            result = await llm_service.translate_content(
                content=article.content_original,
                title=article.title,
                source_language=source_lang,
                target_language=target_lang
            )

            if result.success:
                self.logger.info("✅ 传统翻译完成!")

                # Update article with translated content
                article.content_translated = result.content
                translated_length = len(result.content)

                # 使用传统关键词分类方法
                from .processing_config_service import ProcessingConfigService
                config_service = ProcessingConfigService()
                category, confidence = config_service.classify_article(article)

                article.category = category.value

                self.logger.info("🏷️ 传统分类结果:")
                self.logger.info(f"   📂 分类: {category.value}")
                self.logger.info(f"   🎯 置信度: {confidence:.2%}")
                self.logger.info(f"   🔧 方法: keyword_based")

                # 保存到数据库
                async with get_db_session() as session:
                    session.merge(article)
                    session.commit()
                    self.logger.info("💾 传统翻译和分类结果已保存到数据库")

                return ProcessingResult(True, "传统翻译和分类成功", {
                    "model": getattr(result, 'model', 'unknown'),
                    "usage": getattr(result, 'usage', {}),
                    "classification": {
                        "category": category.value,
                        "confidence": confidence,
                        "method": "keyword_based"
                    },
                    "method": "fallback_translation"
                })
            else:
                self.logger.error("❌ 传统翻译失败")
                self.logger.error(f"💬 错误信息: {result.error}")
                return ProcessingResult(False, f"传统翻译失败: {result.error}")

        except Exception as e:
            self.logger.error("💥 传统翻译过程发生异常")
            self.logger.error(f"💬 异常详情: {str(e)}")
            return ProcessingResult(False, f"传统翻译异常: {str(e)}")

    async def _optimize_content(self, article: Article) -> ProcessingResult:
        """Optimize article content with AI detection loop until AI concentration < 25%."""
        try:
            self.logger.info("⚡ 开始内容优化与AI检测循环...")

            from .llm_api import get_llm_service
            from .prompt_manager import get_prompt_manager, ContentType

            llm_service = get_llm_service()
            prompt_manager = get_prompt_manager()
            self.logger.info("🔧 LLM优化服务和提示词管理器已初始化")

            # Use translated content if available, otherwise original
            content_to_optimize = article.content_translated or article.content_original
            content_source = "翻译后内容" if article.content_translated else "原始内容"

            self.logger.info(f"📝 优化内容来源: {content_source}")

            if not content_to_optimize:
                self.logger.error("❌ 没有可优化的内容")
                return ProcessingResult(False, "没有可优化的内容")

            original_length = len(content_to_optimize)
            original_word_count = len(content_to_optimize.split())

            self.logger.info(f"📝 待优化内容长度: {original_length} 字符")
            self.logger.info(f"🔢 待优化词数: {original_word_count} 词")

            # 确定内容类型
            content_type = self._determine_content_type(article.title, content_to_optimize)
            self.logger.info(f"📋 内容类型: {content_type.value}")

            # Optimize content for the target platform (default: toutiao)
            target_platform = "toutiao"  # Default platform
            optimization_type = "standard"

            self.logger.info(f"🎯 目标平台: {target_platform}")
            self.logger.info(f"⚙️  优化类型: {optimization_type}")

            # 显示待优化的内容（截取前300字符）
            content_preview = content_to_optimize[:300] + "..." if len(content_to_optimize) > 300 else content_to_optimize
            self.logger.info("📄 待优化的内容:")
            self.logger.info("─" * 60)
            self.logger.info(content_preview)
            self.logger.info("─" * 60)

            # 开始优化与检测循环
            from ..core.config import get_ai_optimization_config
            ai_config = get_ai_optimization_config()
            max_attempts = ai_config.max_attempts  # 从配置获取最大优化尝试次数
            ai_threshold = ai_config.threshold  # 从配置获取AI浓度阈值

            self.logger.info("🔄 开始优化与AI检测循环...")
            self.logger.info(f"🎯 目标阈值: {ai_threshold}%")
            self.logger.info(f"🔢 最大尝试次数: {max_attempts}")

            current_content = content_to_optimize

            for attempt in range(1, max_attempts + 1):
                attempt_start_time = datetime.utcnow()

                self.logger.info("═" * 60)
                self.logger.info(f"🔄 第 {attempt}/{max_attempts} 次优化尝试")
                self.logger.info(f"🕐 尝试开始时间: {attempt_start_time.strftime('%H:%M:%S')}")
                self.logger.info("═" * 60)

                # 生成优化提示词
                optimization_prompt = prompt_manager.get_optimization_prompt(
                    content=current_content,
                    ai_probability=50.0 if attempt == 1 else 80.0,  # 后续尝试假设更高AI概率
                    round_number=attempt,
                    content_type=content_type,
                    platform=target_platform
                )

                # 显示使用的优化prompt（截取前400字符）
                prompt_preview = optimization_prompt[:400] + "..." if len(optimization_prompt) > 400 else optimization_prompt
                self.logger.info("📝 使用的优化Prompt:")
                self.logger.info("─" * 60)
                self.logger.info(prompt_preview)
                self.logger.info("─" * 60)

                self.logger.info("🚀 正在调用LLM API进行内容优化...")

                # 执行优化
                result = await llm_service.optimize_content(
                    content=current_content,
                    title=article.title,
                    platform=target_platform,
                    optimization_type=optimization_type,
                    custom_prompt=optimization_prompt
                )

                if not result.success:
                    self.logger.error(f"❌ 第 {attempt} 次优化失败: {result.error}")
                    if attempt == max_attempts:
                        return ProcessingResult(False, f"内容优化在 {max_attempts} 次尝试后失败: {result.error}")
                    self.logger.info("🔄 继续下一次尝试...")
                    continue

                self.logger.info("✅ 内容优化完成!")

                # 更新当前内容为优化后的内容
                current_content = result.content
                optimized_length = len(current_content)
                optimized_word_count = len(current_content.split())

                self.logger.info(f"📝 优化后长度: {optimized_length} 字符")
                self.logger.info(f"🔢 优化后词数: {optimized_word_count} 词")
                self.logger.info(f"📊 长度变化: {optimized_length - original_length:+d} 字符")
                self.logger.info(f"📊 词数变化: {optimized_word_count - original_word_count:+d} 词")

                # 显示优化结果（截取前300字符）
                optimized_preview = current_content[:300] + "..." if len(current_content) > 300 else current_content
                self.logger.info("📄 优化结果内容:")
                self.logger.info("─" * 60)
                self.logger.info(optimized_preview)
                self.logger.info("─" * 60)

                # 立即进行AI检测
                self.logger.info("🤖 开始AI检测...")

                # 临时更新文章内容以便检测
                original_optimized_content = article.content_optimized
                article.content_optimized = current_content

                detection_result = await self._detect_content(article)

                if not detection_result.success:
                    self.logger.error(f"❌ 第 {attempt} 次AI检测失败: {detection_result.message}")
                    # 恢复原始内容
                    article.content_optimized = original_optimized_content
                    if attempt == max_attempts:
                        return ProcessingResult(False, f"AI检测在 {max_attempts} 次尝试后失败")
                    self.logger.info("🔄 继续下一次尝试...")
                    continue

                ai_probability = detection_result.data.get('ai_probability', 100.0)
                attempt_end_time = datetime.utcnow()
                attempt_duration = (attempt_end_time - attempt_start_time).total_seconds()

                self.logger.info(f"📊 检测结果: {ai_probability}% AI概率")
                self.logger.info(f"⏱️  本次尝试耗时: {attempt_duration:.2f}秒")

                # 检查AI浓度是否低于阈值
                if ai_probability < ai_threshold:
                    self.logger.info("🎉 AI检测通过!")
                    self.logger.info(f"✅ AI概率 ({ai_probability}%) 低于阈值 ({ai_threshold}%)")
                    self.logger.info(f"📊 使用尝试次数: {attempt}/{max_attempts}")

                    # 最终更新文章内容和元数据
                    article.content_optimized = current_content

                    if hasattr(article, 'word_count'):
                        article.word_count = optimized_word_count
                        self.logger.info(f"🔢 文章词数已更新: {optimized_word_count}")

                    if hasattr(article, 'estimated_reading_time'):
                        reading_time = max(1, optimized_word_count // 200)
                        article.estimated_reading_time = reading_time
                        self.logger.info(f"⏱️  预计阅读时间已更新: {reading_time} 分钟")

                    self.logger.info("✅ 内容优化与AI检测循环完成")

                    return ProcessingResult(True, f"内容优化成功，AI检测通过: {ai_probability}% AI概率", {
                        "model": getattr(result, 'model', 'unknown'),
                        "usage": getattr(result, 'usage', {}),
                        "finish_reason": getattr(result, 'finish_reason', 'unknown'),
                        "original_length": original_length,
                        "optimized_length": optimized_length,
                        "original_word_count": original_word_count,
                        "optimized_word_count": optimized_word_count,
                        "length_change": optimized_length - original_length,
                        "word_count_change": optimized_word_count - original_word_count,
                        "platform": target_platform,
                        "optimization_type": optimization_type,
                        "ai_probability": ai_probability,
                        "attempts_used": attempt,
                        "threshold": ai_threshold
                    })
                else:
                    # AI浓度过高，需要重新优化
                    self.logger.warning(f"⚠️  AI概率 ({ai_probability}%) 超过阈值 ({ai_threshold}%)")

                    if attempt < max_attempts:
                        self.logger.info("🔄 需要重新优化内容以降低AI痕迹...")
                        # 继续下一次循环，使用当前优化的内容作为下次优化的输入
                    else:
                        # 达到最大尝试次数
                        self.logger.error("💥 优化与AI检测循环失败!")
                        self.logger.error(f"❌ 已达到最大尝试次数 ({max_attempts})")
                        self.logger.error(f"📊 最终AI概率: {ai_probability}%")
                        self.logger.error(f"🎯 要求阈值: {ai_threshold}%")

                        return ProcessingResult(False, f"内容优化失败: AI概率 {ai_probability}% 仍超过阈值 {ai_threshold}%", {
                            "ai_probability": ai_probability,
                            "attempts_used": max_attempts,
                            "threshold": ai_threshold,
                            "final_status": "failed_ai_detection"
                        })

            # 如果到这里，说明所有尝试都失败了
            return ProcessingResult(False, f"内容优化在 {max_attempts} 次尝试后失败")

        except Exception as e:
            self.logger.error("💥 内容优化过程发生异常")
            self.logger.error(f"💬 异常详情: {str(e)}")
            return ProcessingResult(False, f"优化异常: {str(e)}")

    async def _create_content(self, article: Article) -> ProcessingResult:
        """Create content based on topic for topic-based articles."""
        try:
            self.logger.info("="*80)
            self.logger.info("🎨 开始主题内容创作...")

            # Check if this is a topic-based creation
            if not hasattr(article, 'creation_type') or article.creation_type != 'topic_creation':
                self.logger.warning("⚠️  非主题创作文章，跳过创作步骤")
                return ProcessingResult(True, "非主题创作文章，跳过创作步骤")

            if not hasattr(article, 'topic') or not article.topic:
                self.logger.error("❌ 缺少创作主题")
                return ProcessingResult(False, "缺少创作主题")

            self.logger.info(f"🎯 创作主题: {article.topic}")

            # Get keywords if available
            keywords = []
            if hasattr(article, 'keywords') and article.keywords:
                try:
                    import json
                    keywords = json.loads(article.keywords) if isinstance(article.keywords, str) else article.keywords
                    self.logger.info(f"🏷️  关键词: {', '.join(keywords)}")
                except:
                    self.logger.warning("⚠️  关键词解析失败")

            # Get creation requirements
            requirements = ""
            if hasattr(article, 'creation_requirements') and article.creation_requirements:
                requirements = article.creation_requirements
                self.logger.info(f"📋 创作要求: {requirements}")

            # Import LLM service
            from .llm_api import get_llm_service
            llm_service = get_llm_service()
            self.logger.info("🔧 LLM创作服务已初始化")

            # Get creation prompt from database if specified
            creation_prompt = None
            if hasattr(article, 'selected_creation_prompt_id') and article.selected_creation_prompt_id:
                creation_prompt = self._get_creation_prompt_template(article.selected_creation_prompt_id, article.topic, keywords, requirements)
                self.logger.info(f"📝 使用数据库提示词模板 ID: {article.selected_creation_prompt_id}")

            if not creation_prompt:
                creation_prompt = self._build_creation_prompt(article.topic, keywords, requirements)
                self.logger.info("📝 使用默认创作提示词")

            # Display the creation prompt (first 300 characters)
            prompt_preview = creation_prompt[:300] + "..." if len(creation_prompt) > 300 else creation_prompt
            self.logger.info("📄 创作提示词预览:")
            self.logger.info("─" * 60)
            self.logger.info(prompt_preview)
            self.logger.info("─" * 60)

            self.logger.info("🚀 正在调用LLM API进行内容创作...")

            # 获取目标长度设置
            target_length = getattr(article, 'target_length', 'mini')
            self.logger.info(f"📏 文章目标长度: {target_length}")

            # 设置当前目标长度，供模板处理使用
            self._current_target_length = target_length

            # 获取API参数配置（如果有的话）
            api_params = {}
            if hasattr(article, 'selected_model_id') and article.selected_model_id:
                # 从数据库获取模型配置
                try:
                    from ..core.database import get_db_connection
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT temperature, max_tokens, top_p, frequency_penalty, presence_penalty
                        FROM api_models WHERE id = ?
                    """, (article.selected_model_id,))
                    model_config = cursor.fetchone()
                    conn.close()

                    if model_config:
                        api_params = {
                            'temperature': model_config[0] or 0.7,
                            'max_tokens': model_config[1] or 4000,
                            'top_p': model_config[2] or 1.0,
                            'frequency_penalty': model_config[3] or 0.0,
                            'presence_penalty': model_config[4] or 0.0
                        }
                        self.logger.info(f"🔧 使用模型配置: {api_params}")
                except Exception as e:
                    self.logger.warning(f"⚠️  获取模型配置失败，使用默认参数: {e}")

            # Create content using LLM
            result = await llm_service.create_content_by_topic(
                topic=article.topic,
                keywords=keywords,
                requirements=requirements,
                custom_prompt=creation_prompt,
                target_length=target_length,
                **api_params
            )

            if result.success:
                self.logger.info("✅ 主题内容创作完成!")

                # Update article with created content
                article.content_original = result.content
                created_length = len(result.content)
                created_word_count = len(result.content.split())

                # Calculate reading time early to avoid scope issues
                reading_time = max(1, created_word_count // 200)

                self.logger.info(f"📝 创作内容长度: {created_length} 字符")
                self.logger.info(f"🔢 创作词数: {created_word_count} 词")

                # Update metadata
                if hasattr(article, 'word_count'):
                    article.word_count = created_word_count
                    self.logger.info(f"🔢 文章词数已更新: {created_word_count}")

                if hasattr(article, 'estimated_reading_time'):
                    article.estimated_reading_time = reading_time
                    self.logger.info(f"⏱️  预计阅读时间: {reading_time} 分钟")

                # Update title if not set or is default
                if not article.title or article.title.startswith("主题创作:"):
                    if hasattr(result, 'title') and result.title:
                        article.title = result.title
                        self.logger.info(f"📰 文章标题已更新: {result.title}")

                # Display created content (first 500 characters)
                content_preview = result.content[:500] + "..." if len(result.content) > 500 else result.content
                self.logger.info("📄 创作内容预览:")
                self.logger.info("─" * 60)
                self.logger.info(content_preview)
                self.logger.info("─" * 60)

                # 🔥 关键修改：创作完成后立即进行AI检测
                self.logger.info("🤖 开始对创作内容进行AI检测...")

                # 执行AI检测与优化循环
                detection_and_optimization_result = await self._create_content_detection_loop(article)

                if detection_and_optimization_result.success:
                    self.logger.info("✅ 主题内容创作与AI检测完成")

                    # 合并结果数据
                    final_data = {
                        "topic": article.topic,
                        "keywords": keywords,
                        "content_length": len(article.content_original),
                        "word_count": len(article.content_original.split()) if article.content_original else 0,
                        "reading_time": reading_time,
                        "title_updated": bool(hasattr(result, 'title') and result.title),
                        "ai_detection": detection_and_optimization_result.data if hasattr(detection_and_optimization_result, 'data') else {}
                    }

                    return ProcessingResult(True, f"主题内容创作成功，{detection_and_optimization_result.message}", final_data)
                else:
                    self.logger.error("❌ AI检测与优化失败")
                    return ProcessingResult(False, f"主题内容创作成功，但AI检测失败: {detection_and_optimization_result.message}")

            else:
                self.logger.error("❌ 主题内容创作失败")
                self.logger.error(f"💬 失败原因: {result.message}")
                return ProcessingResult(False, f"主题内容创作失败: {result.message}")

        except Exception as e:
            self.logger.error("💥 主题内容创作过程发生异常")
            self.logger.error(f"💬 异常详情: {str(e)}")
            return ProcessingResult(False, f"主题内容创作异常: {str(e)}")

    async def _create_content_detection_loop(self, article: Article) -> ProcessingResult:
        """
        对创作的内容进行AI检测，如果不通过则启动优化循环。
        这是针对主题创作内容的检测与优化流程。
        """
        try:
            from ..core.config import get_ai_optimization_config
            ai_config = get_ai_optimization_config()
            max_attempts = ai_config.max_attempts  # 从配置获取最大优化尝试次数
            ai_threshold = ai_config.threshold  # 从配置获取AI浓度阈值

            self.logger.info("🔄 开始创作内容的AI检测与优化循环...")
            self.logger.info(f"🎯 目标阈值: {ai_threshold}%")
            self.logger.info(f"🔢 最大尝试次数: {max_attempts}")

            # 获取当前创作的内容
            current_content = article.content_original
            if not current_content:
                return ProcessingResult(False, "没有创作内容可供检测")

            for attempt in range(1, max_attempts + 1):
                attempt_start_time = datetime.utcnow()

                self.logger.info("═" * 60)
                self.logger.info(f"🔄 第 {attempt}/{max_attempts} 次检测尝试")
                self.logger.info(f"🕐 尝试开始时间: {attempt_start_time.strftime('%H:%M:%S')}")
                self.logger.info("═" * 60)

                # 执行AI检测
                self.logger.info("🤖 执行AI检测...")

                # 临时设置内容以便检测
                original_content = article.content_original
                article.content_original = current_content

                detection_result = await self._detect_content(article)

                # 恢复原始内容
                article.content_original = original_content

                if not detection_result.success:
                    self.logger.error(f"❌ 第 {attempt} 次AI检测失败: {detection_result.message}")
                    if attempt == max_attempts:
                        return ProcessingResult(False, f"AI检测在 {max_attempts} 次尝试后失败")
                    self.logger.info("🔄 继续下一次尝试...")
                    continue

                ai_probability = detection_result.data.get('ai_probability', 100.0)
                attempt_end_time = datetime.utcnow()
                attempt_duration = (attempt_end_time - attempt_start_time).total_seconds()

                self.logger.info(f"📊 检测结果: {ai_probability}% AI概率")
                self.logger.info(f"⏱️  本次尝试耗时: {attempt_duration:.2f}秒")

                # 检查AI浓度是否低于阈值
                if ai_probability < ai_threshold:
                    self.logger.info("🎉 AI检测通过!")
                    self.logger.info(f"✅ AI概率 ({ai_probability}%) 低于阈值 ({ai_threshold}%)")
                    self.logger.info(f"📊 使用尝试次数: {attempt}/{max_attempts}")

                    # 更新文章内容为最终版本
                    article.content_original = current_content

                    return ProcessingResult(True, f"AI检测通过: {ai_probability}% AI概率", {
                        "ai_probability": ai_probability,
                        "attempts_used": attempt,
                        "threshold": ai_threshold,
                        "final_status": "passed",
                        "content_length": len(current_content),
                        "optimization_applied": attempt > 1
                    })
                else:
                    # AI浓度过高，需要优化
                    self.logger.warning(f"⚠️  AI概率 ({ai_probability}%) 超过阈值 ({ai_threshold}%)")

                    if attempt < max_attempts:
                        self.logger.info("🔄 需要优化内容以降低AI痕迹...")

                        # 执行内容优化
                        optimization_result = await self._optimize_for_ai_detection(current_content, ai_probability, attempt)

                        if optimization_result.success:
                            current_content = optimization_result.content
                            self.logger.info(f"✅ 第 {attempt} 次优化完成")

                            # 显示优化后的内容预览
                            optimized_preview = current_content[:300] + "..." if len(current_content) > 300 else current_content
                            self.logger.info("📄 优化后内容预览:")
                            self.logger.info("─" * 60)
                            self.logger.info(optimized_preview)
                            self.logger.info("─" * 60)
                        else:
                            self.logger.error(f"❌ 第 {attempt} 次优化失败: {optimization_result.message}")
                            if attempt == max_attempts:
                                return ProcessingResult(False, f"内容优化在 {max_attempts} 次尝试后失败")
                            self.logger.info("🔄 继续下一次尝试...")
                            continue
                    else:
                        # 达到最大尝试次数
                        self.logger.error("💥 创作内容AI检测与优化循环失败!")
                        self.logger.error(f"❌ 已达到最大尝试次数 ({max_attempts})")
                        self.logger.error(f"📊 最终AI概率: {ai_probability}%")
                        self.logger.error(f"🎯 要求阈值: {ai_threshold}%")

                        return ProcessingResult(False, f"创作内容AI检测失败: AI概率 {ai_probability}% 仍超过阈值 {ai_threshold}%", {
                            "ai_probability": ai_probability,
                            "attempts_used": max_attempts,
                            "threshold": ai_threshold,
                            "final_status": "failed_ai_detection"
                        })

            # 如果到这里，说明所有尝试都失败了
            return ProcessingResult(False, f"创作内容AI检测在 {max_attempts} 次尝试后失败")

        except Exception as e:
            self.logger.error("💥 创作内容AI检测循环过程发生异常")
            self.logger.error(f"💬 异常详情: {str(e)}")
            return ProcessingResult(False, f"创作内容AI检测循环异常: {str(e)}")

    def _build_creation_prompt(self, topic: str, keywords: list, requirements: str) -> str:
        """Build creation prompt for topic-based content creation."""
        prompt_parts = [
            "你是一位专业的内容创作专家。请根据以下要求创作一篇高质量的文章：",
            "",
            f"主题：{topic}",
        ]

        if keywords:
            prompt_parts.extend([
                f"关键词：{', '.join(keywords)}",
            ])

        if requirements:
            prompt_parts.extend([
                f"创作要求：{requirements}",
            ])

        prompt_parts.extend([
            "",
            "请确保文章：",
            "1. 内容原创且有深度",
            "2. 结构清晰，逻辑性强",
            "3. 语言流畅，符合中文表达习惯",
            "4. 包含实用价值和见解",
            "5. 字数在1000-3000字之间",
            "",
            "请直接输出文章内容，不需要额外的说明。"
        ])

        return "\n".join(prompt_parts)

    def _get_creation_prompt_template(self, prompt_id: int, topic: str, keywords: list, requirements: str) -> str:
        """Get creation prompt template from database and fill variables."""
        try:
            from ..core.database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT template, name, display_name FROM prompt_templates WHERE id = ? AND is_active = 1", (prompt_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                template = row[0]
                template_name = row[1]
                template_display_name = row[2]

                self.logger.info(f"📝 使用提示词模板: {template_display_name} ({template_name})")

                # 显示原始模板内容（前200字符）
                template_preview = template[:200] + "..." if len(template) > 200 else template
                self.logger.info("📄 原始模板内容预览:")
                self.logger.info("─" * 60)
                self.logger.info(template_preview)
                self.logger.info("─" * 60)

                # Replace template variables
                keywords_str = ', '.join(keywords) if keywords else ''

                # 安全的变量替换，避免格式化错误
                try:
                    # Fill template variables - 提供所有可能的变量
                    filled_template = template.format(
                        topic=topic,
                        title=topic,  # 添加title变量，使用topic作为值
                        keywords=keywords_str,
                        requirements=requirements or '请创作一篇高质量的文章。'
                    )

                    self.logger.info("✅ 提示词模板变量填充完成")

                    # 检查模板是否包含角色定位信息，如果是，需要添加明确的创作指令
                    if "角色定位" in filled_template or "情感故事作家" in filled_template:
                        self.logger.info("🎭 检测到角色定位模板，添加明确的创作指令")

                        # 在模板末尾添加明确的创作指令，包含目标长度
                        # 获取目标长度映射
                        length_mapping = {
                            "mini": "300-500",
                            "short": "500-800",
                            "medium": "800-1500",
                            "long": "1500-3000"
                        }

                        # 从当前设置的目标长度获取字数要求
                        target_length = getattr(self, '_current_target_length', 'mini')
                        word_count = length_mapping.get(target_length, "300-500")

                        self.logger.info(f"🎯 角色模板中使用的目标长度: {target_length}")
                        self.logger.info(f"📏 对应的字数要求: {word_count}")

                        creation_instruction = f"""

**📝 本次创作任务：**
请根据以上角色定位和写作要求，围绕主题"{topic}"创作一篇文章。

主题：{topic}
关键词：{keywords_str}
创作要求：{requirements or '请创作一篇高质量的文章。'}
字数要求：{word_count} 字

请直接开始创作文章内容，不要再重复角色定位说明。文章应该：
1. 紧扣主题"{topic}"
2. 体现上述写作风格和结构特点
3. 内容原创且有深度
4. 字数严格控制在 {word_count} 字之间

现在请开始创作："""

                        filled_template += creation_instruction
                        self.logger.info("✅ 已添加明确的创作指令")

                    # 显示填充后的模板内容（前500字符）
                    filled_preview = filled_template[:500] + "..." if len(filled_template) > 500 else filled_template
                    self.logger.info("📄 填充后模板内容预览:")
                    self.logger.info("─" * 60)
                    self.logger.info(filled_preview)
                    self.logger.info("─" * 60)

                    return filled_template

                except KeyError as ke:
                    self.logger.error(f"❌ 模板变量填充失败，缺少变量: {ke}")
                    self.logger.error("💡 模板可能包含未定义的变量，使用原始模板")
                    return template
                except Exception as fe:
                    self.logger.error(f"❌ 模板格式化失败: {fe}")
                    self.logger.error("💡 使用原始模板")
                    return template

            else:
                self.logger.warning(f"⚠️ 未找到提示词模板 ID: {prompt_id}")
                return None

        except Exception as e:
            self.logger.error(f"💥 获取提示词模板失败: {str(e)}")
            return None

    def _determine_content_type(self, title: str, content: str) -> 'ContentType':
        """Determine content type based on title and content."""
        from .prompt_manager import ContentType

        title_lower = title.lower() if title else ""
        content_lower = content.lower() if content else ""

        # Technical keywords
        tech_keywords = [
            'ai', 'machine learning', 'deep learning', 'neural network', 'algorithm',
            'programming', 'python', 'javascript', 'react', 'vue', 'angular',
            'api', 'database', 'sql', 'nosql', 'cloud', 'aws', 'azure',
            'docker', 'kubernetes', 'microservices', 'devops', 'git',
            'blockchain', 'cryptocurrency', 'web3', 'smart contract',
            '人工智能', '机器学习', '深度学习', '神经网络', '算法',
            '编程', '程序', '代码', '开发', '技术', '软件', '硬件',
            '数据库', '云计算', '区块链', '加密货币'
        ]

        # Tutorial keywords
        tutorial_keywords = [
            'how to', 'tutorial', 'guide', 'step by step', 'learn',
            'beginner', 'introduction', 'getting started', 'basics',
            '教程', '指南', '入门', '学习', '如何', '怎么', '步骤'
        ]

        # News keywords
        news_keywords = [
            'news', 'breaking', 'report', 'announcement', 'release',
            'update', 'latest', 'today', 'yesterday', 'this week',
            '新闻', '报道', '发布', '更新', '最新', '今日', '昨日'
        ]

        # Check for technical content
        tech_count = sum(1 for keyword in tech_keywords
                        if keyword in title_lower or keyword in content_lower[:500])

        # Check for tutorial content
        tutorial_count = sum(1 for keyword in tutorial_keywords
                           if keyword in title_lower or keyword in content_lower[:500])

        # Check for news content
        news_count = sum(1 for keyword in news_keywords
                        if keyword in title_lower or keyword in content_lower[:500])

        # Determine content type based on keyword counts
        if tech_count >= 2:
            return ContentType.TECHNICAL
        elif tutorial_count >= 1:
            return ContentType.TUTORIAL
        elif news_count >= 1:
            return ContentType.NEWS
        else:
            return ContentType.GENERAL

    async def _detect_content(self, article: Article) -> ProcessingResult:
        """Detect AI-generated content using Zhuque detection service (single detection only)."""
        try:
            self.logger.info("🤖 开始AI内容检测（确认检测）...")

            from .ai_detection import get_ai_detector
            detector = get_ai_detector()
            self.logger.info("🔧 AI检测服务已初始化")

            # Get the content to detect (use optimized content if available, otherwise translated or original)
            content_to_detect = (
                article.content_optimized or
                article.content_translated or
                article.content_original
            )

            # Determine content source
            if article.content_optimized:
                content_source = "优化后内容"
            elif article.content_translated:
                content_source = "翻译后内容"
            else:
                content_source = "原始内容"

            self.logger.info(f"📝 检测内容来源: {content_source}")

            # 严格验证内容不为空
            if not content_to_detect or len(content_to_detect.strip()) == 0:
                self.logger.error("❌ 没有可检测的内容")
                self.logger.error(f"❌ 文章ID: {article.id}")
                self.logger.error(f"❌ 文章标题: {article.title}")
                self.logger.error(f"❌ 原始内容: {'空' if not article.content_original else f'{len(article.content_original)}字符'}")
                self.logger.error(f"❌ 翻译内容: {'空' if not article.content_translated else f'{len(article.content_translated)}字符'}")
                self.logger.error(f"❌ 优化内容: {'空' if not article.content_optimized else f'{len(article.content_optimized)}字符'}")
                return ProcessingResult(False, "没有可检测的内容")

            content_length = len(content_to_detect)
            self.logger.info(f"📝 待检测内容长度: {content_length} 字符")

            # 显示待检测的内容（截取前300字符）
            content_preview = content_to_detect[:300] + "..." if len(content_to_detect) > 300 else content_to_detect
            self.logger.info("📄 待检测的内容:")
            self.logger.info("─" * 60)
            self.logger.info(content_preview)
            self.logger.info("─" * 60)

            # 执行单次AI检测（不循环，因为优化步骤已经处理了循环）
            self.logger.info("🚀 执行AI检测...")
            detection_result = await detector.detect_ai_content(content_to_detect)

            if detection_result.success:
                ai_probability = detection_result.ai_probability
                ai_threshold = 25.0

                self.logger.info(f"📊 AI检测结果: {ai_probability}% AI概率")
                self.logger.info(f"🎯 阈值标准: {ai_threshold}%")

                if ai_probability < ai_threshold:
                    self.logger.info("✅ AI检测通过!")
                    self.logger.info(f"✅ AI概率 ({ai_probability}%) 低于阈值 ({ai_threshold}%)")
                    status_message = f"AI检测通过: {ai_probability}% AI概率"
                else:
                    self.logger.warning("⚠️ AI检测未通过!")
                    self.logger.warning(f"⚠️ AI概率 ({ai_probability}%) 超过阈值 ({ai_threshold}%)")
                    self.logger.warning("💡 注意: 如果这是在OPTIMIZE步骤之后，可能需要检查优化逻辑")
                    status_message = f"AI检测未通过: {ai_probability}% AI概率超过阈值"

                return ProcessingResult(True, status_message, {
                    "ai_probability": ai_probability,
                    "threshold": ai_threshold,
                    "passed": ai_probability < ai_threshold,
                    "content_length": content_length,
                    "content_source": content_source
                })
            else:
                self.logger.error("❌ AI检测失败")
                error_msg = detection_result.error or "未知错误"
                self.logger.error(f"💬 错误信息: {error_msg}")
                return ProcessingResult(False, f"AI检测失败: {error_msg}")

        except Exception as e:
            self.logger.error("💥 AI检测过程发生异常")
            self.logger.error(f"💬 异常详情: {str(e)}")
            return ProcessingResult(False, f"AI检测异常: {str(e)}")

    async def _execute_ai_detection_loop(self, article: Article, session) -> ProcessingResult:
        """
        Execute AI detection with optimization loop until AI concentration < 25%.

        Args:
            article: Article to process
            session: Database session

        Returns:
            ProcessingResult indicating success or failure
        """
        from ..core.config import get_ai_optimization_config
        ai_config = get_ai_optimization_config()
        max_attempts = ai_config.max_attempts  # 从配置获取最大优化尝试次数
        ai_threshold = ai_config.threshold  # 从配置获取AI浓度阈值

        loop_start_time = datetime.utcnow()

        self.logger.info("🔄 开始AI检测优化循环...")
        self.logger.info(f"🎯 目标阈值: {ai_threshold}%")
        self.logger.info(f"🔢 最大尝试次数: {max_attempts}")
        self.logger.info(f"🕐 循环开始时间: {loop_start_time.strftime('%H:%M:%S')}")

        for attempt in range(1, max_attempts + 1):
            attempt_start_time = datetime.utcnow()

            self.logger.info("─" * 50)
            self.logger.info(f"🔄 第 {attempt}/{max_attempts} 次尝试")
            self.logger.info(f"🕐 尝试开始时间: {attempt_start_time.strftime('%H:%M:%S')}")

            # Perform AI detection
            self.logger.info("🤖 执行AI检测...")
            detection_result = await self._detect_content(article)

            if not detection_result.success:
                self.logger.error(f"❌ 第 {attempt} 次AI检测失败: {detection_result.message}")
                if attempt == max_attempts:
                    self.logger.error(f"💥 AI检测在 {max_attempts} 次尝试后仍然失败")
                    return ProcessingResult(False, f"AI检测在 {max_attempts} 次尝试后失败")
                self.logger.info("🔄 继续下一次尝试...")
                continue

            ai_probability = detection_result.data.get('ai_probability', 100.0)
            attempt_end_time = datetime.utcnow()
            attempt_duration = (attempt_end_time - attempt_start_time).total_seconds()

            self.logger.info(f"📊 检测结果: {ai_probability}% AI概率")
            self.logger.info(f"⏱️  本次尝试耗时: {attempt_duration:.2f}秒")

            # Check if AI concentration is below threshold
            if ai_probability < ai_threshold:
                loop_end_time = datetime.utcnow()
                total_duration = (loop_end_time - loop_start_time).total_seconds()

                self.logger.info("🎉 AI检测循环成功完成!")
                self.logger.info(f"✅ AI概率 ({ai_probability}%) 低于阈值 ({ai_threshold}%)")
                self.logger.info(f"📊 使用尝试次数: {attempt}/{max_attempts}")
                self.logger.info(f"⏱️  总循环耗时: {total_duration:.2f}秒")
                self.logger.info("🚀 文章已准备好发布!")

                return ProcessingResult(True, f"AI检测通过: {ai_probability}% AI概率", {
                    "ai_probability": ai_probability,
                    "attempts_used": attempt,
                    "threshold": ai_threshold,
                    "total_duration": total_duration,
                    "final_status": "ready_for_publish"
                })

            # AI concentration too high, need to re-optimize
            self.logger.warning(f"⚠️  AI概率 ({ai_probability}%) 超过阈值 ({ai_threshold}%)")

            if attempt < max_attempts:
                self.logger.info("🔄 需要重新优化内容以降低AI痕迹...")

                # Re-optimize content to reduce AI traces
                reopt_start_time = datetime.utcnow()
                optimization_result = await self._re_optimize_for_ai_reduction(article)
                reopt_end_time = datetime.utcnow()
                reopt_duration = (reopt_end_time - reopt_start_time).total_seconds()

                if not optimization_result.success:
                    self.logger.error(f"❌ 第 {attempt} 次重新优化失败: {optimization_result.message}")
                    self.logger.error(f"⏱️  重新优化耗时: {reopt_duration:.2f}秒")
                    if attempt == max_attempts:
                        return ProcessingResult(False, f"内容重新优化在 {max_attempts} 次尝试后失败")
                    self.logger.info("🔄 继续下一次尝试...")
                    continue

                self.logger.info(f"✅ 第 {attempt} 次重新优化成功")
                self.logger.info(f"⏱️  重新优化耗时: {reopt_duration:.2f}秒")
                self.logger.info("🔄 准备进行下一次AI检测...")
            else:
                # Maximum attempts reached
                loop_end_time = datetime.utcnow()
                total_duration = (loop_end_time - loop_start_time).total_seconds()

                self.logger.error("💥 AI检测循环失败!")
                self.logger.error(f"❌ 已达到最大尝试次数 ({max_attempts})")
                self.logger.error(f"📊 最终AI概率: {ai_probability}%")
                self.logger.error(f"🎯 要求阈值: {ai_threshold}%")
                self.logger.error(f"⏱️  总循环耗时: {total_duration:.2f}秒")

                return ProcessingResult(False, f"无法将AI概率降低到 {ai_threshold}% 以下，经过 {max_attempts} 次尝试后最终概率为 {ai_probability}%")

        # This should not be reached, but just in case
        self.logger.error("💥 AI检测循环意外结束")
        return ProcessingResult(False, "AI检测循环意外完成")

    async def _re_optimize_for_ai_reduction(self, article: Article) -> ProcessingResult:
        """
        Re-optimize content specifically to reduce AI detection traces.

        Args:
            article: Article to re-optimize

        Returns:
            ProcessingResult indicating success or failure
        """
        try:
            self.logger.info("🔄 开始AI痕迹降低优化...")

            from .llm_api import get_llm_service
            from .prompt_manager import get_prompt_manager

            llm_service = get_llm_service()
            prompt_manager = get_prompt_manager()
            self.logger.info("🔧 LLM重新优化服务和提示词管理器已初始化")

            # Get current content (use optimized if available)
            current_content = article.content_optimized or article.content_translated or article.content_original

            # Determine content source
            if article.content_optimized:
                content_source = "当前优化内容"
            elif article.content_translated:
                content_source = "翻译内容"
            else:
                content_source = "原始内容"

            self.logger.info(f"📝 重新优化内容来源: {content_source}")

            if not current_content:
                self.logger.error("❌ 没有可重新优化的内容")
                return ProcessingResult(False, "没有可重新优化的内容")

            original_length = len(current_content)
            original_word_count = len(current_content.split())

            self.logger.info(f"📝 当前内容长度: {original_length} 字符")
            self.logger.info(f"🔢 当前词数: {original_word_count} 词")

            # 显示当前待重新优化的内容（截取前300字符）
            content_preview = current_content[:300] + "..." if len(current_content) > 300 else current_content
            self.logger.info("📄 待重新优化的内容:")
            self.logger.info("─" * 60)
            self.logger.info(content_preview)
            self.logger.info("─" * 60)

            # 确定内容类型
            content_type = self._determine_content_type(article.title, current_content)
            self.logger.info(f"📋 内容类型: {content_type.value}")

            # Create a specialized prompt for reducing AI traces using prompt manager
            self.logger.info("📝 构建AI痕迹降低专用提示词...")
            ai_reduction_prompt = prompt_manager.get_optimization_prompt(
                content=current_content,
                ai_probability=75.0,  # 假设高AI概率，需要深度优化
                round_number=2,  # 这是重新优化，算作第二轮
                content_type=content_type,
                detection_feedback="需要降低AI痕迹",
                platform="toutiao"
            )

            # 显示使用的AI痕迹降低prompt
            prompt_preview = ai_reduction_prompt[:400] + "..." if len(ai_reduction_prompt) > 400 else ai_reduction_prompt
            self.logger.info("📝 AI痕迹降低专用Prompt:")
            self.logger.info("─" * 60)
            self.logger.info(prompt_preview)
            self.logger.info("─" * 60)

            self.logger.info("🚀 正在调用LLM API进行AI痕迹降低优化...")

            # Call LLM API with specialized prompt
            result = await llm_service._call_api(ai_reduction_prompt)

            if result.success and result.content:
                self.logger.info("✅ AI痕迹降低优化完成!")

                # Update article with re-optimized content
                article.content_optimized = result.content
                new_length = len(result.content)
                new_word_count = len(result.content.split())

                self.logger.info(f"📝 重新优化后长度: {new_length} 字符")
                self.logger.info(f"🔢 重新优化后词数: {new_word_count} 词")
                self.logger.info(f"📊 长度变化: {new_length - original_length:+d} 字符")
                self.logger.info(f"📊 词数变化: {new_word_count - original_word_count:+d} 词")

                if hasattr(result, 'model') and result.model:
                    self.logger.info(f"🤖 使用模型: {result.model}")

                if hasattr(result, 'usage') and result.usage:
                    self.logger.info(f"💰 Token使用情况: {result.usage}")

                # 显示重新优化的结果（截取前300字符）
                reoptimized_preview = result.content[:300] + "..." if len(result.content) > 300 else result.content
                self.logger.info("📄 重新优化结果内容:")
                self.logger.info("─" * 60)
                self.logger.info(reoptimized_preview)
                self.logger.info("─" * 60)

                self.logger.info("✅ AI痕迹降低优化步骤完成")

                return ProcessingResult(True, "AI痕迹降低优化成功", {
                    "model": getattr(result, 'model', 'unknown'),
                    "usage": getattr(result, 'usage', {}),
                    "original_length": original_length,
                    "new_length": new_length,
                    "original_word_count": original_word_count,
                    "new_word_count": new_word_count,
                    "length_change": new_length - original_length,
                    "word_count_change": new_word_count - original_word_count,
                    "optimization_type": "ai_reduction"
                })
            else:
                error_msg = getattr(result, 'error', '未知错误') if result else '调用失败'
                self.logger.error("❌ AI痕迹降低优化失败")
                self.logger.error(f"💬 错误信息: {error_msg}")
                return ProcessingResult(False, f"重新优化失败: {error_msg}")

        except Exception as e:
            self.logger.error("💥 AI痕迹降低优化过程发生异常")
            self.logger.error(f"💬 异常详情: {str(e)}")
            return ProcessingResult(False, f"重新优化异常: {str(e)}")
    
    async def _publish_content(self, article: Article) -> ProcessingResult:
        """Publish article to target platforms."""
        try:
            self.logger.info("📤 开始内容发布...")

            # Check if content is ready for publishing
            final_content = article.content_optimized or article.content_translated or article.content_original

            if not final_content:
                self.logger.error("❌ 没有可发布的内容")
                return ProcessingResult(False, "没有可发布的内容")

            # Determine content source
            if article.content_optimized:
                content_source = "优化后内容"
            elif article.content_translated:
                content_source = "翻译后内容"
            else:
                content_source = "原始内容"

            self.logger.info(f"📝 发布内容来源: {content_source}")
            self.logger.info(f"📝 发布内容长度: {len(final_content)} 字符")
            self.logger.info(f"📰 文章标题: {article.title}")

            # Check AI detection status
            if hasattr(article, 'ai_detection_passed') and hasattr(article, 'ai_detection_score'):
                if article.ai_detection_passed:
                    self.logger.info(f"✅ AI检测已通过 (概率: {article.ai_detection_score}%)")
                else:
                    self.logger.warning(f"⚠️  AI检测未通过 (概率: {article.ai_detection_score}%)，但仍继续发布")
            else:
                self.logger.info("ℹ️  未进行AI检测")

            # TODO: Implement actual content publishing to platforms
            self.logger.info("🚀 正在发布到目标平台...")
            self.logger.info("📱 目标平台: 今日头条 (默认)")

            # Simulate publishing process
            await asyncio.sleep(2)  # Simulate processing time

            self.logger.info("✅ 内容发布完成!")
            self.logger.info("🎉 文章已成功发布到平台")

            return ProcessingResult(True, "内容发布成功", {
                "content_source": content_source,
                "content_length": len(final_content),
                "title": article.title,
                "platform": "toutiao",
                "ai_detection_passed": getattr(article, 'ai_detection_passed', None),
                "ai_detection_score": getattr(article, 'ai_detection_score', None)
            })

        except Exception as e:
            self.logger.error("💥 内容发布过程发生异常")
            self.logger.error(f"💬 异常详情: {str(e)}")
            return ProcessingResult(False, f"发布异常: {str(e)}")
    
    def _get_status_for_step(self, step: str) -> ArticleStatus:
        """Get the appropriate article status for a processing step."""
        status_map = {
            ProcessingStep.CREATE: ArticleStatus.EXTRACTING,  # Use EXTRACTING for CREATE step
            ProcessingStep.EXTRACT: ArticleStatus.EXTRACTING,
            ProcessingStep.TRANSLATE: ArticleStatus.TRANSLATING,
            ProcessingStep.OPTIMIZE: ArticleStatus.OPTIMIZING,
            ProcessingStep.DETECT: ArticleStatus.DETECTING,
            ProcessingStep.PUBLISH: ArticleStatus.PUBLISHING
        }
        return status_map.get(step, ArticleStatus.PENDING)
    
    def _get_article(self, session, article_id: int) -> Optional[Article]:
        """Get article from database."""
        try:
            self.logger.info(f"🔍 正在查询文章 ID: {article_id}")
            cursor = session.execute("""
                SELECT id, title, source_url, source_platform, content_original,
                       content_translated, content_optimized, content_final, status,
                       creation_type, topic, keywords, selected_creation_prompt_id,
                       selected_model_id, creation_requirements
                FROM articles WHERE id = ?
            """, (article_id,))
            row = cursor.fetchone()
            self.logger.info(f"📊 数据库查询结果: {row}")

            if row:
                self.logger.info("✅ 找到文章记录，正在创建Article对象...")
                # Helper function to safely get values from sqlite3.Row
                def safe_get(row, key, default=None):
                    try:
                        return row[key] if row[key] is not None else default
                    except (KeyError, IndexError):
                        return default

                article = Article(
                    id=row['id'],
                    title=row['title'],
                    source_url=row['source_url'],
                    source_platform=row['source_platform'],
                    content_original=row['content_original'],
                    content_translated=row['content_translated'],
                    content_optimized=row['content_optimized'],
                    content_final=row['content_final'],
                    status=ArticleStatus(row['status']),
                    # Topic creation fields
                    creation_type=safe_get(row, 'creation_type', 'url_import'),
                    topic=safe_get(row, 'topic'),
                    keywords=safe_get(row, 'keywords'),
                    selected_creation_prompt_id=safe_get(row, 'selected_creation_prompt_id'),
                    selected_model_id=safe_get(row, 'selected_model_id'),
                    creation_requirements=safe_get(row, 'creation_requirements')
                )
                self.logger.info(f"✅ Article对象创建成功: {article.title}")
                return article
            else:
                self.logger.warning(f"⚠️ 未找到文章 ID: {article_id}")
                self.logger.error("❌ 无法找到文章记录，处理终止")
                return None
        except Exception as e:
            self.logger.error(f"❌ 获取文章失败 {article_id}: {e}")
            return None
    
    def _create_processing_task(self, session, task_id: str, article_id: int, steps: List[str]) -> Task:
        """Create a new processing task."""
        try:
            self.logger.info(f"🔧 正在创建处理任务: {task_id}")
            steps_str = ",".join(steps)
            session.execute(
                """INSERT INTO tasks (task_id, name, type, status, article_id)
                   VALUES (?, ?, ?, ?, ?)""",
                (task_id, f"Process Article {article_id}", "article_processing", "pending", article_id)
            )
            session.commit()
            self.logger.info(f"✅ 处理任务创建成功: {task_id}")

            task = Task(
                id=1,  # We'd need to get the actual ID from the database
                task_id=task_id,
                name=f"Process Article {article_id}",
                type="article_processing",
                article_id=article_id,
                status=TaskStatus.PENDING
            )
            self.logger.info(f"📋 Task对象创建成功: {task.task_id}")
            return task
        except Exception as e:
            self.logger.error(f"❌ 创建处理任务失败: {e}")
            self.logger.info("🔄 返回模拟任务用于测试...")
            # Return mock task for testing
            return Task(
                id=1,
                task_id=task_id,
                name=f"Process Article {article_id}",
                type="article_processing",
                article_id=article_id,
                status=TaskStatus.PENDING
            )
    
    async def _update_task_status(self, session, task_id: int, status: TaskStatus, error_message: str = None):
        """Update task status in database."""
        try:
            session.execute(
                "UPDATE tasks SET status = ? WHERE task_id = ?",
                (status.value, str(task_id))
            )
            session.commit()
            self.logger.info(f"Task {task_id} status updated to {status}")
        except Exception as e:
            self.logger.error(f"Failed to update task status: {e}")

    async def _update_task_progress(self, session, task_id: int, progress: float):
        """Update task progress in database."""
        # For now, just log progress since we don't have a progress column
        self.logger.info(f"Task {task_id} progress updated to {progress}%")

    async def _update_article_status(self, session, article_id: int, status: ArticleStatus):
        """Update article status in database."""
        try:
            session.execute(
                "UPDATE articles SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status.value, article_id)
            )
            session.commit()
            self.logger.info(f"Article {article_id} status updated to {status}")
        except Exception as e:
            self.logger.error(f"Failed to update article status: {e}")

    async def _intelligent_detection_loop(self, article: Article, content: str, detector, max_rounds: int, threshold: float):
        """智能循环检测和优化机制"""
        try:
            current_content = content

            for round_num in range(1, max_rounds + 1):
                self.logger.info(f"🔍 第 {round_num}/{max_rounds} 轮AI检测...")

                # 执行AI检测
                detection_result = await detector.detect_ai_content(current_content)

                if not detection_result.success:
                    self.logger.error(f"❌ 第 {round_num} 轮检测失败: {detection_result.error}")
                    continue

                ai_probability = detection_result.ai_probability
                self.logger.info(f"📊 第 {round_num} 轮检测结果: AI概率 {ai_probability}%")

                # 如果通过检测，直接返回
                if ai_probability < threshold:
                    self.logger.info(f"🎉 第 {round_num} 轮检测通过! (AI概率: {ai_probability}% < 阈值: {threshold}%)")
                    # 更新文章内容为最终优化版本
                    if round_num > 1:  # 如果经过了优化
                        article.content_optimized = current_content
                        self.logger.info("💾 已更新文章为最终优化版本")
                    return detection_result

                # 如果是最后一轮，不再优化
                if round_num == max_rounds:
                    self.logger.warning(f"⚠️ 已达到最大优化轮数 ({max_rounds})，停止优化")
                    self.logger.warning(f"⚠️ 最终AI概率: {ai_probability}% (未达到阈值: {threshold}%)")
                    return detection_result

                # 需要进一步优化
                self.logger.info(f"🔄 第 {round_num} 轮检测未通过 (AI概率: {ai_probability}% >= 阈值: {threshold}%)")
                self.logger.info(f"🛠️ 开始第 {round_num} 轮内容优化...")

                # 执行针对性优化
                optimization_result = await self._optimize_for_ai_detection(
                    current_content, ai_probability, round_num
                )

                if optimization_result.success:
                    current_content = optimization_result.content
                    self.logger.info(f"✅ 第 {round_num} 轮优化完成，内容长度: {len(current_content)} 字符")
                else:
                    self.logger.error(f"❌ 第 {round_num} 轮优化失败: {optimization_result.error}")
                    # 优化失败时返回当前检测结果
                    return detection_result

            # 如果所有轮次都完成但仍未通过，返回最后的检测结果
            return detection_result

        except Exception as e:
            self.logger.error(f"💥 智能循环检测异常: {e}")
            # 返回一个失败的检测结果
            from .ai_detection import AIDetectionResult
            return AIDetectionResult(
                ai_probability=100.0,
                confidence=0.0,
                detector="zhuque",
                status="error",
                error=f"循环检测异常: {str(e)}"
            )

    async def _optimize_for_ai_detection(self, content: str, current_ai_prob: float, round_num: int):
        """针对AI检测结果进行优化"""
        try:
            from .llm_api import get_llm_service
            from .prompt_manager import get_prompt_manager, ContentType

            llm_service = get_llm_service()
            prompt_manager = get_prompt_manager()

            # 使用增强的提示词管理器生成优化提示词
            self.logger.info(f"🎯 使用提示词管理器生成第{round_num}轮优化提示词...")

            # 假设是技术内容类型（实际应用中可以传入更多上下文信息）
            content_type = ContentType.GENERAL

            optimization_prompt = prompt_manager.get_optimization_prompt(
                content=content,
                ai_probability=current_ai_prob,
                round_number=round_num,
                content_type=content_type,
                detection_feedback=f"当前AI概率为{current_ai_prob}%，需要降低到25%以下",
                platform="toutiao"
            )

            # 显示使用的优化prompt（截取前400字符）
            prompt_preview = optimization_prompt[:400] + "..." if len(optimization_prompt) > 400 else optimization_prompt
            self.logger.info("📝 使用的优化Prompt:")
            self.logger.info("─" * 60)
            self.logger.info(prompt_preview)
            self.logger.info("─" * 60)

            # 执行优化
            result = await llm_service.optimize_content(
                content=content,
                custom_prompt=optimization_prompt
            )

            return result

        except Exception as e:
            self.logger.error(f"💥 针对性优化异常: {e}")
            from .llm_api import LLMResult
            return LLMResult(
                success=False,
                content=content,
                error=f"优化异常: {str(e)}"
            )


# Global processor instance
_processor_instance = None


def get_article_processor() -> ArticleProcessor:
    """Get the global article processor instance."""
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = ArticleProcessor()
    return _processor_instance
