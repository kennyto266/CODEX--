//! OBV (能量潮)

use crate::types::OHLCV;

/// 计算OBV
#[inline]
pub fn obv(close: &[f64], volume: &[u64]) -> Vec<f64> {
    let mut obv_values = vec![0.0; close.len()];

    if !close.is_empty() {
        obv_values[0] = volume[0] as f64;
    }

    for i in 1..close.len() {
        obv_values[i] = obv_values[i - 1];
        if close[i] > close[i - 1] {
            obv_values[i] += volume[i] as f64;
        } else if close[i] < close[i - 1] {
            obv_values[i] -= volume[i] as f64;
        }
    }

    obv_values
}

/// 从OHLCV数据计算OBV
#[inline]
pub fn obv_from_ohlcv(data: &[OHLCV]) -> Vec<f64> {
    let close: Vec<f64> = data.iter().map(|d| d.close).collect();
    let volume: Vec<u64> = data.iter().map(|d| d.volume as u64).collect();
    obv(&close, &volume)
}

/// 生成OBV交易信号
#[inline]
pub fn obv_signals(obv_values: &[f64], close: &[f64]) -> Vec<i32> {
    let mut signals = vec![0; close.len()];

    for i in 1..close.len() {
        if obv_values[i] > obv_values[i - 1] && close[i] > close[i - 1] {
            signals[i] = 1; // Buy signal
        } else if obv_values[i] < obv_values[i - 1] && close[i] < close[i - 1] {
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
    fn test_obv() {
        let close = vec![1.0, 2.0, 1.5, 2.5, 2.0];
        let volume = vec![100, 150, 120, 200, 180];
        let result = obv(&close, &volume);
        assert_eq!(result.len(), 5);
        assert!(result[1] > result[0]); // Price up, add volume
    }
}
