"""
Phase 8 Enhanced Features 示例演示
展示所有高级策略的使用方法 (T179-T183)

Author: Claude Code
Date: 2025-11-09
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from strategy.multi_timeframe import MultiTimeframeStrategy
from strategy.portfolio_strategy import PortfolioStrategy
from strategy.ensemble_strategy import EnsembleStrategy
from strategy.ml_strategy import MLStrategy
from strategy.builder import StrategyBuilder
try:
    from strategies import BaseStrategy
except ImportError:
    from core.base_strategy import IStrategy as BaseStrategy
from core.base_strategy import Signal, SignalType


def generate_sample_data(symbol='0700.HK', days=500):
    """生成示例OHLCV数据"""
    dates = pd.date_range(start='2023-01-01', periods=days, freq='D')
    np.random.seed(42)

    # 生成模拟价格数据
    price_base = 100
    returns = np.random.normal(0.001, 0.02, days)
    prices = [price_base]

    for r in returns[1:]:
        prices.append(prices[-1] * (1 + r))

    data = pd.DataFrame({
        'Date': dates,
        'Open': [p * (1 + np.random.normal(0, 0.005)) for p in prices],
        'High': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'Low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, days)
    })
    data.set_index('Date', inplace=True)
    data['Symbol'] = symbol

    return data


def demo_multi_timeframe():
    """演示多时间框架策略"""
    print("\n" + "="*60)
    print("Demo 1: Multi-Timeframe Strategy (T179)")
    print("="*60)

    # 生成多时间框架数据
    daily = generate_sample_data('0700.HK', 365)
    weekly = daily.resample('W').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    })
    monthly = daily.resample('M').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    })

    # 创建策略
    strategy = MultiTimeframeStrategy(
        timeframes=['1D', '1W', '1M'],
        primary_timeframe='1D',
        confirmation_levels=2,
        trend_alignment_threshold=0.6,
        min_confidence=0.5
    )

    # 初始化
    strategy.initialize(
        daily,
        timeframe_data={
            '1D': daily,
            '1W': weekly,
            '1M': monthly
        }
    )

    # 获取趋势摘要
    summary = strategy.get_trend_summary()
    print(f"\nTrend Summary:")
    print(f"  Primary Timeframe: {summary['primary_timeframe']}")
    print(f"  Trend Alignment: {summary['alignment']:.2f}")
    print(f"  Primary Trend: {summary['primary_trend']}")

    # 生成信号
    signals = strategy.generate_signals(daily.tail(50))
    print(f"\nGenerated Signals: {len(signals)}")
    for signal in signals[:3]:  # 显示前3个信号
        print(f"  - {signal.signal_type.value}: {signal.reason}, Confidence: {signal.confidence:.2f}")

    return strategy


def demo_portfolio_strategy():
    """演示投资组合策略"""
    print("\n" + "="*60)
    print("演示2: 投资组合策略 (T180)")
    print("="*60)

    # 生成多资产数据
    symbols = ['0700.HK', '0388.HK', '1398.HK', '0939.HK']
    portfolio_data = {}

    for symbol in symbols:
        portfolio_data[symbol] = generate_sample_data(symbol, 365)

    # 创建策略
    strategy = PortfolioStrategy(
        symbols=symbols,
        rebalance_frequency='monthly',
        risk_target=0.15,
        max_weight=0.4,
        min_weight=0.05,
        risk_parity=True
    )

    # 初始化
    strategy.initialize(
        portfolio_data['0700.HK'],
        portfolio_data=portfolio_data
    )

    # 获取投资组合摘要
    summary = strategy.get_portfolio_summary()
    print(f"\n投资组合摘要:")
    print(f"  策略名称: {summary['strategy_name']}")
    print(f"  资产数量: {len(summary['symbols'])}")
    print(f"  再平衡频率: {summary['rebalance_frequency']}")

    if 'portfolio_metrics' in summary:
        metrics = summary['portfolio_metrics']
        print(f"  组合波动率: {metrics['volatility']:.2%}")
        print(f"  夏普比率: {metrics['sharpe_ratio']:.2f}")
        print(f"  最大回撤: {metrics['max_drawdown']:.2%}")

    # 生成信号
    signals = strategy.generate_signals(portfolio_data['0700.HK'].tail(50))
    print(f"\n生成的信号数量: {len(signals)}")
    for signal in signals[:3]:
        print(f"  - {signal.symbol}: {signal.signal_type.value}")
        print(f"    原因: {signal.reason}")
        print(f"    置信度: {signal.confidence:.2f}")

    return strategy


def demo_ensemble_strategy():
    """演示集成策略"""
    print("\n" + "="*60)
    print("演示3: 集成策略 (T181)")
    print("="*60)

    # 创建基础策略
    class SimpleRSI(BaseStrategy):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

        def generate_signals(self, data):
            signals = []
            if len(data) < 14:
                return signals
            from core.base_strategy import Signal, SignalType
            latest = data.iloc[-1]
            signals.append(Signal(
                symbol='0700.HK',
                timestamp=latest.name,
                signal_type=SignalType.BUY,
                confidence=0.7,
                reason='RSI Signal',
                price=float(latest['Close'])
            ))
            return signals

    class SimpleMACD(BaseStrategy):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

        def generate_signals(self, data):
            signals = []
            if len(data) < 26:
                return signals
            from core.base_strategy import Signal, SignalType
            latest = data.iloc[-1]
            signals.append(Signal(
                symbol='0700.HK',
                timestamp=latest.name,
                signal_type=SignalType.BUY,
                confidence=0.6,
                reason='MACD Signal',
                price=float(latest['Close'])
            ))
            return signals

    rsi_strategy = SimpleRSI(symbol='0700.HK')
    macd_strategy = SimpleMACD(symbol='0700.HK')

    # 创建集成策略
    ensemble = EnsembleStrategy(
        strategies=[rsi_strategy, macd_strategy],
        voting_method='weighted',
        min_consensus=0.6,
        confidence_threshold=0.5,
        adaptive_weights=True
    )

    # 生成示例数据
    data = generate_sample_data('0700.HK', 365)

    # 生成信号
    signals = ensemble.generate_signals(data.tail(100))
    print(f"\n生成的集成信号数量: {len(signals)}")

    for signal in signals[:3]:
        print(f"\n信号:")
        print(f"  类型: {signal.signal_type.value}")
        print(f"  置信度: {signal.confidence:.2f}")
        print(f"  原因: {signal.reason}")
        if 'metadata' in signal and 'voting_method' in signal['metadata']:
            print(f"  投票方法: {signal['metadata']['voting_method']}")

    # 获取集成摘要
    summary = ensemble.get_ensemble_summary()
    print(f"\n集成摘要:")
    print(f"  投票方法: {summary['voting_method']}")
    print(f"  基础策略数量: {len(summary['base_strategies'])}")
    print(f"  自适应权重: {summary['adaptive_weights']}")
    print(f"  最小共识度: {summary['min_consensus']}")

    return ensemble


def demo_ml_strategy():
    """演示机器学习策略"""
    print("\n" + "="*60)
    print("演示4: 机器学习策略 (T182)")
    print("="*60)

    # 创建ML策略
    strategy = MLStrategy(
        model_type='random_forest',
        feature_window=60,
        prediction_horizon=5,
        retrain_frequency=30,
        use_ensemble=True
    )

    # 生成大量历史数据用于训练
    data = generate_sample_data('0700.HK', 1000)

    try:
        # 初始化和训练
        strategy.initialize(data)
        print(f"\n模型训练完成")
        print(f"  模型类型: {strategy.model_type}")
        print(f"  模型准确率: {strategy.model_accuracy:.2%}")
        print(f"  特征数量: {len(strategy.feature_names)}")

        # 生成信号
        signals = strategy.generate_signals(data.tail(100))
        print(f"\n生成的ML信号数量: {len(signals)}")

        for signal in signals[:3]:
            print(f"\n信号:")
            print(f"  类型: {signal.signal_type.value}")
            print(f"  置信度: {signal.confidence:.2f}")
            print(f"  原因: {signal.reason}")

        # 获取ML摘要
        summary = strategy.get_ml_summary()
        print(f"\nML策略摘要:")
        print(f"  重新训练频率: {summary['retrain_frequency']}天")
        print(f"  使用集成: {summary['use_ensemble']}")

    except Exception as e:
        print(f"ML策略初始化跳过: {e}")

    return strategy


def demo_strategy_builder():
    """演示策略构建器"""
    print("\n" + "="*60)
    print("演示5: 策略构建器 (T183)")
    print("="*60)

    # 1. 使用预定义模板
    print("\n1. 使用预定义模板:")
    builder = StrategyBuilder(template_id='simple_ma')
    print(f"  模板: {builder.template_id}")
    print(f"  组件数量: {len(builder.components)}")

    # 显示组件
    for comp in builder.components:
        print(f"    - {comp.name} ({comp.component_class})")

    # 2. 手动构建策略
    print("\n2. 手动构建策略:")
    builder2 = StrategyBuilder()
    builder2.add_component(
        'moving_average',
        '快速MA',
        {'period': 10}
    )
    builder2.add_component(
        'moving_average',
        '慢速MA',
        {'period': 20}
    )
    builder2.add_component(
        'rsi',
        'RSI指标',
        {'period': 14}
    )

    print(f"  组件数量: {len(builder2.components)}")
    for comp in builder2.components:
        print(f"    - {comp.name} ({comp.component_class})")

    # 3. 生成代码
    print("\n3. 生成策略代码:")
    code = builder.generate_code()
    print("  代码预览:")
    print("  " + "\n  ".join(code.split('\n')[:15]))

    # 4. 导出配置
    print("\n4. 导出配置:")
    config = builder.export_config()
    print(f"  配置长度: {len(config)} 字符")

    # 5. 获取构建器摘要
    summary = builder.get_builder_summary()
    print(f"\n构建器摘要:")
    print(f"  策略名称: {summary['strategy_name']}")
    print(f"  组件数量: {summary['component_count']}")
    print(f"  可用模板: {len(summary['available_templates'])}")
    print(f"  可用组件: {len(summary['available_components'])}")

    return builder


def main():
    """主函数"""
    print("="*60)
    print("Phase 8: Enhanced Features Demo")
    print("Advanced Strategy System (T179-T183)")
    print("="*60)

    # 运行所有演示
    strategies = {}

    try:
        strategies['multi_timeframe'] = demo_multi_timeframe()
    except Exception as e:
        print(f"\n多时间框架策略演示跳过: {e}")

    try:
        strategies['portfolio'] = demo_portfolio_strategy()
    except Exception as e:
        print(f"\n投资组合策略演示跳过: {e}")

    try:
        strategies['ensemble'] = demo_ensemble_strategy()
    except Exception as e:
        print(f"\n集成策略演示跳过: {e}")

    try:
        strategies['ml'] = demo_ml_strategy()
    except Exception as e:
        print(f"\n机器学习策略演示跳过: {e}")

    try:
        strategies['builder'] = demo_strategy_builder()
    except Exception as e:
        print(f"\n策略构建器演示跳过: {e}")

    # 总结
    print("\n" + "="*60)
    print("演示完成")
    print("="*60)
    print(f"成功演示的策略数量: {len(strategies)}")
    print("\n策略列表:")
    for name, strategy in strategies.items():
        print(f"  - {name}: {strategy.strategy_name}")


if __name__ == '__main__':
    main()
