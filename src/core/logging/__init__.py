"""
Structured Logging System
"""
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from contextvars import ContextVar


# Context variables for correlation IDs
request_id: ContextVar[str] = ContextVar('request_id', default='')
user_id: ContextVar[str] = ContextVar('user_id', default='')
session_id: ContextVar[str] = ContextVar('session_id', default='')


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add correlation IDs
        if request_id.get():
            log_entry["request_id"] = request_id.get()
        if user_id.get():
            log_entry["user_id"] = user_id.get()
        if session_id.get():
            log_entry["session_id"] = session_id.get()

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created', 'msecs',
                          'relativeCreated', 'thread', 'threadName', 'processName',
                          'process', 'getMessage', 'exc_info', 'exc_text', 'stack_info']:
                log_entry[key] = value

        return json.dumps(log_entry, ensure_ascii=False)


class StructuredLogger:
    """Structured logger with context support"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def _log(self, level: int, message: str, **kwargs):
        """Internal logging method"""
        extra = kwargs.copy()

        # Handle correlation IDs
        if 'request_id' not in extra and request_id.get():
            extra['request_id'] = request_id.get()
        if 'user_id' not in extra and user_id.get():
            extra['user_id'] = user_id.get()
        if 'session_id' not in extra and session_id.get():
            extra['session_id'] = session_id.get()

        self.logger.log(level, message, extra=extra)

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message"""
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self._log(logging.CRITICAL, message, **kwargs)


def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """Setup structured logging"""
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Create logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)

    # Prevent duplicate logs
    logging.getLogger('uvicorn').setLevel(logging.WARNING)

    return StructuredLogger(__name__)


# Global logger instance
_logger: Optional[StructuredLogger] = None


def get_logger(name: str = None) -> StructuredLogger:
    """Get global logger instance"""
    global _logger
    if _logger is None:
        _logger = setup_logging()
    return StructuredLogger(name or "codex")


def set_correlation_ids(request_id: str = None, user_id: str = None, session_id: str = None):
    """Set correlation IDs in context"""
    if request_id:
        request_id.set(request_id)
    if user_id:
        user_id.set(user_id)
    if session_id:
        session_id.set(session_id)
