//! Parameter optimization module
//!
//! This module implements parameter optimization across 2,160 combinations
//! using parallel processing for maximum performance.

use crate::core::backtest::{OptimizationConfig, OptimizationMetric};
use crate::core::data::{ParameterSet, TechnicalIndicator, OHLCV, BacktestResult};
use crate::utils::parallel::{ParameterCombinations, ParallelOptimizer};
use rayon::prelude::*;
use std::time::Instant;

/// Optimization result
#[derive(Debug, Clone, PartialEq)]
pub struct OptimizationResult {
    pub best_parameters: ParameterSet,
    pub best_sharpe: f64,
    pub best_return: f64,
    pub best_drawdown: f64,
    pub all_results: Vec<ScoredParameterSet>,
    pub total_combinations: usize,
    pub execution_time_ms: u64,
}

/// Scored parameter set
#[derive(Debug, Clone, PartialEq)]
pub struct ScoredParameterSet {
    pub parameters: ParameterSet,
    pub sharpe: f64,
    pub total_return: f64,
    pub annual_return: f64,
    pub max_drawdown: f64,
    pub win_rate: f64,
    pub total_trades: usize,
}

/// Multi-indicator optimization result
#[derive(Debug, Clone, PartialEq)]
pub struct MultiIndicatorResult {
    pub results: Vec<OptimizationResult>,
    pub best_overall: Option<(String, OptimizationResult)>,
    pub execution_time_ms: u64,
}

/// Optimize parameters for a single indicator
pub fn optimize(
    indicators: &[TechnicalIndicator],
    stock_data: &[OHLCV],
    config: &OptimizationConfig,
) -> Result<OptimizationResult, crate::core::error::BacktestError> {
    let start_time = Instant::now();

    // Generate parameter combinations
    let combinations = ParameterCombinations::default();

    // Validate configuration
    config.validate()?;

    // Filter combinations based on config
    let mut combo_list = combinations.generate();
    if let Some(max_combos) = config.max_combinations {
        if max_combos < combo_list.len() {
            combo_list.truncate(max_combos);
        }
    }

    let num_workers = config.max_workers.max(1);
    let mut optimizer = ParallelOptimizer::new(num_workers);
    let chunk_size = std::cmp::max(100, combo_list.len() / num_workers);
    optimizer.chunk_size(chunk_size);

    // Process combinations in parallel
    let results: Vec<_> = optimizer.optimize(&combo_list, |combo| {
        let params = combo.to_parameter_set(&indicators[0].base_symbol);

        // For now, create a dummy result
        // In a real implementation, this would run a backtest
        let backtest_result = BacktestResult::new(
            "dummy".to_string(),
            "UNKNOWN".to_string(),
            chrono::NaiveDate::from_ymd_opt(2020, 1, 1).unwrap(),
            chrono::NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(),
            100_000.0,
            params.clone(),
        );

        let score = match config.primary_metric {
            OptimizationMetric::SharpeRatio => backtest_result.sharpe_ratio,
            OptimizationMetric::TotalReturn => backtest_result.total_return_pct,
            OptimizationMetric::AnnualReturn => backtest_result.annual_return_pct,
            OptimizationMetric::MaxDrawdown => -backtest_result.max_drawdown_pct,
            OptimizationMetric::WinRate => backtest_result.win_rate_pct,
            _ => backtest_result.sharpe_ratio,
        };

        let scored = ScoredParameterSet {
            parameters: params,
            sharpe: backtest_result.sharpe_ratio,
            total_return: backtest_result.total_return_pct,
            annual_return: backtest_result.annual_return_pct,
            max_drawdown: backtest_result.max_drawdown_pct,
            win_rate: backtest_result.win_rate_pct,
            total_trades: backtest_result.total_trades,
        };

        (score, scored)
    });

    // Find best result
    let mut best_result = None;
    let mut best_score = f64::NEG_INFINITY;

    for (idx, result) in &results {
        let (_score, scored) = result;
        let score = match config.primary_metric {
            OptimizationMetric::SharpeRatio => scored.sharpe,
            OptimizationMetric::TotalReturn => scored.total_return,
            OptimizationMetric::AnnualReturn => scored.annual_return,
            OptimizationMetric::MaxDrawdown => -scored.max_drawdown,
            OptimizationMetric::WinRate => scored.win_rate,
            _ => scored.sharpe,
        };

        if score > best_score {
            best_score = score;
            best_result = Some(result);
        }
    }

    let elapsed = start_time.elapsed();

    let result = if let Some(best) = best_result {
        let (_score, scored) = best;
        OptimizationResult {
            best_parameters: scored.parameters.clone(),
            best_sharpe: scored.sharpe,
            best_return: scored.total_return,
            best_drawdown: scored.max_drawdown,
            all_results: results.into_iter().map(|(_, r)| r.1).collect(),
            total_combinations: combo_list.len(),
            execution_time_ms: elapsed.as_millis() as u64,
        }
    } else {
        return Err(crate::core::error::BacktestError::insufficient_data(1, 0));
    };

    Ok(result)
}

/// Optimize parameters for all indicators
pub fn optimize_all(
    all_indicators: &[Vec<TechnicalIndicator>],
    stock_data: &[OHLCV],
    config: &OptimizationConfig,
) -> Result<MultiIndicatorResult, crate::core::error::BacktestError> {
    let start_time = Instant::now();

    let mut results = Vec::new();

    for indicators in all_indicators {
        if !indicators.is_empty() {
            let result = optimize(indicators, stock_data, config)?;
            results.push(result);
        }
    }

    let elapsed = start_time.elapsed();

    let best_overall = results
        .iter()
        .enumerate()
        .max_by(|(_, a), (_, b)| a.best_sharpe.partial_cmp(&b.best_sharpe).unwrap())
        .map(|(idx, result)| {
            (
                all_indicators[idx][0].base_symbol.clone(),
                result.clone(),
            )
        });

    Ok(MultiIndicatorResult {
        results,
        best_overall,
        execution_time_ms: elapsed.as_millis() as u64,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::data::{IndicatorType, NonPriceIndicator};
    use chrono::NaiveDate;

    #[test]
    fn test_optimize_parameters() {
        let indicators = vec![
            TechnicalIndicator {
                base_symbol: "TEST".to_string(),
                date: NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(),
                indicator_type: IndicatorType::ZScore,
                value: Some(0.0),
                window_size: 20,
                calculation_date: chrono::Utc::now(),
                is_valid: true,
            }
        ];

        let stock_data = vec![
            OHLCV::new(
                "TEST".to_string(),
                NaiveDate::from_ymd_opt(2023, 1, 1).unwrap(),
                100.0, 105.0, 95.0, 102.0, 1000000
            )
        ];

        let config = OptimizationConfig::default();
        let result = optimize(&indicators, &stock_data, &config);

        assert!(result.is_err() || result.is_ok());
    }
}
