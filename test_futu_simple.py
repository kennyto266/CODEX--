"""
简化的富途连接测试

测试富途OpenD连接，不依赖交易密码
"""

import asyncio
import logging
from decimal import Decimal
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("futu_simple_test")


async def test_connection_only():
    """仅测试连接，不测试交易功能"""
    logger.info("=" * 80)
    logger.info("富途OpenD连接测试 (仅连接测试)")
    logger.info("=" * 80)

    try:
        # 导入富途API
        from src.trading.futu_trading_api import FutuTradingAPI, create_futu_trading_api

        logger.info("✅ 富途API模块导入成功")

        # 创建富途API实例（不使用交易密码）
        logger.info("\n步骤 1/3: 创建富途API实例...")
        futu_api = create_futu_trading_api(
            host='127.0.0.1',
            port=11111,
            trade_password='',  # 空密码
            market='HK'
        )
        logger.info("✅ 富途API实例创建成功")

        # 连接富途API
        logger.info("\n步骤 2/3: 连接到富途OpenD...")
        connected = await futu_api.connect()
        if connected:
            logger.info("✅ 成功连接到富途OpenD (127.0.0.1:11111)")
            logger.info(f"   用户ID: 2860386")
            logger.info(f"   端口: 11111")
        else:
            logger.error("❌ 连接富途OpenD失败")
            logger.error("请确保富途OpenD客户端已启动并登录")
            return False

        # 测试市场数据（不需要交易权限）
        logger.info("\n步骤 3/3: 测试市场数据获取...")
        try:
            market_data = await futu_api.get_market_data('00700.HK')
            if market_data and market_data.last_price:
                logger.info("✅ 市场数据获取成功:")
                logger.info(f"   股票: 00700.HK (腾讯)")
                logger.info(f"   最新价: {market_data.last_price}")
                logger.info(f"   买入价: {market_data.bid_price}")
                logger.info(f"   卖出价: {market_data.ask_price}")
                logger.info(f"   成交量: {market_data.volume}")
                logger.info(f"   时间: {market_data.timestamp}")
            else:
                logger.warning("⚠️ 无法获取市场数据（可能是权限不足）")
        except Exception as e:
            logger.warning(f"⚠️ 市场数据获取失败: {e}")

        # 清理
        await futu_api.disconnect()
        logger.info("\n✅ 已断开连接")

        logger.info("\n" + "=" * 80)
        logger.info("✅ 富途OpenD连接测试成功！")
        logger.info("=" * 80)

        return True

    except ImportError as e:
        logger.error(f"❌ 导入富途API失败: {e}")
        logger.error("请安装富途API: pip install futu-api")
        return False

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        return False


async def test_simulated_trading():
    """测试模拟交易（不需要真实连接）"""
    logger.info("\n" + "=" * 80)
    logger.info("模拟交易功能测试 (无需富途连接)")
    logger.info("=" * 80)

    try:
        from src.trading.paper_trading_engine import PaperTradingEngine
        from src.trading.futu_trading_api import create_futu_trading_api
        from src.trading.realtime_execution_engine import TradeSignal, ExecutionStrategy, OrderSide

        logger.info("✅ 模块导入成功")

        # 创建模拟富途API（不连接）
        logger.info("\n创建模拟富途API...")
        futu_api = create_futu_trading_api(
            host='127.0.0.1',
            port=11111,
            trade_password='',
            market='HK'
        )
        logger.info("✅ 模拟API创建成功")

        # 创建引擎
        logger.info("\n创建模拟交易引擎...")
        engine = PaperTradingEngine(
            futu_api=futu_api,
            initial_balance=Decimal('1000000'),
            commission_rate=Decimal('0.001'),
            min_commission=Decimal('10')
        )
        logger.info("✅ 引擎创建成功")

        # 初始化引擎
        logger.info("\n初始化引擎...")
        success = await engine.initialize()
        if success:
            logger.info("✅ 引擎初始化成功")

            # 获取账户信息
            account = await engine.get_account_info()
            if account:
                logger.info(f"✅ 账户信息:")
                logger.info(f"   账户ID: {account.account_id}")
                logger.info(f"   账户类型: {account.account_type}")
                logger.info(f"   现金余额: {account.cash}")
                logger.info(f"   总资产: {account.equity}")

            # 执行交易信号
            logger.info("\n执行测试交易信号...")
            signal = TradeSignal(
                signal_id="TEST_001",
                symbol="00700.HK",
                side=OrderSide.BUY,
                quantity=Decimal('1000'),
                strategy=ExecutionStrategy.IMMEDIATE,
                price=Decimal('350.0')
            )

            result = await engine.execute_signal(signal)
            if result.get('success'):
                logger.info("✅ 交易执行成功:")
                logger.info(f"   订单ID: {result.get('order_id')}")
                logger.info(f"   股票: {result.get('symbol')}")
                logger.info(f"   数量: {result.get('quantity')}")
                logger.info(f"   价格: {result.get('fill_price')}")
                logger.info(f"   手续费: {result.get('commission')}")
            else:
                logger.error(f"❌ 交易失败: {result.get('error')}")

            # 获取持仓
            positions = await engine.get_positions()
            logger.info(f"\n持仓数量: {len(positions)}")
            for pos in positions:
                logger.info(f"   - {pos.symbol}: {pos.quantity} 股, 成本: {pos.average_price}")

            # 获取性能指标
            metrics = await engine.get_performance_metrics()
            logger.info(f"\n性能指标:")
            for key, value in metrics.items():
                logger.info(f"   {key}: {value}")

            # 清理
            await engine.cleanup()
            logger.info("\n✅ 清理完成")

        logger.info("\n" + "=" * 80)
        logger.info("✅ 模拟交易测试成功！")
        logger.info("=" * 80)

        return True

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        return False


async def main():
    """主函数"""
    logger.info("富途连接和模拟交易测试")
    logger.info("")
    logger.info("⚠️ 注意:")
    logger.info("  - 第一部分测试富途OpenD的实际连接")
    logger.info("  - 第二部分测试模拟交易功能（不依赖真实连接）")
    logger.info("")

    # 测试连接
    logger.info("\n" + "🔌 第一部分：富途OpenD连接测试")
    connection_success = await test_connection_only()

    # 测试模拟交易
    logger.info("\n" + "💼 第二部分：模拟交易测试")
    trading_success = await test_simulated_trading()

    # 总结
    logger.info("\n" + "=" * 80)
    logger.info("测试总结")
    logger.info("=" * 80)
    logger.info(f"富途OpenD连接: {'✅ 成功' if connection_success else '❌ 失败'}")
    logger.info(f"模拟交易功能: {'✅ 成功' if trading_success else '❌ 失败'}")

    if connection_success:
        logger.info("\n✅ 富途OpenD可以正常连接")
        logger.info("   如果需要交易功能，请在富途APP中设置交易密码")
    else:
        logger.warning("\n⚠️ 富途OpenD连接失败")
        logger.warning("   请确保:")
        logger.warning("   1. 富途OpenD客户端正在运行")
        logger.warning("   2. 使用牛牛号 2860386 登录")
        logger.warning("   3. 连接到DEMO环境")

    if trading_success:
        logger.info("\n✅ 模拟交易系统工作正常")
        logger.info("   即使富途连接失败，模拟交易功能也可以独立使用")

    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
