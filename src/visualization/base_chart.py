"""
Base interfaces for the Visualization Tools Layer.

This module defines the standard interfaces for charts, dashboards, and reports.

Author: Claude Code
Date: 2025-10-25
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import pandas as pd


@dataclass
class ChartConfig:
    """Configuration for chart generation."""
    title: str
    x_label: str
    y_label: str
    chart_type: str  # 'line', 'bar', 'candlestick', etc.
    date_range: tuple  # (start_date, end_date)
    show_grid: bool = True
    show_legend: bool = True
    width: int = 1200
    height: int = 600


class IChartBuilder(ABC):
    """
    Interface for chart builders.

    All chart implementations must follow this interface to work
    with the unified visualization system.

    Typical usage:
        builder = LineChartBuilder()
        config = ChartConfig(title="Stock Price", chart_type='line')
        html = builder.build(data, config)
    """

    @abstractmethod
    def build(self, data: pd.DataFrame, config: ChartConfig) -> str:
        """
        Build a chart from data and configuration.

        Args:
            data: DataFrame with data to visualize
            config: ChartConfig with chart configuration

        Returns:
            HTML string representation of the chart

        Example:
            >>> df = pd.DataFrame(ohlcv_data)
            >>> config = ChartConfig(title="Price Chart", chart_type='line')
            >>> html = builder.build(df, config)
            >>> with open('chart.html', 'w') as f:
            >>>     f.write(html)
        """
        pass

    @abstractmethod
    def get_supported_data_formats(self) -> List[str]:
        """Get list of supported data formats (e.g., 'ohlcv', 'indicators')."""
        pass

    @property
    @abstractmethod
    def chart_type(self) -> str:
        """Type of chart this builder produces."""
        pass


class IAnalyzer(ABC):
    """
    Interface for analysis modules.

    Analyzers compute metrics, detect anomalies, and generate insights.
    """

    @abstractmethod
    def analyze(self, data: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """
        Analyze data and return results.

        Args:
            data: DataFrame to analyze
            **kwargs: Analysis-specific parameters

        Returns:
            Dictionary with analysis results
        """
        pass

    @abstractmethod
    def get_analysis_name(self) -> str:
        """Name of this analysis."""
        pass

    @abstractmethod
    def get_required_columns(self) -> List[str]:
        """Columns required in input data."""
        pass


class IDashboard(ABC):
    """
    Interface for dashboard implementations.

    Dashboards aggregate multiple charts and analyzers into a cohesive view.
    """

    @abstractmethod
    def add_chart(self, name: str, chart_html: str) -> None:
        """Add a chart to the dashboard."""
        pass

    @abstractmethod
    def add_metric(self, name: str, value: str) -> None:
        """Add a metric display to the dashboard."""
        pass

    @abstractmethod
    def render(self) -> str:
        """Render the complete dashboard as HTML."""
        pass

    @abstractmethod
    def save(self, filepath: str) -> None:
        """Save dashboard to HTML file."""
        pass

    @property
    @abstractmethod
    def dashboard_name(self) -> str:
        """Dashboard identifier."""
        pass


class IReportGenerator(ABC):
    """
    Interface for report generation.

    Generates formatted reports with charts, metrics, and analysis.
    """

    @abstractmethod
    def generate(
        self,
        data: pd.DataFrame,
        analysis_results: Dict[str, Any],
        **kwargs
    ) -> str:
        """
        Generate a report.

        Args:
            data: Data to include in report
            analysis_results: Results from analyzers
            **kwargs: Report-specific parameters

        Returns:
            Report HTML string
        """
        pass

    @abstractmethod
    def get_report_format(self) -> str:
        """Report format identifier."""
        pass

    @abstractmethod
    def get_supported_sections(self) -> List[str]:
        """List of sections this report can include."""
        pass
