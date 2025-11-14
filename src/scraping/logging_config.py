"""
Logging configuration for the scraping module

Provides structured logging with JSON format and comprehensive monitoring
for NLP processing, configuration generation, and scraping execution.
"""

import logging
import logging.config
import json
from datetime import datetime
from typing import Dict, Any
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "component": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        if hasattr(record, 'execution_id'):
            log_entry["execution_id"] = record.execution_id
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        if hasattr(record, 'operation'):
            log_entry["operation"] = record.operation
        if hasattr(record, 'duration_ms'):
            log_entry["duration_ms"] = record.duration_ms
        if hasattr(record, 'confidence_score'):
            log_entry["confidence_score"] = record.confidence_score
        if hasattr(record, 'data_points_extracted'):
            log_entry["data_points_extracted"] = record.data_points_extracted
        if hasattr(record, 'error_code'):
            log_entry["error_code"] = record.error_code
        if hasattr(record, 'url'):
            log_entry["url"] = record.url

        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(log_level: str = "INFO", log_file: str = None) -> None:
    """
    Setup logging configuration for scraping module

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
    """

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JSONFormatter
            },
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "json",
                "stream": "ext://sys.stdout"
            }
        },
        "loggers": {
            "scraping": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "scraping.nlp": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "scraping.config": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "scraping.executor": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "scraping.quality": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            }
        },
        "root": {
            "level": "WARNING",
            "handlers": ["console"]
        }
    }

    # Add file handler if log_file specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        config["handlers"]["file"] = {
            "class": "logging.FileHandler",
            "level": log_level,
            "formatter": "json",
            "filename": str(log_path),
            "mode": "a",
            "encoding": "utf-8"
        }

        # Add file handler to all scraping loggers
        for logger_name in config["loggers"]:
            if logger_name.startswith("scraping"):
                config["loggers"][logger_name]["handlers"].append("file")

    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name

    Args:
        name: Logger name (should start with 'scraping.')

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class StructuredLogger:
    """Helper class for structured logging with additional context"""

    def __init__(self, name: str):
        self.logger = get_logger(name)
        self._context: Dict[str, Any] = {}

    def set_context(self, **kwargs) -> None:
        """Set default context for all log messages"""
        self._context.update(kwargs)

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message with context"""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message with context"""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message with context"""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log error message with context"""
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """Log critical message with context"""
        self._log(logging.CRITICAL, message, **kwargs)

    def _log(self, level: int, message: str, **kwargs) -> None:
        """Internal logging method with context merging"""
        # Merge default context with provided context
        context = {**self._context, **kwargs}

        # Create log record with extra context
        extra = {}
        for key, value in context.items():
            extra[key] = value

        self.logger.log(level, message, extra=extra)


# Initialize logging when module is imported
setup_logging()