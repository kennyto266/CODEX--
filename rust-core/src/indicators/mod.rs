//! 技术指标模块
//! 包含11种技术指标的实现

pub mod moving_average;
pub mod rsi;
pub mod macd;
pub mod bollinger;
pub mod kdj;
pub mod cci;
pub mod adx;
pub mod atr;
pub mod obv;
pub mod ichimoku;
pub mod sar;

pub use moving_average::{sma, ema, wma, vwma, sma_from_ohlcv, ema_from_ohlcv, sma_parallel, ma_crossover};
pub use rsi::{rsi, rsi_from_ohlcv, rsi_signals};
pub use macd::{macd, macd_from_ohlcv, macd_signals};
pub use bollinger::{bollinger_bands, bollinger_bands_from_ohlcv, bollinger_signals};
pub use kdj::{kdj, kdj_from_ohlcv, kdj_signals};
pub use cci::{cci, cci_from_ohlcv, cci_signals};
pub use adx::{adx, adx_from_ohlcv, adx_signals};
pub use atr::{atr, atr_from_ohlcv, atr_signals};
pub use obv::{obv, obv_from_ohlcv, obv_signals};
pub use ichimoku::{ichimoku, ichimoku_from_ohlcv, ichimoku_signals};
pub use sar::{parabolic_sar, parabolic_sar_from_ohlcv, parabolic_sar_signals};

use crate::types::{OHLCV, Signal, SignalType};
// use rayon::prelude::*; // Not needed here
use std::collections::HashMap;

/// 指标配置
#[derive(Debug, Clone)]
pub struct IndicatorConfig {
    pub period: usize,
    pub threshold: Option<f64>,
    pub parameters: HashMap<String, f64>,
}

/// 指标值
#[derive(Debug, Clone)]
pub struct IndicatorValue {
    pub name: String,
    pub value: f64,
    pub signal: Option<SignalType>,
    pub timestamp: u64,
}

/// 计算所有指标（并行）
#[inline]
pub fn calculate_all_indicators(data: &[OHLCV]) -> HashMap<String, Vec<IndicatorValue>> {
    let close_prices: Vec<f64> = data.iter().map(|d| d.close).collect();
    let high_prices: Vec<f64> = data.iter().map(|d| d.high).collect();
    let low_prices: Vec<f64> = data.iter().map(|d| d.low).collect();
    let volumes: Vec<u64> = data.iter().map(|d| d.volume as u64).collect();

    // 并行计算指标
    let (sma_result, rsi_result) = rayon::join(
        || sma(&close_prices, 20),
        || rsi(&close_prices, 14),
    );

    let (macd_result, bollinger_result) = rayon::join(
        || macd(&close_prices, 12, 26, 9),
        || bollinger_bands(&close_prices, 20, 2.0),
    );

    let (kdj_result, cci_result) = rayon::join(
        || kdj(&high_prices, &low_prices, &close_prices, 9, 3),
        || cci(&high_prices, &low_prices, &close_prices, 20),
    );

    let (atr_result, obv_result) = rayon::join(
        || atr(&high_prices, &low_prices, &close_prices, 14),
        || obv(&close_prices, &volumes),
    );

    let (adx_result, psar_result) = rayon::join(
        || adx(&high_prices, &low_prices, &close_prices, 14),
        || parabolic_sar(&high_prices, &low_prices, 0.02, 0.2),
    );

    // 包装结果
    let mut indicators = HashMap::new();

    // SMA
    indicators.insert(
        "sma_20".to_string(),
        generate_signal_series(&sma_result, &close_prices, "sma_20", data, None),
    );

    // RSI
    indicators.insert(
        "rsi_14".to_string(),
        generate_signal_series(&rsi_result, &close_prices, "rsi_14", data, Some((30.0, 70.0))),
    );

    // MACD
    let macd_signals = macd_signals(&macd_result.0, &macd_result.1);
    indicators.insert(
        "macd".to_string(),
        generate_custom_signals(&macd_result.2, &close_prices, "macd", data, macd_signals),
    );

    // Bollinger Bands
    let bb_signals = bollinger_signals(&close_prices, &bollinger_result.0, &bollinger_result.2);
    indicators.insert(
        "bollinger".to_string(),
        generate_custom_signals(&close_prices, &close_prices, "bollinger", data, bb_signals),
    );

    // KDJ
    let kdj_signals_vec = kdj_signals(&kdj_result.0, &kdj_result.1, 20.0, 80.0);
    indicators.insert(
        "kdj".to_string(),
        generate_custom_signals(&kdj_result.0, &close_prices, "kdj", data, kdj_signals_vec),
    );

    // CCI
    indicators.insert(
        "cci".to_string(),
        generate_signal_series(&cci_result, &close_prices, "cci", data, None),
    );

    // ATR
    indicators.insert(
        "atr".to_string(),
        generate_signal_series(&atr_result, &close_prices, "atr", data, None),
    );

    // OBV
    indicators.insert(
        "obv".to_string(),
        generate_signal_series(&obv_result, &close_prices, "obv", data, None),
    );

    // ADX
    let adx_signals_vec = adx_signals(&adx_result.0, &adx_result.1, &adx_result.2, 25.0);
    indicators.insert(
        "adx".to_string(),
        generate_custom_signals(&adx_result.0, &close_prices, "adx", data, adx_signals_vec),
    );

    // Parabolic SAR
    let psar_signals_vec = parabolic_sar_signals(&close_prices, &psar_result);
    indicators.insert(
        "psar".to_string(),
        generate_custom_signals(&psar_result, &close_prices, "psar", data, psar_signals_vec),
    );

    indicators
}

/// 生成信号序列
fn generate_signal_series(
    indicator: &[f64],
    prices: &[f64], // _prices
    name: &str,
    data: &[OHLCV],
    thresholds: Option<(f64, f64)>,
) -> Vec<IndicatorValue> {
    let mut signals = Vec::with_capacity(indicator.len());

    for i in 0..indicator.len() {
        let signal = if let Some((low_thresh, high_thresh)) = thresholds {
            if indicator[i] < low_thresh {
                SignalType::Buy
            } else if indicator[i] > high_thresh {
                SignalType::Sell
            } else {
                SignalType::Hold
            }
        } else {
            if i > 0 {
                if indicator[i] > indicator[i - 1] {
                    SignalType::Buy
                } else if indicator[i] < indicator[i - 1] {
                    SignalType::Sell
                } else {
                    SignalType::Hold
                }
            } else {
                SignalType::Hold
            }
        };

        signals.push(IndicatorValue {
            name: name.to_string(),
            value: indicator[i],
            signal: Some(signal),
            timestamp: data[i].timestamp,
        });
    }

    signals
}

/// 生成自定义信号
fn generate_custom_signals(
    indicator: &[f64],
    prices: &[f64], // _prices
    name: &str,
    data: &[OHLCV],
    signal_values: Vec<i32>,
) -> Vec<IndicatorValue> {
    let mut signals = Vec::with_capacity(indicator.len());

    for i in 0..indicator.len() {
        let signal = match signal_values[i] {
            1 => SignalType::Buy,
            -1 => SignalType::Sell,
            _ => SignalType::Hold,
        };

        signals.push(IndicatorValue {
            name: name.to_string(),
            value: indicator[i],
            signal: Some(signal),
            timestamp: data[i].timestamp,
        });
    }

    signals
}
