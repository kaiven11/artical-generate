"""
Configuration management for the article migration tool.
"""

import os
from typing import Optional, List, Dict, Any
from pathlib import Path


class Settings:
    """Application settings."""

    def __init__(self):
        # Application
        self.app_name = os.getenv("APP_NAME", "Article Migration Tool")
        self.app_version = "1.0.0"
        self.debug = os.getenv("DEBUG", "false").lower() == "true"

        # Server
        self.host = os.getenv("HOST", "127.0.0.1")
        self.port = int(os.getenv("PORT", "8006"))
        self.reload = self.debug

        # Database
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./data/articles.db")
        self.database_echo = self.debug

        # Security
        self.secret_key = os.getenv("SECRET_KEY", os.urandom(32).hex())
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

        # Paths
        self.work_directory = os.getenv("WORK_DIRECTORY", "./data")
        self.browser_data_directory = os.getenv("BROWSER_DATA_DIRECTORY", "./browser_data")
        self.log_directory = os.getenv("LOG_DIRECTORY", "./data/logs")
        self.template_directory = os.getenv("TEMPLATE_DIRECTORY", "./templates")

        # Browser Settings
        self.chrome_path = os.getenv("BROWSER_CHROME_PATH")
        self.fingerprint_randomization_enabled = os.getenv("BROWSER_FINGERPRINT_RANDOMIZATION_ENABLED", "true").lower() == "true"
        self.randomization_frequency = int(os.getenv("BROWSER_RANDOMIZATION_FREQUENCY", "10"))
        self.headless_mode = False
        self.window_size = os.getenv("BROWSER_WINDOW_SIZE", "1920,1080")

        # Proxy Settings
        self.proxy_enabled = os.getenv("PROXY_ENABLED", "false").lower() == "true"
        self.proxy_config = {}

        # Detection Settings
        self.originality_threshold = float(os.getenv("DETECTION_ORIGINALITY_THRESHOLD", "80.0"))
        self.ai_detection_threshold = float(os.getenv("DETECTION_AI_DETECTION_THRESHOLD", "25.0"))  # 朱雀AI检测阈值
        self.auto_retry_count = int(os.getenv("DETECTION_AUTO_RETRY_COUNT", "3"))
        self.retry_interval_seconds = int(os.getenv("DETECTION_RETRY_INTERVAL_SECONDS", "10"))  # 优化：从30秒减少到10秒

        # AI Optimization Settings
        self.ai_optimization_max_attempts = int(os.getenv("AI_OPTIMIZATION_MAX_ATTEMPTS", "5"))  # AI优化最大尝试次数
        self.ai_optimization_threshold = float(os.getenv("AI_OPTIMIZATION_THRESHOLD", "25.0"))  # AI浓度阈值

        # Task Settings
        self.max_concurrent_tasks = int(os.getenv("MAX_CONCURRENT_TASKS", "5"))
        self.request_timeout_seconds = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "15"))  # 优化：从30秒减少到15秒

        # Logging
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.max_log_file_size = os.getenv("MAX_LOG_FILE_SIZE", "100MB")
        self.log_backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))

        # Auto Backup
        self.auto_backup_enabled = os.getenv("AUTO_BACKUP_ENABLED", "true").lower() == "true"
        self.backup_interval_hours = int(os.getenv("BACKUP_INTERVAL_HOURS", "24"))


class BrowserConfig:
    """Browser configuration."""

    def __init__(self):
        self.chrome_path = os.getenv("BROWSER_CHROME_PATH")
        self.user_data_directory = os.getenv("BROWSER_USER_DATA_DIRECTORY", "./browser_data")
        self.fingerprint_randomization_enabled = os.getenv("BROWSER_FINGERPRINT_RANDOMIZATION_ENABLED", "true").lower() == "true"
        self.randomization_frequency = int(os.getenv("BROWSER_RANDOMIZATION_FREQUENCY", "10"))
        self.headless_mode = False
        self.window_size = os.getenv("BROWSER_WINDOW_SIZE", "1920,1080")
        self.proxy_enabled = os.getenv("BROWSER_PROXY_ENABLED", "false").lower() == "true"
        self.proxy_config = {}


class DetectionConfig:
    """Detection configuration."""

    def __init__(self):
        self.originality_threshold = float(os.getenv("DETECTION_ORIGINALITY_THRESHOLD", "80.0"))
        self.ai_detection_threshold = float(os.getenv("DETECTION_AI_DETECTION_THRESHOLD", "25.0"))  # 朱雀AI检测阈值
        self.auto_retry_count = int(os.getenv("DETECTION_AUTO_RETRY_COUNT", "3"))
        self.retry_interval_seconds = int(os.getenv("DETECTION_RETRY_INTERVAL_SECONDS", "10"))  # 优化：从30秒减少到10秒
        self.enabled_providers = ["zhuque"]

        # AI Optimization Settings
        self.ai_optimization_max_attempts = int(os.getenv("AI_OPTIMIZATION_MAX_ATTEMPTS", "5"))  # AI优化最大尝试次数
        self.ai_optimization_threshold = float(os.getenv("AI_OPTIMIZATION_THRESHOLD", "25.0"))  # AI浓度阈值


class AIOptimizationConfig:
    """AI optimization configuration."""

    def __init__(self):
        self.max_attempts = int(os.getenv("AI_OPTIMIZATION_MAX_ATTEMPTS", "5"))  # 最大优化尝试次数
        self.threshold = float(os.getenv("AI_OPTIMIZATION_THRESHOLD", "25.0"))  # AI浓度阈值
        self.retry_delay_seconds = int(os.getenv("AI_OPTIMIZATION_RETRY_DELAY", "2"))  # 重试间隔秒数
        self.enable_progressive_optimization = os.getenv("AI_OPTIMIZATION_PROGRESSIVE", "true").lower() == "true"  # 是否启用渐进式优化
        self.optimization_strategies = ["standard", "heavy", "extreme"]  # 优化策略列表


class PublishConfig:
    """Publishing configuration."""

    def __init__(self):
        self.default_platform = os.getenv("PUBLISH_DEFAULT_PLATFORM", "toutiao")
        self.auto_publish_enabled = os.getenv("PUBLISH_AUTO_PUBLISH_ENABLED", "false").lower() == "true"
        self.publish_time_strategy = os.getenv("PUBLISH_TIME_STRATEGY", "immediate")
        self.default_category = os.getenv("PUBLISH_DEFAULT_CATEGORY", "科技")
        self.default_tags = ["AI", "机器学习", "技术"]
        self.allow_comments = os.getenv("PUBLISH_ALLOW_COMMENTS", "true").lower() == "true"
        self.allow_repost = os.getenv("PUBLISH_ALLOW_REPOST", "true").lower() == "true"


# Global settings instance
settings = Settings()
browser_config = BrowserConfig()
detection_config = DetectionConfig()
ai_optimization_config = AIOptimizationConfig()
publish_config = PublishConfig()


def get_settings() -> Settings:
    """Get application settings."""
    return settings


def get_browser_config() -> BrowserConfig:
    """Get browser configuration."""
    return browser_config


def get_detection_config() -> DetectionConfig:
    """Get detection configuration."""
    return detection_config


def get_publish_config() -> PublishConfig:
    """Get publishing configuration."""
    return publish_config


def get_ai_optimization_config() -> AIOptimizationConfig:
    """Get AI optimization configuration."""
    return ai_optimization_config


def ensure_directories():
    """Ensure all required directories exist."""
    directories = [
        settings.work_directory,
        settings.browser_data_directory,
        settings.log_directory,
        settings.template_directory,
        f"{settings.template_directory}/prompts",
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


# Initialize directories on import
ensure_directories()
