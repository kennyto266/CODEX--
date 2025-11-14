//! 高性能量化交易核心库
//!
//! 提供了基于Rust的高性能回测引擎，支持并行计算和Python绑定

#![warn(missing_docs)]
#![warn(clippy::all)]

/// 核心数据类型
pub mod types;
pub use types::{OHLCV, Signal, SignalType, Trade, DataPoint};

/// 回测引擎
pub mod backtest;
pub use backtest::{BacktestEngine, BacktestConfig, BacktestResult, PerformanceMetrics, ComprehensiveResult, OptimizationEngine, OptimizationResult, run_backtest, run_comprehensive_backtest};

/// 技术指标
pub mod indicators;
pub use indicators::{
    sma, ema, wma, vwma,
    rsi, macd, bollinger_bands, kdj, cci, adx, atr, obv, ichimoku, parabolic_sar,
    calculate_all_indicators, IndicatorConfig, IndicatorValue
};

/// Python bindings
#[cfg(feature = "python")]

mod metrics_test;
