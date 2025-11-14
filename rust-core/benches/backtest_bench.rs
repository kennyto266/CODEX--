//! T045: 基准测试
//! 使用Criterion进行性能基准测试

use quant_core::backtest::engine::BacktestEngine;
use quant_core::backtest::BacktestConfig;
use quant_core::backtest::optimization::OptimizationEngine;
use quant_core::types::OHLCV;
use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use std::collections::HashMap;

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

/// 单次回测基准测试
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
                    quant_core::types::Signal {
                        timestamp: 0,
                        signal_type: quant_core::types::SignalType::Buy,
                        price: 0.0,
                        strength: 1.0,
                    },
                    quant_core::types::Signal {
                        timestamp: 100,
                        signal_type: quant_core::types::SignalType::Sell,
                        price: 0.0,
                        strength: 1.0,
                    },
                ])
            )
        })
    });
}

/// 不同数据大小的回测基准测试
fn bench_backtest_different_sizes(c: &mut Criterion) {
    let sizes = vec![100, 500, 1000, 2500, 5000];
    let config = BacktestConfig {
        initial_capital: 100000.0,
        commission: 0.001,
        slippage: 0.0005,
    };

    let mut group = c.benchmark_group("backtest_sizes");
    for size in sizes {
        let data = generate_test_data(size);
        let engine = BacktestEngine::new(config.clone());

        group.bench_with_input(
            BenchmarkId::new("backtest", size),
            &size,
            |b, _| {
                b.iter(|| {
                    engine.run(
                        black_box(&data),
                        black_box(&vec![
                            quant_core::types::Signal {
                                timestamp: 0,
                                signal_type: quant_core::types::SignalType::Buy,
                                price: 0.0,
                                strength: 1.0,
                            },
                            quant_core::types::Signal {
                                timestamp: (size / 2) as u64,
                                signal_type: quant_core::types::SignalType::Sell,
                                price: 0.0,
                                strength: 1.0,
                            },
                        ])
                    )
                })
            },
        );
    }
    group.finish();
}

/// 参数优化基准测试
fn bench_optimization(c: &mut Criterion) {
    let data = generate_test_data(1000);
    let engine = OptimizationEngine::new(8);

    // 创建100个参数组合
    let param_combinations: Vec<HashMap<String, f64>> = (0..100)
        .map(|i| {
            std::collections::HashMap::from([
                ("period".to_string(), (5 + i % 50) as f64),
                ("threshold".to_string(), (20.0 + (i as f64 * 0.5)) as f64),
            ])
        })
        .collect();

    c.bench_function("optimization_100_combinations", |b| {
        b.iter(|| {
            engine.optimize_parallel(black_box(&data), black_box(&param_combinations))
        })
    });
}

/// 不同优化组合数的基准测试
fn bench_optimization_different_sizes(c: &mut Criterion) {
    let data = generate_test_data(1000);
    let engine = OptimizationEngine::new(8);

    let sizes = vec![10, 50, 100, 200, 500];

    let mut group = c.benchmark_group("optimization_sizes");
    for size in sizes {
        let param_combinations: Vec<HashMap<String, f64>> = (0..size)
            .map(|i| {
                std::collections::HashMap::from([
                    ("period".to_string(), (5 + i % 50) as f64),
                    ("threshold".to_string(), (20.0 + (i as f64 * 0.5)) as f64),
                ])
            })
            .collect();

        group.bench_with_input(
            BenchmarkId::new("optimization", size),
            &size,
            |b, _| {
                b.iter(|| {
                    engine.optimize_parallel(black_box(&data), black_box(&param_combinations))
                })
            },
        );
    }
    group.finish();
}

/// 技术指标计算基准测试
fn bench_indicators(c: &mut Criterion) {
    use quant_core::indicators::{sma, rsi, macd, bollinger_bands, kdj, cci};

    let data = generate_test_data(1000);
    let prices: Vec<f64> = data.iter().map(|d| d.close).collect();
    let high: Vec<f64> = data.iter().map(|d| d.high).collect();
    let low: Vec<f64> = data.iter().map(|d| d.low).collect();

    let mut group = c.benchmark_group("indicators");

    group.bench_function("sma_20", |b| {
        b.iter(|| sma(black_box(&prices), black_box(20)))
    });

    group.bench_function("ema_20", |b| {
        b.iter(|| quant_core::indicators::ema(black_box(&prices), black_box(20)))
    });

    group.bench_function("rsi_14", |b| {
        b.iter(|| rsi(black_box(&prices), black_box(14)))
    });

    group.bench_function("macd", |b| {
        b.iter(|| macd(black_box(&prices), black_box(12), black_box(26), black_box(9)))
    });

    group.bench_function("bollinger_bands", |b| {
        b.iter(|| bollinger_bands(black_box(&prices), black_box(20), black_box(2.0)))
    });

    group.bench_function("kdj", |b| {
        b.iter(|| kdj(black_box(&high), black_box(&low), black_box(&prices), black_box(9), black_box(3)))
    });

    group.bench_function("cci", |b| {
        b.iter(|| cci(black_box(&high), black_box(&low), black_box(&prices), black_box(20)))
    });

    group.bench_function("adx", |b| {
        b.iter(|| quant_core::indicators::adx(black_box(&high), black_box(&low), black_box(&prices), black_box(14)))
    });

    group.bench_function("atr", |b| {
        b.iter(|| quant_core::indicators::atr(black_box(&high), black_box(&low), black_box(&prices), black_box(14)))
    });

    group.bench_function("obv", |b| {
        b.iter(|| {
            let volumes: Vec<u64> = data.iter().map(|d| d.volume as u64).collect();
            quant_core::indicators::obv(black_box(&prices), black_box(&volumes))
        })
    });

    group.bench_function("ichimoku", |b| {
        b.iter(|| {
            quant_core::indicators::ichimoku_from_ohlcv(
                black_box(&data),
                black_box(9),
                black_box(26),
                black_box(52)
            )
        })
    });

    group.bench_function("parabolic_sar", |b| {
        b.iter(|| quant_core::indicators::parabolic_sar(black_box(&high), black_box(&low), black_box(0.02), black_box(0.2)))
    });

    group.finish();
}

/// 并行回测基准测试
fn bench_parallel_backtests(c: &mut Criterion) {
    let data = Arc::new(generate_test_data(1000));
    let config = BacktestConfig {
        initial_capital: 100000.0,
        commission: 0.001,
        slippage: 0.0005,
    };

    let parallel_levels = vec![1, 4, 8, 16, 32];

    let mut group = c.benchmark_group("parallel_backtests");
    for par_level in parallel_levels {
        group.bench_with_input(
            BenchmarkId::new("parallel", par_level),
            &par_level,
            |b, &par_level| {
                b.iter(|| {
                    (0..par_level)
                        .into_par_iter()
                        .map(|_| {
                            let engine = BacktestEngine::new(config.clone());
                            engine.run(
                                black_box(&data),
                                black_box(&vec![
                                    quant_core::types::Signal {
                                        timestamp: 0,
                                        signal_type: quant_core::types::SignalType::Buy,
                                        price: 0.0,
                                        strength: 1.0,
                                    },
                                ])
                            )
                        })
                        .collect::<Vec<_>>()
                })
            },
        );
    }
    group.finish();
}

/// 端到端基准测试
fn bench_end_to_end(c: &mut Criterion) {
    let data = generate_test_data(1000);
    let config = BacktestConfig {
        initial_capital: 100000.0,
        commission: 0.001,
        slippage: 0.0005,
    };

    c.bench_function("end_to_end_workflow", |b| {
        b.iter(|| {
            // 1. 回测
            let engine = BacktestEngine::new(config.clone());
            let result = engine.run(
                black_box(&data),
                black_box(&vec![
                    quant_core::types::Signal {
                        timestamp: 0,
                        signal_type: quant_core::types::SignalType::Buy,
                        price: 0.0,
                        strength: 1.0,
                    },
                ])
            );

            // 2. 优化
            let opt_engine = OptimizationEngine::new(8);
            let param_combinations: Vec<HashMap<String, f64>> = (0..50)
                .map(|i| {
                    std::collections::HashMap::from([
                        ("period".to_string(), (5 + i % 20) as f64),
                        ("threshold".to_string(), (20.0 + (i as f64 * 1.0)) as f64),
                    ])
                })
                .collect();

            let optimization_results = opt_engine.optimize_parallel(black_box(&data), black_box(&param_combinations));

            // 3. 选最佳参数
            let best = opt_engine.get_best_params_by_sharpe(&optimization_results, 1);

            black_box((result, best))
        })
    });
}

criterion_group!(
    benches,
    bench_single_backtest,
    bench_backtest_different_sizes,
    bench_optimization,
    bench_optimization_different_sizes,
    bench_indicators,
    bench_parallel_backtests,
    bench_end_to_end
);
criterion_main!(benches);
