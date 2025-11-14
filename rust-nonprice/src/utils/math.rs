//! Mathematical utilities
//!
//! This module provides statistical calculations, performance metrics,
//! and mathematical functions for the trading system.

use statrs::statistics::Statistics;

/// Calculate mean of a slice
pub fn mean(values: &[f64]) -> f64 {
    if values.is_empty() {
        f64::NAN
    } else {
        values.mean()
    }
}

/// Calculate standard deviation
pub fn std_dev(values: &[f64]) -> f64 {
    if values.len() < 2 {
        f64::NAN
    } else {
        values.std_dev()
    }
}

/// Calculate variance
pub fn variance(values: &[f64]) -> f64 {
    if values.len() < 2 {
        f64::NAN
    } else {
        values.variance()
    }
}

/// Calculate Z-Score
pub fn zscore(value: f64, mean: f64, std_dev: f64) -> f64 {
    if std_dev == 0.0 || std_dev.is_nan() {
        f64::NAN
    } else {
        (value - mean) / std_dev
    }
}

/// Calculate rolling mean
pub fn rolling_mean(values: &[f64], window: usize) -> Vec<Option<f64>> {
    let n = values.len();
    let mut result = vec![None; n];

    for i in window..=n {
        let start = i - window;
        let end = i;
        let slice = &values[start..end];
        result[i - 1] = Some(mean(slice));
    }

    result
}

/// Calculate rolling standard deviation
pub fn rolling_std(values: &[f64], window: usize) -> Vec<Option<f64>> {
    let n = values.len();
    let mut result = vec![None; n];

    for i in window..=n {
        let start = i - window;
        let end = i;
        let slice = &values[start..end];
        result[i - 1] = Some(std_dev(slice));
    }

    result
}

/// Calculate RSI (Relative Strength Index)
pub fn calculate_rsi(values: &[f64], period: usize) -> Vec<Option<f64>> {
    if values.len() < period + 1 {
        return vec![None; values.len()];
    }

    let n = values.len();
    let mut rsi = vec![None; n];

    // Calculate price changes
    let mut changes = Vec::with_capacity(n - 1);
    for i in 1..n {
        changes.push(values[i] - values[i - 1]);
    }

    // Calculate initial average gain and loss
    let mut avg_gain = 0.0;
    let mut avg_loss = 0.0;

    for i in 0..period {
        let change = changes[i];
        if change > 0.0 {
            avg_gain += change;
        } else {
            avg_loss += -change;
        }
    }

    avg_gain /= period as f64;
    avg_loss /= period as f64;

    // Calculate RSI for the first valid value
    let rs = if avg_loss == 0.0 {
        f64::INFINITY
    } else {
        avg_gain / avg_loss
    };
    rsi[period] = Some(100.0 - (100.0 / (1.0 + rs)));

    // Calculate subsequent values using Wilder's smoothing
    for i in period + 1..n {
        let change = changes[i - 1];

        if change > 0.0 {
            avg_gain = (avg_gain * (period as f64 - 1.0) + change) / period as f64;
            avg_loss = (avg_loss * (period as f64 - 1.0)) / period as f64;
        } else {
            avg_gain = (avg_gain * (period as f64 - 1.0)) / period as f64;
            avg_loss = (avg_loss * (period as f64 - 1.0) + -change) / period as f64;
        }

        let rs = if avg_loss == 0.0 {
            f64::INFINITY
        } else {
            avg_gain / avg_loss
        };
        rsi[i] = Some(100.0 - (100.0 / (1.0 + rs)));
    }

    rsi
}

/// Calculate Simple Moving Average
pub fn simple_moving_average(values: &[f64], window: usize) -> Vec<Option<f64>> {
    rolling_mean(values, window)
}

/// Calculate exponential moving average
pub fn exponential_moving_average(values: &[f64], period: usize) -> Vec<Option<f64>> {
    if values.len() < period {
        return vec![None; values.len()];
    }

    let n = values.len();
    let mut ema = vec![None; n];
    let multiplier = 2.0 / (period as f64 + 1.0);

    // Start with SMA for first value
    let mut sum = 0.0;
    for i in 0..period {
        sum += values[i];
    }
    ema[period - 1] = Some(sum / period as f64);

    // Calculate EMA for subsequent values
    for i in period..n {
        let prev_ema = ema[i - 1].unwrap();
        ema[i] = Some((values[i] - prev_ema) * multiplier + prev_ema);
    }

    ema
}

/// Calculate Sharpe Ratio
pub fn sharpe_ratio(returns: &[f64], risk_free_rate: f64, trading_days: usize) -> f64 {
    if returns.is_empty() {
        return f64::NAN;
    }

    let mean_return = mean(returns);
    let std_deviation = std_dev(returns);

    if std_deviation == 0.0 {
        return f64::NAN;
    }

    let excess_return = mean_return - risk_free_rate;
    let annualized_excess = excess_return * trading_days as f64;
    let annualized_volatility = std_deviation * (trading_days as f64).sqrt();

    annualized_excess / annualized_volatility
}

/// Calculate Sortino Ratio
pub fn sortino_ratio(returns: &[f64], risk_free_rate: f64, trading_days: usize) -> f64 {
    if returns.is_empty() {
        return f64::NAN;
    }

    let mean_return = mean(returns);
    let excess_return = mean_return - risk_free_rate;

    // Calculate downside deviation
    let negative_returns: Vec<f64> = returns
        .iter()
        .filter(|&&r| r < risk_free_rate)
        .copied()
        .collect();

    if negative_returns.is_empty() {
        return f64::INFINITY;
    }

    let downside_deviation = std_dev(&negative_returns);
    if downside_deviation == 0.0 {
        return f64::NAN;
    }

    let annualized_excess = excess_return * trading_days as f64;
    let annualized_downside = downside_deviation * (trading_days as f64).sqrt();

    annualized_excess / annualized_downside
}

/// Calculate Calmar Ratio
pub fn calmar_ratio(returns: &[f64], max_drawdown: f64) -> f64 {
    if max_drawdown >= 0.0 || max_drawdown == f64::NAN {
        return f64::NAN;
    }

    let annual_return = mean(returns) * 252.0; // Assuming daily returns
    let positive_drawdown = -max_drawdown;

    if positive_drawdown == 0.0 {
        return f64::INFINITY;
    }

    annual_return / positive_drawdown
}

/// Calculate Maximum Drawdown
pub fn max_drawdown(equity_curve: &[f64]) -> f64 {
    if equity_curve.is_empty() {
        return f64::NAN;
    }

    let mut max_drawdown = 0.0;
    let mut peak = equity_curve[0];

    for &value in equity_curve {
        if value > peak {
            peak = value;
        }

        let drawdown = (peak - value) / peak;
        if drawdown > max_drawdown {
            max_drawdown = drawdown;
        }
    }

    -max_drawdown // Return as negative value
}

/// Calculate Win Rate
pub fn win_rate(trades: &[f64]) -> f64 {
    if trades.is_empty() {
        return 0.0;
    }

    let winning_trades = trades.iter().filter(|&&t| t > 0.0).count();
    (winning_trades as f64 / trades.len() as f64) * 100.0
}

/// Calculate Profit Factor
pub fn profit_factor(trades: &[f64]) -> f64 {
    if trades.is_empty() {
        return f64::NAN;
    }

    let gross_profit: f64 = trades.iter().filter(|&&t| t > 0.0).sum();
    let gross_loss: f64 = trades.iter().filter(|&&t| t < 0.0).sum();

    if gross_loss == 0.0 {
        return f64::INFINITY;
    }

    gross_profit / gross_loss.abs()
}

/// Annualize metrics
pub fn annualize_return(daily_return: f64, trading_days: usize) -> f64 {
    (1.0 + daily_return).powi(trading_days as i32) - 1.0
}

/// Annualize volatility
pub fn annualize_volatility(daily_volatility: f64, trading_days: usize) -> f64 {
    daily_volatility * (trading_days as f64).sqrt()
}

/// Calculate Value at Risk (VaR)
pub fn value_at_risk(returns: &[f64], confidence: f64) -> f64 {
    if returns.is_empty() {
        return f64::NAN;
    }

    let mut sorted_returns = returns.to_vec();
    sorted_returns.sort_by(|a, b| a.partial_cmp(b).unwrap());

    let index = ((1.0 - confidence) * sorted_returns.len() as f64) as usize;
    sorted_returns[index]
}

/// Calculate Conditional Value at Risk (CVaR)
pub fn conditional_value_at_risk(returns: &[f64], confidence: f64) -> f64 {
    if returns.is_empty() {
        return f64::NAN;
    }

    let var = value_at_risk(returns, confidence);
    let tail_returns: Vec<f64> = returns
        .iter()
        .filter(|&&r| r <= var)
        .copied()
        .collect();

    if tail_returns.is_empty() {
        return var;
    }

    -mean(&tail_returns) // Return as positive value
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_mean() {
        let values = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        assert_eq!(mean(&values), 3.0);
    }

    #[test]
    fn test_zscore() {
        let score = zscore(2.0, 5.0, 2.0);
        assert!((score + 1.5).abs() < 0.01);
    }

    #[test]
    fn test_calculate_rsi() {
        let prices = vec![100.0, 102.0, 101.0, 105.0, 103.0];
        let rsi = calculate_rsi(&prices, 2);
        assert!(rsi[1].is_some());
    }

    #[test]
    fn test_simple_moving_average() {
        let values = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let sma = simple_moving_average(&values, 3);
        assert_eq!(sma[2], Some(2.0));
    }

    #[test]
    fn test_max_drawdown() {
        let equity = vec![100.0, 110.0, 105.0, 115.0, 90.0, 95.0];
        let drawdown = max_drawdown(&equity);
        assert!(drawdown < 0.0);
        assert!((drawdown + 0.2).abs() < 0.01);
    }
}
