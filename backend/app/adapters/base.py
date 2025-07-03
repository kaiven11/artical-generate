"""
Base adapter classes for platform integrations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class AdapterType(str, Enum):
    """Adapter types."""
    SOURCE = "source"
    AI = "ai"
    DETECTION = "detection"
    PUBLISH = "publish"


@dataclass
class PlatformInfo:
    """Platform information."""
    name: str
    display_name: str
    type: AdapterType
    features: List[str]
    requires_auth: bool
    description: Optional[str] = None
    version: Optional[str] = None
    website: Optional[str] = None


@dataclass
class AdapterInfo:
    """Adapter information."""
    name: str
    display_name: str
    version: str
    is_enabled: bool
    is_installed: bool
    platform_info: PlatformInfo
    config: Dict[str, Any]
    last_used: Optional[datetime] = None


@dataclass
class ArticleInfo:
    """Article information from source platforms."""
    title: str
    url: str
    author: Optional[str] = None
    publish_date: Optional[datetime] = None
    summary: Optional[str] = None
    tags: List[str] = None
    platform: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class ArticleContent:
    """Article content with metadata."""
    title: str
    content: str
    author: Optional[str] = None
    publish_date: Optional[datetime] = None
    tags: List[str] = None
    category: Optional[str] = None
    source_url: Optional[str] = None
    platform: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class TranslationResult:
    """Translation result."""
    translated_text: str
    original_text: str
    source_language: str
    target_language: str
    quality_score: Optional[float] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    processing_time: Optional[float] = None


@dataclass
class DetectionResult:
    """Detection result."""
    detection_type: str
    platform: str
    score: float
    is_passed: bool
    details: Dict[str, Any]
    confidence: Optional[float] = None
    processing_time: Optional[float] = None
    detected_at: Optional[datetime] = None


@dataclass
class PublishResult:
    """Publishing result."""
    success: bool
    platform: str
    published_url: Optional[str] = None
    error_message: Optional[str] = None
    platform_response: Dict[str, Any] = None
    published_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.platform_response is None:
            self.platform_response = {}


class BaseAdapter(ABC):
    """Base adapter class for all platform integrations."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize adapter with configuration.
        
        Args:
            config: Adapter configuration
        """
        self.config = config or {}
        self._is_initialized = False
    
    @abstractmethod
    def get_platform_info(self) -> PlatformInfo:
        """Get platform information."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test connection to the platform."""
        pass
    
    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for the adapter."""
        pass
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return self.config.copy()
    
    def update_config(self, config: Dict[str, Any]):
        """Update adapter configuration."""
        self.config.update(config)
        self._is_initialized = False
    
    async def initialize(self):
        """Initialize the adapter."""
        if not self._is_initialized:
            await self._initialize()
            self._is_initialized = True
    
    async def _initialize(self):
        """Internal initialization method to be overridden by subclasses."""
        pass
    
    def is_initialized(self) -> bool:
        """Check if adapter is initialized."""
        return self._is_initialized


class BaseSourceAdapter(BaseAdapter):
    """Base adapter for content source platforms."""
    
    @abstractmethod
    async def search_articles(self, keywords: List[str], limit: int = 20) -> List[ArticleInfo]:
        """
        Search for articles on the platform.
        
        Args:
            keywords: Search keywords
            limit: Maximum number of articles to return
            
        Returns:
            List of article information
        """
        pass
    
    @abstractmethod
    async def extract_content(self, url: str) -> ArticleContent:
        """
        Extract content from article URL.
        
        Args:
            url: Article URL
            
        Returns:
            Article content with metadata
        """
        pass
    
    def get_supported_features(self) -> List[str]:
        """Get list of supported features."""
        return ["search", "extract"]


class BaseAIAdapter(BaseAdapter):
    """Base adapter for AI service providers."""
    
    @abstractmethod
    async def translate(self, text: str, prompt: str, **kwargs) -> TranslationResult:
        """
        Translate text using AI service.
        
        Args:
            text: Text to translate
            prompt: Translation prompt
            **kwargs: Additional parameters
            
        Returns:
            Translation result
        """
        pass
    
    @abstractmethod
    async def optimize_content(self, content: str, optimization_prompt: str, **kwargs) -> str:
        """
        Optimize content using AI service.
        
        Args:
            content: Content to optimize
            optimization_prompt: Optimization prompt
            **kwargs: Additional parameters
            
        Returns:
            Optimized content
        """
        pass
    
    @abstractmethod
    def get_pricing_info(self) -> Dict[str, float]:
        """Get pricing information for the AI service."""
        pass
    
    @abstractmethod
    def estimate_cost(self, text: str) -> float:
        """Estimate cost for processing given text."""
        pass


class BaseDetectionAdapter(BaseAdapter):
    """Base adapter for detection services."""
    
    @abstractmethod
    async def detect_originality(self, content: str) -> DetectionResult:
        """
        Detect originality of content.
        
        Args:
            content: Content to check
            
        Returns:
            Detection result
        """
        pass
    
    @abstractmethod
    async def detect_ai_generated(self, content: str) -> DetectionResult:
        """
        Detect if content is AI-generated.
        
        Args:
            content: Content to check
            
        Returns:
            Detection result
        """
        pass
    
    def get_supported_detection_types(self) -> List[str]:
        """Get list of supported detection types."""
        return ["originality", "ai_generated"]


class BasePublishAdapter(BaseAdapter):
    """Base adapter for publishing platforms."""
    
    @abstractmethod
    async def login(self, credentials: Dict[str, str]) -> bool:
        """
        Login to the publishing platform.
        
        Args:
            credentials: Login credentials
            
        Returns:
            True if login successful
        """
        pass
    
    @abstractmethod
    async def publish_article(self, article: ArticleContent, config: Dict[str, Any]) -> PublishResult:
        """
        Publish article to the platform.
        
        Args:
            article: Article content to publish
            config: Publishing configuration
            
        Returns:
            Publishing result
        """
        pass
    
    @abstractmethod
    async def get_publish_status(self, task_id: str) -> str:
        """
        Get publishing status.
        
        Args:
            task_id: Publishing task ID
            
        Returns:
            Publishing status
        """
        pass
    
    @abstractmethod
    def get_platform_requirements(self) -> Dict[str, Any]:
        """Get platform-specific requirements and limitations."""
        pass
    
    def get_supported_features(self) -> List[str]:
        """Get list of supported publishing features."""
        return ["publish", "status_check"]
