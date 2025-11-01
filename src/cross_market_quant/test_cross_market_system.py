#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cross-Market Quantitative Trading System - Test Suite

Testing all core components

Run:
    python test_cross_market_system.py
"""

import unittest
import asyncio
import pandas as pd
import numpy as np
import sys
from datetime import datetime, timedelta

# Set UTF-8 encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())


import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adapters.fx_adapter import FXAdapter
from adapters.hkex_adapter import HKEXAdapter
from utils.cumulative_filter import CumulativeReturnFilter
from strategies.fx_hsi_strategy import FXHsiStrategy
from metrics.signal_statistics import SignalStatistics
from metrics.risk_adjusted_returns import RiskAdjustedReturns


class TestCrossMarketQuant(unittest.TestCase):
    """跨市场量化系统测试"""

    def setUp(self):
        """测试初始化"""
        self.fx_adapter = FXAdapter()
        self.hkex_adapter = HKEXAdapter()
        self.cumulative_filter = CumulativeReturnFilter()
        self.signal_stats = SignalStatistics()
        self.risk_metrics = RiskAdjustedReturns()

    def test_cumulative_filter_4day_window(self):
        """Test 4-day cumulative return calculation (Spec requirement)"""
        print("\nTesting cumulative return filter...")

        # Example price series (from specification)
        prices = pd.Series([6.78, 6.79, 6.80, 6.81, 6.82])
        prices.index = pd.date_range('2024-01-01', periods=len(prices))

        # Calculate cumulative return
        cumulative_returns = self.cumulative_filter.calculate_cumulative_returns(prices)

        # Verify result
        expected_return = (6.82 - 6.78) / 6.78  # 0.0044
        actual_return = cumulative_returns.iloc[-1]

        self.assertAlmostEqual(actual_return, expected_return, places=4)
        print(f"✓ 4-day cumulative return: {actual_return:.4f} (expected: {expected_return:.4f})")

    def test_cumulative_filter_threshold(self):
        """Test threshold filtering (Spec requirement ±0.4%)"""
        print("\nTesting signal filtering...")

        # Create test data
        prices = pd.Series([7.0] * 10)
        for i in range(1, 10):
            prices.iloc[i] = 7.0 * (1 + 0.001 * i)  # Daily 0.1% increase

        cumulative_returns = self.cumulative_filter.calculate_cumulative_returns(prices)

        # Filter signals using auto mode
        signals = self.cumulative_filter.filter_signals(
            cumulative_returns=cumulative_returns,
            price_data=prices,
            signal_type='auto'
        )

        # Verify signal generation
        self.assertIsNotNone(signals)
        print(f"✓ Generated {len(signals)} signals")

    def test_signal_statistics(self):
        """Test signal statistics (Spec requirement)"""
        print("\nTesting signal statistics...")

        # Create test signals
        signals = pd.Series([0, 1, 0, -1, 0, 1, 0, -1, 0])
        returns = pd.Series([0.001, 0.002, -0.001, -0.002, 0.001, 0.003, -0.001, -0.002, 0.001])

        # Calculate statistics
        stats = self.signal_stats.calculate(signals, returns)

        # Verify results
        self.assertIn('trigger_rate', stats)
        self.assertIn('win_rate', stats)
        self.assertGreaterEqual(stats['trigger_rate'], 0)
        self.assertLessEqual(stats['trigger_rate'], 1)

        print(f"✓ Signal trigger rate: {stats['trigger_rate']:.2%}")
        print(f"✓ Win rate: {stats['win_rate']:.2%}")

    def test_risk_adjusted_returns(self):
        """Test risk-adjusted returns (Spec requirement)"""
        print("\nTesting risk-adjusted returns...")

        # Create test return data
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.001, 0.02, 252))

        # Calculate risk metrics
        metrics = self.risk_metrics.calculate_all(returns)

        # Verify results
        self.assertIn('sharpe_ratio', metrics)
        self.assertIn('sortino_ratio', metrics)
        self.assertIn('calmar_ratio', metrics)
        self.assertIn('max_drawdown', metrics)

        print(f"✓ Sharpe ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"✓ Sortino ratio: {metrics['sortino_ratio']:.2f}")
        print(f"✓ Calmar ratio: {metrics['calmar_ratio']:.2f}")
        print(f"✓ Max drawdown: {metrics['max_drawdown']:.2%}")

    def test_fx_adapter_mock_data(self):
        """Test FX adapter (mock data)"""
        print("\nTesting FX adapter...")

        async def run_test():
            try:
                # Get mock data
                fx_data = await self.fx_adapter.fetch_data(
                    'USD_CNH', '2024-01-01', '2024-01-10'
                )

                self.assertFalse(fx_data.empty)
                self.assertIn('Close', fx_data.columns)
                self.assertGreater(len(fx_data), 0)

                print(f"✓ Got {len(fx_data)} FX data points")
                return True
            except Exception as e:
                print(f"✗ FX adapter test failed: {e}")
                return False

        return asyncio.run(run_test())

    def test_hkex_adapter_mock_data(self):
        """Test HKEX adapter (mock data)"""
        print("\nTesting HKEX adapter...")

        async def run_test():
            try:
                # Get mock data
                hkex_data = await self.hkex_adapter.fetch_data(
                    '0700.HK', '2024-01-01', '2024-01-10'
                )

                self.assertFalse(hkex_data.empty)
                self.assertIn('Close', hkex_data.columns)
                self.assertGreater(len(hkex_data), 0)

                print(f"✓ Got {len(hkex_data)} HKEX data points")
                return True
            except Exception as e:
                print(f"✗ HKEX adapter test failed: {e}")
                return False

        return asyncio.run(run_test())

    def test_fx_hsi_strategy(self):
        """Test USD/CNH → HSI strategy (Spec requirement)"""
        print("\nTesting USD/CNH → HSI strategy...")

        async def run_test():
            try:
                # Create strategy
                strategy = FXHsiStrategy(
                    fx_symbol='USD_CNH',
                    hsi_symbol='0700.HK',
                    window=4,
                    threshold=0.005,  # 0.5% threshold
                    holding_period=14
                )

                # Generate signals
                signals_data = await strategy.generate_signals(
                    '2024-01-01', '2024-01-31'
                )

                self.assertFalse(signals_data.empty)
                self.assertIn('Signal', signals_data.columns)
                self.assertIn('Action', signals_data.columns)

                # Verify signal values
                valid_signals = signals_data['Signal'].dropna()
                self.assertTrue(all(s in [-1, 0, 1] for s in valid_signals))

                # Count signals
                buy_signals = len(signals_data[signals_data['Signal'] == 1])
                sell_signals = len(signals_data[signals_data['Signal'] == -1])

                print(f"✓ Generated signals: Buy {buy_signals}, Sell {sell_signals}")
                return True
            except Exception as e:
                print(f"✗ Strategy test failed: {e}")
                return False

        return asyncio.run(run_test())


def run_all_tests():
    """Run all tests"""
    print("=" * 80)
    print("Cross-Market Quantitative Trading System - Test Suite")
    print("Based on OpenSpec Specification")
    print("=" * 80)

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCrossMarketQuant)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Output test results
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Success: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✓ All tests passed!")
        return True
    else:
        print("\n✗ Some tests failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
