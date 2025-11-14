//! 移动平均线指标
//! 包含SMA, EMA, WMA, VWMA等变体

use crate::types::OHLCV;
use rayon::prelude::*;

/// 简单移动平均线 (Simple Moving Average)
#[inline]
pub fn sma(prices: &[f64], period: usize) -> Vec<f64> {
    if prices.is_empty() || period == 0 {
        return Vec::new();
    }

    let mut result = vec![0.0; prices.len()];
    let mut sum = 0.0;

    // 初始化第一个窗口
    for i in 0..period.min(prices.len()) {
        sum += prices[i];
    }

    // 填充初始值
    for i in 0..period.min(prices.len()) {
        result[i] = prices[i];
    }

    // 使用滑动窗口计算SMA
    for i in period..prices.len() {
        sum += prices[i] - prices[i - period];
        result[i] = sum / period as f64;
    }

    result
}

/// 指数移动平均线 (Exponential Moving Average)
#[inline]
pub fn ema(prices: &[f64], period: usize) -> Vec<f64> {
    if prices.is_empty() || period == 0 {
        return Vec::new();
    }

    let mut result = vec![0.0; prices.len()];
    let multiplier = 2.0 / (period as f64 + 1.0);

    result[0] = prices[0];

    for i in 1..prices.len() {
        result[i] = (prices[i] - result[i - 1]) * multiplier + result[i - 1];
    }

    result
}

/// 加权移动平均线 (Weighted Moving Average)
#[inline]
pub fn wma(prices: &[f64], period: usize) -> Vec<f64> {
    if prices.is_empty() || period == 0 {
        return Vec::new();
    }

    let mut result = vec![0.0; prices.len()];

    for i in 0..prices.len() {
        if i + 1 >= period {
            let mut weighted_sum = 0.0;
            let mut weight_sum = 0.0;

            for j in 0..period {
                let weight = (period - j) as f64;
                weighted_sum += prices[i - j] * weight;
                weight_sum += weight;
            }

            result[i] = weighted_sum / weight_sum;
        } else {
            result[i] = prices[i];
        }
    }

    result
}

/// 成交量加权移动平均线 (Volume Weighted Moving Average)
#[inline]
pub fn vwma(prices: &[f64], volumes: &[u64], period: usize) -> Vec<f64> {
    if prices.is_empty() || volumes.is_empty() || period == 0 || prices.len() != volumes.len() {
        return Vec::new();
    }

    let mut result = vec![0.0; prices.len()];

    for i in 0..prices.len() {
        if i + 1 >= period {
            let mut weighted_sum = 0.0;
            let mut volume_sum = 0.0;

            for j in 0..period {
                let volume = volumes[i - j] as f64;
                weighted_sum += prices[i - j] * volume;
                volume_sum += volume;
            }

            result[i] = if volume_sum > 0.0 {
                weighted_sum / volume_sum
            } else {
                prices[i]
            };
        } else {
            result[i] = prices[i];
        }
    }

    result
}

/// 从OHLCV数据计算移动平均线
#[inline]
pub fn sma_from_ohlcv(data: &[OHLCV], period: usize) -> Vec<f64> {
    let prices: Vec<f64> = data.iter().map(|d| d.close).collect();
    sma(&prices, period)
}

/// 从OHLCV数据计算指数移动平均线
#[inline]
pub fn ema_from_ohlcv(data: &[OHLCV], period: usize) -> Vec<f64> {
    let prices: Vec<f64> = data.iter().map(|d| d.close).collect();
    ema(&prices, period)
}

/// 并行计算多个周期的移动平均线
#[inline]
pub fn sma_parallel(prices: &[f64], periods: &[usize]) -> Vec<Vec<f64>> {
    periods
        .par_iter()
        .map(|&period| sma(prices, period))
        .collect()
}

/// 计算移动平均线交叉信号
#[inline]
pub fn ma_crossover(short_ma: &[f64], long_ma: &[f64], threshold: f64) -> Vec<i32> {
    let mut signals = vec![0; short_ma.len()];

    for i in 1..short_ma.len() {
        let diff = short_ma[i] - long_ma[i];
        let prev_diff = short_ma[i - 1] - long_ma[i - 1];

        if diff.abs() < threshold {
            signals[i] = 0; // No signal
        } else if prev_diff <= 0.0 && diff > 0.0 {
            signals[i] = 1; // Buy signal
        } else if prev_diff >= 0.0 && diff < 0.0 {
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
    fn test_sma() {
        let prices = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let result = sma(&prices, 3);
        assert_eq!(result.len(), 5);
        assert!((result[2] - 2.0).abs() < 1e-10);
        assert!((result[3] - 3.0).abs() < 1e-10);
    }

    #[test]
    fn test_ema() {
        let prices = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let result = ema(&prices, 3);
        assert_eq!(result.len(), 5);
        assert_eq!(result[0], 1.0);
    }

    #[test]
    fn test_wma() {
        let prices = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let result = wma(&prices, 3);
        assert_eq!(result.len(), 5);
        // WMA for period 3: (3*price[i] + 2*price[i-1] + 1*price[i-2]) / 6
        assert!((result[2] - 2.666).abs() < 0.01);
    }

    #[test]
    fn test_vwma() {
        let prices = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let volumes = vec![10, 20, 30, 40, 50];
        let result = vwma(&prices, &volumes, 3);
        assert_eq!(result.len(), 5);
    }

    #[test]
    fn test_ma_crossover() {
        let short_ma = vec![1.0, 2.0, 3.0, 2.5, 2.0];
        let long_ma = vec![2.0, 2.0, 2.5, 2.5, 2.5];
        let signals = ma_crossover(&short_ma, &long_ma, 0.1);
        assert_eq!(signals.len(), 5);
        assert_eq!(signals[3], -1); // Sell signal when short MA crosses below long MA
    }
}
