//! Parameter optimization example for rust-nonprice
//!
//! This example demonstrates how to optimize trading parameters
//! using different optimization metrics

use rust_nonprice::*;
use std::path::Path;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("=== Rust-NonPrice Parameter Optimization Example ===\n");

    // Create sample data
    let data = create_sample_data();
    let stock_data = create_sample_stock_data();

    // Set up optimization configuration
    let config = OptimizationConfig {
        metric: OptimizationMetric::SharpeRatio,
        max_iterations: 1000,
        tolerance: 0.0001,
        parallel: true,
    };

    println!("1. Calculating all indicators...");
    let all_indicators = api::calculate_all_indicators(&data)?;
    println!("   Total indicators: {}\n", all_indicators.len());

    // Optimize parameters for each metric
    optimize_for_metric(&all_indicators, &stock_data, &config, "Sharpe Ratio", OptimizationMetric::SharpeRatio)?;
    optimize_for_metric(&all_indicators, &stock_data, &config, "Total Return", OptimizationMetric::TotalReturn)?;
    optimize_for_metric(&all_indicators, &stock_data, &config, "Max Drawdown", OptimizationMetric::MaxDrawdown)?;

    println!("=== Optimization completed successfully! ===");
    Ok(())
}

fn optimize_for_metric(
    indicators: &[Vec<TechnicalIndicator>],
    stock_data: &[OHLCV],
    config: &OptimizationConfig,
    metric_name: &str,
    metric: OptimizationMetric,
) -> Result<(), Box<dyn std::error::Error>> {
    println!("2. Optimizing for {}...", metric_name);

    let mut optimized_config = config.clone();
    optimized_config.metric = metric;

    // Optimize all indicators
    let result = api::optimize_all_indicators(indicators, stock_data, &optimized_config)?;

    println!("   Best result:");
    println!("     Metric value: {:.4}", result.best_metric_value);
    println!("     Best parameters:");
    println!("       Z-Score: buy={:.2}, sell={:.2}",
        result.best_parameters.zscore_buy,
        result.best_parameters.zscore_sell);
    println!("       RSI: buy={:.2}, sell={:.2}",
        result.best_parameters.rsi_buy,
        result.best_parameters.rsi_sell);
    println!("       SMA: fast={}, slow={}",
        result.best_parameters.sma_fast,
        result.best_parameters.sma_slow);
    println!("     Backtest return: {:.2}%", result.backtest_result.total_return * 100.0);
    println!("     Sharpe ratio: {:.2}", result.backtest_result.sharpe_ratio);
    println!("     Max drawdown: {:.2}%\n", result.backtest_result.max_drawdown * 100.0);

    // Save results
    let results_path = format!("optimization_results_{}.json", metric_name.to_lowercase().replace(' ', "_"));
    let report_path = Path::new(&results_path);
    api::generate_json_report(&result.backtest_result, report_path)?;
    println!("   Results saved to: {:?}\n", report_path);

    Ok(())
}

fn create_sample_data() -> Vec<NonPriceIndicator> {
    let mut data = Vec::new();
    let start_date = chrono::NaiveDate::from_ymd_opt(2023, 1, 1).unwrap();

    for day in 0..365 {
        let date = start_date + chrono::Duration::days(day);

        // HIBOR data
        let hibor_value = 3.0 + (day as f64 * 0.01).sin() * 0.5;
        data.push(NonPriceIndicator::new(
            "HIBOR_1M".to_string(),
            date,
            hibor_value,
            "HKMA".to_string(),
        ));

        // Visitor count
        let visitor_value = 400000.0 + (day as f64 * 0.02).sin() * 50000.0;
        data.push(NonPriceIndicator::new(
            "VISITOR_COUNT".to_string(),
            date,
            visitor_value,
            "HKTB".to_string(),
        ));
    }

    data
}

fn create_sample_stock_data() -> Vec<OHLCV> {
    let mut data = Vec::new();
    let start_date = chrono::NaiveDate::from_ymd_opt(2023, 1, 1).unwrap();

    let mut price = 380.0;

    for day in 0..365 {
        let date = start_date + chrono::Duration::days(day);
        price += (day as f64 * 0.01).sin() * 3.0; // Simulate realistic price movement

        data.push(OHLCV {
            symbol: "0700.HK".to_string(),
            date,
            open: price - 2.0,
            high: price + 3.0,
            low: price - 3.0,
            close: price,
            volume: 1000000 + (day as i64 * 100),
        });
    }

    data
}
