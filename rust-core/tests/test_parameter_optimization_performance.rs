//! T037: 参数优化基准测试
//! 测试参数优化是否满足 < 10s (1000组合, 8核) 的要求

use quant_core::optimization::{OptimizationEngine, ParameterGrid, OptimizationResult};
use quant_core::backtest::engine::BacktestEngine;
use quant_core::types::OHLCV;
use std::time::Instant;
use rayon::prelude::*;

/// 生成模拟数据
fn generate_test_data(days: usize) -> Vec<OHLCV> {
    let mut data = Vec::with_capacity(days);
    let base_price = 100.0;

    for i in 0..days {
        let price = base_price * (1.0 + (i as f64 * 0.001));
        let noise = (rand::random::<f64>() - 0.5) * 0.02;

        data.push(OHLCV {
            timestamp: i as u64,
            open: price * (1.0 + noise),
            high: price * (1.0 + noise + 0.01),
            low: price * (1.0 + noise - 0.01),
            close: price * (1.0 + noise * 0.5),
            volume: 1000000.0 + (rand::random::<f64>() * 100000.0),
        });
    }

    data
}

/// 测试100个参数组合的优化性能
#[test]
fn test_optimization_100_combinations() {
    let data = generate_test_data(1000);

    // 创建100个参数组合
    let param_combinations: Vec<_> = (0..100)
        .map(|i| {
            std::collections::HashMap::from([
                ("period".to_string(), (5 + i % 50) as f64),
                ("threshold".to_string(), (20.0 + (i as f64 * 0.5)) as f64),
            ])
        })
        .collect();

    let engine = OptimizationEngine::new(8); // 8个并行worker
    let start = Instant::now();

    let results = engine.optimize_parallel(&data, &param_combinations);

    let elapsed = start.elapsed();

    println!("100个组合优化耗时: {:?}", elapsed);
    println!("平均每个组合: {}ms", elapsed.as_millis() as f64 / 100.0);

    // 100个组合应该在5秒内完成
    assert!(
        elapsed.as_secs() < 5,
        "100个组合优化耗时 {}s 超过5秒阈值",
        elapsed.as_secs()
    );

    assert_eq!(results.len(), 100);
    assert!(results.iter().all(|r| r.sharpe_ratio.is_some()));
}

/// 测试500个参数组合的优化性能
#[test]
fn test_optimization_500_combinations() {
    let data = generate_test_data(1000);

    let param_combinations: Vec<_> = (0..500)
        .map(|i| {
            std::collections::HashMap::from([
                ("period".to_string(), (5 + i % 50) as f64),
                ("threshold".to_string(), (20.0 + (i as f64 * 0.5)) as f64),
                ("multiplier".to_string(), (1.0 + (i as f64 * 0.02)) as f64),
            ])
        })
        .collect();

    let engine = OptimizationEngine::new(8);
    let start = Instant::now();

    let results = engine.optimize_parallel(&data, &param_combinations);

    let elapsed = start.elapsed();

    println!("500个组合优化耗时: {:?}", elapsed);
    println!("平均每个组合: {}ms", elapsed.as_millis() as f64 / 500.0);

    // 500个组合应该在10秒内完成
    assert!(
        elapsed.as_secs() < 10,
        "500个组合优化耗时 {}s 超过10秒阈值",
        elapsed.as_secs()
    );

    assert_eq!(results.len(), 500);
}

/// 测试1000个参数组合的优化性能
#[test]
fn test_optimization_1000_combinations() {
    let data = generate_test_data(1000);

    let param_combinations: Vec<_> = (0..1000)
        .map(|i| {
            std::collections::HashMap::from([
                ("period".to_string(), (5 + i % 50) as f64),
                ("threshold".to_string(), (20.0 + (i as f64 * 0.5)) as f64),
                ("multiplier".to_string(), (1.0 + (i as f64 * 0.02)) as f64),
            ])
        })
        .collect();

    let engine = OptimizationEngine::new(8);
    let start = Instant::now();

    let results = engine.optimize_parallel(&data, &param_combinations);

    let elapsed = start.elapsed();

    println!("1000个组合优化耗时: {:?}", elapsed);
    println!("平均每个组合: {}ms", elapsed.as_millis() as f64 / 1000.0);
    println!("每秒处理组合数: {}", 1000.0 / elapsed.as_secs_f64());

    // 1000个组合应该在10秒内完成
    assert!(
        elapsed.as_secs() < 10,
        "1000个组合优化耗时 {}s 超过10秒阈值",
        elapsed.as_secs()
    );

    assert_eq!(results.len(), 1000);

    // 验证最佳结果
    let best_result = results
        .iter()
        .max_by(|a, b| {
            a.sharpe_ratio
                .unwrap_or(0.0)
                .partial_cmp(&b.sharpe_ratio.unwrap_or(0.0))
                .unwrap_or(std::cmp::Ordering::Equal)
        })
        .unwrap();

    println!("最佳Sharpe比率: {:?}", best_result.sharpe_ratio);
    println!("最佳参数: {:?}", best_result.parameters);
}

/// 测试不同并行度的性能
#[test]
fn test_optimization_parallelism_scaling() {
    let data = generate_test_data(500);

    let param_combinations: Vec<_> = (0..500)
        .map(|i| {
            std::collections::HashMap::from([
                ("period".to_string(), (5 + i % 50) as f64),
                ("threshold".to_string(), (20.0 + (i as f64 * 0.5)) as f64),
            ])
        })
        .collect();

    // 测试1个worker
    let engine_1 = OptimizationEngine::new(1);
    let start_1 = Instant::now();
    let results_1 = engine_1.optimize_parallel(&data, &param_combinations);
    let elapsed_1 = start_1.elapsed();

    // 测试8个worker
    let engine_8 = OptimizationEngine::new(8);
    let start_8 = Instant::now();
    let results_8 = engine_8.optimize_parallel(&data, &param_combinations);
    let elapsed_8 = start_8.elapsed();

    // 测试16个worker
    let engine_16 = OptimizationEngine::new(16);
    let start_16 = Instant::now();
    let results_16 = engine_16.optimize_parallel(&data, &param_combinations);
    let elapsed_16 = start_16.elapsed();

    println!("1个worker: {:?}", elapsed_1);
    println!("8个worker: {:?}", elapsed_8);
    println!("16个worker: {:?}", elapsed_16);

    // 验证加速比（理想情况下8个worker应该比1个快约8倍）
    let speedup_8 = elapsed_1.as_secs_f64() / elapsed_8.as_secs_f64();
    let speedup_16 = elapsed_1.as_secs_f64() / elapsed_16.as_secs_f64();

    println!("8核加速比: {:.2}x", speedup_8);
    println!("16核加速比: {:.2}x", speedup_16);

    // 至少应该有2倍加速
    assert!(
        speedup_8 > 2.0,
        "8核加速比 {} 低于2x",
        speedup_8
    );

    // 所有结果应该一致
    assert_eq!(results_1.len(), 500);
    assert_eq!(results_8.len(), 500);
    assert_eq!(results_16.len(), 500);
}

/// 测试优化器内存使用
#[test]
fn test_optimization_memory_usage() {
    use std::mem::size_of;

    // 计算单个结果的大小
    let single_result = OptimizationResult {
        parameters: std::collections::HashMap::from([
            ("period".to_string(), 20.0),
            ("threshold".to_string(), 30.0),
        ]),
        total_return: 0.15,
        sharpe_ratio: Some(1.2),
        max_drawdown: 0.08,
        win_rate: 0.65,
        trades: 45,
    };

    let result_size = size_of::<OptimizationResult>();
    println!("单个结果大小: {} bytes", result_size);

    // 10000个结果的内存使用（10MB应该是可接受的）
    let total_results = 10000;
    let total_memory = total_results * result_size;
    let total_memory_mb = total_memory as f64 / (1024.0 * 1024.0);

    println!("10000个结果预计内存使用: {:.2} MB", total_memory_mb);

    assert!(
        total_memory_mb < 100.0,
        "10000个结果内存使用 {} MB 超过100MB阈值",
        total_memory_mb
    );
}
