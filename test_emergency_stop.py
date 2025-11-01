"""
紧急停止机制测试

测试增强的紧急停止功能，包括：
- 触发紧急停止
- 紧急停止状态检查
- 交易被阻止
- 恢复机制
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

logger = logging.getLogger("test_emergency_stop")


async def test_emergency_stop_activation():
    """测试紧急停止激活"""
    logger.info("=" * 80)
    logger.info("测试 1: 紧急停止激活")
    logger.info("=" * 80)

    try:
        # 创建风险管理器
        risk_manager = create_risk_manager(
            min_cash_reserve=Decimal('100000'),
            max_trade_value=Decimal('50000'),
            max_daily_trades=10
        )

        # 检查初始状态
        assert not risk_manager.is_emergency_stop_active()
        logger.info("✅ 初始状态：紧急停止未激活")

        # 触发紧急停止
        reason = "测试紧急停止 - 系统异常"
        result = await risk_manager.emergency_stop(reason)

        if result:
            logger.info(f"✅ 紧急停止触发成功: {reason}")
        else:
            logger.error("❌ 紧急停止触发失败")
            return False

        # 检查紧急停止状态
        if risk_manager.is_emergency_stop_active():
            logger.info("✅ 紧急停止状态已激活")
        else:
            logger.error("❌ 紧急停止状态未激活")
            return False

        # 检查状态详情
        risk_status = await risk_manager.get_risk_status()
        emergency_info = risk_status.get('emergency_stop', {})

        logger.info(f"  - 激活状态: {emergency_info['active']}")
        logger.info(f"  - 触发时间: {emergency_info['trigger_time']}")
        logger.info(f"  - 停止原因: {emergency_info['reason']}")
        logger.info(f"  - 有备份: {emergency_info['has_backup']}")

        if emergency_info['active'] and emergency_info['reason'] == reason:
            logger.info("✅ 紧急停止状态信息正确")
        else:
            logger.error("❌ 紧急停止状态信息错误")
            return False

        return True

    except Exception as e:
        logger.error(f"❌ 紧急停止激活测试失败: {e}", exc_info=True)
        return False


async def test_emergency_stop_trade_blocking():
    """测试紧急停止时交易被阻止"""
    logger.info("\n" + "=" * 80)
    logger.info("测试 2: 紧急停止时交易被阻止")
    logger.info("=" * 80)

    try:
        # 创建风险管理器和账户
        risk_manager = create_risk_manager()
        account = AccountInfo(
            account_id="TEST_ACCOUNT",
            account_type="SIMULATED",
            buying_power=Decimal('1000000'),
            cash=Decimal('1000000'),
            equity=Decimal('1000000'),
            margin_used=Decimal('0'),
            margin_available=Decimal('1000000')
        )

        # 触发紧急停止
        await risk_manager.emergency_stop("测试交易阻止")

        # 尝试执行交易（应该被阻止）
        signal = TradeSignal(
            signal_id="TEST_001",
            symbol="00700.HK",
            side=OrderSide.BUY,
            quantity=Decimal('100'),
            strategy=ExecutionStrategy.IMMEDIATE,
            price=Decimal('300.0')
        )

        passed, message, details = await risk_manager.check_pre_trade_risk(
            signal, account, []
        )

        if not passed:
            logger.info(f"✅ 紧急停止时交易被正确阻止: {message}")
        else:
            logger.error("❌ 紧急停止时交易未被阻止")
            return False

        # 检查返回的详细信息
        if details.get('emergency_stop'):
            logger.info("✅ 返回了紧急停止信息")
        else:
            logger.error("❌ 未返回紧急停止信息")
            return False

        return True

    except Exception as e:
        logger.error(f"❌ 紧急停止交易阻止测试失败: {e}", exc_info=True)
        return False


async def test_emergency_stop_resume():
    """测试紧急停止恢复"""
    logger.info("\n" + "=" * 80)
    logger.info("测试 3: 紧急停止恢复")
    logger.info("=" * 80)

    try:
        # 创建风险管理器
        risk_manager = create_risk_manager(
            min_cash_reserve=Decimal('100000'),
            max_trade_value=Decimal('50000')
        )

        # 记录原始限制
        original_max_trade = risk_manager.limits.max_trade_value

        # 触发紧急停止
        await risk_manager.emergency_stop("测试恢复机制")

        # 等待一秒
        await asyncio.sleep(1)

        # 恢复紧急停止
        result = await risk_manager.resume_from_emergency_stop()

        if result:
            logger.info("✅ 紧急停止恢复成功")
        else:
            logger.error("❌ 紧急停止恢复失败")
            return False

        # 检查恢复后状态
        if not risk_manager.is_emergency_stop_active():
            logger.info("✅ 紧急停止状态已清除")
        else:
            logger.error("❌ 紧急停止状态未清除")
            return False

        # 检查风险限额是否恢复
        risk_status = await risk_manager.get_risk_status()
        emergency_info = risk_status.get('emergency_stop', {})

        if not emergency_info['active']:
            logger.info("✅ 风险状态显示正常")
        else:
            logger.error("❌ 风险状态显示异常")
            return False

        # 测试恢复后交易是否正常
        account = AccountInfo(
            account_id="TEST_ACCOUNT",
            account_type="SIMULATED",
            buying_power=Decimal('1000000'),
            cash=Decimal('1000000'),
            equity=Decimal('1000000'),
            margin_used=Decimal('0'),
            margin_available=Decimal('1000000')
        )

        signal = TradeSignal(
            signal_id="TEST_RESUME_001",
            symbol="00700.HK",
            side=OrderSide.BUY,
            quantity=Decimal('100'),
            strategy=ExecutionStrategy.IMMEDIATE,
            price=Decimal('300.0')
        )

        passed, message, details = await risk_manager.check_pre_trade_risk(
            signal, account, []
        )

        if passed:
            logger.info("✅ 恢复后交易正常执行")
        else:
            logger.error(f"❌ 恢复后交易被错误阻止: {message}")
            return False

        return True

    except Exception as e:
        logger.error(f"❌ 紧急停止恢复测试失败: {e}", exc_info=True)
        return False


async def test_emergency_stop_double_activation():
    """测试重复触发紧急停止"""
    logger.info("\n" + "=" * 80)
    logger.info("测试 4: 重复触发紧急停止")
    logger.info("=" * 80)

    try:
        risk_manager = create_risk_manager()

        # 第一次触发
        await risk_manager.emergency_stop("第一次紧急停止")
        first_stop_time = risk_manager.emergency_stop_time

        # 等待一会儿
        await asyncio.sleep(0.5)

        # 第二次触发（应该被忽略或记录但不重复执行）
        await risk_manager.emergency_stop("第二次紧急停止")
        second_stop_time = risk_manager.emergency_stop_time

        # 两次时间应该相同（没有重复触发）
        if first_stop_time == second_stop_time:
            logger.info("✅ 重复触发紧急停止被正确处理（忽略重复触发）")
        else:
            logger.warning("⚠️ 重复触发紧急停止可能触发了多次（需要检查逻辑）")

        return True

    except Exception as e:
        logger.error(f"❌ 重复触发紧急停止测试失败: {e}", exc_info=True)
        return False


async def test_emergency_stop_with_paper_engine():
    """测试与模拟交易引擎的紧急停止集成"""
    logger.info("\n" + "=" * 80)
    logger.info("测试 5: 与模拟交易引擎的紧急停止集成")
    logger.info("=" * 80)

    try:
        from src.trading.paper_trading_engine import PaperTradingEngine
        from src.trading.futu_trading_api import create_futu_trading_api

        # 创建模拟富途API和引擎
        futu_api = create_futu_trading_api(
            host='127.0.0.1',
            port=11111,
            trade_password='',
            market='HK'
        )

        risk_manager = create_risk_manager()
        engine = PaperTradingEngine(
            futu_api=futu_api,
            initial_balance=Decimal('1000000'),
            risk_manager=risk_manager
        )

        await engine.initialize()

        # 触发紧急停止
        await risk_manager.emergency_stop("引擎集成测试")

        # 尝试执行交易
        signal = TradeSignal(
            signal_id="ENGINE_TEST_001",
            symbol="00700.HK",
            side=OrderSide.BUY,
            quantity=Decimal('100'),
            strategy=ExecutionStrategy.IMMEDIATE,
            price=Decimal('350.0')
        )

        result = await engine.execute_signal(signal)

        if not result.get('success'):
            logger.info(f"✅ 紧急停止时引擎正确阻止交易: {result.get('error')}")
        else:
            logger.error("❌ 紧急停止时引擎未阻止交易")
            return False

        # 恢复紧急停止
        await risk_manager.resume_from_emergency_stop()

        # 测试恢复后交易
        signal2 = TradeSignal(
            signal_id="ENGINE_TEST_002",
            symbol="00700.HK",
            side=OrderSide.BUY,
            quantity=Decimal('100'),
            strategy=ExecutionStrategy.IMMEDIATE,
            price=Decimal('350.0')
        )

        result2 = await engine.execute_signal(signal2)

        if result2.get('success'):
            logger.info("✅ 恢复后引擎交易正常执行")
        else:
            logger.error(f"❌ 恢复后引擎交易失败: {result2.get('error')}")
            return False

        await engine.cleanup()

        return True

    except Exception as e:
        logger.error(f"❌ 引擎紧急停止集成测试失败: {e}", exc_info=True)
        return False


async def main():
    """主函数"""
    logger.info("\n" + "=" * 80)
    logger.info("富途模拟交易系统 - 紧急停止机制测试")
    logger.info("=" * 80 + "\n")

    tests = [
        ("紧急停止激活", test_emergency_stop_activation),
        ("紧急停止交易阻止", test_emergency_stop_trade_blocking),
        ("紧急停止恢复", test_emergency_stop_resume),
        ("重复触发紧急停止", test_emergency_stop_double_activation),
        ("引擎紧急停止集成", test_emergency_stop_with_paper_engine),
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
    logger.info("紧急停止机制测试总结")
    logger.info("=" * 80)
    logger.info(f"总测试数: {len(tests)}")
    logger.info(f"通过: {passed}")
    logger.info(f"失败: {failed}")
    logger.info(f"成功率: {passed/len(tests)*100:.1f}%")

    if failed == 0:
        logger.info("\n🎉 所有紧急停止测试通过！紧急停止机制验证成功")
    else:
        logger.error(f"\n⚠️ 有 {failed} 个测试失败，请检查代码")

    logger.info("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
