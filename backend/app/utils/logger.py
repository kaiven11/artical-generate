"""
Logging configuration and utilities.
"""

import sys
import logging
from pathlib import Path
from loguru import logger as loguru_logger

from ..core.config import get_settings

settings = get_settings()


class InterceptHandler(logging.Handler):
    """Intercept standard logging and redirect to loguru."""
    
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = loguru_logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        loguru_logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging():
    """Setup logging configuration."""
    
    # Remove default loguru handler
    loguru_logger.remove()
    
    # Add console handler
    loguru_logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # Add file handler
    log_file_path = Path(settings.log_directory) / "app.log"
    loguru_logger.add(
        log_file_path,
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation=settings.max_log_file_size,
        retention=settings.log_backup_count,
        compression="zip",
        backtrace=True,
        diagnose=True
    )
    
    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Set specific loggers
    for logger_name in ["uvicorn", "uvicorn.access", "fastapi", "sqlalchemy"]:
        logging.getLogger(logger_name).handlers = [InterceptHandler()]
    
    loguru_logger.info("Logging configured successfully")


def get_logger(name: str):
    """Get logger instance."""
    return loguru_logger.bind(name=name)
