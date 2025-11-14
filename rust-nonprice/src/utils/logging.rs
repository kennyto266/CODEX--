//! Structured JSON logging
//!
//! This module provides JSON-structured logging for audit trails
//! and machine-readable log analysis.

use std::fmt;
use chrono::Utc;
use serde::{Serialize, Deserialize};
use serde_json::{json, Value};
use std::collections::HashMap;

/// Log level
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Serialize, Deserialize)]
pub enum LogLevel {
    Trace,
    Debug,
    Info,
    Warn,
    Error,
}

impl fmt::Display for LogLevel {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            LogLevel::Trace => write!(f, "TRACE"),
            LogLevel::Debug => write!(f, "DEBUG"),
            LogLevel::Info => write!(f, "INFO"),
            LogLevel::Warn => write!(f, "WARN"),
            LogLevel::Error => write!(f, "ERROR"),
        }
    }
}

/// Log entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LogEntry {
    pub timestamp: chrono::DateTime<Utc>,
    pub level: LogLevel,
    pub module: String,
    pub message: String,
    pub context: HashMap<String, Value>,
}

impl LogEntry {
    /// Create a new log entry
    pub fn new(
        level: LogLevel,
        module: String,
        message: String,
    ) -> Self {
        Self {
            timestamp: Utc::now(),
            level,
            module,
            message,
            context: HashMap::new(),
        }
    }

    /// Add context to the log entry
    pub fn with_context(mut self, key: &str, value: Value) -> Self {
        self.context.insert(key.to_string(), value);
        self
    }

    /// Serialize to JSON string
    pub fn to_json(&self) -> Result<String, serde_json::Error> {
        serde_json::to_string(self)
    }
}

/// JSON logger
pub struct JsonLogger {
    min_level: LogLevel,
}

impl JsonLogger {
    pub fn new(min_level: LogLevel) -> Self {
        Self { min_level }
    }

    pub fn log(&self, entry: &LogEntry) {
        if entry.level >= self.min_level {
            if let Ok(json) = entry.to_json() {
                println!("{}", json);
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_log_level_display() {
        assert_eq!(LogLevel::Info.to_string(), "INFO");
        assert_eq!(LogLevel::Error.to_string(), "ERROR");
    }

    #[test]
    fn test_log_entry_creation() {
        let entry = LogEntry::new(
            LogLevel::Info,
            "test".to_string(),
            "test message".to_string(),
        );
        assert_eq!(entry.level, LogLevel::Info);
        assert_eq!(entry.module, "test");
        assert_eq!(entry.message, "test message");
    }
}
