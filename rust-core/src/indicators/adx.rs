//! ADX (平均方向性指数)

use crate::types::OHLCV;
use super::moving_average::sma;

/// 计算ADX
#[inline]
pub fn adx(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    period: usize,
) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    let mut dm_plus = vec![0.0; high.len()];
    let mut dm_minus = vec![0.0; high.len()];
    let mut tr_values = vec![0.0; high.len()];

    for i in 1..high.len() {
        let up_move = high[i] - high[i - 1];
        let down_move = low[i - 1] - low[i];

        dm_plus[i] = if up_move > down_move && up_move > 0.0 {
            up_move
        } else {
            0.0
        };
        dm_minus[i] = if down_move > up_move && down_move > 0.0 {
            down_move
        } else {
            0.0
        };

        let tr1 = high[i] - low[i];
        let tr2 = (high[i] - close[i - 1]).abs();
        let tr3 = (low[i] - close[i - 1]).abs();
        tr_values[i] = tr1.max(tr2).max(tr3);
    }

    let tr_smooth = sma(&tr_values, period);
    let dm_plus_smooth = sma(&dm_plus, period);
    let dm_minus_smooth = sma(&dm_minus, period);

    let mut di_plus = vec![0.0; high.len()];
    let mut di_minus = vec![0.0; high.len()];
    let mut adx = vec![0.0; high.len()];

    for i in period..high.len() {
        di_plus[i] = (dm_plus_smooth[i] / tr_smooth[i]) * 100.0;
        di_minus[i] = (dm_minus_smooth[i] / tr_smooth[i]) * 100.0;

        let dx = ((di_plus[i] - di_minus[i]).abs() / (di_plus[i] + di_minus[i])) * 100.0;
        adx[i] = if i == period {
            dx
        } else {
            (adx[i - 1] * (period as f64 - 1.0) + dx) / period as f64
        };
    }

    (adx, di_plus, di_minus)
}

/// 从OHLCV数据计算ADX
#[inline]
pub fn adx_from_ohlcv(
    data: &[OHLCV],
    period: usize,
) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    let high: Vec<f64> = data.iter().map(|d| d.high).collect();
    let low: Vec<f64> = data.iter().map(|d| d.low).collect();
    let close: Vec<f64> = data.iter().map(|d| d.close).collect();
    adx(&high, &low, &close, period)
}

/// 生成ADX交易信号
#[inline]
pub fn adx_signals(
    adx: &[f64],
    di_plus: &[f64],
    di_minus: &[f64],
    threshold: f64,
) -> Vec<i32> {
    let mut signals = vec![0; adx.len()];

    for i in 1..adx.len() {
        if adx[i] > threshold && di_plus[i] > di_minus[i] && di_plus[i - 1] <= di_minus[i - 1]
        {
            signals[i] = 1; // Buy signal
        } else if adx[i] > threshold
            && di_plus[i] < di_minus[i]
            && di_plus[i - 1] >= di_minus[i - 1]
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
    fn test_adx() {
        let high = vec![1.5, 2.5, 3.5, 4.5, 5.0, 4.8, 4.5, 4.0, 3.5, 3.0];
        let low = vec![0.5, 1.5, 2.5, 3.5, 4.0, 3.8, 3.5, 3.0, 2.5, 2.0];
        let close = vec![1.0, 2.0, 3.0, 4.0, 4.5, 4.2, 4.0, 3.5, 3.0, 2.5];
        let (adx_result, di_p, di_m) = adx(&high, &low, &close, 5);
        assert_eq!(adx_result.len(), 10);
        assert_eq!(di_p.len(), 10);
        assert_eq!(di_m.len(), 10);
    }
}
