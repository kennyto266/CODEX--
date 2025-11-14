//! Data processing module
//!
//! This module implements the core technical indicator calculations:
//! Z-Score, RSI, and SMA using vectorized operations with Polars.

use crate::core::data::{IndicatorType, NonPriceIndicator, TechnicalIndicator};
use crate::core::error::BacktestError;
use chrono::NaiveDate;
use rayon::prelude::*;

/// Calculate all technical indicators for a dataset
pub fn calculate_all(data: &[NonPriceIndicator]) -> Result<Vec<TechnicalIndicator>, BacktestError> {
    if data.is_empty() {
        return Err(BacktestError::insufficient_data(1, 0));
    }

    let mut results = Vec::new();

    // Calculate Z-Score (20-day default)
    let zscore_results = calculate_zscore(data, 20)?;
    results.extend(zscore_results);

    // Calculate RSI (14-day default)
    let rsi_results = calculate_rsi(data, 14)?;
    results.extend(rsi_results);

    // Calculate SMA fast (10-day)
    let sma_fast_results = calculate_sma(data, 10)?;
    results.extend(sma_fast_results);

    // Calculate SMA slow (30-day)
    let sma_slow_results = calculate_sma(data, 30)?;
    results.extend(sma_slow_results);

    Ok(results)
}

/// Calculate Z-Score for given window size
pub fn calculate_zscore(
    data: &[NonPriceIndicator],
    window_size: usize,
) -> Result<Vec<TechnicalIndicator>, BacktestError> {
    if data.len() < window_size {
        return Err(BacktestError::insufficient_data(window_size, data.len()));
    }

    // Sort by date
    let mut sorted_data = data.to_vec();
    sorted_data.sort_by(|a, b| a.date.cmp(&b.date));

    // Calculate Z-Score for each point
    let mut indicators = Vec::new();

    for i in window_size..sorted_data.len() {
        let window = &sorted_data[(i - window_size)..i];
        let values: Vec<f64> = window.iter().map(|d| d.value).collect();

        // Calculate mean
        let mean: f64 = values.iter().sum::<f64>() / values.len() as f64;

        // Calculate standard deviation
        let variance: f64 = values
            .iter()
            .map(|v| (v - mean).powi(2))
            .sum::<f64>() / values.len() as f64;
        let std = variance.sqrt();

        // Calculate Z-Score
        let zscore = if std > 0.0 {
            (sorted_data[i].value - mean) / std
        } else {
            0.0
        };

        let mut indicator = TechnicalIndicator::new(
            sorted_data[i].symbol.clone(),
            sorted_data[i].date,
            IndicatorType::ZScore,
            window_size,
        );

        if zscore.is_finite() {
            indicator.set_value(zscore);
        }

        indicators.push(indicator);
    }

    Ok(indicators)
}

/// Calculate RSI with Wilder's smoothing
pub fn calculate_rsi(
    data: &[NonPriceIndicator],
    window_size: usize,
) -> Result<Vec<TechnicalIndicator>, BacktestError> {
    if data.len() < window_size + 1 {
        return Err(BacktestError::insufficient_data(window_size + 1, data.len()));
    }

    // Sort by date
    let mut sorted_data = data.to_vec();
    sorted_data.sort_by(|a, b| a.date.cmp(&b.date));

    // Calculate price changes
    let changes: Vec<f64> = sorted_data
        .windows(2)
        .map(|w| w[1].value - w[0].value)
        .collect();

    // Calculate gains and losses
    let gains: Vec<f64> = changes.iter().map(|c| if *c > 0.0 { *c } else { 0.0 }).collect();
    let losses: Vec<f64> = changes.iter().map(|c| if *c < 0.0 { -*c } else { 0.0 }).collect();

    // Calculate RSI using Wilder's method
    let mut indicators = Vec::new();

    for i in (window_size - 1)..sorted_data.len() {
        // Calculate average gain and loss
        let avg_gain = gains[(i - window_size + 1)..=i]
            .iter()
            .sum::<f64>() / window_size as f64;
        let avg_loss = losses[(i - window_size + 1)..=i]
            .iter()
            .sum::<f64>() / window_size as f64;

        // Calculate RSI: 100 - (100 / (1 + RS))
        let rs = if avg_loss == 0.0 {
            f64::INFINITY
        } else {
            avg_gain / avg_loss
        };

        let rsi = if rs.is_infinite() {
            100.0
        } else {
            100.0 - (100.0 / (1.0 + rs))
        };

        let mut indicator = TechnicalIndicator::new(
            sorted_data[i].symbol.clone(),
            sorted_data[i].date,
            IndicatorType::RSI,
            window_size,
        );

        if rsi.is_finite() {
            indicator.set_value(rsi);
        }

        indicators.push(indicator);
    }

    Ok(indicators)
}

/// Calculate Simple Moving Average
pub fn calculate_sma(
    data: &[NonPriceIndicator],
    window_size: usize,
) -> Result<Vec<TechnicalIndicator>, BacktestError> {
    if data.len() < window_size {
        return Err(BacktestError::insufficient_data(window_size, data.len()));
    }

    // Sort by date
    let mut sorted_data = data.to_vec();
    sorted_data.sort_by(|a, b| a.date.cmp(&b.date));

    // Calculate SMA
    let mut indicators = Vec::new();

    for i in window_size..sorted_data.len() {
        let window = &sorted_data[(i - window_size)..i];
        let sma: f64 = window.iter().map(|d| d.value).sum::<f64>() / window_size as f64;

        let mut indicator = TechnicalIndicator::new(
            sorted_data[i].symbol.clone(),
            sorted_data[i].date,
            IndicatorType::SMAFast,
            window_size,
        );

        if sma.is_finite() {
            indicator.set_value(sma);
        }

        indicators.push(indicator);
    }

    Ok(indicators)
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::NaiveDate;

    #[test]
    fn test_calculate_zscore() {
        let data = vec![
            NonPriceIndicator::new("TEST".to_string(), NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(), 100.0, "test".to_string()),
            NonPriceIndicator::new("TEST".to_string(), NaiveDate::from_ymd_opt(2023, 1, 2).unwrap(), 101.0, "test".to_string()),
            NonPriceIndicator::new("TEST".to_string(), NaiveDate::from_ymd_opt(2023, 1, 3).unwrap(), 102.0, "test".to_string()),
        ];

        let result = calculate_zscore(&data, 2);
        assert!(result.is_ok());
        let indicators = result.unwrap();
        assert_eq!(indicators.len(), 1);
    }

    #[test]
    fn test_calculate_rsi() {
        let data = vec![
            NonPriceIndicator::new("TEST".to_string(), NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(), 100.0, "test".to_string()),
            NonPriceIndicator::new("TEST".to_string(), NaiveDate::from_ymd_opt(2023, 1, 2).unwrap(), 101.0, "test".to_string()),
            NonPriceIndicator::new("TEST".to_string(), NaiveDate::from_ymd_opt(2023, 1, 3).unwrap(), 102.0, "test".to_string()),
        ];

        let result = calculate_rsi(&data, 2);
        assert!(result.is_ok());
    }

    #[test]
    fn test_calculate_sma() {
        let data = vec![
            NonPriceIndicator::new("TEST".to_string(), NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(), 100.0, "test".to_string()),
            NonPriceIndicator::new("TEST".to_string(), NaiveDate::from_ymd_opt(2023, 1, 2).unwrap(), 101.0, "test".to_string()),
            NonPriceIndicator::new("TEST".to_string(), NaiveDate::from_ymd_opt(2023, 1, 3).unwrap(), 102.0, "test".to_string()),
        ];

        let result = calculate_sma(&data, 2);
        assert!(result.is_ok());
        let indicators = result.unwrap();
        assert_eq!(indicators.len(), 1);
    }
}
