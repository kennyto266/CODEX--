//! Core module containing fundamental data structures and types
//!
//! This module is the foundation of the system, defining all core types
//! that are used throughout the codebase.

pub mod data;
pub mod backtest;
pub mod error;
pub mod validators;

pub use data::*;
pub use backtest::*;
pub use error::BacktestError;
pub use validators::*;
