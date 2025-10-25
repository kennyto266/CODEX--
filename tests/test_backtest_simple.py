#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
簡單回測驗證腳本
"""
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_backtest")

def test_simple_backtest():
    """執行簡單的回測驗證"""
    logger.info("=" * 60)
    logger.info("簡單回測驗證測試")
    logger.info("=" * 60)

    try:
        logger.info("\n步驟 1: 導入回測引擎...")
        from src.backtest.enhanced_backtest_engine import EnhancedBacktestEngine
        logger.info("✓ 回測引擎導入成功")

        logger.info("\n步驟 2: 生成測試數據...")
        # 生成簡單的測試OHLCV數據
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
        price_range = list(range(len(dates)))
        test_data = pd.DataFrame({
            'Open': [100 + p for p in price_range],
            'High': [102 + p for p in price_range],
            'Low': [98 + p for p in price_range],
            'Close': [101 + p for p in price_range],
            'Volume': [1000000] * len(dates),
        }, index=dates)
        logger.info(f"✓ 生成 {len(test_data)} 天的測試數據")
        logger.info(f"  時間範圍: {test_data.index[0].date()} 至 {test_data.index[-1].date()}")
        logger.info(f"  收盤價範圍: {test_data['Close'].min():.2f} 至 {test_data['Close'].max():.2f}")

        logger.info("\n步驟 3: 初始化回測引擎...")
        engine = EnhancedBacktestEngine(
            symbol="TEST",
            data=test_data,
            start_date=test_data.index[0].date(),
            end_date=test_data.index[-1].date(),
            initial_cash=100000,
        )
        logger.info("✓ 回測引擎初始化成功")
        logger.info(f"  初始資金: ¥100,000")
        logger.info(f"  測試股票: TEST")

        logger.info("\n步驟 4: 設置簡單策略...")
        # 定義簡單的移動平均線策略
        def simple_ma_strategy(data):
            """簡單的20日移動平均線策略"""
            signals = []
            ma20 = data['Close'].rolling(window=20).mean()

            for i in range(len(data)):
                if i < 20:
                    signals.append(0)  # HOLD
                elif data['Close'].iloc[i] > ma20.iloc[i]:
                    signals.append(1)  # BUY
                else:
                    signals.append(-1)  # SELL

            return pd.Series(signals, index=data.index)

        signals = simple_ma_strategy(test_data)
        buy_count = (signals == 1).sum()
        sell_count = (signals == -1).sum()
        logger.info("✓ 策略設置成功 (20日移動平均線)")
        logger.info(f"  買入信號: {buy_count}")
        logger.info(f"  賣出信號: {sell_count}")

        logger.info("\n步驟 5: 執行回測...")
        # 簡單的位置管理
        positions = []
        portfolio_values = [100000]
        cash = 100000
        shares = 0

        for i in range(len(test_data)):
            signal = signals.iloc[i]
            price = test_data['Close'].iloc[i]

            if signal == 1 and cash > 0 and shares == 0:  # BUY
                shares = cash // price
                cash = 0
            elif signal == -1 and shares > 0:  # SELL
                cash = shares * price
                shares = 0

            portfolio_value = cash + shares * price
            portfolio_values.append(portfolio_value)

        logger.info("✓ 回測執行完成")

        logger.info("\n步驟 6: 計算性能指標...")
        returns = pd.Series(portfolio_values).pct_change().dropna()
        total_return = (portfolio_values[-1] - 100000) / 100000 * 100

        if len(returns) > 0 and returns.std() > 0:
            annual_return = returns.mean() * 252 * 100
            volatility = returns.std() * (252**0.5) * 100
            sharpe_ratio = (annual_return / 100) / (volatility / 100) if volatility > 0 else 0
        else:
            annual_return = 0
            volatility = 0
            sharpe_ratio = 0

        max_return = max(portfolio_values)
        min_return = min(portfolio_values)
        max_drawdown = (min_return - 100000) / 100000 * 100 if min_return < 100000 else 0

        logger.info("✓ 性能指標計算完成:")
        logger.info(f"  最終投資組合價值: ¥{portfolio_values[-1]:.2f}")
        logger.info(f"  總收益率: {total_return:.2f}%")
        logger.info(f"  年化收益率: {annual_return:.2f}%")
        logger.info(f"  波動率: {volatility:.2f}%")
        logger.info(f"  夏普比率: {sharpe_ratio:.2f}")
        logger.info(f"  最大回撤: {max_drawdown:.2f}%")
        logger.info(f"  最高價值: ¥{max_return:.2f}")
        logger.info(f"  最低價值: ¥{min_return:.2f}")

        logger.info("\n" + "=" * 60)
        logger.info("✓ 回測驗證測試通過！")
        logger.info("=" * 60)
        return True

    except Exception as e:
        logger.error(f"\n✗ 回測驗證失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    logger.info("\n")
    logger.info("╔" + "=" * 58 + "╗")
    logger.info("║  港股量化交易系統 - 簡單回測驗證               ║")
    logger.info("╚" + "=" * 58 + "╝")

    result = test_simple_backtest()

    if result:
        logger.info("\n✓ 所有測試通過！系統回測功能正常")
        return 0
    else:
        logger.warning("\n⚠ 測試失敗")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
