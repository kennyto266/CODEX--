//! 一目均衡表 (Ichimoku)

use crate::types::OHLCV;
use super::moving_average::sma;

/// 计算一目均衡表
#[inline]
pub fn ichimoku(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    conv_period: usize,
    base_period: usize,
    lag_period: usize,
) -> (
    Vec<f64>,  // Tenkan-sen
    Vec<f64>,  // Kijun-sen
    Vec<f64>,  // Senkou Span A
    Vec<f64>,  // Senkou Span B
    Vec<f64>,  // Chikou Span
) {
    let tenkan_sen = ichimoku_tenkan(high, low, conv_period);
    let kijun_sen = ichimoku_kijun(high, low, base_period);
    let senkou_span_a = ichimoku_senkou_a(&tenkan_sen, &kijun_sen);
    let senkou_span_b = ichimoku_senkou_b(high, low, lag_period * 2);
    let chikou_span = ichimoku_chikou(close, lag_period);

    (tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b, chikou_span)
}

/// 计算转换线 (Tenkan-sen)
#[inline]
fn ichimoku_tenkan(high: &[f64], low: &[f64], period: usize) -> Vec<f64> {
    if high.is_empty() || low.is_empty() || period == 0 {
        return Vec::new();
    }

    let mut result = vec![0.0; high.len()];

    for i in 0..high.len() {
        if i + 1 >= period {
            let window_high = &high[i - period + 1..=i];
            let window_low = &low[i - period + 1..=i];

            let highest = window_high.iter().fold(f64::NEG_INFINITY, |a, &b| a.max(b));
            let lowest = window_low.iter().fold(f64::INFINITY, |a, &b| a.min(b));

            result[i] = (highest + lowest) / 2.0;
        } else {
            result[i] = high[i]; // 初期值使用当前高价
        }
    }

    result
}

/// 计算基准线 (Kijun-sen)
#[inline]
fn ichimoku_kijun(high: &[f64], low: &[f64], period: usize) -> Vec<f64> {
    if high.is_empty() || low.is_empty() || period == 0 {
        return Vec::new();
    }

    let mut result = vec![0.0; high.len()];

    for i in 0..high.len() {
        if i + 1 >= period {
            let window_high = &high[i - period + 1..=i];
            let window_low = &low[i - period + 1..=i];

            let highest = window_high.iter().fold(f64::NEG_INFINITY, |a, &b| a.max(b));
            let lowest = window_low.iter().fold(f64::INFINITY, |a, &b| a.min(b));

            result[i] = (highest + lowest) / 2.0;
        } else {
            result[i] = high[i];
        }
    }

    result
}

/// 计算先行带A (Senkou Span A)
#[inline]
fn ichimoku_senkou_a(tenkan: &[f64], kijun: &[f64]) -> Vec<f64> {
    tenkan
        .iter()
        .zip(kijun.iter())
        .map(|(&t, &k)| (t + k) / 2.0)
        .collect()
}

/// 计算先行带B (Senkou Span B)
#[inline]
fn ichimoku_senkou_b(high: &[f64], low: &[f64], period: usize) -> Vec<f64> {
    if high.is_empty() || low.is_empty() || period == 0 {
        return Vec::new();
    }

    let mut result = vec![0.0; high.len()];

    for i in 0..high.len() {
        if i + 1 >= period {
            let window_high = &high[i - period + 1..=i];
            let window_low = &low[i - period + 1..=i];

            let highest = window_high.iter().fold(f64::NEG_INFINITY, |a, &b| a.max(b));
            let lowest = window_low.iter().fold(f64::INFINITY, |a, &b| a.min(b));

            result[i] = (highest + lowest) / 2.0;
        } else {
            result[i] = high[i];
        }
    }

    result
}

/// 计算滞后线 (Chikou Span)
#[inline]
fn ichimoku_chikou(close: &[f64], lag: usize) -> Vec<f64> {
    if close.is_empty() {
        return Vec::new();
    }

    let mut result = vec![0.0; close.len()];

    for i in 0..close.len() {
        if i >= lag {
            result[i] = close[i - lag];
        } else {
            result[i] = close[i];
        }
    }

    result
}

/// 从OHLCV数据计算一目均衡表
#[inline]
pub fn ichimoku_from_ohlcv(
    data: &[OHLCV],
    conv_period: usize,
    base_period: usize,
    lag_period: usize,
) -> (
    Vec<f64>,
    Vec<f64>,
    Vec<f64>,
    Vec<f64>,
    Vec<f64>,
) {
    let high: Vec<f64> = data.iter().map(|d| d.high).collect();
    let low: Vec<f64> = data.iter().map(|d| d.low).collect();
    let close: Vec<f64> = data.iter().map(|d| d.close).collect();
    ichimoku(&high, &low, &close, conv_period, base_period, lag_period)
}

/// 生成一目均衡表交易信号
#[inline]
pub fn ichimoku_signals(
    close: &[f64],
    tenkan: &[f64],
    kijun: &[f64],
    ssa: &[f64],
    ssb: &[f64],
) -> Vec<i32> {
    let mut signals = vec![0; close.len()];

    for i in 1..close.len() {
        if i < ssa.len() && i < ssb.len() {
            let cloud_high = ssa[i].max(ssb[i]);
            let cloud_low = ssa[i].min(ssb[i]);

            if close[i] > cloud_high && tenkan[i] > kijun[i] {
                signals[i] = 1; // Buy signal
            } else if close[i] < cloud_low && tenkan[i] < kijun[i] {
                signals[i] = -1; // Sell signal
            } else {
                signals[i] = 0; // Hold
            }
        }
    }

    signals
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ichimoku_tenkan() {
        let high = vec![1.5, 2.5, 3.5, 4.5, 5.0];
        let low = vec![0.5, 1.5, 2.5, 3.5, 4.0];
        let result = ichimoku_tenkan(&high, &low, 3);
        assert_eq!(result.len(), 5);
    }

    #[test]
    fn test_ichimoku_senkou_a() {
        let tenkan = vec![1.0, 2.0, 3.0];
        let kijun = vec![1.5, 2.5, 3.5];
        let ssa = ichimoku_senkou_a(&tenkan, &kijun);
        assert_eq!(ssa, vec![1.25, 2.25, 3.25]);
    }
}
