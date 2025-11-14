//! T038: 内存使用测试
//! 验证系统内存使用 < 1GB (5年数据)

use quant_core::backtest::engine::BacktestEngine;
use quant_core::types::OHLCV;
use std::alloc::{GlobalAlloc, Layout, System};
use std::sync::atomic::{AtomicUsize, Ordering};

/// 内存分配跟踪器
static ALLOCATED: AtomicUsize = AtomicUsize::new(0);

/// 包装默认分配器来跟踪内存使用
struct TrackingAllocator;

unsafe impl GlobalAlloc for TrackingAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        let ptr = System.alloc(layout);
        if !ptr.is_null() {
            ALLOCATED.fetch_add(layout.size(), Ordering::SeqCst);
        }
        ptr
    }

    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        System.dealloc(ptr, layout);
        ALLOCATED.fetch_sub(layout.size(), Ordering::SeqCst);
    }
}

#[global_allocator]
static GLOBAL: TrackingAllocator = TrackingAllocator;

/// 获取当前内存使用量（MB）
fn get_memory_usage_mb() -> f64 {
    ALLOCATED.load(Ordering::SeqCst) as f64 / (1024.0 * 1024.0)
}

/// 重置内存跟踪
fn reset_memory_tracking() {
    let current = ALLOCATED.load(Ordering::SeqCst);
    println!("当前内存使用: {:.2} MB", get_memory_usage_mb());
    ALLOCATED.store(0, Ordering::SeqCst);
}

/// 生成大量测试数据（5年交易日约1260天）
fn generate_large_data(days: usize) -> Vec<OHLCV> {
    let mut data = Vec::with_capacity(days);
    let base_price = 100.0;

    for i in 0..days {
        let price = base_price * (1.0 + (i as f64 * 0.0005));
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

/// 计算OHLCV数据结构的大小
fn calculate_ohlcv_size() -> usize {
    std::mem::size_of::<OHLCV>()
}

/// 测试1年数据（252个交易日）的内存使用
#[test]
fn test_1_year_data_memory() {
    reset_memory_tracking();

    let days = 252;
    let data = generate_large_data(days);

    let memory_used = get_memory_usage_mb();
    let data_size = calculate_ohlcv_size();
    let total_data_size = data.len() * data_size;
    let total_data_mb = total_data_size as f64 / (1024.0 * 1024.0);

    println!("1年数据 ({}) 天的实际内存使用: {:.2} MB", days, memory_used);
    println!("数据本身大小: {:.2} MB", total_data_mb);
    println!("OHLCV结构大小: {} bytes", data_size);

    // 1年数据应该少于10MB
    assert!(
        memory_used < 10.0,
        "1年数据内存使用 {:.2} MB 超过10MB阈值",
        memory_used
    );

    // 数据本身应该约2-3MB
    assert!(
        total_data_mb > 1.0 && total_data_mb < 5.0,
        "数据大小 {:.2} MB 超出预期范围 1-5MB",
        total_data_mb
    );
}

/// 测试5年数据（1260个交易日）的内存使用
#[test]
fn test_5_year_data_memory() {
    reset_memory_tracking();

    let days = 1260;
    let data = generate_large_data(days);

    let memory_used = get_memory_usage_mb();
    let data_size = calculate_ohlcv_size();
    let total_data_size = data.len() * data_size;
    let total_data_mb = total_data_size as f64 / (1024.0 * 1024.0);

    println!("5年数据 ({}) 天的实际内存使用: {:.2} MB", days, memory_used);
    println!("数据本身大小: {:.2} MB", total_data_mb);

    // 5年数据应该少于50MB（主要数据）
    assert!(
        memory_used < 50.0,
        "5年数据内存使用 {:.2} MB 超过50MB阈值",
        memory_used
    );

    // 数据本身应该约5-10MB
    assert!(
        total_data_mb > 5.0 && total_data_mb < 15.0,
        "数据大小 {:.2} MB 超出预期范围 5-15MB",
        total_data_mb
    );
}

/// 测试10年数据（2520个交易日）的内存使用
#[test]
fn test_10_year_data_memory() {
    reset_memory_tracking();

    let days = 2520;
    let data = generate_large_data(days);

    let memory_used = get_memory_usage_mb();
    let data_size = calculate_ohlcv_size();
    let total_data_size = data.len() * data_size;
    let total_data_mb = total_data_size as f64 / (1024.0 * 1024.0);

    println!("10年数据 ({}) 天的实际内存使用: {:.2} MB", days, memory_used);
    println!("数据本身大小: {:.2} MB", total_data_mb);

    // 10年数据应该少于100MB
    assert!(
        memory_used < 100.0,
        "10年数据内存使用 {:.2} MB 超过100MB阈值",
        memory_used
    );

    // 数据本身应该约10-20MB
    assert!(
        total_data_mb > 10.0 && total_data_mb < 30.0,
        "数据大小 {:.2} MB 超出预期范围 10-30MB",
        total_data_mb
    );
}

/// 测试回测引擎的内存占用
#[test]
fn test_backtest_engine_memory_footprint() {
    reset_memory_tracking();

    let data = generate_large_data(1260); // 5年数据
    let engine = BacktestEngine::new(quant_core::backtest::engine::BacktestConfig {
        initial_capital: 100000.0,
        commission: 0.001,
        slippage: 0.0005,
    });

    let engine_memory = get_memory_usage_mb();
    println!("回测引擎初始内存占用: {:.2} MB", engine_memory);

    // 运行回测
    let _result = engine.run(&data, &vec![]);

    let after_backtest_memory = get_memory_usage_mb();
    let additional_memory = after_backtest_memory - engine_memory;

    println!("回测后总内存: {:.2} MB", after_backtest_memory);
    println!("回测额外内存占用: {:.2} MB", additional_memory);

    // 回测引擎本身的内存占用应该很小
    assert!(
        engine_memory < 5.0,
        "回测引擎内存占用 {:.2} MB 超过5MB",
        engine_memory
    );

    // 回测过程中额外内存应该 < 10MB
    assert!(
        additional_memory < 10.0,
        "回测额外内存占用 {:.2} MB 超过10MB",
        additional_memory
    );
}

/// 测试并行优化的内存使用
#[test]
fn test_parallel_optimization_memory() {
    use quant_core::optimization::OptimizationEngine;

    reset_memory_tracking();

    let data = generate_large_data(1000);
    let engine = OptimizationEngine::new(8);

    let before_memory = get_memory_usage_mb();
    println!("优化前内存: {:.2} MB", before_memory);

    // 创建1000个参数组合
    let param_combinations: Vec<_> = (0..1000)
        .map(|i| {
            std::collections::HashMap::from([
                ("period".to_string(), (5 + i % 50) as f64),
                ("threshold".to_string(), (20.0 + (i as f64 * 0.5)) as f64),
            ])
        })
        .collect();

    let results = engine.optimize_parallel(&data, &param_combinations);

    let after_memory = get_memory_usage_mb();
    let peak_memory = after_memory;
    let memory_increase = peak_memory - before_memory;

    println!("优化后内存: {:.2} MB", after_memory);
    println!("内存增长: {:.2} MB", memory_increase);
    println!("结果数量: {}", results.len());

    // 并行优化的内存增长应该 < 200MB
    assert!(
        memory_increase < 200.0,
        "并行优化内存增长 {:.2} MB 超过200MB",
        memory_increase
    );

    assert_eq!(results.len(), 1000);
}

/// 测试长期间回测的内存稳定性
#[test]
fn test_long_term_backtest_memory_stability() {
    use quant_core::backtest::engine::BacktestEngine;
    use quant_core::backtest::engine::BacktestConfig;

    reset_memory_tracking();

    let days = 2520; // 10年
    let data = generate_large_data(days);
    let engine = BacktestEngine::new(BacktestConfig {
        initial_capital: 100000.0,
        commission: 0.001,
        slippage: 0.0005,
    });

    let memory_before = get_memory_usage_mb();
    println!("10年回测前内存: {:.2} MB", memory_before);

    // 运行多次回测
    for iteration in 0..10 {
        let _result = engine.run(&data, &vec![]);
        let current_memory = get_memory_usage_mb();
        let memory_growth = current_memory - memory_before;

        println!("第{}次迭代内存: {:.2} MB, 增长: {:.2} MB",
                 iteration + 1, current_memory, memory_growth);

        // 内存增长应该稳定
        assert!(
            memory_growth < 50.0,
            "第{}次迭代内存增长 {:.2} MB 超过50MB",
            iteration + 1,
            memory_growth
        );
    }

    let final_memory = get_memory_usage_mb();
    let total_growth = final_memory - memory_before;

    println!("最终内存: {:.2} MB, 总增长: {:.2} MB", final_memory, total_growth);

    // 10年回测10次，内存增长应该 < 50MB
    assert!(
        total_growth < 50.0,
        "10年回测10次总内存增长 {:.2} MB 超过50MB",
        total_growth
    );
}

/// 测试内存使用是否符合1GB限制
#[test]
fn test_total_memory_under_1gb() {
    reset_memory_tracking();

    // 模拟实际使用场景
    let data = generate_large_data(2520); // 10年数据
    let engine = BacktestEngine::new(quant_core::backtest::engine::BacktestConfig {
        initial_capital: 100000.0,
        commission: 0.001,
        slippage: 0.0005,
    });

    // 运行回测
    let _result = engine.run(&data, &vec![]);

    let final_memory = get_memory_usage_mb();

    println!("完整系统内存使用: {:.2} MB", final_memory);

    // 总内存使用应该远小于1GB (1024MB)
    assert!(
        final_memory < 100.0,
        "总内存使用 {:.2} MB 接近或超过1GB限制",
        final_memory
    );
}
