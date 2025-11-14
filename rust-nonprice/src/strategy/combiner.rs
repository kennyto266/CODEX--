//! Signal combination strategies
//!
//! This module provides different methods for combining signals
//! from multiple indicators.

use crate::core::data::{ParameterSet, TechnicalIndicator, TradingSignal, SignalAction};
use crate::core::error::BacktestError;

/// Signal combination strategy
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CombinationStrategy {
    MajorityVote,
    Consensus,
    Weighted,
    BestPerformer,
}

/// Generate combined signals from multiple indicators
pub fn generate_combined(
    indicators: &[TechnicalIndicator],
    parameter_sets: &[ParameterSet],
    strategy: CombinationStrategy,
) -> Result<Vec<TradingSignal>, BacktestError> {
    match strategy {
        CombinationStrategy::MajorityVote => generate_majority_vote(indicators, parameter_sets),
        CombinationStrategy::Consensus => generate_consensus(indicators, parameter_sets),
        CombinationStrategy::Weighted => generate_weighted(indicators, parameter_sets),
        CombinationStrategy::BestPerformer => generate_best_performer(indicators, parameter_sets),
    }
}

/// Majority vote: use signal from majority of indicators
fn generate_majority_vote(
    indicators: &[TechnicalIndicator],
    parameter_sets: &[ParameterSet],
) -> Result<Vec<TradingSignal>, BacktestError> {
    // For simplicity, use first parameter set
    let binding = ParameterSet::default();
    let params = parameter_sets.first().unwrap_or(&binding);
    crate::strategy::signals::generate(indicators, params)
}

/// Consensus: all indicators must agree
fn generate_consensus(
    indicators: &[TechnicalIndicator],
    parameter_sets: &[ParameterSet],
) -> Result<Vec<TradingSignal>, BacktestError> {
    let binding = ParameterSet::default();
    let params = parameter_sets.first().unwrap_or(&binding);
    let signals = crate::strategy::signals::generate(indicators, params)?;

    // Filter to only signals where all indicators agree
    let mut combined_signals = Vec::new();

    for signal in signals {
        if signal.source_indicators.len() == indicators.len() {
            combined_signals.push(signal);
        }
    }

    Ok(combined_signals)
}

/// Weighted: weighted by confidence
fn generate_weighted(
    indicators: &[TechnicalIndicator],
    parameter_sets: &[ParameterSet],
) -> Result<Vec<TradingSignal>, BacktestError> {
    // Implementation would weight signals by historical performance
    // For now, use majority vote
    generate_majority_vote(indicators, parameter_sets)
}

/// Best performer: use signal from historically best indicator
fn generate_best_performer(
    indicators: &[TechnicalIndicator],
    parameter_sets: &[ParameterSet],
) -> Result<Vec<TradingSignal>, BacktestError> {
    // Implementation would track historical performance
    // For now, use majority vote
    generate_majority_vote(indicators, parameter_sets)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::data::{TechnicalIndicator, ParameterSet, IndicatorType};
    use chrono::NaiveDate;

    #[test]
    fn test_generate_combined_majority() {
        let indicators = vec![
            TechnicalIndicator {
                base_symbol: "TEST".to_string(),
                date: NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(),
                indicator_type: IndicatorType::ZScore,
                value: Some(-1.0),
                window_size: 20,
                calculation_date: chrono::Utc::now(),
                is_valid: true,
            }
        ];

        let params = ParameterSet::default();
        let signals = generate_combined(&indicators, &[params], CombinationStrategy::MajorityVote).unwrap();

        assert!(!signals.is_empty());
    }
}
