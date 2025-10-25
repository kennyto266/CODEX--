"""
Alternative Data Dashboard Views

Provides visualization components for correlation analysis and alternative data insights.

Features:
    - Correlation heatmap visualization
    - Time series overlay charts
    - Rolling correlation trends
    - Indicator summary tables
    - Interactive filtering
    - Dashboard-compatible data formatting

Usage:
    from src.dashboard.alternative_data_views import AlternativeDataDashboard

    dashboard = AlternativeDataDashboard()

    # Get correlation heatmap data
    heatmap_data = dashboard.get_correlation_heatmap(
        correlation_matrix,
        title="HIBOR vs Bank Stocks"
    )

    # Get time series chart data
    timeseries = dashboard.get_timeseries_overlay(
        alt_data, stock_prices,
        alt_name="HIBOR", stock_name="0939.HK"
    )

    # Get rolling correlation chart
    rolling_chart = dashboard.get_rolling_correlation_chart(
        rolling_correlation_series,
        title="60-Day Rolling Correlation"
    )
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

import pandas as pd
import numpy as np

logger = logging.getLogger("hk_quant_system.alternative_data_views")


class AlternativeDataDashboard:
    """
    Dashboard visualization generator for alternative data analysis.

    Creates data structures compatible with dashboard charting libraries
    (Chart.js, Plotly, etc.) from correlation analysis results.
    """

    def __init__(self):
        """Initialize AlternativeDataDashboard."""
        logger.info("Initialized AlternativeDataDashboard")

    def get_correlation_heatmap(
        self,
        correlation_matrix: pd.DataFrame,
        p_values: Optional[pd.DataFrame] = None,
        title: str = "Correlation Matrix",
    ) -> Dict[str, Any]:
        """
        Generate correlation heatmap data.

        Args:
            correlation_matrix: DataFrame with correlations
            p_values: Optional DataFrame with p-values
            title: Chart title

        Returns:
            Dashboard-compatible heatmap data
        """
        if correlation_matrix.empty:
            logger.warning("Empty correlation matrix provided")
            return None

        # Prepare data for heatmap
        heatmap_data = {
            "type": "heatmap",
            "title": title,
            "generated_at": datetime.now().isoformat(),
            "data": {
                "labels": {
                    "x": list(correlation_matrix.columns),
                    "y": list(correlation_matrix.index),
                },
                "values": correlation_matrix.values.tolist(),
            },
            "scale": {
                "min": -1.0,
                "max": 1.0,
                "mid": 0.0,
            },
            "colorScale": [
                {"value": -1.0, "color": "#d73027"},  # Red for negative
                {"value": -0.5, "color": "#fc8d59"},
                {"value": 0.0, "color": "#ffffbf"},   # Yellow for neutral
                {"value": 0.5, "color": "#91bfdb"},
                {"value": 1.0, "color": "#4575b4"},   # Blue for positive
            ],
        }

        # Add statistical significance if provided
        if p_values is not None:
            heatmap_data["p_values"] = p_values.values.tolist()
            heatmap_data["significance_threshold"] = 0.05

        logger.info(f"Generated heatmap: {title}")
        return heatmap_data

    def get_timeseries_overlay(
        self,
        alt_data: pd.Series,
        stock_data: pd.Series,
        alt_name: str = "Indicator",
        stock_name: str = "Stock",
        normalize: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate time series overlay chart data.

        Args:
            alt_data: Alternative data time series
            stock_data: Stock price/return time series
            alt_name: Name for alternative data
            stock_name: Name for stock
            normalize: Normalize both series to [0, 1] for comparison

        Returns:
            Dashboard-compatible time series data
        """
        if alt_data.empty or stock_data.empty:
            logger.warning("Empty data provided")
            return None

        # Align data
        common_dates = alt_data.index.intersection(stock_data.index)
        alt_aligned = alt_data.loc[common_dates]
        stock_aligned = stock_data.loc[common_dates]

        # Normalize if requested
        if normalize:
            alt_min, alt_max = alt_aligned.min(), alt_aligned.max()
            stock_min, stock_max = stock_aligned.min(), stock_aligned.max()

            if alt_max > alt_min:
                alt_normalized = (alt_aligned - alt_min) / (alt_max - alt_min)
            else:
                alt_normalized = alt_aligned.copy()

            if stock_max > stock_min:
                stock_normalized = (stock_aligned - stock_min) / (stock_max - stock_min)
            else:
                stock_normalized = stock_aligned.copy()

            alt_series = alt_normalized
            stock_series = stock_normalized
        else:
            alt_series = alt_aligned
            stock_series = stock_aligned

        # Format for dashboard
        timeseries_data = {
            "type": "timeseries_overlay",
            "title": f"{alt_name} vs {stock_name}",
            "generated_at": datetime.now().isoformat(),
            "dates": [d.strftime("%Y-%m-%d") for d in alt_series.index],
            "series": [
                {
                    "name": alt_name,
                    "data": alt_series.values.tolist(),
                    "color": "#1f77b4",
                    "yAxis": 0,
                },
                {
                    "name": stock_name,
                    "data": stock_series.values.tolist(),
                    "color": "#ff7f0e",
                    "yAxis": 1,
                },
            ],
            "axes": [
                {
                    "side": "left",
                    "label": alt_name,
                    "color": "#1f77b4",
                },
                {
                    "side": "right",
                    "label": stock_name,
                    "color": "#ff7f0e",
                },
            ],
            "normalized": normalize,
        }

        logger.info(f"Generated time series overlay: {alt_name} vs {stock_name}")
        return timeseries_data

    def get_rolling_correlation_chart(
        self,
        rolling_correlation: pd.Series,
        regime_changes: Optional[List[Dict]] = None,
        title: str = "Rolling Correlation",
    ) -> Dict[str, Any]:
        """
        Generate rolling correlation trend chart.

        Args:
            rolling_correlation: Series with rolling correlation values
            regime_changes: List of regime change points
            title: Chart title

        Returns:
            Dashboard-compatible chart data
        """
        if rolling_correlation.empty:
            logger.warning("Empty rolling correlation provided")
            return None

        # Classify current regimes
        current_regime = self._classify_regime(rolling_correlation.iloc[-1])

        # Format data
        chart_data = {
            "type": "line",
            "title": title,
            "generated_at": datetime.now().isoformat(),
            "data": {
                "dates": [d.strftime("%Y-%m-%d") for d in rolling_correlation.index],
                "values": rolling_correlation.values.tolist(),
            },
            "thresholds": [
                {"value": 0.7, "label": "HIGH", "color": "#2ecc71", "opacity": 0.3},
                {"value": 0.4, "label": "MEDIUM", "color": "#f39c12", "opacity": 0.3},
                {"value": 0.1, "label": "LOW", "color": "#e74c3c", "opacity": 0.3},
                {"value": -1.0, "label": "DECOUPLING", "color": "#c0392b", "opacity": 0.3},
            ],
            "current_regime": current_regime,
            "current_value": float(rolling_correlation.iloc[-1]) if len(rolling_correlation) > 0 else 0,
        }

        # Add regime changes if provided
        if regime_changes:
            chart_data["regime_changes"] = [
                {
                    "date": rc.get("date"),
                    "from_regime": rc.get("from_regime"),
                    "to_regime": rc.get("to_regime"),
                }
                for rc in regime_changes
            ]

        logger.info(f"Generated rolling correlation chart: {title}")
        return chart_data

    def get_indicator_summary_table(
        self,
        correlations: List[Dict[str, Any]],
        title: str = "Correlation Summary",
    ) -> Dict[str, Any]:
        """
        Generate indicator summary table.

        Args:
            correlations: List of significant correlations
            title: Table title

        Returns:
            Dashboard-compatible table data
        """
        if not correlations:
            logger.warning("No correlations provided")
            return None

        # Prepare table rows
        rows = []
        for corr in sorted(
            correlations,
            key=lambda x: abs(x.get("correlation", 0)),
            reverse=True
        ):
            rows.append({
                "indicator": corr.get("indicator"),
                "stock": corr.get("stock"),
                "correlation": f"{corr.get('correlation', 0):.4f}",
                "p_value": f"{corr.get('p_value', 0):.4f}",
                "strength": corr.get("strength"),
                "significance": "Yes" if corr.get("p_value", 1) < 0.05 else "No",
            })

        table_data = {
            "type": "table",
            "title": title,
            "generated_at": datetime.now().isoformat(),
            "columns": [
                {"key": "indicator", "label": "Indicator", "sortable": True},
                {"key": "stock", "label": "Stock", "sortable": True},
                {"key": "correlation", "label": "Correlation", "sortable": True},
                {"key": "p_value", "label": "P-Value", "sortable": True},
                {"key": "strength", "label": "Strength", "sortable": False},
                {"key": "significance", "label": "Significant", "sortable": False},
            ],
            "rows": rows,
            "total_rows": len(rows),
        }

        logger.info(f"Generated summary table: {len(rows)} correlations")
        return table_data

    def get_top_correlations_cards(
        self,
        correlations: List[Dict[str, Any]],
        top_n: int = 5,
    ) -> Dict[str, Any]:
        """
        Generate top correlations as card components.

        Args:
            correlations: List of significant correlations
            top_n: Number of top correlations to show

        Returns:
            Dashboard-compatible card data
        """
        if not correlations:
            return None

        # Sort and take top N
        sorted_corrs = sorted(
            correlations,
            key=lambda x: abs(x.get("correlation", 0)),
            reverse=True
        )[:top_n]

        cards = []
        for i, corr in enumerate(sorted_corrs, 1):
            corr_value = corr.get("correlation", 0)
            card = {
                "rank": i,
                "indicator": corr.get("indicator"),
                "stock": corr.get("stock"),
                "correlation": corr_value,
                "correlation_formatted": f"{corr_value:.4f}",
                "p_value": corr.get("p_value", 0),
                "strength": corr.get("strength"),
                "color": "#2ecc71" if corr_value > 0 else "#e74c3c",
                "icon": "arrow-up" if corr_value > 0 else "arrow-down",
                "interpretation": self._interpret_correlation(
                    corr.get("indicator"),
                    corr.get("stock"),
                    corr_value,
                ),
            }
            cards.append(card)

        cards_data = {
            "type": "cards",
            "title": "Top Correlations",
            "generated_at": datetime.now().isoformat(),
            "cards": cards,
            "total": len(correlations),
        }

        logger.info(f"Generated top correlation cards: {len(cards)} cards")
        return cards_data

    def get_dashboard_summary(
        self,
        report: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate complete dashboard summary.

        Args:
            report: Report from CorrelationReport.generate_report()

        Returns:
            Complete dashboard data structure
        """
        if not report:
            return None

        summary = {
            "title": report.get("metadata", {}).get("title"),
            "generated_at": report.get("metadata", {}).get("generated_at"),
            "period": {
                "start": report.get("metadata", {}).get("period_start"),
                "end": report.get("metadata", {}).get("period_end"),
            },
            "statistics": {
                "total_pairs": report.get("statistics", {}).get("total_pairs"),
                "significant_pairs": report.get("statistics", {}).get("significant_pairs"),
                "mean_correlation": f"{report.get('statistics', {}).get('mean_correlation', 0):.4f}",
                "std_correlation": f"{report.get('statistics', {}).get('std_correlation', 0):.4f}",
            },
            "key_findings": report.get("key_findings", []),
            "recommendations": report.get("recommendations", []),
        }

        logger.info("Generated dashboard summary")
        return summary

    def get_sector_filter_options(
        self,
        stock_list: List[str],
        sector_map: Optional[Dict[str, str]] = None,
    ) -> Dict[str, List[str]]:
        """
        Generate sector filter options for dashboard.

        Args:
            stock_list: List of stock codes
            sector_map: Optional mapping of stock code to sector

        Returns:
            Sector groupings for filtering
        """
        if not sector_map:
            # Default sector classification for Hong Kong stocks
            sector_map = {
                "0001.HK": "Banking",  # HSBC
                "0939.HK": "Banking",  # CCB
                "1398.HK": "Banking",  # ICBC
                "2388.HK": "Banking",  # BOC
                "0005.HK": "Property",  # HSBC
                "1113.HK": "Property",  # CK
                "0016.HK": "Property",  # SHK
                "0686.HK": "Property",  # HH
                "2333.HK": "Consumer",  # AEON
                "6030.HK": "Consumer",  # Dah Sing
                "0883.HK": "Technology",  # CITIC Telecom
                "1810.HK": "Technology",  # Xiaomi
            }

        sectors = {}
        for stock in stock_list:
            sector = sector_map.get(stock, "Other")
            if sector not in sectors:
                sectors[sector] = []
            sectors[sector].append(stock)

        logger.info(f"Generated sector filters: {len(sectors)} sectors")
        return sectors

    @staticmethod
    def _classify_regime(correlation: float) -> str:
        """Classify correlation regime."""
        if correlation >= 0.7:
            return "HIGH"
        elif correlation >= 0.4:
            return "MEDIUM"
        elif correlation >= 0.1:
            return "LOW"
        else:
            return "DECOUPLING"

    @staticmethod
    def _interpret_correlation(
        indicator: str,
        stock: str,
        correlation: float,
    ) -> str:
        """Generate human-readable interpretation."""
        direction = "rises" if correlation > 0 else "falls"
        strength = "strongly" if abs(correlation) > 0.6 else "moderately" if abs(correlation) > 0.3 else "weakly"

        return f"When {indicator} increases, {stock} tends to {direction} {strength}"


class DashboardDataFormatter:
    """
    Formats various data types for dashboard consumption.
    """

    @staticmethod
    def format_metric(value: float, decimals: int = 2) -> str:
        """Format numeric metric."""
        return f"{value:.{decimals}f}"

    @staticmethod
    def format_percentage(value: float, decimals: int = 1) -> str:
        """Format as percentage."""
        return f"{value * 100:.{decimals}f}%"

    @staticmethod
    def format_date(date: Any) -> str:
        """Format date for display."""
        if hasattr(date, "strftime"):
            return date.strftime("%Y-%m-%d")
        return str(date)

    @staticmethod
    def format_correlation_color(correlation: float) -> str:
        """Get color for correlation value."""
        if correlation >= 0.7:
            return "#27ae60"  # Green
        elif correlation >= 0.4:
            return "#3498db"  # Blue
        elif correlation >= 0.1:
            return "#f39c12"  # Orange
        elif correlation >= -0.1:
            return "#95a5a6"  # Gray
        elif correlation >= -0.4:
            return "#e67e22"  # Dark orange
        elif correlation >= -0.7:
            return "#e74c3c"  # Red
        else:
            return "#c0392b"  # Dark red


# Usage examples
if __name__ == "__main__":
    import pandas as pd

    # Create sample data
    dates = pd.date_range("2025-01-01", "2025-10-18", freq="D")

    # Sample correlation matrix
    corr_matrix = pd.DataFrame(
        np.random.uniform(-1, 1, (3, 3)),
        index=["HIBOR_ON", "Visitor_Arrivals", "HKEX_Futures"],
        columns=["0939.HK", "1398.HK", "2388.HK"],
    )

    # Sample time series
    alt_data = pd.Series(np.random.uniform(3, 5, len(dates)), index=dates)
    stock_data = pd.Series(np.random.uniform(10, 15, len(dates)), index=dates)

    # Create dashboard
    dashboard = AlternativeDataDashboard()

    # Generate visualizations
    heatmap = dashboard.get_correlation_heatmap(corr_matrix)
    timeseries = dashboard.get_timeseries_overlay(alt_data, stock_data)
    rolling = dashboard.get_rolling_correlation_chart(
        pd.Series(np.random.uniform(0, 1, 100))
    )

    print("Dashboard visualizations generated successfully!")
    print(f"Heatmap type: {heatmap['type']}")
    print(f"TimeSeries type: {timeseries['type']}")
    print(f"Rolling chart type: {rolling['type']}")
