//! Data validation utilities
//!
//! This module provides validation functions for data integrity,
//! missing data handling, and quality assessment.

use crate::core::data::{DataQuality, NonPriceIndicator};
use chrono::NaiveDate;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Data validation report
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationReport {
    pub total_records: usize,
    pub valid_count: usize,
    pub invalid_count: usize,
    pub issues: Vec<ValidationIssue>,
    pub data_quality_score: f64,
}

/// Individual validation issue
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationIssue {
    pub row: usize,
    pub field: String,
    pub issue: String,
    pub severity: String,
}

/// Interpolation method for handling missing data
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum InterpolationMethod {
    ForwardFill,
    BackwardFill,
    Linear,
    Mean,
    Median,
}

impl InterpolationMethod {
    /// Get method name
    pub fn name(&self) -> &'static str {
        match self {
            InterpolationMethod::ForwardFill => "Forward Fill",
            InterpolationMethod::BackwardFill => "Backward Fill",
            InterpolationMethod::Linear => "Linear",
            InterpolationMethod::Mean => "Mean",
            InterpolationMethod::Median => "Median",
        }
    }
}

/// Validate a single non-price indicator
pub fn validate_indicator(indicator: &NonPriceIndicator) -> Result<(), ValidationIssue> {
    // Check if value is finite
    if !indicator.value.is_finite() {
        return Err(ValidationIssue {
            row: 0,
            field: "value".to_string(),
            issue: "Value is not finite (NaN or Infinity)".to_string(),
            severity: "ERROR".to_string(),
        });
    }

    // Check date range
    let year_str = indicator.date.format("%Y").to_string();
    let year: i32 = year_str.parse().unwrap_or(0);
    if year < 1900 || year > 2100 {
        return Err(ValidationIssue {
            row: 0,
            field: "date".to_string(),
            issue: "Date outside valid range (1900-2100)".to_string(),
            severity: "ERROR".to_string(),
        });
    }

    // Check symbol format (uppercase with underscores)
    if !indicator.symbol.chars().all(|c| c.is_ascii_uppercase() || c == '_') {
        return Err(ValidationIssue {
            row: 0,
            field: "symbol".to_string(),
            issue: "Symbol must be uppercase with underscores only".to_string(),
            severity: "ERROR".to_string(),
        });
    }

    Ok(())
}

/// Validate entire dataset
pub fn validate(data: &[NonPriceIndicator]) -> Result<ValidationReport, crate::core::error::BacktestError> {
    let mut report = ValidationReport {
        total_records: data.len(),
        valid_count: 0,
        invalid_count: 0,
        issues: Vec::new(),
        data_quality_score: 0.0,
    };

    for (idx, indicator) in data.iter().enumerate() {
        match validate_indicator(indicator) {
            Ok(_) => {
                report.valid_count += 1;
            }
            Err(issue) => {
                let mut issue = issue;
                issue.row = idx;
                report.invalid_count += 1;
                report.issues.push(issue);
            }
        }
    }

    // Calculate quality score
    if report.total_records > 0 {
        report.data_quality_score = report.valid_count as f64 / report.total_records as f64;
    }

    Ok(report)
}

/// Assess data quality
pub fn assess_quality(data: &[NonPriceIndicator]) -> DataQuality {
    if data.is_empty() {
        return DataQuality::Rejected;
    }

    let mut valid_count = 0;
    let mut total_value = 0.0;
    let mut values = Vec::new();

    for indicator in data {
        if indicator.is_valid() {
            valid_count += 1;
            total_value += indicator.value;
            values.push(indicator.value);
        }
    }

    let validity_ratio = valid_count as f64 / data.len() as f64;

    if validity_ratio >= 0.99 {
        DataQuality::Good
    } else if validity_ratio >= 0.95 {
        DataQuality::Fair
    } else if validity_ratio >= 0.80 {
        DataQuality::Poor
    } else {
        DataQuality::Rejected
    }
}

/// Detect missing data points
pub fn detect_missing_data(data: &[NonPriceIndicator]) -> Vec<NaiveDate> {
    if data.len() < 2 {
        return Vec::new();
    }

    let mut missing = Vec::new();
    let mut sorted_data = data.to_vec();
    sorted_data.sort_by(|a, b| a.date.cmp(&b.date));

    // Check for gaps in dates
    for i in 1..sorted_data.len() {
        let prev_date = sorted_data[i - 1].date;
        let curr_date = sorted_data[i].date;
        let days_diff = (curr_date - prev_date).num_days();

        // If gap > 1 day, add intermediate dates as missing
        if days_diff > 1 {
            for day in 1..days_diff {
                missing.push(prev_date + chrono::Duration::days(day));
            }
        }
    }

    missing
}

/// Handle missing data using specified interpolation method
pub fn interpolate_missing(
    data: &mut [NonPriceIndicator],
    method: InterpolationMethod,
) -> Result<(), crate::core::error::BacktestError> {
    if data.is_empty() {
        return Ok(());
    }

    // Sort by date
    data.sort_by(|a, b| a.date.cmp(&b.date));

    match method {
        InterpolationMethod::ForwardFill => forward_fill(data),
        InterpolationMethod::BackwardFill => backward_fill(data),
        InterpolationMethod::Linear => linear_interpolation(data),
        InterpolationMethod::Mean => mean_fill(data),
        InterpolationMethod::Median => median_fill(data),
    }
}

/// Forward fill missing values
fn forward_fill(data: &mut [NonPriceIndicator]) -> Result<(), crate::core::error::BacktestError> {
    let mut last_valid_value = None;

    for indicator in data {
        if indicator.is_valid() {
            last_valid_value = Some(indicator.value);
        } else if let Some(value) = last_valid_value {
            indicator.value = value;
            indicator.quality = crate::core::data::DataQuality::Fair;
        }
    }

    Ok(())
}

/// Backward fill missing values
fn backward_fill(data: &mut [NonPriceIndicator]) -> Result<(), crate::core::error::BacktestError> {
    let mut next_valid_value = None;

    for i in (0..data.len()).rev() {
        if data[i].is_valid() {
            next_valid_value = Some(data[i].value);
        } else if let Some(value) = next_valid_value {
            data[i].value = value;
            data[i].quality = crate::core::data::DataQuality::Fair;
        }
    }

    Ok(())
}

/// Linear interpolation for missing values
fn linear_interpolation(data: &mut [NonPriceIndicator]) -> Result<(), crate::core::error::BacktestError> {
    let n = data.len();
    let mut i = 0;

    while i < n {
        // Find start of missing sequence
        if data[i].is_valid() {
            i += 1;
            continue;
        }

        // Find previous valid point
        let mut start_idx = i;
        while start_idx > 0 && !data[start_idx - 1].is_valid() {
            start_idx -= 1;
        }

        // Find next valid point
        let mut end_idx = i;
        while end_idx < n && !data[end_idx].is_valid() {
            end_idx += 1;
        }

        // Interpolate if we have valid points on both sides
        if start_idx > 0 && end_idx < n {
            let start_value = data[start_idx - 1].value;
            let end_value = data[end_idx].value;
            let start_date = data[start_idx - 1].date;
            let end_date = data[end_idx].date;
            let total_days = (end_date - start_date).num_days() as f64;

            for j in start_idx..end_idx {
                let current_date = data[j].date;
                let days_from_start = (current_date - start_date).num_days() as f64;
                let ratio = days_from_start / total_days;
                data[j].value = start_value + ratio * (end_value - start_value);
                data[j].quality = crate::core::data::DataQuality::Fair;
            }
        } else {
            // Use forward fill if no valid endpoint
            forward_fill(&mut data[start_idx..end_idx])?;
        }

        i = end_idx;
    }

    Ok(())
}

/// Mean fill for missing values
fn mean_fill(data: &mut [NonPriceIndicator]) -> Result<(), crate::core::error::BacktestError> {
    let valid_values: Vec<f64> = data
        .iter()
        .filter(|i| i.is_valid())
        .map(|i| i.value)
        .collect();

    if valid_values.is_empty() {
        return Err(crate::core::error::BacktestError::insufficient_data(1, 0));
    }

    let mean = valid_values.iter().sum::<f64>() / valid_values.len() as f64;

    for indicator in data.iter_mut() {
        if !indicator.is_valid() {
            indicator.value = mean;
            indicator.quality = crate::core::data::DataQuality::Fair;
        }
    }

    Ok(())
}

/// Median fill for missing values
fn median_fill(data: &mut [NonPriceIndicator]) -> Result<(), crate::core::error::BacktestError> {
    let mut valid_values: Vec<f64> = data
        .iter()
        .filter(|i| i.is_valid())
        .map(|i| i.value)
        .collect();

    if valid_values.is_empty() {
        return Err(crate::core::error::BacktestError::insufficient_data(1, 0));
    }

    valid_values.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let median = if valid_values.len() % 2 == 0 {
        let mid = valid_values.len() / 2;
        (valid_values[mid - 1] + valid_values[mid]) / 2.0
    } else {
        valid_values[valid_values.len() / 2]
    };

    for indicator in data.iter_mut() {
        if !indicator.is_valid() {
            indicator.value = median;
            indicator.quality = crate::core::data::DataQuality::Fair;
        }
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::NaiveDate;

    #[test]
    fn test_validate_indicator_valid() {
        let indicator = NonPriceIndicator::new(
            "TEST_INDICATOR".to_string(),
            NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(),
            100.0,
            "TEST".to_string(),
        );
        assert!(validate_indicator(&indicator).is_ok());
    }

    #[test]
    fn test_validate_indicator_invalid_value() {
        let mut indicator = NonPriceIndicator::new(
            "TEST_INDICATOR".to_string(),
            NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(),
            100.0,
            "TEST".to_string(),
        );
        indicator.value = f64::NAN;
        assert!(validate_indicator(&indicator).is_err());
    }

    #[test]
    fn test_assess_quality() {
        let mut data = vec![
            NonPriceIndicator::new("T1".to_string(), NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(), 100.0, "T".to_string()),
            NonPriceIndicator::new("T2".to_string(), NaiveDate::from_ymd_opt(2023, 1, 2).unwrap(), 200.0, "T".to_string()),
        ];
        data[1].value = f64::NAN;

        let quality = assess_quality(&data);
        assert_eq!(quality, DataQuality::Fair);
    }
}
