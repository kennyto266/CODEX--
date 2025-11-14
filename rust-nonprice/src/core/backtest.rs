//! Backtest configuration and related types

use serde::{Deserialize, Serialize};
use std::fmt;

#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub enum PositionSizing {
    Fixed { size: f64 },
    Kelly { fraction: f64 },
    FractionalKelly { fraction: f64 },
}

impl PositionSizing {
    pub fn size(&self) -> f64 {
        match self {
            PositionSizing::Fixed { size } => *size,
            PositionSizing::Kelly { fraction } => *fraction,
            PositionSizing::FractionalKelly { fraction } => *fraction,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BacktestConfig {
    pub initial_capital: f64,
    pub commission_rate: f64,
    pub slippage: f64,
    pub risk_free_rate: f64,
    pub position_sizing: PositionSizing,
    pub allow_short_selling: bool,
}

impl BacktestConfig {
    pub fn default() -> Self {
        Self {
            initial_capital: 100_000.0,
            commission_rate: 0.001,
            slippage: 0.0005,
            risk_free_rate: 0.02,
            position_sizing: PositionSizing::Fixed { size: 1.0 },
            allow_short_selling: false,
        }
    }

    /// Validate configuration
    pub fn validate(&self) -> Result<(), crate::core::error::BacktestError> {
        if self.initial_capital <= 0.0 {
            return Err(crate::core::error::BacktestError::validation_error(
                "initial_capital",
                "must be positive",
            ));
        }
        if self.commission_rate < 0.0 || self.commission_rate > 0.1 {
            return Err(crate::core::error::BacktestError::validation_error(
                "commission_rate",
                "must be between 0 and 0.1",
            ));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum OptimizationMetric {
    SharpeRatio,
    TotalReturn,
    AnnualReturn,
    MaxDrawdown,
    WinRate,
    CalmarRatio,
}

impl fmt::Display for OptimizationMetric {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            OptimizationMetric::SharpeRatio => write!(f, "Sharpe Ratio"),
            OptimizationMetric::TotalReturn => write!(f, "Total Return"),
            OptimizationMetric::AnnualReturn => write!(f, "Annual Return"),
            OptimizationMetric::MaxDrawdown => write!(f, "Max Drawdown"),
            OptimizationMetric::WinRate => write!(f, "Win Rate"),
            OptimizationMetric::CalmarRatio => write!(f, "Calmar Ratio"),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OptimizationConfig {
    pub max_combinations: Option<usize>,
    pub max_workers: usize,
    pub timeout: Option<std::time::Duration>,
    pub min_trades: usize,
    pub primary_metric: OptimizationMetric,
    pub early_termination: bool,
    pub verbose: bool,
    pub backtest_config: BacktestConfig,
}

impl OptimizationConfig {
    pub fn default() -> Self {
        Self {
            max_combinations: None,
            max_workers: num_cpus::get(),
            timeout: Some(std::time::Duration::from_secs(3600)),
            min_trades: 10,
            primary_metric: OptimizationMetric::SharpeRatio,
            early_termination: true,
            verbose: true,
            backtest_config: BacktestConfig::default(),
        }
    }

    pub fn single_indicator(max_workers: usize) -> Self {
        let mut config = Self::default();
        config.max_workers = max_workers;
        config
    }

    pub fn all_indicators(max_workers: usize, timeout_seconds: u64) -> Self {
        let mut config = Self::default();
        config.max_workers = max_workers;
        config.timeout = Some(std::time::Duration::from_secs(timeout_seconds));
        config
    }

    pub fn validate(&self) -> Result<(), crate::BacktestError> {
        if self.max_workers == 0 {
            return Err(crate::BacktestError::validation_error(
                "max_workers",
                "must be positive",
            ));
        }
        if self.min_trades == 0 {
            return Err(crate::BacktestError::validation_error(
                "min_trades",
                "must be positive",
            ));
        }
        Ok(())
    }
}
