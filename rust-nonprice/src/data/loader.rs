//! Data loading utilities
//!
//! This module provides functions for loading non-price indicators
//! and stock price data from CSV files.

use crate::core::data::{NonPriceIndicator, OHLCV};
use crate::core::error::BacktestError;
use std::path::Path;

/// Load non-price indicators from CSV file
pub fn load_csv(path: &Path) -> Result<Vec<NonPriceIndicator>, BacktestError> {
    let file = std::fs::File::open(path)
        .map_err(|e| BacktestError::data_load_error(path.to_str().unwrap_or("unknown"), &e.to_string()))?;

    let mut rdr = csv::Reader::from_reader(file);
    let mut indicators = Vec::new();

    for (idx, result) in rdr.records().enumerate() {
        match result {
            Ok(record) => {
                if record.len() < 3 {
                    return Err(BacktestError::validation_error(
                        &format!("row {}", idx),
                        "insufficient columns (need at least 3: symbol, date, value)",
                    ));
                }

                let symbol = record[0].to_string();
                let date_str = record[1].to_string();
                let value_str = record[2].to_string();
                let source = if record.len() > 3 {
                    record[3].to_string()
                } else {
                    "unknown".to_string()
                };

                // Parse date
                let date = chrono::NaiveDate::parse_from_str(&date_str, "%Y-%m-%d")
                    .or_else(|_| chrono::NaiveDate::parse_from_str(&date_str, "%d/%m/%Y"))
                    .or_else(|_| chrono::NaiveDate::parse_from_str(&date_str, "%m/%d/%Y"))
                    .map_err(|e| {
                        BacktestError::validation_error(
                            &format!("row {}, date", idx),
                            &format!("invalid date format: {}", e),
                        )
                    })?;

                // Parse value
                let value = value_str.parse::<f64>().map_err(|e| {
                    BacktestError::validation_error(
                        &format!("row {}, value", idx),
                        &format!("invalid number: {}", e),
                    )
                })?;

                let indicator = NonPriceIndicator {
                    symbol,
                    date,
                    value,
                    quality: crate::core::data::DataQuality::Good,
                    source,
                    metadata: std::collections::HashMap::new(),
                };

                indicators.push(indicator);
            }
            Err(e) => {
                return Err(BacktestError::data_load_error(
                    path.to_str().unwrap_or("unknown"),
                    &format!("CSV parsing error at row {}: {}", idx, e),
                ));
            }
        }
    }

    Ok(indicators)
}

/// Load non-price indicators from Parquet file (simplified - requires actual implementation)
pub fn load_parquet(_path: &Path) -> Result<Vec<NonPriceIndicator>, BacktestError> {
    // Placeholder - Parquet loading would require polars
    Err(BacktestError::config_error("Parquet loading not implemented"))
}

/// Load stock price data for backtesting
pub fn load_stock_prices(path: &Path, symbol: &str) -> Result<Vec<OHLCV>, BacktestError> {
    let file = std::fs::File::open(path)
        .map_err(|e| BacktestError::data_load_error(path.to_str().unwrap_or("unknown"), &e.to_string()))?;

    let mut rdr = csv::Reader::from_reader(file);
    let mut prices = Vec::new();

    for (idx, result) in rdr.records().enumerate() {
        match result {
            Ok(record) => {
                if record.len() < 5 {
                    return Err(BacktestError::validation_error(
                        &format!("row {}", idx),
                        "insufficient columns (need 5: date, open, high, low, close, volume)",
                    ));
                }

                let date_str = record[0].to_string();
                let open_str = record[1].to_string();
                let high_str = record[2].to_string();
                let low_str = record[3].to_string();
                let close_str = record[4].to_string();
                let volume_str = if record.len() > 5 {
                    record[5].to_string()
                } else {
                    "0".to_string()
                };

                // Parse date
                let date = chrono::NaiveDate::parse_from_str(&date_str, "%Y-%m-%d")
                    .or_else(|_| chrono::NaiveDate::parse_from_str(&date_str, "%d/%m/%Y"))
                    .or_else(|_| chrono::NaiveDate::parse_from_str(&date_str, "%m/%d/%Y"))
                    .map_err(|e| {
                        BacktestError::validation_error(
                            &format!("row {}, date", idx),
                            &format!("invalid date format: {}", e),
                        )
                    })?;

                // Parse OHLC
                let open = open_str.parse::<f64>().map_err(|e| {
                    BacktestError::validation_error(
                        &format!("row {}, open", idx),
                        &format!("invalid number: {}", e),
                    )
                })?;

                let high = high_str.parse::<f64>().map_err(|e| {
                    BacktestError::validation_error(
                        &format!("row {}, high", idx),
                        &format!("invalid number: {}", e),
                    )
                })?;

                let low = low_str.parse::<f64>().map_err(|e| {
                    BacktestError::validation_error(
                        &format!("row {}, low", idx),
                        &format!("invalid number: {}", e),
                    )
                })?;

                let close = close_str.parse::<f64>().map_err(|e| {
                    BacktestError::validation_error(
                        &format!("row {}, close", idx),
                        &format!("invalid number: {}", e),
                    )
                })?;

                // Parse volume
                let volume = volume_str.parse::<u64>().unwrap_or(0);

                let ohlcv = OHLCV::new(
                    symbol.to_string(),
                    date,
                    open,
                    high,
                    low,
                    close,
                    volume,
                );

                // Validate OHLCV
                ohlcv.validate().map_err(|e| {
                    BacktestError::validation_error(
                        &format!("row {}", idx),
                        &format!("invalid OHLCV: {}", e),
                    )
                })?;

                prices.push(ohlcv);
            }
            Err(e) => {
                return Err(BacktestError::data_load_error(
                    path.to_str().unwrap_or("unknown"),
                    &format!("CSV parsing error at row {}: {}", idx, e),
                ));
            }
        }
    }

    // Sort by date
    prices.sort_by(|a, b| a.date.cmp(&b.date));

    Ok(prices)
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::NaiveDate;
    use tempfile::NamedTempFile;
    use std::io::Write;

    #[test]
    fn test_load_csv() {
        let mut temp_file = NamedTempFile::new().unwrap();
        writeln!(temp_file, "TEST_INDICATOR,2023-01-01,100.0,TEST").unwrap();
        writeln!(temp_file, "TEST_INDICATOR,2023-01-02,105.0,TEST").unwrap();

        let indicators = load_csv(temp_file.path()).unwrap();
        assert_eq!(indicators.len(), 2);
        assert_eq!(indicators[0].symbol, "TEST_INDICATOR");
        assert_eq!(indicators[0].value, 100.0);
    }

    #[test]
    fn test_load_stock_prices() {
        let mut temp_file = NamedTempFile::new().unwrap();
        writeln!(temp_file, "2023-01-01,100.0,105.0,95.0,102.0,1000000").unwrap();
        writeln!(temp_file, "2023-01-02,102.0,108.0,101.0,106.0,1500000").unwrap();

        let prices = load_stock_prices(temp_file.path(), "TEST").unwrap();
        assert_eq!(prices.len(), 2);
        assert_eq!(prices[0].symbol, "TEST");
        assert_eq!(prices[0].close, 102.0);
    }
}
