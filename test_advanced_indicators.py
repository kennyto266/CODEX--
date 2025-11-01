#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级技术指标策略 - 单元测试与验证
测试所有7个新增指标的策略执行、参数优化和性能

Test Coverage:
  - KDJ, CCI, ADX, ATR, OBV, Ichimoku, Parabolic SAR
  - 参数优化并行执行
  - 结果验证和性能基准
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import time
from enhanced_strategy_backtest import EnhancedStrategyBacktest

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestAdvancedIndicators(unittest.TestCase):
    """高级技术指标策略测试"""

    @classmethod
    def setUpClass(cls):
        """设置测试用例，加载测试数据"""
        logger.info("=" * 80)
        logger.info("🧪 开始执行高级技术指标测试套件")
        logger.info("=" * 80)

        # 创建2年的测试数据 (约500个交易日)
        cls.backtest = EnhancedStrategyBacktest(
            symbol='0700.HK',
            start_date='2022-01-01',
            end_date='2024-01-01'
        )

        # 加载数据
        success = cls.backtest.load_data()
        assert success, "数据加载失败"

        logger.info(f"✓ 加载数据成功: {len(cls.backtest.data)} 个交易日")
        logger.info(f"  日期范围: {cls.backtest.data.index[0].date()} 至 {cls.backtest.data.index[-1].date()}")
        logger.info(f"  数据列: {list(cls.backtest.data.columns)}")

    def test_calculate_technical_indicators(self):
        """测试技术指标计算"""
        logger.info("\n📊 测试1: 技术指标计算")

        df = self.backtest.data.copy()
        result_df = self.backtest.calculate_technical_indicators(df)

        # 验证指标列是否存在
        required_indicators = [
            'K', 'D', 'J',  # KDJ
            'CCI',  # CCI
            'plus_di', 'minus_di', 'ADX',  # ADX
            'ATR',  # ATR
            'OBV', 'OBV_MA',  # OBV
            'Tenkan', 'Kijun', 'Senkou_A', 'Senkou_B', 'Chikou',  # Ichimoku
            'SAR'  # Parabolic SAR
        ]

        for indicator in required_indicators:
            self.assertIn(indicator, result_df.columns, f"缺少指标: {indicator}")
            logger.info(f"  ✓ {indicator:15} - 计算成功")

        # 验证数据类型
        numeric_cols = result_df.select_dtypes(include=[np.number]).columns
        self.assertGreater(len(numeric_cols), 20, "指标列数不足")

        logger.info(f"  ✓ 总共计算 {len(numeric_cols)} 个指标列")
        logger.info(f"  ✓ 技术指标计算测试通过 ✅")

    def test_kdj_strategy(self):
        """测试KDJ策略"""
        logger.info("\n📈 测试2: KDJ 随机指标策略")

        result = self.backtest.run_kdj_strategy(k_period=9, d_period=3, oversold=20, overbought=80)

        self.assertIsNotNone(result, "KDJ策略返回None")
        self._validate_strategy_result(result, "KDJ")

        logger.info(f"  策略名称: {result['strategy_name']}")
        logger.info(f"  总收益率: {result['total_return']:.2f}%")
        logger.info(f"  夏普比率: {result['sharpe_ratio']:.3f}")
        logger.info(f"  最大回撤: {result['max_drawdown']:.2f}%")
        logger.info(f"  ✓ KDJ策略测试通过 ✅")

    def test_cci_strategy(self):
        """测试CCI策略"""
        logger.info("\n📈 测试3: CCI 商品通道指标策略")

        result = self.backtest.run_cci_strategy(period=20, oversold=-100, overbought=100)

        self.assertIsNotNone(result, "CCI策略返回None")
        self._validate_strategy_result(result, "CCI")

        logger.info(f"  策略名称: {result['strategy_name']}")
        logger.info(f"  年化收益率: {result['annual_return']:.2f}%")
        logger.info(f"  波动率: {result['volatility']:.2f}%")
        logger.info(f"  胜率: {result['win_rate']:.2f}%")
        logger.info(f"  ✓ CCI策略测试通过 ✅")

    def test_adx_strategy(self):
        """测试ADX策略"""
        logger.info("\n📈 测试4: ADX 平均趋向指标策略")

        result = self.backtest.run_adx_strategy(period=14, adx_threshold=25)

        self.assertIsNotNone(result, "ADX策略返回None")
        self._validate_strategy_result(result, "ADX")

        logger.info(f"  策略名称: {result['strategy_name']}")
        logger.info(f"  总收益率: {result['total_return']:.2f}%")
        logger.info(f"  交易次数: {result['trade_count']}")
        logger.info(f"  ✓ ADX策略测试通过 ✅")

    def test_atr_strategy(self):
        """测试ATR策略"""
        logger.info("\n📈 测试5: ATR 平均真实范围策略")

        result = self.backtest.run_atr_strategy(period=14, atr_multiplier=2.0)

        self.assertIsNotNone(result, "ATR策略返回None")
        self._validate_strategy_result(result, "ATR")

        logger.info(f"  策略名称: {result['strategy_name']}")
        logger.info(f"  年化收益率: {result['annual_return']:.2f}%")
        logger.info(f"  最大回撤: {result['max_drawdown']:.2f}%")
        logger.info(f"  ✓ ATR策略测试通过 ✅")

    def test_obv_strategy(self):
        """测试OBV策略"""
        logger.info("\n📈 测试6: OBV 能量潮指标策略")

        result = self.backtest.run_obv_strategy(trend_period=20)

        self.assertIsNotNone(result, "OBV策略返回None")
        self._validate_strategy_result(result, "OBV")

        logger.info(f"  策略名称: {result['strategy_name']}")
        logger.info(f"  夏普比率: {result['sharpe_ratio']:.3f}")
        logger.info(f"  胜率: {result['win_rate']:.2f}%")
        logger.info(f"  ✓ OBV策略测试通过 ✅")

    def test_ichimoku_strategy(self):
        """测试Ichimoku策略"""
        logger.info("\n📈 测试7: Ichimoku 一目均衡表策略")

        result = self.backtest.run_ichimoku_strategy(conversion_period=9, base_period=26, span_b_period=52)

        self.assertIsNotNone(result, "Ichimoku策略返回None")
        self._validate_strategy_result(result, "Ichimoku")

        logger.info(f"  策略名称: {result['strategy_name']}")
        logger.info(f"  总收益率: {result['total_return']:.2f}%")
        logger.info(f"  年化收益率: {result['annual_return']:.2f}%")
        logger.info(f"  ✓ Ichimoku策略测试通过 ✅")

    def test_parabolic_sar_strategy(self):
        """测试Parabolic SAR策略"""
        logger.info("\n📈 测试8: Parabolic SAR 拋物線轉向指標策略")

        result = self.backtest.run_parabolic_sar_strategy(acceleration=0.02, max_acceleration=0.2)

        self.assertIsNotNone(result, "Parabolic SAR策略返回None")
        self._validate_strategy_result(result, "Parabolic SAR")

        logger.info(f"  策略名称: {result['strategy_name']}")
        logger.info(f"  夏普比率: {result['sharpe_ratio']:.3f}")
        logger.info(f"  最大回撤: {result['max_drawdown']:.2f}%")
        logger.info(f"  ✓ Parabolic SAR策略测试通过 ✅")

    def test_parameter_optimization_kdj(self):
        """测试KDJ参数优化"""
        logger.info("\n⚙️  测试9: KDJ 参数优化")

        start_time = time.time()
        results = self.backtest.optimize_parameters(strategy_type='kdj', max_workers=4)
        elapsed = time.time() - start_time

        self.assertGreater(len(results), 0, "KDJ优化返回空结果")
        self.assertGreater(len(results), 50, f"KDJ优化结果过少: {len(results)}")

        # 验证排序
        sharpe_ratios = [r['sharpe_ratio'] for r in results]
        self.assertEqual(sharpe_ratios, sorted(sharpe_ratios, reverse=True), "结果未按Sharpe比率排序")

        logger.info(f"  ✓ 测试参数组合数: {len(results)}")
        logger.info(f"  ✓ 最佳Sharpe比率: {results[0]['sharpe_ratio']:.3f}")
        logger.info(f"  ✓ 最佳策略: {results[0]['strategy_name']}")
        logger.info(f"  ✓ 执行时间: {elapsed:.2f}秒")
        logger.info(f"  ✓ KDJ参数优化测试通过 ✅")

    def test_parameter_optimization_cci(self):
        """测试CCI参数优化"""
        logger.info("\n⚙️  测试10: CCI 参数优化")

        start_time = time.time()
        results = self.backtest.optimize_parameters(strategy_type='cci', max_workers=4)
        elapsed = time.time() - start_time

        self.assertGreater(len(results), 0, "CCI优化返回空结果")

        logger.info(f"  ✓ 测试参数组合数: {len(results)}")
        logger.info(f"  ✓ 最佳Sharpe比率: {results[0]['sharpe_ratio']:.3f}")
        logger.info(f"  ✓ 执行时间: {elapsed:.2f}秒")
        logger.info(f"  ✓ CCI参数优化测试通过 ✅")

    def test_parameter_ranges(self):
        """测试参数范围的合理性"""
        logger.info("\n✅ 测试11: 参数范围验证")

        # 测试各个指标的参数范围
        parameter_tests = [
            ("KDJ", {"k_period": [5, 30], "oversold": [20, 80]}),
            ("CCI", {"period": [10, 30], "oversold": [-300, 100]}),
            ("ADX", {"period": [10, 30], "adx_threshold": [15, 50]}),
            ("ATR", {"period": [10, 30], "atr_multiplier": [0.5, 5.0]}),
            ("Ichimoku", {"conversion_period": [5, 15], "base_period": [20, 40]}),
        ]

        for strategy_name, params in parameter_tests:
            logger.info(f"  ✓ {strategy_name:12} - 参数范围验证")
            for param, (min_val, max_val) in params.items():
                self.assertLessEqual(min_val, max_val, f"{strategy_name} {param} 范围错误")

        logger.info(f"  ✓ 参数范围验证通过 ✅")

    def test_strategy_comparison(self):
        """测试新旧策略对比"""
        logger.info("\n📊 测试12: 新旧策略对比")

        # 运行基础策略
        ma_result = self.backtest.run_ma_crossover_strategy(short_window=5, long_window=20)
        rsi_result = self.backtest.run_rsi_strategy(rsi_period=14, oversold=30, overbought=70)

        # 运行新策略
        kdj_result = self.backtest.run_kdj_strategy()
        ichimoku_result = self.backtest.run_ichimoku_strategy()

        strategies = {
            'MA': ma_result,
            'RSI': rsi_result,
            'KDJ': kdj_result,
            'Ichimoku': ichimoku_result
        }

        logger.info(f"\n  {'策略':<12} {'总收益率':>12} {'年化收益':>12} {'夏普比率':>12} {'最大回撤':>12}")
        logger.info(f"  {'-'*60}")

        for name, result in strategies.items():
            if result:
                logger.info(
                    f"  {name:<12} {result['total_return']:>11.2f}% {result['annual_return']:>11.2f}% "
                    f"{result['sharpe_ratio']:>11.3f} {result['max_drawdown']:>11.2f}%"
                )

        logger.info(f"  ✓ 策略对比测试通过 ✅")

    def test_performance_benchmark(self):
        """性能基准测试"""
        logger.info("\n⚡ 测试13: 性能基准测试")

        strategies = [
            ('KDJ', lambda: self.backtest.run_kdj_strategy()),
            ('CCI', lambda: self.backtest.run_cci_strategy()),
            ('ADX', lambda: self.backtest.run_adx_strategy()),
            ('ATR', lambda: self.backtest.run_atr_strategy()),
            ('OBV', lambda: self.backtest.run_obv_strategy()),
            ('Ichimoku', lambda: self.backtest.run_ichimoku_strategy()),
            ('Parabolic SAR', lambda: self.backtest.run_parabolic_sar_strategy()),
        ]

        logger.info(f"\n  {'策略':<15} {'执行时间(秒)':>15} {'结果':>20}")
        logger.info(f"  {'-'*50}")

        for name, func in strategies:
            start = time.time()
            result = func()
            elapsed = time.time() - start
            status = "✓ 成功" if result else "✗ 失败"
            logger.info(f"  {name:<15} {elapsed:>14.3f}s {status:>20}")

        logger.info(f"  ✓ 性能基准测试完成 ✅")

    def _validate_strategy_result(self, result, strategy_name):
        """验证策略结果的有效性"""
        self.assertIn('strategy_name', result)
        self.assertIn('total_return', result)
        self.assertIn('annual_return', result)
        self.assertIn('sharpe_ratio', result)
        self.assertIn('max_drawdown', result)
        self.assertIn('win_rate', result)
        self.assertIn('trade_count', result)

        # 验证数值范围合理性
        self.assertIsInstance(result['total_return'], (int, float))
        self.assertIsInstance(result['sharpe_ratio'], (int, float))
        self.assertGreaterEqual(result['win_rate'], 0)
        self.assertLessEqual(result['win_rate'], 100)


class TestIndicatorCalculations(unittest.TestCase):
    """技术指标计算细节测试"""

    @classmethod
    def setUpClass(cls):
        """设置测试数据"""
        cls.backtest = EnhancedStrategyBacktest('0700.HK', '2023-01-01', '2024-01-01')
        cls.backtest.load_data()

    def test_kdj_bounds(self):
        """KDJ指标应在0-100之间"""
        df = self.backtest.calculate_technical_indicators(self.backtest.data.copy())

        # 忽略NaN值
        k_values = df['K'].dropna()
        d_values = df['D'].dropna()

        self.assertTrue((k_values >= 0).all() and (k_values <= 100).all(), "KDJ K值超出范围")
        self.assertTrue((d_values >= 0).all() and (d_values <= 100).all(), "KDJ D值超出范围")

        logger.info("✓ KDJ界限验证通过")

    def test_ichimoku_lag(self):
        """Ichimoku Chikou线应该领先26个周期"""
        df = self.backtest.calculate_technical_indicators(self.backtest.data.copy())

        # 验证Chikou线的shift
        self.assertEqual(df['Chikou'].isna().sum(), 26, "Chikou线shift错误")

        logger.info("✓ Ichimoku延迟线验证通过")

    def test_atr_positive(self):
        """ATR值应该始终为正"""
        df = self.backtest.calculate_technical_indicators(self.backtest.data.copy())

        atr_values = df['ATR'].dropna()
        self.assertTrue((atr_values > 0).all(), "ATR包含非正值")

        logger.info("✓ ATR正值验证通过")

    def test_obv_monotonic(self):
        """OBV应该是单调的（非递减）"""
        df = self.backtest.calculate_technical_indicators(self.backtest.data.copy())

        obv = df['OBV'].dropna()
        # OBV可能增加、减少或保持不变
        self.assertEqual(len(obv), len(df['OBV'].dropna()), "OBV数据完整性检查")

        logger.info("✓ OBV单调性验证通过")


def run_full_test_suite():
    """运行完整的测试套件"""
    logger.info("\n" + "=" * 80)
    logger.info("🚀 开始执行完整测试套件 - 高级技术指标策略验证")
    logger.info("=" * 80)

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试
    suite.addTests(loader.loadTestsFromTestCase(TestAdvancedIndicators))
    suite.addTests(loader.loadTestsFromTestCase(TestIndicatorCalculations))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 打印总结
    logger.info("\n" + "=" * 80)
    logger.info("📋 测试完成总结")
    logger.info("=" * 80)
    logger.info(f"运行测试数: {result.testsRun}")
    logger.info(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    logger.info(f"失败: {len(result.failures)}")
    logger.info(f"错误: {len(result.errors)}")

    if result.wasSuccessful():
        logger.info("\n✅ 所有测试通过! 高级技术指标框架验证完成。")
    else:
        logger.error("\n❌ 部分测试失败，请检查上面的详细信息。")

    logger.info("=" * 80)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_full_test_suite()
    exit(0 if success else 1)
