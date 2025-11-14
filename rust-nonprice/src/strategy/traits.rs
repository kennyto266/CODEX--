//! Strategy trait for extensibility
//!
//! This module defines the Strategy trait that allows for easy
//! extension of the system with new indicators and strategies.

use crate::core::data::{NonPriceIndicator, ParameterSet, TechnicalIndicator, TradingSignal};
use crate::core::error::BacktestError;

/// Strategy trait for calculating technical indicators
pub trait TechnicalIndicatorStrategy {
    /// Calculate the technical indicator
    fn calculate(
        &self,
        data: &[NonPriceIndicator],
        window_size: usize,
    ) -> Result<Vec<TechnicalIndicator>, BacktestError>;

    /// Get the indicator type
    fn indicator_type(&self) -> crate::core::data::IndicatorType;
}

/// Signal generation strategy
pub trait SignalGenerationStrategy {
    /// Generate signals from technical indicators
    fn generate_signals(
        &self,
        indicators: &[TechnicalIndicator],
        parameters: &ParameterSet,
    ) -> Result<Vec<TradingSignal>, BacktestError>;
}

/// Parameter optimization strategy
pub trait OptimizationStrategy {
    /// Optimize parameters for a given dataset
    fn optimize(
        &self,
        indicators: &[TechnicalIndicator],
        stock_data: &[crate::core::data::OHLCV],
        config: &crate::core::backtest::OptimizationConfig,
    ) -> Result<crate::strategy::optimizer::OptimizationResult, BacktestError>;
}

/// Default implementations
pub mod defaults {
    use super::*;

    /// Z-Score strategy
    pub struct ZScoreStrategy;

    impl ZScoreStrategy {
        pub fn new() -> Self {
            Self
        }
    }

    impl TechnicalIndicatorStrategy for ZScoreStrategy {
        fn calculate(
            &self,
            data: &[NonPriceIndicator],
            window_size: usize,
        ) -> Result<Vec<TechnicalIndicator>, BacktestError> {
            crate::data::processor::calculate_zscore(data, window_size)
        }

        fn indicator_type(&self) -> crate::core::data::IndicatorType {
            crate::core::data::IndicatorType::ZScore
        }
    }

    /// RSI strategy
    pub struct RSIStrategy;

    impl RSIStrategy {
        pub fn new() -> Self {
            Self
        }
    }

    impl TechnicalIndicatorStrategy for RSIStrategy {
        fn calculate(
            &self,
            data: &[NonPriceIndicator],
            window_size: usize,
        ) -> Result<Vec<TechnicalIndicator>, BacktestError> {
            crate::data::processor::calculate_rsi(data, window_size)
        }

        fn indicator_type(&self) -> crate::core::data::IndicatorType {
            crate::core::data::IndicatorType::RSI
        }
    }

    /// SMA strategy
    pub struct SMAStrategy;

    impl SMAStrategy {
        pub fn new() -> Self {
            Self
        }
    }

    impl TechnicalIndicatorStrategy for SMAStrategy {
        fn calculate(
            &self,
            data: &[NonPriceIndicator],
            window_size: usize,
        ) -> Result<Vec<TechnicalIndicator>, BacktestError> {
            crate::data::processor::calculate_sma(data, window_size)
        }

        fn indicator_type(&self) -> crate::core::data::IndicatorType {
            crate::core::data::IndicatorType::SMAFast
        }
    }
}
