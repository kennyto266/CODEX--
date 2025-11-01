"""
风险控制功能测试

测试模拟交易系统的风险控制机制
包括资金检查、仓位限制、交易频率限制等
"""

import asyncio
import logging
from decimal import Decimal
from datetime import datetime

from src.trading.paper_trading_risk_manager import (
    PaperTradingRiskManager,
    RiskLimits,
    create_risk_manager
)
from src.trading.realtime_execution_engine import TradeSignal, ExecutionStrategy, OrderSide
from src.trading.base_trading_api import AccountInfo, Position

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("test_risk_management")


async def test_risk_manager_basic():
    """测试风险管理器基本功能"""
    logger.info("=" * 80)
    logger.info("测试 1: 风险管理器基本功能")
    logger.info("=" * 80)

    try:
        # 创建风险管理器
        risk_manager = create_risk_manager(
            min_cash_reserve=Decimal('50000'),
            max_trade_value=Decimal('200000'),
            max_daily_trades=5,
            max_position_value=Decimal('300000')
        )

        logger.info("✅ 风险管理器创建成功")

        # 获取风险状态
        risk_status = await risk_manager.get_risk_status()
        logger.info(f"✅ 风险状态获取成功: {len(risk_status)} 项指标")

        # 测试紧急停止
        stopped = await risk_manager.emergency_stop()
        if stopped:
            logger.info("✅ 紧急停止执行成功")

        # 获取更新后的风险状态
        risk_status = await risk_manager.get_risk_status()
        logger.info(f"紧急停止后，日最大交易次数: {risk_status['risk_limits']['max_daily_trades']}")

        # 重置风险状态
        await risk_manager.reset_risk_state()
        logger.info("✅ 风险状态重置成功")

        return True

    except Exception as e:
        logger.error(f"❌ 风险管理器测试失败: {e}", exc_info=True)
        return False


async def test_risk_checks():
    """测试各种风险检查"""
    logger.info("\n" + "=" * 80)
    logger.info("测试 2: 风险检查功能")
    logger.info("=" * 80)

    try:
        # 创建风险管理器
        risk_manager = create_risk_manager(
            min_cash_reserve=Decimal('100000'),
            max_trade_value=Decimal('50000'),
            max_daily_trades=3
        )

        # 创建账户信息
        account = AccountInfo(
            account_id="TEST_ACCOUNT",
            account_type="SIMULATED",
            buying_power=Decimal('1000000'),
            cash=Decimal('1000000'),
            equity=Decimal('1000000'),
            margin_used=Decimal('0'),
            margin_available=Decimal('1000000')
        )

        # 测试1: 正常交易（应该通过）
        logger.info("\n测试 2.1: 正常交易检查")
        signal = TradeSignal(
            signal_id="TEST_001",
            symbol="00700.HK",
            side=OrderSide.BUY,
            quantity=Decimal('100'),
            strategy=ExecutionStrategy.IMMEDIATE,
            price=Decimal('300.0')
        )

        passed, message, details = await risk_manager.check_pre_trade_risk(signal, account, [])
        if passed:
            logger.info(f"✅ 正常交易检查通过: {message}")
        else:
            logger.error(f"❌ 正常交易检查失败: {message}")
            return False

        # 测试2: 超大交易（应该失败）
        logger.info("\n测试 2.2: 超大交易检查")
        signal_large = TradeSignal(
            signal_id="TEST_002",
            symbol="00700.HK",
            side=OrderSide.BUY,
            quantity=Decimal('1000'),
            strategy=ExecutionStrategy.IMMEDIATE,
            price=Decimal('300.0')  # 总价值 300,000 > 50,000 限制
        )

        passed, message, details = await risk_manager.check_pre_trade_risk(signal_large, account, [])
        if not passed:
            logger.info(f"✅ 超大交易检查正确拒绝: {message}")
        else:
            logger.error(f"❌ 超大交易检查未正确拒绝")
            return False

        # 测试3: 交易频率限制（应该失败）
        logger.info("\n测试 2.3: 交易频率检查")
        # 先执行3次交易（达到限制）
        for i in range(3):
            signal_freq = TradeSignal(
                signal_id=f"FREQ_{i}",
                symbol="03888.HK",
                side=OrderSide.BUY,
                quantity=Decimal('10'),
                strategy=ExecutionStrategy.IMMEDIATE,
                price=Decimal('100.0')
            )
            passed, message, details = await risk_manager.check_pre_trade_risk(signal_freq, account, [])
            if i < 2 and not passed:
                logger.error(f"❌ 第{i+1}次交易频率检查失败")
                return False

        # 尝试第4次交易（应该失败）
        signal_freq_4 = TradeSignal(
            signal_id="FREQ_3",
            symbol="03888.HK",
            side=OrderSide.BUY,
            quantity=Decimal('10'),
            strategy=ExecutionStrategy.IMMEDIATE,
            price=Decimal('100.0')
        )

        passed, message, details = await risk_manager.check_pre_trade_risk(signal_freq_4, account, [])
        if not passed:
            logger.info(f"✅ 交易频率检查正确拒绝: {message}")
        else:
            logger.error(f"❌ 交易频率检查未正确拒绝")
            return False

        logger.info("\n✅ 所有风险检查测试通过")
        return True

    except Exception as e:
        logger.error(f"❌ 风险检查测试失败: {e}", exc_info=True)
        return False


async def test_paper_engine_integration():
    """测试与模拟交易引擎的集成"""
    logger.info("\n" + "=" * 80)
    logger.info("测试 3: 模拟交易引擎集成")
    logger.info("=" * 80)

    try:
        from src.trading.paper_trading_engine import PaperTradingEngine
        from src.trading.futu_trading_api import create_futu_trading_api

        # 创建模拟富途API
        futu_api = create_futu_trading_api(
            host='127.0.0.1',
            port=11111,
            trade_password='',
            market='HK'
        )

        # 创建风险管理器
        risk_manager = create_risk_manager(
            max_trade_value=Decimal('50000')
        )

        # 创建模拟交易引擎
        engine = PaperTradingEngine(
            futu_api=futu_api,
            initial_balance=Decimal('1000000'),
            commission_rate=Decimal('0.001'),
            min_commission=Decimal('10'),
            risk_manager=risk_manager
        )

        await engine.initialize()

        logger.info("✅ 模拟交易引擎初始化成功（带风险控制）")

        # 执行正常交易
        signal = TradeSignal(
            signal_id="INTEGRATION_TEST_001",
            symbol="00700.HK",
            side=OrderSide.BUY,
            quantity=Decimal('100'),
            strategy=ExecutionStrategy.IMMEDIATE,
            price=Decimal('350.0')
        )

        result = await engine.execute_signal(signal)
        if result.get('success'):
            logger.info("✅ 正常交易执行成功")
        else:
            logger.error(f"❌ 正常交易执行失败: {result.get('error')}")
            return False

        # 尝试超大交易（应该被风险控制阻止）
        signal_large = TradeSignal(
            signal_id="INTEGRATION_TEST_002",
            symbol="00700.HK",
            side=OrderSide.BUY,
            quantity=Decimal('500'),
            strategy=ExecutionStrategy.IMMEDIATE,
            price=Decimal('350.0')  # 总价值 175,000 > 50,000 限制
        )

        result = await engine.execute_signal(signal_large)
        if not result.get('success'):
            logger.info(f"✅ 超大交易被风险控制阻止: {result.get('error')}")
        else:
            logger.error(f"❌ 超大交易未被阻止")
            return False

        # 获取风险状态
        risk_status = await risk_manager.get_risk_status()
        logger.info(f"✅ 风险状态: 日交易次数={risk_status['daily_trade_count']}")

        await engine.cleanup()

        logger.info("\n✅ 模拟交易引擎集成测试通过")
        return True

    except Exception as e:
        logger.error(f"❌ 引擎集成测试失败: {e}", exc_info=True)
        return False


async def main():
    """主函数"""
    logger.info("\n" + "=" * 80)
    logger.info("富途模拟交易系统 - 风险控制功能测试")
    logger.info("=" * 80 + "\n")

    tests = [
        ("风险管理器基本功能", test_risk_manager_basic),
        ("风险检查功能", test_risk_checks),
        ("模拟交易引擎集成", test_paper_engine_integration),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            result = await test_func()
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
        logger.info("\n🎉 所有测试通过！风险控制功能验证成功")
    else:
        logger.error(f"\n⚠️ 有 {failed} 个测试失败，请检查代码")

    logger.info("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
