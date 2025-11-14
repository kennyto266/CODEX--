//! T036: 单次回测基准测试
//! 测试单次回测的性能是否满足 < 50ms (Rust) 或 < 100ms (Python) 的要求

use quant_core::backtest::engine::{BacktestEngine, BacktestConfig, Signal};
use quant_core::types::OHLCV;
use std::time::Instant;
use criterion::{black_box, criterion_group, criterion_main, Criterion};

/// 生成模拟的OHLCV数据用于测试
fn generate_test_data(days: usize) -> Vec<OHLCV> {
    let mut data = Vec::with_capacity(days);
    let base_price = 100.0;
    let volatility = 0.02;

    for i in 0..days {
        let price = base_price * (1.0 + (i as f64 * 0.001));
        let noise = (rand::random::<f64>() - 0.5) * volatility;

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

/// 测试单次回测性能
fn test_single_backtest_performance() {
    let data = generate_test_data(1000);
    let config = BacktestConfig {
        initial_capital: 100000.0,
        commission: 0.001,
        slippage: 0.0005,
    };

    let engine = BacktestEngine::new(config);
    let start = Instant::now();

    // 运行回测
    let result = engine.run(&data, &vec![
        Signal::new(0, "BUY", 0.5),
        Signal::new(100, "SELL", 0.5),
    ]);

    let elapsed = start.elapsed();

    println!("单次回测耗时: {:?}", elapsed);

    // 性能断言：Rust版本应该 < 50ms
    assert!(
        elapsed.as_millis() < 50,
        "单次回测耗时 {}ms 超过50ms阈值",
        elapsed.as_millis()
    );

    // 验证结果
    assert!(result.is_ok(), "回测执行失败: {:?}", result.err());
}

/// Criterion基准测试
fn bench_single_backtest(c: &mut Criterion) {
    let data = generate_test_data(1000);
    let config = BacktestConfig {
        initial_capital: 100000.0,
        commission: 0.001,
        slippage: 0.0005,
    };

    let engine = BacktestEngine::new(config);

    c.bench_function("single_backtest_1000_days", |b| {
        b.iter(|| {
            engine.run(
                black_box(&data),
                black_box(&vec![
                    Signal::new(0, "BUY", 0.5),
                    Signal::new(100, "SELL", 0.5),
                    Signal::new(200, "BUY", 0.3),
                    Signal::new(300, "SELL", 0.3),
                ])
            )
        })
    });
}

criterion_group!(benches, bench_single_backtest);
criterion_main!(benches);

#[test]
fn test_single_backtest_100_days() {
    let data = generate_test_data(100);
    let config = BacktestConfig {
        initial_capital: 100000.0,
        commission: 0.001,
        slippage: 0.0005,
    };

    let engine = BacktestEngine::new(config);
    let start = Instant::now();

    let result = engine.run(&data, &vec![]);
    let elapsed = start.elapsed();

    println!("100天回测耗时: {:?}", elapsed);

    assert!(
        elapsed.as_millis() < 10,
        "100天回测耗时 {}ms 超过10ms阈值",
        elapsed.as_millis()
    );

    assert!(result.is_ok());
}

#[test]
fn test_single_backtest_1000_days() {
    let data = generate_test_data(1000);
    let config = BacktestConfig {
        initial_capital: 100000.0,
        commission: 0.001,
        slippage: 0.0005,
    };

    let engine = BacktestEngine::new(config);
    let start = Instant::now();

    let result = engine.run(&data, &vec![]);
    let elapsed = start.elapsed();

    println!("1000天回测耗时: {:?}", elapsed);

    assert!(
        elapsed.as_millis() < 50,
        "1000天回测耗时 {}ms 超过50ms阈值",
        elapsed.as_millis()
    );

    assert!(result.is_ok());
}

#[test]
fn test_single_backtest_5000_days() {
    let data = generate_test_data(5000);
    let config = BacktestConfig {
        initial_capital: 100000.0,
        commission: 0.001,
        slippage: 0.0005,
    };

    let engine = BacktestEngine::new(config);
    let start = Instant::now();

    let result = engine.run(&data, &vec![]);
    let elapsed = start.elapsed();

    println!("5000天回测耗时: {:?}", elapsed);

    assert!(
        elapsed.as_millis() < 250,
        "5000天回测耗时 {}ms 超过250ms阈值",
        elapsed.as_millis()
    );

    assert!(result.is_ok());
}
