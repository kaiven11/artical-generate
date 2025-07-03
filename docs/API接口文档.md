# 今日头条AI赛道文章搬运工具 - API接口文档

## 1. 接口概述

### 1.1 基础信息
- **Base URL**: `http://127.0.0.1:8007/api/v1` (当前运行地址)
- **协议**: HTTP/HTTPS
- **数据格式**: JSON
- **字符编码**: UTF-8
- **认证方式**: Bearer Token (暂未启用)

### 1.1.1 当前可用接口 (2025-06-27)
- ✅ `POST /articles/create` - 文章创建
- ✅ `POST /articles/{id}/process` - 文章处理
- ✅ `GET /tasks/{task_id}/status` - 任务状态查询
- ✅ `POST /search` - 文章搜索
- ✅ `GET /status` - 系统状态
- ✅ `GET /articles` - 文章列表

### 1.2 通用响应格式

#### 成功响应
```json
{
    "success": true,
    "data": {},
    "message": "操作成功",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

#### 错误响应
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "参数验证失败",
        "details": {}
    },
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### 1.3 状态码说明
- `200` - 请求成功
- `201` - 创建成功
- `400` - 请求参数错误
- `401` - 未授权
- `403` - 禁止访问
- `404` - 资源不存在
- `429` - 请求过于频繁
- `500` - 服务器内部错误

## 2. 文章获取接口

### 2.1 搜索Medium文章

**接口地址**: `POST /articles/search`

**说明**: 通过网页自动化搜索Medium平台的AI相关文章

**请求参数**:
```json
{
    "keywords": ["AI", "machine learning", "deep learning"],
    "limit": 20,
    "browser_config": {
        "fingerprint_seed": "random_seed_123",
        "proxy": "http://proxy:port"
    }
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "articles": [
            {
                "title": "The Future of AI in Healthcare",
                "url": "https://medium.com/@author/article-url",
                "author": "John Doe",
                "publish_date": "2024-01-10",
                "reading_time": "5 min read",
                "preview": "Article preview text...",
                "tags": ["AI", "Healthcare", "Technology"]
            }
        ],
        "total_found": 150,
        "search_keywords": ["AI", "machine learning"],
        "search_method": "web_automation"
    }
}
```

### 2.2 抓取文章内容

**接口地址**: `POST /articles/extract`

**说明**: 通过Freedium.cfd网页操作提取Medium文章完整内容

**请求参数**:
```json
{
    "url": "https://medium.com/@author/article-url",
    "use_freedium": true,
    "browser_config": {
        "fingerprint_seed": "random_seed_456",
        "proxy": "http://proxy:port"
    }
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "task_id": "extract_abc123",
        "status": "browser_starting",
        "estimated_completion_time": "2024-01-15T10:32:00Z",
        "message": "正在启动浏览器进行内容提取"
    }
}
```

### 2.3 获取提取结果

**接口地址**: `GET /articles/extract/{task_id}`

**响应示例**:
```json
{
    "success": true,
    "data": {
        "task_id": "extract_abc123",
        "status": "completed",
        "article": {
            "title": "The Future of AI in Healthcare",
            "content": "Full article content...",
            "author": "John Doe",
            "publish_date": "2024-01-10T15:30:00Z",
            "tags": ["AI", "Healthcare", "Technology"],
            "reading_time": 8,
            "source_url": "https://medium.com/@author/article-url",
            "extracted_via": "freedium",
            "word_count": 2500
        },
        "extraction_method": "web_automation",
        "browser_session_id": "session_abc123",
        "completed_at": "2024-01-15T10:31:45Z"
    }
}
```

## 3. 文章管理接口

### 3.1 获取文章列表

**接口地址**: `GET /articles`

**请求参数**:
```json
{
    "page": 1,
    "page_size": 20,
    "status": "all",
    "source_platform": "",
    "keyword": "",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "items": [
            {
                "id": 1,
                "title": "AI的未来发展趋势分析",
                "original_url": "https://medium.com/example",
                "source_platform": "medium",
                "status": "published",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T12:30:00Z",
                "metadata": {
                    "word_count": 2500,
                    "estimated_reading_time": 10
                }
            }
        ],
        "total": 100,
        "page": 1,
        "page_size": 20,
        "total_pages": 5
    }
}
```

### 3.2 创建文章

**接口地址**: `POST /articles`

**请求参数**:
```json
{
    "url": "https://medium.com/example-article",
    "source_platform": "medium",
    "auto_process": true,
    "priority": "normal",
    "extract_immediately": true
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "id": 123,
        "title": "新创建的文章标题",
        "status": "extracting",
        "extract_task_id": "extract_abc123",
        "process_task_id": "task_def456"
    }
}
```

### 3.3 获取文章详情

**接口地址**: `GET /articles/{article_id}`

**响应示例**:
```json
{
    "success": true,
    "data": {
        "id": 1,
        "title": "AI的未来发展趋势分析",
        "original_url": "https://medium.com/example",
        "source_platform": "medium",
        "status": "published",
        "content": {
            "original": "原文内容...",
            "translated": "翻译内容...",
            "optimized": "优化内容...",
            "final": "最终内容..."
        },
        "detection_results": [
            {
                "type": "originality",
                "platform": "zhuque",
                "score": 85.5,
                "passed": true,
                "detected_at": "2024-01-15T11:00:00Z"
            }
        ],
        "publish_results": [
            {
                "platform": "toutiao",
                "status": "published",
                "published_url": "https://toutiao.com/article/123",
                "published_at": "2024-01-15T12:00:00Z"
            }
        ]
    }
}
```

### 3.4 更新文章

**接口地址**: `PUT /articles/{article_id}`

**请求参数**:
```json
{
    "title": "更新后的标题",
    "content_final": "更新后的最终内容",
    "status": "optimized"
}
```

### 3.5 删除文章

**接口地址**: `DELETE /articles/{article_id}`

### 3.6 批量操作文章

**接口地址**: `POST /articles/batch`

**请求参数**:
```json
{
    "article_ids": [1, 2, 3, 4, 5],
    "operation": "process",
    "parameters": {
        "auto_publish": false,
        "priority": "high"
    }
}
```

## 4. 平台管理接口

### 4.1 获取平台适配器列表

**接口地址**: `GET /platforms/adapters`

**请求参数**:
```json
{
    "adapter_type": "source", // source, ai, publish, detection, 或 null(全部)
    "enabled_only": true
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "source": [
            {
                "id": 1,
                "name": "medium",
                "display_name": "Medium",
                "version": "1.0.0",
                "is_enabled": true,
                "is_builtin": true,
                "features": ["search", "extract", "paywall_bypass"],
                "config_status": "configured"
            }
        ],
        "ai": [
            {
                "id": 2,
                "name": "openai",
                "display_name": "OpenAI",
                "version": "1.2.0",
                "is_enabled": true,
                "is_builtin": true,
                "features": ["translate", "optimize", "chat"],
                "config_status": "configured"
            }
        ]
    }
}
```

### 4.2 安装平台插件

**接口地址**: `POST /platforms/plugins/install`

**请求参数**:
```json
{
    "plugin_source": "file", // file, url, marketplace
    "plugin_path": "/path/to/plugin.zip",
    "auto_enable": true
}
```

### 4.3 配置平台适配器

**接口地址**: `PUT /platforms/adapters/{adapter_id}/config`

**请求参数**:
```json
{
    "config": {
        "api_key": "your-api-key",
        "api_url": "https://api.example.com",
        "timeout": 30,
        "max_retries": 3
    }
}
```

### 4.4 测试平台连接

**接口地址**: `POST /platforms/adapters/{adapter_id}/test`

**响应示例**:
```json
{
    "success": true,
    "data": {
        "connection_status": "success",
        "response_time_ms": 250,
        "test_message": "连接测试成功",
        "platform_info": {
            "version": "v1.0",
            "features": ["search", "extract"]
        }
    }
}
```

### 4.5 启用/禁用平台适配器

**接口地址**: `PUT /platforms/adapters/{adapter_id}/status`

**请求参数**:
```json
{
    "is_enabled": true
}
```

### 4.6 获取平台使用统计

**接口地址**: `GET /platforms/adapters/usage-stats`

**请求参数**:
```json
{
    "time_range": "today",
    "adapter_type": "ai",
    "adapter_id": null
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "summary": {
            "total_requests": 500,
            "total_cost": 25.50,
            "average_response_time": 1.8,
            "success_rate": 97.2
        },
        "by_adapter": [
            {
                "adapter_name": "openai",
                "requests": 200,
                "cost": 15.00,
                "success_rate": 98.5
            }
        ]
    }
}
```

### 4.2 创建API提供商

**接口地址**: `POST /api-providers`

**请求参数**:
```json
{
    "name": "claude",
    "display_name": "Anthropic Claude",
    "api_key": "sk-ant-api03-...",
    "api_url": "https://api.anthropic.com/v1",
    "weight": 30,
    "max_requests_per_minute": 60,
    "max_requests_per_hour": 1000
}
```

### 4.3 更新API提供商

**接口地址**: `PUT /api-providers/{provider_id}`

### 4.4 测试API连接

**接口地址**: `POST /api-providers/{provider_id}/test`

**响应示例**:
```json
{
    "success": true,
    "data": {
        "connection_status": "success",
        "response_time_ms": 250,
        "test_message": "连接测试成功"
    }
}
```

### 4.5 获取API使用统计

**接口地址**: `GET /api-providers/usage-stats`

**请求参数**:
```json
{
    "time_range": "today",
    "provider_id": null,
    "group_by": "provider"
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "summary": {
            "total_requests": 500,
            "total_cost": 25.50,
            "average_response_time": 1.8,
            "success_rate": 97.2
        },
        "by_provider": [
            {
                "provider_name": "openai",
                "requests": 200,
                "cost": 15.00,
                "success_rate": 98.5
            }
        ],
        "timeline": [
            {
                "hour": "2024-01-15T10:00:00Z",
                "requests": 25,
                "cost": 1.25
            }
        ]
    }
}
```

## 5. 翻译服务接口

### 5.1 翻译文章

**接口地址**: `POST /translation/translate`

**请求参数**:
```json
{
    "article_id": 123,
    "prompt_template_id": 1,
    "provider_preference": ["openai", "claude"],
    "parameters": {
        "temperature": 0.7,
        "max_tokens": 4000
    }
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "task_id": "translate_abc123",
        "estimated_completion_time": "2024-01-15T10:35:00Z",
        "status": "processing"
    }
}
```

### 5.2 优化内容

**接口地址**: `POST /translation/optimize`

**请求参数**:
```json
{
    "article_id": 123,
    "content": "需要优化的内容...",
    "optimization_type": "ai_detection_bypass",
    "prompt_template_id": 2
}
```

### 5.3 获取翻译任务状态

**接口地址**: `GET /translation/tasks/{task_id}`

**响应示例**:
```json
{
    "success": true,
    "data": {
        "task_id": "translate_abc123",
        "status": "completed",
        "progress": 100,
        "result": {
            "translated_content": "翻译后的内容...",
            "word_count": 2500,
            "tokens_used": 3200,
            "cost": 0.096,
            "provider_used": "openai",
            "model_used": "gpt-4"
        },
        "started_at": "2024-01-15T10:30:00Z",
        "completed_at": "2024-01-15T10:34:30Z"
    }
}
```

## 6. 检测服务接口

### 6.1 执行检测

**接口地址**: `POST /detection/detect`

**说明**: 启动网页自动化检测任务，通过浏览器操作朱雀检测平台

**请求参数**:
```json
{
    "article_id": 123,
    "detection_types": ["originality", "ai_generated"],
    "providers": ["zhuque"],
    "content": "要检测的内容...",
    "browser_config": {
        "fingerprint_seed": "random_seed_123",
        "proxy": "http://proxy:port"
    }
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "task_id": "detect_xyz789",
        "status": "browser_starting",
        "estimated_completion_time": "2024-01-15T10:35:00Z",
        "message": "正在启动浏览器进行网页检测"
    }
}
```

### 6.2 获取检测结果

**接口地址**: `GET /detection/results/{article_id}`

**响应示例**:
```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "detection_type": "originality",
            "platform": "zhuque",
            "score": 85.5,
            "is_passed": true,
            "threshold": 80.0,
            "details": {
                "similar_content_found": false,
                "similarity_sources": [],
                "browser_session_id": "session_abc123",
                "detection_method": "web_automation"
            },
            "detected_at": "2024-01-15T10:31:45Z"
        },
        {
            "id": 2,
            "detection_type": "ai_generated",
            "platform": "zhuque",
            "score": 72.3,
            "is_passed": true,
            "threshold": 70.0,
            "details": {
                "ai_probability": 0.277,
                "confidence": 0.85,
                "browser_session_id": "session_abc123",
                "detection_method": "web_automation"
            },
            "detected_at": "2024-01-15T10:31:50Z"
        }
    ]
}
```

### 6.3 批量检测

**接口地址**: `POST /detection/batch-detect`

**请求参数**:
```json
{
    "article_ids": [1, 2, 3, 4, 5],
    "detection_types": ["originality", "ai_generated"],
    "priority": "normal"
}
```

## 7. 发布服务接口

### 7.1 创建发布任务

**接口地址**: `POST /publish/tasks`

**说明**: 创建网页自动化发布任务，通过浏览器操作今日头条创作者平台

**请求参数**:
```json
{
    "article_id": 123,
    "platform": "toutiao",
    "scheduled_at": "2024-01-15T18:00:00Z",
    "config": {
        "title": "自定义标题",
        "category": "科技",
        "tags": ["AI", "机器学习", "技术"],
        "allow_comments": true,
        "allow_repost": true,
        "cover_image_url": "https://example.com/cover.jpg"
    },
    "browser_config": {
        "fingerprint_seed": "random_seed_456",
        "proxy": "http://proxy:port",
        "login_required": true
    }
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "task_id": "publish_def456",
        "status": "browser_starting",
        "scheduled_at": "2024-01-15T18:00:00Z",
        "estimated_duration": 600,
        "message": "正在启动浏览器进行网页发布"
    }
}
```

### 6.2 获取发布任务状态

**接口地址**: `GET /publish/tasks/{task_id}`

**响应示例**:
```json
{
    "success": true,
    "data": {
        "task_id": "publish_def456",
        "article_id": 123,
        "platform": "toutiao",
        "status": "published",
        "progress": 100,
        "result": {
            "published_url": "https://toutiao.com/article/123456",
            "article_id_on_platform": "123456",
            "published_at": "2024-01-15T18:02:30Z",
            "browser_session_id": "session_def456",
            "publish_method": "web_automation"
        },
        "error_message": null,
        "retry_count": 0,
        "created_at": "2024-01-15T17:55:00Z",
        "started_at": "2024-01-15T18:00:00Z",
        "completed_at": "2024-01-15T18:02:30Z"
    }
}
```

### 6.3 取消发布任务

**接口地址**: `DELETE /publish/tasks/{task_id}`

### 6.4 重试发布任务

**接口地址**: `POST /publish/tasks/{task_id}/retry`

### 6.5 获取发布历史

**接口地址**: `GET /publish/history`

**请求参数**:
```json
{
    "page": 1,
    "page_size": 20,
    "platform": "all",
    "status": "all",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
}
```

## 7. 提示词管理接口

### 7.1 获取提示词列表

**接口地址**: `GET /prompts`

**响应示例**:
```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "name": "技术文章翻译模板v2.0",
            "type": "translation",
            "content": "你是一位专业的AI技术文章翻译专家...",
            "variables": ["original_text", "article_type"],
            "success_rate": 92.5,
            "usage_count": 150,
            "is_enabled": true,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-10T10:00:00Z"
        }
    ]
}
```

### 7.2 创建提示词

**接口地址**: `POST /prompts`

**请求参数**:
```json
{
    "name": "新的翻译模板",
    "type": "translation",
    "content": "提示词内容...",
    "variables": ["original_text", "target_style"],
    "is_enabled": true
}
```

### 7.3 更新提示词

**接口地址**: `PUT /prompts/{prompt_id}`

### 7.4 测试提示词

**接口地址**: `POST /prompts/{prompt_id}/test`

**请求参数**:
```json
{
    "test_content": "测试内容...",
    "variables": {
        "original_text": "测试文本",
        "target_style": "技术文章"
    }
}
```

## 8. 任务管理接口

### 8.1 获取任务队列状态

**接口地址**: `GET /tasks/queue-status`

**响应示例**:
```json
{
    "success": true,
    "data": {
        "queue_size": 15,
        "running_tasks": 3,
        "completed_today": 25,
        "failed_today": 2,
        "average_processing_time": 180,
        "current_tasks": [
            {
                "task_id": "task_123",
                "type": "translation",
                "article_id": 456,
                "status": "running",
                "progress": 65,
                "started_at": "2024-01-15T10:30:00Z",
                "estimated_completion": "2024-01-15T10:35:00Z"
            }
        ]
    }
}
```

### 8.2 获取任务详情

**接口地址**: `GET /tasks/{task_id}`

### 8.3 取消任务

**接口地址**: `DELETE /tasks/{task_id}`

### 8.4 重启任务调度器

**接口地址**: `POST /tasks/scheduler/restart`

## 9. 系统管理接口

### 9.1 获取系统状态

**接口地址**: `GET /system/status`

**响应示例**:
```json
{
    "success": true,
    "data": {
        "system": {
            "cpu_usage": 25.5,
            "memory_usage": 45.2,
            "disk_usage": 60.8,
            "uptime_seconds": 86400
        },
        "application": {
            "version": "1.0.0",
            "environment": "production",
            "database_status": "connected",
            "cache_status": "active"
        },
        "services": {
            "translation_service": "running",
            "detection_service": "running",
            "publish_service": "running",
            "browser_manager": "running"
        }
    }
}
```

### 9.2 获取配置信息

**接口地址**: `GET /system/config`

### 9.3 更新配置

**接口地址**: `PUT /system/config`

**请求参数**:
```json
{
    "section": "browser",
    "config": {
        "chrome_path": "/path/to/chrome",
        "headless_mode": false,
        "fingerprint_randomization": true
    }
}
```

### 9.4 获取日志

**接口地址**: `GET /system/logs`

**请求参数**:
```json
{
    "level": "error",
    "start_time": "2024-01-15T00:00:00Z",
    "end_time": "2024-01-15T23:59:59Z",
    "limit": 100
}
```

### 9.5 清理缓存

**接口地址**: `POST /system/cache/clear`

### 9.6 备份数据

**接口地址**: `POST /system/backup`

**响应示例**:
```json
{
    "success": true,
    "data": {
        "backup_id": "backup_20240115_103000",
        "backup_path": "/backups/backup_20240115_103000.zip",
        "backup_size": 1024000,
        "created_at": "2024-01-15T10:30:00Z"
    }
}
```

## 10. WebSocket实时通信

### 10.1 连接地址
`ws://localhost:8000/ws`

### 10.2 消息格式

#### 客户端订阅
```json
{
    "type": "subscribe",
    "channels": ["task_updates", "system_alerts", "article_status"]
}
```

#### 服务端推送 - 任务更新
```json
{
    "type": "task_update",
    "data": {
        "task_id": "task_123",
        "status": "completed",
        "progress": 100,
        "result": {}
    },
    "timestamp": "2024-01-15T10:30:00Z"
}
```

#### 服务端推送 - 系统告警
```json
{
    "type": "system_alert",
    "data": {
        "level": "warning",
        "message": "CPU使用率过高",
        "details": {
            "cpu_usage": 85.5
        }
    },
    "timestamp": "2024-01-15T10:30:00Z"
}
```

#### 服务端推送 - 文章状态变更
```json
{
    "type": "article_status_change",
    "data": {
        "article_id": 123,
        "old_status": "translating",
        "new_status": "translated",
        "message": "文章翻译完成"
    },
    "timestamp": "2024-01-15T10:30:00Z"
}
```

## 11. 错误码说明

### 11.1 通用错误码
- `VALIDATION_ERROR` - 参数验证失败
- `AUTHENTICATION_ERROR` - 认证失败
- `AUTHORIZATION_ERROR` - 权限不足
- `RESOURCE_NOT_FOUND` - 资源不存在
- `RATE_LIMIT_EXCEEDED` - 请求频率超限
- `INTERNAL_SERVER_ERROR` - 服务器内部错误

### 11.2 业务错误码
- `ARTICLE_NOT_FOUND` - 文章不存在
- `ARTICLE_PROCESSING_FAILED` - 文章处理失败
- `TRANSLATION_FAILED` - 翻译失败
- `DETECTION_FAILED` - 检测失败
- `PUBLISH_FAILED` - 发布失败
- `API_PROVIDER_UNAVAILABLE` - API服务商不可用
- `BROWSER_SESSION_EXPIRED` - 浏览器会话过期
- `TASK_QUEUE_FULL` - 任务队列已满

### 11.3 错误响应示例
```json
{
    "success": false,
    "error": {
        "code": "TRANSLATION_FAILED",
        "message": "翻译服务暂时不可用",
        "details": {
            "provider": "openai",
            "error_type": "rate_limit",
            "retry_after": 60
        }
    },
    "timestamp": "2024-01-15T10:30:00Z"
}
```
