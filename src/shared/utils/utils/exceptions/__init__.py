"""
Custom exceptions for the application
"""

class QuantSystemError(Exception):
    """Base exception for quantitative system"""
    pass

class DataAdapterError(QuantSystemError):
    """Data adapter specific errors"""
    pass

class APIError(QuantSystemError):
    """API related errors"""
    pass

class ValidationError(QuantSystemError):
    """Data validation errors"""
    pass

class ConfigurationError(QuantSystemError):
    """Configuration related errors"""
    pass
