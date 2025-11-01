"""
富途DEMO账户连接验证脚本

测试富途OpenD连接、认证和基本交易功能
使用DEMO环境，确保不会产生真实交易
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

logger = logging.getLogger("futu_connection_test")


async def test_futu_connection():
    """测试富途连接"""
    logger.info("=" * 80)
    logger.info("富途牛牛DEMO账户连接验证")
    logger.info("=" * 80)

    try:
        # 导入富途API
        from src.trading.futu_trading_api import FutuTradingAPI, create_futu_trading_api
        from src.trading.realtime_execution_engine import TradeSignal, ExecutionStrategy, OrderSide

        logger.info("✅ 富途API模块导入成功")

        # 创建富途API实例
        logger.info("\n步骤 1/5: 创建富途API实例...")
        futu_api = create_futu_trading_api(
            host='127.0.0.1',
            port=11111,
            trade_password='123456',  # DEMO环境默认密码
            market='HK'
        )
        logger.info("✅ 富途API实例创建成功")

        # 连接富途API
        logger.info("\n步骤 2/5: 连接到富途OpenD...")
        connected = await futu_api.connect()
        if connected:
            logger.info("✅ 成功连接到富途OpenD (127.0.0.1:11111)")
        else:
            logger.error("❌ 连接富途OpenD失败")
            logger.error("请确保：")
            logger.error("  1. 富途OpenD客户端已启动")
            logger.error("  2. 使用牛牛号 2860386 登录DEMO环境")
            logger.error("  3. 端口 11111 未被占用")
            return False

        # 身份验证
        logger.info("\n步骤 3/5: 解锁交易接口...")
        auth_config = {'trade_password': '123456'}
        authenticated = await futu_api.authenticate(auth_config)
        if authenticated:
            logger.info("✅ 成功解锁交易接口")
        else:
            logger.error("❌ 解锁交易接口失败")
            logger.error("请检查DEMO账户的交易密码")
            return False

        # 健康检查
        logger.info("\n步骤 4/5: 执行健康检查...")
        health = await futu_api.health_check()
        logger.info(f"健康状态: {health}")

        if health.get('status') == 'healthy':
            logger.info("✅ 系统健康检查通过")
        else:
            logger.warning("⚠️ 系统健康检查未完全通过，但可以继续")

        # 测试获取账户信息
        logger.info("\n步骤 5/5: 获取账户信息...")
        account_info = await futu_api.get_account_info()
        if account_info:
            logger.info("✅ 账户信息获取成功:")
            logger.info(f"  账户ID: {account_info.account_id}")
            logger.info(f"  账户类型: {account_info.account_type}")
            logger.info(f"  现金余额: {account_info.cash}")
            logger.info(f"  购买力: {account_info.buying_power}")
        else:
            logger.warning("⚠️ 无法获取账户信息（可能是权限不足）")

        # 测试获取持仓
        logger.info("\n获取持仓信息...")
        positions = await futu_api.get_positions()
        logger.info(f"持仓数量: {len(positions)}")
        for pos in positions:
            logger.info(f"  - {pos.symbol}: {pos.quantity} 股")

        # 测试获取订单
        logger.info("\n获取订单信息...")
        orders = await futu_api.get_orders()
        logger.info(f"订单数量: {len(orders)}")

        # 测试获取市场数据
        logger.info("\n获取市场数据 (00700.HK - 腾讯)...")
        market_data = await futu_api.get_market_data('00700.HK')
        if market_data:
            logger.info("✅ 市场数据获取成功:")
            logger.info(f"  最新价: {market_data.last_price}")
            logger.info(f"  买入价: {market_data.bid_price}")
            logger.info(f"  卖出价: {market_data.ask_price}")
            logger.info(f"  成交量: {market_data.volume}")
        else:
            logger.warning("⚠️ 无法获取市场数据")

        logger.info("\n" + "=" * 80)
        logger.info("✅ 富途DEMO账户连接验证成功！")
        logger.info("=" * 80)

        # 清理
        await futu_api.disconnect()
        logger.info("✅ 已断开连接")

        return True

    except ImportError as e:
        logger.error(f"❌ 导入富途API失败: {e}")
        logger.error("请安装富途API: pip install futu-api")
        return False

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        return False


async def test_demo_trading():
    """测试DEMO交易（仅限测试环境）"""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO环境交易功能测试")
    logger.info("=" * 80)

    try:
        from src.trading.futu_trading_api import create_futu_trading_api
        from src.trading.realtime_execution_engine import TradeSignal, ExecutionStrategy, OrderSide
        from src.trading.futu_paper_trading_controller import create_paper_trading_controller

        # 创建控制器
        logger.info("\n创建模拟交易控制器...")
        controller = create_paper_trading_controller(
            futu_host='127.0.0.1',
            futu_port=11111,
            trade_password='123456',
            market='HK',
            initial_balance=Decimal('1000000')
        )
        logger.info("✅ 控制器创建成功")

        # 初始化
        logger.info("\n初始化控制器...")
        success = await controller.initialize()
        if not success:
            logger.error("❌ 控制器初始化失败")
            return False
        logger.info("✅ 控制器初始化成功")

        # 启动交易
        logger.info("\n启动交易...")
        await controller.start_trading()
        logger.info("✅ 交易已启动")

        # 创建测试交易信号
        logger.info("\n创建测试交易信号...")
        signal = TradeSignal(
            signal_id=f"TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            symbol="00700.HK",
            side=OrderSide.BUY,
            quantity=Decimal('100'),
            strategy=ExecutionStrategy.IMMEDIATE,
            price=Decimal('350.0')  # 腾讯 350 HKD
        )
        logger.info(f"信号: {signal.symbol} {signal.side} {signal.quantity} @ {signal.price}")

        # 执行交易
        logger.info("\n执行交易信号...")
        result = await controller.execute_signal(signal)
        logger.info(f"交易结果: {result}")

        # 获取状态
        logger.info("\n获取交易状态...")
        status = await controller.get_status()
        logger.info(f"交易次数: {status['stats']['total_trades']}")
        logger.info(f"账户余额: {status['account']['cash'] if status['account'] else 'N/A'}")

        # 清理
        await controller.cleanup()
        logger.info("✅ 清理完成")

        logger.info("\n" + "=" * 80)
        logger.info("✅ DEMO交易测试完成")
        logger.info("=" * 80)

        return True

    except Exception as e:
        logger.error(f"❌ DEMO交易测试失败: {e}", exc_info=True)
        return False


async def main():
    """主函数"""
    logger.info("富途牛牛DEMO账户验证工具")
    logger.info("")
    logger.info("⚠️ 重要提示:")
    logger.info("  - 本工具使用DEMO环境，不会产生真实交易")
    logger.info("  - 请确保富途OpenD客户端正在运行")
    logger.info("  - 使用牛牛号 2860386 登录DEMO环境")
    logger.info("")

    # 测试连接
    logger.info("\n" + "🔍 第一阶段：连接测试")
    connection_success = await test_futu_connection()

    if not connection_success:
        logger.error("\n❌ 连接测试失败，请检查富途OpenD客户端")
        return

    # 测试交易
    logger.info("\n" + "💼 第二阶段：交易测试")
    trading_success = await test_demo_trading()

    # 总结
    logger.info("\n" + "=" * 80)
    logger.info("验证总结")
    logger.info("=" * 80)
    logger.info(f"连接测试: {'✅ 通过' if connection_success else '❌ 失败'}")
    logger.info(f"交易测试: {'✅ 通过' if trading_success else '❌ 失败'}")

    if connection_success and trading_success:
        logger.info("\n🎉 所有测试通过！富途DEMO账户可以正常使用")
    else:
        logger.warning("\n⚠️ 部分测试失败，请检查错误信息")

    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
