"""
简化版实时交易系统测试
"""

import asyncio
import sys
sys.path.append('.')

from paper_trading_api import PaperTradingAPI
from realtime_execution_engine import RealtimeExecutionEngine
from signal_generator import SignalManager, SignalConfig, OrderSide
from base_trading_api import Order, OrderType
from decimal import Decimal


async def test_basic_trading():
    """基础交易测试"""
    print("\n" + "="*60)
    print("Basic Trading Test")
    print("="*60)

    # 初始化模拟交易API
    print("\n1. Initializing Paper Trading API...")
    api = PaperTradingAPI({'initial_cash': 1000000})
    await api.connect()
    await api.authenticate({})
    print("   Paper Trading API connected")

    # 获取账户信息
    print("\n2. Getting account info...")
    account = await api.get_account_info()
    if account:
        print(f"   Account ID: {account.account_id}")
        print(f"   Cash: ${account.cash:,.2f}")
        print(f"   Equity: ${account.equity:,.2f}")

    # 获取市场数据
    print("\n3. Getting market data...")
    market_data = await api.get_market_data('0700.HK')
    if market_data:
        print(f"   0700.HK Price: ${market_data.last_price:.2f}")

    # 下单
    print("\n4. Placing test order...")
    buy_order = Order(
        order_id="test_buy_001",
        symbol="0700.HK",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal('1000')
    )

    order_id = await api.place_order(buy_order)
    if order_id:
        print(f"   Order submitted: {order_id}")
        await asyncio.sleep(2)

        # 检查订单状态
        status = await api.get_order_status(order_id)
        print(f"   Order status: {status}")

    # 查看持仓
    print("\n5. Getting positions...")
    positions = await api.get_positions()
    for pos in positions:
        print(f"   {pos.symbol}: Qty={pos.quantity}, PnL=${pos.unrealized_pnl:.2f}")

    # 交易摘要
    print("\n6. Trading summary...")
    summary = await api.get_trading_summary()
    print(f"   Total trades: {summary.get('filled_orders', 0)}")

    await api.disconnect()
    print("\nBasic Trading Test Complete!")


async def test_signal_generation():
    """信号生成测试"""
    print("\n" + "="*60)
    print("Signal Generation Test")
    print("="*60)

    # 初始化信号管理器
    print("\n1. Initializing signal manager...")
    signal_manager = SignalManager()
    print("   Signal manager ready")

    # 添加信号配置
    print("\n2. Adding signal configurations...")
    configs = [
        SignalConfig('0700.HK', 'rsi', {'period': 14}),
        SignalConfig('0700.HK', 'macd', {'fast': 12, 'slow': 26}),
        SignalConfig('0388.HK', 'ma_crossover', {'short_period': 20, 'long_period': 50})
    ]

    for config in configs:
        await signal_manager.add_signal_config(config)
    print(f"   Added {len(configs)} configurations")

    # 扫描信号
    print("\n3. Scanning for signals...")
    signals = await signal_manager.scan_signals()

    if signals:
        print(f"   Found {len(signals)} signals:")
        for signal in signals:
            print(f"   - {signal.symbol}: {signal.side.value}")
            print(f"     Confidence: {signal.metadata.get('confidence', 0):.2f}")
    else:
        print("   No signals found (data insufficient - expected)")

    # 信号统计
    print("\n4. Signal statistics...")
    stats = await signal_manager.get_stats()
    print(f"   Total signals: {stats['stats']['total_signals']}")


async def test_full_workflow():
    """完整交易流程测试"""
    print("\n" + "="*60)
    print("Full Trading Workflow Test")
    print("="*60)

    # 初始化系统
    print("\n1. Initializing trading system...")
    api = PaperTradingAPI({'initial_cash': 1000000})
    await api.connect()
    await api.authenticate({})

    engine = RealtimeExecutionEngine({
        'primary_api': 'paper_trading',
        'risk': {
            'max_position_size': 500000,
            'max_daily_loss': 50000,
            'max_order_size': 100000,
            'min_cash_reserve': 10000
        }
    })

    await engine.add_trading_api('paper_trading', api)
    await engine.start()
    print("   Trading system started")

    # 信号管理器
    signal_manager = SignalManager()
    await signal_manager.add_signal_config(
        SignalConfig('0700.HK', 'rsi', {'period': 14, 'oversold': 30, 'overbought': 70})
    )
    print("   Signal manager ready")

    # 执行交易
    print("\n2. Executing trades...")
    trades = 0

    for i in range(3):
        print(f"\n   Cycle {i+1}/3:")

        # 扫描信号
        signals = await signal_manager.scan_signals()

        if signals:
            for signal in signals:
                order_id = await engine.execute_signal(signal)
                if order_id:
                    trades += 1
                    print(f"     Signal executed: {signal.symbol} {signal.side.value}")

                    await asyncio.sleep(1)

                    status = await engine.get_order_status(order_id)
                    print(f"     Status: {status}")

        else:
            print("     No signals found")

        # 投资组合摘要
        portfolio = await engine.get_portfolio_summary()
        if portfolio:
            account = portfolio.get('account', {})
            print(f"     Cash: ${account.get('cash', 0):,.2f}")
            print(f"     Equity: ${account.get('equity', 0):,.2f}")

        await asyncio.sleep(1)

    # 性能指标
    print("\n3. Performance metrics...")
    metrics = await engine.get_performance_metrics()
    print(f"   Total orders: {metrics.get('total_orders', 0)}")
    print(f"   Filled orders: {metrics.get('filled_orders', 0)}")
    print(f"   Total commission: ${metrics.get('total_commission', 0):.2f}")

    # 清理
    await engine.stop()
    await api.disconnect()

    print(f"\nFull workflow complete! Executed {trades} trades.")


async def test_risk_management():
    """风险管理测试"""
    print("\n" + "="*60)
    print("Risk Management Test")
    print("="*60)

    # 初始化
    api = PaperTradingAPI({'initial_cash': 100000})
    await api.connect()
    await api.authenticate({})

    engine = RealtimeExecutionEngine({
        'primary_api': 'paper_trading',
        'risk': {
            'max_position_size': 50000,
            'max_daily_loss': 10000,
            'max_order_size': 20000,
            'min_cash_reserve': 10000
        }
    })

    await engine.add_trading_api('paper_trading', api)
    await engine.start()

    print("\n1. Testing order size limit...")
    from realtime_execution_engine import TradeSignal, ExecutionStrategy

    large_signal = TradeSignal(
        signal_id='test_large',
        symbol='0700.HK',
        side=OrderSide.BUY,
        quantity=Decimal('30000'),
        strategy=ExecutionStrategy.IMMEDIATE
    )

    order_id = await engine.execute_signal(large_signal)
    if not order_id:
        print("   Large order correctly blocked")
    else:
        print("   Large order not blocked (issue)")

    print("\n2. Testing normal order...")
    normal_signal = TradeSignal(
        signal_id='test_normal',
        symbol='0700.HK',
        side=OrderSide.BUY,
        quantity=Decimal('1000'),
        strategy=ExecutionStrategy.IMMEDIATE
    )

    order_id = await engine.execute_signal(normal_signal)
    if order_id:
        print(f"   Normal order executed: {order_id}")
    else:
        print("   Normal order failed (issue)")

    await engine.stop()
    await api.disconnect()

    print("\nRisk management test complete!")


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("Realtime Trading System Test Suite")
    print("="*60)

    try:
        await test_basic_trading()
        await test_signal_generation()
        await test_risk_management()
        await test_full_workflow()

        print("\n" + "="*60)
        print("All Tests Complete!")
        print("="*60)

    except Exception as e:
        print(f"\nTest error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
