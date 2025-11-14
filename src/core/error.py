"""Error types and exceptions for the quantitative trading system.

This module defines all custom exception types used throughout the system.
"""

from typing import Any, Dict, Optional


class QuantError(Exception):
    """Base exception for all quantitative trading system errors.
    
    All custom exceptions in the system should inherit from this class.
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize QuantError.
        
        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        """String representation."""
        return self.message
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"{self.__class__.__name__}({self.message})"


class DataError(QuantError):
    """Raised when there's an error with data handling.
    
    This includes:
    - Invalid data format
    - Missing required columns
    - Data quality issues
    - API errors
    """
    pass


class ValidationError(QuantError):
    """Raised when data validation fails.
    
    This includes:
    - Invalid parameter values
    - Missing required fields
    - Data type mismatches
    """
    pass


class BacktestError(QuantError):
    """Raised when there's an error during backtesting.
    
    This includes:
    - Invalid strategy parameters
    - Insufficient data
    - Execution errors
    """
    pass


class OptimizationError(QuantError):
    """Raised when there's an error during parameter optimization.
    
    This includes:
    - Invalid parameter grid
    - Optimization convergence issues
    - Performance metric errors
    """
    pass


class StrategyError(QuantError):
    """Raised when there's an error in strategy execution.
    
    This includes:
    - Invalid indicator parameters
    - Signal generation errors
    - Strategy logic errors
    """
    pass


class DataNotFoundError(DataError):
    """Raised when requested data is not available.
    
    This includes:
    - Symbol not found
    - Date range not available
    - Missing historical data
    """
    pass


class InsufficientDataError(DataError):
    """Raised when there isn't enough data to perform analysis.
    
    Args:
        required: Number of data points required
        available: Number of data points available
    """
    
    def __init__(self, message: str, required: int, available: int):
        """Initialize InsufficientDataError.
        
        Args:
            message: Error message
            required: Required data points
            available: Available data points
        """
        super().__init__(message)
        self.required = required
        self.available = available
