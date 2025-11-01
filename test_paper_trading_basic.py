"""
快速验证模拟交易系统代码

验证导入和基本功能，不依赖富途连接
"""

import sys
import asyncio
from decimal import Decimal
from datetime import datetime

# 配置日志
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_basic")


def test_imports():
    """测试模块导入"""
    logger.info("=" * 60)
    logger.info("测试 1: 导入模块")
    logger.info("=" * 60)

    try:
        # 测试基础类
        from src.trading.base_trading_api import Order, OrderSide, OrderType, OrderStatus, Position, AccountInfo
        logger.info("✅ 导入 base_trading_api 成功")

        # 测试 FutuTradingAPI
        from src.trading.futu_trading_api import FutuTradingAPI, create_futu_trading_api
        logger.info("✅ 导入 futu_trading_api 成功")

        # 测试 TradeSignal
        from src.trading.realtime_execution_engine import TradeSignal, ExecutionStrategy, OrderSide
        logger.info("✅ 导入 realtime_execution_engine 成功")

        # 测试 PaperTradingEngine
        from src.trading.paper_trading_engine import PaperTradingEngine
        logger.info("✅ 导入 paper_trading_engine 成功")

        # 测试 FutuPaperTradingController
        from src.trading.futu_paper_trading_controller import FutuPaperTradingController, create_paper_trading_controller
        logger.info("✅ 导入 futu_paper_trading_controller 成功")

        logger.info("\n✅ 所有模块导入成功")
        return True

    except ImportError as e:
        logger.error(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ 未知错误: {e}")
        return False


def test_data_structures():
    """测试数据结构"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 2: 数据结构")
    logger.info("=" * 60)

    try:
        from src.trading.base_trading_api import Order, OrderSide, OrderType
        from src.trading.realtime_execution_engine import TradeSignal, ExecutionStrategy

        # 创建测试订单
        order = Order(
            order_id="TEST_001",
            symbol="00700.HK",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal('1000'),
            price=Decimal('350.0')
        )
        logger.info(f"✅ 订单创建成功: {order.order_id}")

        # 创建交易信号
        signal = TradeSignal(
            signal_id="SIGNAL_001",
            symbol="00700.HK",
            side=OrderSide.BUY,
            quantity=Decimal('1000'),
            strategy=ExecutionStrategy.IMMEDIATE,
            price=Decimal('350.0')
        )
        logger.info(f"✅ 交易信号创建成功: {signal.signal_id}")

        logger.info("\n✅ 数据结构测试通过")
        return True

    except Exception as e:
        logger.error(f"❌ 数据结构测试失败: {e}", exc_info=True)
        return False


async def test_paper_engine():
    """测试模拟交易引擎（简化版）"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 3: 模拟交易引擎")
    logger.info("=" * 60)

    try:
        from src.trading.paper_trading_engine import PaperTradingEngine
        from src.trading.futu_trading_api import create_futu_trading_api
        from src.trading.realtime_execution_engine import TradeSignal, ExecutionStrategy, OrderSide

        # 创建模拟富途API（不连接）
        futu_api = create_futu_trading_api(
            host='127.0.0.1',
            port=11111,
            trade_password='123456',
            market='HK'
        )

        # 创建引擎
        engine = PaperTradingEngine(
            futu_api=futu_api,
            initial_balance=Decimal('1000000'),
            commission_rate=Decimal('0.001'),
            min_commission=Decimal('10')
        )

        logger.info("✅ PaperTradingEngine 创建成功")

        # 初始化引擎
        success = await engine.initialize()
        if success:
            logger.info("✅ 引擎初始化成功")

            # 获取账户信息
            account = await engine.get_account_info()
            if account:
                logger.info(f"✅ 账户信息: 余额={account.cash}")

            # 模拟创建信号（不执行）
            signal = TradeSignal(
                signal_id="TEST_SIGNAL",
                symbol="00700.HK",
                side=OrderSide.BUY,
                quantity=Decimal('1000'),
                strategy=ExecutionStrategy.IMMEDIATE,
                price=Decimal('350.0')
            )
            logger.info(f"✅ 交易信号创建: {signal.symbol}")

            # 获取性能指标
            metrics = await engine.get_performance_metrics()
            logger.info(f"✅ 性能指标获取成功: {len(metrics)} 项")

            await engine.cleanup()
            logger.info("✅ 引擎清理成功")

        logger.info("\n✅ 模拟交易引擎测试通过")
        return True

    except Exception as e:
        logger.error(f"❌ 引擎测试失败: {e}", exc_info=True)
        return False


async def test_controller():
    """测试控制器（简化版）"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 4: 控制器")
    logger.info("=" * 60)

    try:
        from src.trading.futu_paper_trading_controller import FutuPaperTradingController

        # 创建配置
        config = {
            'futu': {
                'host': '127.0.0.1',
                'port': 11111,
                'trade_password': '123456',
                'market': 'HK'
            },
            'auth': {
                'trade_password': '123456'
            },
            'trading': {
                'initial_balance': Decimal('1000000'),
                'max_position_size': Decimal('100000'),
                'max_daily_trades': 100
            }
        }

        # 创建控制器（不初始化）
        controller = FutuPaperTradingController(config)
        logger.info("✅ FutuPaperTradingController 创建成功")

        # 获取状态（未初始化）
        status = await controller.get_status()
        logger.info(f"✅ 状态获取成功: initialized={status['initialized']}")

        logger.info("\n✅ 控制器测试通过")
        return True

    except Exception as e:
        logger.error(f"❌ 控制器测试失败: {e}", exc_info=True)
        return False


async def main():
    """主函数"""
    logger.info("\n" + "=" * 80)
    logger.info("富途模拟交易系统 - 快速验证测试")
    logger.info("=" * 80 + "\n")

    tests = [
        ("模块导入", test_imports),
        ("数据结构", test_data_structures),
        ("模拟交易引擎", test_paper_engine),
        ("控制器", test_controller),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()

            if result:
                passed += 1
                logger.info(f"\n✅ {test_name} - 通过")
            else:
                failed += 1
                logger.error(f"\n❌ {test_name} - 失败")

        except Exception as e:
            failed += 1
            logger.error(f"\n❌ {test_name} - 异常: {e}", exc_info=True)

    # 总结
    logger.info("\n" + "=" * 80)
    logger.info("测试总结")
    logger.info("=" * 80)
    logger.info(f"总测试数: {len(tests)}")
    logger.info(f"通过: {passed}")
    logger.info(f"失败: {failed}")
    logger.info(f"成功率: {passed/len(tests)*100:.1f}%")

    if failed == 0:
        logger.info("\n🎉 所有测试通过！模拟交易系统核心代码验证成功")
    else:
        logger.error(f"\n⚠️  有 {failed} 个测试失败，请检查代码")

    logger.info("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
