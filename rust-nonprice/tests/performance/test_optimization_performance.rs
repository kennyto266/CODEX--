//! Performance benchmarks for parameter optimization

use criterion::{criterion_group, criterion_main, Criterion};
use rust_nonprice::utils::parallel::*;

#[cfg(test)]
mod benchmarks {
    use super::*;

    fn bench_combination_generation(c: &mut Criterion) {
        c.bench_function("combination_generation", |b| {
            b.iter(|| {
                let combinations = ParameterCombinations::default();
                let _ = combinations.generate();
            })
        });
    }

    fn bench_parallel_processing(c: &mut Criterion) {
        let worker_counts = vec![1, 2, 4, 8, 16];
        let combinations = ParameterCombinations::default();
        let combo_list = combinations.generate();
        
        for &workers in &worker_counts {
            c.bench_with_input(
                &format!("parallel_optimize_{}", workers), 
                &workers, 
                |b, &workers| {
                b.iter(|| {
                    let optimizer = ParallelOptimizer::new(workers);
                    let _ = optimizer.optimize(&combo_list, |combo| {
                        let score = combo.zscore_buy.abs() + combo.zscore_sell;
                        (score, format!("{}-{}", combo.zscore_buy, combo.zscore_sell))
                    });
                })
            });
        }
    }
}

criterion_group!(
    benches,
    benchmarks::bench_combination_generation,
    benchmarks::bench_parallel_processing
);
criterion_main!(benches);

#[cfg(test)]
mod performance_tests {
    use super::*;

    #[test]
    fn test_sc002_optimization_time() {
        let combinations = ParameterCombinations::default();
        let combo_list = combinations.generate();
        let workers = 8;
        
        let start = std::time::Instant::now();
        let optimizer = ParallelOptimizer::new(workers);
        let results = optimizer.optimize(&combo_list, |combo| {
            let score = combo.zscore_buy.abs() + combo.zscore_sell;
            (score, format!("{}", combo.zscore_buy))
        });
        let elapsed = start.elapsed();
        
        assert!(elapsed.as_secs() < 30);
        assert_eq!(results.len(), 2160);
    }

    #[test]
    fn test_configurable_workers() {
        for workers in [1, 2, 4, 8, 16].iter() {
            let optimizer = ParallelOptimizer::new(*workers);
            assert!(optimizer.max_workers > 0);
        }
    }
}
