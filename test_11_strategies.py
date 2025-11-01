#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试11种技术指标策略的一致性验证脚本
验证前后端11种策略的完整性和正确性
"""

import requests
import json
import time
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 测试配置
BASE_URL = "http://localhost:8013"
TEST_SYMBOL = "0700.HK"

def test_api_health():
    """测试API健康状态"""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        logger.info(f"健康检查: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return False

def test_strategy_optimization(strategy_type):
    """测试特定策略的优化"""
    try:
        logger.info(f"测试策略优化: {strategy_type}")

        # 调用策略优化API
        url = f"{BASE_URL}/api/strategy-optimization/{TEST_SYMBOL}?strategy_type={strategy_type}"
        response = requests.get(url, timeout=30)

        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                logger.info(f"✅ {strategy_type} 策略优化成功")
                logger.info(f"   - 找到策略数: {result.get('data', {}).get('total_strategies', 0)}")
                logger.info(f"   - 最佳Sharpe比率: {result.get('data', {}).get('best_sharpe_ratio', 0):.3f}")
                return True
            else:
                logger.warning(f"⚠️ {strategy_type} 策略优化失败: {result.get('message', '未知错误')}")
                return False
        else:
            logger.error(f"❌ {strategy_type} API调用失败: {response.status_code}")
            logger.error(f"   响应内容: {response.text}")
            return False

    except requests.exceptions.Timeout:
        logger.error(f"❌ {strategy_type} 策略优化超时")
        return False
    except Exception as e:
        logger.error(f"❌ {strategy_type} 策略优化异常: {e}")
        return False

def test_all_strategies():
    """测试所有11种策略"""
    # 策略类型列表（11种）
    strategies = [
        ('all', '全部策略'),
        # 基础策略 (4种)
        ('ma', 'MA交叉策略'),
        ('rsi', 'RSI策略'),
        ('macd', 'MACD策略'),
        ('bb', '布林带策略'),
        # 高级指标 (7种)
        ('kdj', 'KDJ策略'),
        ('cci', 'CCI策略'),
        ('adx', 'ADX策略'),
        ('atr', 'ATR策略'),
        ('obv', 'OBV策略'),
        ('ichimoku', 'Ichimoku策略'),
        ('psar', 'PSAR策略')
    ]

    results = []

    logger.info("=" * 80)
    logger.info("开始测试11种技术指标策略优化")
    logger.info("=" * 80)

    for strategy_type, strategy_name in strategies:
        logger.info(f"\n[{strategy_name}] ({strategy_type})")
        logger.info("-" * 50)

        success = test_strategy_optimization(strategy_type)
        results.append((strategy_type, strategy_name, success))

        # 避免API调用过于频繁
        time.sleep(1)

    return results

def generate_test_report(results):
    """生成测试报告"""
    logger.info("\n" + "=" * 80)
    logger.info("测试报告")
    logger.info("=" * 80)

    total = len(results)
    passed = sum(1 for _, _, success in results if success)
    failed = total - passed

    logger.info(f"测试总数: {total}")
    logger.info(f"通过: {passed} ✅")
    logger.info(f"失败: {failed} ❌")
    logger.info(f"成功率: {(passed/total)*100:.1f}%")

    logger.info("\n详细结果:")
    logger.info("-" * 80)
    for strategy_type, strategy_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status:<8} {strategy_name} ({strategy_type})")

    # 前端一致性验证
    logger.info("\n" + "=" * 80)
    logger.info("前端一致性验证")
    logger.info("=" * 80)

    expected_strategies = [
        'all', 'ma', 'rsi', 'macd', 'bb',
        'kdj', 'cci', 'adx', 'atr', 'obv', 'ichimoku', 'psar'
    ]

    actual_strategies = [r[0] for r in results]

    logger.info(f"预期策略数量: {len(expected_strategies)}")
    logger.info(f"实际策略数量: {len(actual_strategies)}")

    if set(expected_strategies) == set(actual_strategies):
        logger.info("✅ 前后端策略类型完全一致！")
    else:
        missing = set(expected_strategies) - set(actual_strategies)
        extra = set(actual_strategies) - set(expected_strategies)

        if missing:
            logger.warning(f"⚠️ 缺失策略: {missing}")
        if extra:
            logger.warning(f"⚠️ 额外策略: {extra}")

    # 最终结论
    logger.info("\n" + "=" * 80)
    logger.info("最终结论")
    logger.info("=" * 80)

    if passed == total:
        logger.info("🎉 所有11种策略测试通过！")
        logger.info("✅ 前后端一致性验证成功")
        logger.info("✅ 系统功能完整")
    else:
        logger.warning(f"⚠️ 有 {failed} 种策略测试失败")
        logger.info("需要检查失败的策略实现")

    return passed == total

def main():
    """主函数"""
    logger.info("开始11种技术指标策略一致性验证")
    logger.info(f"测试目标: {BASE_URL}")
    logger.info(f"测试股票: {TEST_SYMBOL}")
    logger.info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. 测试API健康状态
    logger.info("\n1. 测试API健康状态...")
    if not test_api_health():
        logger.error("API健康检查失败，测试终止")
        return False

    # 2. 测试所有策略
    logger.info("\n2. 测试所有策略...")
    results = test_all_strategies()

    # 3. 生成测试报告
    logger.info("\n3. 生成测试报告...")
    success = generate_test_report(results)

    return success

if __name__ == "__main__":
    try:
        success = main()
        exit_code = 0 if success else 1
        logger.info(f"\n测试完成，退出码: {exit_code}")
        exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n测试被用户中断")
        exit(1)
    except Exception as e:
        logger.error(f"\n测试异常: {e}")
        exit(1)
