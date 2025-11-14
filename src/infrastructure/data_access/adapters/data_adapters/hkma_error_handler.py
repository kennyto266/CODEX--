"""
HKMA错误处理器
提供统一的错误处理、重试和降级策略

功能:
- 网络错误处理
- 重试机制（指数退避、抖动）
- 降级策略
- 错误分类
- 告警机制
- 错误统计
- 缓存恢复
"""

import asyncio
import logging
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
import os
from dataclasses import dataclass, asdict
from enum import Enum
from functools import wraps
import aiofiles

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """错误类型"""
    NETWORK_ERROR = "network_error"
    HTTP_ERROR = "http_error"
    TIMEOUT = "timeout"
    PARSING_ERROR = "parsing_error"
    VALIDATION_ERROR = "validation_error"
    DATA_NOT_FOUND = "data_not_found"
    RATE_LIMIT = "rate_limit"
    SERVER_ERROR = "server_error"
    AUTH_ERROR = "auth_error"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """错误严重级别"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class RetryStrategy(Enum):
    """重试策略"""
    FIXED_DELAY = "fixed_delay"  # 固定延迟
    EXPONENTIAL_BACKOFF = "exponential_backoff"  # 指数退避
    EXPONENTIAL_WITH_JITTER = "exponential_with_jitter"  # 指数退避+抖动
    LINEAR_BACKOFF = "linear_backoff"  # 线性退避


@dataclass
class HKMARecoverableError(Exception):
    """可恢复的HKMA错误"""
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    original_error: Exception
    retryable: bool = True
    context: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'error_type': self.error_type.value,
            'severity': self.severity.value,
            'message': self.message,
            'retryable': self.retryable,
            'context': self.context,
            'timestamp': datetime.now().isoformat()
        }


@dataclass
class ErrorStats:
    """错误统计"""
    error_type: ErrorType
    count: int
    first_occurrence: datetime
    last_occurrence: datetime
    last_message: str
    recovery_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'error_type': self.error_type.value,
            'count': self.count,
            'first_occurrence': self.first_occurrence.isoformat(),
            'last_occurrence': self.last_occurrence.isoformat(),
            'last_message': self.last_message,
            'recovery_count': self.recovery_count
        }


class HKMAErrorHandler:
    """HKMA错误处理器"""

    ERROR_STORE_FILE = "data/hkma_error_store.json"

    # 错误类型到重试配置的映射
    RETRY_CONFIGS = {
        ErrorType.NETWORK_ERROR: {
            'max_retries': 5,
            'initial_delay': 1.0,
            'max_delay': 60.0,
            'strategy': RetryStrategy.EXPONENTIAL_WITH_JITTER,
            'backoff_factor': 2.0,
            'jitter': True
        },
        ErrorType.TIMEOUT: {
            'max_retries': 3,
            'initial_delay': 2.0,
            'max_delay': 30.0,
            'strategy': RetryStrategy.EXPONENTIAL_WITH_JITTER,
            'backoff_factor': 2.0,
            'jitter': True
        },
        ErrorType.RATE_LIMIT: {
            'max_retries': 8,
            'initial_delay': 5.0,
            'max_delay': 300.0,
            'strategy': RetryStrategy.EXPONENTIAL_WITH_JITTER,
            'backoff_factor': 2.0,
            'jitter': True
        },
        ErrorType.SERVER_ERROR: {
            'max_retries': 3,
            'initial_delay': 3.0,
            'max_delay': 60.0,
            'strategy': RetryStrategy.EXPONENTIAL_WITH_JITTER,
            'backoff_factor': 2.0,
            'jitter': True
        },
        ErrorType.HTTP_ERROR: {
            'max_retries': 1,
            'initial_delay': 1.0,
            'max_delay': 10.0,
            'strategy': RetryStrategy.FIXED_DELAY,
            'backoff_factor': 1.0,
            'jitter': False
        }
    }

    # 不可重试的错误
    NON_RETRYABLE_ERRORS = {
        ErrorType.AUTH_ERROR,
        ErrorType.VALIDATION_ERROR,
        ErrorType.PARSING_ERROR
    }

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化错误处理器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # 错误统计
        self.error_stats: Dict[str, ErrorStats] = {}
        self.load_error_stats()

        # 告警回调
        self.alert_callbacks: List[Callable] = []

        # 降级模式
        self.degraded_mode = False
        self.degraded_mode_count = 0
        self.degraded_mode_threshold = self.config.get('degraded_mode_threshold', 10)
        self.degraded_mode_reset_time = self.config.get('degraded_mode_reset_time', 3600)  # 1小时

    def add_alert_callback(self, callback: Callable):
        """
        添加告警回调

        Args:
            callback: 告警回调函数
        """
        self.alert_callbacks.append(callback)

    async def _trigger_alert(self, error: HKMARecoverableError):
        """触发告警"""
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(error)
                else:
                    callback(error)
            except Exception as e:
                self.logger.error(f"告警回调执行失败: {e}")

    def classify_error(self, error: Exception) -> ErrorType:
        """
        分类错误

        Args:
            error: 异常对象

        Returns:
            错误类型
        """
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()

        # 网络错误
        if any(keyword in error_str for keyword in ['connection', 'network', 'dns', 'unreachable']):
            return ErrorType.NETWORK_ERROR

        # 超时错误
        if 'timeout' in error_str or 'timed out' in error_str:
            return ErrorType.TIMEOUT

        # HTTP错误
        if 'http' in error_str or 'status' in error_str:
            if '404' in error_str or 'not found' in error_str:
                return ErrorType.DATA_NOT_FOUND
            elif '401' in error_str or '403' in error_str or 'unauthorized' in error_str:
                return ErrorType.AUTH_ERROR
            elif '429' in error_str or 'rate limit' in error_str:
                return ErrorType.RATE_LIMIT
            elif any(code in error_str for code in ['500', '502', '503', '504']):
                return ErrorType.SERVER_ERROR
            else:
                return ErrorType.HTTP_ERROR

        # 解析错误
        if any(keyword in error_str for keyword in ['parse', 'parse error', '解析']):
            return ErrorType.PARSING_ERROR

        # 验证错误
        if any(keyword in error_str for keyword in ['validate', 'validation', '验证']):
            return ErrorType.VALIDATION_ERROR

        # 数据未找到
        if any(keyword in error_str for keyword in ['not found', 'no data', 'data not found']):
            return ErrorType.DATA_NOT_FOUND

        return ErrorType.UNKNOWN

    def determine_severity(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorSeverity:
        """
        确定错误严重级别

        Args:
            error: 异常对象
            context: 错误上下文

        Returns:
            严重级别
        """
        error_type = self.classify_error(error)

        # 关键错误
        if error_type in {ErrorType.AUTH_ERROR, ErrorType.VALIDATION_ERROR}:
            return ErrorSeverity.CRITICAL

        # 严重错误
        if error_type in {ErrorType.SERVER_ERROR, ErrorType.PARSING_ERROR}:
            return ErrorSeverity.HIGH

        # 中等错误
        if error_type in {ErrorType.TIMEOUT, ErrorType.DATA_NOT_FOUND}:
            return ErrorSeverity.MEDIUM

        # 低级错误
        if error_type in {ErrorType.NETWORK_ERROR, ErrorType.RATE_LIMIT}:
            return ErrorSeverity.LOW

        return ErrorSeverity.MEDIUM

    def is_retryable(self, error: Exception) -> bool:
        """
        判断错误是否可重试

        Args:
            error: 异常对象

        Returns:
            是否可重试
        """
        error_type = self.classify_error(error)
        return error_type not in self.NON_RETRYABLE_ERRORS

    def calculate_retry_delay(
        self,
        error: Exception,
        attempt: int,
        config: Optional[Dict] = None
    ) -> float:
        """
        计算重试延迟

        Args:
            error: 异常对象
            attempt: 当前尝试次数（从0开始）
            config: 特定重试配置

        Returns:
            延迟时间（秒）
        """
        error_type = self.classify_error(error)
        retry_config = config or self.RETRY_CONFIGS.get(
            error_type,
            {
                'max_retries': 3,
                'initial_delay': 1.0,
                'max_delay': 30.0,
                'strategy': RetryStrategy.EXPONENTIAL_BACKOFF,
                'backoff_factor': 2.0,
                'jitter': True
            }
        )

        strategy = retry_config.get('strategy', RetryStrategy.EXPONENTIAL_BACKOFF)
        initial_delay = retry_config.get('initial_delay', 1.0)
        max_delay = retry_config.get('max_delay', 30.0)
        backoff_factor = retry_config.get('backoff_factor', 2.0)
        jitter = retry_config.get('jitter', True)

        if strategy == RetryStrategy.FIXED_DELAY:
            delay = initial_delay

        elif strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = initial_delay * (attempt + 1)

        elif strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = initial_delay * (backoff_factor ** attempt)

        elif strategy == RetryStrategy.EXPONENTIAL_WITH_JITTER:
            delay = initial_delay * (backoff_factor ** attempt)
            if jitter:
                # 添加±20%抖动
                import random
                delay *= (0.8 + 0.4 * random.random())

        else:
            delay = initial_delay

        # 限制最大延迟
        return min(delay, max_delay)

    def should_retry(
        self,
        error: Exception,
        attempt: int,
        max_retries: Optional[int] = None
    ) -> bool:
        """
        判断是否应该重试

        Args:
            error: 异常对象
            attempt: 当前尝试次数
            max_retries: 最大重试次数

        Returns:
            是否应该重试
        """
        error_type = self.classify_error(error)

        # 不可重试的错误
        if not self.is_retryable(error):
            return False

        # 达到最大重试次数
        if max_retries is None:
            max_retries = self.RETRY_CONFIGS.get(error_type, {}).get('max_retries', 3)

        if attempt >= max_retries:
            return False

        # 检查降级模式
        if self.degraded_mode:
            return attempt < 1  # 降级模式下只重试一次

        return True

    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        error_type: Optional[ErrorType] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[Callable] = None,
        fallback: Optional[Callable] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        执行函数并处理错误

        Args:
            func: 要执行的函数
            *args: 位置参数
            error_type: 错误类型
            max_retries: 最大重试次数
            retry_delay: 自定义重试延迟计算函数
            fallback: 降级处理函数
            context: 错误上下文
            **kwargs: 关键字参数

        Returns:
            函数执行结果

        Raises:
            HKMARecoverableError: 可恢复错误
            Exception: 不可恢复错误
        """
        attempt = 0
        last_error = None

        while attempt == 0 or self.should_retry(last_error, attempt, max_retries):
            try:
                # 执行函数
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = await asyncio.get_event_loop().run_in_executor(
                        None, func, *args, **kwargs
                    )

                # 成功，重置降级模式
                if self.degraded_mode and attempt > 0:
                    self.logger.info("错误已恢复，退出降级模式")
                    self.degraded_mode = False
                    self.degraded_mode_count = 0

                return result

            except Exception as e:
                last_error = e
                classified_error = self.classify_error(e)
                severity = self.determine_severity(e, context)

                # 记录错误统计
                self._update_error_stats(classified_error, str(e))

                # 转换为可恢复错误
                recoverable_error = HKMARecoverableError(
                    error_type=classified_error,
                    severity=severity,
                    message=str(e),
                    original_error=e,
                    retryable=self.is_retryable(e),
                    context=context
                )

                # 触发告警
                await self._trigger_alert(recoverable_error)

                # 检查是否需要重试
                if not self.is_retryable(e):
                    self.logger.error(f"不可重试错误: {e}")
                    raise recoverable_error

                # 计算重试延迟
                if retry_delay:
                    delay = retry_delay(e, attempt)
                else:
                    delay = self.calculate_retry_delay(e, attempt)

                # 检查是否还有重试机会
                if self.should_retry(e, attempt + 1, max_retries):
                    self.logger.warning(
                        f"错误 {classified_error.value}，{delay:.2f}秒后重试 "
                        f"(第 {attempt + 1} 次尝试): {e}"
                    )
                    await asyncio.sleep(delay)
                    attempt += 1
                else:
                    self.logger.error(f"达到最大重试次数，错误: {e}")
                    break

        # 所有重试都失败了
        self.logger.error(f"重试失败，最终错误: {last_error}")

        # 尝试降级处理
        if fallback:
            self.logger.info("尝试降级处理...")
            try:
                if asyncio.iscoroutinefunction(fallback):
                    return await fallback(*args, **kwargs)
                else:
                    return await asyncio.get_event_loop().run_in_executor(
                        None, fallback, *args, **kwargs
                    )
            except Exception as fallback_error:
                self.logger.error(f"降级处理也失败: {fallback_error}")
                raise fallback_error

        # 进入降级模式
        self.degraded_mode_count += 1
        if self.degraded_mode_count >= self.degraded_mode_threshold:
            self.logger.warning("进入降级模式")
            self.degraded_mode = True

        raise last_error

    def retry(
        self,
        error_type: Optional[ErrorType] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[Callable] = None,
        fallback: Optional[Callable] = None,
        context_key: Optional[str] = None
    ):
        """
        重试装饰器

        Args:
            error_type: 错误类型
            max_retries: 最大重试次数
            retry_delay: 自定义重试延迟计算函数
            fallback: 降级处理函数
            context_key: 上下文键名

        Returns:
            装饰器
        """
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # 提取上下文
                context = None
                if context_key and context_key in kwargs:
                    context = kwargs[context_key]

                return await self.execute_with_retry(
                    func,
                    *args,
                    error_type=error_type,
                    max_retries=max_retries,
                    retry_delay=retry_delay,
                    fallback=fallback,
                    context=context,
                    **kwargs
                )

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # 同步函数包装为异步
                async def async_func():
                    return func(*args, **kwargs)

                return asyncio.run(async_func())

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        return decorator

    def _update_error_stats(self, error_type: ErrorType, message: str):
        """更新错误统计"""
        now = datetime.now()
        key = error_type.value

        if key in self.error_stats:
            stats = self.error_stats[key]
            stats.count += 1
            stats.last_occurrence = now
            stats.last_message = message
        else:
            self.error_stats[key] = ErrorStats(
                error_type=error_type,
                count=1,
                first_occurrence=now,
                last_occurrence=now,
                last_message=message
            )

        # 保存统计
        self.save_error_stats()

    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计"""
        return {
            key: stats.to_dict() for key, stats in self.error_stats.items()
        }

    def get_error_summary(self) -> Dict[str, Any]:
        """获取错误摘要"""
        total_errors = sum(stats.count for stats in self.error_stats.values())
        unique_errors = len(self.error_stats)

        # 错误最多的类型
        most_common = max(
            self.error_stats.items(),
            key=lambda x: x[1].count,
            default=(None, None)
        )

        return {
            'total_errors': total_errors,
            'unique_error_types': unique_errors,
            'most_common_error': {
                'type': most_common[0],
                'count': most_common[1].count if most_common[1] else 0
            } if most_common[0] else None,
            'degraded_mode': self.degraded_mode,
            'error_breakdown': {
                key: {
                    'count': stats.count,
                    'percentage': (stats.count / total_errors * 100) if total_errors > 0 else 0
                }
                for key, stats in self.error_stats.items()
            }
        }

    def load_error_stats(self):
        """加载错误统计"""
        try:
            if os.path.exists(self.ERROR_STORE_FILE):
                with open(self.ERROR_STORE_FILE, 'r') as f:
                    data = json.load(f)

                for key, stats_data in data.get('error_stats', {}).items():
                    try:
                        self.error_stats[key] = ErrorStats(
                            error_type=ErrorType(stats_data['error_type']),
                            count=stats_data['count'],
                            first_occurrence=datetime.fromisoformat(stats_data['first_occurrence']),
                            last_occurrence=datetime.fromisoformat(stats_data['last_occurrence']),
                            last_message=stats_data['last_message'],
                            recovery_count=stats_data.get('recovery_count', 0)
                        )
                    except (ValueError, KeyError) as e:
                        self.logger.warning(f"跳过无效的错误统计数据: {e}")
        except Exception as e:
            self.logger.error(f"加载错误统计失败: {e}")

    def save_error_stats(self):
        """保存错误统计"""
        try:
            import os
            os.makedirs(os.path.dirname(self.ERROR_STORE_FILE), exist_ok=True)

            data = {
                'error_stats': {
                    key: stats.to_dict() for key, stats in self.error_stats.items()
                },
                'updated_at': datetime.now().isoformat()
            }

            with open(self.ERROR_STORE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"保存错误统计失败: {e}")

    def clear_error_stats(self):
        """清除错误统计"""
        self.error_stats.clear()
        self.save_error_stats()
        self.logger.info("已清除错误统计")

    async def handle_cache_recovery(
        self,
        cache_key: str,
        fetch_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        缓存恢复处理器

        Args:
            cache_key: 缓存键
            fetch_func: 数据获取函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            数据（来自缓存或重新获取）
        """
        # 首先尝试从缓存获取
        from .hkma_hibor import HKMAHibiorAdapter
        cache = HKMAHibiorAdapter().cache

        cached_data = cache.get(cache_key)
        if cached_data:
            self.logger.info(f"从缓存获取数据: {cache_key}")
            return cached_data

        # 缓存未命中，尝试重新获取
        try:
            data = await self.execute_with_retry(fetch_func, *args, **kwargs)

            # 保存到缓存
            cache.set(cache_key, data, ttl=3600)  # 1小时缓存

            return data

        except Exception as e:
            # 获取失败，尝试从旧缓存获取（如果允许）
            self.logger.warning(f"数据获取失败，尝试降级到旧缓存: {e}")
            # 这里可以实现更复杂的缓存恢复策略
            raise


# 全局错误处理器实例
error_handler: Optional[HKMAErrorHandler] = None


def get_error_handler() -> HKMAErrorHandler:
    """获取全局错误处理器实例"""
    global error_handler
    if error_handler is None:
        error_handler = HKMAErrorHandler()
    return error_handler


# 装饰器便捷函数
def hkma_retry(
    error_type: Optional[ErrorType] = None,
    max_retries: Optional[int] = None,
    fallback: Optional[Callable] = None
):
    """
    HIBOR重试装饰器便捷函数

    Args:
        error_type: 错误类型
        max_retries: 最大重试次数
        fallback: 降级处理函数

    Returns:
        装饰器
    """
    return get_error_handler().retry(
        error_type=error_type,
        max_retries=max_retries,
        fallback=fallback
    )


if __name__ == "__main__":
    # 测试代码
    import random

    async def test_function(success_rate: float = 0.5):
        """模拟可能失败的函数"""
        if random.random() > success_rate:
            raise ConnectionError("模拟网络错误")
        return "成功"

    async def test():
        handler = HKMAErrorHandler()

        # 测试重试
        result = await handler.execute_with_retry(
            test_function,
            success_rate=0.3,
            max_retries=5,
            context={'test': True}
        )

        print(f"执行结果: {result}")
        print(f"错误统计: {json.dumps(handler.get_error_summary(), indent=2)}")

    asyncio.run(test())
