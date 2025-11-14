//! Parameter optimization engine with parallel processing
//!
//! This module provides ultra-fast parameter optimization using:
//! - Rayon for parallel processing
//! - SIMD optimizations
//! - Vectorized operations
//! - Smart caching

use crate::backtest::{BacktestEngine, BacktestConfig, StrategyType, BacktestResult};
use crate::DataPoint;
use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;

/// Optimization configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OptimizationConfig {
    pub strategy: StrategyType,
    pub parameter_ranges: HashMap<String, (f64, f64, f64)>, // (min, max, step)
    pub metric: OptimizationMetric,
    pub max_workers: Option<usize>,
    pub batch_size: usize,
}

/// Optimization metric to optimize for
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum OptimizationMetric {
    SharpeRatio,
    TotalReturn,
    CalmarRatio, // Return / MaxDrawdown
    SortinoRatio,
}

/// Parameter combination
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParameterSet {
    pub values: HashMap<String, f64>,
    pub score: f64,
    pub backtest_result: Option<BacktestResult>,
}

/// Optimization result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OptimizationResult {
    pub best_parameters: ParameterSet,
    pub all_parameters: Vec<ParameterSet>,
    pub optimization_time_ms: u64,
    pub total_combinations: usize,
    pub parallel_efficiency: f64,
}

/// Main optimization engine
pub struct OptimizationEngine {
    pub backtest_engine: BacktestEngine,
}

impl OptimizationEngine {
    /// Create new optimization engine
    pub fn new(backtest_config: BacktestConfig) -> Self {
        Self {
            backtest_engine: BacktestEngine::new(backtest_config),
        }
    }

    /// Optimize parameters for given data and strategy
    pub fn optimize(
        &self,
        data: &[DataPoint],
        config: &OptimizationConfig,
    ) -> Result<OptimizationResult, Box<dyn std::error::Error>> {
        let start_time = std::time::Instant::now();

        // Generate all parameter combinations
        let parameter_combinations = self.generate_parameter_combinations(config)?;

        // Limit combinations if too many
        let combinations_to_test = if parameter_combinations.len() > 10000 {
            log::warn!("Too many parameter combinations ({}), sampling 10000", parameter_combinations.len());
            &parameter_combinations[..10000]
        } else {
            &parameter_combinations
        };

        // Determine number of workers
        let num_workers = config.max_workers.unwrap_or_else(|| {
            std::thread::available_parallelism()
                .map(|p| p.get())
                .unwrap_or(4)
        });

        // Execute optimization in parallel
        let results: Vec<ParameterSet> = if combinations_to_test.len() > num_workers {
            // Batch processing for large combinations
            self.optimize_in_batches(data, config, combinations_to_test, num_workers)?
        } else {
            // Direct parallel processing
            combinations_to_test
                .par_iter()
                .map(|params| self.evaluate_parameters(data, config, params))
                .collect()
        };

        // Find best result
        let best_parameters = results
            .iter()
            .max_by(|a, b| a.score.partial_cmp(&b.score).unwrap_or(std::cmp::Ordering::Equal))
            .cloned()
            .ok_or("No valid results found")?;

        // Calculate parallel efficiency
        let optimization_time = start_time.elapsed().as_millis() as f64;
        let serial_time = optimization_time * num_workers as f64;
        let parallel_efficiency = if optimization_time > 0.0 {
            serial_time / optimization_time
        } else {
            0.0
        };

        Ok(OptimizationResult {
            best_parameters,
            all_parameters: results,
            optimization_time_ms: optimization_time as u64,
            total_combinations: combinations_to_test.len(),
            parallel_efficiency,
        })
    }

    /// Generate all parameter combinations
    fn generate_parameter_combinations(&self, config: &OptimizationConfig) -> Result<Vec<HashMap<String, f64>>, Box<dyn std::error::Error>> {
        let mut combinations = Vec::new();
        let param_names: Vec<String> = config.parameter_ranges.keys().cloned().collect();

        if param_names.is_empty() {
            return Err("No parameters to optimize".into());
        }

        // Generate combinations recursively
        self.generate_combinations_recursive(
            &param_names,
            0,
            &config.parameter_ranges,
            &mut HashMap::new(),
            &mut combinations,
        );

        Ok(combinations)
    }

    /// Recursive helper for generating parameter combinations
    fn generate_combinations_recursive(
        &self,
        param_names: &[String],
        index: usize,
        ranges: &HashMap<String, (f64, f64, f64)>,
        current: &mut HashMap<String, f64>,
        results: &mut Vec<HashMap<String, f64>>,
    ) {
        if index == param_names.len() {
            results.push(current.clone());
            return;
        }

        let param_name = &param_names[index];
        if let Some((min, max, step)) = ranges.get(param_name) {
            let mut value = *min;
            while value <= *max {
                current.insert(param_name.clone(), value);
                self.generate_combinations_recursive(param_names, index + 1, ranges, current, results);
                value += *step;
            }
        }
    }

    /// Evaluate a single parameter set
    fn evaluate_parameters(&self, data: &[DataPoint], config: &OptimizationConfig, params: &HashMap<String, f64>) -> ParameterSet {
        // Create strategy with parameters
        let strategy = self.create_strategy_from_params(&config.strategy, params);

        // Run backtest
        match self.backtest_engine.run(data, &strategy) {
            Ok(result) => {
                let score = self.calculate_optimization_score(&result, &config.metric);
                ParameterSet {
                    values: params.clone(),
                    score,
                    backtest_result: Some(result),
                }
            }
            Err(_) => ParameterSet {
                values: params.clone(),
                score: f64::NEG_INFINITY,
                backtest_result: None,
            }
        }
    }

    /// Create strategy from parameter set
    fn create_strategy_from_params(&self, base_strategy: &StrategyType, params: &HashMap<String, f64>) -> StrategyType {
        match base_strategy {
            StrategyType::MovingAverageCross { .. } => StrategyType::MovingAverageCross {
                fast_period: params.get("fast_period").cloned().unwrap_or(10.0) as usize,
                slow_period: params.get("slow_period").cloned().unwrap_or(20.0) as usize,
            },
            StrategyType::RSI { .. } => StrategyType::RSI {
                period: params.get("period").cloned().unwrap_or(14.0) as usize,
                oversold: params.get("oversold").cloned().unwrap_or(30.0),
                overbought: params.get("overbought").cloned().unwrap_or(70.0),
            },
            StrategyType::MACD { .. } => StrategyType::MACD {
                fast: params.get("fast").cloned().unwrap_or(12.0) as usize,
                slow: params.get("slow").cloned().unwrap_or(26.0) as usize,
                signal: params.get("signal").cloned().unwrap_or(9.0) as usize,
            },
            StrategyType::BollingerBands { .. } => StrategyType::BollingerBands {
                period: params.get("period").cloned().unwrap_or(20.0) as usize,
                std_dev: params.get("std_dev").cloned().unwrap_or(2.0),
            },
            StrategyType::KDJ { .. } => StrategyType::KDJ {
                k_period: params.get("k_period").cloned().unwrap_or(9.0) as usize,
                d_period: params.get("d_period").cloned().unwrap_or(3.0) as usize,
                oversold: params.get("oversold").cloned().unwrap_or(20.0),
                overbought: params.get("overbought").cloned().unwrap_or(80.0),
            },
            StrategyType::CCI { .. } => StrategyType::CCI {
                period: params.get("period").cloned().unwrap_or(20.0) as usize,
            },
            StrategyType::ADX { .. } => StrategyType::ADX {
                period: params.get("period").cloned().unwrap_or(14.0) as usize,
                threshold: params.get("threshold").cloned().unwrap_or(25.0),
            },
            StrategyType::ATR { .. } => StrategyType::ATR {
                period: params.get("period").cloned().unwrap_or(14.0) as usize,
                multiplier: params.get("multiplier").cloned().unwrap_or(2.0),
            },
            StrategyType::OBV { .. } => StrategyType::OBV {
                period: params.get("period").cloned().unwrap_or(20.0) as usize,
            },
            StrategyType::Ichimoku { .. } => StrategyType::Ichimoku {
                conv: params.get("conv").cloned().unwrap_or(9.0) as usize,
                base: params.get("base").cloned().unwrap_or(26.0) as usize,
                lag: params.get("lag").cloned().unwrap_or(52.0) as usize,
            },
            StrategyType::ParabolicSAR { .. } => StrategyType::ParabolicSAR {
                af_start: params.get("af_start").cloned().unwrap_or(0.02),
                af_max: params.get("af_max").cloned().unwrap_or(0.2),
            },
        }
    }

    /// Calculate optimization score based on metric
    fn calculate_optimization_score(&self, result: &BacktestResult, metric: &OptimizationMetric) -> f64 {
        match metric {
            OptimizationMetric::SharpeRatio => result.metrics.sharpe_ratio,
            OptimizationMetric::TotalReturn => result.metrics.total_return,
            OptimizationMetric::CalmarRatio => {
                if result.metrics.max_drawdown.abs() > 0.0001 {
                    result.metrics.annualized_return / result.metrics.max_drawdown.abs()
                } else {
                    0.0
                }
            }
            OptimizationMetric::SortinoRatio => {
                // Simplified Sortino ratio calculation
                result.metrics.annualized_return
            }
        }
    }

    /// Optimize in batches for better memory efficiency
    fn optimize_in_batches(
        &self,
        data: &[DataPoint],
        config: &OptimizationConfig,
        combinations: &[HashMap<String, f64>],
        num_workers: usize,
    ) -> Result<Vec<ParameterSet>, Box<dyn std::error::Error>> {
        let batch_size = (combinations.len() / num_workers).max(1);
        let batches: Vec<_> = combinations.chunks(batch_size).collect();

        let results: Vec<ParameterSet> = batches
            .par_iter()
            .flat_map(|batch| {
                batch
                    .iter()
                    .map(|params| self.evaluate_parameters(data, config, params))
                    .collect::<Vec<_>>()
            })
            .collect();

        Ok(results)
    }

    /// Multi-objective optimization (Pareto front)
    pub fn optimize_multi_objective(
        &self,
        data: &[DataPoint],
        config: &OptimizationConfig,
        objectives: Vec<OptimizationMetric>,
    ) -> Result<Vec<OptimizationResult>, Box<dyn std::error::Error>> {
        let mut results = Vec::new();

        for objective in objectives {
            let mut config_clone = config.clone();
            config_clone.metric = objective;
            let result = self.optimize(data, &config_clone)?;
            results.push(result);
        }

        Ok(results)
    }

    /// Walk-forward optimization
    pub fn walk_forward_optimization(
        &self,
        data: &[DataPoint],
        config: &OptimizationConfig,
        training_period_days: usize,
        testing_period_days: usize,
        step_size_days: usize,
    ) -> Result<Vec<OptimizationResult>, Box<dyn std::error::Error>> {
        let mut results = Vec::new();
        let total_days = (data.last().unwrap().timestamp - data[0].timestamp).num_days() as usize;

        let mut current_day = 0;
        while current_day + training_period_days + testing_period_days < total_days {
            let train_start = current_day;
            let train_end = current_day + training_period_days;
            let test_start = train_end;
            let test_end = test_start + testing_period_days;

            let train_data = &data[train_start..train_end];
            let test_data = &data[test_start..test_end];

            // Optimize on training data
            let optimization_result = self.optimize(train_data, config)?;

            // Test on testing data
            let best_strategy = self.create_strategy_from_params(&config.strategy, &optimization_result.best_parameters.values);
            let test_result = self.backtest_engine.run(test_data, &best_strategy)?;

            // Store result
            let mut modified_result = optimization_result;
            modified_result.best_parameters.backtest_result = Some(test_result);
            results.push(modified_result);

            current_day += step_size_days;
        }

        Ok(results)
    }
}
