//! Simple benchmark

use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use rust_core::backtest::{BacktestEngine, BacktestConfig, StrategyType};
use rust_core::DataPoint;
use chrono::Utc;

fn create_test_data(n: usize) -> Vec<DataPoint> {
    let start = Utc::now() - chrono::Duration::days(n as i64);
    (0..n)
        .map(|i| {
            let price = 100.0 + (i as f64 * 0.1) + (i as f64 * 0.05).sin();
            DataPoint {
                timestamp: start + chrono::Duration::days(i as i64),
                open: price * 0.999,
                high: price * 1.005,
                low: price * 0.995,
                close: price,
                volume: 1000 + (i % 100) as u64 * 10,
            }
        })
        .collect()
}

fn bench_ma_strategy(c: &mut Criterion) {
    let config = BacktestConfig {
        initial_capital: 100000.0,
        commission: 0.001,
        slippage: 0.0005,
        position_size: 1.0,
        risk_free_rate: 0.02,
    };
    let engine = BacktestEngine::new(config);
    let data = create_test_data(1000);
    let strategy = StrategyType::MovingAverageCross {
        fast_period: 10,
        slow_period: 20,
    };

    c.bench_function("ma_strategy_1000", |b| {
        b.iter(|| {
            let result = engine.run(
                black_box(&data),
                black_box(&strategy),
            );
            black_box(result);
        })
    });
}

criterion_group!(benches, bench_ma_strategy);
criterion_main!(benches);
