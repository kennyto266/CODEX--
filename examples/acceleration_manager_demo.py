"""
T048: Acceleration Manager 使用示例
演示如何使用加速管理器进行智能执行模式选择
"""

import sys
import os
import numpy as np
import pandas as pd
import time
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.performance.acceleration import (
    AccelerationManager,
    AccelerationConfig,
    ExecutionMode,
    get_acceleration_manager,
    run_accelerated_backtest_new,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def generate_sample_data(size: int, start_date: str = '2020-01-01') -> pd.DataFrame:
    """生成示例股票数据"""
    dates = pd.date_range(start_date, periods=size, freq='D')
    prices = 100 + np.cumsum(np.random.randn(size) * 0.5)

    data = pd.DataFrame({
        'Open': prices * (1 + np.random.randn(size) * 0.001),
        'High': prices * (1 + np.random.randn(size) * 0.002),
        'Low': prices * (1 - np.random.randn(size) * 0.002),
        'Close': prices,
        'Volume': np.random.randint(1000, 10000, size),
    }, index=dates)

    return data


def demo_basic_usage():
    """演示基本用法"""
    print("\n" + "="*80)
    print("📖 基础用法演示")
    print("="*80)

    # 1. 创建配置
    config = AccelerationConfig(
        preferred_mode=ExecutionMode.AUTO,
        min_cores_for_rust=2,
        batch_size=200,
        enable_metrics=True,
        auto_switch_mode=True
    )

    # 2. 初始化管理器
    manager = AccelerationManager(config)

    # 3. 显示系统能力
    capabilities = manager.get_capabilities()
    print(f"\n📊 系统能力:")
    print(f"  CPU 核心: {capabilities.cpu_cores} 物理, {capabilities.cpu_count_logical} 逻辑")
    print(f"  内存: {capabilities.total_memory_gb:.2f}GB 总计, {capabilities.available_memory_gb:.2f}GB 可用")
    print(f"  Rust 可用: {capabilities.rust_available}")
    print(f"  Rust 版本: {capabilities.rust_version or 'N/A'}")
    print(f"  Python 版本: {capabilities.py_version}")
    print(f"  平台: {capabilities.platform} {capabilities.architecture}")

    # 4. 生成测试数据
    print(f"\n📈 生成测试数据...")
    data = generate_sample_data(1000, '2020-01-01')
    print(f"  数据大小: {len(data)} 行")
    print(f"  日期范围: {data.index[0].strftime('%Y-%m-%d')} 到 {data.index[-1].strftime('%Y-%m-%d')}")

    # 5. 执行回测 (自动模式选择)
    print(f"\n⚡ 执行回测 (自动模式选择)...")
    result = manager.execute_backtest(
        data=data,
        fast_period=10,
        slow_period=30
    )

    print(f"  执行模式: {result.mode}")
    print(f"  执行时间: {result.execution_time_ms:.2f}ms")
    print(f"  总收益率: {result.total_return:.2%}")
    print(f"  年化收益率: {result.annualized_return:.2%}")
    print(f"  夏普比率: {result.sharpe_ratio:.2f}")
    print(f"  最大回撤: {result.max_drawdown:.2%}")
    print(f"  胜率: {result.win_rate:.2%}")
    print(f"  交易次数: {result.trade_count}")

    # 6. 手动指定模式
    print(f"\n🔧 手动指定模式执行...")
    for mode in [ExecutionMode.PYTHON, ExecutionMode.RUST]:
        try:
            result = manager.execute_backtest(
                data=data,
                fast_period=10,
                slow_period=30,
                mode=mode
            )
            print(f"  {mode.value}: {result.execution_time_ms:.2f}ms, 收益率: {result.total_return:.2%}")
        except Exception as e:
            print(f"  {mode.value}: 错误 - {e}")


def demo_batch_processing():
    """演示批处理"""
    print("\n" + "="*80)
    print("📦 批处理演示")
    print("="*80)

    # 创建配置
    config = AccelerationConfig(
        preferred_mode=ExecutionMode.AUTO,
        enable_metrics=True
    )

    manager = AccelerationManager(config)

    # 生成测试数据
    data = generate_sample_data(500, '2020-01-01')

    # 创建策略配置
    strategy_configs = []
    for fast in [5, 10, 15, 20]:
        for slow in [20, 30, 40]:
            strategy_configs.append({
                'strategy_type': 'ma',
                'params': {'fast_period': fast, 'slow_period': slow}
            })

    print(f"\n📊 策略参数组合数: {len(strategy_configs)}")
    print(f"  参数范围: 快速周期={5,10,15,20}, 慢速周期={20,30,40}")

    # 执行批处理
    print(f"\n⚡ 执行批处理...")
    start_time = time.time()
    results = manager.execute_batch(data, strategy_configs)
    batch_time = (time.time() - start_time) * 1000

    print(f"  执行时间: {batch_time:.2f}ms")
    print(f"  完成策略数: {len(results)}")
    print(f"  平均每策略: {batch_time/len(results):.2f}ms")

    # 找到最佳策略
    if results:
        best_result = None
        best_score = float('-inf')
        for result in results:
            if 'metrics' in result and 'sharpe_ratio' in result['metrics']:
                score = result['metrics']['sharpe_ratio']
                if score > best_score:
                    best_score = score
                    best_result = result

        if best_result:
            print(f"\n🏆 最佳策略:")
            print(f"  夏普比率: {best_result['metrics']['sharpe_ratio']:.2f}")
            print(f"  总收益率: {best_result['metrics']['total_return']:.2%}")


def demo_performance_monitoring():
    """演示性能监控"""
    print("\n" + "="*80)
    print("📊 性能监控演示")
    print("="*80)

    config = AccelerationConfig(
        preferred_mode=ExecutionMode.AUTO,
        enable_metrics=True,
        auto_switch_mode=True,
        performance_threshold_ms=50.0
    )

    manager = AccelerationManager(config)

    # 生成不同大小的数据
    data_sizes = [100, 500, 1000, 2000]

    print(f"\n🔄 执行多轮回测以收集性能数据...")
    for size in data_sizes:
        data = generate_sample_data(size, '2020-01-01')
        result = manager.execute_backtest(
            data=data,
            fast_period=10,
            slow_period=30
        )
        print(f"  数据大小 {size}: {result.execution_time_ms:.2f}ms (模式: {result.mode})")

    # 生成性能报告
    print(f"\n📈 性能报告:")
    report = manager.get_performance_report()
    print(f"  当前模式: {report.get('current_mode', 'N/A')}")
    print(f"  总操作数: {report.get('performance_history_count', 0)}")

    if 'execution_stats' in report and report['execution_stats']:
        stats = report['execution_stats']
        print(f"\n  按模式统计:")
        for mode, data in stats.get('by_mode', {}).items():
            print(f"    {mode}:")
            print(f"      执行次数: {data['count']}")
            print(f"      平均时间: {data['avg_time']:.2f}ms")
            print(f"      最小时间: {data['min_time']:.2f}ms")
            print(f"      最大时间: {data['max_time']:.2f}ms")


def demo_mode_switching():
    """演示模式切换"""
    print("\n" + "="*80)
    print("🔄 模式切换演示")
    print("="*80)

    config = AccelerationConfig(
        preferred_mode=ExecutionMode.AUTO,
        auto_switch_mode=False  # 禁用自动切换
    )

    manager = AccelerationManager(config)

    # 生成测试数据
    data = generate_sample_data(500, '2020-01-01')

    print(f"\n📊 初始模式: {manager.get_current_mode().value}")

    # 手动切换模式
    for mode in [ExecutionMode.PYTHON, ExecutionMode.RUST, ExecutionMode.HYBRID]:
        manager.switch_mode(mode)
        print(f"🔧 切换到: {mode.value}")

        result = manager.execute_backtest(
            data=data,
            fast_period=10,
            slow_period=30
        )
        print(f"  执行时间: {result.execution_time_ms:.2f}ms")
        print(f"  实际模式: {result.mode}")


def demo_global_manager():
    """演示全局管理器"""
    print("\n" + "="*80)
    print("🌐 全局管理器演示")
    print("="*80)

    # 获取全局管理器
    manager1 = get_acceleration_manager()
    manager2 = get_acceleration_manager()

    print(f"\n📊 检查单例模式:")
    print(f"  第一次获取: {id(manager1)}")
    print(f"  第二次获取: {id(manager2)}")
    print(f"  是同一实例: {manager1 is manager2}")

    # 使用便捷函数
    data = generate_sample_data(200, '2020-01-01')

    print(f"\n⚡ 使用便捷函数执行回测:")
    result = run_accelerated_backtest_new(
        data=data,
        fast_period=10,
        slow_period=30
    )
    print(f"  执行时间: {result.execution_time_ms:.2f}ms")
    print(f"  执行模式: {result.mode}")
    print(f"  收益率: {result.total_return:.2%}")


def demo_config_file():
    """演示配置文件加载（概念示例）"""
    print("\n" + "="*80)
    print("⚙️ 配置文件演示")
    print("="*80)

    print(f"\n📝 配置文件位置: config/acceleration.yaml")
    print(f"\n示例配置场景:")

    scenarios = {
        "开发环境": {
            "preferred_mode": "python",
            "min_cores_for_rust": 1,
            "min_memory_gb_for_rust": 1.0,
            "max_data_points_for_rust": 5000,
            "batch_size": 50,
            "auto_switch_mode": False
        },
        "生产环境": {
            "preferred_mode": "auto",
            "min_cores_for_rust": 4,
            "min_memory_gb_for_rust": 4.0,
            "max_data_points_for_rust": 50000,
            "batch_size": 200,
            "enable_metrics": True,
            "auto_switch_mode": True
        },
        "高性能环境": {
            "preferred_mode": "rust",
            "min_cores_for_rust": 8,
            "min_memory_gb_for_rust": 8.0,
            "max_data_points_for_rust": 100000,
            "batch_size": 500
        }
    }

    for name, config_dict in scenarios.items():
        print(f"\n  {name}:")
        for key, value in config_dict.items():
            print(f"    {key}: {value}")

    print(f"\n💡 提示: 实际使用时可从 YAML 文件加载配置")
    print(f"  import yaml")
    print(f"  with open('config/acceleration.yaml', 'r') as f:")
    print(f"      config_dict = yaml.safe_load(f)")
    print(f"  # 然后根据配置创建 AccelerationConfig 对象")


def main():
    """主演示函数"""
    print("\n" + "="*80)
    print("🚀 T048: Acceleration Manager 使用指南")
    print("="*80)

    try:
        # 基础用法
        demo_basic_usage()

        # 批处理
        demo_batch_processing()

        # 性能监控
        demo_performance_monitoring()

        # 模式切换
        demo_mode_switching()

        # 全局管理器
        demo_global_manager()

        # 配置文件
        demo_config_file()

        print("\n" + "="*80)
        print("✅ 所有演示完成")
        print("="*80)
        print("\n💡 更多信息:")
        print("  - 配置文件: config/acceleration.yaml")
        print("  - 测试文件: tests/test_acceleration_manager.py")
        print("  - 源代码: src/performance/acceleration.py")

    except Exception as e:
        print(f"\n❌ 演示过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
