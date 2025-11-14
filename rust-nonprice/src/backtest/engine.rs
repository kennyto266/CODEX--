//! Backtest engine
//!
//! This module implements the event-driven backtest engine that applies
//! trading signals to stock price data and calculates performance metrics.

use crate::core::backtest::BacktestConfig;
use crate::core::data::{BacktestResult, OHLCV, SignalAction, Trade, ParameterSet, TradingSignal};
use crate::utils::math::{max_drawdown, sharpe_ratio, win_rate};
use crate::core::error::BacktestError;
use chrono::NaiveDate;
use serde::{Deserialize, Serialize};

/// Run a single backtest
pub fn run(
    signals: &[TradingSignal],
    stock_data: &[OHLCV],
    config: &BacktestConfig,
) -> Result<BacktestResult, BacktestError> {
    // Validate configuration
    config.validate()?;

    let start_time = std::time::Instant::now();

    // Sort signals by date
    let mut sorted_signals = signals.to_vec();
    sorted_signals.sort_by(|a, b| a.date.cmp(&b.date));

    // Sort stock data by date
    let mut sorted_stock = stock_data.to_vec();
    sorted_stock.sort_by(|a, b| a.date.cmp(&b.date));

    if sorted_stock.is_empty() {
        return Err(BacktestError::insufficient_data(1, 0));
    }

    let start_date = sorted_stock[0].date;
    let end_date = sorted_stock.last().unwrap().date;

    // Initialize backtest result
    let mut result = BacktestResult::new(
        format!("backtest-{}", start_time.elapsed().as_millis()),
        sorted_stock[0].symbol.clone(),
        start_date,
        end_date,
        config.initial_capital,
        ParameterSet::default(),
    );

    // Run backtest
    let mut position = 0.0; // Current position (shares)
    let mut cash = config.initial_capital;
    let mut equity_curve = Vec::new();
    let mut trades = Vec::new();

    // Process each trading day
    for stock_point in &sorted_stock {
        let current_price = stock_point.close;
        let current_value = cash + position * current_price;

        // Check for signals on this date
        if let Some(signal) = sorted_signals.iter().find(|s| s.date == stock_point.date) {
            match signal.action {
                SignalAction::Buy if position == 0.0 => {
                    // Enter long position
                    let shares = (cash * config.position_sizing.size()) / current_price;
                    let commission = shares * current_price * config.commission_rate;
                    let total_cost = shares * current_price + commission;

                    if total_cost <= cash {
                        position += shares;
                        cash -= total_cost;

                        trades.push(Trade::new(
                            format!("trade-{}", trades.len()),
                            stock_point.date,
                            stock_point.date, // Will be updated on exit
                            current_price,
                            current_price,    // Will be updated on exit
                            shares,
                            SignalAction::Buy,
                            SignalAction::Hold, // Will be updated on exit
                        ));
                    }
                }
                SignalAction::Sell if position > 0.0 => {
                    // Exit long position
                    let commission = position * current_price * config.commission_rate;
                    let proceeds = position * current_price - commission;
                    cash += proceeds;

                    // Update the last trade
                    if let Some(last_trade) = trades.last_mut() {
                        last_trade.exit_date = stock_point.date;
                        last_trade.exit_price = current_price;
                        last_trade.exit_signal = SignalAction::Sell;
                        last_trade.pnl = (current_price - last_trade.entry_price)
                            * last_trade.quantity
                            - last_trade.commission;
                    }

                    position = 0.0;
                }
                _ => {}
            }
        }

        // Record equity for this day
        equity_curve.push((stock_point.date, current_value));
    }

    // Final value
    let final_value = if position > 0.0 {
        // Close any remaining position at last price
        let last_price = sorted_stock.last().unwrap().close;
        position * last_price + cash
    } else {
        cash
    };

    // Calculate performance metrics
    if equity_curve.len() < 2 {
        return Err(BacktestError::insufficient_data(2, equity_curve.len()));
    }

    let returns: Vec<f64> = equity_curve
        .windows(2)
        .map(|window| {
            (window[1].1 - window[0].1) / window[0].1
        })
        .collect();

    let total_return_pct = (final_value - config.initial_capital) / config.initial_capital * 100.0;
    let annual_return_pct = total_return_pct * (252.0 / equity_curve.len() as f64);
    let sharpe = sharpe_ratio(&returns, config.risk_free_rate, 252);
    let max_dd = max_drawdown(&equity_curve.iter().map(|(_, v)| *v).collect::<Vec<_>>());
    let win_rate_pct = win_rate(&trades.iter().map(|t| t.pnl).collect::<Vec<_>>());

    // Update result
    result.final_value = final_value;
    result.total_return_pct = total_return_pct;
    result.annual_return_pct = annual_return_pct;
    result.sharpe_ratio = sharpe;
    result.max_drawdown_pct = max_dd;
    result.win_rate_pct = win_rate_pct;
    result.total_trades = trades.len();
    result.winning_trades = trades.iter().filter(|t| t.pnl > 0.0).count();
    result.losing_trades = result.total_trades - result.winning_trades;
    result.execution_time_ms = start_time.elapsed().as_millis() as u64;
    result.trades = trades;
    result.equity_curve = equity_curve;

    Ok(result)
}

/// Comprehensive backtest result with additional metrics
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ComprehensiveResult {
    pub backtest_result: BacktestResult,
    pub additional_metrics: std::collections::HashMap<String, f64>,
}

/// Run comprehensive backtest
pub fn run_comprehensive(
    signals: &[TradingSignal],
    stock_data: &[OHLCV],
    config: &BacktestConfig,
) -> Result<ComprehensiveResult, BacktestError> {
    let backtest_result = run(signals, stock_data, config)?;

    // Calculate additional metrics
    let mut additional_metrics = std::collections::HashMap::new();

    // These would be calculated based on the backtest result
    // For now, add placeholder metrics
    additional_metrics.insert("calmar_ratio".to_string(), 0.0);
    additional_metrics.insert("sortino_ratio".to_string(), 0.0);
    additional_metrics.insert("profit_factor".to_string(), 0.0);
    additional_metrics.insert("value_at_risk".to_string(), 0.0);

    Ok(ComprehensiveResult {
        backtest_result,
        additional_metrics,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::data::{OHLCV, TradingSignal, SignalAction, ParameterSet};
    use chrono::NaiveDate;

    #[test]
    fn test_run_backtest() {
        let stock_data = vec![
            OHLCV::new(
                "TEST".to_string(),
                NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(),
                100.0, 105.0, 95.0, 102.0, 1000000
            ),
            OHLCV::new(
                "TEST".to_string(),
                NaiveDate::from_ymd_opt(2023, 1, 2).unwrap(),
                102.0, 108.0, 101.0, 106.0, 1500000
            ),
        ];

        let signals = vec![TradingSignal {
            symbol: "TEST".to_string(),
            date: NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(),
            action: SignalAction::Buy,
            confidence: 1.0,
            source_indicators: vec!["TEST_ZSCORE".to_string()],
            reasoning: "Test".to_string(),
            parameters: std::collections::HashMap::new(),
        }];

        let config = BacktestConfig::default();
        let result = run(&signals, &stock_data, &config).unwrap();

        assert!(result.total_return_pct >= 0.0);
        assert!(result.total_trades >= 0);
    }
}
