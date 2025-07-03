"""
Performance monitoring and optimization API endpoints.
性能监控和优化API端点
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..core.performance_config import get_performance_config, update_performance_config, get_optimization_summary
from ..utils.performance_monitor import get_performance_monitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/performance", tags=["performance"])


class PerformanceConfigUpdate(BaseModel):
    """Performance configuration update request."""
    ai_detection_timeout: Optional[int] = Field(None, ge=5, le=60, description="AI检测超时时间（秒）")
    ai_detection_max_wait: Optional[int] = Field(None, ge=5, le=60, description="AI检测最大等待时间（秒）")
    ai_detection_check_interval: Optional[int] = Field(None, ge=1, le=5, description="检测结果轮询间隔（秒）")
    browser_startup_wait: Optional[float] = Field(None, ge=0.5, le=5.0, description="浏览器启动等待时间（秒）")
    page_load_wait: Optional[float] = Field(None, ge=1.0, le=10.0, description="页面加载等待时间（秒）")
    content_load_wait: Optional[float] = Field(None, ge=1.0, le=10.0, description="内容加载等待时间（秒）")
    input_wait: Optional[float] = Field(None, ge=0.1, le=2.0, description="输入操作等待时间（秒）")
    click_wait: Optional[float] = Field(None, ge=0.1, le=3.0, description="点击操作等待时间（秒）")
    text_input_wait: Optional[float] = Field(None, ge=0.5, le=5.0, description="文本输入完成等待时间（秒）")
    element_find_timeout: Optional[int] = Field(None, ge=1, le=15, description="元素查找超时时间（秒）")
    button_find_timeout: Optional[int] = Field(None, ge=1, le=10, description="按钮查找超时时间（秒）")
    http_timeout: Optional[int] = Field(None, ge=5, le=60, description="HTTP请求超时时间（秒）")
    api_timeout: Optional[int] = Field(None, ge=5, le=120, description="API调用超时时间（秒）")
    retry_interval: Optional[int] = Field(None, ge=5, le=60, description="重试间隔时间（秒）")
    js_execution_wait: Optional[float] = Field(None, ge=0.1, le=3.0, description="JavaScript执行等待时间（秒）")
    content_extraction_timeout: Optional[int] = Field(None, ge=5, le=60, description="内容提取超时时间（秒）")


@router.get("/config")
async def get_performance_config_api() -> Dict[str, Any]:
    """
    获取当前性能配置
    Get current performance configuration
    """
    try:
        config = get_performance_config()
        return {
            "success": True,
            "data": config.to_dict(),
            "message": "性能配置获取成功"
        }
    except Exception as e:
        logger.error(f"获取性能配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取性能配置失败: {str(e)}")


@router.put("/config")
async def update_performance_config_api(config_update: PerformanceConfigUpdate) -> Dict[str, Any]:
    """
    更新性能配置
    Update performance configuration
    """
    try:
        # 只更新提供的字段
        update_data = {k: v for k, v in config_update.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="没有提供要更新的配置项")
        
        # 更新配置
        update_performance_config(**update_data)
        
        # 获取更新后的配置
        updated_config = get_performance_config()
        
        logger.info(f"性能配置已更新: {list(update_data.keys())}")
        
        return {
            "success": True,
            "data": updated_config.to_dict(),
            "updated_fields": list(update_data.keys()),
            "message": f"成功更新 {len(update_data)} 个配置项"
        }
    except Exception as e:
        logger.error(f"更新性能配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新性能配置失败: {str(e)}")


@router.get("/optimization-summary")
async def get_optimization_summary_api() -> Dict[str, Any]:
    """
    获取优化总结
    Get optimization summary
    """
    try:
        summary = get_optimization_summary()
        return {
            "success": True,
            "data": summary,
            "message": "优化总结获取成功"
        }
    except Exception as e:
        logger.error(f"获取优化总结失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取优化总结失败: {str(e)}")


@router.get("/monitor/report")
async def get_performance_report() -> Dict[str, Any]:
    """
    获取性能监控报告
    Get performance monitoring report
    """
    try:
        monitor = get_performance_monitor()
        report = monitor.get_optimization_report()
        
        return {
            "success": True,
            "data": report,
            "message": "性能监控报告获取成功"
        }
    except Exception as e:
        logger.error(f"获取性能监控报告失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取性能监控报告失败: {str(e)}")


@router.get("/monitor/sessions")
async def get_active_sessions() -> Dict[str, Any]:
    """
    获取活跃的监控会话
    Get active monitoring sessions
    """
    try:
        monitor = get_performance_monitor()
        active_sessions = {
            session_id: {
                "session_id": session.session_id,
                "article_id": session.article_id,
                "start_time": session.start_time,
                "steps_count": len(session.steps),
                "current_step": session.steps[-1].step_name if session.steps else None
            }
            for session_id, session in monitor.sessions.items()
        }
        
        return {
            "success": True,
            "data": {
                "active_sessions": active_sessions,
                "total_active": len(active_sessions)
            },
            "message": f"当前有 {len(active_sessions)} 个活跃会话"
        }
    except Exception as e:
        logger.error(f"获取活跃会话失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取活跃会话失败: {str(e)}")


@router.post("/reset-config")
async def reset_performance_config_api() -> Dict[str, Any]:
    """
    重置性能配置为默认值
    Reset performance configuration to defaults
    """
    try:
        from ..core.performance_config import reset_performance_config
        reset_performance_config()
        
        config = get_performance_config()
        
        logger.info("性能配置已重置为默认值")
        
        return {
            "success": True,
            "data": config.to_dict(),
            "message": "性能配置已重置为默认值"
        }
    except Exception as e:
        logger.error(f"重置性能配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"重置性能配置失败: {str(e)}")


@router.get("/presets")
async def get_performance_presets() -> Dict[str, Any]:
    """
    获取性能预设配置
    Get performance preset configurations
    """
    presets = {
        "ultra_fast": {
            "name": "极速模式",
            "description": "最快的处理速度，可能影响稳定性",
            "config": {
                "ai_detection_timeout": 10,
                "ai_detection_max_wait": 10,
                "ai_detection_check_interval": 1,
                "browser_startup_wait": 0.5,
                "page_load_wait": 2.0,
                "content_load_wait": 1.0,
                "input_wait": 0.2,
                "click_wait": 0.5,
                "text_input_wait": 0.5,
                "element_find_timeout": 3,
                "button_find_timeout": 1,
                "http_timeout": 10,
                "api_timeout": 10,
                "retry_interval": 5,
                "js_execution_wait": 0.2,
                "content_extraction_timeout": 10
            }
        },
        "balanced": {
            "name": "平衡模式",
            "description": "速度和稳定性的平衡（推荐）",
            "config": {
                "ai_detection_timeout": 15,
                "ai_detection_max_wait": 15,
                "ai_detection_check_interval": 1,
                "browser_startup_wait": 1.0,
                "page_load_wait": 3.0,
                "content_load_wait": 2.0,
                "input_wait": 0.5,
                "click_wait": 1.0,
                "text_input_wait": 1.0,
                "element_find_timeout": 5,
                "button_find_timeout": 1,
                "http_timeout": 15,
                "api_timeout": 15,
                "retry_interval": 10,
                "js_execution_wait": 0.5,
                "content_extraction_timeout": 15
            }
        },
        "stable": {
            "name": "稳定模式",
            "description": "最稳定的处理，速度较慢",
            "config": {
                "ai_detection_timeout": 30,
                "ai_detection_max_wait": 25,
                "ai_detection_check_interval": 2,
                "browser_startup_wait": 2.0,
                "page_load_wait": 5.0,
                "content_load_wait": 3.0,
                "input_wait": 1.0,
                "click_wait": 2.0,
                "text_input_wait": 2.0,
                "element_find_timeout": 10,
                "button_find_timeout": 3,
                "http_timeout": 30,
                "api_timeout": 30,
                "retry_interval": 20,
                "js_execution_wait": 1.0,
                "content_extraction_timeout": 30
            }
        }
    }
    
    return {
        "success": True,
        "data": presets,
        "message": "性能预设配置获取成功"
    }


@router.post("/apply-preset/{preset_name}")
async def apply_performance_preset(preset_name: str) -> Dict[str, Any]:
    """
    应用性能预设配置
    Apply performance preset configuration
    """
    try:
        presets_response = await get_performance_presets()
        presets = presets_response["data"]
        
        if preset_name not in presets:
            raise HTTPException(status_code=404, detail=f"预设配置 '{preset_name}' 不存在")
        
        preset = presets[preset_name]
        config_data = preset["config"]
        
        # 应用预设配置
        update_performance_config(**config_data)
        
        # 获取更新后的配置
        updated_config = get_performance_config()
        
        logger.info(f"已应用性能预设: {preset['name']}")
        
        return {
            "success": True,
            "data": {
                "applied_preset": preset,
                "current_config": updated_config.to_dict()
            },
            "message": f"成功应用预设配置: {preset['name']}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"应用性能预设失败: {e}")
        raise HTTPException(status_code=500, detail=f"应用性能预设失败: {str(e)}")
