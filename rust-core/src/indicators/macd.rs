//! MACD (指数平滑异同移动平均线)

use super::moving_average::ema;

/// 计算MACD
#[inline]
pub fn macd(
    prices: &[f64],
    fast_period: usize,
    slow_period: usize,
    signal_period: usize,
) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    let ema_fast = ema(prices, fast_period);
    let ema_slow = ema(prices, slow_period);
    let mut macd_line = vec![0.0; prices.len()];

    for i in 0..prices.len() {
        macd_line[i] = ema_fast[i] - ema_slow[i];
    }

    let signal_line = ema(&macd_line, signal_period);
    let mut histogram = vec![0.0; prices.len()];
    for i in 0..prices.len() {
        histogram[i] = macd_line[i] - signal_line[i];
    }

    (macd_line, signal_line, histogram)
}

/// 从OHLCV数据计算MACD
#[inline]
pub fn macd_from_ohlcv(
    data: &[crate::types::OHLCV],
    fast_period: usize,
    slow_period: usize,
    signal_period: usize,
) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    let prices: Vec<f64> = data.iter().map(|d| d.close).collect();
    macd(&prices, fast_period, slow_period, signal_period)
}

/// 生成MACD交易信号
#[inline]
pub fn macd_signals(macd_line: &[f64], signal_line: &[f64]) -> Vec<i32> {
    let mut signals = vec![0; macd_line.len()];

    for i in 1..macd_line.len() {
        let curr_diff = macd_line[i] - signal_line[i];
        let prev_diff = macd_line[i - 1] - signal_line[i - 1];

        if prev_diff <= 0.0 && curr_diff > 0.0 {
            signals[i] = 1; // Buy signal
        } else if prev_diff >= 0.0 && curr_diff < 0.0 {
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
    fn test_macd() {
        let prices = vec![1.0, 2.0, 3.0, 4.0, 5.0, 4.5, 4.0, 3.5, 3.0, 2.5];
        let (macd_line, signal_line, histogram) = macd(&prices, 3, 6, 3);
        assert_eq!(macd_line.len(), 10);
        assert_eq!(signal_line.len(), 10);
        assert_eq!(histogram.len(), 10);
    }

    #[test]
    fn test_macd_signals() {
        let macd_line = vec![0.0, -0.1, 0.05, 0.1, -0.05];
        let signal_line = vec![0.0, -0.05, 0.0, 0.05, 0.0];
        let signals = macd_signals(&macd_line, &signal_line);
        assert_eq!(signals.len(), 5);
    }
}
