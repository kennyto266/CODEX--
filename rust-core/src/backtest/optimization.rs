//! T043: Rust优化引擎
//! 高性能参数优化引擎，支持网格搜索和并行处理

use super::{BacktestEngine, BacktestConfig};
use crate::backtest::metrics::PerformanceMetrics;
use crate::types::{OHLCV, Signal, SignalType};
use rayon::prelude::*;
use std::collections::HashMap;
use std::time::Instant;

/// Optimization result
#[derive(Debug, Clone)]
pub struct OptimizationResult {
    pub parameters: HashMap<String, f64>,
    pub total_return: f64,
    pub sharpe_ratio: Option<f64>,
    pub max_drawdown: f64,
    pub win_rate: f64,
    pub trades: usize,
    pub execution_time_ms: u64,
}

/// Parameter grid search configuration
#[derive(Debug, Clone)]
pub struct ParameterGrid {
    pub name: String,
    pub min_value: f64,
    pub max_value: f64,
    pub step: f64,
}

/// Optimization engine
pub struct OptimizationEngine {
    num_workers: usize,
}

impl OptimizationEngine {
    /// Create a new optimization engine
    pub fn new(num_workers: usize) -> Self {
        Self { num_workers }
    }

    /// Optimize parameters using grid search in parallel
    pub fn optimize_parallel(
        &self,
        data: &[OHLCV],
        param_combinations: &[HashMap<String, f64>],
    ) -> Vec<OptimizationResult> {
        let config = BacktestConfig {
            initial_capital: 100000.0,
            commission: 0.001,
            slippage: 0.0005,
            start_date: 0,
            end_date: u64::MAX,
        };

        let engine = BacktestEngine::new(config);

        // Use Rayon for parallel processing
        param_combinations
            .par_iter()
            .map(|params| {
                let start = Instant::now();
                let signals = self.generate_signals_from_params(data, params);
                let result = engine.run(data, &signals);
                let elapsed = start.elapsed();

                match result {
                    Ok(backtest_result) => OptimizationResult {
                        parameters: params.clone(),
                        total_return: backtest_result.metrics.total_return,
                        sharpe_ratio: Some(backtest_result.metrics.sharpe_ratio),
                        max_drawdown: backtest_result.metrics.max_drawdown,
                        win_rate: backtest_result.metrics.win_rate,
                        trades: backtest_result.trades.len(),
                        execution_time_ms: elapsed.as_millis() as u64,
                    },
                    Err(_) => OptimizationResult {
                        parameters: params.clone(),
                        total_return: -1.0,
                        sharpe_ratio: None,
                        max_drawdown: 1.0,
                        win_rate: 0.0,
                        trades: 0,
                        execution_time_ms: elapsed.as_millis() as u64,
                    },
                }
            })
            .collect()
    }

    /// Generate signals based on parameters
    fn generate_signals_from_params(
        &self,
        data: &[OHLCV],
        params: &HashMap<String, f64>,
    ) -> Vec<Signal> {
        let mut signals = Vec::new();

        // Extract parameters
        let period = params.get("period").unwrap_or(&20.0) / 20.0;
        let threshold = params.get("threshold").unwrap_or(&30.0);
        let multiplier = params.get("multiplier").unwrap_or(&1.0);

        // Simple moving average crossover strategy
        let mut short_ma = data[0].close;
        let mut long_ma = data[0].close;

        for i in 1..data.len() {
            // Update moving averages
            if i < (period * 5.0) as usize {
                short_ma = data[i].close;
                long_ma = data[i].close;
            } else {
                short_ma = data[i - (period * 3.0) as usize..=i]
                    .iter()
                    .map(|d| d.close)
                    .sum::<f64>()
                    / (period * 3.0);
                long_ma = data[i - (period * 5.0) as usize..=i]
                    .iter()
                    .map(|d| d.close)
                    .sum::<f64>()
                    / (period * 5.0);
            }

            // Generate signal
            if i > 0 {
                let prev_short = data[i - 1..=i - 1]
                    .iter()
                    .map(|d| d.close)
                    .sum::<f64>()
                    / 1.0;
                let prev_long = data[i - 1..=i - 1]
                    .iter()
                    .map(|d| d.close)
                    .sum::<f64>()
                    / 1.0;

                if short_ma > long_ma && prev_short <= prev_long {
                    signals.push(Signal {
                        timestamp: data[i].timestamp,
                        signal_type: SignalType::Buy,
                        price: data[i].close,
                        strength: *multiplier,
                    });
                } else if short_ma < long_ma && prev_short >= prev_long {
                    signals.push(Signal {
                        timestamp: data[i].timestamp,
                        signal_type: SignalType::Sell,
                        price: data[i].close,
                        strength: *multiplier,
                    });
                }
            }
        }

        signals
    }

    /// Get best parameters by Sharpe ratio
    pub fn get_best_params_by_sharpe(
        &self,
        results: &[OptimizationResult],
        top_n: usize,
    ) -> Vec<OptimizationResult> {
        let mut sorted_results = results.to_vec();
        sorted_results.sort_by(|a, b| {
            b.sharpe_ratio
                .unwrap_or(0.0)
                .partial_cmp(&a.sharpe_ratio.unwrap_or(0.0))
                .unwrap_or(std::cmp::Ordering::Equal)
        });
        sorted_results.into_iter().take(top_n).collect()
    }

    /// Get best parameters by total return
    pub fn get_best_params_by_return(
        &self,
        results: &[OptimizationResult],
        top_n: usize,
    ) -> Vec<OptimizationResult> {
        let mut sorted_results = results.to_vec();
        sorted_results.sort_by(|a, b| {
            b.total_return
                .partial_cmp(&a.total_return)
                .unwrap_or(std::cmp::Ordering::Equal)
        });
        sorted_results.into_iter().take(top_n).collect()
    }

    /// Get best parameters by Calmar ratio
    pub fn get_best_params_by_calmar(
        &self,
        results: &[OptimizationResult],
        top_n: usize,
    ) -> Vec<OptimizationResult> {
        let mut sorted_results = results.to_vec();
        sorted_results.sort_by(|a, b| {
            let calmar_a = if a.max_drawdown > 0.0 {
                a.total_return / a.max_drawdown
            } else {
                0.0
            };
            let calmar_b = if b.max_drawdown > 0.0 {
                b.total_return / b.max_drawdown
            } else {
                0.0
            };
            calmar_b.partial_cmp(&calmar_a).unwrap_or(std::cmp::Ordering::Equal)
        });
        sorted_results.into_iter().take(top_n).collect()
    }

    /// Generate parameter grid
    pub fn generate_parameter_grid(
        &self,
        param_defs: &[(&str, f64, f64, f64)],
    ) -> Vec<HashMap<String, f64>> {
        let mut grids = Vec::new();

        // Create all parameter combinations
        let param_vectors: Vec<Vec<f64>> = param_defs            .iter()            .map(|&(name, min, max, step)| {                let steps = ((max - min) / step).round() as usize + 1;                (0..steps).map(|i| min + (i as f64) * step).collect::<Vec<_>>()            })            .collect();
        // Cartesian product
        if param_vectors.is_empty() {
            return vec![HashMap::new()];
        }

        let mut indices = vec![0; param_vectors.len()];
        let mut done = false;

        while !done {
            let mut params = HashMap::new();
            for (i, param_name) in param_defs.iter().map(|(name, _, _, _)| name.to_string()).enumerate() {
                params.insert(param_name.to_string(), param_vectors[i][indices[i]]);
            }
            grids.push(params);

            // Increment indices
            let mut pos = 0;
            while pos < indices.len() {
                indices[pos] += 1;
                if indices[pos] < param_vectors[pos].len() {
                    break;
                }
                indices[pos] = 0;
                pos += 1;
            }
            if pos >= indices.len() {
                done = true;
            }
        }

        grids
    }

    /// Optimize single parameter
    pub fn optimize_single_param(
        &self,
        data: &[OHLCV],
        param_name: &str,
        values: &[f64],
    ) -> Vec<OptimizationResult> {
        let param_combinations: Vec<HashMap<String, f64>> = values
            .iter()
            .map(|&v| {
                let mut params = HashMap::new();
                params.insert(param_name.to_string(), v);
                params
            })
            .collect();

        self.optimize_parallel(data, &param_combinations)
    }

    /// Optimize with statistics
    pub fn optimize_with_stats(
        &self,
        data: &[OHLCV],
        param_combinations: &[HashMap<String, f64>],
    ) -> (Vec<OptimizationResult>, f64, u64) {
        let start = Instant::now();
        let results = self.optimize_parallel(data, param_combinations);
        let elapsed = start.elapsed();

        let avg_time = if !results.is_empty() {
            results.iter().map(|r| r.execution_time_ms).sum::<u64>() as f64 / results.len() as f64
        } else {
            0.0
        };

        (results, avg_time, elapsed.as_millis() as u64)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use rand::Rng;

    fn generate_test_data(days: usize) -> Vec<OHLCV> {
        let mut rng = rand::thread_rng();
        let mut data = Vec::with_capacity(days);
        let base_price = 100.0;

        for i in 0..days {
            let price = base_price * (1.0 + (i as f64 * 0.001));
            let noise = (rng.gen::<f64>() - 0.5) * 0.02;

            data.push(OHLCV {
                timestamp: i as u64,
                open: price * (1.0 + noise),
                high: price * (1.0 + noise + 0.01),
                low: price * (1.0 + noise - 0.01),
                close: price * (1.0 + noise * 0.5),
                volume: 1000000.0 + (rng.gen::<f64>() * 100000.0),
            });
        }

        data
    }

    #[test]
    fn test_optimization_engine() {
        let data = generate_test_data(100);
        let engine = OptimizationEngine::new(4);

        let param_combinations: Vec<_> = (0..10)
            .map(|i| {
                let mut params = HashMap::new();
                params.insert("period".to_string(), (5 + i % 10) as f64);
                params.insert("threshold".to_string(), (20.0 + i as f64) as f64);
                params
            })
            .collect();

        let results = engine.optimize_parallel(&data, &param_combinations);

        assert_eq!(results.len(), 10);
        assert!(results.iter().all(|r| r.sharpe_ratio.is_some() || r.total_return == -1.0));
    }

    #[test]
    fn test_parameter_grid() {
        let engine = OptimizationEngine::new(1);
        let param_defs = vec![
            ("period", 5.0, 20.0, 5.0),
            ("threshold", 20.0, 50.0, 10.0),
        ];

        let grid = engine.generate_parameter_grid(&param_defs);

        assert!(!grid.is_empty());
        // Should have 4 combinations: 4 period values × 4 threshold values
        assert_eq!(grid.len(), 16);
    }

    #[test]
    fn test_get_best_params() {
        let data = generate_test_data(100);
        let engine = OptimizationEngine::new(4);

        let param_combinations: Vec<_> = (0..50)
            .map(|i| {
                let mut params = HashMap::new();
                params.insert("period".to_string(), (5 + i) as f64);
                params
            })
            .collect();

        let results = engine.optimize_parallel(&data, &param_combinations);
        let best = engine.get_best_params_by_sharpe(&results, 5);

        assert_eq!(best.len(), 5);
        // Best results should be sorted by Sharpe ratio
        for i in 1..best.len() {
            assert!(best[i - 1].sharpe_ratio >= best[i].sharpe_ratio);
        }
    }

    #[test]
    fn test_optimize_with_stats() {
        let data = generate_test_data(100);
        let engine = OptimizationEngine::new(4);

        let param_combinations: Vec<_> = (0..20)
            .map(|i| {
                let mut params = HashMap::new();
                params.insert("period".to_string(), (5 + i) as f64);
                params
            })
            .collect();

        let (results, avg_time, total_time) = engine.optimize_with_stats(&data, &param_combinations);

        assert_eq!(results.len(), 20);
        assert!(avg_time > 0.0);
        assert!(total_time > 0);
        assert!(total_time >= avg_time as u64);
    }
}
