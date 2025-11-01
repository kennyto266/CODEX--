"""
模拟交易系统测试脚本

测试 FutuPaperTradingController 和 PaperTradingEngine 的功能
"""

import asyncio
import logging
from decimal import Decimal
from datetime import datetime

from futu_paper_trading_controller import create_paper_trading_controller
from paper_trading_engine import PaperTradingEngine
from realtime_execution_engine import TradeSignal, ExecutionStrategy, OrderSide

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("test_paper_trading")


async def test_paper_trading_controller():
    """测试模拟交易控制器"""
    logger.info("=" * 80)
    logger.info("开始测试富途模拟交易控制器")
    logger.info("=" * 80)

    # 创建配置
    config = {
        'futu': {
            'host': '127.0.0.1',
            'port': 11111,
            'trade_password': '123456',  # DEMO环境密码
            'market': 'HK'
        },
        'auth': {
            'trade_password': '123456'
        },
        'trading': {
            'initial_balance': Decimal('1000000'),  # 100万港币
            'max_position_size': Decimal('100000'),
            'max_daily_trades': 100,
            'commission_rate': Decimal('0.001'),
            'min_commission': Decimal('10')
        }
    }

    # 创建控制器
    controller = create_paper_trading_controller(
        futu_host='127.0.0.1',
        futu_port=11111,
        trade_password='123456',
        market='HK',
        initial_balance=Decimal('1000000')
    )

    try:
        # 测试1: 初始化
        logger.info("\n" + "=" * 60)
        logger.info("测试 1: 初始化")
        logger.info("=" * 60)

        success = await controller.initialize()
        if success:
            logger.info("✅ 初始化成功")
        else:
            logger.error("❌ 初始化失败")
            return

        # 测试2: 获取状态
        logger.info("\n" + "=" * 60)
        logger.info("测试 2: 获取状态")
        logger.info("=" * 60)

        status = await controller.get_status()
        logger.info(f"控制器状态: {status['initialized']}")
        logger.info(f"账户余额: {status['account']['cash'] if status['account'] else 'N/A'}")

        # 测试3: 启动交易
        logger.info("\n" + "=" * 60)
        logger.info("测试 3: 启动交易")
        logger.info("=" * 60)

        await controller.start_trading()
        logger.info("✅ 交易已启动")

        # 测试4: 执行交易信号
        logger.info("\n" + "=" * 60)
        logger.info("测试 4: 执行交易信号")
        logger.info("=" * 60)

        # 创建买入信号
        buy_signal = TradeSignal(
            signal_id=f"BUY_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            symbol="00700.HK",
            side=OrderSide.BUY,
            quantity=Decimal('1000'),
            strategy=ExecutionStrategy.IMMEDIATE,
            price=Decimal('350.0')  # 腾讯350港币
        )

        logger.info(f"发送买入信号: {buy_signal.symbol} {buy_signal.side} {buy_signal.quantity}")
        result = await controller.execute_signal(buy_signal)
        logger.info(f"执行结果: {result}")

        # 测试5: 创建卖出信号
        logger.info("\n" + "=" * 60)
        logger.info("测试 5: 执行卖出信号")
        logger.info("=" * 60)

        sell_signal = TradeSignal(
            signal_id=f"SELL_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            symbol="00700.HK",
            side=OrderSide.SELL,
            quantity=Decimal('500'),
            strategy=ExecutionStrategy.IMMEDIATE,
            price=Decimal('360.0')
        )

        logger.info(f"发送卖出信号: {sell_signal.symbol} {sell_signal.side} {sell_signal.quantity}")
        result = await controller.execute_signal(sell_signal)
        logger.info(f"执行结果: {result}")

        # 测试6: 获取持仓
        logger.info("\n" + "=" * 60)
        logger.info("测试 6: 获取持仓")
        logger.info("=" * 60)

        positions = await controller.get_positions()
        logger.info(f"当前持仓数量: {len(positions)}")
        for pos in positions:
            logger.info(f"  - {pos.symbol}: {pos.quantity} 股, 成本: {pos.average_price}")

        # 测试7: 获取订单
        logger.info("\n" + "=" * 60)
        logger.info("测试 7: 获取订单")
        logger.info("=" * 60)

        orders = await controller.get_orders()
        logger.info(f"订单数量: {len(orders)}")
        for order in orders:
            logger.info(f"  - {order.order_id}: {order.symbol} {order.side} {order.status}")

        # 测试8: 获取性能指标
        logger.info("\n" + "=" * 60)
        logger.info("测试 8: 获取性能指标")
        logger.info("=" * 60)

        metrics = await controller.get_performance_metrics()
        logger.info(f"性能指标: {metrics}")

        # 测试9: 紧急停止
        logger.info("\n" + "=" * 60)
        logger.info("测试 9: 紧急停止")
        logger.info("=" * 60)

        await controller.emergency_stop()
        logger.info("✅ 紧急停止执行成功")

        # 测试10: 解锁交易
        logger.info("\n" + "=" * 60)
        logger.info("测试 10: 解锁交易")
        logger.info("=" * 60)

        await controller.unlock_trading()
        logger.info("✅ 交易解锁成功")

        # 最终状态
        logger.info("\n" + "=" * 60)
        logger.info("最终状态")
        logger.info("=" * 60)

        final_status = await controller.get_status()
        logger.info(f"账户余额: {final_status['account']['cash'] if final_status['account'] else 'N/A'}")
        logger.info(f"总交易次数: {final_status['stats']['total_trades']}")

        logger.info("\n" + "=" * 80)
        logger.info("✅ 所有测试完成")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)

    finally:
        # 清理
        await controller.cleanup()
        logger.info("✅ 资源清理完成")


async def test_paper_trading_engine_only():
    """仅测试模拟交易引擎（不需要富途连接）"""
    logger.info("=" * 80)
    logger.info("开始测试模拟交易引擎（独立模式）")
    logger.info("=" * 80)

    try:
        # 创建引擎（不连接富途）
        from futu_trading_api import create_futu_trading_api

        futu_api = create_futu_trading_api(
            host='127.0.0.1',
            port=11111,
            trade_password='123456',
            market='HK'
        )

        engine = PaperTradingEngine(
            futu_api=futu_api,
            initial_balance=Decimal('1000000'),
            commission_rate=Decimal('0.001'),
            min_commission=Decimal('10')
        )

        await engine.initialize()

        logger.info("✅ 引擎初始化成功")

        # 获取账户信息
        account = await engine.get_account_info()
        logger.info(f"账户信息: {account.dict()}")

        # 创建并执行信号（不依赖富途API）
        from realtime_execution_engine import TradeSignal, ExecutionStrategy, OrderSide

        signal = TradeSignal(
            signal_id="TEST_001",
            symbol="00700.HK",
            side=OrderSide.BUY,
            quantity=Decimal('1000'),
            strategy=ExecutionStrategy.IMMEDIATE,
            price=Decimal('350.0')
        )

        result = await engine.execute_signal(signal)
        logger.info(f"执行结果: {result}")

        # 获取持仓
        positions = await engine.get_positions()
        logger.info(f"持仓数量: {len(positions)}")

        # 获取性能指标
        metrics = await engine.get_performance_metrics()
        logger.info(f"性能指标: {metrics}")

        await engine.cleanup()

        logger.info("\n" + "=" * 80)
        logger.info("✅ 引擎测试完成")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)


async def main():
    """主函数"""
    logger.info("富途模拟交易系统测试")
    logger.info("请确保富途 OpenD 客户端正在运行并连接到 DEMO 环境")
    logger.info("")

    # 选择测试模式
    test_mode = input("请选择测试模式:\n1. 完整测试（需要富途连接）\n2. 引擎测试（独立模式）\n请输入 (1/2): ").strip()

    if test_mode == "1":
        await test_paper_trading_controller()
    else:
        await test_paper_trading_engine_only()


if __name__ == "__main__":
    asyncio.run(main())
