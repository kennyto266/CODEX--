#!/usr/bin/env python3
"""
Python bindings demo for rust-nonprice

This script demonstrates the Python API for the rust-nonprice library.
"""

import sys
from datetime import datetime, date

try:
    import rust_nonprice
except ImportError:
    print("Error: rust_nonprice module not found. Please build the Python bindings first:")
    print("  cd python && maturin build --release && pip install target/wheels/*.whl")
    sys.exit(1)


def demo_nonprice_indicators():
    """Demonstrate NonPriceIndicator class"""
    print("\n=== NonPriceIndicator Demo ===")

    # Create indicators
    hibor_1m = rust_nonprice.PyNonPriceIndicator(
        symbol="HIBOR_1M",
        date="2025-01-01",
        value=3.45,
        source="HKMA"
    )

    visitor_count = rust_nonprice.PyNonPriceIndicator(
        symbol="VISITOR_COUNT",
        date="2025-01-01",
        value=450000,
        source="HKTB"
    )

    print(f"HIBOR 1M: {hibor_1m.value} from {hibor_1m.source}")
    print(f"Visitor Count: {visitor_count.value} from {visitor_count.source}")


def demo_technical_indicators():
    """Demonstrate TechnicalIndicator class"""
    print("\n=== TechnicalIndicator Demo ===")

    # Create technical indicators
    zscore = rust_nonprice.PyTechnicalIndicator(
        symbol="0700.HK",
        date="2025-01-01",
        indicator_type="ZSCORE",
        window_size=20,
        value=1.5
    )

    rsi = rust_nonprice.PyTechnicalIndicator(
        symbol="0700.HK",
        date="2025-01-01",
        indicator_type="RSI",
        window_size=14,
        value=65.5
    )

    print(f"Z-Score: {zscore.value} (window: {zscore.window_size})")
    print(f"RSI: {rsi.value} (window: {rsi.window_size})")


def demo_trading_signals():
    """Demonstrate TradingSignal class"""
    print("\n=== TradingSignal Demo ===")

    # Create trading signals
    buy_signal = rust_nonprice.PyTradingSignal(
        symbol="0700.HK",
        date="2025-01-01",
        action="BUY",
        strength=0.85
    )

    sell_signal = rust_nonprice.PyTradingSignal(
        symbol="0700.HK",
        date="2025-01-02",
        action="SELL",
        strength=0.75
    )

    print(f"Signal 1: {buy_signal.action()} on {buy_signal.date()}")
    print(f"  Strength: {buy_signal.strength()}, Confidence: {buy_signal.confidence()}")
    print(f"Signal 2: {sell_signal.action()} on {sell_signal.date()}")
    print(f"  Strength: {sell_signal.strength()}, Confidence: {sell_signal.confidence()}")


def demo_parameter_set():
    """Demonstrate ParameterSet class"""
    print("\n=== ParameterSet Demo ===")

    # Create parameter set
    params = rust_nonprice.PyParameterSet(
        indicator_name="HIBOR_ZSCORE",
        zscore_buy=-0.5,
        zscore_sell=0.5,
        rsi_buy=25.0,
        rsi_sell=65.0,
        sma_fast=10,
        sma_slow=30
    )

    print(f"Parameter Set: {params.indicator_name()}")
    print(f"  ID: {params.id()}")
    print(f"  Z-Score: buy={params.zscore_buy()}, sell={params.zscore_sell()}")
    print(f"  RSI: buy={params.rsi_buy()}, sell={params.rsi_sell()}")
    print(f"  SMA: fast={params.sma_fast()}, slow={params.sma_slow()}")


def demo_backtest_engine():
    """Demonstrate BacktestEngine class"""
    print("\n=== BacktestEngine Demo ===")

    # Create backtest engine
    engine = rust_nonprice.PyBacktestEngine(
        initial_capital=1000000.0,
        commission=0.001
    )

    # Create sample signals
    signals = [
        rust_nonprice.PyTradingSignal("0700.HK", "2025-01-01", "BUY", 0.85),
        rust_nonprice.PyTradingSignal("0700.HK", "2025-01-02", "HOLD", 0.50),
        rust_nonprice.PyTradingSignal("0700.HK", "2025-01-03", "SELL", 0.75),
    ]

    # Create sample stock data
    stock_data = [
        "2025-01-01,380.0",
        "2025-01-02,385.0",
        "2025-01-03,382.0",
    ]

    # Run backtest
    result = engine.run_backtest(signals, stock_data)
    print(f"Backtest Result: {result}")


def demo_parameter_optimizer():
    """Demonstrate ParameterOptimizer class"""
    print("\n=== ParameterOptimizer Demo ===")

    # Create optimizer
    optimizer = rust_nonprice.PyParameterOptimizer(
        metric="SHARPE",
        max_iterations=100
    )

    # Create sample data
    indicators = [
        rust_nonprice.PyNonPriceIndicator("HIBOR_1M", "2025-01-01", 3.45, "HKMA"),
        rust_nonprice.PyNonPriceIndicator("HIBOR_1M", "2025-01-02", 3.50, "HKMA"),
        rust_nonprice.PyNonPriceIndicator("HIBOR_1M", "2025-01-03", 3.48, "HKMA"),
    ]

    # Optimize parameters
    optimized_params = optimizer.optimize(indicators)
    print(f"Optimized Parameters:")
    print(f"  Indicator: {optimized_params.indicator_name()}")
    print(f"  Z-Score: buy={optimized_params.zscore_buy()}, sell={optimized_params.zscore_sell()}")


def demo_report_generator():
    """Demonstrate ReportGenerator class"""
    print("\n=== ReportGenerator Demo ===")

    # Create report generator
    generator = rust_nonprice.PyReportGenerator()

    # Generate markdown report
    result = "Sample backtest result"
    md_path = "/tmp/backtest_report.md"
    md_msg = generator.generate_markdown(result, md_path)
    print(f"Markdown: {md_msg}")

    # Generate JSON report
    json_path = "/tmp/backtest_report.json"
    json_msg = generator.generate_json(result, json_path)
    print(f"JSON: {json_msg}")


def main():
    """Run all demos"""
    print("=" * 60)
    print("Rust-NonPrice Python Bindings Demo")
    print("=" * 60)

    try:
        demo_nonprice_indicators()
        demo_technical_indicators()
        demo_trading_signals()
        demo_parameter_set()
        demo_backtest_engine()
        demo_parameter_optimizer()
        demo_report_generator()

        print("\n" + "=" * 60)
        print("All demos completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
