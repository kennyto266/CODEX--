//! Strategy layer module
//!
//! This module contains strategy implementations, signal generation,
//! and parameter optimization.

pub mod traits;
pub mod signals;
pub mod optimizer;
pub mod combiner;

pub use traits::*;
pub use signals::*;
pub use optimizer::*;
pub use combiner::*;
