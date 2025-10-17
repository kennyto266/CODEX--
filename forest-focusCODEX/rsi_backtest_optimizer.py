#!/usr/bin/env python
"""
RSI Backtest Optimizer - Main CLI Entry Point

Command-line interface for running RSI parameter sweep optimization.
"""

import argparse
import sys
import logging
from pathlib import Path

from src import setup_logging, __version__
from src.performance.optimizer import RSIOptimizer


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="RSI Backtest Optimizer - Find optimal RSI parameters for trading strategy",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Version
    parser.add_argument(
        '--version',
        action='version',
        version=f'RSI Backtest Optimizer v{__version__}'
    )

    # Data input
    parser.add_argument(
        '--data',
        type=str,
        default='data/0700_HK.csv',
        help='Path to input CSV file containing OHLCV data'
    )

    # RSI window parameters
    parser.add_argument(
        '--start-window',
        type=int,
        default=1,
        help='Starting RSI window for parameter sweep'
    )

    parser.add_argument(
        '--end-window',
        type=int,
        default=300,
        help='Ending RSI window for parameter sweep'
    )

    parser.add_argument(
        '--step',
        type=int,
        default=1,
        help='Step size for window sweep'
    )

    # Signal thresholds
    parser.add_argument(
        '--buy-threshold',
        type=float,
        default=30.0,
        help='RSI level below which to generate BUY signal'
    )

    parser.add_argument(
        '--sell-threshold',
        type=float,
        default=70.0,
        help='RSI level above which to generate SELL signal'
    )

    # Trading costs
    parser.add_argument(
        '--commission',
        type=float,
        default=0.001,
        help='Commission rate (0.001 = 0.1%%)'
    )

    parser.add_argument(
        '--stamp-duty',
        type=float,
        default=0.001,
        help='Stamp duty rate on sells (0.001 = 0.1%%)'
    )

    # Portfolio parameters
    parser.add_argument(
        '--initial-capital',
        type=float,
        default=100000.0,
        help='Starting portfolio value in HKD'
    )

    parser.add_argument(
        '--risk-free-rate',
        type=float,
        default=0.02,
        help='Annual risk-free rate for Sharpe calculation (0.02 = 2%%)'
    )

    # Output
    parser.add_argument(
        '--output-dir',
        type=str,
        default='results',
        help='Directory for output files'
    )

    parser.add_argument(
        '--no-charts',
        action='store_true',
        help='Skip chart generation (faster for testing)'
    )

    # Performance
    parser.add_argument(
        '--parallel-workers',
        type=int,
        default=None,
        help='Number of parallel processes (0 = auto-detect cores)'
    )

    # Logging
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output (same as --log-level DEBUG)'
    )

    return parser.parse_args()


def validate_arguments(args: argparse.Namespace) -> None:
    """
    Validate command-line arguments.

    Args:
        args: Parsed arguments

    Raises:
        ValueError: If validation fails
    """
    # Window validation
    if args.start_window < 1:
        raise ValueError(f"start-window must be >= 1, got {args.start_window}")

    if args.end_window > 500:
        raise ValueError(f"end-window must be <= 500, got {args.end_window}")

    if args.start_window >= args.end_window:
        raise ValueError(
            f"start-window ({args.start_window}) must be < end-window ({args.end_window})"
        )

    if args.step < 1:
        raise ValueError(f"step must be >= 1, got {args.step}")

    # Threshold validation
    if args.buy_threshold >= args.sell_threshold:
        raise ValueError(
            f"buy-threshold ({args.buy_threshold}) must be < sell-threshold ({args.sell_threshold})"
        )

    if not (0 <= args.buy_threshold <= 100):
        raise ValueError(f"buy-threshold must be in [0, 100], got {args.buy_threshold}")

    if not (0 <= args.sell_threshold <= 100):
        raise ValueError(f"sell-threshold must be in [0, 100], got {args.sell_threshold}")

    # Cost validation
    if not (0 <= args.commission <= 0.1):
        raise ValueError(f"commission must be in [0, 0.1], got {args.commission}")

    if not (0 <= args.stamp_duty <= 0.1):
        raise ValueError(f"stamp-duty must be in [0, 0.1], got {args.stamp_duty}")

    # Portfolio validation
    if args.initial_capital <= 0:
        raise ValueError(f"initial-capital must be > 0, got {args.initial_capital}")

    if not (0 <= args.risk_free_rate <= 1.0):
        raise ValueError(f"risk-free-rate must be in [0, 1.0], got {args.risk_free_rate}")

    # File validation
    data_path = Path(args.data)
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code (0 = success, non-zero = error)
    """
    try:
        # Parse arguments
        args = parse_arguments()

        # Setup logging
        log_level = 'DEBUG' if args.verbose else args.log_level
        setup_logging(log_level=log_level)

        logger = logging.getLogger("rsi_backtest")
        logger.info(f"RSI Backtest Optimizer v{__version__}")

        # Validate arguments
        validate_arguments(args)

        # Print configuration
        logger.info("Configuration:")
        logger.info(f"  Data: {args.data}")
        logger.info(f"  RSI Windows: {args.start_window}-{args.end_window} (step={args.step})")
        logger.info(f"  Thresholds: Buy<{args.buy_threshold}, Sell>{args.sell_threshold}")
        logger.info(f"  Costs: Commission={args.commission*100:.1f}%, Stamp Duty={args.stamp_duty*100:.1f}%")
        logger.info(f"  Initial Capital: HK${args.initial_capital:,.0f}")
        logger.info(f"  Output: {args.output_dir}")

        # Create optimizer
        optimizer = RSIOptimizer(
            data_path=args.data,
            start_window=args.start_window,
            end_window=args.end_window,
            step=args.step,
            buy_threshold=args.buy_threshold,
            sell_threshold=args.sell_threshold,
            initial_capital=args.initial_capital,
            commission=args.commission,
            stamp_duty=args.stamp_duty,
            risk_free_rate=args.risk_free_rate,
            parallel_workers=args.parallel_workers,
            generate_charts=not args.no_charts
        )

        # Run optimization
        optimal = optimizer.run(output_dir=args.output_dir)

        # Print results
        print("\n" + "=" * 60)
        print("Optimization Complete!")
        print("=" * 60)
        print(f"Optimal RSI Window: {optimal.rsi_window}")
        print(f"Sharpe Ratio: {optimal.sharpe_ratio:.4f}")
        print(f"Total Return: {optimal.total_return*100:.2f}%")
        print(f"Max Drawdown: {optimal.max_drawdown*100:.2f}%")
        print(f"Win Rate: {optimal.win_rate*100:.1f}%")
        print(f"Number of Trades: {optimal.num_trades}")
        print(f"\nResults saved to: {args.output_dir}/")
        print("=" * 60)

        logger.info("Backtest completed successfully")
        return 0

    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 4

    except ValueError as e:
        print(f"ERROR: Configuration error: {e}", file=sys.stderr)
        return 5

    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        logging.exception("Unexpected error during backtest")
        return 1


if __name__ == '__main__':
    sys.exit(main())
