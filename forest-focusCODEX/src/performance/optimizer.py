"""
Parameter sweep optimizer for RSI backtest.

Coordinates parallel execution of multiple RSI window configurations.
"""

import logging
from pathlib import Path
from typing import List, Tuple
from multiprocessing import Pool, cpu_count
from dataclasses import asdict

import pandas as pd

from src.data.loader import load_csv
from src.data.validator import validate_data
from src.indicators.rsi import precompute_rsi_series
from src.strategy.signals import generate_rsi_signals
from src.strategy.backtest_engine import BacktestEngine
from src.performance.metrics import (
    calculate_performance_metrics,
    calculate_buy_and_hold_metrics,
    PerformanceMetrics
)
from src.visualization.equity_curve import plot_equity_curve
from src.visualization.parameter_chart import plot_parameter_sensitivity

logger = logging.getLogger("rsi_backtest.optimizer")


def run_single_backtest(args: tuple) -> PerformanceMetrics:
    """
    Run backtest for a single RSI window configuration.

    This function is designed to be called in parallel via multiprocessing.

    Args:
        args: Tuple of (data, rsi_series, window, buy_threshold, sell_threshold,
                       initial_capital, commission, stamp_duty, risk_free_rate)

    Returns:
        PerformanceMetrics for this configuration
    """
    (data, rsi_series, window, buy_threshold, sell_threshold,
     initial_capital, commission, stamp_duty, risk_free_rate) = args

    # Generate signals
    signals = generate_rsi_signals(rsi_series, buy_threshold, sell_threshold)

    # Run backtest
    engine = BacktestEngine(
        data=data,
        signals=signals,
        initial_capital=initial_capital,
        commission=commission,
        stamp_duty=stamp_duty
    )

    trades, equity_curve = engine.run()

    # Calculate metrics
    metrics = calculate_performance_metrics(
        rsi_window=window,
        equity_curve=equity_curve,
        trades=trades,
        initial_capital=initial_capital,
        risk_free_rate=risk_free_rate
    )

    return metrics


class RSIOptimizer:
    """
    RSI parameter sweep optimizer.

    Manages parallel execution of backtests across multiple RSI windows.
    """

    def __init__(
        self,
        data_path: str,
        start_window: int = 1,
        end_window: int = 300,
        step: int = 1,
        buy_threshold: float = 30.0,
        sell_threshold: float = 70.0,
        initial_capital: float = 100000.0,
        commission: float = 0.0,
        stamp_duty: float = 0.0,
        risk_free_rate: float = 0.02,
        parallel_workers: int = None,
        generate_charts: bool = True
    ):
        """
        Initialize optimizer.

        Args:
            data_path: Path to CSV data file
            start_window: Starting RSI window
            end_window: Ending RSI window
            step: Step size for window sweep
            buy_threshold: RSI buy signal threshold
            sell_threshold: RSI sell signal threshold
            initial_capital: Starting capital
            commission: Commission rate
            stamp_duty: Stamp duty rate (on sells)
            risk_free_rate: Annual risk-free rate
            parallel_workers: Number of parallel processes (None = auto-detect)
            generate_charts: Whether to generate visualization charts
        """
        self.data_path = data_path
        self.start_window = start_window
        self.end_window = end_window
        self.step = step
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.initial_capital = initial_capital
        self.commission = commission
        self.stamp_duty = stamp_duty
        self.risk_free_rate = risk_free_rate

        if parallel_workers is None or parallel_workers == 0:
            self.parallel_workers = max(1, cpu_count() - 1)  # Leave 1 core free
        else:
            self.parallel_workers = parallel_workers

        self.generate_charts = generate_charts

        # Data and results
        self.data: pd.DataFrame = None
        self.rsi_cache: dict = {}
        self.results: List[PerformanceMetrics] = []
        self.baseline_metrics: PerformanceMetrics = None
        self.chart_paths: dict = {}

    def load_and_validate_data(self) -> None:
        """Load and validate input data."""
        logger.info(f"Loading data from {self.data_path}...")
        self.data = load_csv(self.data_path)

        logger.info("Validating data...")
        is_valid, warnings = validate_data(self.data, strict=True)

        if warnings:
            for warning in warnings:
                logger.warning(warning)

    def precompute_rsi(self) -> None:
        """Pre-compute all RSI series for the window range."""
        windows = range(self.start_window, self.end_window + 1, self.step)
        logger.info(f"Pre-computing RSI for windows {self.start_window}-{self.end_window}...")

        self.rsi_cache = precompute_rsi_series(self.data['close'], windows)

        logger.info(f"Pre-computed {len(self.rsi_cache)} RSI series")

    def run_optimization(self) -> None:
        """Run parameter sweep optimization."""
        windows = list(range(self.start_window, self.end_window + 1, self.step))
        total_windows = len(windows)

        logger.info(
            f"Starting optimization: {total_windows} windows, "
            f"{self.parallel_workers} parallel workers"
        )

        # Prepare arguments for parallel execution
        args_list = [
            (
                self.data,
                self.rsi_cache[window],
                window,
                self.buy_threshold,
                self.sell_threshold,
                self.initial_capital,
                self.commission,
                self.stamp_duty,
                self.risk_free_rate
            )
            for window in windows
        ]

        # Run parallel backtests
        with Pool(processes=self.parallel_workers) as pool:
            self.results = pool.map(run_single_backtest, args_list)

        logger.info(f"Optimization complete: {len(self.results)} backtests executed")

    def calculate_baseline(self) -> None:
        """Calculate buy-and-hold baseline metrics."""
        logger.info("Calculating buy-and-hold baseline...")

        self.baseline_metrics = calculate_buy_and_hold_metrics(
            data=self.data,
            initial_capital=self.initial_capital,
            risk_free_rate=self.risk_free_rate
        )

        logger.info(
            f"Baseline Sharpe: {self.baseline_metrics.sharpe_ratio:.4f}, "
            f"Return: {self.baseline_metrics.total_return*100:.2f}%"
        )

    def get_optimal_result(self) -> PerformanceMetrics:
        """Get the optimal result (highest Sharpe ratio)."""
        if not self.results:
            raise ValueError("No results available. Run optimization first.")

        optimal = max(self.results, key=lambda x: x.sharpe_ratio)
        return optimal

    def get_top_n_results(self, n: int = 10) -> List[PerformanceMetrics]:
        """Get top N results by Sharpe ratio."""
        if not self.results:
            return []

        sorted_results = sorted(self.results, key=lambda x: x.sharpe_ratio, reverse=True)
        return sorted_results[:n]

    def generate_charts(self, output_dir: str) -> None:
        """Generate visualization charts."""
        if not self.generate_charts:
            logger.info("Chart generation skipped (--no-charts flag)")
            return

        logger.info("Generating visualization charts...")

        output_path = Path(output_dir)
        charts_dir = output_path / "charts"
        charts_dir.mkdir(parents=True, exist_ok=True)

        # Get optimal result and recalculate its equity curve
        optimal = self.get_optimal_result()

        # Re-run optimal backtest to get equity curve
        rsi_series = self.rsi_cache[optimal.rsi_window]
        signals = generate_rsi_signals(rsi_series, self.buy_threshold, self.sell_threshold)

        engine = BacktestEngine(
            data=self.data,
            signals=signals,
            initial_capital=self.initial_capital,
            commission=self.commission,
            stamp_duty=self.stamp_duty
        )

        _, optimal_equity = engine.run()

        # Calculate baseline equity curve
        baseline_equity = (self.data['close'] / self.data['close'].iloc[0]) * self.initial_capital
        baseline_equity = pd.Series(baseline_equity.values, index=self.data['date'])

        # Generate equity curve chart
        equity_chart_path = plot_equity_curve(
            strategy_equity=optimal_equity,
            baseline_equity=baseline_equity,
            title=f"RSI({optimal.rsi_window}) Strategy vs Buy-and-Hold",
            output_path=str(charts_dir / "equity_curve.png")
        )

        self.chart_paths['equity_curve'] = equity_chart_path

        # Generate parameter sensitivity chart
        param_chart_path = plot_parameter_sensitivity(
            results=self.results,
            optimal_window=optimal.rsi_window,
            output_path=str(charts_dir / "rsi_sharpe_relationship.png")
        )

        self.chart_paths['parameter_sensitivity'] = param_chart_path

        logger.info("Chart generation complete")

    def save_results(self, output_dir: str) -> None:
        """
        Save optimization results to files.

        Args:
            output_dir: Directory to save results
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save all results to CSV
        results_df = pd.DataFrame([asdict(m) for m in self.results])
        results_file = output_path / "optimization_results.csv"
        results_df.to_csv(results_file, index=False)
        logger.info(f"Saved optimization results to {results_file}")

        # Save top 10 results
        top_10 = self.get_top_n_results(10)
        top_10_df = pd.DataFrame([asdict(m) for m in top_10])
        top_10_file = output_path / "top_10_windows.csv"
        top_10_df.to_csv(top_10_file, index=False)
        logger.info(f"Saved top 10 results to {top_10_file}")

        # Generate charts
        self.generate_charts(output_dir)

        # Generate summary report (after charts, so paths are available)
        self.generate_summary_report(output_path)

    def generate_summary_report(self, output_path: Path) -> None:
        """Generate human-readable summary report."""
        optimal = self.get_optimal_result()
        top_10 = self.get_top_n_results(10)

        report_file = output_path / "summary_report.txt"

        with open(report_file, 'w') as f:
            f.write("=" * 60 + "\n")
            f.write("RSI Backtest Optimization Report\n")
            f.write("=" * 60 + "\n\n")

            # Data info
            f.write(f"Stock: {Path(self.data_path).stem}\n")
            f.write(f"Data Period: {self.data['date'].min().date()} to {self.data['date'].max().date()}\n")
            f.write(f"Trading Days: {len(self.data)}\n\n")

            # Configuration
            f.write("Configuration:\n")
            f.write(f"- RSI Windows Tested: {self.start_window}-{self.end_window} (step={self.step})\n")
            f.write(f"- Buy Threshold: RSI < {self.buy_threshold}\n")
            f.write(f"- Sell Threshold: RSI > {self.sell_threshold}\n")
            f.write(f"- Commission: {self.commission*100:.1f}%\n")
            f.write(f"- Stamp Duty: {self.stamp_duty*100:.1f}% (on sells)\n")
            f.write(f"- Risk-Free Rate: {self.risk_free_rate*100:.1f}%\n")
            f.write(f"- Initial Capital: HK${self.initial_capital:,.0f}\n\n")

            # Optimal result
            f.write("Optimal Result:\n")
            f.write(f"- Best RSI Window: {optimal.rsi_window}\n")
            f.write(f"- Sharpe Ratio: {optimal.sharpe_ratio:.4f}\n")
            f.write(f"- Total Return: {optimal.total_return*100:.2f}%\n")
            f.write(f"- Annualized Return: {optimal.annualized_return*100:.2f}%\n")
            f.write(f"- Annual Volatility: {optimal.annualized_volatility*100:.2f}%\n")
            f.write(f"- Max Drawdown: {optimal.max_drawdown*100:.2f}%\n")
            f.write(f"- Win Rate: {optimal.win_rate*100:.1f}%\n")
            f.write(f"- Number of Trades: {optimal.num_trades}\n\n")

            # Top 10
            f.write("Top 10 RSI Windows:\n")
            f.write(f"{'Rank':<6}{'Window':<8}{'Sharpe':<10}{'Return':<10}{'Volatility':<12}{'Drawdown':<10}{'Trades':<8}\n")
            f.write("-" * 60 + "\n")

            for rank, metrics in enumerate(top_10, 1):
                f.write(
                    f"{rank:<6}{metrics.rsi_window:<8}{metrics.sharpe_ratio:<10.4f}"
                    f"{metrics.total_return*100:<10.2f}{metrics.annualized_volatility*100:<12.2f}"
                    f"{metrics.max_drawdown*100:<10.2f}{metrics.num_trades:<8}\n"
                )

            # Baseline comparison
            if self.baseline_metrics:
                f.write("\nBuy-and-Hold Baseline:\n")
                f.write(f"- Total Return: {self.baseline_metrics.total_return*100:.2f}%\n")
                f.write(f"- Sharpe Ratio: {self.baseline_metrics.sharpe_ratio:.4f}\n")
                f.write(f"- Max Drawdown: {self.baseline_metrics.max_drawdown*100:.2f}%\n\n")

                f.write("Strategy vs Baseline:\n")
                ret_diff = (optimal.total_return - self.baseline_metrics.total_return) * 100
                dd_diff = (optimal.max_drawdown - self.baseline_metrics.max_drawdown) * 100
                sharpe_diff = optimal.sharpe_ratio - self.baseline_metrics.sharpe_ratio

                f.write(f"- Return Difference: {ret_diff:+.2f}%\n")
                f.write(f"- Drawdown Difference: {dd_diff:+.2f}%\n")
                f.write(f"- Sharpe Improvement: {sharpe_diff:+.4f}\n\n")

            # Chart paths
            if self.chart_paths:
                f.write("Chart Files:\n")
                for chart_name, chart_path in self.chart_paths.items():
                    f.write(f"- {chart_name}: {chart_path}\n")

            f.write("\n" + "=" * 60 + "\n")

        logger.info(f"Saved summary report to {report_file}")

    def run(self, output_dir: str) -> PerformanceMetrics:
        """
        Run complete optimization workflow.

        Args:
            output_dir: Directory to save results

        Returns:
            Optimal PerformanceMetrics
        """
        self.load_and_validate_data()
        self.precompute_rsi()
        self.run_optimization()
        self.calculate_baseline()
        self.save_results(output_dir)

        optimal = self.get_optimal_result()
        logger.info(f"Optimal RSI window: {optimal.rsi_window} (Sharpe={optimal.sharpe_ratio:.4f})")

        return optimal
