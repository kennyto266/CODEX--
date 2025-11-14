//! Error types for the non-price data system
//!
//! This module defines the `BacktestError` enum and related error types.
//! All APIs use `Result<T, BacktestError>` for error handling - no unwrap()/panic!

use chrono::NaiveDate;
use std::fmt;
use thiserror::Error;

/// Main error type for the backtest system
#[derive(Error, Debug)]
pub enum BacktestError {
    #[error("Insufficient data: needed {needed}, have {have}")]
    InsufficientData {
        needed: usize,
        have: usize,
    },

    #[error("Invalid price: {price} on {date}")]
    InvalidPrice {
        price: f64,
        date: NaiveDate,
    },

    #[error("Calculation overflow in {operation}: {value}")]
    CalculationOverflow {
        operation: String,
        value: f64,
    },

    #[error("Optimization timeout after {elapsed:?}")]
    OptimizationTimeout {
        elapsed: std::time::Duration,
    },

    #[error("Data load error: {message}")]
    DataLoadError {
        message: String,
    },

    #[error("Validation error for {field}: {reason}")]
    ValidationError {
        field: String,
        reason: String,
    },

    #[error("IO error: {message}")]
    IoError {
        message: String,
    },

    #[error("JSON serialization error: {message}")]
    JsonError {
        message: String,
    },

    #[error("Parallel processing error: {message}")]
    ParallelError {
        message: String,
    },

    #[error("Configuration error: {message}")]
    ConfigError {
        message: String,
    },
}

impl BacktestError {
    /// Create an insufficient data error
    pub fn insufficient_data(needed: usize, have: usize) -> Self {
        Self::InsufficientData { needed, have }
    }

    /// Create an invalid price error
    pub fn invalid_price(price: f64, date: NaiveDate) -> Self {
        Self::InvalidPrice { price, date }
    }

    /// Create a calculation overflow error
    pub fn calculation_overflow(operation: String, value: f64) -> Self {
        Self::CalculationOverflow { operation, value }
    }

    /// Create a data load error
    pub fn data_load_error(source: &str, error: &str) -> Self {
        Self::DataLoadError {
            message: format!("{}: {}", source, error),
        }
    }

    /// Create a validation error
    pub fn validation_error(field: &str, reason: &str) -> Self {
        Self::ValidationError {
            field: field.to_string(),
            reason: reason.to_string(),
        }
    }

    /// Create an IO error
    pub fn io_error(message: &str) -> Self {
        Self::IoError {
            message: message.to_string(),
        }
    }

    /// Create a JSON error
    pub fn json_error(message: &str) -> Self {
        Self::JsonError {
            message: message.to_string(),
        }
    }

    /// Create a parallel error
    pub fn parallel_error(message: &str) -> Self {
        Self::ParallelError {
            message: message.to_string(),
        }
    }

    /// Create a configuration error
    pub fn config_error(message: &str) -> Self {
        Self::ConfigError {
            message: message.to_string(),
        }
    }
}

impl From<std::io::Error> for BacktestError {
    fn from(error: std::io::Error) -> Self {
        Self::IoError {
            message: error.to_string(),
        }
    }
}

impl From<serde_json::Error> for BacktestError {
    fn from(error: serde_json::Error) -> Self {
        Self::JsonError {
            message: error.to_string(),
        }
    }
}

impl From<csv::Error> for BacktestError {
    fn from(error: csv::Error) -> Self {
        Self::DataLoadError {
            message: format!("CSV: {}", error),
        }
    }
}

impl From<polars::prelude::PolarsError> for BacktestError {
    fn from(error: polars::prelude::PolarsError) -> Self {
        Self::DataLoadError {
            message: format!("Polars: {}", error),
        }
    }
}

impl From<std::time::SystemTimeError> for BacktestError {
    fn from(error: std::time::SystemTimeError) -> Self {
        Self::IoError {
            message: error.to_string(),
        }
    }
}

impl From<rayon::ThreadPoolBuildError> for BacktestError {
    fn from(error: rayon::ThreadPoolBuildError) -> Self {
        Self::ParallelError {
            message: error.to_string(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::NaiveDate;

    #[test]
    fn test_error_creation() {
        let error = BacktestError::insufficient_data(100, 50);
        assert!(matches!(error, BacktestError::InsufficientData { .. }));

        let error = BacktestError::validation_error("field", "invalid");
        assert!(matches!(error, BacktestError::ValidationError { .. }));
    }

    #[test]
    fn test_error_display() {
        let error = BacktestError::insufficient_data(100, 50);
        let message = format!("{}", error);
        assert!(message.contains("Insufficient data"));
        assert!(message.contains("needed 100"));
        assert!(message.contains("have 50"));
    }
}
