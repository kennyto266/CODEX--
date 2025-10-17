"""
Parameter sensitivity visualization module.

Generates scatter plot showing RSI window vs Sharpe ratio relationship.
"""

import logging
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import seaborn as sns

from src.performance.metrics import PerformanceMetrics

logger = logging.getLogger("rsi_backtest.visualization.parameter_chart")


def plot_parameter_sensitivity(
    results: List[PerformanceMetrics],
    optimal_window: int,
    title: str = "Parameter Sensitivity: RSI Window vs Sharpe Ratio",
    output_path: str = None,
    dpi: int = 150,
    figsize: tuple = (12, 8)
) -> str:
    """
    Plot parameter sensitivity scatter chart.

    Args:
        results: List of PerformanceMetrics for all tested windows
        optimal_window: Optimal RSI window to highlight
        title: Chart title
        output_path: Path to save chart (if None, auto-generate)
        dpi: Chart resolution
        figsize: Figure size in inches

    Returns:
        Path to saved chart file
    """
    # Extract data
    windows = [m.rsi_window for m in results]
    sharpe_ratios = [m.sharpe_ratio for m in results]

    # Set style
    sns.set_style("whitegrid")

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Scatter plot
    ax.scatter(
        windows,
        sharpe_ratios,
        alpha=0.6,
        s=50,
        color='#2E86DE',
        edgecolors='white',
        linewidths=0.5
    )

    # Highlight optimal window
    optimal_sharpe = next(m.sharpe_ratio for m in results if m.rsi_window == optimal_window)

    ax.axvline(
        x=optimal_window,
        color='#EE5A24',
        linestyle='--',
        linewidth=2,
        label=f'Optimal: RSI({optimal_window}), Sharpe={optimal_sharpe:.4f}',
        alpha=0.8
    )

    # Horizontal line at Sharpe=0
    ax.axhline(
        y=0,
        color='gray',
        linestyle='-',
        linewidth=1,
        alpha=0.5
    )

    # Labels and formatting
    ax.set_xlabel('RSI Window (days)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Sharpe Ratio', fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

    # Legend
    ax.legend(fontsize=11, loc='best', framealpha=0.9)

    # Grid
    ax.grid(True, alpha=0.3, linestyle='--')

    # Tight layout
    fig.tight_layout()

    # Save
    if output_path is None:
        output_path = Path("results/charts/rsi_sharpe_relationship.png")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig.savefig(output_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)

    logger.info(f"Parameter sensitivity chart saved to {output_path}")

    return str(output_path)
