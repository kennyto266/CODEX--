"""
真實數據回測演示

展示如何使用 HKEXAdapter 和 RealDataBacktester 進行實際回測
"""

import asyncio
import logging
from datetime import date, timedelta
import sys
import os

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加項目路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_adapters.hkex_adapter import HKEXAdapter
from src.backtest.real_data_backtest import (
    RealDataBacktester,
    SimpleMovingAverageStrategy,
    MomentumStrategy
)


async def demo_basic_data_fetching():
    """演示 1: 基本數據獲取"""
    print("\n" + "="*60)
    print("演示 1: 基本 HKEX 數據獲取")
    print("="*60)

    adapter = HKEXAdapter()

    # 連接測試
    print("\n[1] 連接測試...")
    connected = await adapter.connect()
    print(f"  連接狀態: {'✓ 成功' if connected else '✗ 失敗'}")

    if not connected:
        print("無法連接到數據源，終止演示")
        return

    # 獲取單個股票數據
    print("\n[2] 獲取騰訊 (0700.HK) 最近 1 年數據...")
    end_date = date.today()
    start_date = end_date - timedelta(days=365)

    df = await adapter.get_hkex_stock_data("0700.HK", start_date, end_date)

    if not df.empty:
        print(f"  ✓ 成功獲取 {len(df)} 個交易日")
        print(f"\n  數據摘要:")
        print(f"    開盤: {df['open'].iloc[0]:.2f} HKD")
        print(f"    收盤: {df['close'].iloc[-1]:.2f} HKD")
        print(f"    最高: {df['high'].max():.2f} HKD")
        print(f"    最低: {df['low'].min():.2f} HKD")
        print(f"    平均成交量: {df['volume'].mean():,.0f}")

        # 計算漲跌
        price_change = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]
        print(f"    期間漲跌: {price_change:+.2%}")
    else:
        print("  ✗ 無法獲取數據")

    await adapter.disconnect()


async def demo_multiple_stocks():
    """演示 2: 批量獲取多個股票"""
    print("\n" + "="*60)
    print("演示 2: 批量獲取多個 HKEX 股票")
    print("="*60)

    adapter = HKEXAdapter()
    await adapter.connect()

    # 獲取主要成分股列表
    major_stocks = adapter.get_major_stocks()
    print(f"\n恒生指數主要成分股: {len(major_stocks)} 支")

    # 選擇前 3 個進行演示
    selected_stocks = list(major_stocks.items())[:3]
    print(f"演示使用前 3 支:")

    end_date = date.today()
    start_date = end_date - timedelta(days=90)

    for symbol, info in selected_stocks:
        print(f"\n  [{symbol}] {info['name']} ({info['sector']})")

        df = await adapter.get_hkex_stock_data(symbol, start_date, end_date)

        if not df.empty:
            current_price = df['close'].iloc[-1]
            previous_price = df['close'].iloc[0]
            change = (current_price - previous_price) / previous_price

            print(f"    期間: {len(df)} 交易日")
            print(f"    前價格: {previous_price:.2f} HKD")
            print(f"    現價格: {current_price:.2f} HKD")
            print(f"    漲跌: {change:+.2%}")

    await adapter.disconnect()


async def demo_single_stock_backtest():
    """演示 3: 單個股票回測"""
    print("\n" + "="*60)
    print("演示 3: 單個股票策略回測")
    print("="*60)

    backtester = RealDataBacktester(initial_capital=100000)

    # 設置回測參數
    symbol = "0700.HK"  # 騰訊
    end_date = date.today()
    start_date = end_date - timedelta(days=365)

    print(f"\n回測設置:")
    print(f"  股票: {symbol} (騰訊控股)")
    print(f"  期間: {start_date} 到 {end_date}")
    print(f"  初始資本: ¥100,000")

    # 運行簡單移動平均策略
    print(f"\n[1] 運行 SMA(20,50) 策略...")
    sma_results = await backtester.backtest_single_stock(
        symbol,
        SimpleMovingAverageStrategy,
        start_date,
        end_date,
        strategy_name="SMA(20,50)",
        fast_period=20,
        slow_period=50,
        threshold=0.01
    )

    # 生成報告
    print(backtester.generate_report(sma_results))

    # 運行動量策略
    print(f"\n[2] 運行動量策略...")
    momentum_results = await backtester.backtest_single_stock(
        symbol,
        MomentumStrategy,
        start_date,
        end_date,
        strategy_name="Momentum(20)",
        period=20,
        momentum_threshold=0.02
    )

    print(backtester.generate_report(momentum_results))


async def demo_strategy_comparison():
    """演示 4: 多策略對比"""
    print("\n" + "="*60)
    print("演示 4: 多策略對比分析")
    print("="*60)

    backtester = RealDataBacktester(initial_capital=100000)

    symbol = "0700.HK"
    end_date = date.today()
    start_date = end_date - timedelta(days=180)  # 使用較短周期加快演示

    strategies = {
        "SMA_Fast": SimpleMovingAverageStrategy,
        "SMA_Slow": SimpleMovingAverageStrategy,
        "Momentum": MomentumStrategy,
    }

    params = {
        "SMA_Fast": {"fast_period": 10, "slow_period": 30, "threshold": 0.01},
        "SMA_Slow": {"fast_period": 20, "slow_period": 50, "threshold": 0.02},
        "Momentum": {"period": 15, "momentum_threshold": 0.015},
    }

    print(f"\n對比策略: {', '.join(strategies.keys())}")
    print(f"股票: {symbol} (騰訊控股)")
    print(f"期間: {start_date} 到 {end_date}\n")

    results_summary = []

    for strategy_name, strategy_func in strategies.items():
        print(f"[策略] 運行 {strategy_name}...")

        result = await backtester.backtest_single_stock(
            symbol,
            strategy_func,
            start_date,
            end_date,
            strategy_name=strategy_name,
            **params[strategy_name]
        )

        metrics = result.calculate_metrics()
        results_summary.append({
            "strategy": strategy_name,
            "total_return": metrics["total_return"],
            "sharpe_ratio": metrics["sharpe_ratio"],
            "win_rate": metrics["win_rate"],
            "trades": metrics["total_trades"]
        })

    # 打印對比表格
    print("\n" + "="*60)
    print("策略對比結果")
    print("="*60)
    print(f"{'策略':<15} {'總收益':>12} {'Sharpe':>10} {'勝率':>10} {'交易':>8}")
    print("-" * 60)

    for r in results_summary:
        print(
            f"{r['strategy']:<15} "
            f"{r['total_return']:>11.2%} "
            f"{r['sharpe_ratio']:>10.2f} "
            f"{r['win_rate']:>10.1%} "
            f"{r['trades']:>8}"
        )

    # 找出最佳策略
    best_strategy = max(results_summary, key=lambda x: x["total_return"])
    print("-" * 60)
    print(f"🏆 最佳策略: {best_strategy['strategy']} "
          f"(收益 {best_strategy['total_return']:+.2%})")


async def demo_sector_analysis():
    """演示 5: 行業分析"""
    print("\n" + "="*60)
    print("演示 5: 行業性能分析")
    print("="*60)

    adapter = HKEXAdapter()
    await adapter.connect()

    # 獲取所有行業
    sectors = await adapter.get_all_sectors()
    print(f"\n可用行業: {', '.join(sectors)}\n")

    # 分析每個行業的表現
    end_date = date.today()
    start_date = end_date - timedelta(days=90)

    for sector in sectors[:3]:  # 只演示前 3 個行業
        print(f"[{sector}] 行業分析...")

        sector_perf = await adapter.get_sector_performance(sector, start_date, end_date)

        if sector_perf.get("status") == "success":
            print(f"  股票數: {sector_perf['stocks_count']}")
            print(f"  平均收益: {sector_perf['average_return']:+.2%}")
            print(f"  最佳股票: {sector_perf['best_stock']['symbol']} "
                  f"({sector_perf['best_stock']['return']:+.2%})")
            print(f"  最差股票: {sector_perf['worst_stock']['symbol']} "
                  f"({sector_perf['worst_stock']['return']:+.2%})")
        else:
            print(f"  ✗ 無法獲取數據: {sector_perf.get('error')}")

        print()

    await adapter.disconnect()


async def main():
    """主程序"""
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║        HKEX 真實數據回測演示                              ║")
    print("║                                                             ║")
    print("║  本演示展示如何使用真實 HKEX 數據進行量化交易回測          ║")
    print("╚════════════════════════════════════════════════════════════╝")

    try:
        # 演示 1: 基本數據獲取
        await demo_basic_data_fetching()

        # 演示 2: 批量獲取多個股票
        await demo_multiple_stocks()

        # 演示 3: 單個股票回測
        await demo_single_stock_backtest()

        # 演示 4: 多策略對比
        await demo_strategy_comparison()

        # 演示 5: 行業分析
        await demo_sector_analysis()

        print("\n" + "="*60)
        print("✓ 所有演示完成")
        print("="*60 + "\n")

    except Exception as e:
        logger.error(f"演示出錯: {e}", exc_info=True)
        print(f"\n✗ 演示失敗: {e}")


if __name__ == "__main__":
    asyncio.run(main())
