//! CCI (商品通道指数)

use crate::types::OHLCV;

/// 计算CCI
#[inline]
pub fn cci(high: &[f64], low: &[f64], close: &[f64], period: usize) -> Vec<f64> {
    let mut cci_values = vec![0.0; close.len()];

    for i in period..close.len() {
        let typical_prices: Vec<f64> = (0..period)
            .map(|j| (high[i - j] + low[i - j] + close[i - j]) / 3.0)
            .collect();

        let sma_tp: f64 = typical_prices.iter().sum::<f64>() / period as f64;
        let mean_dev: f64 = typical_prices
            .iter()
            .map(|&x| (x - sma_tp).abs())
            .sum::<f64>()
            / period as f64;

        let current_tp = (high[i] + low[i] + close[i]) / 3.0;
        cci_values[i] = (current_tp - sma_tp) / (0.015 * mean_dev);
    }

    cci_values
}

/// 从OHLCV数据计算CCI
#[inline]
pub fn cci_from_ohlcv(data: &[OHLCV], period: usize) -> Vec<f64> {
    let high: Vec<f64> = data.iter().map(|d| d.high).collect();
    let low: Vec<f64> = data.iter().map(|d| d.low).collect();
    let close: Vec<f64> = data.iter().map(|d| d.close).collect();
    cci(&high, &low, &close, period)
}

/// 生成CCI交易信号
#[inline]
pub fn cci_signals(cci_values: &[f64]) -> Vec<i32> {
    let mut signals = vec![0; cci_values.len()];

    for i in 1..cci_values.len() {
        if cci_values[i] < -100.0 && cci_values[i - 1] >= -100.0 {
            signals[i] = 1; // Buy signal
        } else if cci_values[i] > 100.0 && cci_values[i - 1] <= 100.0 {
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
    fn test_cci() {
        let high = vec![1.5, 2.5, 3.5, 4.5, 5.0, 4.8, 4.5, 4.0, 3.5, 3.0];
        let low = vec![0.5, 1.5, 2.5, 3.5, 4.0, 3.8, 3.5, 3.0, 2.5, 2.0];
        let close = vec![1.0, 2.0, 3.0, 4.0, 4.5, 4.2, 4.0, 3.5, 3.0, 2.5];
        let result = cci(&high, &low, &close, 5);
        assert_eq!(result.len(), 10);
    }
}
