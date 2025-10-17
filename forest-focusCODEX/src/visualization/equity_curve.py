"""
Equity curve visualization module.

Generates cumulative returns chart comparing strategy vs buy-and-hold.
"""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

logger = logging.getLogger("rsi_backtest.visualization.equity_curve")


def plot_equity_curve(
    strategy_equity: pd.Series,
    baseline_equity: pd.Series,
    title: str = "RSI Strategy vs Buy-and-Hold",
    output_path: str = None,
    dpi: int = 150,
    figsize: tuple = (12, 8)
) -> str:
    """
    Plot equity curve comparing strategy vs baseline.

    Args:
        strategy_equity: Strategy equity curve (datetime index)
        baseline_equity: Buy-and-hold equity curve (datetime index)
        title: Chart title
        output_path: Path to save chart (if None, auto-generate)
        dpi: Chart resolution
        figsize: Figure size in inches (width, height)

    Returns:
        Path to saved chart file
    """
    # Set style
    sns.set_style("whitegrid")

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Plot equity curves
    ax.plot(
        strategy_equity.index,
        strategy_equity.values,
        label='RSI Strategy',
        linewidth=2,
        color='#2E86DE'
    )

    ax.plot(
        baseline_equity.index,
        baseline_equity.values,
        label='Buy & Hold',
        linewidth=2,
        alpha=0.7,
        color='#EE5A24'
    )

    # Labels and formatting
    ax.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax.set_ylabel('Portfolio Value (HKD)', fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

    # Legend
    ax.legend(fontsize=11, loc='best', framealpha=0.9)

    # Grid
    ax.grid(True, alpha=0.3, linestyle='--')

    # Format y-axis as currency
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

    # Tight layout
    fig.tight_layout()

    # Save
    if output_path is None:
        output_path = Path("results/charts/equity_curve.png")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig.savefig(output_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)

    logger.info(f"Equity curve chart saved to {output_path}")

    return str(output_path)
