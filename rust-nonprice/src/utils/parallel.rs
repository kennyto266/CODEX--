//! Parallel processing utilities
//!
//! This module provides Rayon-based parallel processing utilities
//! for parameter optimization and other CPU-intensive tasks.

use rayon::prelude::*;
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

/// Progress tracker for parallel operations
#[derive(Debug, Clone)]
pub struct ProgressTracker {
    total: usize,
    completed: Arc<Mutex<usize>>,
    start_time: Instant,
}

impl ProgressTracker {
    /// Create a new progress tracker
    pub fn new(total: usize) -> Self {
        Self {
            total,
            completed: Arc::new(Mutex::new(0)),
            start_time: Instant::now(),
        }
    }

    /// Mark one item as completed
    pub fn increment(&self) {
        let mut completed = self.completed.lock().unwrap();
        *completed += 1;
    }

    /// Get current progress as percentage
    pub fn progress(&self) -> f64 {
        let completed = *self.completed.lock().unwrap();
        if self.total == 0 {
            0.0
        } else {
            (completed as f64 / self.total as f64) * 100.0
        }
    }

    /// Get elapsed time
    pub fn elapsed(&self) -> Duration {
        self.start_time.elapsed()
    }
}

/// Parallel optimizer
pub struct ParallelOptimizer {
    num_workers: usize,
}

impl ParallelOptimizer {
    /// Create a new parallel optimizer
    pub fn new(num_workers: usize) -> Self {
        Self { num_workers }
    }

    /// Set chunk size for parallel processing
    pub fn chunk_size(&mut self, _chunk_size: usize) {
        // Chunk size is managed automatically by Rayon
    }

    /// Optimize parameters in parallel
    pub fn optimize<T, R, F>(
        &self,
        items: &[T],
        mut processor: F,
    ) -> Vec<(usize, R)>
    where
        T: Send + Sync,
        R: Send,
        F: Fn(&T) -> R + Send + Sync,
    {
        items
            .par_iter()
            .enumerate()
            .map(|(idx, item)| (idx, processor(item)))
            .collect()
    }
}

/// Parallel parameter combination generator
#[derive(Debug, Clone)]
pub struct ParameterCombinations {
    pub zscore_buy_values: Vec<f64>,      // 4 values
    pub zscore_sell_values: Vec<f64>,     // 4 values
    pub rsi_buy_values: Vec<f64>,         // 3 values
    pub rsi_sell_values: Vec<f64>,        // 3 values
    pub sma_fast_values: Vec<usize>,      // 3 values
    pub sma_slow_values: Vec<usize>,      // 5 values
}

impl Default for ParameterCombinations {
    fn default() -> Self {
        Self {
            zscore_buy_values: vec![-2.0, -1.5, -1.0, -0.5],
            zscore_sell_values: vec![0.5, 1.0, 1.5, 2.0],
            rsi_buy_values: vec![20.0, 25.0, 30.0],
            rsi_sell_values: vec![65.0, 70.0, 75.0],
            sma_fast_values: vec![5, 10, 20],
            sma_slow_values: vec![20, 30, 50, 100, 200],
        }
    }
}

impl ParameterCombinations {
    /// Create a new parameter combination generator
    pub fn new() -> Self {
        Self::default()
    }

    /// Generate all parameter combinations
    pub fn generate(&self) -> Vec<ParameterCombo> {
        let mut combinations = Vec::new();

        for &zs_buy in &self.zscore_buy_values {
            for &zs_sell in &self.zscore_sell_values {
                for &rsi_buy in &self.rsi_buy_values {
                    for &rsi_sell in &self.rsi_sell_values {
                        for &sma_fast in &self.sma_fast_values {
                            for &sma_slow in &self.sma_slow_values {
                                combinations.push(ParameterCombo {
                                    zscore_buy: zs_buy,
                                    zscore_sell: zs_sell,
                                    rsi_buy: rsi_buy,
                                    rsi_sell: rsi_sell,
                                    sma_fast,
                                    sma_slow,
                                });
                            }
                        }
                    }
                }
            }
        }

        combinations
    }

    /// Get total number of combinations
    pub fn total_combinations(&self) -> usize {
        self.zscore_buy_values.len()
            * self.zscore_sell_values.len()
            * self.rsi_buy_values.len()
            * self.rsi_sell_values.len()
            * self.sma_fast_values.len()
            * self.sma_slow_values.len()
    }
}

/// Individual parameter combination
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct ParameterCombo {
    pub zscore_buy: f64,
    pub zscore_sell: f64,
    pub rsi_buy: f64,
    pub rsi_sell: f64,
    pub sma_fast: usize,
    pub sma_slow: usize,
}

impl ParameterCombo {
    /// Convert to ParameterSet
    pub fn to_parameter_set(&self, indicator_name: &str) -> crate::core::data::ParameterSet {
        crate::core::data::ParameterSet::new(
            indicator_name.to_string(),
            self.zscore_buy,
            self.zscore_sell,
            self.rsi_buy,
            self.rsi_sell,
            self.sma_fast,
            self.sma_slow,
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parameter_combinations() {
        let combos = ParameterCombinations::new();
        let generated = combos.generate();
        assert_eq!(generated.len(), combos.total_combinations());
    }

    #[test]
    fn test_parallel_optimizer() {
        let optimizer = ParallelOptimizer::new(4);
        let items = vec![1, 2, 3, 4, 5];
        let results = optimizer.optimize(&items, |x| x * 2);
        assert_eq!(results.len(), 5);
        assert_eq!(results[0].1, 2);
    }
}
