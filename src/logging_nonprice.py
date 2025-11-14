"""
非价格数据系统专用日志配置
为5个政府数据源（访客、地产、GDP、零售、贸易）提供结构化日志记录
"""

import logging
import logging.handlers
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class NonPriceDataFormatter(logging.Formatter):
    """非价格数据专用格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON结构"""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "logger": record.name,
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        # 添加数据源上下文
        if hasattr(record, 'data_source'):
            log_entry["data_source"] = record.data_source

        if hasattr(record, 'indicator_type'):
            log_entry["indicator_type"] = record.indicator_type

        if hasattr(record, 'record_count'):
            log_entry["record_count"] = record.record_count

        if hasattr(record, 'validation_errors'):
            log_entry["validation_errors"] = record.validation_errors

        return json.dumps(log_entry, ensure_ascii=False)


def setup_nonprice_logging():
    """设置非价格数据系统日志"""
    # 创建日志目录
    log_dir = Path('logs/nonprice')
    log_dir.mkdir(parents=True, exist_ok=True)

    # 创建根logger
    logger = logging.getLogger('nonprice_data')
    logger.setLevel(logging.DEBUG)

    # 文件处理器 - 所有日志
    all_log_file = log_dir / 'nonprice_all.log'
    file_handler = logging.handlers.RotatingFileHandler(
        all_log_file, maxBytes=10*1024*1024, backupCount=10, encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(NonPriceDataFormatter())

    # 文件处理器 - 仅错误
    error_log_file = log_dir / 'nonprice_errors.log'
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(NonPriceDataFormatter())

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)

    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)

    return logger


def get_data_source_logger(data_source: str) -> logging.Logger:
    """获取特定数据源的logger"""
    logger_name = f'nonprice_data.{data_source}'
    return logging.getLogger(logger_name)


def log_data_validation(
    logger: logging.Logger,
    data_source: str,
    total_records: int,
    valid_records: int,
    invalid_records: int,
    errors: list
):
    """记录数据验证结果"""
    logger.info(
        f"Data validation completed",
        extra={
            'data_source': data_source,
            'record_count': {
                'total': total_records,
                'valid': valid_records,
                'invalid': invalid_records
            },
            'validation_errors': errors
        }
    )


def log_data_fetch(
    logger: logging.Logger,
    data_source: str,
    indicator: str,
    start_date: str,
    end_date: str,
    record_count: int
):
    """记录数据获取结果"""
    logger.info(
        f"Data fetched successfully",
        extra={
            'data_source': data_source,
            'indicator': indicator,
            'start_date': start_date,
            'end_date': end_date,
            'record_count': record_count
        }
    )


def log_mock_data_detection(
    logger: logging.Logger,
    data_source: str,
    mock_indicators: list,
    confidence: float
):
    """记录模拟数据检测结果"""
    logger.warning(
        f"Mock data detected",
        extra={
            'data_source': data_source,
            'mock_indicators': mock_indicators,
            'confidence': confidence
        }
    )


# 默认logger实例
default_logger = setup_nonprice_logging()
