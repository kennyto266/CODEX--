"""
实时交易执行系统测试脚本

演示完整的交易流程：
1. 初始化交易引擎
2. 添加交易信号配置
3. 生成交易信号
4. 执行交易
5. 监控订单状态
6. 查看投资组合
"""

import asyncio
import logging
import json
import sys
from datetime import datetime
from decimal import Decimal

# 添加路径以支持绝对导入
sys.path.append('.')

from paper_trading_api import PaperTradingAPI
from realtime_execution_engine import RealtimeExecutionEngine
from signal_generator import SignalManager, SignalConfig, OrderSide


async def test_basic_trading():
    """基础交易测试"""
    print("\n" + "="*80)
    print("基础交易功能测试")
    print("="*80)

    # 1. 初始化模拟交易API
    print("\n1. 初始化模拟交易API...")
    api_config = {
        'initial_cash': 1000000,  # 100万初始资金
        'execution_delay': 0.5
    }
    api = PaperTradingAPI(api_config)

    # 连接并认证
    await api.connect()
    await api.authenticate({})
    print("   ✓ 模拟交易API已连接")

    # 2. 获取初始账户信息
    print("\n2. 获取账户信息...")
    account = await api.get_account_info()
    if account:
        print(f"   账户ID: {account.account_id}")
        print(f"   账户类型: {account.account_type}")
        print(f"   现金余额: ${account.cash:,.2f}")
        print(f"   购买力: ${account.buying_power:,.2f}")
        print(f"   权益: ${account.equity:,.2f}")

    # 3. 获取市场数据
    print("\n3. 获取市场数据...")
    for symbol in ['0700.HK', '0388.HK']:
        market_data = await api.get_market_data(symbol)
        if market_data:
            print(f"   {symbol}:")
            print(f"     最新价: ${market_data.last_price:.2f}")
            print(f"     买卖价差: ${(market_data.ask_price - market_data.bid_price):.2f}")
            print(f"     成交量: {market_data.volume:,}")

    # 4. 下测试订单
    print("\n4. 下测试订单...")

    # 买入订单
    from base_trading_api import Order, OrderType, OrderStatus
    from decimal import Decimal

    buy_order = Order(
        order_id="test_buy_001",
        symbol="0700.HK",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal('1000')
    )

    order_id = await api.place_order(buy_order)
    if order_id:
        print(f"   ✓ 买入订单已提交: {order_id}")
        print(f"     股票: {buy_order.symbol}")
        print(f"     数量: {buy_order.quantity}")
        print(f"     类型: 市价单")

        # 等待订单执行
        await asyncio.sleep(2)

        # 检查订单状态
        status = await api.get_order_status(order_id)
        print(f"   订单状态: {status}")

    # 5. 查看持仓
    print("\n5. 查看持仓...")
    positions = await api.get_positions()
    for pos in positions:
        print(f"   {pos.symbol}:")
        print(f"     数量: {pos.quantity}")
        print(f"     平均成本: ${pos.average_price:.2f}")
        print(f"     当前价格: ${pos.current_price:.2f}")
        print(f"     市值: ${pos.market_value:.2f}")
        print(f"     未实现损益: ${pos.unrealized_pnl:.2f}")

    # 6. 卖出订单
    if positions:
        print("\n6. 执行卖出订单...")
        sell_order = Order(
            order_id="test_sell_001",
            symbol="0700.HK",
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=Decimal('500')
        )

        order_id = await api.place_order(sell_order)
        if order_id:
            print(f"   ✓ 卖出订单已提交: {order_id}")
            await asyncio.sleep(2)

    # 7. 获取最终账户信息
    print("\n7. 最终账户信息...")
    account = await api.get_account_info()
    if account:
        print(f"   现金余额: ${account.cash:,.2f}")
        print(f"   权益: ${account.equity:,.2f}")

    # 8. 获取交易摘要
    print("\n8. 交易摘要...")
    summary = await api.get_trading_summary()
    print(json.dumps(summary, indent=2, default=str))

    # 清理
    await api.disconnect()
    print("\n✓ 基础交易测试完成")


async def test_signal_generation():
    """信号生成测试"""
    print("\n" + "="*80)
    print("交易信号生成测试")
    print("="*80)

    # 1. 初始化信号管理器
    print("\n1. 初始化信号管理器...")
    signal_manager = SignalManager()
    print("   ✓ 信号管理器已启动")

    # 2. 添加信号配置
    print("\n2. 添加信号配置...")

    # RSI策略配置
    rsi_config = SignalConfig(
        symbol='0700.HK',
        strategy='rsi',
        parameters={'period': 14, 'oversold': 30, 'overbought': 70}
    )
    await signal_manager.add_signal_config(rsi_config)
    print(f"   ✓ 添加RSI策略: {rsi_config.symbol}")

    # MACD策略配置
    macd_config = SignalConfig(
        symbol='0700.HK',
        strategy='macd',
        parameters={'fast': 12, 'slow': 26, 'signal': 9}
    )
    await signal_manager.add_signal_config(macd_config)
    print(f"   ✓ 添加MACD策略: {macd_config.symbol}")

    # MA交叉策略配置
    ma_config = SignalConfig(
        symbol='0388.HK',
        strategy='ma_crossover',
        parameters={'short_period': 20, 'long_period': 50}
    )
    await signal_manager.add_signal_config(ma_config)
    print(f"   ✓ 添加MA交叉策略: {ma_config.symbol}")

    # 3. 扫描信号
    print("\n3. 扫描交易信号...")
    signals = await signal_manager.scan_signals()

    if signals:
        print(f"   发现 {len(signals)} 个信号:")
        for signal in signals:
            print(f"   - {signal.symbol}: {signal.side.value}")
            print(f"     数量: {signal.quantity}")
            print(f"     置信度: {signal.metadata.get('confidence', 0):.2f}")
            print(f"     原因: {signal.metadata.get('reason', '')}")
            print()
    else:
        print("   未发现交易信号（正常，可能是数据不足）")

    # 4. 查看信号历史
    print("\n4. 信号历史...")
    history = await signal_manager.get_signal_history()
    print(f"   总计信号数: {len(history)}")

    # 5. 查看统计
    print("\n5. 信号统计...")
    stats = await signal_manager.get_stats()
    print(json.dumps(stats, indent=2, default=str))


async def test_full_trading_workflow():
    """完整交易流程测试"""
    print("\n" + "="*80)
    print("完整交易流程测试")
    print("="*80)

    # 1. 初始化系统
    print("\n1. 初始化交易系统...")

    # 模拟交易API
    api_config = {
        'initial_cash': 1000000,
        'execution_delay': 0.5
    }
    api = PaperTradingAPI(api_config)
    await api.connect()
    await api.authenticate({})

    # 执行引擎
    engine_config = {
        'primary_api': 'paper_trading',
        'risk': {
            'max_position_size': 500000,
            'max_daily_loss': 50000,
            'max_order_size': 100000,
            'min_cash_reserve': 10000
        }
    }
    engine = RealtimeExecutionEngine(engine_config)
    await engine.add_trading_api('paper_trading', api)
    await engine.start()
    print("   ✓ 交易系统已启动")

    # 信号管理器
    signal_manager = SignalManager()
    print("   ✓ 信号管理器已启动")

    # 2. 添加信号配置
    print("\n2. 添加信号配置...")
    configs = [
        SignalConfig('0700.HK', 'rsi', {'period': 14, 'oversold': 30, 'overbought': 70}),
        SignalConfig('0700.HK', 'macd', {'fast': 12, 'slow': 26, 'signal': 9}),
        SignalConfig('0388.HK', 'ma_crossover', {'short_period': 20, 'long_period': 50})
    ]

    for config in configs:
        await signal_manager.add_signal_config(config)
    print(f"   ✓ 已添加 {len(configs)} 个信号配置")

    # 3. 主循环：生成信号并执行交易
    print("\n3. 开始交易循环...")

    trade_count = 0
    for i in range(3):  # 运行3个周期
        print(f"\n   周期 {i+1}/3:")

        # 扫描信号
        signals = await signal_manager.scan_signals()

        if signals:
            print(f"   发现 {len(signals)} 个信号，执行交易...")

            for signal in signals:
                # 执行信号
                order_id = await engine.execute_signal(signal)

                if order_id:
                    trade_count += 1
                    print(f"     ✓ 信号已执行: {signal.symbol} {signal.side.value} -> 订单 {order_id}")

                    # 等待订单执行
                    await asyncio.sleep(1)

                    # 查看订单状态
                    status = await engine.get_order_status(order_id)
                    if status:
                        print(f"       状态: {status}")

                else:
                    print(f"     ✗ 信号执行失败: {signal.symbol} {signal.side.value}")
        else:
            print("   未发现信号")

        # 显示投资组合摘要
        portfolio = await engine.get_portfolio_summary()
        if portfolio:
            account = portfolio.get('account', {})
            positions = portfolio.get('positions', [])
            print(f"   当前现金: ${account.get('cash', 0):,.2f}")
            print(f"   当前权益: ${account.get('equity', 0):,.2f}")
            print(f"   持仓数量: {len(positions)}")

        # 等待下一周期
        await asyncio.sleep(2)

    # 4. 查看性能指标
    print("\n4. 性能指标...")
    metrics = await engine.get_performance_metrics()
    print(json.dumps(metrics, indent=2, default=str))

    # 5. 获取交易摘要
    print("\n5. 最终交易摘要...")
    summary = await api.get_trading_summary()
    print(json.dumps(summary, indent=2, default=str))

    # 清理
    await engine.stop()
    await api.disconnect()

    print(f"\n✓ 完整交易流程测试完成，共执行 {trade_count} 笔交易")


async def test_risk_management():
    """风险管理测试"""
    print("\n" + "="*80)
    print("风险管理测试")
    print("="*80)

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

    print("\n1. 测试订单大小限制...")

    # 测试大额订单
    from realtime_execution_engine import TradeSignal, ExecutionStrategy, OrderSide

    large_signal = TradeSignal(
        signal_id='test_large',
        symbol='0700.HK',
        side=OrderSide.BUY,
        quantity=Decimal('30000'),  # 超过最大订单大小
        strategy=ExecutionStrategy.IMMEDIATE
    )

    order_id = await engine.execute_signal(large_signal)
    if not order_id:
        print("   ✓ 大额订单被正确拦截")
    else:
        print("   ✗ 大额订单未被拦截")

    print("\n2. 测试现金限制...")

    # 测试现金不足
    insufficient_signal = TradeSignal(
        signal_id='test_insufficient',
        symbol='0700.HK',
        side=OrderSide.BUY,
        quantity=Decimal('1000000'),  # 超过现金余额
        strategy=ExecutionStrategy.IMMEDIATE
    )

    order_id = await engine.execute_signal(insufficient_signal)
    if not order_id:
        print("   ✓ 现金不足订单被正确拦截")
    else:
        print("   ✗ 现金不足订单未被拦截")

    print("\n3. 测试正常订单...")

    # 测试正常订单
    normal_signal = TradeSignal(
        signal_id='test_normal',
        symbol='0700.HK',
        side=OrderSide.BUY,
        quantity=Decimal('1000'),  # 正常大小
        strategy=ExecutionStrategy.IMMEDIATE
    )

    order_id = await engine.execute_signal(normal_signal)
    if order_id:
        print(f"   ✓ 正常订单已执行: {order_id}")
    else:
        print("   ✗ 正常订单执行失败")

    # 清理
    await engine.stop()
    await api.disconnect()

    print("\n✓ 风险管理测试完成")


async def main():
    """主测试函数"""
    print("="*80)
    print("实时交易执行系统测试")
    print("="*80)

    try:
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # 运行测试
        await test_basic_trading()
        await test_signal_generation()
        await test_risk_management()
        await test_full_trading_workflow()

        print("\n" + "="*80)
        print("所有测试完成！")
        print("="*80)

    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
