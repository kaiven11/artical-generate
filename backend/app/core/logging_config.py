# -*- coding: utf-8 -*-
"""
Logging Configuration
Enhanced logging setup for detailed article processing monitoring.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


def setup_logging(
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
    log_dir: str = "logs"
):
    """
    Setup enhanced logging configuration for article processing.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file
        log_to_console: Whether to log to console
        log_dir: Directory for log files
    """
    
    # Create logs directory if it doesn't exist
    if log_to_file:
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colors
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        
        # Use colored formatter for console
        console_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        console_formatter = ColoredFormatter(
            console_format,
            datefmt="%H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # File handler for general logs
    if log_to_file:
        # General log file
        general_log_file = log_path / "article_processor.log"
        file_handler = logging.handlers.RotatingFileHandler(
            general_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        
        # File formatter (no colors)
        file_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
        file_formatter = logging.Formatter(
            file_format,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # Separate error log file
        error_log_file = log_path / "errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)
        
        # Daily processing log file
        today = datetime.now().strftime("%Y-%m-%d")
        daily_log_file = log_path / f"processing_{today}.log"
        daily_handler = logging.FileHandler(
            daily_log_file,
            encoding='utf-8'
        )
        daily_handler.setLevel(logging.INFO)
        daily_handler.setFormatter(file_formatter)
        root_logger.addHandler(daily_handler)
    
    # Configure specific loggers
    configure_specific_loggers()
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info("="*80)
    logger.info("🚀 文章处理系统日志系统已启动")
    logger.info(f"📊 日志级别: {log_level.upper()}")
    logger.info(f"📺 控制台输出: {'启用' if log_to_console else '禁用'}")
    logger.info(f"📁 文件输出: {'启用' if log_to_file else '禁用'}")
    if log_to_file:
        logger.info(f"📂 日志目录: {os.path.abspath(log_dir)}")
    logger.info("="*80)


def configure_specific_loggers():
    """Configure specific loggers for different components."""
    
    # Article processor logger
    processor_logger = logging.getLogger("app.services.article_processor")
    processor_logger.setLevel(logging.INFO)
    
    # Content extractor logger
    extractor_logger = logging.getLogger("app.services.content_extractor")
    extractor_logger.setLevel(logging.INFO)
    
    # LLM API logger
    llm_logger = logging.getLogger("app.services.llm_api")
    llm_logger.setLevel(logging.INFO)
    
    # AI detection logger
    detection_logger = logging.getLogger("app.services.ai_detection")
    detection_logger.setLevel(logging.INFO)
    
    # Database logger
    db_logger = logging.getLogger("app.core.database")
    db_logger.setLevel(logging.WARNING)  # Only warnings and errors for DB
    
    # HTTP client loggers (reduce noise)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_processing_logger(name: str = None) -> logging.Logger:
    """
    Get a logger specifically configured for processing operations.
    
    Args:
        name: Logger name (defaults to caller's module)
        
    Returns:
        Configured logger instance
    """
    if name is None:
        # Get caller's module name
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    
    logger = logging.getLogger(name)
    return logger


def log_processing_start(logger: logging.Logger, article_id: int, steps: list):
    """Log the start of article processing with detailed information."""
    logger.info("🎬 " + "="*60)
    logger.info(f"🎬 开始处理文章 ID: {article_id}")
    logger.info(f"🎬 处理步骤: {' -> '.join(steps)}")
    logger.info(f"🎬 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("🎬 " + "="*60)


def log_processing_end(logger: logging.Logger, article_id: int, success: bool, duration: float = None):
    """Log the end of article processing with results."""
    status = "成功" if success else "失败"
    emoji = "🎉" if success else "💥"
    
    logger.info(f"{emoji} " + "="*60)
    logger.info(f"{emoji} 文章处理{status} - ID: {article_id}")
    if duration:
        logger.info(f"{emoji} 总耗时: {duration:.2f}秒")
    logger.info(f"{emoji} 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"{emoji} " + "="*60)


def log_step_start(logger: logging.Logger, step: str, step_num: int, total_steps: int):
    """Log the start of a processing step."""
    logger.info("🔄 " + "-"*50)
    logger.info(f"🔄 步骤 {step_num}/{total_steps}: {step.upper()}")
    logger.info(f"🔄 开始时间: {datetime.now().strftime('%H:%M:%S')}")
    logger.info("🔄 " + "-"*50)


def log_step_end(logger: logging.Logger, step: str, success: bool, duration: float = None, details: dict = None):
    """Log the end of a processing step."""
    status = "成功" if success else "失败"
    emoji = "✅" if success else "❌"
    
    logger.info(f"{emoji} 步骤 '{step}' {status}")
    if duration:
        logger.info(f"{emoji} 耗时: {duration:.2f}秒")
    if details:
        for key, value in details.items():
            logger.info(f"{emoji} {key}: {value}")
