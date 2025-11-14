//! 相对强度指数 (RSI)

use crate::types::OHLCV;

/// 计算RSI (Relative Strength Index)
#[inline]
pub fn rsi(prices: &[f64], period: usize) -> Vec<f64> {
    if prices.len() < period + 1 {
        return vec![50.0; prices.len()]; // 中性RSI
    }

    let mut result = vec![50.0; prices.len()];
    let mut gains = vec![0.0; prices.len()];
    let mut losses = vec![0.0; prices.len()];

    // 计算价格变化
    for i in 1..prices.len() {
        let change: f64 = prices[i] - prices[i - 1];
        gains[i] = if change > 0.0 { change } else { 0.0 };
        losses[i] = if change < 0.0 { -change } else { 0.0 };
    }

    // 计算初始平均值
    let mut avg_gain = gains[1..=period].iter().sum::<f64>() / period as f64;
    let mut avg_loss = losses[1..=period].iter().sum::<f64>() / period as f64;

    result[period] = 100.0 - (100.0 / (1.0 + avg_gain / (avg_loss + 1e-10)));

    // 使用平滑方法计算后续值
    for i in (period + 1)..prices.len() {
        avg_gain = (avg_gain * (period as f64 - 1.0) + gains[i]) / period as f64;
        avg_loss = (avg_loss * (period as f64 - 1.0) + losses[i]) / period as f64;
        let rs = avg_gain / (avg_loss + 1e-10);
        result[i] = 100.0 - (100.0 / (1.0 + rs));
    }

    result
}

/// 从OHLCV数据计算RSI
#[inline]
pub fn rsi_from_ohlcv(data: &[OHLCV], period: usize) -> Vec<f64> {
    let prices: Vec<f64> = data.iter().map(|d| d.close).collect();
    rsi(&prices, period)
}

/// 生成RSI交易信号
#[inline]
pub fn rsi_signals(rsi_values: &[f64], oversold: f64, overbought: f64) -> Vec<i32> {
    let mut signals = vec![0; rsi_values.len()];

    for i in 1..rsi_values.len() {
        if rsi_values[i] < oversold && rsi_values[i - 1] >= oversold {
            signals[i] = 1; // Buy signal
        } else if rsi_values[i] > overbought && rsi_values[i - 1] <= overbought {
            signals[i] = -1; // Sell signal
        } else {
            signals[i] = 0; // Hold
        }
    }

    signals
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rsi() {
        let prices = vec![1.0, 2.0, 3.0, 2.0, 1.5, 2.0, 2.5, 3.0];
        let result = rsi(&prices, 5);
        assert_eq!(result.len(), 8);
        assert!(result[5] >= 0.0 && result[5] <= 100.0);
    }

    #[test]
    fn test_rsi_signals() {
        let rsi_values = vec![60.0, 25.0, 35.0, 75.0, 70.0];
        let signals = rsi_signals(&rsi_values, 30.0, 70.0);
        assert_eq!(signals.len(), 5);
        assert_eq!(signals[1], 1); // Buy at 25
        assert_eq!(signals[3], -1); // Sell at 75
    }
}
