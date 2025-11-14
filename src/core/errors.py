"""
错误处理框架
定义非价格数据系统的所有错误类型
"""

from typing import Optional, Dict, Any, List
from enum import Enum


class ErrorCode(str, Enum):
    """错误代码枚举"""
    # 数据获取错误 (1000-1999)
    DATA_FETCH_FAILED = "DATA_FETCH_FAILED"
    API_RATE_LIMIT_EXCEEDED = "API_RATE_LIMIT_EXCEEDED"
    API_AUTHENTICATION_FAILED = "API_AUTHENTICATION_FAILED"
    API_ENDPOINT_UNREACHABLE = "API_ENDPOINT_UNREACHABLE"
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"

    # 数据验证错误 (2000-2999)
    DATA_VALIDATION_FAILED = "DATA_VALIDATION_FAILED"
    INVALID_DATA_FORMAT = "INVALID_DATA_FORMAT"
    MISSING_REQUIRED_FIELDS = "MISSING_REQUIRED_FIELDS"
    INVALID_DATE_RANGE = "INVALID_DATE_RANGE"
    DATA_CORRUPTION_DETECTED = "DATA_CORRUPTION_DETECTED"

    # 数据处理错误 (3000-3999)
    DATA_PROCESSING_FAILED = "DATA_PROCESSING_FAILED"
    INDICATOR_CALCULATION_ERROR = "INDICATOR_CALCULATION_ERROR"
    INSUFFICIENT_DATA_POINTS = "INSUFFICIENT_DATA_POINTS"
    DIVISION_BY_ZERO = "DIVISION_BY_ZERO"
    INVALID_PARAMETERS = "INVALID_PARAMETERS"

    # 数据源错误 (4000-4999)
    DATA_SOURCE_NOT_FOUND = "DATA_SOURCE_NOT_FOUND"
    DATA_SOURCE_UNAVAILABLE = "DATA_SOURCE_UNAVAILABLE"
    ADAPTER_NOT_REGISTERED = "ADAPTER_NOT_REGISTERED"
    UNSUPPORTED_DATA_SOURCE = "UNSUPPORTED_DATA_SOURCE"

    # 模拟数据错误 (5000-5999)
    MOCK_DATA_DETECTED = "MOCK_DATA_DETECTED"
    HIGH_MOCK_CONFIDENCE = "HIGH_MOCK_CONFIDENCE"
    REAL_DATA_REQUIRED = "REAL_DATA_REQUIRED"

    # 配置错误 (6000-6999)
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    MISSING_CONFIGURATION = "MISSING_CONFIGURATION"
    INVALID_CONFIGURATION = "INVALID_CONFIGURATION"

    # 系统错误 (7000-7999)
    SYSTEM_ERROR = "SYSTEM_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    CACHE_ERROR = "CACHE_ERROR"
    PARALLEL_EXECUTION_ERROR = "PARALLEL_EXECUTION_ERROR"


class NonPriceDataError(Exception):
    """
    非价格数据系统基础错误类
    """

    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        """
        初始化错误

        Args:
            message: 错误消息
            error_code: 错误代码
            details: 错误详情
            cause: 原因异常
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause

        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典

        Returns:
            Dict[str, Any]: 错误信息字典
        """
        result = {
            "error_code": self.error_code.value,
            "message": self.message,
            "details": self.details
        }

        if self.cause:
            result["cause"] = str(self.cause)
            result["cause_type"] = self.cause.__class__.__name__

        return result

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__}("
            f"error_code={self.error_code.value}, "
            f"message='{self.message}'"
            f")>"
        )


class DataFetchError(NonPriceDataError):
    """数据获取错误"""

    def __init__(
        self,
        message: str,
        data_source: str,
        indicator: str,
        **kwargs
    ):
        details = kwargs.get('details', {})
        details.update({
            'data_source': data_source,
            'indicator': indicator
        })

        kwargs['details'] = details
        super().__init__(message, ErrorCode.DATA_FETCH_FAILED, **kwargs)


class APIRateLimitError(NonPriceDataError):
    """API速率限制错误"""

    def __init__(
        self,
        message: str,
        data_source: str,
        retry_after: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        details.update({
            'data_source': data_source,
            'retry_after': retry_after
        })

        kwargs['details'] = details
        super().__init__(message, ErrorCode.API_RATE_LIMIT_EXCEEDED, **kwargs)


class DataValidationError(NonPriceDataError):
    """数据验证错误"""

    def __init__(
        self,
        message: str,
        validation_errors: List[str],
        **kwargs
    ):
        details = kwargs.get('details', {})
        details.update({
            'validation_errors': validation_errors
        })

        kwargs['details'] = details
        super().__init__(message, ErrorCode.DATA_VALIDATION_FAILED, **kwargs)


class DataProcessingError(NonPriceDataError):
    """数据处理错误"""

    def __init__(
        self,
        message: str,
        operation: str,
        data_source: str,
        **kwargs
    ):
        details = kwargs.get('details', {})
        details.update({
            'operation': operation,
            'data_source': data_source
        })

        kwargs['details'] = details
        super().__init__(message, ErrorCode.DATA_PROCESSING_FAILED, **kwargs)


class IndicatorCalculationError(NonPriceDataError):
    """指标计算错误"""

    def __init__(
        self,
        message: str,
        indicator_type: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        details.update({
            'indicator_type': indicator_type,
            'parameters': parameters
        })

        kwargs['details'] = details
        super().__init__(message, ErrorCode.INDICATOR_CALCULATION_ERROR, **kwargs)


class DataSourceError(NonPriceDataError):
    """数据源错误"""

    def __init__(
        self,
        message: str,
        data_source: str,
        **kwargs
    ):
        details = kwargs.get('details', {})
        details.update({
            'data_source': data_source
        })

        kwargs['details'] = details
        super().__init__(message, ErrorCode.DATA_SOURCE_UNAVAILABLE, **kwargs)


class MockDataError(NonPriceDataError):
    """模拟数据错误"""

    def __init__(
        self,
        message: str,
        data_source: str,
        confidence: float,
        **kwargs
    ):
        details = kwargs.get('details', {})
        details.update({
            'data_source': data_source,
            'confidence': confidence
        })

        kwargs['details'] = details
        super().__init__(message, ErrorCode.MOCK_DATA_DETECTED, **kwargs)


class ConfigurationError(NonPriceDataError):
    """配置错误"""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if config_key:
            details.update({'config_key': config_key})

        kwargs['details'] = details
        super().__init__(message, ErrorCode.CONFIGURATION_ERROR, **kwargs)


class SystemError(NonPriceDataError):
    """系统错误"""

    def __init__(
        self,
        message: str,
        component: str,
        **kwargs
    ):
        details = kwargs.get('details', {})
        details.update({
            'component': component
        })

        kwargs['details'] = details
        super().__init__(message, ErrorCode.SYSTEM_ERROR, **kwargs)


# 错误处理装饰器
def handle_errors(
    reraise: bool = True,
    default_return: Any = None,
    log_errors: bool = True
):
    """
    错误处理装饰器

    Args:
        reraise: 是否重新抛出错误
        default_return: 默认返回值
        log_errors: 是否记录错误
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except NonPriceDataError:
                raise  # 重新抛出已知错误
            except Exception as e:
                if log_errors:
                    import logging
                    logger = logging.getLogger('nonprice_data')
                    logger.error(
                        f"Unexpected error in {func.__name__}: {str(e)}",
                        exc_info=True
                    )

                if reraise:
                    raise SystemError(
                        f"Unexpected error in {func.__name__}: {str(e)}",
                        component=func.__name__,
                        cause=e
                    )
                else:
                    return default_return
        return wrapper
    return decorator


# 错误上下文管理器
class ErrorContext:
    """错误上下文管理器"""

    def __init__(self, operation: str, data_source: str = None):
        self.operation = operation
        self.data_source = data_source
        self.errors: List[NonPriceDataError] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None and issubclass(exc_type, Exception):
            error = SystemError(
                f"Error in {self.operation}: {str(exc_val)}",
                component=self.operation,
                cause=exc_val
            )
            self.errors.append(error)
            return True  # 抑制异常

    def add_error(self, error: NonPriceDataError):
        """添加错误"""
        self.errors.append(error)

    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0

    def get_errors(self) -> List[NonPriceDataError]:
        """获取所有错误"""
        return self.errors.copy()

    def raise_if_errors(self):
        """如果有错误则抛出"""
        if self.has_errors():
            if len(self.errors) == 1:
                raise self.errors[0]
            else:
                # 合并多个错误
                error_messages = [str(e) for e in self.errors]
                raise SystemError(
                    f"Multiple errors occurred in {self.operation}: {'; '.join(error_messages)}",
                    component=self.operation
                )
