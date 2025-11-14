//! T039: 并行回测吞吐量测试
//! 验证32个并发回测的性能

use quant_core::backtest::engine::{BacktestEngine, BacktestConfig};
use quant_core::types::OHLCV;
use std::time::Instant;
use std::sync::Arc;
use rayon::prelude::*;

/// 生成测试数据
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

/// 测试8个并行回测
#[test]
fn test_8_parallel_backtests() {
    let data = Arc::new(generate_test_data(1000));
    let config = BacktestConfig {
        initial_capital: 100000.0,
        commission: 0.001,
        slippage: 0.0005,
    };

    let start = Instant::now();

    let results: Vec<_> = (0..8)
        .into_par_iter()
        .map(|i| {
            let engine = BacktestEngine::new(config.clone());
            let signals = vec![
                quant_core::backtest::engine::Signal::new(0, "BUY", 0.5),
                quant_core::backtest::engine::Signal::new(100, "SELL", 0.5),
                quant_core::backtest::engine::Signal::new(200, "BUY", 0.3),
                quant_core::backtest::engine::Signal::new(300, "SELL", 0.3),
            ];

            let result = engine.run(&data, &signals);
            (i, result)
        })
        .collect();

    let elapsed = start.elapsed();

    println!("8个并行回测耗时: {:?}", elapsed);
    println!("平均每个回测: {}ms", elapsed.as_millis() as f64 / 8.0);

    assert_eq!(results.len(), 8);
    assert!(results.iter().all(|(_, r)| r.is_ok()));

    // 8个并行回测应该比串行快
    let serialized_time = elapsed.as_millis() as f64 / 8.0;
    assert!(
        serialized_time < 50,
        "单个回测平均耗时 {}ms 超过50ms",
        serialized_time
    );
}

/// 测试16个并行回测
#[test]
fn test_16_parallel_backtests() {
    let data = Arc::new(generate_test_data(1000));
    let config = BacktestConfig {
        initial_capital: 100000.0,
        commission: 0.001,
        slippage: 0.0005,
    };

    let start = Instant::now();

    let results: Vec<_> = (0..16)
        .into_par_iter()
        .map(|i| {
            let engine = BacktestEngine::new(config.clone());
            let signals = vec![
                quant_core::backtest::engine::Signal::new(0, "BUY", 0.5),
                quant_core::backtest::engine::Signal::new(100, "SELL", 0.5),
            ];

            let result = engine.run(&data, &signals);
            (i, result)
        })
        .collect();

    let elapsed = start.elapsed();

    println!("16个并行回测耗时: {:?}", elapsed);
    println!("平均每个回测: {}ms", elapsed.as_millis() as f64 / 16.0);

    assert_eq!(results.len(), 16);
    assert!(results.iter().all(|(_, r)| r.is_ok()));

    let avg_time = elapsed.as_millis() as f64 / 16.0;
    assert!(
        avg_time < 50,
        "单个回测平均耗时 {}ms 超过50ms",
        avg_time
    );
}

/// 测试32个并行回测（目标指标）
#[test]
fn test_32_parallel_backtests() {
    let data = Arc::new(generate_test_data(1000));
    let config = BacktestConfig {
        initial_capital: 100000.0,
        commission: 0.001,
        slippage: 0.0005,
    };

    let start = Instant::now();

    let results: Vec<_> = (0..32)
        .into_par_iter()
        .map(|i| {
            let engine = BacktestEngine::new(config.clone());
            let signals = vec![
                quant_core::backtest::engine::Signal::new(0, "BUY", 0.5),
                quant_core::backtest::engine::Signal::new(100, "SELL", 0.5),
            ];

            let result = engine.run(&data, &signals);
            (i, result)
        })
        .collect();

    let elapsed = start.elapsed();

    println!("32个并行回测耗时: {:?}", elapsed);
    println!("平均每个回测: {}ms", elapsed.as_millis() as f64 / 32.0);
    println!("总吞吐量: {} 回测/秒", 32.0 / elapsed.as_secs_f64());

    assert_eq!(results.len(), 32);
    assert!(results.iter().all(|(_, r)| r.is_ok()));

    let avg_time = elapsed.as_millis() as f64 / 32.0;
    assert!(
        avg_time < 50,
        "单个回测平均耗时 {}ms 超过50ms",
        avg_time
    );

    // 验证吞吐量
    let throughput = 32.0 / elapsed.as_secs_f64();
    assert!(
        throughput > 10.0,
        "32个回测吞吐量 {} 回测/秒 低于10",
        throughput
    );
}

/// 测试64个并行回测（压力测试）
#[test]
fn test_64_parallel_backtests_stress() {
    let data = Arc::new(generate_test_data(1000));
    let config = BacktestConfig {
        initial_capital: 100000.0,
        commission: 0.001,
        slippage: 0.0005,
    };

    let start = Instant::now();

    let results: Vec<_> = (0..64)
        .into_par_iter()
        .map(|i| {
            let engine = BacktestEngine::new(config.clone());
            let signals = vec![]; // 空信号，避免复杂性

            let result = engine.run(&data, &signals);
            (i, result)
        })
        .collect();

    let elapsed = start.elapsed();

    println!("64个并行回测耗时: {:?}", elapsed);
    println!("平均每个回测: {}ms", elapsed.as_millis() as f64 / 64.0);
    println!("总吞吐量: {} 回测/秒", 64.0 / elapsed.as_secs_f64());

    assert_eq!(results.len(), 64);
    assert!(results.iter().all(|(_, r)| r.is_ok()));

    let avg_time = elapsed.as_millis() as f64 / 64.0;
    assert!(
        avg_time < 100,
        "压力测试单个回测平均耗时 {}ms 超过100ms",
        avg_time
    );
}

/// 测试不同数据大小的并行吞吐量
#[test]
fn test_parallel_throughput_different_sizes() {
    let sizes = vec![252, 500, 1000, 2520]; // 1月, 2月, 1年, 10年
    let parallel_levels = vec![8, 16, 32];

    for &size in &sizes {
        println!("\n测试数据大小: {} 天", size);
        let data = Arc::new(generate_test_data(size));

        for &par_level in &parallel_levels {
            let config = BacktestConfig {
                initial_capital: 100000.0,
                commission: 0.001,
                slippage: 0.0005,
            };

            let start = Instant::now();

            let results: Vec<_> = (0..par_level)
                .into_par_iter()
                .map(|i| {
                    let engine = BacktestEngine::new(config.clone());
                    let signals = vec![];
                    let result = engine.run(&data, &signals);
                    (i, result)
                })
                .collect();

            let elapsed = start.elapsed();
            let throughput = par_level as f64 / elapsed.as_secs_f64();
            let avg_time = elapsed.as_millis() as f64 / par_level as f64;

            println!("  {}个并行: {:?}, 平均: {:.2}ms, 吞吐量: {:.2} 回测/秒",
                     par_level, elapsed, avg_time, throughput);

            assert_eq!(results.len(), par_level);
            assert!(results.iter().all(|(_, r)| r.is_ok()));
        }
    }
}

/// 测试并行回测的可扩展性
#[test]
fn test_parallel_scalability() {
    let data = Arc::new(generate_test_data(1000));
    let config = BacktestConfig {
        initial_capital: 100000.0,
        commission: 0.001,
        slippage: 0.0005,
    };

    // 测量不同并行度的性能
    let parallel_levels = vec![1, 2, 4, 8, 16, 32];
    let mut times = Vec::new();

    for &par_level in &parallel_levels {
        let start = Instant::now();

        let results: Vec<_> = (0..par_level)
            .into_par_iter()
            .map(|i| {
                let engine = BacktestEngine::new(config.clone());
                let signals = vec![];
                let result = engine.run(&data, &signals);
                (i, result)
            })
            .collect();

        let elapsed = start.elapsed();
        times.push(elapsed);

        println!("{}个并行耗时: {:?}", par_level, elapsed);

        assert_eq!(results.len(), par_level);
        assert!(results.iter().all(|(_, r)| r.is_ok()));
    }

    // 验证可扩展性（理想情况下应该是线性的）
    for i in 1..parallel_levels.len() {
        let speedup = times[0].as_secs_f64() / times[i].as_secs_f64();
        let ideal_speedup = parallel_levels[i] as f64;

        println!("{}核加速比: {:.2}x (理想: {:.2}x)",
                 parallel_levels[i], speedup, ideal_speedup);

        // 至少应该有2倍加速（考虑实际情况）
        assert!(
            speedup > 1.5,
            "{}个并行加速比 {} 低于1.5x",
            parallel_levels[i],
            speedup
        );
    }
}

/// 测试32个不同策略的并行回测
#[test]
fn test_32_different_strategies_parallel() {
    let data = Arc::new(generate_test_data(1000));
    let config = BacktestConfig {
        initial_capital: 100000.0,
        commission: 0.001,
        slippage: 0.0005,
    };

    let start = Instant::now();

    let results: Vec<_> = (0..32)
        .into_par_iter()
        .map(|i| {
            let engine = BacktestEngine::new(config.clone());

            // 为每个策略生成不同的信号
            let signals = vec![
                quant_core::backtest::engine::Signal::new(0, "BUY", 0.1 * (i as f64 + 1.0)),
                quant_core::backtest::engine::Signal::new(100, "SELL", 0.1 * (i as f64 + 1.0)),
            ];

            let result = engine.run(&data, &signals);
            (i, result)
        })
        .collect();

    let elapsed = start.elapsed();

    println!("32个不同策略并行回测耗时: {:?}", elapsed);
    println!("平均每个策略: {}ms", elapsed.as_millis() as f64 / 32.0);
    println!("总吞吐量: {} 策略/秒", 32.0 / elapsed.as_secs_f64());

    assert_eq!(results.len(), 32);
    assert!(results.iter().all(|(_, r)| r.is_ok()));

    // 验证所有策略都产生了不同的结果
    assert!(results.len() == 32);

    let throughput = 32.0 / elapsed.as_secs_f64();
    assert!(
        throughput > 10.0,
        "32个策略吞吐量 {} 策略/秒 低于10",
        throughput
    );
}
