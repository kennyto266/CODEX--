"""
QF-Lib 集成示例

演示如何使用QF-Lib进行回测，并与现有技术指标系统集成
"""

import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from typing import List, Dict, Any

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.backtest.qf_lib_adapter import (
    QFLibBacktestEngine,
    QFLibBacktestConfig,
    run_qf_lib_backtest,
    run_portfolio_backtest,
    create_qf_lib_backtester
)
from src.backtest.python_engine import TechnicalIndicators

logger = None  # 使用默认日志配置


def generate_sample_data(
    symbol: str = "0700.HK",
    days: int = 365,
    start_price: float = 400.0
) -> List[Dict[str, Any]]:
    """
    生成示例股价数据

    Args:
        symbol: 股票代码
        days: 数据天数
        start_price: 起始价格

    Returns:
        市场数据列表
    """
    np.random.seed(42)  # 固定种子，确保结果可重现

    data = []
    current_price = start_price

    for i in range(days):
        # 生成随机价格变动（几何布朗运动）
        daily_return = np.random.normal(0.0005, 0.02)  # 平均日收益0.05%，波动率2%
        current_price = current_price * (1 + daily_return)

        # 生成OHLC数据
        open_price = current_price * (1 + np.random.normal(0, 0.005))
        high_price = max(open_price, current_price) * (1 + abs(np.random.normal(0, 0.01)))
        low_price = min(open_price, current_price) * (1 - abs(np.random.normal(0, 0.01)))
        close_price = current_price
        volume = int(np.random.uniform(1000000, 10000000))

        # 确保数据合理性
        high_price = max(high_price, open_price, close_price)
        low_price = min(low_price, open_price, close_price)

        data.append({
            'timestamp': (datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d'),
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': volume
        })

    return data


def demo_basic_strategy():
    """演示基本策略回测"""
    print("\n" + "="*60)
    print("演示1: 基本策略回测")
    print("="*60)

    # 生成示例数据
    print("\n1. 生成示例数据 (腾讯 0700.HK, 365天)")
    data = generate_sample_data("0700.HK", days=365, start_price=400.0)
    print(f"   生成了 {len(data)} 天的数据")
    print(f"   起始价格: ${data[0]['close']:.2f}")
    print(f"   结束价格: ${data[-1]['close']:.2f}")

    # 配置回测参数
    print("\n2. 配置回测参数")
    config = QFLibBacktestConfig(
        initial_capital=100000.0,
        commission=0.001,  # 0.1% 佣金
        slippage=0.0005,   # 0.05% 滑点
        risk_free_rate=0.03
    )
    print(f"   初始资本: ${config.initial_capital:,.2f}")
    print(f"   佣金: {config.commission:.2%}")
    print(f"   滑点: {config.slippage:.2%}")

    # 创建回测引擎
    print("\n3. 创建QF-Lib回测引擎")
    engine = QFLibBacktestEngine(config)

    # 运行回测
    print("\n4. 运行策略回测")
    results = engine.run_strategy(
        data=data,
        strategy_name="MA交叉策略",
        strategy_params={'fast_period': 20, 'slow_period': 50}
    )

    # 显示结果
    print("\n5. 回测结果:")
    report = engine.generate_report(results)
    print(report)

    return results


def demo_multi_asset_strategy():
    """演示多资产策略"""
    print("\n" + "="*60)
    print("演示2: 多资产策略回测")
    print("="*60)

    # 生成多个资产的数据
    print("\n1. 生成多资产数据")
    assets = {
        '0700.HK': generate_sample_data("0700.HK", days=365, start_price=400.0),
        '0388.HK': generate_sample_data("0388.HK", days=365, start_price=300.0),
        '1398.HK': generate_sample_data("1398.HK", days=365, start_price=5.0),
        '0939.HK': generate_sample_data("0939.HK", days=365, start_price=6.0)
    }

    for symbol, data in assets.items():
        print(f"   {symbol}: {len(data)}天, ${data[0]['close']:.2f} -> ${data[-1]['close']:.2f}")

    # 配置投资组合权重
    weights = {
        '0700.HK': 0.3,   # 腾讯 30%
        '0388.HK': 0.3,   # 港交所 30%
        '1398.HK': 0.2,   # 工行 20%
        '0939.HK': 0.2    # 建行 20%
    }

    print("\n2. 配置投资组合权重:")
    for symbol, weight in weights.items():
        print(f"   {symbol}: {weight:.0%}")

    # 运行多资产回测
    print("\n3. 运行多资产策略回测")
    results = run_portfolio_backtest(
        assets_data=assets,
        weights=weights,
        initial_capital=500000.0
    )

    print("\n4. 多资产回测结果:")
    print(f"   策略名称: {results['strategy_name']}")
    print(f"   投资组合收益率: {results['portfolio_return']:.2%}")
    print(f"   使用QF-Lib: {results.get('qf_lib_used', False)}")

    # 显示各资产表现
    print("\n   各资产表现:")
    for symbol, result in results['individual_results'].items():
        print(f"     {symbol}: {result.get('total_return', 0):.2%} "
              f"(夏普比率: {result.get('sharpe_ratio', 0):.2f})")

    return results


def demo_technical_indicators():
    """演示技术指标集成"""
    print("\n" + "="*60)
    print("演示3: 技术指标系统集成")
    print("="*60)

    # 生成示例数据
    print("\n1. 生成示例数据")
    data = generate_sample_data("0700.HK", days=365, start_price=400.0)

    # 转换为numpy数组
    prices = np.array([d['close'] for d in data])
    high = np.array([d['high'] for d in data])
    low = np.array([d['low'] for d in data])

    print(f"   数据长度: {len(prices)} 天")

    # 使用现有的技术指标系统
    print("\n2. 计算技术指标")
    indicators = TechnicalIndicators()

    # 计算各种指标
    sma_20 = indicators.sma(prices, 20)
    sma_50 = indicators.sma(prices, 50)
    rsi = indicators.rsi(prices, 14)
    macd, macd_signal, macd_hist = indicators.macd(prices)
    bb_upper, bb_middle, bb_lower = indicators.bollinger_bands(prices, 20, 2.0)
    atr = indicators.atr(high, low, prices, 14)

    # 显示指标统计
    print(f"\n3. 指标统计:")
    print(f"   SMA(20) 最新值: {sma_20[-1]:.2f}")
    print(f"   SMA(50) 最新值: {sma_50[-1]:.2f}")
    print(f"   RSI(14) 最新值: {rsi[-1]:.2f}")
    print(f"   MACD 最新值: {macd[-1]:.4f}")
    print(f"   布林带上轨: {bb_upper[-1]:.2f}")
    print(f"   布林带下轨: {bb_lower[-1]:.2f}")
    print(f"   ATR(14) 最新值: {atr[-1]:.2f}")

    # 生成交易信号
    print("\n4. 生成交易信号")
    signals = np.zeros(len(prices))
    for i in range(1, len(prices)):
        if np.isnan(sma_20[i]) or np.isnan(sma_50[i]) or np.isnan(rsi[i]):
            continue

        # 买入信号
        if (sma_20[i-1] <= sma_50[i-1] and sma_20[i] > sma_50[i] and rsi[i] < 70):
            signals[i] = 1

        # 卖出信号
        elif (sma_20[i-1] >= sma_50[i-1] and sma_20[i] < sma_50[i]) or rsi[i] > 80:
            signals[i] = -1

    buy_signals = np.sum(signals == 1)
    sell_signals = np.sum(signals == -1)

    print(f"   买入信号: {buy_signals} 次")
    print(f"   卖出信号: {sell_signals} 次")

    return {
        'indicators': {
            'sma_20': sma_20,
            'sma_50': sma_50,
            'rsi': rsi,
            'macd': macd,
            'bb_upper': bb_upper,
            'bb_lower': bb_lower,
            'atr': atr
        },
        'signals': signals
    }


def demo_portfolio_optimization():
    """演示投资组合优化"""
    print("\n" + "="*60)
    print("演示4: 投资组合优化")
    print("="*60)

    # 生成多个资产的历史数据
    print("\n1. 生成多资产历史数据")
    assets_data = {
        '0700.HK': generate_sample_data("0700.HK", days=1000, start_price=400.0),
        '0388.HK': generate_sample_data("0388.HK", days=1000, start_price=300.0),
        '1398.HK': generate_sample_data("1398.HK", days=1000, start_price=5.0),
        '0939.HK': generate_sample_data("0939.HK", days=1000, start_price=6.0),
        '3988.HK': generate_sample_data("3988.HK", days=1000, start_price=3.0),
        '2318.HK': generate_sample_data("2318.HK", days=1000, start_price=50.0)
    }

    print(f"   生成了 {len(assets_data)} 个资产的数据，每个资产 {len(next(iter(assets_data.values())))} 天")

    # 创建回测引擎
    config = QFLibBacktestConfig(initial_capital=1000000.0)
    engine = QFLibBacktestEngine(config)

    # 运行投资组合优化
    print("\n2. 运行均值-方差优化")
    optimization_result = engine.run_portfolio_optimization(
        assets_data=assets_data,
        method='mean_variance'
    )

    print("\n3. 优化结果:")
    print(f"   优化方法: {optimization_result['method']}")
    print(f"   期望收益率: {optimization_result.get('expected_return', 0):.2%}")
    print(f"   期望波动率: {optimization_result.get('expected_volatility', 0):.2%}")
    print(f"   使用QF-Lib: {optimization_result.get('qf_lib_used', False)}")

    print("\n   最优权重:")
    for symbol, weight in optimization_result.get('optimal_weights', {}).items():
        print(f"     {symbol}: {weight:.2%}")

    return optimization_result


def demo_risk_analysis():
    """演示风险分析"""
    print("\n" + "="*60)
    print("演示5: 风险分析")
    print("="*60)

    # 运行基本回测获取数据
    print("\n1. 运行基本策略获取回测数据")
    data = generate_sample_data("0700.HK", days=365, start_price=400.0)
    config = QFLibBacktestConfig(initial_capital=100000.0)
    engine = QFLibBacktestEngine(config)
    results = engine.run_strategy(data, "风险分析策略")

    print("\n2. 计算风险指标")
    risk_metrics = engine.analyze_risk_metrics(results)

    print("\n3. 风险分析结果:")
    print(f"   VaR (95%): {risk_metrics['var_95']:.2%}")
    print(f"   CVaR (95%): {risk_metrics['cvar_95']:.2%}")
    print(f"   最大回撤: {risk_metrics['max_drawdown']:.2%}")
    print(f"   偏度: {risk_metrics['skewness']:.2f}")
    print(f"   峰度: {risk_metrics['kurtosis']:.2f}")

    # 解释风险指标
    print("\n4. 风险指标解释:")
    if risk_metrics['var_95'] < -0.05:
        print("   ⚠️  VaR较高，存在较大潜在损失风险")
    else:
        print("   ✓ VaR在可接受范围内")

    if risk_metrics['skewness'] < 0:
        print("   ⚠️  负偏度，左尾风险较高（极端损失概率大）")
    else:
        print("   ✓ 正偏度，收益分布相对正常")

    if risk_metrics['max_drawdown'] > 0.2:
        print("   ⚠️  最大回撤较高，风险较大")
    else:
        print("   ✓ 最大回撤在可接受范围内")

    return risk_metrics


def compare_with_python_engine():
    """比较QF-Lib与Python引擎的性能"""
    print("\n" + "="*60)
    print("演示6: 性能比较")
    print("="*60)

    import time

    # 生成测试数据
    print("\n1. 准备测试数据")
    data = generate_sample_data("0700.HK", days=1000, start_price=400.0)
    print(f"   数据大小: {len(data)} 条记录")

    # 测试QF-Lib引擎（使用fallback实现）
    print("\n2. 测试QF-Lib引擎性能")
    config = QFLibBacktestConfig(initial_capital=100000.0)
    engine = QFLibBacktestEngine(config)

    start_time = time.time()
    qf_results = engine.run_strategy(data, "QF-Lib策略")
    qf_time = time.time() - start_time

    print(f"   执行时间: {qf_time:.4f} 秒")
    print(f"   总收益率: {qf_results.get('total_return', 0):.2%}")
    print(f"   使用QF-Lib: {qf_results.get('qf_lib_used', False)}")

    # 测试Python引擎
    print("\n3. 测试Python引擎性能")
    from src.backtest.python_engine import PythonBacktestEngine

    python_engine = PythonBacktestEngine(initial_capital=100000.0)

    start_time = time.time()
    python_result = python_engine.run_backtest(
        data=data,
        strategy_type='ma',
        params={'fast_period': 20, 'slow_period': 50}
    )
    python_time = time.time() - start_time

    print(f"   执行时间: {python_time:.4f} 秒")
    print(f"   总收益率: {python_result.total_return:.2%}")

    # 比较结果
    print("\n4. 性能比较:")
    print(f"   QF-Lib引擎: {qf_time:.4f}s")
    print(f"   Python引擎: {python_time:.4f}s")
    if python_time > 0:
        speedup = qf_time / python_time
        print(f"   速度比率: {speedup:.2f}x")

    return {
        'qf_lib_time': qf_time,
        'python_time': python_time,
        'qf_lib_result': qf_results,
        'python_result': python_result.to_dict() if hasattr(python_result, 'to_dict') else python_result
    }


def main():
    """主演示函数"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*10 + "QF-Lib 回测引擎集成演示" + " "*21 + "║")
    print("╚" + "="*58 + "╝")
    print("\n这个演示将展示如何使用QF-Lib进行交易策略回测，")
    print("并与现有的技术指标系统集成。\n")

    try:
        # 演示1: 基本策略
        demo_basic_strategy()

        # 演示2: 多资产策略
        demo_multi_asset_strategy()

        # 演示3: 技术指标集成
        demo_technical_indicators()

        # 演示4: 投资组合优化
        demo_portfolio_optimization()

        # 演示5: 风险分析
        demo_risk_analysis()

        # 演示6: 性能比较
        compare_with_python_engine()

        print("\n" + "="*60)
        print("✓ 所有演示完成!")
        print("="*60)
        print("\n使用说明:")
        print("1. 使用 create_qf_lib_backtester() 创建回测引擎")
        print("2. 使用 run_qf_lib_backtest() 进行快速回测")
        print("3. 使用 run_portfolio_backtest() 进行多资产回测")
        print("4. 所有指标计算使用现有的TechnicalIndicators类")
        print("5. 即使QF-Lib未安装，也会自动使用fallback实现")

    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
