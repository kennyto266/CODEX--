"""
Structured logging configuration
JSON format logging using structlog
"""

import logging
import logging.config
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from structlog.typing import EventDict


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    enable_json_logs: bool = True,
) -> None:
    """
    Configure structured logging system

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Log file path (optional)
        enable_json_logs: Enable JSON format logging
    """
    # Ensure log directory exists
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Clear structlog configuration
    structlog.reset_defaults()

    # Set log directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Add timestamp processor
    def add_timestamp(logger, name, event_dict: EventDict) -> EventDict:
        """Add timestamp to log event"""
        event_dict["timestamp"] = time.time()
        event_dict["datetime"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        return event_dict

    # Configure processors
    processors: list = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if enable_json_logs else structlog.dev.ConsoleRenderer(colors=True),
    ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    if enable_json_logs:
        logging_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.processors.JSONRenderer(),
                },
            },
            "handlers": {
                "default": {
                    "level": level,
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "stream": sys.stdout,
                },
            },
            "loggers": {
                "": {
                    "handlers": ["default"],
                    "level": level,
                    "propagate": True,
                },
                "uvicorn": {
                    "handlers": ["default"],
                    "level": "INFO",
                    "propagate": False,
                },
            },
        }

        if log_file:
            logging_config["handlers"]["file"] = {
                "level": level,
                "class": "logging.handlers.RotatingFileHandler",
                "filename": log_file,
                "maxBytes": 10 * 1024 * 1024,
                "backupCount": 5,
                "formatter": "json",
                "encoding": "utf-8",
            }
            logging_config["loggers"][""]["handlers"].append("file")

        logging.config.dictConfig(logging_config)
    else:
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=getattr(logging, level.upper()),
            force=True,
        )

    # Get configured logger
    logger = structlog.get_logger("api.logging")
    logger.info(
        "Logging system initialized",
        level=level,
        log_file=log_file,
        json_logs=enable_json_logs,
        log_dir=str(log_dir.absolute()),
    )


def get_request_logger(request_id: str, **kwargs):
    """
    Get logger with request context

    Args:
        request_id: Request ID
        **kwargs: Additional context information

    Returns:
        Configured structured logger
    """
    context = {
        "request_id": request_id,
        **kwargs,
    }
    return structlog.get_logger(**context)


# Predefined loggers
api_logger = structlog.get_logger("api")
backtest_logger = structlog.get_logger("backtest")
data_logger = structlog.get_logger("data")
