//! 布林带 (Bollinger Bands)

use super::moving_average::sma;

/// 计算布林带
#[inline]
pub fn bollinger_bands(prices: &[f64], period: usize, num_std: f64) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    let sma_values = sma(prices, period);
    let mut upper = vec![0.0; prices.len()];
    let mut lower = vec![0.0; prices.len()];

    for i in period..prices.len() {
        let window = &prices[i - period..i];
        let mean = sma_values[i];
        let variance = window.iter().map(|&x| (x - mean).powi(2)).sum::<f64>() / period as f64;
        let std_dev = variance.sqrt();

        upper[i] = mean + num_std * std_dev;
        lower[i] = mean - num_std * std_dev;
    }

    (upper, sma_values, lower)
}

/// 从OHLCV数据计算布林带
#[inline]
pub fn bollinger_bands_from_ohlcv(
    data: &[crate::types::OHLCV],
    period: usize,
    num_std: f64,
) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    let prices: Vec<f64> = data.iter().map(|d| d.close).collect();
    bollinger_bands(&prices, period, num_std)
}

/// 生成布林带交易信号
#[inline]
pub fn bollinger_signals(prices: &[f64], upper: &[f64], lower: &[f64]) -> Vec<i32> {
    let mut signals = vec![0; prices.len()];

    for i in 1..prices.len() {
        if prices[i] < lower[i] && prices[i - 1] >= lower[i - 1] {
            signals[i] = 1; // Buy signal
        } else if prices[i] > upper[i] && prices[i - 1] <= upper[i - 1] {
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
    fn test_bollinger_bands() {
        let prices = vec![1.0, 2.0, 3.0, 4.0, 5.0, 4.5, 4.0, 3.5, 3.0, 2.5];
        let (upper, middle, lower) = bollinger_bands(&prices, 5, 2.0);
        assert_eq!(upper.len(), 10);
        assert_eq!(middle.len(), 10);
        assert_eq!(lower.len(), 10);
        assert!(upper[5] > middle[5]);
        assert!(lower[5] < middle[5]);
    }
}
