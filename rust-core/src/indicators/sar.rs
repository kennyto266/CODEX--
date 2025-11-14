//! 抛物线转向指标 (Parabolic SAR)

use crate::types::OHLCV;

/// 计算抛物线SAR
#[inline]
pub fn parabolic_sar(
    high: &[f64],
    low: &[f64],
    af_start: f64,
    af_max: f64,
) -> Vec<f64> {
    if high.len() < 2 {
        return vec![0.0; high.len()];
    }

    let mut sar = vec![0.0; high.len()];
    let mut af = af_start;
    let mut ep = if high[1] > high[0] { high[1] } else { low[1] };
    let mut trend = if high[1] > high[0] { 1.0 } else { -1.0 };

    sar[1] = if trend == 1.0 { low[0] } else { high[0] };

    for i in 2..high.len() {
        sar[i] = sar[i - 1] + af * (ep - sar[i - 1]);

        if trend == 1.0 && sar[i] > low[i] {
            trend = -1.0;
            af = af_start;
            ep = low[i];
            sar[i] = ep;
        } else if trend == -1.0 && sar[i] < high[i] {
            trend = 1.0;
            af = af_start;
            ep = high[i];
            sar[i] = ep;
        } else {
            if (trend == 1.0 && high[i] > ep) || (trend == -1.0 && low[i] < ep) {
                ep = if trend == 1.0 { high[i] } else { low[i] };
                af = (af + af_start).min(af_max);
            }
        }
    }

    sar
}

/// 从OHLCV数据计算抛物线SAR
#[inline]
pub fn parabolic_sar_from_ohlcv(
    data: &[OHLCV],
    af_start: f64,
    af_max: f64,
) -> Vec<f64> {
    let high: Vec<f64> = data.iter().map(|d| d.high).collect();
    let low: Vec<f64> = data.iter().map(|d| d.low).collect();
    parabolic_sar(&high, &low, af_start, af_max)
}

/// 生成抛物线SAR交易信号
#[inline]
pub fn parabolic_sar_signals(close: &[f64], sar: &[f64]) -> Vec<i32> {
    let mut signals = vec![0; close.len()];

    for i in 1..close.len() {
        if close[i] > sar[i] && close[i - 1] <= sar[i - 1] {
            signals[i] = 1; // Buy signal
        } else if close[i] < sar[i] && close[i - 1] >= sar[i - 1] {
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
    fn test_parabolic_sar() {
        let high = vec![1.5, 2.5, 3.5, 4.5, 5.0, 4.8, 4.5, 4.0, 3.5, 3.0];
        let low = vec![0.5, 1.5, 2.5, 3.5, 4.0, 3.8, 3.5, 3.0, 2.5, 2.0];
        let result = parabolic_sar(&high, &low, 0.02, 0.2);
        assert_eq!(result.len(), 10);
    }

    #[test]
    fn test_parabolic_sar_signals() {
        let close = vec![1.0, 2.0, 1.5, 2.5, 2.0];
        let sar = vec![0.9, 1.1, 1.4, 1.6, 1.8];
        let signals = parabolic_sar_signals(&close, &sar);
        assert_eq!(signals.len(), 5);
    }
}
