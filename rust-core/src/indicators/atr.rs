//! ATR (真实波动幅度)

use crate::types::OHLCV;
use super::moving_average::sma;

/// 计算ATR
#[inline]
pub fn atr(high: &[f64], low: &[f64], close: &[f64], period: usize) -> Vec<f64> {
    if high.len() < 2 {
        return vec![0.0; high.len()];
    }

    let mut true_ranges = vec![0.0; high.len()];
    true_ranges[0] = high[0] - low[0];

    for i in 1..high.len() {
        let tr1 = high[i] - low[i];
        let tr2 = (high[i] - close[i - 1]).abs();
        let tr3 = (low[i] - close[i - 1]).abs();
        true_ranges[i] = tr1.max(tr2).max(tr3);
    }

    // 使用SMA计算ATR
    sma(&true_ranges, period)
}

/// 从OHLCV数据计算ATR
#[inline]
pub fn atr_from_ohlcv(data: &[OHLCV], period: usize) -> Vec<f64> {
    let high: Vec<f64> = data.iter().map(|d| d.high).collect();
    let low: Vec<f64> = data.iter().map(|d| d.low).collect();
    let close: Vec<f64> = data.iter().map(|d| d.close).collect();
    atr(&high, &low, &close, period)
}

/// 生成ATR突破交易信号
#[inline]
pub fn atr_signals(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    atr_values: &[f64],
    multiplier: f64,
) -> Vec<i32> {
    let mut signals = vec![0; close.len()];

    for i in 1..close.len() {
        let upper = close[i - 1] + multiplier * atr_values[i];
        let lower = close[i - 1] - multiplier * atr_values[i];

        if high[i] > upper && close[i - 1] <= upper {
            signals[i] = 1; // Buy signal
        } else if low[i] < lower && close[i - 1] >= lower {
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
    fn test_atr() {
        let high = vec![1.5, 2.5, 3.5, 4.5, 5.0, 4.8, 4.5, 4.0, 3.5, 3.0];
        let low = vec![0.5, 1.5, 2.5, 3.5, 4.0, 3.8, 3.5, 3.0, 2.5, 2.0];
        let close = vec![1.0, 2.0, 3.0, 4.0, 4.5, 4.2, 4.0, 3.5, 3.0, 2.5];
        let result = atr(&high, &low, &close, 5);
        assert_eq!(result.len(), 10);
        assert!(result[0] >= 0.0);
    }
}
