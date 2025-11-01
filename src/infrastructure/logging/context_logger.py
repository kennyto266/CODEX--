#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
业务上下文物化模块
为日志添加用户会话、请求ID、交易ID等业务上下文信息
"""

import os
import uuid
import time
import threading
import logging
from contextvars import ContextVar
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum

class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class BusinessContext:
    """业务上下文数据类"""
    # 用户相关
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None

    # API相关
    api_endpoint: Optional[str] = None
    http_method: Optional[str] = None
    http_status: Optional[int] = None
    response_time_ms: Optional[float] = None

    # 交易相关
    trading_symbol: Optional[str] = None
    trading_action: Optional[str] = None
    trading_quantity: Optional[float] = None
    trading_price: Optional[float] = None
    order_id: Optional[str] = None
    portfolio_id: Optional[str] = None
    strategy_name: Optional[str] = None

    # Agent相关
    agent_name: Optional[str] = None
    agent_id: Optional[str] = None
    message_type: Optional[str] = None
    correlation_id: Optional[str] = None

    # 系统相关
    service_name: Optional[str] = None
    environment: Optional[str] = None
    version: Optional[str] = None
    hostname: Optional[str] = None

    # 自定义字段
    custom_fields: Dict[str, Any] = field(default_factory=dict)

    def update(self, **kwargs):
        """更新上下文字段"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                self.custom_fields[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result.update(self.custom_fields)
        # 移除None值
        return {k: v for k, v in result.items() if v is not None}

    def merge(self, other: 'BusinessContext'):
        """合并另一个上下文"""
        self_dict = self.to_dict()
        other_dict = other.to_dict()

        # 覆盖策略：other优先，但保留两个都不为None的值
        for key, value in other_dict.items():
            if key in self_dict and self_dict[key] is not None and value is not None:
                # 如果两个都有值，保留当前的（更具体的上下文）
                continue
            setattr(self, key, value)

class ContextLogger:
    """上下文日志记录器"""

    # Context Variables for thread-safe context storage
    _user_id: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
    _session_id: ContextVar[Optional[str]] = ContextVar('session_id', default=None)
    _request_id: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
    _trading_symbol: ContextVar[Optional[str]] = ContextVar('trading_symbol', default=None)
    _agent_name: ContextVar[Optional[str]] = ContextVar('agent_name', default=None)
    _correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
    _custom_context: ContextVar[Dict[str, Any]] = ContextVar('custom_context', default_factory=dict)

    def __init__(self, name: str, logger: Optional[logging.Logger] = None):
        self.name = name
        self.logger = logger or logging.getLogger(name)
        self._lock = threading.Lock()

        # 预定义的上下文字段
        self._context_fields = [
            'user_id', 'session_id', 'request_id', 'client_ip', 'user_agent',
            'api_endpoint', 'http_method', 'http_status', 'response_time_ms',
            'trading_symbol', 'trading_action', 'trading_quantity', 'trading_price',
            'order_id', 'portfolio_id', 'strategy_name', 'agent_name', 'agent_id',
            'message_type', 'correlation_id', 'service_name', 'environment',
            'version', 'hostname'
        ]

    # ========== 上下文设置方法 ==========

    @classmethod
    def set_user_context(cls, user_id: str, session_id: Optional[str] = None):
        """设置用户上下文"""
        cls._user_id.set(user_id)
        if session_id:
            cls._session_id.set(session_id)

    @classmethod
    def set_request_context(cls, request_id: str, client_ip: Optional[str] = None,
                          user_agent: Optional[str] = None, api_endpoint: Optional[str] = None):
        """设置请求上下文"""
        cls._request_id.set(request_id)
        if client_ip:
            cls._custom_context.get().update({'client_ip': client_ip})
        if user_agent:
            cls._custom_context.get().update({'user_agent': user_agent})
        if api_endpoint:
            cls._custom_context.get().update({'api_endpoint': api_endpoint})

    @classmethod
    def set_trading_context(cls, symbol: str, action: Optional[str] = None,
                          quantity: Optional[float] = None, price: Optional[float] = None,
                          order_id: Optional[str] = None):
        """设置交易上下文"""
        cls._trading_symbol.set(symbol)
        context = cls._custom_context.get()
        if action:
            context['trading_action'] = action
        if quantity:
            context['trading_quantity'] = quantity
        if price:
            context['trading_price'] = price
        if order_id:
            context['order_id'] = order_id

    @classmethod
    def set_agent_context(cls, agent_name: str, agent_id: Optional[str] = None,
                        message_type: Optional[str] = None):
        """设置Agent上下文"""
        cls._agent_name.set(agent_name)
        context = cls._custom_context.get()
        if agent_id:
            context['agent_id'] = agent_id
        if message_type:
            context['message_type'] = message_type

    @classmethod
    def set_correlation_id(cls, correlation_id: str):
        """设置关联ID"""
        cls._correlation_id.set(correlation_id)

    @classmethod
    def set_custom_context(cls, **kwargs):
        """设置自定义上下文"""
        context = cls._custom_context.get()
        context.update(kwargs)

    @classmethod
    def clear_context(cls):
        """清除所有上下文"""
        cls._user_id.set(None)
        cls._session_id.set(None)
        cls._request_id.set(None)
        cls._trading_symbol.set(None)
        cls._agent_name.set(None)
        cls._correlation_id.set(None)
        cls._custom_context.set({})

    # ========== 上下文获取方法 ==========

    @classmethod
    def get_context(cls) -> Dict[str, Any]:
        """获取当前上下文"""
        context = cls._custom_context.get().copy()

        # 添加强制上下文字段
        if cls._user_id.get():
            context['user_id'] = cls._user_id.get()
        if cls._session_id.get():
            context['session_id'] = cls._session_id.get()
        if cls._request_id.get():
            context['request_id'] = cls._request_id.get()
        if cls._trading_symbol.get():
            context['trading_symbol'] = cls._trading_symbol.get()
        if cls._agent_name.get():
            context['agent_name'] = cls._agent_name.get()
        if cls._correlation_id.get():
            context['correlation_id'] = cls._correlation_id.get()

        # 添加系统信息
        if 'service_name' not in context:
            context['service_name'] = 'CODEX-Trading-System'
        if 'environment' not in context:
            context['environment'] = os.getenv('ENVIRONMENT', 'development')
        if 'version' not in context:
            context['version'] = os.getenv('APP_VERSION', '7.0.0')
        if 'hostname' not in context:
            context['hostname'] = os.getenv('HOSTNAME', 'localhost')

        return context

    @classmethod
    def get_context_summary(cls) -> str:
        """获取上下文摘要"""
        context = cls.get_context()

        # 提取关键信息
        summary_parts = []

        if context.get('user_id'):
            summary_parts.append(f"user={context['user_id']}")

        if context.get('session_id'):
            summary_parts.append(f"session={context['session_id'][:8]}...")

        if context.get('trading_symbol'):
            summary_parts.append(f"symbol={context['trading_symbol']}")

        if context.get('agent_name'):
            summary_parts.append(f"agent={context['agent_name']}")

        if context.get('request_id'):
            summary_parts.append(f"req={context['request_id'][:8]}...")

        return " | ".join(summary_parts) if summary_parts else "no-context"

    # ========== 日志记录方法 ==========

    def _format_message(self, message: str, **kwargs) -> str:
        """格式化日志消息"""
        # 获取上下文
        context = self.get_context()

        # 添加自定义字段
        context.update(kwargs)

        # 构建前缀
        context_summary = self.get_context_summary()

        # 格式化消息
        if context_summary != "no-context":
            formatted_message = f"[{context_summary}] {message}"
        else:
            formatted_message = message

        # 添加JSON格式的上下文（如果需要）
        if context:
            # 只添加一些关键上下文到消息中，避免过长
            key_context = {}
            for key in ['user_id', 'session_id', 'request_id', 'trading_symbol', 'agent_name', 'correlation_id']:
                if context.get(key):
                    key_context[key] = context[key]

            if key_context:
                context_str = ", ".join([f"{k}={v}" for k, v in key_context.items()])
                formatted_message += f" | ctx: {{{context_str}}}"

        return formatted_message

    def debug(self, message: str, **kwargs):
        """Debug级别日志"""
        formatted_msg = self._format_message(message, **kwargs)
        self.logger.debug(formatted_msg)

    def info(self, message: str, **kwargs):
        """Info级别日志"""
        formatted_msg = self._format_message(message, **kwargs)
        self.logger.info(formatted_msg)

    def warning(self, message: str, **kwargs):
        """Warning级别日志"""
        formatted_msg = self._format_message(message, **kwargs)
        self.logger.warning(formatted_msg)

    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Error级别日志"""
        formatted_msg = self._format_message(message, **kwargs)
        self.logger.error(formatted_msg, exc_info=exc_info)

    def critical(self, message: str, exc_info: bool = False, **kwargs):
        """Critical级别日志"""
        formatted_msg = self._format_message(message, **kwargs)
        self.logger.critical(formatted_msg, exc_info=exc_info)

    # ========== 结构化日志方法 ==========

    def log_structured(self, level: LogLevel, message: str, **kwargs):
        """记录结构化日志"""
        context = self.get_context()
        context.update(kwargs)

        log_data = {
            'timestamp': datetime.now().isoformat(),
            'level': level.value,
            'logger': self.name,
            'message': message,
            'context': context
        }

        if level == LogLevel.DEBUG:
            self.logger.debug(str(log_data))
        elif level == LogLevel.INFO:
            self.logger.info(str(log_data))
        elif level == LogLevel.WARNING:
            self.logger.warning(str(log_data))
        elif level == LogLevel.ERROR:
            self.logger.error(str(log_data))
        elif level == LogLevel.CRITICAL:
            self.logger.critical(str(log_data))

    # ========== 性能日志方法 ==========

    def log_performance(self, operation: str, duration_ms: float, **kwargs):
        """记录性能日志"""
        self.info(
            f"性能指标: {operation}",
            operation=operation,
            duration_ms=duration_ms,
            **kwargs
        )

    def log_api_call(self, endpoint: str, method: str, status_code: int,
                    response_time_ms: float, **kwargs):
        """记录API调用"""
        self.info(
            f"API调用: {method} {endpoint}",
            api_endpoint=endpoint,
            http_method=method,
            http_status=status_code,
            response_time_ms=response_time_ms,
            **kwargs
        )

    def log_trade_execution(self, symbol: str, action: str, quantity: float,
                          price: float, order_id: str, **kwargs):
        """记录交易执行"""
        self.info(
            f"交易执行: {action} {quantity} {symbol} @ {price}",
            trading_symbol=symbol,
            trading_action=action,
            trading_quantity=quantity,
            trading_price=price,
            order_id=order_id,
            **kwargs
        )

    def log_agent_message(self, agent_name: str, message_type: str,
                        correlation_id: str, **kwargs):
        """记录Agent消息"""
        self.info(
            f"Agent消息: {agent_name} - {message_type}",
            agent_name=agent_name,
            message_type=message_type,
            correlation_id=correlation_id,
            **kwargs
        )

# 全局上下文日志记录器实例
_global_context_logger: Optional[ContextLogger] = None

def get_context_logger(name: str = "app") -> ContextLogger:
    """获取全局上下文日志记录器"""
    global _global_context_logger
    if _global_context_logger is None:
        _global_context_logger = ContextLogger(name)
    return _global_context_logger

# 装饰器和上下文管理器
from contextlib import contextmanager
import functools

@contextmanager
def user_context(user_id: str, session_id: Optional[str] = None):
    """用户上下文管理器"""
    ContextLogger.set_user_context(user_id, session_id)
    try:
        yield
    finally:
        ContextLogger.set_user_context(None, None)

@contextmanager
def request_context(request_id: str, client_ip: Optional[str] = None,
                   user_agent: Optional[str] = None, api_endpoint: Optional[str] = None):
    """请求上下文管理器"""
    ContextLogger.set_request_context(request_id, client_ip, user_agent, api_endpoint)
    try:
        yield
    finally:
        ContextLogger.set_request_context(None)

@contextmanager
def trading_context(symbol: str, action: Optional[str] = None,
                   quantity: Optional[float] = None, price: Optional[float] = None,
                   order_id: Optional[str] = None):
    """交易上下文管理器"""
    ContextLogger.set_trading_context(symbol, action, quantity, price, order_id)
    try:
        yield
    finally:
        ContextLogger.set_trading_context(None)

@contextmanager
def agent_context(agent_name: str, agent_id: Optional[str] = None,
                 message_type: Optional[str] = None):
    """Agent上下文管理器"""
    ContextLogger.set_agent_context(agent_name, agent_id, message_type)
    try:
        yield
    finally:
        ContextLogger.set_agent_context(None)

def with_context(**context_kwargs):
    """上下文装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 保存当前上下文
            original_context = ContextLogger.get_context()

            # 设置新上下文
            for key, value in context_kwargs.items():
                ContextLogger.set_custom_context(**{key: value})

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # 恢复原始上下文
                ContextLogger.clear_context()
                # 重新设置原始上下文
                for key, value in original_context.items():
                    ContextLogger.set_custom_context(**{key: value})

        return wrapper
    return decorator

def generate_request_id() -> str:
    """生成请求ID"""
    return str(uuid.uuid4())

def generate_correlation_id() -> str:
    """生成关联ID"""
    return str(uuid.uuid4())

def measure_time(func):
    """测量执行时间装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger = get_context_logger(func.__module__)

        try:
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000
            logger.log_performance(func.__name__, duration_ms)
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"函数执行失败: {func.__name__}",
                operation=func.__name__,
                duration_ms=duration_ms,
                error=str(e),
                exc_info=True
            )
            raise

    return wrapper

# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = get_context_logger("test")

    print("🧪 测试业务上下文物化系统...")

    # 测试基本上下文
    with user_context("user123", "session456"):
        logger.info("用户登录")
        logger.info("用户查看交易")

    # 测试交易上下文
    with trading_context("0700.HK", "BUY", 100, 350.5, "order789"):
        logger.log_trade_execution("0700.HK", "BUY", 100, 350.5, "order789")

    # 测试Agent上下文
    with agent_context("DataScientist", "agent001", "DATA_PROCESS"):
        logger.log_agent_message("DataScientist", "DATA_PROCESS", "corr123")
        logger.info("Agent处理数据")

    # 测试性能监控
    @measure_time
    def slow_operation():
        time.sleep(0.1)
        return "完成"

    result = slow_operation()

    # 测试API调用日志
    logger.log_api_call("/api/analysis/0700.HK", "GET", 200, 150.5)

    print("\n✅ 业务上下文物化系统测试完成")
    print("📋 所有日志都包含了丰富的业务上下文信息")
