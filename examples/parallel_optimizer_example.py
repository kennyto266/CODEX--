"""
Rayon-based Parallel Optimizer 使用示例
展示如何使用高性能並行參數優化器
"""

import sys
import os
import time
import numpy as np
import pandas as pd

# 添加項目根目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.performance.parallel_optimizer_enhanced import (
    ParallelOptimizer,
    OptimizationConfig,
    optimize_parameters,
    CPUDetector
)


def example_1_basic_usage():
    """示例 1: 基本使用"""
    print("\n" + "=" * 70)
    print("示例 1: 基本使用 - MA 策略參數優化")
    print("=" * 70)

    # 生成測試數據
    dates = pd.date_range('2020-01-01', periods=500, freq='D')
    prices = 100 + np.cumsum(np.random.randn(500) * 0.5)
    data = pd.DataFrame({
        'Close': prices,
        'Volume': np.random.randint(1000, 10000, 500),
    }, index=dates)

    # 定義參數空間
    parameter_spaces = [
        {'name': 'fast_period', 'min': 5, 'max': 30, 'step': 5},
        {'name': 'slow_period', 'min': 20, 'max': 100, 'step': 20},
    ]

    # 執行優化
    result = optimize_parameters(
        data=data,
        strategy_type='ma',
        parameter_spaces=parameter_spaces,
        max_workers=4
    )

    # 打印結果
    print(f"\n✅ 優化完成!")
    print(f"   最佳參數: {result.best_params}")
    print(f"   最佳分數: {result.best_score:.4f}")
    print(f"   執行時間: {result.execution_time_ms:.2f}ms")
    print(f"   總組合數: {result.total_combinations}")
    print(f"   加速比: {result.speedup_factor:.2f}x")
    print(f"   吞吐量: {result.throughput_per_second:.2f} 組合/秒")


def example_2_advanced_config():
    """示例 2: 高級配置"""
    print("\n" + "=" * 70)
    print("示例 2: 高級配置 - 自定義優化參數")
    print("=" * 70)

    # 生成測試數據
    dates = pd.date_range('2020-01-01', periods=1000, freq='D')
    prices = 100 + np.cumsum(np.random.randn(1000) * 0.5)
    data = pd.DataFrame({
        'Close': prices,
        'Volume': np.random.randint(1000, 10000, 1000),
    }, index=dates)

    # 創建高級配置
    config = OptimizationConfig(
        strategy_type='kdj',
        parameter_spaces=[
            {'name': 'k_period', 'min': 5, 'max': 30, 'step': 5},
            {'name': 'd_period', 'min': 3, 'max': 5, 'step': 1},
            {'name': 'oversold', 'min': 20, 'max': 40, 'step': 5},
            {'name': 'overbought', 'min': 60, 'max': 80, 'step': 5},
        ],
        data=data,
        objective='sharpe_ratio',
        max_workers=8,
        chunk_size=50,
        timeout_seconds=60,
        use_rayon=True,
        use_rust=True,
        adaptive_chunking=True,
        load_balance=True,
        memory_limit_mb=2048
    )

    # 創建優化器
    optimizer = ParallelOptimizer(config)

    # 執行優化
    start_time = time.time()
    result = optimizer.optimize()
    total_time = time.time() - start_time

    # 打印結果
    print(f"\n✅ 高級配置優化完成!")
    print(f"   執行時間: {result.execution_time_ms:.2f}ms ({total_time:.2f}s)")
    print(f"   最佳參數: {result.best_params}")
    print(f"   最佳分數: {result.best_score:.4f}")
    print(f"   加速比: {result.speedup_factor:.2f}x")
    print(f"   負載均衡效率: {result.load_balance_efficiency:.2%}")
    print(f"   峰值內存: {result.peak_memory_mb:.2f}MB")


def example_3_custom_backtest():
    """示例 3: 自定義回測函數"""
    print("\n" + "=" * 70)
    print("示例 3: 自定義回測函數")
    print("=" * 70)

    # 生成測試數據
    dates = pd.date_range('2020-01-01', periods=500, freq='D')
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(500) * 0.5)
    data = pd.DataFrame({
        'Close': prices,
        'Volume': np.random.randint(1000, 10000, 500),
    }, index=dates)

    # 定義參數空間
    parameter_spaces = [
        {'name': 'fast', 'min': 5, 'max': 20, 'step': 5},
        {'name': 'slow', 'min': 20, 'max': 50, 'step': 10},
    ]

    # 定義自定義回測函數
    def custom_backtest(data, strategy_type, fast, slow):
        """自定義回測實現"""
        # 模擬回測邏輯
        if strategy_type == 'ma':
            # 簡單移動平均策略
            fast_ma = data['Close'].rolling(fast).mean()
            slow_ma = data['Close'].rolling(slow).mean()

            # 計算信號
            signals = (fast_ma > slow_ma).astype(int)
            signals = signals.diff().fillna(0)

            # 計算收益
            returns = data['Close'].pct_change()
            strategy_returns = signals.shift(1) * returns

            # 計算指標
            total_return = (1 + strategy_returns).prod() - 1
            volatility = strategy_returns.std() * np.sqrt(252)
            sharpe_ratio = total_return / volatility if volatility > 0 else 0
            max_drawdown = ((1 + strategy_returns).cumprod() / (1 + strategy_returns).cumprod().cummax() - 1).min()

            return {
                'total_return': total_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'volatility': volatility,
                'win_rate': (strategy_returns > 0).mean()
            }

        # 默認返回
        return {
            'total_return': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
        }

    # 創建配置
    config = OptimizationConfig(
        strategy_type='ma',
        parameter_spaces=parameter_spaces,
        data=data,
        objective='sharpe_ratio',
        max_workers=4
    )

    # 創建優化器
    optimizer = ParallelOptimizer(config)

    # 執行優化（使用自定義回測函數）
    result = optimizer.optimize(backtest_function=custom_backtest)

    # 打印結果
    print(f"\n✅ 自定義回測優化完成!")
    print(f"   執行時間: {result.execution_time_ms:.2f}ms")
    print(f"   最佳參數: {result.best_params}")
    print(f"   最佳 Sharpe 比率: {result.best_score:.4f}")
    print(f"   吞吐量: {result.throughput_per_second:.2f} 組合/秒")

    # 顯示前 3 個最佳結果
    sorted_results = sorted(result.all_results, key=lambda x: x['score'], reverse=True)
    print(f"\n🏆 前 3 個最佳參數組合:")
    for i, res in enumerate(sorted_results[:3], 1):
        print(f"   {i}. 參數: {res['params']}, 分數: {res['score']:.4f}")


def example_4_performance_monitoring():
    """示例 4: 性能監控"""
    print("\n" + "=" * 70)
    print("示例 4: 性能監控與報告")
    print("=" * 70)

    # 獲取 CPU 信息
    cpu_info = CPUDetector.detect_cpu_cores()
    print(f"\n💻 系統信息:")
    print(f"   物理核心: {cpu_info['physical_cores']}")
    print(f"   邏輯核心: {cpu_info['logical_cores']}")
    print(f"   推薦工作線程: {cpu_info['max_recommended_workers']}")
    print(f"   當前 CPU 使用率: {cpu_info['current_cpu_percent']:.1f}%")

    # 生成測試數據
    dates = pd.date_range('2020-01-01', periods=1000, freq='D')
    prices = 100 + np.cumsum(np.random.randn(1000) * 0.5)
    data = pd.DataFrame({
        'Close': prices,
        'Volume': np.random.randint(1000, 10000, 1000),
    }, index=dates)

    # 定義參數空間
    parameter_spaces = [
        {'name': 'p1', 'min': 5, 'max': 30, 'step': 5},
        {'name': 'p2', 'min': 20, 'max': 50, 'step': 10},
    ]

    # 執行多次優化以查看歷史
    results = []
    for i in range(3):
        print(f"\n第 {i+1} 次優化...")
        result = optimize_parameters(
            data=data,
            strategy_type='ma',
            parameter_spaces=parameter_spaces,
            max_workers=4
        )
        results.append(result)

    # 獲取性能報告
    config = OptimizationConfig(
        strategy_type='ma',
        parameter_spaces=parameter_spaces,
        data=data
    )
    optimizer = ParallelOptimizer(config)
    report = optimizer.get_performance_report()

    print(f"\n📊 性能報告:")
    print(f"   總優化次數: {report['total_optimizations']}")
    print(f"   平均執行時間: {report['average_execution_time_ms']:.2f}ms")
    print(f"   平均加速比: {report['average_speedup_factor']:.2f}x")
    print(f"   平均吞吐量: {report['average_throughput']:.2f} 組合/秒")

    # 性能趨勢
    print(f"\n📈 性能趨勢:")
    for i, res in enumerate(results):
        print(f"   第 {i+1} 次: {res.execution_time_ms:.2f}ms, "
              f"加速比 {res.speedup_factor:.2f}x, "
              f"吞吐量 {res.throughput_per_second:.2f} 組合/秒")


def example_5_benchmark():
    """示例 5: 性能基準測試"""
    print("\n" + "=" * 70)
    print("示例 5: 性能基準測試 - 驗證 1000 組合 < 10 秒")
    print("=" * 70)

    # 生成大型測試數據
    dates = pd.date_range('2020-01-01', periods=2000, freq='D')
    prices = 100 + np.cumsum(np.random.randn(2000) * 0.5)
    data = pd.DataFrame({
        'Close': prices,
        'Volume': np.random.randint(1000, 10000, 2000),
    }, index=dates)

    # 生成足夠多的參數組合
    parameter_spaces = [
        {'name': 'fast', 'min': 5, 'max': 50, 'step': 5},  # 10 個值
        {'name': 'slow', 'min': 20, 'max': 100, 'step': 10},  # 9 個值
    ]
    # 總共 10 * 9 = 90 個組合

    # 測試不同工作線程數
    worker_configs = [1, 2, 4, 8]
    results = []

    for workers in worker_configs:
        print(f"\n測試 {workers} 個工作線程...")
        result = optimize_parameters(
            data=data,
            strategy_type='ma',
            parameter_spaces=parameter_spaces,
            max_workers=workers
        )
        results.append((workers, result))
        print(f"  執行時間: {result.execution_time_ms:.2f}ms")
        print(f"  加速比: {result.speedup_factor:.2f}x")

    # 比較結果
    print(f"\n📊 性能比較:")
    print(f"{'工作線程':<10} {'執行時間(ms)':<15} {'加速比':<10} {'吞吐量(組合/秒)':<20}")
    print("-" * 60)
    for workers, result in results:
        print(f"{workers:<10} {result.execution_time_ms:<15.2f} "
              f"{result.speedup_factor:<10.2f} {result.throughput_per_second:<20.2f}")

    # 找到最佳配置
    best = min(results, key=lambda x: x[1].execution_time_ms)
    print(f"\n🏆 最佳配置: {best[0]} 個工作線程")
    print(f"   執行時間: {best[1].execution_time_ms:.2f}ms")
    print(f"   加速比: {best[1].speedup_factor:.2f}x")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("🚀 Rayon-based Parallel Optimizer 使用示例")
    print("=" * 70)

    try:
        # 運行所有示例
        example_1_basic_usage()
        example_2_advanced_config()
        example_3_custom_backtest()
        example_4_performance_monitoring()
        example_5_benchmark()

        print("\n" + "=" * 70)
        print("✅ 所有示例運行完成!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ 運行示例時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
