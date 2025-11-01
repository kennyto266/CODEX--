"""
Quick HKEX Backtest Demo
Quick start real data backtesting with default parameters
"""

import asyncio
import sys
import os
from datetime import date, timedelta

# Fix encoding for Windows
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_adapters.hkex_adapter import HKEXAdapter
from src.backtest.real_data_backtest import RealDataBacktester, SimpleMovingAverageStrategy


async def quick_demo():
    """Quick demonstration"""

    print("\n" + "="*60)
    print("    QUICK HKEX BACKTEST DEMO")
    print("="*60 + "\n")

    # STEP 1: Get Real Data
    print("STEP 1: Fetch Real HKEX Data")
    print("-" * 60)

    adapter = HKEXAdapter()
    connected = await adapter.connect()

    if not connected:
        print("[ERROR] Cannot connect to data source")
        return

    print("[OK] Connected to Yahoo Finance API\n")

    # Get Tencent stock data
    symbol = "0700.HK"  # Tencent
    end_date = date.today()
    start_date = end_date - timedelta(days=365)

    print(f"Fetching {symbol} (Tencent) 1-year historical data...")
    df = await adapter.get_hkex_stock_data(symbol, start_date, end_date)

    if df.empty:
        print("[ERROR] Cannot fetch data")
        return

    print(f"[OK] Got {len(df)} trading days\n")

    # Show data summary
    print("Data Summary:")
    print(f"  * Opening price: {df['open'].iloc[0]:.2f} HKD")
    print(f"  * Current price: {df['close'].iloc[-1]:.2f} HKD")
    print(f"  * Year high: {df['high'].max():.2f} HKD")
    print(f"  * Year low: {df['low'].min():.2f} HKD")
    print(f"  * Avg volume: {df['volume'].mean():,.0f}\n")

    # STEP 2: Run Backtest
    print("STEP 2: Execute SMA Strategy Backtest")
    print("-" * 60)

    backtester = RealDataBacktester(initial_capital=100000)

    print("Running SMA(20,50) strategy...")
    print("  * Initial capital: 100,000 HKD")
    print("  * Fast MA period: 20")
    print("  * Slow MA period: 50")
    print("  * Signal threshold: 1%\n")

    results = await backtester.backtest_single_stock(
        symbol=symbol,
        strategy_func=SimpleMovingAverageStrategy,
        start_date=start_date,
        end_date=end_date,
        strategy_name="SMA(20,50)",
        fast_period=20,
        slow_period=50,
        threshold=0.01
    )

    # STEP 3: Show Results
    print("STEP 3: Backtest Results")
    print("-" * 60)

    metrics = results.calculate_metrics()

    print("\nPerformance Metrics:")
    print(f"  * Total Return: {metrics['total_return']:+.2%}")
    print(f"  * Final Capital: {metrics['final_capital']:,.0f} HKD")
    print(f"  * Sharpe Ratio: {metrics['sharpe_ratio']:.4f}")
    print(f"  * Max Drawdown: {metrics['max_drawdown']:.2%}")

    print("\nTrading Statistics:")
    print(f"  * Total Trades: {metrics['total_trades']}")
    print(f"  * Winning Trades: {metrics['winning_trades']}")
    print(f"  * Losing Trades: {metrics['losing_trades']}")
    print(f"  * Win Rate: {metrics['win_rate']:.2%}")

    print("\nProfit/Loss Statistics:")
    print(f"  * Avg Trade P&L: {metrics['avg_pnl']:+,.0f} HKD")
    print(f"  * Best Trade: {metrics['best_trade']:+,.0f} HKD")
    print(f"  * Worst Trade: {metrics['worst_trade']:+,.0f} HKD")
    print(f"  * Total P&L: {metrics['total_pnl']:+,.0f} HKD")

    # STEP 4: Recent Trades
    if results.trades:
        print(f"\nRecent Trades (Total: {len(results.trades)})")
        print("-" * 60)

        # Show first 10 trades
        for i, trade in enumerate(results.trades[:10]):
            print(f"  {i+1}. [{trade['signal']}] "
                  f"{trade['date'].strftime('%Y-%m-%d')} "
                  f"@ {trade['price']:.2f} HKD "
                  f"(qty={trade['quantity']}, "
                  f"p&l={trade['pnl']:+,.0f})")

        if len(results.trades) > 10:
            print(f"  ... {len(results.trades) - 10} more trades")

    # Conclusion
    print("\n" + "="*60)
    print("[DONE] Backtest Complete!")
    print("="*60)

    # Evaluation
    if metrics['total_return'] > 0:
        status = "[PROFIT]"
    else:
        status = "[LOSS]"

    print(f"\nResult: {status} {metrics['total_return']:+.2%}\n")

    await adapter.disconnect()


if __name__ == "__main__":
    asyncio.run(quick_demo())
