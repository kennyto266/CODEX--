//! Basic usage example for rust-nonprice
//!
//! This example demonstrates the core functionality of the rust-nonprice library

use rust_nonprice::*;
use chrono::NaiveDate;
use std::path::Path;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("=== Rust-NonPrice Basic Usage Example ===\n");

    // Create sample non-price data
    let data = create_sample_data();

    // Validate data
    println!("1. Validating data...");
    let validation_report = api::validate_data(&data)?;
    println!("   Total records: {}", validation_report.total_records);
    println!("   Valid records: {}", validation_report.valid_count);
    println!("   Data quality score: {:.2}%\n", validation_report.data_quality_score);

    // Calculate technical indicators
    println!("2. Calculating technical indicators...");

    // Calculate Z-Score
    let zscore_indicators = api::calculate_zscore(&data, 20)?;
    println!("   Z-Score indicators: {}", zscore_indicators.len());

    // Calculate RSI
    let rsi_indicators = api::calculate_rsi(&data, 14)?;
    println!("   RSI indicators: {}", rsi_indicators.len());

    // Calculate SMA
    let sma_indicators = api::calculate_sma(&data, 30)?;
    println!("   SMA indicators: {}\n", sma_indicators.len());

    // Create parameter set
    println!("3. Creating parameter set...");
    let params = ParameterSet::default();
    println!("   Parameter set ID: {}", params.id);
    println!("   Z-Score buy threshold: {}", params.zscore_buy);
    println!("   Z-Score sell threshold: {}\n", params.zscore_sell);

    // Generate trading signals
    println!("4. Generating trading signals...");
    let all_indicators = vec![
        zscore_indicators,
        rsi_indicators,
        sma_indicators,
    ];

    // Combine all indicators
    let combined_indicators: Vec<TechnicalIndicator> = all_indicators
        .into_iter()
        .flatten()
        .collect();

    let signals = api::generate_signals(&combined_indicators, &params)?;
    println!("   Generated {} trading signals\n", signals.len());

    // Create sample stock data
    println!("5. Creating sample stock data...");
    let stock_data = create_sample_stock_data();
    println!("   Stock data points: {}\n", stock_data.len());

    // Run backtest
    println!("6. Running backtest...");
    let config = BacktestConfig {
        initial_capital: 1_000_000.0,
        commission: 0.001,
        position_sizing: PositionSizing::Fixed,
        risk_free_rate: 0.02,
    };

    let backtest_result = api::run_backtest(&signals, &stock_data, &config)?;
    println!("   Backtest completed!");
    println!("   Total return: {:.2}%", backtest_result.total_return * 100.0);
    println!("   Sharpe ratio: {:.2}", backtest_result.sharpe_ratio);
    println!("   Max drawdown: {:.2}%\n", backtest_result.max_drawdown * 100.0);

    // Generate report
    println!("7. Generating report...");
    let report_path = Path::new("backtest_report.md");
    api::generate_markdown_report(&backtest_result, report_path)?;
    println!("   Report generated: {:?}\n", report_path);

    println!("=== Example completed successfully! ===");
    Ok(())
}

fn create_sample_data() -> Vec<NonPriceIndicator> {
    let mut data = Vec::new();
    let start_date = NaiveDate::from_ymd_opt(2024, 1, 1).unwrap();

    for i in 0..100 {
        let date = start_date + chrono::Duration::days(i as i64);
        let value = 3.0 + (i as f64 * 0.01).sin() * 0.5; // Simulated HIBOR

        data.push(NonPriceIndicator::new(
            "HIBOR_1M".to_string(),
            date,
            value,
            "HKMA".to_string(),
        ));
    }

    data
}

fn create_sample_stock_data() -> Vec<OHLCV> {
    let mut data = Vec::new();
    let start_date = NaiveDate::from_ymd_opt(2024, 1, 1).unwrap();

    let mut price = 380.0;

    for i in 0..100 {
        let date = start_date + chrono::Duration::days(i as i64);
        price += (i as f64 * 0.01).sin() * 2.0; // Simulate price movement

        data.push(OHLCV {
            symbol: "0700.HK".to_string(),
            date,
            open: price - 1.0,
            high: price + 2.0,
            low: price - 2.0,
            close: price,
            volume: 1000000,
        });
    }

    data
}
