"""
Correlation Report Generation Module

Generates comprehensive correlation analysis reports from CorrelationAnalyzer results.

Features:
    - Summary statistics generation
    - Correlation matrix formatting
    - Top correlation identification
    - Recommendations for trading signals
    - HTML and text report export
    - Dashboard-compatible JSON output

Usage:
    from src.analysis import CorrelationAnalyzer
    from src.analysis.correlation_report import CorrelationReport

    analyzer = CorrelationAnalyzer()
    corr_result = analyzer.calculate_correlation_matrix(alt_data, returns)

    reporter = CorrelationReport()
    report = reporter.generate_report(
        correlation_result=corr_result,
        leading_indicators_result=leading_result,
        title="Alternative Data Correlation Analysis - Oct 2025"
    )

    # Export report
    reporter.export_html(report, "correlation_report.html")
    reporter.export_json(report, "correlation_report.json")
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

import pandas as pd
import numpy as np

logger = logging.getLogger("hk_quant_system.correlation_report")


class CorrelationReport:
    """
    Generator for correlation analysis reports.

    Creates comprehensive reports from correlation analysis results
    with summary statistics, visualizations, and recommendations.
    """

    def __init__(self):
        """Initialize CorrelationReport."""
        logger.info("Initialized CorrelationReport")

    def generate_report(
        self,
        correlation_result: Dict[str, Any],
        leading_indicators_result: Optional[Dict[str, Any]] = None,
        rolling_correlation_result: Optional[Dict[str, Any]] = None,
        sharpe_comparison_result: Optional[Dict[str, Any]] = None,
        title: str = "Alternative Data Correlation Analysis Report",
        period_start: Optional[str] = None,
        period_end: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive correlation analysis report.

        Args:
            correlation_result: Output from calculate_correlation_matrix()
            leading_indicators_result: Output from identify_leading_indicators()
            rolling_correlation_result: Output from calculate_rolling_correlation()
            sharpe_comparison_result: Output from calculate_sharpe_comparison()
            title: Report title
            period_start: Analysis period start date
            period_end: Analysis period end date

        Returns:
            Dictionary with:
                - title: Report title
                - summary: Executive summary
                - key_findings: Main insights
                - correlation_matrix: Formatted correlation data
                - top_correlations: Strongest relationships
                - leading_indicators: Leading/lagging analysis
                - recommendations: Trading recommendations
                - statistics: Detailed statistics
                - generated_at: Timestamp
        """
        if not correlation_result:
            logger.error("No correlation result provided")
            return None

        # Extract data
        corr_matrix = correlation_result.get("correlation_matrix")
        p_values = correlation_result.get("p_values")
        significant_corrs = correlation_result.get("significant_correlations", [])
        summary_stats = correlation_result.get("summary", {})

        # Sort significant correlations by absolute value
        sorted_corrs = sorted(
            significant_corrs,
            key=lambda x: abs(x["correlation"]),
            reverse=True
        )

        # Identify top correlations
        top_positive = [c for c in sorted_corrs if c["correlation"] > 0][:5]
        top_negative = [c for c in sorted_corrs if c["correlation"] < 0][:5]

        # Generate key findings
        key_findings = self._generate_key_findings(
            corr_matrix=corr_matrix,
            significant_corrs=significant_corrs,
            top_positive=top_positive,
            top_negative=top_negative,
            leading_result=leading_indicators_result,
            rolling_result=rolling_correlation_result,
            sharpe_result=sharpe_comparison_result,
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            significant_corrs=significant_corrs,
            leading_result=leading_indicators_result,
            sharpe_result=sharpe_comparison_result,
        )

        # Generate summary
        summary = self._generate_summary(
            title=title,
            period_start=period_start,
            period_end=period_end,
            summary_stats=summary_stats,
            significant_count=len(significant_corrs),
        )

        # Compile report
        report = {
            "metadata": {
                "title": title,
                "generated_at": datetime.now().isoformat(),
                "period_start": period_start,
                "period_end": period_end,
            },
            "summary": summary,
            "key_findings": key_findings,
            "statistics": {
                "total_pairs": summary_stats.get("total_pairs", 0),
                "significant_pairs": summary_stats.get("significant_pairs", 0),
                "mean_correlation": summary_stats.get("mean_correlation"),
                "std_correlation": summary_stats.get("std_correlation"),
                "min_correlation": summary_stats.get("min_correlation"),
                "max_correlation": summary_stats.get("max_correlation"),
            },
            "top_correlations": {
                "positive": self._format_correlations(top_positive),
                "negative": self._format_correlations(top_negative),
            },
            "correlation_matrix": {
                "data": corr_matrix.to_dict() if corr_matrix is not None else {},
                "p_values": p_values.to_dict() if p_values is not None else {},
            },
            "leading_indicators": self._format_leading_indicators(leading_indicators_result),
            "rolling_correlation": self._format_rolling_correlation(rolling_correlation_result),
            "sharpe_comparison": self._format_sharpe_comparison(sharpe_comparison_result),
            "recommendations": recommendations,
        }

        logger.info(f"Generated report: {title}")
        return report

    def export_html(self, report: Dict[str, Any], filename: str) -> str:
        """
        Export report as HTML.

        Args:
            report: Report dictionary from generate_report()
            filename: Output HTML filename

        Returns:
            HTML content as string
        """
        html = self._build_html(report)

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html)
            logger.info(f"Exported HTML report to {filename}")
        except Exception as e:
            logger.error(f"Failed to export HTML: {e}")
            raise

        return html

    def export_json(self, report: Dict[str, Any], filename: str) -> str:
        """
        Export report as JSON.

        Args:
            report: Report dictionary from generate_report()
            filename: Output JSON filename

        Returns:
            JSON content as string
        """
        import json

        json_str = json.dumps(report, indent=2, default=str)

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(json_str)
            logger.info(f"Exported JSON report to {filename}")
        except Exception as e:
            logger.error(f"Failed to export JSON: {e}")
            raise

        return json_str

    def export_text(self, report: Dict[str, Any], filename: str) -> str:
        """
        Export report as text.

        Args:
            report: Report dictionary from generate_report()
            filename: Output text filename

        Returns:
            Text content as string
        """
        text = self._build_text(report)

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(text)
            logger.info(f"Exported text report to {filename}")
        except Exception as e:
            logger.error(f"Failed to export text: {e}")
            raise

        return text

    def export_dashboard_json(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Export report data for dashboard visualization.

        Args:
            report: Report dictionary from generate_report()

        Returns:
            Dashboard-compatible data structure
        """
        dashboard_data = {
            "title": report["metadata"]["title"],
            "generated_at": report["metadata"]["generated_at"],
            "summary": report["summary"],
            "key_findings": report["key_findings"],
            "statistics": report["statistics"],
            "top_correlations": report["top_correlations"],
            "correlation_matrix_data": report["correlation_matrix"],
            "recommendations": report["recommendations"],
        }

        return dashboard_data

    @staticmethod
    def _generate_key_findings(
        corr_matrix,
        significant_corrs,
        top_positive,
        top_negative,
        leading_result,
        rolling_result,
        sharpe_result,
    ) -> List[str]:
        """Generate key findings from analysis."""
        findings = []

        # Correlation findings
        if top_positive:
            findings.append(
                f"Strongest positive correlation: {top_positive[0]['indicator']} "
                f"-> {top_positive[0]['stock']} (r={top_positive[0]['correlation']:.3f})"
            )

        if top_negative:
            findings.append(
                f"Strongest negative correlation: {top_negative[0]['indicator']} "
                f"-> {top_negative[0]['stock']} (r={top_negative[0]['correlation']:.3f})"
            )

        if significant_corrs:
            findings.append(
                f"{len(significant_corrs)} statistically significant correlations found "
                f"(p < 0.05)"
            )

        # Leading indicator findings
        if leading_result and leading_result.get("is_leading"):
            findings.append(
                f"Leading indicator identified: "
                f"Leads by {leading_result['peak_lag']} days "
                f"(r={leading_result['peak_correlation']:.3f})"
            )

        # Rolling correlation findings
        if rolling_result:
            regime_changes = len(rolling_result.get("regime_changes", []))
            if regime_changes > 0:
                findings.append(
                    f"{regime_changes} correlation regime changes detected "
                    f"(stability score: {rolling_result.get('stability_score', 0):.3f})"
                )

        # Sharpe ratio findings
        if sharpe_result:
            improvement = sharpe_result.get("sharpe_improvement_percentage", 0)
            findings.append(
                f"Alternative data improves Sharpe ratio by {improvement:+.1f}% "
                f"({sharpe_result['sharpe_without_signal']:.3f} -> "
                f"{sharpe_result['sharpe_with_signal']:.3f})"
            )

        return findings

    @staticmethod
    def _generate_recommendations(
        significant_corrs,
        leading_result,
        sharpe_result,
    ) -> List[Dict[str, str]]:
        """Generate trading recommendations."""
        recommendations = []

        # Correlation-based recommendations
        positive_corrs = [c for c in significant_corrs if c["correlation"] > 0.5]
        negative_corrs = [c for c in significant_corrs if c["correlation"] < -0.5]

        if positive_corrs:
            for corr in positive_corrs[:3]:
                recommendations.append({
                    "type": "positive_correlation",
                    "indicator": corr["indicator"],
                    "stock": corr["stock"],
                    "action": f"When {corr['indicator']} rises, {corr['stock']} tends to rise",
                    "confidence": corr["strength"],
                })

        if negative_corrs:
            for corr in negative_corrs[:3]:
                recommendations.append({
                    "type": "negative_correlation",
                    "indicator": corr["indicator"],
                    "stock": corr["stock"],
                    "action": f"When {corr['indicator']} rises, {corr['stock']} tends to fall",
                    "confidence": corr["strength"],
                })

        # Leading indicator recommendations
        if leading_result and leading_result.get("is_leading"):
            recommendations.append({
                "type": "leading_indicator",
                "indicator": "Identified",
                "action": f"Use as leading signal (leads by {leading_result['peak_lag']} days)",
                "confidence": "high" if leading_result.get("is_significant") else "medium",
            })

        # Sharpe ratio recommendations
        if sharpe_result:
            improvement = sharpe_result.get("sharpe_improvement_percentage", 0)
            if improvement > 20:
                recommendations.append({
                    "type": "performance_improvement",
                    "action": "Integrate alternative data signals - significant Sharpe ratio improvement",
                    "confidence": "high",
                })

        return recommendations

    @staticmethod
    def _generate_summary(
        title,
        period_start,
        period_end,
        summary_stats,
        significant_count,
    ) -> str:
        """Generate report summary."""
        summary = f"""
ALTERNATIVE DATA CORRELATION ANALYSIS REPORT
{'=' * 60}

Title: {title}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Analysis Period: {period_start or 'N/A'} to {period_end or 'N/A'}

SUMMARY STATISTICS
{'-' * 60}
Total correlation pairs analyzed: {summary_stats.get('total_pairs', 0)}
Statistically significant pairs (p < 0.05): {significant_count}

Correlation range:
  Minimum: {summary_stats.get('min_correlation', 0):.3f}
  Maximum: {summary_stats.get('max_correlation', 0):.3f}
  Mean: {summary_stats.get('mean_correlation', 0):.3f}
  Std Dev: {summary_stats.get('std_correlation', 0):.3f}

KEY INSIGHTS
{'-' * 60}
- Analysis identifies relationships between alternative data indicators
  and stock returns
- Results help inform trading signal design and risk management
- Correlations may change over time - monitor regularly for regime shifts
"""
        return summary.strip()

    @staticmethod
    def _format_correlations(correlations) -> List[Dict[str, Any]]:
        """Format correlation results for display."""
        formatted = []
        for i, corr in enumerate(correlations, 1):
            formatted.append({
                "rank": i,
                "indicator": corr.get("indicator"),
                "stock": corr.get("stock"),
                "correlation": f"{corr.get('correlation', 0):.4f}",
                "p_value": f"{corr.get('p_value', 0):.4f}",
                "strength": corr.get("strength"),
            })
        return formatted

    @staticmethod
    def _format_leading_indicators(result) -> Dict[str, Any]:
        """Format leading indicators analysis."""
        if not result:
            return {}

        return {
            "peak_lag_days": result.get("peak_lag"),
            "peak_correlation": f"{result.get('peak_correlation', 0):.4f}",
            "p_value": f"{result.get('peak_pvalue', 0):.4f}",
            "is_leading": result.get("is_leading"),
            "is_significant": result.get("is_significant"),
            "interpretation": result.get("interpretation"),
        }

    @staticmethod
    def _format_rolling_correlation(result) -> Dict[str, Any]:
        """Format rolling correlation analysis."""
        if not result:
            return {}

        return {
            "window_days": result.get("window"),
            "mean_correlation": f"{result.get('mean_correlation', 0):.4f}",
            "min_correlation": f"{result.get('min_correlation', 0):.4f}",
            "max_correlation": f"{result.get('max_correlation', 0):.4f}",
            "stability_score": f"{result.get('stability_score', 0):.3f}",
            "regime_changes": len(result.get("regime_changes", [])),
        }

    @staticmethod
    def _format_sharpe_comparison(result) -> Dict[str, Any]:
        """Format Sharpe ratio comparison."""
        if not result:
            return {}

        return {
            "sharpe_without_signal": f"{result.get('sharpe_without_signal', 0):.3f}",
            "sharpe_with_signal": f"{result.get('sharpe_with_signal', 0):.3f}",
            "improvement_pct": f"{result.get('sharpe_improvement_percentage', 0):+.1f}%",
            "return_without": f"{result.get('return_without_signal', 0):.1%}",
            "return_with": f"{result.get('return_with_signal', 0):.1%}",
            "volatility_reduction_pct": f"{result.get('volatility_reduction_percentage', 0):.1f}%",
        }

    def _build_html(self, report: Dict[str, Any]) -> str:
        """Build HTML report."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{report['metadata']['title']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; }}
        h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        h2 {{ color: #0066cc; margin-top: 30px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #007bff; color: white; }}
        tr:hover {{ background-color: #f9f9f9; }}
        .positive {{ color: green; font-weight: bold; }}
        .negative {{ color: red; font-weight: bold; }}
        .findings {{ background-color: #e7f3ff; padding: 10px; border-left: 4px solid #007bff; margin: 10px 0; }}
        .recommendation {{ background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin: 5px 0; }}
        .meta {{ color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{report['metadata']['title']}</h1>
        <p class="meta">Generated: {report['metadata']['generated_at']}</p>

        <h2>Summary</h2>
        <pre>{report['summary']}</pre>

        <h2>Key Findings</h2>
        <ul>
"""
        for finding in report.get("key_findings", []):
            html += f"            <li>{finding}</li>\n"

        html += """        </ul>

        <h2>Statistics</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
"""
        stats = report.get("statistics", {})
        for key, value in stats.items():
            if isinstance(value, float):
                value = f"{value:.4f}"
            html += f"            <tr><td>{key}</td><td>{value}</td></tr>\n"

        html += """        </table>

        <h2>Top Correlations</h2>
        <h3>Positive Correlations</h3>
        <table>
            <tr>
                <th>Rank</th>
                <th>Indicator</th>
                <th>Stock</th>
                <th>Correlation</th>
                <th>P-Value</th>
            </tr>
"""
        for corr in report.get("top_correlations", {}).get("positive", []):
            html += f"""            <tr>
                <td>{corr['rank']}</td>
                <td>{corr['indicator']}</td>
                <td>{corr['stock']}</td>
                <td class="positive">{corr['correlation']}</td>
                <td>{corr['p_value']}</td>
            </tr>
"""

        html += """        </table>

        <h3>Negative Correlations</h3>
        <table>
            <tr>
                <th>Rank</th>
                <th>Indicator</th>
                <th>Stock</th>
                <th>Correlation</th>
                <th>P-Value</th>
            </tr>
"""
        for corr in report.get("top_correlations", {}).get("negative", []):
            html += f"""            <tr>
                <td>{corr['rank']}</td>
                <td>{corr['indicator']}</td>
                <td>{corr['stock']}</td>
                <td class="negative">{corr['correlation']}</td>
                <td>{corr['p_value']}</td>
            </tr>
"""

        html += """        </table>

        <h2>Recommendations</h2>
"""
        for rec in report.get("recommendations", []):
            html += f"""        <div class="recommendation">
            <strong>{rec.get('type', 'N/A').replace('_', ' ').title()}</strong><br>
            {rec.get('action', 'N/A')}<br>
            <em>Confidence: {rec.get('confidence', 'N/A').title()}</em>
        </div>
"""

        html += """    </div>
</body>
</html>
"""
        return html

    def _build_text(self, report: Dict[str, Any]) -> str:
        """Build text report."""
        text = f"""
{report['metadata']['title']}
{'=' * 70}

Generated: {report['metadata']['generated_at']}
Period: {report['metadata']['period_start']} to {report['metadata']['period_end']}

{report.get('summary', '')}

TOP CORRELATIONS
{'-' * 70}

Positive Correlations:
"""
        for corr in report.get("top_correlations", {}).get("positive", []):
            text += f"  {corr['rank']}. {corr['indicator']} -> {corr['stock']}: {corr['correlation']} (p={corr['p_value']})\n"

        text += "\nNegative Correlations:\n"
        for corr in report.get("top_correlations", {}).get("negative", []):
            text += f"  {corr['rank']}. {corr['indicator']} -> {corr['stock']}: {corr['correlation']} (p={corr['p_value']})\n"

        text += f"""
RECOMMENDATIONS
{'-' * 70}
"""
        for i, rec in enumerate(report.get("recommendations", []), 1):
            text += f"""
{i}. {rec.get('type', 'N/A').replace('_', ' ').title()}
   Action: {rec.get('action', 'N/A')}
   Confidence: {rec.get('confidence', 'N/A')}
"""

        return text.strip()


# Usage example
if __name__ == "__main__":
    from src.analysis import CorrelationAnalyzer
    import pandas as pd

    # Create sample data
    dates = pd.date_range("2025-01-01", "2025-10-18", freq="D")

    alt_data = pd.DataFrame({
        "HIBOR_ON": np.random.uniform(3.0, 4.5, len(dates)),
        "HIBOR_3M": np.random.uniform(3.5, 5.0, len(dates)),
    }, index=dates)

    returns = pd.DataFrame({
        "0939.HK": np.random.normal(-0.001, 0.02, len(dates)),
        "1398.HK": np.random.normal(-0.0005, 0.025, len(dates)),
    }, index=dates)

    # Generate report
    analyzer = CorrelationAnalyzer()
    corr_result = analyzer.calculate_correlation_matrix(alt_data, returns)

    reporter = CorrelationReport()
    report = reporter.generate_report(
        correlation_result=corr_result,
        title="Sample Correlation Analysis Report",
        period_start="2025-01-01",
        period_end="2025-10-18",
    )

    # Export to text (console display)
    print(reporter.export_text(report, "/tmp/report.txt"))
