//! 回测引擎模块
//! 包含回测配置、结果和性能指标

pub mod engine;
pub mod metrics;
pub mod optimization;

pub use engine::{BacktestEngine, run_backtest, run_comprehensive_backtest, ComprehensiveResult, StrategyParams, validate_data, calculate_drawdown, run_sma_backtest};
pub use metrics::{PerformanceMetrics, BacktestResult, Trade};
pub use optimization::{OptimizationEngine, ParameterGrid, OptimizationResult};

use serde::{Deserialize, Serialize};

/// 回测配置
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
pub struct BacktestConfig {
    pub initial_capital: f64,
    pub commission: f64,
    pub slippage: f64,
    pub start_date: u64,
    pub end_date: u64,
}

impl BacktestConfig {
    /// Create a default configuration
    pub fn default() -> Self {
        Self {
            initial_capital: 100_000.0,
            commission: 0.001,
            slippage: 0.0005,
            start_date: 0,
            end_date: u64::MAX,
        }
    }
}

