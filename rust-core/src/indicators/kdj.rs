//! KDJ指标 (随机指标)

use crate::types::OHLCV;

/// 计算KDJ
#[inline]
pub fn kdj(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    k_period: usize,
    d_period: usize,
) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    let mut k_values = vec![50.0; close.len()];
    let mut d_values = vec![50.0; close.len()];
    let mut j_values = vec![50.0; close.len()];

    for i in k_period..close.len() {
        let window_high = &high[i - k_period..i];
        let window_low = &low[i - k_period..i];

        let highest = window_high.iter().fold(f64::NEG_INFINITY, |a, &b| a.max(b));
        let lowest = window_low.iter().fold(f64::INFINITY, |a, &b| a.min(b));

        if highest != lowest {
            let rsv = (close[i] - lowest) / (highest - lowest) * 100.0;
            k_values[i] = (rsv + (k_period as f64 - 1.0) * k_values[i - 1]) / k_period as f64;
        }

        if i >= k_period + d_period - 1 {
            let d_start = i - d_period + 1;
            d_values[i] = k_values[d_start..=i].iter().sum::<f64>() / d_period as f64;
        }

        j_values[i] = 3.0 * k_values[i] - 2.0 * d_values[i];
    }

    (k_values, d_values, j_values)
}

/// 从OHLCV数据计算KDJ
#[inline]
pub fn kdj_from_ohlcv(
    data: &[OHLCV],
    k_period: usize,
    d_period: usize,
) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    let high: Vec<f64> = data.iter().map(|d| d.high).collect();
    let low: Vec<f64> = data.iter().map(|d| d.low).collect();
    let close: Vec<f64> = data.iter().map(|d| d.close).collect();
    kdj(&high, &low, &close, k_period, d_period)
}

/// 生成KDJ交易信号
#[inline]
pub fn kdj_signals(
    k_values: &[f64],
    d_values: &[f64],
    oversold: f64,
    overbought: f64,
) -> Vec<i32> {
    let mut signals = vec![0; k_values.len()];

    for i in 1..k_values.len() {
        if k_values[i] > oversold
            && d_values[i] > oversold
            && k_values[i] > d_values[i]
            && k_values[i - 1] <= d_values[i - 1]
        {
            signals[i] = 1; // Buy signal
        } else if k_values[i] < overbought
            && d_values[i] < overbought
            && k_values[i] < d_values[i]
            && k_values[i - 1] >= d_values[i - 1]
        {
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
    fn test_kdj() {
        let high = vec![1.5, 2.5, 3.5, 4.5, 5.0, 4.8, 4.5, 4.0, 3.5, 3.0];
        let low = vec![0.5, 1.5, 2.5, 3.5, 4.0, 3.8, 3.5, 3.0, 2.5, 2.0];
        let close = vec![1.0, 2.0, 3.0, 4.0, 4.5, 4.2, 4.0, 3.5, 3.0, 2.5];
        let (k, d, j) = kdj(&high, &low, &close, 3, 3);
        assert_eq!(k.len(), 10);
        assert_eq!(d.len(), 10);
        assert_eq!(j.len(), 10);
    }
}
