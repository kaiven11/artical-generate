"""
Dashboard service for real-time statistics and monitoring.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from ..core.database import get_db_connection

logger = logging.getLogger(__name__)

@dataclass
class TaskInfo:
    """Task information for monitoring."""
    task_id: str
    article_id: int
    title: str
    status: str
    progress: float
    current_step: str
    started_at: datetime
    estimated_completion: Optional[datetime] = None

@dataclass
class ActivityInfo:
    """Recent activity information."""
    id: int
    type: str  # 'article_processed', 'task_completed', 'task_failed', etc.
    title: str
    description: str
    timestamp: datetime
    status: str
    metadata: Dict[str, Any]

class DashboardService:
    """Service for dashboard data and real-time monitoring."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._active_tasks = {}
        self._recent_activities = []
        
    async def get_real_time_statistics(self) -> Dict[str, Any]:
        """Get real-time dashboard statistics."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get today's date
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Total articles
            cursor.execute("SELECT COUNT(*) FROM articles")
            total_articles = cursor.fetchone()[0]
            
            # Processed today
            cursor.execute("""
                SELECT COUNT(*) FROM articles 
                WHERE DATE(created_at) = ? AND status IN ('completed', 'published')
            """, (today,))
            processed_today = cursor.fetchone()[0]
            
            # Success rate (last 100 articles)
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'completed' OR status = 'published' THEN 1 ELSE 0 END) as successful
                FROM (
                    SELECT status FROM articles 
                    ORDER BY created_at DESC 
                    LIMIT 100
                )
            """)
            result = cursor.fetchone()
            total_recent = result[0] if result[0] > 0 else 1
            successful_recent = result[1] if result[1] else 0
            success_rate = (successful_recent / total_recent) * 100
            
            # Active tasks
            cursor.execute("""
                SELECT COUNT(*) FROM tasks 
                WHERE status IN ('pending', 'running')
            """)
            active_tasks = cursor.fetchone()[0]
            
            # AI detection rate from actual detection results
            cursor.execute("""
                SELECT AVG(score) FROM detection_results
                WHERE detection_type = 'ai_detection'
                AND detected_at >= datetime('now', '-7 days')
            """)
            result = cursor.fetchone()
            ai_detection_rate = result[0] if result[0] else 0.0
            
            # Average processing time
            cursor.execute("""
                SELECT AVG(
                    CASE 
                        WHEN completed_at IS NOT NULL AND created_at IS NOT NULL 
                        THEN (julianday(completed_at) - julianday(created_at)) * 24 * 60 
                        ELSE NULL 
                    END
                ) as avg_minutes
                FROM tasks 
                WHERE status = 'completed' 
                AND created_at >= datetime('now', '-7 days')
            """)
            result = cursor.fetchone()
            avg_processing_time = result[0] if result[0] else 0
            
            conn.close()
            
            return {
                "total_articles": total_articles,
                "processed_today": processed_today,
                "success_rate": round(success_rate, 1),
                "active_tasks": active_tasks,
                "ai_detection_rate": ai_detection_rate,
                "avg_processing_time_minutes": round(avg_processing_time, 1) if avg_processing_time else 0,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get real-time statistics: {e}")
            # Return default values on error
            return {
                "total_articles": 0,
                "processed_today": 0,
                "success_rate": 0.0,
                "active_tasks": 0,
                "ai_detection_rate": 0.0,
                "avg_processing_time_minutes": 0.0,
                "last_updated": datetime.now().isoformat()
            }
    
    async def get_active_tasks(self) -> List[TaskInfo]:
        """Get currently active tasks for monitoring."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    t.task_id,
                    t.article_id,
                    COALESCE(a.title, 'Unknown Article') as title,
                    t.status,
                    COALESCE(t.progress, 0) as progress,
                    COALESCE(t.current_step, 'pending') as current_step,
                    t.created_at
                FROM tasks t
                LEFT JOIN articles a ON t.article_id = a.id
                WHERE t.status IN ('pending', 'running')
                ORDER BY t.created_at DESC
                LIMIT 10
            """)
            
            tasks = []
            for row in cursor.fetchall():
                task_info = TaskInfo(
                    task_id=row[0],
                    article_id=row[1],
                    title=row[2],
                    status=row[3],
                    progress=float(row[4]),
                    current_step=row[5],
                    started_at=datetime.fromisoformat(row[6]) if row[6] else datetime.now()
                )
                tasks.append(task_info)
            
            conn.close()
            return tasks
            
        except Exception as e:
            self.logger.error(f"Failed to get active tasks: {e}")
            return []
    
    async def get_recent_activities(self, limit: int = 20) -> List[ActivityInfo]:
        """Get recent system activities."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get recent articles
            cursor.execute("""
                SELECT 
                    id,
                    'article' as type,
                    title,
                    status,
                    created_at,
                    source_url,
                    source_platform
                FROM articles
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            
            activities = []
            for row in cursor.fetchall():
                activity = ActivityInfo(
                    id=row[0],
                    type='article_processed',
                    title=row[2] or 'Unknown Article',
                    description=f"从 {row[6]} 处理文章",
                    timestamp=datetime.fromisoformat(row[4]) if row[4] else datetime.now(),
                    status=row[3],
                    metadata={
                        "source_url": row[5],
                        "source_platform": row[6]
                    }
                )
                activities.append(activity)
            
            conn.close()
            
            # Sort by timestamp
            activities.sort(key=lambda x: x.timestamp, reverse=True)
            return activities[:limit]
            
        except Exception as e:
            self.logger.error(f"Failed to get recent activities: {e}")
            return []

# Global instance
_dashboard_service = None

def get_dashboard_service() -> DashboardService:
    """Get dashboard service instance."""
    global _dashboard_service
    if _dashboard_service is None:
        _dashboard_service = DashboardService()
    return _dashboard_service
