"""
Database models for the article migration tool.
"""

from .article import Article, ArticleStatus
from .prompt import PromptTemplate, PromptType
from .detection import DetectionResult, DetectionType
from .task import Task, TaskType, TaskStatus, TaskPriority
from .config import APIProvider, APIModel, SystemConfig

__all__ = [
    "Article",
    "ArticleStatus", 
    "PromptTemplate",
    "PromptType",
    "DetectionResult",
    "DetectionType",
    "Task",
    "TaskType",
    "TaskStatus", 
    "TaskPriority",
    "APIProvider",
    "APIModel",
    "SystemConfig",
]
