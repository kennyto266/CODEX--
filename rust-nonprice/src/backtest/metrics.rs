//! Performance metrics calculation
//!
//! This module calculates various performance metrics for backtesting
//! including Sharpe ratio, max drawdown, win rate, etc.

use crate::utils::math::{max_drawdown, sharpe_ratio, win_rate, sortino_ratio, calmar_ratio};
use serde::{Deserialize, Serialize};

/// Performance metrics
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PerformanceMetrics {
    pub total_return: f64,
    pub annual_return: f64,
    pub sharpe_ratio: f64,
    pub sortino_ratio: f64,
    pub max_drawdown: f64,
    pub calmar_ratio: f64,
    pub win_rate: f64,
    pub profit_factor: f64,
    pub total_trades: usize,
    pub winning_trades: usize,
    pub losing_trades: usize,
}

impl PerformanceMetrics {
    /// Create a new metrics struct
    pub fn new() -> Self {
        Self {
            total_return: 0.0,
            annual_return: 0.0,
            sharpe_ratio: 0.0,
            sortino_ratio: 0.0,
            max_drawdown: 0.0,
            calmar_ratio: 0.0,
            win_rate: 0.0,
            profit_factor: 0.0,
            total_trades: 0,
            winning_trades: 0,
            losing_trades: 0,
        }
    }
}

/// Annualized metrics
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AnnualizedMetrics {
    pub annual_return: f64,
    pub annual_volatility: f64,
    pub annual_sharpe: f64,
}

/// Calculate performance metrics from equity curve
pub fn calculate(
    equity_curve: &[(chrono::NaiveDate, f64)],
    initial_capital: f64,
) -> PerformanceMetrics {
    if equity_curve.len() < 2 {
        return PerformanceMetrics::new();
    }

    let final_value = equity_curve.last().unwrap().1;
    let total_return = (final_value - initial_capital) / initial_capital;

    // Calculate daily returns
    let returns: Vec<f64> = equity_curve
        .windows(2)
        .map(|window| {
            (window[1].1 - window[0].1) / window[0].1
        })
        .collect();

    let annual_return = total_return * 252.0; // Assuming daily data
    let sharpe = sharpe_ratio(&returns, 0.02, 252);
    let sortino = sortino_ratio(&returns, 0.02, 252);

    let max_dd = max_drawdown(&equity_curve.iter().map(|(_, v)| *v).collect::<Vec<_>>());
    let calmar = calmar_ratio(&returns, max_dd);

    // Win rate and trades would need trade data
    // For now, return default values
    PerformanceMetrics {
        total_return,
        annual_return,
        sharpe_ratio: sharpe,
        sortino_ratio: sortino,
        max_drawdown: max_dd,
        calmar_ratio: calmar,
        win_rate: 0.0,
        profit_factor: 0.0,
        total_trades: 0,
        winning_trades: 0,
        losing_trades: 0,
    }
}

/// Annualize metrics
pub fn annualize(
    daily_return: f64,
    daily_volatility: f64,
    trading_days: usize,
) -> AnnualizedMetrics {
    let annual_return = (1.0 + daily_return).powi(trading_days as i32) - 1.0;
    let annual_volatility = daily_volatility * (trading_days as f64).sqrt();
    let annual_sharpe = if annual_volatility == 0.0 {
        0.0
    } else {
        annual_return / annual_volatility
    };

    AnnualizedMetrics {
        annual_return,
        annual_volatility,
        annual_sharpe,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::NaiveDate;

    #[test]
    fn test_calculate_metrics() {
        let equity_curve = vec![
            (NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(), 100000.0),
            (NaiveDate::from_ymd_opt(2023, 1, 2).unwrap(), 101000.0),
            (NaiveDate::from_ymd_opt(2023, 1, 3).unwrap(), 99000.0),
        ];

        let metrics = calculate(&equity_curve, 100000.0);
        assert!(metrics.total_return > 0.0);
    }
}
