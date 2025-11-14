//! Unit tests for signal generation module
//!
//! This module tests the signal generation functionality including
//! indicator evaluation, threshold checking, and signal combination.

use rust_nonprice::core::data::{ParameterSet, TechnicalIndicator, IndicatorType, SignalAction, TradingSignal};
use rust_nonprice::strategy::signals;
use chrono::NaiveDate;

#[test]
fn test_generate_signals_zscore_buy() {
    let mut indicator = TechnicalIndicator::new(
        "HIBOR_1M".to_string(),
        NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(),
        IndicatorType::ZScore,
        20,
    );
    indicator.set_value(-2.0); // Well below buy threshold

    let parameters = ParameterSet::default();
    let signals = signals::generate(&[indicator], &parameters).unwrap();

    assert!(!signals.is_empty(), "Should generate at least one signal");
    assert_eq!(signals[0].action, SignalAction::Buy);
    assert!(signals[0].confidence > 0.0);
}

#[test]
fn test_generate_signals_zscore_sell() {
    let mut indicator = TechnicalIndicator::new(
        "HIBOR_1M".to_string(),
        NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(),
        IndicatorType::ZScore,
        20,
    );
    indicator.set_value(2.5); // Well above sell threshold

    let parameters = ParameterSet::default();
    let signals = signals::generate(&[indicator], &parameters).unwrap();

    assert!(!signals.is_empty(), "Should generate at least one signal");
    assert_eq!(signals[0].action, SignalAction::Sell);
    assert!(signals[0].confidence > 0.0);
}

#[test]
fn test_generate_signals_zscore_hold() {
    let mut indicator = TechnicalIndicator::new(
        "HIBOR_1M".to_string(),
        NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(),
        IndicatorType::ZScore,
        20,
    );
    indicator.set_value(0.5); // In neutral range

    let parameters = ParameterSet::default();
    let signals = signals::generate(&[indicator], &parameters).unwrap();

    assert!(signals.is_empty(), "Should not generate signal in neutral range");
}

#[test]
fn test_generate_signals_rsi_buy() {
    let mut indicator = TechnicalIndicator::new(
        "VISITOR_COUNT".to_string(),
        NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(),
        IndicatorType::RSI,
        14,
    );
    indicator.set_value(25.0); // Oversold

    let parameters = ParameterSet::default();
    let signals = signals::generate(&[indicator], &parameters).unwrap();

    assert!(!signals.is_empty(), "Should generate buy signal for oversold RSI");
    assert_eq!(signals[0].action, SignalAction::Buy);
}

#[test]
fn test_generate_signals_rsi_sell() {
    let mut indicator = TechnicalIndicator::new(
        "VISITOR_COUNT".to_string(),
        NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(),
        IndicatorType::RSI,
        14,
    );
    indicator.set_value(75.0); // Overbought

    let parameters = ParameterSet::default();
    let signals = signals::generate(&[indicator], &parameters).unwrap();

    assert!(!signals.is_empty(), "Should generate sell signal for overbought RSI");
    assert_eq!(signals[0].action, SignalAction::Sell);
}

#[test]
fn test_generate_signals_rsi_hold() {
    let mut indicator = TechnicalIndicator::new(
        "VISITOR_COUNT".to_string(),
        NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(),
        IndicatorType::RSI,
        14,
    );
    indicator.set_value(50.0); // Neutral

    let parameters = ParameterSet::default();
    let signals = signals::generate(&[indicator], &parameters).unwrap();

    assert!(signals.is_empty(), "Should not generate signal for neutral RSI");
}

#[test]
fn test_generate_signals_multiple_indicators_majority_buy() {
    let mut indicator1 = TechnicalIndicator::new(
        "HIBOR_1M".to_string(),
        NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(),
        IndicatorType::ZScore,
        20,
    );
    indicator1.set_value(-2.0);

    let mut indicator2 = TechnicalIndicator::new(
        "VISITOR_COUNT".to_string(),
        NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(),
        IndicatorType::RSI,
        14,
    );
    indicator2.set_value(20.0);

    let mut indicator3 = TechnicalIndicator::new(
        "TRAFFIC_SPEED".to_string(),
        NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(),
        IndicatorType::ZScore,
        20,
    );
    indicator3.set_value(-1.8);

    let parameters = ParameterSet::default();
    let signals = signals::generate(&[indicator1, indicator2, indicator3], &parameters).unwrap();

    assert!(!signals.is_empty(), "Should generate signal with multiple indicators");
    assert_eq!(signals[0].action, SignalAction::Buy, "Should be buy signal from majority");
    assert_eq!(signals[0].source_indicators.len(), 3, "Should include all 3 indicators");
}

#[test]
fn test_generate_signals_multiple_indicators_majority_sell() {
    let mut indicator1 = TechnicalIndicator::new(
        "HIBOR_1M".to_string(),
        NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(),
        IndicatorType::ZScore,
        20,
    );
    indicator1.set_value(2.0);

    let mut indicator2 = TechnicalIndicator::new(
        "VISITOR_COUNT".to_string(),
        NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(),
        IndicatorType::RSI,
        14,
    );
    indicator2.set_value(80.0);

    let mut indicator3 = TechnicalIndicator::new(
        "TRAFFIC_SPEED".to_string(),
        NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(),
        IndicatorType::ZScore,
        20,
    );
    indicator3.set_value(1.5);

    let parameters = ParameterSet::default();
    let signals = signals::generate(&[indicator1, indicator2, indicator3], &parameters).unwrap();

    assert!(!signals.is_empty(), "Should generate signal with multiple indicators");
    assert_eq!(signals[0].action, SignalAction::Sell, "Should be sell signal from majority");
}

#[test]
fn test_generate_signals_conflicting_indicators_hold() {
    let mut indicator1 = TechnicalIndicator::new(
        "HIBOR_1M".to_string(),
        NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(),
        IndicatorType::ZScore,
        20,
    );
    indicator1.set_value(-2.0); // Buy signal

    let mut indicator2 = TechnicalIndicator::new(
        "VISITOR_COUNT".to_string(),
        NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(),
        IndicatorType::RSI,
        14,
    );
    indicator2.set_value(80.0); // Sell signal

    let parameters = ParameterSet::default();
    let signals = signals::generate(&[indicator1, indicator2], &parameters).unwrap();

    // With equal buy and sell signals, should hold
    assert!(!signals.is_empty(), "Should still generate a signal");
    assert_eq!(signals[0].action, SignalAction::Hold, "Should hold with conflicting signals");
}

#[test]
fn test_generate_signals_with_custom_parameters() {
    let mut indicator = TechnicalIndicator::new(
        "HIBOR_1M".to_string(),
        NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(),
        IndicatorType::ZScore,
        20,
    );
    indicator.set_value(-1.2);

    let mut parameters = ParameterSet::default();
    parameters.zscore_buy = -1.5; // More conservative buy threshold
    parameters.zscore_sell = 1.5;

    let signals = signals::generate(&[indicator], &parameters).unwrap();

    // Value is -1.2, which is above the buy threshold of -1.5, so should not buy
    assert!(signals.is_empty(), "Should not generate signal with conservative parameters");
}

#[test]
fn test_generate_signals_invalid_indicator_value() {
    let mut indicator = TechnicalIndicator::new(
        "HIBOR_1M".to_string(),
        NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(),
        IndicatorType::ZScore,
        20,
    );
    // Don't set value - it will be None

    let parameters = ParameterSet::default();
    let signals = signals::generate(&[indicator], &parameters).unwrap();

    assert!(signals.is_empty(), "Should not generate signal for indicator without value");
}

#[test]
fn test_signal_reasoning() {
    let mut indicator = TechnicalIndicator::new(
        "HIBOR_1M".to_string(),
        NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(),
        IndicatorType::ZScore,
        20,
    );
    indicator.set_value(-2.0);

    let parameters = ParameterSet::default();
    let signals = signals::generate(&[indicator], &parameters).unwrap();

    assert!(!signals.is_empty());
    let signal = &signals[0];
    assert!(!signal.reasoning.is_empty(), "Should have reasoning text");
    assert!(signal.reasoning.contains("Z-Score"), "Should mention indicator type");
    assert!(signal.reasoning.contains("buy threshold"), "Should mention threshold");
}

#[test]
fn test_signal_parameters_stored() {
    let mut indicator = TechnicalIndicator::new(
        "HIBOR_1M".to_string(),
        NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(),
        IndicatorType::ZScore,
        20,
    );
    indicator.set_value(-2.0);

    let parameters = ParameterSet::default();
    let signals = signals::generate(&[indicator], &parameters).unwrap();

    assert!(!signals.is_empty());
    let signal = &signals[0];
    assert!(signal.parameters.contains_key("zscore_buy"), "Should store zscore_buy parameter");
    assert!(signal.parameters.contains_key("zscore_sell"), "Should store zscore_sell parameter");
    assert!(signal.parameters.contains_key("rsi_buy"), "Should store rsi_buy parameter");
    assert!(signal.parameters.contains_key("rsi_sell"), "Should store rsi_sell parameter");
}

#[test]
fn test_parameter_validation() {
    let parameters = ParameterSet {
        id: "test".to_string(),
        indicator_name: "TEST".to_string(),
        zscore_buy: 1.0,  // Should be negative!
        zscore_sell: 2.0,
        rsi_buy: 40.0,
        rsi_sell: 30.0,  // Should be > rsi_buy!
        sma_fast: 10,
        sma_slow: 5,     // Should be > sma_fast!
        created_at: chrono::Utc::now(),
    };

    let result = parameters.validate();

    assert!(result.is_err(), "Invalid parameters should fail validation");
}

#[test]
fn test_parameter_validation_valid() {
    let parameters = ParameterSet::default();

    let result = parameters.validate();

    assert!(result.is_ok(), "Valid parameters should pass validation");
}
