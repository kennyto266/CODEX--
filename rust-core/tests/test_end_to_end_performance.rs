//! T040: 端到端性能验证测试
//! 验证完整系统的端到端性能

use quant_core::backtest::engine::{BacktestEngine, BacktestConfig};
use quant_core::optimization::{OptimizationEngine, OptimizationResult};
use quant_core::types::OHLCV;
use std::time::Instant;
use std::sync::Arc;
use rayon::prelude::*;

/// 生成综合测试数据
fn generate_comprehensive_data(days: usize) -> Vec<OHLCV> {
    let mut data = Vec::with_capacity(days);
    let base_price = 100.0;

    for i in 0..days {
        let trend = (i as f64).sin() * 0.01;
        let price = base_price * (1.0 + trend);
        let noise = (rand::random::<f64>() - 0.5) * 0.03;

        data.push(OHLCV {
            timestamp: i as u64,
            open: price * (1.0 + noise),
            high: price * (1.0 + noise + 0.015),
            low: price * (1.0 + noise - 0.015),
            close: price * (1.0 + noise * 0.6),
            volume: 1000000.0 + (rand::random::<f64>() * 200000.0),
        });
    }

    data
}

/// 完整的回测 + 优化工作流
fn full_backtest_optimization_workflow(data: &Vec<OHLCV>) -> OptimizationResult {
    let config = BacktestConfig {
        initial_capital: 100000.0,
        commission: 0.001,
        slippage: 0.0005,
    };

    // 第一步：运行基准回测
    let engine = BacktestEngine::new(config);
    let _baseline = engine.run(data, &vec![]).unwrap();

    // 第二步：参数优化
    let param_combinations: Vec<_> = (0..100)
        .map(|i| {
            std::collections::HashMap::from([
                ("period".to_string(), (5 + i % 30) as f64),
                ("threshold".to_string(), (20.0 + (i as f64 * 1.0)) as f64),
            ])
        })
        .collect();

    let opt_engine = OptimizationEngine::new(8);
    let results = opt_engine.optimize_parallel(data, &param_combinations);

    // 返回最佳结果
    results
        .into_iter()
        .max_by(|a, b| {
            a.sharpe_ratio
                .unwrap_or(0.0)
                .partial_cmp(&b.sharpe_ratio.unwrap_or(0.0))
                .unwrap_or(std::cmp::Ordering::Equal)
        })
        .unwrap()
}

/// 测试小型端到端流程（100天数据）
#[test]
fn test_e2e_small_workflow() {
    let data = generate_comprehensive_data(100);
    let start = Instant::now();

    let result = full_backtest_optimization_workflow(&data);

    let elapsed = start.elapsed();

    println!("小型端到端流程 (100天): {:?}", elapsed);
    println!("最佳Sharpe比率: {:?}", result.sharpe_ratio);
    println!("总收益率: {:.2}%", result.total_return * 100.0);

    assert!(
        elapsed.as_millis() < 500,
        "小型端到端流程耗时 {}ms 超过500ms",
        elapsed.as_millis()
    );

    assert!(result.sharpe_ratio.is_some());
}

/// 测试中型端到端流程（1000天数据）
#[test]
fn test_e2e_medium_workflow() {
    let data = generate_comprehensive_data(1000);
    let start = Instant::now();

    let result = full_backtest_optimization_workflow(&data);

    let elapsed = start.elapsed();

    println!("中型端到端流程 (1000天): {:?}", elapsed);
    println!("最佳Sharpe比率: {:?}", result.sharpe_ratio);
    println!("总收益率: {:.2}%", result.total_return * 100.0);

    assert!(
        elapsed.as_secs() < 5,
        "中型端到端流程耗时 {}s 超过5s",
        elapsed.as_secs()
    );

    assert!(result.sharpe_ratio.is_some());
}

/// 测试大型端到端流程（2520天数据）
#[test]
fn test_e2e_large_workflow() {
    let data = generate_comprehensive_data(2520);
    let start = Instant::now();

    let result = full_backtest_optimization_workflow(&data);

    let elapsed = start.elapsed();

    println!("大型端到端流程 (2520天): {:?}", elapsed);
    println!("最佳Sharpe比率: {:?}", result.sharpe_ratio);
    println!("总收益率: {:.2}%", result.total_return * 100.0);
    println!("最大回撤: {:.2}%", result.max_drawdown * 100.0);
    println!("胜率: {:.2}%", result.win_rate * 100.0);
    println!("交易次数: {}", result.trades);

    assert!(
        elapsed.as_secs() < 30,
        "大型端到端流程耗时 {}s 超过30s",
        elapsed.as_secs()
    );

    assert!(result.sharpe_ratio.is_some());
    assert!(result.total_return > -1.0);
    assert!(result.max_drawdown >= 0.0 && result.max_drawdown <= 1.0);
}

/// 测试端到端并行工作流
#[test]
fn test_e2e_parallel_workflow() {
    let data = Arc::new(generate_comprehensive_data(1000));
    let start = Instant::now();

    let results: Vec<_> = (0..16)
        .into_par_iter()
        .map(|i| {
            // 为每个工作流添加轻微变化
            let data_clone = data.clone();
            let result = full_backtest_optimization_workflow(&data_clone);
            (i, result)
        })
        .collect();

    let elapsed = start.elapsed();

    println!("16个并行端到端工作流: {:?}", elapsed);
    println!("平均每个工作流: {}ms", elapsed.as_millis() as f64 / 16.0);
    println!("总吞吐量: {:.2} 工作流/秒", 16.0 / elapsed.as_secs_f64());

    assert_eq!(results.len(), 16);
    assert!(results.iter().all(|(_, r)| r.sharpe_ratio.is_some()));

    let avg_time = elapsed.as_millis() as f64 / 16.0;
    assert!(
        avg_time < 5000,
        "并行工作流平均耗时 {}ms 超过5s",
        avg_time
    );
}

/// 测试实时信号处理性能
#[test]
fn test_realtime_signal_processing() {
    let data = generate_comprehensive_data(1000);
    let config = BacktestConfig {
        initial_capital: 100000.0,
        commission: 0.001,
        slippage: 0.0005,
    };

    let engine = BacktestEngine::new(config);

    // 模拟实时信号处理
    let signal_count = 100;
    let start = Instant::now();

    for i in 0..signal_count {
        let signal = quant_core::backtest::engine::Signal::new(
            i as u64 * 10,
            if i % 2 == 0 { "BUY" } else { "SELL" },
            0.5,
        );

        let signals = vec![signal];
        let _result = engine.run(&data, &signals);
    }

    let elapsed = start.elapsed();

    println!("{}个实时信号处理耗时: {:?}", signal_count, elapsed);
    println!("平均每个信号: {}ms", elapsed.as_millis() as f64 / signal_count as f64);

    assert!(
        elapsed.as_millis() < 1000,
        "实时信号处理耗时 {}ms 超过1000ms",
        elapsed.as_millis()
    );

    let avg_time = elapsed.as_millis() as f64 / signal_count as f64;
    assert!(
        avg_time < 10,
        "平均信号处理时间 {}ms 超过10ms",
        avg_time
    );
}

/// 测试完整的回测生命周期
#[test]
fn test_full_backtest_lifecycle() {
    let data = generate_comprehensive_data(1260);
    let start = Instant::now();

    // 1. 初始化
    let config = BacktestConfig {
        initial_capital: 100000.0,
        commission: 0.001,
        slippage: 0.0005,
    };
    let engine = BacktestEngine::new(config);

    // 2. 数据验证
    assert!(!data.is_empty());
    assert_eq!(data.len(), 1260);

    // 3. 运行初始回测
    let initial_signals = vec![];
    let initial_result = engine.run(&data, &initial_signals).unwrap();
    println!("初始回测总价值: {:.2}", initial_result.final_value);

    // 4. 参数优化
    let param_combinations: Vec<_> = (0..200)
        .map(|i| {
            std::collections::HashMap::from([
                ("period".to_string(), (5 + i % 50) as f64),
                ("threshold".to_string(), (20.0 + (i as f64 * 1.0)) as f64),
            ])
        })
        .collect();

    let opt_engine = OptimizationEngine::new(8);
    let optimization_results = opt_engine.optimize_parallel(&data, &param_combinations);
    assert_eq!(optimization_results.len(), 200);

    // 5. 选择最佳参数
    let best_result = optimization_results
        .into_iter()
        .max_by(|a, b| {
            a.sharpe_ratio
                .unwrap_or(0.0)
                .partial_cmp(&b.sharpe_ratio.unwrap_or(0.0))
                .unwrap_or(std::cmp::Ordering::Equal)
        })
        .unwrap();

    // 6. 使用最佳参数运行最终回测
    let final_signals = vec![
        quant_core::backtest::engine::Signal::new(0, "BUY", 0.5),
        quant_core::backtest::engine::Signal::new(252, "SELL", 0.5),
    ];
    let final_result = engine.run(&data, &final_signals).unwrap();

    let elapsed = start.elapsed();

    println!("完整生命周期耗时: {:?}", elapsed);
    println!("最终回测总价值: {:.2}", final_result.final_value);
    println!("最佳Sharpe比率: {:?}", best_result.sharpe_ratio);
    println!("总收益率: {:.2}%", best_result.total_return * 100.0);

    // 验证完整生命周期在合理时间内完成
    assert!(
        elapsed.as_secs() < 60,
        "完整生命周期耗时 {}s 超过60s",
        elapsed.as_secs()
    );

    assert!(best_result.sharpe_ratio.is_some());
    assert!(initial_result.final_value > 0.0);
    assert!(final_result.final_value > 0.0);
}

/// 测试多阶段性能优化
#[test]
fn test_multistage_performance_optimization() {
    let data = generate_comprehensive_data(1000);

    // 第一阶段：粗粒度优化
    let coarse_params: Vec<_> = (0..50)
        .map(|i| {
            std::collections::HashMap::from([
                ("period".to_string(), (5 + i * 5) as f64),
                ("threshold".to_string(), (20.0 + i * 5.0) as f64),
            ])
        })
        .collect();

    let opt_engine = OptimizationEngine::new(8);
    let stage1_start = Instant::now();
    let coarse_results = opt_engine.optimize_parallel(&data, &coarse_params);
    let stage1_time = stage1_start.elapsed();

    println!("第一阶段优化 (50组合): {:?}", stage1_time);

    // 第二阶段：基于第一阶段结果进行细粒度优化
    let best_coarse = coarse_results
        .into_iter()
        .max_by(|a, b| {
            a.sharpe_ratio
                .unwrap_or(0.0)
                .partial_cmp(&b.sharpe_ratio.unwrap_or(0.0))
                .unwrap_or(std::cmp::Ordering::Equal)
        })
        .unwrap();

    let base_period = best_coarse.parameters.get("period").unwrap_or(&20.0);
    let base_threshold = best_coarse.parameters.get("threshold").unwrap_or(&30.0);

    let fine_params: Vec<_> = (0..50)
        .map(|i| {
            std::collections::HashMap::from([
                ("period".to_string(), base_period + (i as f64 - 25.0)),
                ("threshold".to_string(), base_threshold + (i as f64 - 25.0)),
            ])
        })
        .collect();

    let stage2_start = Instant::now();
    let fine_results = opt_engine.optimize_parallel(&data, &fine_params);
    let stage2_time = stage2_start.elapsed();

    println!("第二阶段优化 (50组合): {:?}", stage2_time);

    let total_time = stage1_time + stage2_time;

    println!("多阶段优化总耗时: {:?}", total_time);
    println!("总组合数: 100");

    assert!(
        total_time.as_secs() < 10,
        "多阶段优化耗时 {}s 超过10s",
        total_time.as_secs()
    );

    assert_eq!(fine_results.len(), 50);
    assert!(fine_results.iter().all(|r| r.sharpe_ratio.is_some()));
}

/// 测试系统稳定性在高负载下
#[test]
fn test_system_stability_under_load() {
    let data = generate_comprehensive_data(1000);
    let config = BacktestConfig {
        initial_capital: 100000.0,
        commission: 0.001,
        slippage: 0.0005,
    };

    // 连续运行32个回测
    let start = Instant::now();
    let mut success_count = 0;
    let mut error_count = 0;

    for iteration in 0..32 {
        let engine = BacktestEngine::new(config.clone());
        let signals = vec![
            quant_core::backtest::engine::Signal::new(0, "BUY", 0.5),
            quant_core::backtest::engine::Signal::new(100, "SELL", 0.5),
        ];

        match engine.run(&data, &signals) {
            Ok(_) => {
                success_count += 1;
                if iteration % 10 == 0 {
                    println!("第{}次回测成功", iteration + 1);
                }
            }
            Err(e) => {
                error_count += 1;
                println!("第{}次回测失败: {:?}", iteration + 1, e);
            }
        }
    }

    let elapsed = start.elapsed();

    println!("高负载测试结果:");
    println!("  成功: {}/32", success_count);
    println!("  失败: {}/32", error_count);
    println!("  总耗时: {:?}", elapsed);
    println!("  平均每次: {}ms", elapsed.as_millis() as f64 / 32.0);

    // 所有32个回测都应该成功
    assert_eq!(error_count, 0, "有 {} 个回测失败", error_count);
    assert_eq!(success_count, 32);

    assert!(
        elapsed.as_secs() < 30,
        "高负载测试耗时 {}s 超过30s",
        elapsed.as_secs()
    );
}
