"""
Topic-based article creation API endpoints.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import json
import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..core.database import get_db_connection
from ..services.article_processor import get_article_processor

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/articles", tags=["topic-creation"])


# Pydantic models for API requests/responses
class TopicCreationRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=500, description="文章主题")
    keywords: Optional[List[str]] = Field(default=[], description="关键词列表")
    creation_requirements: Optional[str] = Field(default="", description="创作要求")
    selected_creation_prompt_id: int = Field(..., description="选择的创作提示词ID")
    selected_model_id: Optional[int] = Field(default=None, description="选择的模型ID")
    auto_process: bool = Field(default=True, description="是否自动处理")
    target_length: Optional[str] = Field(default="mini", description="目标长度: mini, short, medium, long")
    writing_style: Optional[str] = Field(default="", description="写作风格")


class BatchTopicCreationRequest(BaseModel):
    topics: List[str] = Field(..., min_items=1, max_items=10, description="主题列表")
    shared_config: TopicCreationRequest = Field(..., description="共享配置")


class CreationConfigResponse(BaseModel):
    creation_prompts: List[Dict[str, Any]]
    available_models: List[Dict[str, Any]]
    default_settings: Dict[str, Any]


class TopicCreationResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.get("/creation-config", response_model=CreationConfigResponse)
async def get_creation_config():
    """获取主题创作的配置选项"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取所有可用的提示词模板（不限制类型，让用户自由选择）
        cursor.execute("""
            SELECT id, name, display_name, description, type, template
            FROM prompt_templates
            WHERE is_active = 1
            ORDER BY priority DESC, display_name
        """)
        creation_prompts = []
        for row in cursor.fetchall():
            creation_prompts.append({
                "id": row[0],
                "name": row[1],
                "display_name": row[2],
                "description": row[3],
                "type": row[4],
                "preview": row[5][:200] + "..." if len(row[5]) > 200 else row[5]
            })
        
        # 获取可用的模型
        cursor.execute("""
            SELECT am.id, am.model_name, am.display_name, am.model_type,
                   ap.name as provider_name, ap.display_name as provider_display_name
            FROM api_models am
            JOIN api_providers ap ON am.provider_id = ap.id
            WHERE am.is_enabled = 1 AND ap.is_enabled = 1
            AND am.model_type = 'text'
            ORDER BY am.display_name
        """)
        available_models = []
        for row in cursor.fetchall():
            available_models.append({
                "id": row[0],
                "model_name": row[1],
                "display_name": row[2],
                "model_type": row[3],
                "provider_name": row[4],
                "provider_display_name": row[5]
            })
        
        conn.close()
        
        # 默认设置
        default_settings = {
            "target_length": "mini",
            "writing_style": "professional",
            "auto_process": True,
            "creation_requirements": "请创作一篇专业、有深度的技术文章，内容要有实用价值。"
        }
        
        return CreationConfigResponse(
            creation_prompts=creation_prompts,
            available_models=available_models,
            default_settings=default_settings
        )
        
    except Exception as e:
        logger.error(f"Failed to get creation config: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.post("/create-by-topic", response_model=TopicCreationResponse)
async def create_article_by_topic(request: TopicCreationRequest):
    """根据主题创作文章"""
    try:
        logger.info(f"🎯 开始主题创作: {request.topic}")
        
        # 验证提示词和模型是否存在
        conn = get_db_connection()
        try:
            cursor = conn.cursor()

            # 验证创作提示词（必选）
            cursor.execute("SELECT id, template FROM prompt_templates WHERE id = ? AND is_active = 1",
                         (request.selected_creation_prompt_id,))
            prompt_row = cursor.fetchone()
            if not prompt_row:
                raise HTTPException(status_code=400, detail="选择的提示词不存在或已禁用")

            if request.selected_model_id:
                cursor.execute("""
                    SELECT am.id FROM api_models am
                    JOIN api_providers ap ON am.provider_id = ap.id
                    WHERE am.id = ? AND am.is_enabled = 1 AND ap.is_enabled = 1
                """, (request.selected_model_id,))
                if not cursor.fetchone():
                    raise HTTPException(status_code=400, detail="选择的模型不存在或已禁用")

            # 创建文章记录
            now = datetime.utcnow().isoformat()
            import time
            timestamp = int(time.time() * 1000)  # 毫秒级时间戳
            cursor.execute('''
                INSERT INTO articles (
                    title, source_url, source_platform, content_original, status,
                    creation_type, topic, keywords, selected_creation_prompt_id,
                    selected_model_id, creation_requirements, target_length, writing_style,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                f"主题创作: {request.topic}",
                f"topic://{request.topic}#{timestamp}",  # 添加时间戳确保唯一性
                "topic_creation",
                "",  # 内容将在处理过程中生成
                "pending",
                "topic_creation",
                request.topic,
                json.dumps(request.keywords or []),
                request.selected_creation_prompt_id,
                request.selected_model_id,
                request.creation_requirements,
                request.target_length,  # 保存目标长度
                request.writing_style,  # 保存写作风格
                now,
                now
            ))

            article_id = cursor.lastrowid
            conn.commit()

        finally:
            conn.close()
        
        logger.info(f"✅ 主题创作文章记录创建成功，ID: {article_id}")
        
        # 如果启用自动处理，开始处理流程
        task_id = None
        if request.auto_process:
            try:
                processor = get_article_processor()
                # 主题创作使用专门的处理步骤：创作->优化->检测
                # 跳过翻译步骤，因为创作内容已经是中文
                result = await processor.process_article(
                    article_id=article_id,
                    steps=['create', 'optimize', 'detect'],  # 移除translate步骤
                    priority='normal'
                )
                task_id = result.get("task_id")
                logger.info(f"🚀 自动处理任务已启动，任务ID: {task_id}")
            except Exception as e:
                logger.error(f"启动自动处理失败: {e}")
                # 不抛出异常，文章已创建成功
        
        return TopicCreationResponse(
            success=True,
            data={
                "id": article_id,
                "title": f"主题创作: {request.topic}",
                "topic": request.topic,
                "keywords": request.keywords,
                "creation_type": "topic_creation",
                "status": "pending",
                "auto_process": request.auto_process,
                "task_id": task_id,
                "created_at": now + "Z"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"主题创作失败: {e}")
        raise HTTPException(status_code=500, detail=f"主题创作失败: {str(e)}")


@router.post("/batch-create", response_model=Dict[str, Any])
async def batch_create_by_topics(request: BatchTopicCreationRequest):
    """批量主题创作"""
    try:
        logger.info(f"🎯 开始批量主题创作，共 {len(request.topics)} 个主题")
        
        results = []
        failed_topics = []
        
        for topic in request.topics:
            try:
                # 为每个主题创建单独的请求
                topic_request = TopicCreationRequest(
                    topic=topic,
                    keywords=request.shared_config.keywords,
                    creation_requirements=request.shared_config.creation_requirements,
                    selected_creation_prompt_id=request.shared_config.selected_creation_prompt_id,
                    selected_model_id=request.shared_config.selected_model_id,
                    auto_process=request.shared_config.auto_process,
                    target_length=request.shared_config.target_length,
                    writing_style=request.shared_config.writing_style
                )
                
                result = await create_article_by_topic(topic_request)
                if result.success:
                    results.append(result.data)
                else:
                    failed_topics.append({"topic": topic, "error": result.error})
                    
            except Exception as e:
                logger.error(f"主题 '{topic}' 创作失败: {e}")
                failed_topics.append({"topic": topic, "error": str(e)})
        
        return {
            "success": True,
            "data": {
                "created_count": len(results),
                "failed_count": len(failed_topics),
                "created_articles": results,
                "failed_topics": failed_topics
            }
        }
        
    except Exception as e:
        logger.error(f"批量主题创作失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量创作失败: {str(e)}")
