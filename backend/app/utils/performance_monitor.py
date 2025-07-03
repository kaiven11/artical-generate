"""
Performance monitoring and optimization tracking for article processing.
文章处理性能监控和优化跟踪工具
"""

import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import contextmanager

from ..core.performance_config import get_performance_config


@dataclass
class PerformanceMetrics:
    """Performance metrics for a processing step."""
    step_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def finish(self, success: bool = True, error_message: Optional[str] = None):
        """Mark the step as finished."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.success = success
        self.error_message = error_message


@dataclass
class ProcessingSession:
    """Performance tracking for an entire processing session."""
    session_id: str
    article_id: Optional[int] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    total_duration: Optional[float] = None
    steps: List[PerformanceMetrics] = field(default_factory=list)
    success: bool = True
    
    def add_step(self, step_name: str) -> PerformanceMetrics:
        """Add a new processing step."""
        step = PerformanceMetrics(step_name=step_name, start_time=time.time())
        self.steps.append(step)
        return step
    
    def finish(self, success: bool = True):
        """Mark the session as finished."""
        self.end_time = time.time()
        self.total_duration = self.end_time - self.start_time
        self.success = success
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        return {
            "session_id": self.session_id,
            "article_id": self.article_id,
            "total_duration": self.total_duration,
            "success": self.success,
            "steps_count": len(self.steps),
            "successful_steps": sum(1 for step in self.steps if step.success),
            "failed_steps": sum(1 for step in self.steps if not step.success),
            "step_details": [
                {
                    "name": step.step_name,
                    "duration": step.duration,
                    "success": step.success,
                    "error": step.error_message
                }
                for step in self.steps if step.duration is not None
            ]
        }


class PerformanceMonitor:
    """Performance monitoring and optimization tracking."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.perf_config = get_performance_config()
        self.sessions: Dict[str, ProcessingSession] = {}
        self.historical_data: List[Dict[str, Any]] = []
        
    def start_session(self, session_id: str, article_id: Optional[int] = None) -> ProcessingSession:
        """Start a new performance tracking session."""
        session = ProcessingSession(session_id=session_id, article_id=article_id)
        self.sessions[session_id] = session
        self.logger.info(f"🚀 开始性能监控会话: {session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[ProcessingSession]:
        """Get an existing session."""
        return self.sessions.get(session_id)
    
    def finish_session(self, session_id: str, success: bool = True) -> Optional[Dict[str, Any]]:
        """Finish a session and get summary."""
        session = self.sessions.get(session_id)
        if not session:
            return None
            
        session.finish(success)
        summary = session.get_summary()
        
        # Add to historical data
        self.historical_data.append({
            **summary,
            "timestamp": datetime.now().isoformat(),
            "optimization_config": self.perf_config.to_dict()
        })
        
        # Log performance summary
        self._log_performance_summary(summary)
        
        # Clean up
        del self.sessions[session_id]
        
        return summary
    
    @contextmanager
    def track_step(self, session_id: str, step_name: str):
        """Context manager for tracking a processing step."""
        session = self.get_session(session_id)
        if not session:
            yield None
            return
            
        step = session.add_step(step_name)
        self.logger.info(f"⏱️  开始步骤: {step_name}")
        
        try:
            yield step
            step.finish(success=True)
            self.logger.info(f"✅ 完成步骤: {step_name} (用时: {step.duration:.2f}秒)")
        except Exception as e:
            step.finish(success=False, error_message=str(e))
            self.logger.error(f"❌ 步骤失败: {step_name} (用时: {step.duration:.2f}秒) - {e}")
            raise
    
    def _log_performance_summary(self, summary: Dict[str, Any]):
        """Log performance summary."""
        self.logger.info("📊 性能监控总结:")
        self.logger.info(f"   会话ID: {summary['session_id']}")
        self.logger.info(f"   文章ID: {summary.get('article_id', 'N/A')}")
        self.logger.info(f"   总用时: {summary['total_duration']:.2f}秒")
        self.logger.info(f"   成功: {summary['success']}")
        self.logger.info(f"   步骤总数: {summary['steps_count']}")
        self.logger.info(f"   成功步骤: {summary['successful_steps']}")
        self.logger.info(f"   失败步骤: {summary['failed_steps']}")
        
        if summary['step_details']:
            self.logger.info("   步骤详情:")
            for step in summary['step_details']:
                status = "✅" if step['success'] else "❌"
                self.logger.info(f"     {status} {step['name']}: {step['duration']:.2f}秒")
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Get optimization effectiveness report."""
        if not self.historical_data:
            return {"message": "暂无历史数据"}
        
        recent_sessions = self.historical_data[-10:]  # 最近10次会话
        
        # 计算平均处理时间
        avg_duration = sum(s['total_duration'] for s in recent_sessions if s['total_duration']) / len(recent_sessions)
        
        # 计算成功率
        success_rate = sum(1 for s in recent_sessions if s['success']) / len(recent_sessions) * 100
        
        # 分析步骤性能
        step_performance = {}
        for session in recent_sessions:
            for step in session.get('step_details', []):
                step_name = step['name']
                if step_name not in step_performance:
                    step_performance[step_name] = []
                if step['duration']:
                    step_performance[step_name].append(step['duration'])
        
        step_averages = {
            name: sum(durations) / len(durations)
            for name, durations in step_performance.items()
            if durations
        }
        
        return {
            "optimization_summary": self.perf_config.get_optimization_summary(),
            "recent_performance": {
                "sessions_analyzed": len(recent_sessions),
                "average_duration": f"{avg_duration:.2f}秒",
                "success_rate": f"{success_rate:.1f}%",
                "step_averages": {
                    name: f"{duration:.2f}秒"
                    for name, duration in step_averages.items()
                }
            },
            "performance_config": self.perf_config.to_dict(),
            "recommendations": self._get_performance_recommendations(step_averages)
        }
    
    def _get_performance_recommendations(self, step_averages: Dict[str, float]) -> List[str]:
        """Get performance optimization recommendations."""
        recommendations = []
        
        # 检查AI检测步骤
        if 'ai_detection' in step_averages:
            ai_time = step_averages['ai_detection']
            if ai_time > 20:
                recommendations.append("AI检测时间较长，建议检查网络连接或考虑调整检测超时设置")
            elif ai_time < 10:
                recommendations.append("AI检测时间很短，性能优化效果良好")
        
        # 检查内容提取步骤
        if 'content_extraction' in step_averages:
            extract_time = step_averages['content_extraction']
            if extract_time > 15:
                recommendations.append("内容提取时间较长，建议检查网络连接或优化页面加载等待时间")
            elif extract_time < 8:
                recommendations.append("内容提取时间很短，性能优化效果良好")
        
        # 检查翻译步骤
        if 'translation' in step_averages:
            translate_time = step_averages['translation']
            if translate_time > 30:
                recommendations.append("翻译时间较长，建议检查API响应时间或考虑使用更快的模型")
        
        if not recommendations:
            recommendations.append("当前性能表现良好，优化设置有效")
        
        return recommendations


# 全局性能监控实例
performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """获取性能监控实例"""
    return performance_monitor
