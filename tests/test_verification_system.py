#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证系统测试脚本
测试CPU监控、任务计时、结果验证功能
"""

import sys
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("TEST")

# 导入系统组件
try:
    from complete_project_system import (
        CPUMonitor,
        validate_optimization_results,
        run_ma_strategy,
        calculate_strategy_performance
    )
    logger.info("✅ 成功导入系统组件")
except Exception as e:
    logger.error(f"❌ 导入失败: {e}")
    sys.exit(1)

# ==================== Test 1: CPU监控系统 ====================
def test_cpu_monitoring():
    """测试CPU监控功能"""
    logger.info("\n" + "="*60)
    logger.info("📊 Test 1: CPU监控系统")
    logger.info("="*60)

    try:
        # 创建CPU监控实例
        cpu_monitor = CPUMonitor()
        logger.info("✅ CPUMonitor实例创建成功")

        # 捕获基线
        baseline = cpu_monitor.capture_baseline()
        if baseline:
            logger.info(f"✅ 基线捕获成功: {baseline}")
        else:
            logger.error("❌ 基线捕获失败")
            return False

        # 模拟一些计算
        logger.info("⏳ 模拟计算中（3秒）...")
        time.sleep(3)

        # 捕获快照
        snapshot = cpu_monitor.capture_snapshot()
        if snapshot:
            logger.info(f"✅ 快照捕获成功: CPU={snapshot['cpu_percent']:.1f}%")
        else:
            logger.error("❌ 快照捕获失败")
            return False

        # 生成报告
        report = cpu_monitor.generate_report()
        if report:
            logger.info(f"✅ 报告生成成功")
            logger.info(f"   CPU变化: {report['cpu_change']:+.1f}%")
            logger.info(f"   内存变化: {report['memory_change']:+.1f}MB")
            logger.info(f"   活跃进程: {report['active_children']}/{report.get('peak_children', 'N/A')}")
            return True
        else:
            logger.error("❌ 报告生成失败")
            return False

    except Exception as e:
        logger.error(f"❌ Test 1失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

# ==================== Test 2: 结果验证系统 ====================
def test_result_validation():
    """测试结果验证功能"""
    logger.info("\n" + "="*60)
    logger.info("🔍 Test 2: 结果验证系统")
    logger.info("="*60)

    try:
        # 创建模拟结果
        mock_results = [
            {
                'strategy_name': f'MA_Test_{i}',
                'sharpe_ratio': 1.2 + np.random.randn() * 0.3,
                'total_return': 15 + np.random.randn() * 8,
                'max_drawdown': -8 + np.random.randn() * 2,
            }
            for i in range(50)
        ]

        logger.info(f"✅ 创建{len(mock_results)}个模拟结果")

        # 验证结果
        validation_report = validate_optimization_results(mock_results)
        if validation_report:
            logger.info(f"✅ 验证报告生成成功")
            logger.info(f"   状态: {validation_report['status']}")
            logger.info(f"   Sharpe多样性: {validation_report['diversity_metrics']['sharpe_ratio_unique']}/{len(mock_results)}")
            logger.info(f"   多样性比率: {validation_report['diversity_metrics']['sharpe_ratio_diversity']:.1%}")
            logger.info(f"   检查通过: {validation_report['checks']['all_passed']}")
            logger.info(f"   Sharpe统计: 平均={validation_report['statistics']['sharpe_mean']:.2f}, "
                       f"标准差={validation_report['statistics']['sharpe_std']:.2f}")
            return validation_report['checks']['all_passed']
        else:
            logger.error("❌ 验证报告生成失败")
            return False

    except Exception as e:
        logger.error(f"❌ Test 2失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

# ==================== Test 3: 任务计时 ====================
def test_task_timing():
    """测试任务计时功能"""
    logger.info("\n" + "="*60)
    logger.info("⏱️ Test 3: 任务计时系统")
    logger.info("="*60)

    try:
        # 生成测试数据
        dates = pd.date_range(end=datetime.now(), periods=500, freq='D')
        test_data = []
        price = 100
        for date in dates:
            price += np.random.randn() * 2
            test_data.append({
                'date': date,
                'open': price,
                'high': price + 1,
                'low': price - 1,
                'close': price,
                'volume': 1000000,
            })

        df = pd.DataFrame(test_data)
        logger.info(f"✅ 创建{len(df)}行测试数据")

        # 测试MA策略计算计时
        logger.info("⏳ 运行MA策略计算...")
        wall_start = time.time()
        cpu_start = time.process_time()

        result = run_ma_strategy(df, short_window=5, long_window=20)

        wall_time_ms = (time.time() - wall_start) * 1000
        cpu_time_ms = (time.process_time() - cpu_start) * 1000
        cpu_efficiency = (cpu_time_ms / wall_time_ms * 100) if wall_time_ms > 0 else 0

        if result:
            logger.info(f"✅ 策略计算完成")
            logger.info(f"   壁钟时间: {wall_time_ms:.2f}ms")
            logger.info(f"   CPU时间: {cpu_time_ms:.2f}ms")
            logger.info(f"   CPU效率: {cpu_efficiency:.1f}%")
            logger.info(f"   Sharpe比率: {result['sharpe_ratio']:.3f}")

            # 验证计时数据合理性
            if wall_time_ms > 0 and cpu_efficiency > 50:
                logger.info("✅ 计时数据合理")
                return True
            else:
                logger.warning("⚠️ 计时数据异常")
                return False
        else:
            logger.error("❌ 策略计算失败")
            return False

    except Exception as e:
        logger.error(f"❌ Test 3失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

# ==================== Test 4: 小规模多策略优化 ====================
def test_small_optimization():
    """测试小规模策略优化"""
    logger.info("\n" + "="*60)
    logger.info("🚀 Test 4: 小规模多策略优化")
    logger.info("="*60)

    try:
        # 生成测试数据
        dates = pd.date_range(end=datetime.now(), periods=500, freq='D')
        test_data = []
        price = 100
        for date in dates:
            price += np.random.randn() * 2
            test_data.append({
                'date': date,
                'open': price,
                'high': price + 1,
                'low': price - 1,
                'close': price,
                'volume': 1000000,
            })

        df = pd.DataFrame(test_data)
        logger.info(f"✅ 创建{len(df)}行测试数据")

        # 测试少数MA参数组合
        logger.info("⏳ 运行小规模优化（只测试5个MA参数组合）...")

        results = []
        timing_stats = []
        start_time = time.time()

        for short in [3, 5, 10, 15, 20]:
            for long in [30, 50]:
                if short < long:
                    # 计时
                    wall_start = time.time()
                    cpu_start = time.process_time()

                    result = run_ma_strategy(df, short, long)

                    wall_time_ms = (time.time() - wall_start) * 1000
                    cpu_time_ms = (time.process_time() - cpu_start) * 1000

                    if result:
                        result['_timing'] = {
                            'wall_time_ms': round(wall_time_ms, 2),
                            'cpu_time_ms': round(cpu_time_ms, 2),
                            'cpu_efficiency': round(cpu_time_ms / wall_time_ms * 100, 1),
                        }
                        results.append(result)
                        timing_stats.append(result['_timing'])
                        logger.info(f"✓ MA({short},{long}): Sharpe={result['sharpe_ratio']:.3f}, "
                                  f"时间={wall_time_ms:.1f}ms")

        elapsed = time.time() - start_time
        logger.info(f"✅ 优化完成: {len(results)}个结果, 耗时{elapsed:.2f}秒")

        # 计时统计
        if timing_stats:
            wall_times = [t['wall_time_ms'] for t in timing_stats]
            logger.info(f"⏱️ 计时统计:")
            logger.info(f"   平均耗时: {np.mean(wall_times):.1f}ms")
            logger.info(f"   范围: {min(wall_times):.1f}ms - {max(wall_times):.1f}ms")
            logger.info(f"   平均CPU效率: {np.mean([t['cpu_efficiency'] for t in timing_stats]):.1f}%")

        # 验证结果
        if len(results) > 0:
            validation_report = validate_optimization_results(results)
            logger.info(f"✅ 验证报告:")
            logger.info(f"   状态: {validation_report['status']}")
            logger.info(f"   Sharpe多样性: {validation_report['diversity_metrics']['sharpe_ratio_unique']}/{len(results)}")
            return True
        else:
            logger.error("❌ 没有结果返回")
            return False

    except Exception as e:
        logger.error(f"❌ Test 4失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

# ==================== 主测试函数 ====================
def run_all_tests():
    """运行所有测试"""
    logger.info("\n" + "█"*60)
    logger.info("验证系统完整测试套件")
    logger.info("█"*60)

    tests = [
        ("CPU监控", test_cpu_monitoring),
        ("结果验证", test_result_validation),
        ("任务计时", test_task_timing),
        ("小规模优化", test_small_optimization),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"❌ {test_name}异常: {e}")
            results[test_name] = False

    # 总结
    logger.info("\n" + "="*60)
    logger.info("📋 测试总结")
    logger.info("="*60)
    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {test_name}")

    logger.info(f"\n总体: {passed}/{total} 测试通过")

    if passed == total:
        logger.info("🎉 所有测试通过！系统就绪")
        return True
    else:
        logger.warning(f"⚠️ {total - passed}个测试失败")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
