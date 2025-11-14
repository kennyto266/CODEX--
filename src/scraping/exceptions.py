"""
Exception classes for the scraping module

Defines custom exceptions for NLP processing, configuration generation,
and scraping execution errors.
"""


class ScrapingBaseException(Exception):
    """Base exception for all scraping-related errors"""

    def __init__(self, message: str, error_code: str = None, context: dict = None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__.upper()
        self.context = context or {}
        super().__init__(message)

    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class NLPProcessingError(ScrapingBaseException):
    """Exception raised when natural language processing fails"""

    def __init__(self, message: str, description: str = None, error_code: str = "NLP_001"):
        self.description = description
        super().__init__(message, error_code)


class ConfigurationGenerationError(ScrapingBaseException):
    """Exception raised when pipet configuration generation fails"""

    def __init__(self, message: str, nlp_result=None, config_id=None, error_code: str = "CONFIG_001"):
        self.nlp_result = nlp_result
        self.config_id = config_id
        super().__init__(message, error_code)


class ValidationError(ScrapingBaseException):
    """Exception raised when configuration validation fails"""

    def __init__(self, message: str, validation_issues: list = None, error_code: str = "VAL_001"):
        self.validation_issues = validation_issues or []
        super().__init__(message, error_code)


class ExecutionError(ScrapingBaseException):
    """Exception raised when pipet execution fails"""

    def __init__(self, message: str, execution_id: str = None, config_id: str = None,
                 exit_code: int = None, error_code: str = "EXEC_001"):
        self.execution_id = execution_id
        self.config_id = config_id
        self.exit_code = exit_code
        super().__init__(message, error_code)


class BatchExecutionError(ScrapingBaseException):
    """Exception raised when batch execution fails"""

    def __init__(self, message: str, batch_id: str = None, failed_executions: list = None,
                 error_code: str = "BATCH_001"):
        self.batch_id = batch_id
        self.failed_executions = failed_executions or []
        super().__init__(message, error_code)


class ResourceError(ScrapingBaseException):
    """Exception raised when resource limits are exceeded"""

    def __init__(self, message: str, resource_type: str = None, current_usage: float = None,
                 limit: float = None, error_code: str = "RESOURCE_001"):
        self.resource_type = resource_type
        self.current_usage = current_usage
        self.limit = limit
        super().__init__(message, error_code)


class TimeoutError(ScrapingBaseException):
    """Exception raised when operations exceed timeout"""

    def __init__(self, message: str, timeout_duration: float = None, operation_type: str = None,
                 error_code: str = "TIMEOUT_001"):
        self.timeout_duration = timeout_duration
        self.operation_type = operation_type
        super().__init__(message, error_code)


class NetworkError(ScrapingBaseException):
    """Exception raised when network operations fail"""

    def __init__(self, message: str, url: str = None, status_code: int = None,
                 error_code: str = "NETWORK_001"):
        self.url = url
        self.status_code = status_code
        super().__init__(message, error_code)


class DataQualityError(ScrapingBaseException):
    """Exception raised when data quality issues are detected"""

    def __init__(self, message: str, quality_score: float = None, quality_issues: list = None,
                 error_code: str = "QUALITY_001"):
        self.quality_score = quality_score
        self.quality_issues = quality_issues or []
        super().__init__(message, error_code)


class OptimizationError(ScrapingBaseException):
    """Exception raised when configuration optimization fails"""

    def __init__(self, message: str, optimization_goals: list = None, error_code: str = "OPT_001"):
        self.optimization_goals = optimization_goals or []
        super().__init__(message, error_code)


class CancellationError(ScrapingBaseException):
    """Exception raised when operation is cancelled"""

    def __init__(self, message: str, execution_id: str = None, reason: str = None,
                 error_code: str = "CANCEL_001"):
        self.execution_id = execution_id
        self.reason = reason
        super().__init__(message, error_code)


class MonitoringError(ScrapingBaseException):
    """Exception raised when monitoring operations fail"""

    def __init__(self, message: str, metric_name: str = None, error_code: str = "MONITOR_001"):
        self.metric_name = metric_name
        super().__init__(message, error_code)


# Exception mapping for error handling
ERROR_MAPPING = {
    "nlp_processing": NLPProcessingError,
    "config_generation": ConfigurationGenerationError,
    "validation": ValidationError,
    "execution": ExecutionError,
    "batch_execution": BatchExecutionError,
    "resource": ResourceError,
    "timeout": TimeoutError,
    "network": NetworkError,
    "data_quality": DataQualityError,
    "optimization": OptimizationError,
    "cancellation": CancellationError,
    "monitoring": MonitoringError,
}


def create_error(error_type: str, message: str, **kwargs) -> ScrapingBaseException:
    """
    Create an appropriate error instance based on error type

    Args:
        error_type: Type of error
        message: Error message
        **kwargs: Additional error-specific parameters

    Returns:
        ScrapingBaseException instance
    """
    error_class = ERROR_MAPPING.get(error_type, ScrapingBaseException)
    return error_class(message, **kwargs)