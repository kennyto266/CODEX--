//! Data validation module
//!
//! This module provides data validation functions re-exported from core::validators

pub use crate::core::validators::{
    validate, validate_indicator, assess_quality, detect_missing_data, interpolate_missing,
    InterpolationMethod, ValidationReport, ValidationIssue,
};
