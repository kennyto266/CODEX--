//! Signal generation module
//!
//! This module implements the logic for generating trading signals
//! from technical indicators using configurable thresholds.

use crate::core::data::{ParameterSet, TechnicalIndicator, TradingSignal, SignalAction};
use crate::core::error::BacktestError;

/// Generate trading signals from technical indicators
pub fn generate(
    indicators: &[TechnicalIndicator],
    parameters: &ParameterSet,
) -> Result<Vec<TradingSignal>, BacktestError> {
    // Validate parameters
    parameters.validate()?;

    let mut signals = Vec::new();

    // Group indicators by date
    let mut indicators_by_date: std::collections::HashMap<
        chrono::NaiveDate,
        Vec<&TechnicalIndicator>,
    > = std::collections::HashMap::new();

    for indicator in indicators {
        if indicator.is_valid {
            indicators_by_date
                .entry(indicator.date)
                .or_insert_with(Vec::new)
                .push(indicator);
        }
    }

    // Generate signals for each date
    for (date, inds) in indicators_by_date {
        let signal = generate_signal_for_date(date, inds, parameters)?;
        if let Some(signal) = signal {
            signals.push(signal);
        }
    }

    Ok(signals)
}

/// Generate signal for a specific date
fn generate_signal_for_date(
    date: chrono::NaiveDate,
    indicators: Vec<&TechnicalIndicator>,
    parameters: &ParameterSet,
) -> Result<Option<TradingSignal>, BacktestError> {
    let mut buy_signals = 0;
    let mut sell_signals = 0;
    let mut confidence_sum = 0.0;
    let mut source_indicators = Vec::new();
    let mut reasoning_parts = Vec::new();

    for indicator in indicators {
        let action = evaluate_indicator(indicator, parameters)?;
        match action {
            SignalAction::Buy => {
                buy_signals += 1;
                confidence_sum += 1.0;
            }
            SignalAction::Sell => {
                sell_signals += 1;
                confidence_sum += 1.0;
            }
            SignalAction::Hold => {}
        }

        source_indicators.push(format!(
            "{}_{:?}",
            indicator.base_symbol, indicator.indicator_type
        ));

        // Add reasoning
        if let Some(value) = indicator.value {
            let reason = match indicator.indicator_type {
                crate::core::data::IndicatorType::ZScore => {
                    if value <= parameters.zscore_buy {
                        format!("Z-Score={:.2} <= buy threshold({:.2})", value, parameters.zscore_buy)
                    } else if value >= parameters.zscore_sell {
                        format!("Z-Score={:.2} >= sell threshold({:.2})", value, parameters.zscore_sell)
                    } else {
                        format!("Z-Score={:.2} in neutral range", value)
                    }
                }
                crate::core::data::IndicatorType::RSI => {
                    if value <= parameters.rsi_buy {
                        format!("RSI={:.2} <= oversold({:.2})", value, parameters.rsi_buy)
                    } else if value >= parameters.rsi_sell {
                        format!("RSI={:.2} >= overbought({:.2})", value, parameters.rsi_sell)
                    } else {
                        format!("RSI={:.2} in neutral range", value)
                    }
                }
                _ => {
                    format!("{:?}=>{:.2}", indicator.indicator_type, value)
                }
            };
            reasoning_parts.push(reason);
        }
    }

    if buy_signals == 0 && sell_signals == 0 {
        return Ok(None); // No clear signal
    }

    // Determine final action (majority vote)
    let action = if buy_signals > sell_signals {
        SignalAction::Buy
    } else if sell_signals > buy_signals {
        SignalAction::Sell
    } else {
        SignalAction::Hold
    };

    let confidence = if source_indicators.is_empty() {
        0.0
    } else {
        confidence_sum / source_indicators.len() as f64
    };

    let mut signal = TradingSignal::new(
        "UNKNOWN".to_string(), // Will be set by caller
        date,
        action,
        confidence,
    );

    signal.source_indicators = source_indicators;
    signal.reasoning = reasoning_parts.join(", ");

    // Add parameters used
    signal.parameters.insert("zscore_buy".to_string(), parameters.zscore_buy);
    signal.parameters.insert("zscore_sell".to_string(), parameters.zscore_sell);
    signal.parameters.insert("rsi_buy".to_string(), parameters.rsi_buy);
    signal.parameters.insert("rsi_sell".to_string(), parameters.rsi_sell);

    Ok(Some(signal))
}

/// Evaluate a single indicator
fn evaluate_indicator(
    indicator: &TechnicalIndicator,
    parameters: &ParameterSet,
) -> Result<SignalAction, BacktestError> {
    let value = if let Some(val) = indicator.value {
        val
    } else {
        return Ok(SignalAction::Hold);
    };

    match indicator.indicator_type {
        crate::core::data::IndicatorType::ZScore => {
            if value <= parameters.zscore_buy {
                Ok(SignalAction::Buy)
            } else if value >= parameters.zscore_sell {
                Ok(SignalAction::Sell)
            } else {
                Ok(SignalAction::Hold)
            }
        }
        crate::core::data::IndicatorType::RSI => {
            if value <= parameters.rsi_buy {
                Ok(SignalAction::Buy)
            } else if value >= parameters.rsi_sell {
                Ok(SignalAction::Sell)
            } else {
                Ok(SignalAction::Hold)
            }
        }
        crate::core::data::IndicatorType::SMAFast => {
            // Would need to compare with SMASlow
            // For now, return Hold
            Ok(SignalAction::Hold)
        }
        crate::core::data::IndicatorType::SMASlow => {
            // Would need to compare with SMAFast
            Ok(SignalAction::Hold)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::data::{ParameterSet, TechnicalIndicator, IndicatorType};
    use chrono::NaiveDate;

    #[test]
    fn test_generate_signals() {
        let mut indicator = TechnicalIndicator::new(
            "TEST".to_string(),
            NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(),
            IndicatorType::ZScore,
            20,
        );
        indicator.set_value(-1.0);

        let parameters = ParameterSet::default();
        let signals = generate(&[indicator], &parameters).unwrap();

        assert!(!signals.is_empty());
        assert_eq!(signals[0].action, SignalAction::Buy);
    }
}
