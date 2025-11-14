//! Rust Non-Price Data Technical Indicators System

pub mod core;
pub mod data;
pub mod strategy;
pub mod backtest;
pub mod utils;

pub use core::data::{
    BacktestResult, DataQuality, IndicatorType, NonPriceIndicator, OHLCV,
    ParameterSet, SignalAction, TechnicalIndicator, Trade,
};
pub use core::backtest::{BacktestConfig, PositionSizing, OptimizationConfig, OptimizationMetric};
pub use core::error::BacktestError;
pub use strategy::optimizer::{OptimizationResult, ScoredParameterSet, MultiIndicatorResult};

pub mod api {
    use super::*;
    use std::path::Path;

    pub fn load_nonprice_csv(path: &Path) -> Result<Vec<NonPriceIndicator>, BacktestError> {
        data::loader::load_csv(path)
    }

    pub fn load_nonprice_parquet(path: &Path) -> Result<Vec<NonPriceIndicator>, BacktestError> {
        data::loader::load_parquet(path)
    }

    pub fn load_stock_prices(path: &Path, symbol: &str) -> Result<Vec<OHLCV>, BacktestError> {
        data::loader::load_stock_prices(path, symbol)
    }

    pub fn validate_data(data: &[NonPriceIndicator]) -> Result<data::ValidationReport, BacktestError> {
        data::validator::validate(data)
    }

    pub fn calculate_all_indicators(
        data: &[NonPriceIndicator],
    ) -> Result<Vec<TechnicalIndicator>, BacktestError> {
        data::processor::calculate_all(data)
    }

    pub fn calculate_zscore(
        data: &[NonPriceIndicator],
        window_size: usize,
    ) -> Result<Vec<TechnicalIndicator>, BacktestError> {
        data::processor::calculate_zscore(data, window_size)
    }

    pub fn calculate_rsi(
        data: &[NonPriceIndicator],
        window_size: usize,
    ) -> Result<Vec<TechnicalIndicator>, BacktestError> {
        data::processor::calculate_rsi(data, window_size)
    }

    pub fn calculate_sma(
        data: &[NonPriceIndicator],
        window_size: usize,
    ) -> Result<Vec<TechnicalIndicator>, BacktestError> {
        data::processor::calculate_sma(data, window_size)
    }

    pub fn generate_signals(
        indicators: &[TechnicalIndicator],
        parameters: &ParameterSet,
    ) -> Result<Vec<core::data::TradingSignal>, BacktestError> {
        strategy::signals::generate(indicators, parameters)
    }

    pub fn generate_combined_signals(
        indicators: &[TechnicalIndicator],
        parameter_sets: &[ParameterSet],
        combination_strategy: strategy::combiner::CombinationStrategy,
    ) -> Result<Vec<core::data::TradingSignal>, BacktestError> {
        strategy::combiner::generate_combined(indicators, parameter_sets, combination_strategy)
    }

    pub fn optimize_parameters(
        indicators: &[TechnicalIndicator],
        stock_data: &[OHLCV],
        config: &OptimizationConfig,
    ) -> Result<OptimizationResult, BacktestError> {
        strategy::optimizer::optimize(indicators, stock_data, config)
    }

    pub fn optimize_all_indicators(
        all_indicators: &[Vec<TechnicalIndicator>],
        stock_data: &[OHLCV],
        config: &OptimizationConfig,
    ) -> Result<strategy::optimizer::MultiIndicatorResult, BacktestError> {
        strategy::optimizer::optimize_all(all_indicators, stock_data, config)
    }

    pub fn run_backtest(
        signals: &[core::data::TradingSignal],
        stock_data: &[OHLCV],
        config: &BacktestConfig,
    ) -> Result<BacktestResult, BacktestError> {
        backtest::engine::run(signals, stock_data, config)
    }

    pub fn run_comprehensive_backtest(
        signals: &[core::data::TradingSignal],
        stock_data: &[OHLCV],
        config: &BacktestConfig,
    ) -> Result<backtest::engine::ComprehensiveResult, BacktestError> {
        backtest::engine::run_comprehensive(signals, stock_data, config)
    }

    pub fn generate_markdown_report(
        result: &BacktestResult,
        output_path: &Path,
    ) -> Result<(), BacktestError> {
        backtest::report::generate_markdown(result, output_path)
    }

    pub fn generate_json_report(
        result: &BacktestResult,
        output_path: &Path,
    ) -> Result<(), BacktestError> {
        backtest::report::generate_json(result, output_path)
    }

    pub fn generate_comprehensive_report(
        result: &BacktestResult,
        output_dir: &Path,
    ) -> Result<backtest::report::ReportBundle, BacktestError> {
        backtest::report::generate_comprehensive(result, output_dir)
    }

    pub fn calculate_metrics(
        equity_curve: &[(chrono::NaiveDate, f64)],
        initial_capital: f64,
    ) -> Result<backtest::metrics::PerformanceMetrics, BacktestError> {
        Ok(backtest::metrics::calculate(equity_curve, initial_capital))
    }

    pub fn annualize_metrics(
        daily_return: f64,
        volatility: f64,
        trading_days: usize,
    ) -> backtest::metrics::AnnualizedMetrics {
        backtest::metrics::annualize(daily_return, volatility, trading_days)
    }

    pub fn interpolate_missing(
        data: &mut [NonPriceIndicator],
        method: data::validator::InterpolationMethod,
    ) -> Result<(), BacktestError> {
        data::validator::interpolate_missing(data, method)
    }
}
