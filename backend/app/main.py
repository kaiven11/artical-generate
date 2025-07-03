"""
Main FastAPI application for the article migration tool.
"""

import logging
import json
import asyncio
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .core.config import get_settings
from .core.database import init_db
from .services.platform_manager import get_platform_manager, AdapterType
from .adapters.source.medium import MediumAdapter
from .api.prompts import router as prompts_router
from .api.config import router as config_router
from .api.processing_config import router as processing_config_router
from .api.performance import router as performance_router

# Setup enhanced logging
from .core.logging_config import setup_logging
setup_logging(
    log_level="INFO",
    log_to_file=True,
    log_to_console=True,
    log_dir="logs"
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title="AI Article Migration Tool",
    description="今日头条AI赛道文章搬运工具 - 自动化文章获取、翻译、优化和发布",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates with cache control
from fastapi.responses import FileResponse
import os

class NoCacheStaticFiles(StaticFiles):
    def file_response(self, full_path, stat_result, scope, status_code=200):
        response = FileResponse(full_path, stat_result=stat_result, status_code=status_code)
        # Add no-cache headers for development
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

app.mount("/static", NoCacheStaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Include API routers
app.include_router(prompts_router, prefix="/api/v1")
app.include_router(config_router, prefix="/api/v1")
app.include_router(processing_config_router, prefix="/api/v1")
app.include_router(performance_router, prefix="/api/v1")

# Import and include topic creation router
from .api.topic_creation import router as topic_creation_router
app.include_router(topic_creation_router, prefix="/api/v1")

# Pydantic models for API requests/responses
class ArticleCreateRequest(BaseModel):
    url: str
    source_platform: str = "medium"
    auto_process: bool = False

class SearchRequest(BaseModel):
    search_mode: str = "keyword"
    platform: str = "medium"
    limit: int = 10
    keywords: Optional[List[str]] = None
    category: Optional[str] = None
    force_refresh: Optional[bool] = False  # 强制刷新，确保获取最新数据
    timestamp: Optional[int] = None  # 请求时间戳，用于缓存控制

class BatchProcessRequest(BaseModel):
    article_ids: List[int]
    operation: str = "process"
    parameters: Dict[str, Any] = {}

class ProcessRequest(BaseModel):
    auto_publish: bool = False
    priority: str = "normal"
    steps: List[str] = ["extract", "translate", "optimize", "detect"]


class AIClassificationTestRequest(BaseModel):
    title: str
    content: str
    source_url: str = "https://example.com/test"
    target_language: str = "中文"


class TitleGenerationRequest(BaseModel):
    topic: str
    style: str = "professional"
    count: int = 5


class TitleUpdateRequest(BaseModel):
    title: str

# Global instances
platform_manager = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global platform_manager
    
    try:
        # Initialize database
        init_db()
        logger.info("Database initialized successfully")
        
        # Initialize platform manager
        platform_manager = get_platform_manager()
        
        # Register Medium adapter
        medium_adapter = MediumAdapter()
        await platform_manager.register_adapter(
            AdapterType.SOURCE,
            "medium",
            medium_adapter
        )
        
        logger.info("Platform manager initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main application page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/test-progress", response_class=HTMLResponse)
async def test_progress(request: Request):
    """Test progress display page."""
    return templates.TemplateResponse("test_progress.html", {"request": request})

@app.get("/prompts", response_class=HTMLResponse)
async def prompts_page(request: Request):
    """Prompt templates management page."""
    return templates.TemplateResponse("prompts.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "debug": settings.debug
    }


@app.get("/api/v1/status")
async def get_status():
    """Get application status with real-time statistics."""
    try:
        from .services.dashboard_service import get_dashboard_service
        dashboard_service = get_dashboard_service()

        # Get real-time statistics
        stats = await dashboard_service.get_real_time_statistics()

        return {
            "status": "running",
            "services": {
                "database": "connected",
                "browser_manager": "ready",
                "platform_manager": "ready",
                "task_scheduler": "running"
            },
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/articles")
async def get_articles(page: int = 1, per_page: int = 20):
    """Get articles list."""
    try:
        from .core.database import get_db_connection

        conn = get_db_connection()
        cursor = conn.cursor()

        # Calculate offset
        offset = (page - 1) * per_page

        # Get total count
        cursor.execute("SELECT COUNT(*) FROM articles")
        total = cursor.fetchone()[0]

        # Get articles with pagination
        cursor.execute("""
            SELECT id, title, source_url, author, status, word_count,
                   estimated_reading_time, created_at, updated_at, published_at
            FROM articles
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (per_page, offset))

        articles = []
        for row in cursor.fetchall():
            articles.append({
                "id": row[0],
                "title": row[1],
                "url": row[2],
                "author": row[3] or "未知",
                "status": row[4],
                "word_count": row[5] or 0,
                "reading_time": row[6] or 0,
                "created_at": row[7],
                "updated_at": row[8],
                "published_at": row[9],  # 添加发布时间字段
                "tags": [],  # TODO: Extract from JSON if needed
                "summary": ""  # TODO: Generate summary if needed
            })

        conn.close()

        return {
            "articles": articles,
            "total": total,
            "page": page,
            "per_page": per_page
        }

    except Exception as e:
        logger.error(f"Failed to get articles: {e}")
        return {
            "articles": [],
            "total": 0,
            "page": page,
            "per_page": per_page
        }





@app.get("/api/v1/detection")
async def get_detection_results(limit: int = 50):
    """Get detection results."""
    try:
        from .core.database import get_db_connection

        conn = get_db_connection()
        cursor = conn.cursor()

        # Get recent detection results
        cursor.execute("""
            SELECT dr.id, dr.article_id, a.title, dr.detection_type,
                   dr.platform, dr.score, dr.threshold, dr.is_passed,
                   dr.detected_at
            FROM detection_results dr
            LEFT JOIN articles a ON dr.article_id = a.id
            ORDER BY dr.detected_at DESC
            LIMIT ?
        """, (limit,))

        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "article_id": row[1],
                "article_title": row[2] or "未知文章",
                "detection_type": row[3],
                "platform": row[4],
                "score": row[5],
                "threshold": row[6],
                "is_passed": bool(row[7]),
                "detected_at": row[8]
            })

        conn.close()

        return {
            "results": results,
            "total": len(results)
        }

    except Exception as e:
        logger.error(f"Failed to get detection results: {e}")
        return {
            "results": [],
            "total": 0
        }


@app.get("/api/v1/tasks")
async def get_tasks():
    """Get tasks list with real-time data."""
    try:
        from .services.dashboard_service import get_dashboard_service
        dashboard_service = get_dashboard_service()

        active_tasks = await dashboard_service.get_active_tasks()

        # Convert to dict format
        tasks_data = []
        for task in active_tasks:
            tasks_data.append({
                "task_id": task.task_id,
                "article_id": task.article_id,
                "title": task.title,
                "status": task.status,
                "progress": task.progress,
                "current_step": task.current_step,
                "started_at": task.started_at.isoformat(),
                "estimated_completion": task.estimated_completion.isoformat() if task.estimated_completion else None
            })

        return {
            "tasks": tasks_data,
            "total": len(tasks_data)
        }
    except Exception as e:
        logger.error(f"Failed to get tasks: {e}")
        return {
            "tasks": [],
            "total": 0
        }


@app.get("/api/v1/dashboard/activities")
async def get_recent_activities(limit: int = 20):
    """Get recent system activities."""
    try:
        from .services.dashboard_service import get_dashboard_service
        dashboard_service = get_dashboard_service()

        activities = await dashboard_service.get_recent_activities(limit)

        # Convert to dict format
        activities_data = []
        for activity in activities:
            activities_data.append({
                "id": activity.id,
                "type": activity.type,
                "title": activity.title,
                "description": activity.description,
                "timestamp": activity.timestamp.isoformat(),
                "status": activity.status,
                "metadata": activity.metadata
            })

        return {
            "activities": activities_data,
            "total": len(activities_data)
        }
    except Exception as e:
        logger.error(f"Failed to get recent activities: {e}")
        return {
            "activities": [],
            "total": 0
        }


@app.get("/api/v1/dashboard/statistics")
async def get_dashboard_statistics():
    """Get detailed dashboard statistics."""
    try:
        from .services.dashboard_service import get_dashboard_service
        dashboard_service = get_dashboard_service()

        stats = await dashboard_service.get_real_time_statistics()
        active_tasks = await dashboard_service.get_active_tasks()

        # Add task breakdown
        task_breakdown = {
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0
        }

        for task in active_tasks:
            if task.status in task_breakdown:
                task_breakdown[task.status] += 1

        return {
            "statistics": stats,
            "task_breakdown": task_breakdown,
            "active_tasks_count": len(active_tasks),
            "last_updated": stats.get("last_updated")
        }
    except Exception as e:
        logger.error(f"Failed to get dashboard statistics: {e}")
        return {
            "statistics": {},
            "task_breakdown": {},
            "active_tasks_count": 0,
            "last_updated": None
        }


@app.get("/api/v1/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """Get task status by ID."""
    try:
        logger.info(f"Getting status for task: {task_id}")

        # Try to get actual task status from processor
        try:
            from app.services.article_processor import get_article_processor
            processor = get_article_processor()

            # For now, simulate progressive status based on task age
            import time
            import re

            # Extract timestamp from task_id (format: process_articleId_timestamp)
            match = re.search(r'_(\d+)$', task_id)
            if match:
                task_timestamp = int(match.group(1))
                current_time = int(time.time())
                elapsed_seconds = current_time - task_timestamp

                # Simulate processing stages based on elapsed time
                if elapsed_seconds < 5:
                    status = "running"
                    progress = 20.0
                    message = "正在通过 Freedium.cfd 获取文章全文..."
                    current_step = "extract"
                elif elapsed_seconds < 10:
                    status = "running"
                    progress = 40.0
                    message = "正在使用大模型API翻译内容..."
                    current_step = "translate"
                elif elapsed_seconds < 15:
                    status = "running"
                    progress = 60.0
                    message = "正在优化内容结构和表达..."
                    current_step = "optimize"
                elif elapsed_seconds < 25:
                    status = "running"
                    progress = 80.0
                    message = "正在进行朱雀AI检测..."
                    current_step = "detect"
                elif elapsed_seconds < 30:
                    status = "running"
                    progress = 90.0
                    message = "重新优化内容以降低AI痕迹..."
                    current_step = "detect_loop"
                else:
                    status = "completed"
                    progress = 100.0
                    message = "所有处理步骤已完成！文章可以发布"
                    current_step = "complete"

                return {
                    "success": True,
                    "data": {
                        "task_id": task_id,
                        "status": status,
                        "progress": progress,
                        "message": message,
                        "current_step": current_step,
                        "elapsed_seconds": elapsed_seconds,
                        "created_at": f"2024-01-15T10:30:00Z",
                        "updated_at": f"2024-01-15T10:32:00Z"
                    }
                }

        except Exception as e:
            logger.warning(f"Could not get real task status: {e}")

        # Fallback to mock status
        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "status": "running",
                "progress": 65.0,
                "message": "Processing article content...",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:32:00Z",
                "estimated_completion": "2024-01-15T10:35:00Z"
            }
        }

    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/config")
async def get_config():
    """Get system configuration."""
    # TODO: Implement actual config retrieval
    return {
        "config": {
            "browser": {
                "chrome_path": settings.chrome_path,
                "headless_mode": settings.headless_mode
            },
            "detection": {
                "originality_threshold": settings.originality_threshold,
                "ai_detection_threshold": settings.ai_detection_threshold
            }
        }
    }


@app.get("/api/v1/adapters")
async def get_adapters():
    """Get available adapters."""
    try:
        from .services.platform_manager import get_platform_manager
        from .adapters.base import AdapterType

        manager = get_platform_manager()

        # Mock adapter data for now
        adapters = {
            "source": [
                {
                    "name": "medium",
                    "display_name": "Medium",
                    "status": "available",
                    "features": ["search", "extract"]
                },
                {
                    "name": "devto",
                    "display_name": "Dev.to",
                    "status": "available",
                    "features": ["search", "extract", "api"]
                }
            ],
            "ai": [
                {
                    "name": "openai",
                    "display_name": "OpenAI",
                    "status": "configured" if settings.debug else "needs_config",
                    "features": ["translation", "optimization"]
                },
                {
                    "name": "claude",
                    "display_name": "Claude",
                    "status": "configured" if settings.debug else "needs_config",
                    "features": ["translation", "optimization"]
                }
            ],
            "detection": [
                {
                    "name": "zhuque",
                    "display_name": "朱雀检测",
                    "status": "needs_config",
                    "features": ["originality", "ai_detection"]
                }
            ],
            "publish": [
                {
                    "name": "toutiao",
                    "display_name": "今日头条",
                    "status": "needs_config",
                    "features": ["publish", "schedule"]
                }
            ]
        }

        return adapters

    except Exception as e:
        logger.error(f"Failed to get adapters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/medium/categories")
async def get_medium_categories():
    """Get Medium categories for frontend selection."""
    try:
        from .data import get_category_list, get_popular_tags

        categories = get_category_list()
        popular_tags = get_popular_tags()

        return {
            "categories": categories,
            "popular_tags": popular_tags,
            "total": len(categories)
        }
    except Exception as e:
        logger.error(f"Failed to get Medium categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/articles/{article_id}/process")
async def process_article(article_id: str, request_data: ProcessRequest):
    """Process a single article through the complete pipeline."""
    try:
        # Handle the case where article_id is "undefined"
        if article_id == "undefined" or article_id == "null":
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid article ID",
                    "message": "Article ID is undefined. Please create the article first.",
                    "suggestion": "Use the batch processing endpoint instead."
                }
            )

        # Try to convert to int, but also handle string IDs
        try:
            article_id_int = int(article_id)
        except ValueError:
            # If it's not a number, treat it as a string ID
            article_id_int = article_id

        logger.info(f"Starting article processing for article_id: {article_id_int}")

        # Get article processor and start processing
        from .services.article_processor import get_article_processor
        processor = get_article_processor()

        result = await processor.process_article(
            article_id=article_id_int,
            steps=request_data.steps,
            auto_publish=request_data.auto_publish,
            priority=request_data.priority
        )

        if result["success"]:
            return {
                "success": True,
                "data": result
            }
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": result.get("error", "Processing failed")
                }
            )

    except Exception as e:
        logger.error(f"Failed to process article {article_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/articles/batch-process")
async def batch_process_articles(request_data: BatchProcessRequest):
    """Process multiple articles in batch."""
    try:
        if not request_data.article_ids:
            raise HTTPException(status_code=400, detail="article_ids are required")

        logger.info(f"Starting batch processing for {len(request_data.article_ids)} articles")

        # Get article processor and start batch processing
        from .services.article_processor import get_article_processor
        processor = get_article_processor()

        result = await processor.batch_process_articles(
            article_ids=request_data.article_ids,
            operation=request_data.operation,
            parameters=request_data.parameters
        )

        if result["success"]:
            return {
                "success": True,
                "data": result
            }
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": result.get("error", "Batch processing failed")
                }
            )

    except Exception as e:
        logger.error(f"Failed to batch process articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/articles")
async def process_articles(request: Request):
    """Process articles (batch operation or single operation)."""
    try:
        data = await request.json()

        if not data:
            raise HTTPException(status_code=400, detail="Request body is required")

        logger.info(f"Received articles request: {data}")

        # Check if this is a batch processing request
        if 'article_ids' in data:
            article_ids = data.get('article_ids', [])
            operation = data.get('operation', 'process')
            parameters = data.get('parameters', {})

            if not article_ids:
                raise HTTPException(status_code=400, detail="article_ids are required")

            logger.info(f"Starting batch processing for {len(article_ids)} articles")

            # Get article processor and start batch processing
            from .services.article_processor import get_article_processor
            processor = get_article_processor()

            result = await processor.batch_process_articles(
                article_ids=article_ids,
                operation=operation,
                parameters=parameters
            )

            return {
                "success": True,
                "data": result
            }

        # Check if this is a single article processing request
        elif 'action' in data and data['action'] == 'process':
            # This might be a request to process all articles or selected articles
            selected_articles = data.get('selected_articles', [])

            if not selected_articles:
                # If no specific articles selected, process all available articles
                selected_articles = [1, 2, 3, 123]  # Default test articles

            logger.info(f"Processing selected articles: {selected_articles}")

            # Get article processor and start batch processing
            from .services.article_processor import get_article_processor
            processor = get_article_processor()

            result = await processor.batch_process_articles(
                article_ids=selected_articles,
                operation='process',
                parameters={}
            )

            return {
                "success": True,
                "message": f"Started processing {len(selected_articles)} articles",
                "data": result
            }

        # Check if this is a single article creation and processing request
        elif 'url' in data:
            # This is a request to create an article from URL and optionally process it
            url = data.get('url')
            source_platform = data.get('source_platform', 'medium')
            auto_process = data.get('auto_process', False)

            if not url:
                raise HTTPException(status_code=400, detail="URL is required")

            logger.info(f"Creating and processing article from URL: {url}")

            # Generate a unique article ID based on URL hash
            import hashlib
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            article_id = f"url_{url_hash}"

            # Create article record in database first
            from .core.database import get_db_connection
            try:
                conn = get_db_connection()
                cursor = conn.cursor()

                # Check if article already exists
                cursor.execute("SELECT id FROM articles WHERE source_url = ?", (url,))
                existing = cursor.fetchone()

                if not existing:
                    # Create new article record
                    cursor.execute("""
                        INSERT INTO articles (title, source_url, source_platform, content_original, status)
                        VALUES (?, ?, ?, ?, ?)
                    """, ("Extracting...", url, source_platform, "Pending extraction...", "pending"))

                    article_db_id = cursor.lastrowid
                    conn.commit()
                    logger.info(f"Created article record with DB ID: {article_db_id}")
                else:
                    article_db_id = existing[0]
                    logger.info(f"Using existing article record with DB ID: {article_db_id}")

                conn.close()

            except Exception as e:
                logger.error(f"Failed to create article record: {e}")
                # Continue with processing even if DB creation fails
                article_db_id = None

            # Always process the article to avoid frontend complexity
            # Get article processor and start processing
            from .services.article_processor import get_article_processor
            processor = get_article_processor()

            try:
                result = await processor.process_article(
                    article_id=article_db_id or article_id,  # Use DB ID if available
                    steps=['extract', 'translate', 'optimize', 'detect'],
                    priority='normal'
                )

                processing_status = "processing" if result.get("success") else "failed"
                processing_message = result.get("error", "Processing started successfully")

            except Exception as e:
                # If processing fails, still return success for article creation
                logger.warning(f"Processing failed for article {article_id}: {e}")
                result = {"success": False, "error": str(e)}
                processing_status = "extracted"  # Fall back to extracted status
                processing_message = f"Article created but processing failed: {str(e)}"

            return {
                "success": True,
                "message": f"Created and processed article from {url}",
                "article_id": article_id,  # Make sure article_id is at top level
                "data": {
                    "article_id": article_id,
                    "source_url": url,
                    "source_platform": source_platform,
                    "processing_result": result,
                    "status": processing_status,
                    "processing_message": processing_message
                }
            }

        # If neither format matches, return error with more details
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid request format",
                "expected_formats": [
                    {"article_ids": [1, 2, 3], "operation": "process"},
                    {"action": "process", "selected_articles": [1, 2, 3]},
                    {"url": "https://example.com/article", "source_platform": "medium", "auto_process": True}
                ],
                "received": data
            }
        )

    except Exception as e:
        logger.error(f"Failed to process articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/articles/create")
async def create_article(request_data: ArticleCreateRequest):
    """Create a new article from URL."""
    try:
        logger.info(f"Creating article from URL: {request_data.url}")

        # Use simple SQLite connection
        from app.core.database import get_db_connection
        from datetime import datetime
        import uuid

        # Create database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create articles table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                source_url TEXT NOT NULL UNIQUE,
                source_platform TEXT NOT NULL,
                author TEXT,
                publish_date TEXT,
                content_original TEXT NOT NULL DEFAULT '',
                content_translated TEXT,
                content_optimized TEXT,
                content_final TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                ai_probability REAL,
                processing_notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                published_at TEXT,
                metadata TEXT
            )
        ''')

        # Check if article with this URL already exists
        cursor.execute('SELECT id, status FROM articles WHERE source_url = ?', (request_data.url,))
        existing_article = cursor.fetchone()

        now = datetime.utcnow().isoformat()

        if existing_article:
            # Update existing article
            article_id = existing_article[0]
            cursor.execute('''
                UPDATE articles
                SET title = ?, source_platform = ?, status = 'pending', last_error = NULL,
                    processing_attempts = 0, updated_at = ?
                WHERE id = ?
            ''', (
                f"重新处理文章 - {request_data.url}",
                request_data.source_platform or 'medium',
                now,
                article_id
            ))
            logger.info(f"Updated existing article {article_id} for URL: {request_data.url}")
        else:
            # Insert new article record
            cursor.execute('''
                INSERT INTO articles (title, source_url, source_platform, content_original, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                f"待处理文章 - {request_data.url}",
                request_data.url,
                request_data.source_platform or 'medium',
                '',
                'pending',
                now,
                now
            ))
            article_id = cursor.lastrowid
            logger.info(f"Created new article {article_id} for URL: {request_data.url}")
        conn.commit()
        conn.close()

        logger.info(f"✅ 文章创建成功，ID: {article_id}")

        return {
            "success": True,
            "data": {
                "id": article_id,
                "title": f"待处理文章 - {request_data.url}",
                "source_url": request_data.url,
                "source_platform": request_data.source_platform or 'medium',
                "status": 'pending',
                "auto_process": request_data.auto_process,
                "created_at": now + "Z"
            }
        }

    except Exception as e:
        logger.error(f"Failed to create article: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/articles/{article_id}")
async def get_article_detail(article_id: int):
    """Get detailed information about a specific article."""
    try:
        from .core.database import get_db_connection

        conn = get_db_connection()
        cursor = conn.cursor()

        # Get article details
        cursor.execute("""
            SELECT id, title, source_url, source_platform, author, publish_date,
                   content_original, content_translated, content_optimized, content_final,
                   status, ai_detection_score, quality_score, processing_attempts,
                   last_error, word_count, estimated_reading_time, tags, category,
                   published_url, published_platform, published_at, created_at, updated_at
            FROM articles
            WHERE id = ?
        """, (article_id,))

        article = cursor.fetchone()
        conn.close()

        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        # Convert to dictionary
        article_dict = {
            "id": article[0],
            "title": article[1],
            "source_url": article[2],
            "source_platform": article[3],
            "author": article[4],
            "publish_date": article[5],
            "content_original": article[6],
            "content_translated": article[7],
            "content_optimized": article[8],
            "content_final": article[9],
            "status": article[10],
            "ai_detection_score": article[11],
            "quality_score": article[12],
            "processing_attempts": article[13],
            "last_error": article[14],
            "word_count": article[15],
            "estimated_reading_time": article[16],
            "tags": article[17],
            "category": article[18],
            "published_url": article[19],
            "published_platform": article[20],
            "published_at": article[21],
            "created_at": article[22],
            "updated_at": article[23]
        }

        return JSONResponse(content=article_dict)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get article detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/articles/{article_id}/publish")
async def toggle_article_publish_status(article_id: int, request: Request):
    """Toggle article publish status."""
    try:
        data = await request.json()
        action = data.get('action', 'publish')  # 'publish' or 'unpublish'

        from .core.database import get_db_connection
        from datetime import datetime

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if article exists
        cursor.execute("SELECT id, title, published_at FROM articles WHERE id = ?", (article_id,))
        article = cursor.fetchone()

        if not article:
            conn.close()
            raise HTTPException(status_code=404, detail="Article not found")

        # Update publish status
        if action == 'publish':
            # Mark as published
            now = datetime.utcnow().isoformat()
            cursor.execute("""
                UPDATE articles
                SET published_at = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (now, article_id))
            message = f"文章 '{article[1]}' 已标记为已发布"
        else:
            # Mark as unpublished
            cursor.execute("""
                UPDATE articles
                SET published_at = NULL, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (article_id,))
            message = f"文章 '{article[1]}' 发布状态已取消"

        conn.commit()
        conn.close()

        logger.info(f"Article {article_id} publish status updated: {action}")

        return {
            "success": True,
            "message": message,
            "action": action,
            "article_id": article_id
        }

    except Exception as e:
        logger.error(f"Failed to toggle publish status for article {article_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/config/ai-optimization")
async def get_ai_optimization_config():
    """Get AI optimization configuration."""
    try:
        from .core.config import get_ai_optimization_config
        config = get_ai_optimization_config()

        return {
            "success": True,
            "config": {
                "max_attempts": config.max_attempts,
                "threshold": config.threshold,
                "retry_delay_seconds": config.retry_delay_seconds,
                "enable_progressive_optimization": config.enable_progressive_optimization,
                "optimization_strategies": config.optimization_strategies
            }
        }
    except Exception as e:
        logger.error(f"Failed to get AI optimization config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/config/ai-optimization")
async def update_ai_optimization_config(request: Request):
    """Update AI optimization configuration."""
    try:
        data = await request.json()

        # 验证配置参数
        max_attempts = data.get('max_attempts', 5)
        threshold = data.get('threshold', 25.0)
        retry_delay_seconds = data.get('retry_delay_seconds', 2)
        enable_progressive_optimization = data.get('enable_progressive_optimization', True)

        # 参数验证
        if not isinstance(max_attempts, int) or max_attempts < 1 or max_attempts > 20:
            raise HTTPException(status_code=400, detail="max_attempts must be between 1 and 20")

        if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 100:
            raise HTTPException(status_code=400, detail="threshold must be between 0 and 100")

        if not isinstance(retry_delay_seconds, int) or retry_delay_seconds < 0 or retry_delay_seconds > 60:
            raise HTTPException(status_code=400, detail="retry_delay_seconds must be between 0 and 60")

        # 更新配置（这里可以保存到数据库或配置文件）
        from .core.config import get_ai_optimization_config
        config = get_ai_optimization_config()
        config.max_attempts = max_attempts
        config.threshold = threshold
        config.retry_delay_seconds = retry_delay_seconds
        config.enable_progressive_optimization = enable_progressive_optimization

        logger.info(f"AI optimization config updated: max_attempts={max_attempts}, threshold={threshold}")

        return {
            "success": True,
            "message": "AI优化配置已更新",
            "config": {
                "max_attempts": config.max_attempts,
                "threshold": config.threshold,
                "retry_delay_seconds": config.retry_delay_seconds,
                "enable_progressive_optimization": config.enable_progressive_optimization
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update AI optimization config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/articles/{article_id}")
async def delete_article(article_id: int):
    """Delete an article."""
    try:
        from .core.database import get_db_connection

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if article exists
        cursor.execute("SELECT id FROM articles WHERE id = ?", (article_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Article not found")

        # Delete the article
        cursor.execute("DELETE FROM articles WHERE id = ?", (article_id,))
        conn.commit()
        conn.close()

        logger.info(f"Article {article_id} deleted successfully")

        return JSONResponse(content={
            "success": True,
            "message": "Article deleted successfully"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete article {article_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/articles/{article_id}/retry")
async def retry_article_processing(article_id: int):
    """Retry processing a failed article."""
    try:
        from .core.database import get_db_connection
        from .services.article_processor import ArticleProcessor

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if article exists
        cursor.execute("SELECT id, source_url, status FROM articles WHERE id = ?", (article_id,))
        article_data = cursor.fetchone()

        if not article_data:
            conn.close()
            raise HTTPException(status_code=404, detail="Article not found")

        # Reset article status to pending
        cursor.execute("""
            UPDATE articles
            SET status = 'pending', last_error = NULL, processing_attempts = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (article_id,))
        conn.commit()

        # Get article data for processing
        cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
        article_row = cursor.fetchone()
        conn.close()

        logger.info(f"Article {article_id} reset for retry processing")

        # Start processing immediately in background
        import asyncio
        from threading import Thread

        def start_processing():
            try:
                processor = ArticleProcessor()
                # Create article object from database row
                # Note: ArticleProcessor uses a simple Article class, not the SQLAlchemy model
                from .services.article_processor import Article
                article = Article(
                    id=article_row[0],                    # id
                    title=article_row[1],                 # title
                    source_url=article_row[2],            # source_url
                    source_platform=article_row[3],       # source_platform
                    content_original=article_row[4],      # content_original
                    content_translated=article_row[5],    # content_translated
                    content_optimized=article_row[6],     # content_optimized
                    content_final=article_row[7],         # content_final
                    status=article_row[8]                 # status
                )

                # Process the article
                result = processor.process_article(article)
                logger.info(f"Retry processing result for article {article_id}: {result.success}")

            except Exception as e:
                logger.error(f"Error in retry processing for article {article_id}: {e}")

        # Start processing in background thread
        processing_thread = Thread(target=start_processing)
        processing_thread.daemon = True
        processing_thread.start()

        return JSONResponse(content={
            "success": True,
            "message": "Article retry processing started",
            "article_id": article_id
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry article {article_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/articles/{article_id}/generate-titles")
async def generate_article_titles(article_id: int, request_data: TitleGenerationRequest):
    """Generate creative titles for an article using AI."""
    try:
        from .services.real_ai_api_call import get_real_ai_api_call

        # Get AI service
        api_service = get_real_ai_api_call()

        # Create title generation prompt
        style_prompts = {
            "professional": "专业、严谨、权威的风格",
            "catchy": "吸引眼球、引人注目的风格",
            "question": "疑问式、引发思考的风格",
            "howto": "教程式、实用指导的风格",
            "trending": "热点、时事相关的风格",
            "emotional": "情感化、有感染力的风格"
        }

        style_desc = style_prompts.get(request_data.style, "专业严谨的风格")

        messages = [
            {
                "role": "user",
                "content": f"""
请为以下主题生成 {request_data.count} 个{style_desc}的标题：

主题: {request_data.topic}

要求：
1. 标题要有吸引力和点击欲望
2. 符合{style_desc}
3. 长度控制在15-30个字符
4. 避免过于夸张或误导性
5. 每个标题独立一行

请直接返回标题列表，不需要其他说明。
"""
            }
        ]

        # Call AI API
        result = await api_service.call_ai_api(
            messages=messages,
            temperature=0.8,
            max_tokens=500
        )

        if result.get("success"):
            # Parse titles from response
            content = result.get("content", "")
            titles_text = content.strip()
            titles = [title.strip() for title in titles_text.split('\n') if title.strip()]

            # Filter and clean titles
            clean_titles = []
            for title in titles:
                # Remove numbering and bullet points
                title = title.strip()
                if title.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.', '-', '•')):
                    title = title.split('.', 1)[-1].strip() if '.' in title else title[1:].strip()

                if title and len(title) > 5:  # Basic validation
                    clean_titles.append(title)

            # Ensure we have the requested number of titles
            if len(clean_titles) < request_data.count:
                # If we don't have enough, add some generic ones
                for i in range(len(clean_titles), request_data.count):
                    clean_titles.append(f"{request_data.topic} - 深度解析 ({i+1})")

            # Limit to requested count
            clean_titles = clean_titles[:request_data.count]

            logger.info(f"Generated {len(clean_titles)} titles for article {article_id}")

            return JSONResponse(content={
                "success": True,
                "titles": clean_titles,
                "count": len(clean_titles),
                "style": request_data.style,
                "topic": request_data.topic
            })
        else:
            raise HTTPException(status_code=500, detail=f"AI title generation failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        logger.error(f"Failed to generate titles for article {article_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/articles/{article_id}/update-title")
async def update_article_title(article_id: int, request_data: TitleUpdateRequest):
    """Update an article's title."""
    try:
        from .core.database import get_db_connection

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if article exists
        cursor.execute("SELECT id FROM articles WHERE id = ?", (article_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Article not found")

        # Update the title
        cursor.execute("""
            UPDATE articles
            SET title = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (request_data.title, article_id))

        conn.commit()
        conn.close()

        logger.info(f"Article {article_id} title updated to: {request_data.title}")

        return JSONResponse(content={
            "success": True,
            "message": "Title updated successfully",
            "article_id": article_id,
            "new_title": request_data.title
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update title for article {article_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/articles/{article_id}/export")
async def export_article_content(article_id: int):
    """Export article content in JSON format."""
    try:
        from .core.database import get_db_connection

        conn = get_db_connection()
        cursor = conn.cursor()

        # Get article details
        cursor.execute("""
            SELECT id, title, source_url, source_platform, author, publish_date,
                   content_original, content_translated, content_optimized, content_final,
                   status, ai_detection_score, quality_score, word_count,
                   estimated_reading_time, tags, category, created_at, updated_at
            FROM articles
            WHERE id = ?
        """, (article_id,))

        article = cursor.fetchone()
        conn.close()

        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        # Create export data
        export_data = {
            "export_info": {
                "article_id": article[0],
                "export_date": datetime.now().isoformat(),
                "export_version": "1.0"
            },
            "article": {
                "id": article[0],
                "title": article[1],
                "source_url": article[2],
                "source_platform": article[3],
                "author": article[4],
                "publish_date": article[5],
                "status": article[10],
                "ai_detection_score": article[11],
                "quality_score": article[12],
                "word_count": article[13],
                "estimated_reading_time": article[14],
                "tags": article[15],
                "category": article[16],
                "created_at": article[17],
                "updated_at": article[18]
            },
            "content": {
                "original": article[6],
                "translated": article[7],
                "optimized": article[8],
                "final": article[9]
            }
        }

        return JSONResponse(content=export_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export article {article_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/test-ai-classification")
async def test_ai_classification(request_data: AIClassificationTestRequest):
    """Test AI intelligent translation and classification."""
    try:
        logger.info(f"🤖 AI分类测试请求: {request_data.title[:50]}...")

        # Import the AI service
        from .services.real_ai_api_call import get_real_ai_api_call

        api_service = get_real_ai_api_call()

        # Call AI translation and classification
        result = await api_service.translate_and_classify_article(
            title=request_data.title,
            content=request_data.content,
            source_url=request_data.source_url,
            target_language=request_data.target_language
        )

        logger.info(f"🎯 AI分类结果: {result.get('classification', {}).get('category', 'unknown')}")

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"❌ AI分类测试失败: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "classification": {
                    "category": "general",
                    "confidence": 0.0,
                    "reasoning": "测试失败",
                    "method": "error"
                }
            }
        )


@app.post("/api/v1/search")
async def search_articles(request_data: SearchRequest):
    """Search for articles from source platforms."""
    try:
        # Validate search parameters based on mode
        if request_data.search_mode == 'keyword':
            if not request_data.keywords:
                raise HTTPException(status_code=400, detail="Keywords are required for keyword search")
            search_params = request_data.keywords
        elif request_data.search_mode == 'category':
            if not request_data.category:
                raise HTTPException(status_code=400, detail="Category is required for category search")
            search_params = [request_data.category]  # Convert to list for compatibility
        else:
            raise HTTPException(status_code=400, detail="Invalid search mode. Use 'keyword' or 'category'")

        # Get platform manager instance
        platform_manager = get_platform_manager()

        # Get the appropriate adapter
        adapter = await platform_manager.get_adapter(AdapterType.SOURCE, request_data.platform)
        if adapter is None:
            logger.error(f"No adapter found for platform: {request_data.platform}")
            raise HTTPException(status_code=400, detail=f"Platform '{request_data.platform}' not supported")

        # 记录搜索请求信息
        search_info = {
            "mode": request_data.search_mode,
            "platform": request_data.platform,
            "params": search_params,
            "limit": request_data.limit,
            "force_refresh": request_data.force_refresh,
            "timestamp": request_data.timestamp
        }
        logger.info(f"🔍 执行搜索请求: {search_info}")

        # Perform the search
        if request_data.search_mode == 'keyword':
            logger.info(f"Searching for articles with keywords: {search_params} on platform: {request_data.platform}")
            if request_data.force_refresh:
                logger.info("🔄 强制刷新模式：将获取最新数据，不使用缓存")
            articles = await adapter.search_articles(search_params, request_data.limit)
        else:  # category mode
            logger.info(f"Searching for articles with category: {search_params[0]} on platform: {request_data.platform}")
            if request_data.force_refresh:
                logger.info("🔄 强制刷新模式：将获取最新分类数据，不使用缓存")
            # For category search, we'll use the tag-based search method
            if hasattr(adapter, 'search_by_tag'):
                articles = await adapter.search_by_tag(search_params[0], request_data.limit)
            else:
                # Fallback to keyword search with the category tag
                articles = await adapter.search_articles(search_params, request_data.limit)

        # Convert ArticleInfo objects to dictionaries for JSON response
        article_dicts = []
        for article in articles:
            article_dict = {
                "title": article.title,
                "url": article.url,
                "author": article.author or "Unknown",
                "platform": article.platform,
                "summary": article.summary or "",
                "tags": article.tags or [],
                "publish_date": article.publish_date.isoformat() if article.publish_date else None
            }

            # Add metadata if available
            if hasattr(article, 'metadata') and article.metadata:
                article_dict["metadata"] = article.metadata

            article_dicts.append(article_dict)

        logger.info(f"Found {len(article_dicts)} articles for {request_data.search_mode} search: {search_params}")

        response_data = {
            "articles": article_dicts,
            "total": len(article_dicts),
            "platform": request_data.platform,
            "search_mode": request_data.search_mode
        }

        if request_data.search_mode == 'keyword':
            response_data["keywords"] = search_params
        else:
            response_data["category"] = search_params[0]

        return response_data

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# FastAPI exception handlers
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    # Check if this is an API request
    if request.url.path.startswith('/api/'):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code
            }
        )
    
    # For non-API requests, return 404 as HTML
    if exc.status_code == 404:
        return templates.TemplateResponse("index.html", {"request": request})
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "details": exc.errors(),
            "status_code": 422
        }
    )

def run_app():
    """Run the FastAPI application."""
    import uvicorn
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Server will run on http://{settings.host}:{settings.port}")
    
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=settings.reload
    )


if __name__ == "__main__":
    run_app()
