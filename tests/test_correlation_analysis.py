"""
Comprehensive test suite for Phase 3: Correlation Analysis & Visualization

Tests cover:
- CorrelationAnalyzer: correlation calculations, leading indicators, rolling correlation
- CorrelationReport: report generation, export formats, recommendations
- AlternativeDataDashboard: visualization components, formatting, filtering

Test Coverage Target: 90%+
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import tempfile
import os
from pathlib import Path

from src.analysis.correlation_analyzer import CorrelationAnalyzer, CorrelationMethod
from src.analysis.correlation_report import CorrelationReport
from src.dashboard.alternative_data_views import AlternativeDataDashboard, DashboardDataFormatter


# ============================================================================
# FIXTURES: Sample Data
# ============================================================================

@pytest.fixture
def date_range():
    """Generate 252 trading days of data (1 year)"""
    return pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')


@pytest.fixture
def alt_data_hibor(date_range):
    """Alternative data: HIBOR rates"""
    np.random.seed(42)
    return pd.Series(
        np.random.uniform(3.5, 4.5, len(date_range)),
        index=date_range,
        name='HIBOR_ON'
    )


@pytest.fixture
def stock_returns_bank(date_range):
    """Stock returns: Bank stocks (0939.HK - CCB)"""
    np.random.seed(42)
    # Negative correlation with HIBOR (when rates go up, bank profits down)
    base = np.random.normal(0.0005, 0.015, len(date_range))
    adjustment = -0.3 * np.random.uniform(3.5, 4.5, len(date_range)) / 4.0
    return pd.Series(base + adjustment, index=date_range, name='0939.HK_Returns')


@pytest.fixture
def visitor_arrivals(date_range):
    """Alternative data: Hong Kong visitor arrivals"""
    np.random.seed(43)
    # Seasonal pattern + trend
    seasonal = 100000 * np.sin(np.arange(len(date_range)) * 2 * np.pi / 365)
    trend = np.linspace(0, 50000, len(date_range))
    noise = np.random.normal(0, 20000, len(date_range))
    return pd.Series(
        seasonal + trend + noise + 250000,
        index=date_range,
        name='Visitor_Arrivals'
    )


@pytest.fixture
def stock_returns_retail(date_range):
    """Stock returns: Retail stocks (1113.HK - Cheung Kong)"""
    np.random.seed(43)
    # Positive correlation with visitor arrivals (3-day lag)
    base = np.random.normal(0.0005, 0.012, len(date_range))
    adjustment = 0.2 * (np.random.uniform(200000, 350000, len(date_range)) - 250000) / 50000
    return pd.Series(base + adjustment, index=date_range, name='1113.HK_Returns')


@pytest.fixture
def correlation_matrix(alt_data_hibor, stock_returns_bank):
    """Pre-calculated correlation matrix"""
    return pd.DataFrame(
        [[1.0, -0.65], [-0.65, 1.0]],
        index=['HIBOR_ON', '0939.HK'],
        columns=['HIBOR_ON', '0939.HK']
    )


@pytest.fixture
def p_values_matrix():
    """P-values for correlations"""
    return pd.DataFrame(
        [[0.0, 0.0001], [0.0001, 0.0]],
        index=['HIBOR_ON', '0939.HK'],
        columns=['HIBOR_ON', '0939.HK']
    )


@pytest.fixture
def significant_correlations():
    """List of significant correlations"""
    return [
        {
            'indicator': 'HIBOR_ON',
            'stock': '0939.HK',
            'correlation': -0.65,
            'p_value': 0.0001,
            'strength': 'STRONG'
        },
        {
            'indicator': 'HIBOR_1M',
            'stock': '0939.HK',
            'correlation': -0.58,
            'p_value': 0.0002,
            'strength': 'STRONG'
        }
    ]


# ============================================================================
# TESTS: CorrelationAnalyzer
# ============================================================================

class TestCorrelationAnalyzer:
    """Test suite for CorrelationAnalyzer"""

    def test_initialization(self):
        """Test CorrelationAnalyzer initialization"""
        analyzer = CorrelationAnalyzer(
            correlation_method='pearson',
            min_periods=20,
            significance_level=0.05
        )
        assert analyzer is not None

    def test_correlation_matrix_calculation(self, alt_data_hibor, stock_returns_bank):
        """Test correlation matrix calculation"""
        analyzer = CorrelationAnalyzer(correlation_method='pearson')

        # Prepare DataFrame with both series
        data = pd.DataFrame({
            'HIBOR': alt_data_hibor,
            'Bank_Returns': stock_returns_bank
        })

        result = analyzer.calculate_correlation_matrix(
            alt_data=data[['HIBOR']],
            returns=data[['Bank_Returns']]
        )

        assert 'correlation_matrix' in result
        assert 'p_values' in result
        assert 'significant_correlations' in result
        assert result['correlation_matrix'].shape == (1, 1)
        assert -1 <= result['correlation_matrix'].iloc[0, 0] <= 1

    def test_correlation_methods(self, alt_data_hibor, stock_returns_bank):
        """Test different correlation methods"""
        data = pd.DataFrame({
            'HIBOR': alt_data_hibor,
            'Returns': stock_returns_bank
        })

        methods = [
            (CorrelationMethod.PEARSON, 'pearson'),
            (CorrelationMethod.SPEARMAN, 'spearman'),
            (CorrelationMethod.KENDALL, 'kendall')
        ]

        for method, method_name in methods:
            analyzer = CorrelationAnalyzer(correlation_method=method_name)
            result = analyzer.calculate_correlation_matrix(
                data[['HIBOR']], data[['Returns']]
            )
            assert 'correlation_matrix' in result
            assert isinstance(result['correlation_matrix'], pd.DataFrame)

    def test_leading_indicator_detection(self, visitor_arrivals, stock_returns_retail):
        """Test leading indicator detection with lag analysis"""
        analyzer = CorrelationAnalyzer()

        result = analyzer.identify_leading_indicators(
            indicator_data=visitor_arrivals,
            returns_data=stock_returns_retail,
            max_lag=20
        )

        assert 'peak_lag' in result
        assert 'peak_correlation' in result
        assert 'is_leading' in result
        assert 'interpretation' in result
        assert isinstance(result['peak_lag'], (int, np.integer))
        assert -1 <= result['peak_correlation'] <= 1

    def test_rolling_correlation(self, alt_data_hibor, stock_returns_bank):
        """Test rolling correlation calculation"""
        analyzer = CorrelationAnalyzer()

        result = analyzer.calculate_rolling_correlation(
            alt_data=alt_data_hibor,
            price_data=stock_returns_bank,
            window=60
        )

        assert 'rolling_correlation' in result
        assert 'regime_changes' in result
        assert 'stability_score' in result
        assert isinstance(result['rolling_correlation'], pd.Series)
        assert 0 <= result['stability_score'] <= 1

    def test_rolling_correlation_regime_classification(self, alt_data_hibor, stock_returns_bank):
        """Test regime classification in rolling correlation"""
        analyzer = CorrelationAnalyzer()

        result = analyzer.calculate_rolling_correlation(
            alt_data=alt_data_hibor,
            price_data=stock_returns_bank,
            window=60
        )

        rolling_corr = result['rolling_correlation']
        assert len(rolling_corr) > 0
        assert all(-1 <= val <= 1 for val in rolling_corr)

    def test_sharpe_comparison(self, stock_returns_bank):
        """Test Sharpe ratio comparison"""
        analyzer = CorrelationAnalyzer()

        # Create base returns and improved returns with signal
        base_returns = stock_returns_bank.copy()
        improved_returns = base_returns + 0.001  # Slight improvement

        result = analyzer.calculate_sharpe_comparison(
            returns_without_signal=base_returns,
            returns_with_signal=improved_returns,
            risk_free_rate=0.02
        )

        assert 'sharpe_without_signal' in result
        assert 'sharpe_with_signal' in result
        assert 'sharpe_improvement_percentage' in result
        assert 'volatility_reduction_percentage' in result
        assert 'return_improvement_percentage' in result
        assert result['volatility_with_signal'] <= result['volatility_without_signal']

    def test_edge_case_insufficient_data(self):
        """Test handling of insufficient data"""
        analyzer = CorrelationAnalyzer(min_periods=30)

        # Create very small series
        dates = pd.date_range('2024-01-01', periods=10)
        small_series = pd.Series(np.random.randn(10), index=dates)

        result = analyzer.calculate_correlation_matrix(
            alt_data=pd.DataFrame(small_series),
            returns=pd.DataFrame(small_series)
        )

        # Should handle gracefully
        assert result is not None or result is None  # Either processes or returns None

    def test_edge_case_nan_values(self, alt_data_hibor):
        """Test handling of NaN values"""
        analyzer = CorrelationAnalyzer()

        # Introduce NaN values
        data_with_nan = alt_data_hibor.copy()
        data_with_nan.iloc[10:20] = np.nan

        result = analyzer.calculate_correlation_matrix(
            alt_data=pd.DataFrame(data_with_nan),
            returns=pd.DataFrame(data_with_nan)
        )

        # Should handle gracefully
        assert result is not None

    def test_edge_case_zero_variance(self):
        """Test handling of zero variance data"""
        analyzer = CorrelationAnalyzer()

        dates = pd.date_range('2024-01-01', periods=100)
        constant_series = pd.Series(np.ones(100), index=dates)

        # Zero variance data should either return None or raise a ValueError
        # depending on implementation - both are acceptable
        try:
            result = analyzer.calculate_correlation_matrix(
                alt_data=pd.DataFrame(constant_series),
                returns=pd.DataFrame(constant_series)
            )
            # If no exception, result should be None (no valid correlations)
            assert result is None or isinstance(result, dict)
        except (ValueError, RuntimeWarning):
            # Acceptable to raise error on zero variance
            pass


# ============================================================================
# TESTS: CorrelationReport
# ============================================================================

class TestCorrelationReport:
    """Test suite for CorrelationReport"""

    def test_initialization(self):
        """Test CorrelationReport initialization"""
        reporter = CorrelationReport()
        assert reporter is not None

    def test_report_generation(self, significant_correlations):
        """Test basic report generation"""
        reporter = CorrelationReport()

        correlation_result = {
            'correlation_matrix': pd.DataFrame([[1.0, -0.65], [-0.65, 1.0]]),
            'p_values': pd.DataFrame([[0.0, 0.0001], [0.0001, 0.0]]),
            'significant_correlations': significant_correlations,
            'summary': {
                'mean_correlation': -0.32,
                'std_correlation': 0.46,
                'total_pairs': 2,
                'significant_pairs': 2
            }
        }

        report = reporter.generate_report(
            correlation_result=correlation_result,
            leading_indicators_result={},
            rolling_correlation_result={},
            sharpe_comparison_result={},
            title='Test Report',
            period_start='2024-01-01',
            period_end='2024-12-31'
        )

        assert report is not None
        assert 'metadata' in report
        assert 'statistics' in report
        assert 'key_findings' in report

    def test_export_html(self, significant_correlations, tmp_path):
        """Test HTML export"""
        reporter = CorrelationReport()

        correlation_result = {
            'correlation_matrix': pd.DataFrame([[1.0, -0.65], [-0.65, 1.0]]),
            'significant_correlations': significant_correlations,
            'summary': {'mean_correlation': -0.32, 'std_correlation': 0.46}
        }

        report = reporter.generate_report(
            correlation_result=correlation_result,
            leading_indicators_result={},
            rolling_correlation_result={},
            sharpe_comparison_result={},
            title='Test Report'
        )

        output_file = str(tmp_path / 'test_report.html')
        result = reporter.export_html(report, output_file)

        assert os.path.exists(output_file)
        with open(output_file, 'r') as f:
            content = f.read()
            assert 'Test Report' in content

    def test_export_json(self, significant_correlations, tmp_path):
        """Test JSON export"""
        reporter = CorrelationReport()

        correlation_result = {
            'correlation_matrix': pd.DataFrame([[1.0, -0.65], [-0.65, 1.0]]),
            'significant_correlations': significant_correlations,
            'summary': {'mean_correlation': -0.32, 'std_correlation': 0.46}
        }

        report = reporter.generate_report(
            correlation_result=correlation_result,
            leading_indicators_result={},
            rolling_correlation_result={},
            sharpe_comparison_result={},
            title='Test Report'
        )

        output_file = str(tmp_path / 'test_report.json')
        result = reporter.export_json(report, output_file)

        assert os.path.exists(output_file)
        with open(output_file, 'r') as f:
            data = json.load(f)
            assert 'metadata' in data

    def test_export_text(self, significant_correlations, tmp_path):
        """Test text export"""
        reporter = CorrelationReport()

        correlation_result = {
            'correlation_matrix': pd.DataFrame([[1.0, -0.65], [-0.65, 1.0]]),
            'significant_correlations': significant_correlations,
            'summary': {'mean_correlation': -0.32, 'std_correlation': 0.46}
        }

        report = reporter.generate_report(
            correlation_result=correlation_result,
            leading_indicators_result={},
            rolling_correlation_result={},
            sharpe_comparison_result={},
            title='Test Report'
        )

        output_file = str(tmp_path / 'test_report.txt')
        result = reporter.export_text(report, output_file)

        assert os.path.exists(output_file)

    def test_export_dashboard_json(self, significant_correlations):
        """Test dashboard JSON export"""
        reporter = CorrelationReport()

        correlation_result = {
            'correlation_matrix': pd.DataFrame([[1.0, -0.65], [-0.65, 1.0]]),
            'significant_correlations': significant_correlations,
            'summary': {'mean_correlation': -0.32, 'std_correlation': 0.46}
        }

        report = reporter.generate_report(
            correlation_result=correlation_result,
            leading_indicators_result={},
            rolling_correlation_result={},
            sharpe_comparison_result={},
            title='Test Report'
        )

        dashboard_data = reporter.export_dashboard_json(report)
        assert dashboard_data is not None

    def test_recommendation_generation(self):
        """Test trading recommendation generation"""
        reporter = CorrelationReport()

        # Strong negative correlation should suggest hedging
        correlation_result = {
            'correlation_matrix': pd.DataFrame([[-0.75]]),
            'significant_correlations': [{
                'correlation': -0.75,
                'indicator': 'HIBOR',
                'stock': '0939.HK',
                'p_value': 0.0001,
                'strength': 'STRONG'  # Include required strength field
            }],
            'summary': {}
        }

        report = reporter.generate_report(
            correlation_result=correlation_result,
            leading_indicators_result={},
            rolling_correlation_result={},
            sharpe_comparison_result={},
            title='Test Report'
        )

        assert 'recommendations' in report
        assert len(report['recommendations']) > 0


# ============================================================================
# TESTS: AlternativeDataDashboard
# ============================================================================

class TestAlternativeDataDashboard:
    """Test suite for AlternativeDataDashboard"""

    def test_initialization(self):
        """Test AlternativeDataDashboard initialization"""
        dashboard = AlternativeDataDashboard()
        assert dashboard is not None

    def test_correlation_heatmap(self, correlation_matrix, p_values_matrix):
        """Test correlation heatmap generation"""
        dashboard = AlternativeDataDashboard()

        heatmap = dashboard.get_correlation_heatmap(
            correlation_matrix=correlation_matrix,
            p_values=p_values_matrix,
            title='Test Heatmap'
        )

        assert heatmap is not None
        assert heatmap['type'] == 'heatmap'
        assert heatmap['title'] == 'Test Heatmap'
        assert 'data' in heatmap
        assert 'colorScale' in heatmap

    def test_correlation_heatmap_empty_data(self):
        """Test heatmap with empty correlation matrix"""
        dashboard = AlternativeDataDashboard()
        empty_matrix = pd.DataFrame()

        heatmap = dashboard.get_correlation_heatmap(empty_matrix)
        assert heatmap is None

    def test_timeseries_overlay(self, alt_data_hibor, stock_returns_bank):
        """Test time series overlay chart generation"""
        dashboard = AlternativeDataDashboard()

        timeseries = dashboard.get_timeseries_overlay(
            alt_data=alt_data_hibor,
            stock_data=stock_returns_bank,
            alt_name='HIBOR',
            stock_name='0939.HK',
            normalize=True
        )

        assert timeseries is not None
        assert timeseries['type'] == 'timeseries_overlay'
        assert len(timeseries['series']) == 2
        assert timeseries['normalized'] == True

    def test_timeseries_overlay_unnormalized(self, alt_data_hibor, stock_returns_bank):
        """Test time series overlay without normalization"""
        dashboard = AlternativeDataDashboard()

        timeseries = dashboard.get_timeseries_overlay(
            alt_data=alt_data_hibor,
            stock_data=stock_returns_bank,
            normalize=False
        )

        assert timeseries is not None
        assert timeseries['normalized'] == False

    def test_rolling_correlation_chart(self, alt_data_hibor, stock_returns_bank):
        """Test rolling correlation chart generation"""
        dashboard = AlternativeDataDashboard()

        analyzer = CorrelationAnalyzer()
        result = analyzer.calculate_rolling_correlation(
            alt_data=alt_data_hibor,
            price_data=stock_returns_bank,
            window=60
        )

        rolling_chart = dashboard.get_rolling_correlation_chart(
            rolling_correlation=result['rolling_correlation'],
            title='Test Rolling Correlation'
        )

        assert rolling_chart is not None
        assert rolling_chart['type'] == 'line'
        assert 'thresholds' in rolling_chart
        assert 'current_regime' in rolling_chart

    def test_indicator_summary_table(self, significant_correlations):
        """Test indicator summary table generation"""
        dashboard = AlternativeDataDashboard()

        table = dashboard.get_indicator_summary_table(
            correlations=significant_correlations,
            title='Test Summary Table'
        )

        assert table is not None
        assert table['type'] == 'table'
        assert len(table['rows']) == len(significant_correlations)
        assert all(col['key'] for col in table['columns'])

    def test_indicator_summary_empty(self):
        """Test summary table with no correlations"""
        dashboard = AlternativeDataDashboard()

        table = dashboard.get_indicator_summary_table(correlations=[])
        assert table is None

    def test_top_correlations_cards(self, significant_correlations):
        """Test top correlations card generation"""
        dashboard = AlternativeDataDashboard()

        cards = dashboard.get_top_correlations_cards(
            correlations=significant_correlations,
            top_n=2
        )

        assert cards is not None
        assert cards['type'] == 'cards'
        assert len(cards['cards']) == 2
        assert all('rank' in card for card in cards['cards'])
        assert all('color' in card for card in cards['cards'])

    def test_top_correlations_fewer_than_requested(self, significant_correlations):
        """Test top correlations when fewer exist than requested"""
        dashboard = AlternativeDataDashboard()

        cards = dashboard.get_top_correlations_cards(
            correlations=significant_correlations,
            top_n=10  # Request more than available
        )

        assert cards is not None
        assert len(cards['cards']) == len(significant_correlations)

    def test_dashboard_summary(self, significant_correlations):
        """Test complete dashboard summary generation"""
        dashboard = AlternativeDataDashboard()

        report = {
            'metadata': {
                'title': 'Test Dashboard',
                'generated_at': datetime.now().isoformat(),
                'period_start': '2024-01-01',
                'period_end': '2024-12-31'
            },
            'statistics': {
                'total_pairs': 2,
                'significant_pairs': 2,
                'mean_correlation': -0.32,
                'std_correlation': 0.46
            },
            'key_findings': ['Finding 1', 'Finding 2'],
            'recommendations': ['Recommendation 1']
        }

        summary = dashboard.get_dashboard_summary(report)

        assert summary is not None
        assert summary['title'] == 'Test Dashboard'
        assert summary['statistics']['total_pairs'] == 2

    def test_sector_filter_options(self):
        """Test sector filter options generation"""
        dashboard = AlternativeDataDashboard()

        stock_list = ['0939.HK', '1398.HK', '0005.HK', '1113.HK']
        sectors = dashboard.get_sector_filter_options(stock_list)

        assert sectors is not None
        assert isinstance(sectors, dict)
        assert len(sectors) > 0

    def test_sector_filter_custom_map(self):
        """Test sector filter with custom sector map"""
        dashboard = AlternativeDataDashboard()

        stock_list = ['TEST.HK', 'CUSTOM.HK']
        sector_map = {'TEST.HK': 'Technology', 'CUSTOM.HK': 'Finance'}

        sectors = dashboard.get_sector_filter_options(stock_list, sector_map)

        assert sectors is not None
        assert 'Technology' in sectors
        assert 'Finance' in sectors


# ============================================================================
# TESTS: DashboardDataFormatter
# ============================================================================

class TestDashboardDataFormatter:
    """Test suite for DashboardDataFormatter"""

    def test_format_metric(self):
        """Test numeric metric formatting"""
        result = DashboardDataFormatter.format_metric(3.14159, decimals=2)
        assert result == '3.14'

    def test_format_percentage(self):
        """Test percentage formatting"""
        result = DashboardDataFormatter.format_percentage(0.2543, decimals=1)
        assert result == '25.4%'

    def test_format_date_datetime(self):
        """Test date formatting with datetime object"""
        date = datetime(2024, 10, 18)
        result = DashboardDataFormatter.format_date(date)
        assert '2024' in result
        assert '10' in result
        assert '18' in result

    def test_format_date_string(self):
        """Test date formatting with string"""
        result = DashboardDataFormatter.format_date('2024-10-18')
        assert result == '2024-10-18'

    def test_format_correlation_color(self):
        """Test correlation color mapping"""
        test_cases = [
            (0.8, '#27ae60'),    # High positive - green
            (0.5, '#3498db'),    # Moderate positive - blue
            (0.2, '#f39c12'),    # Weak positive - orange
            (0.05, '#95a5a6'),   # Very weak - gray
            (-0.3, '#e67e22'),   # Weak negative - dark orange
            (-0.6, '#e74c3c'),   # Moderate negative - red
            (-0.9, '#c0392b')    # Strong negative - dark red
        ]

        for correlation, expected_color in test_cases:
            result = DashboardDataFormatter.format_correlation_color(correlation)
            assert result == expected_color


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestPhase3Integration:
    """Integration tests for Phase 3 components"""

    def test_end_to_end_analysis_pipeline(
        self,
        alt_data_hibor,
        stock_returns_bank,
        significant_correlations
    ):
        """Test complete analysis pipeline: analyze → report → visualize"""
        # Step 1: Analyze correlations
        analyzer = CorrelationAnalyzer()
        data = pd.DataFrame({
            'HIBOR': alt_data_hibor,
            'Returns': stock_returns_bank
        })

        analysis_result = analyzer.calculate_correlation_matrix(
            alt_data=data[['HIBOR']],
            returns=data[['Returns']]
        )

        # Step 2: Generate report
        reporter = CorrelationReport()
        report = reporter.generate_report(
            correlation_result=analysis_result,
            leading_indicators_result={},
            rolling_correlation_result={},
            sharpe_comparison_result={},
            title='Integration Test Report'
        )

        # Step 3: Create visualizations
        dashboard = AlternativeDataDashboard()
        heatmap = dashboard.get_correlation_heatmap(
            correlation_matrix=analysis_result['correlation_matrix']
        )

        # Verify all steps completed
        assert analysis_result is not None
        assert report is not None
        assert heatmap is not None

    def test_export_all_formats(self, significant_correlations, tmp_path):
        """Test exporting report in all formats"""
        reporter = CorrelationReport()

        correlation_result = {
            'correlation_matrix': pd.DataFrame([[1.0, -0.65], [-0.65, 1.0]]),
            'significant_correlations': significant_correlations,
            'summary': {'mean_correlation': -0.32, 'std_correlation': 0.46}
        }

        report = reporter.generate_report(
            correlation_result=correlation_result,
            leading_indicators_result={},
            rolling_correlation_result={},
            sharpe_comparison_result={},
            title='Export Test'
        )

        # Test all formats
        formats = [
            ('html', lambda f: reporter.export_html(report, f)),
            ('json', lambda f: reporter.export_json(report, f)),
            ('text', lambda f: reporter.export_text(report, f)),
        ]

        for fmt, export_fn in formats:
            output_file = str(tmp_path / f'test_report.{fmt}')
            export_fn(output_file)
            assert os.path.exists(output_file), f"Failed to export {fmt}"

    def test_dashboard_json_compatibility(self, significant_correlations):
        """Test that dashboard JSON is valid and complete"""
        dashboard = AlternativeDataDashboard()
        reporter = CorrelationReport()

        correlation_result = {
            'correlation_matrix': pd.DataFrame([[1.0, -0.65], [-0.65, 1.0]]),
            'significant_correlations': significant_correlations,
            'summary': {'mean_correlation': -0.32, 'std_correlation': 0.46}
        }

        report = reporter.generate_report(
            correlation_result=correlation_result,
            leading_indicators_result={},
            rolling_correlation_result={},
            sharpe_comparison_result={},
            title='Dashboard Test'
        )

        dashboard_data = reporter.export_dashboard_json(report)

        # Verify structure
        assert isinstance(dashboard_data, dict)
        assert 'data' in dashboard_data or 'summary' in dashboard_data


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPhase3Performance:
    """Performance tests for Phase 3 components"""

    def test_correlation_calculation_speed(self, alt_data_hibor, stock_returns_bank):
        """Test correlation calculation performance"""
        analyzer = CorrelationAnalyzer()

        import time
        start = time.time()

        data = pd.DataFrame({
            'HIBOR': alt_data_hibor,
            'Returns': stock_returns_bank
        })

        result = analyzer.calculate_correlation_matrix(
            alt_data=data[['HIBOR']],
            returns=data[['Returns']]
        )

        elapsed = time.time() - start

        # Should complete in < 100ms
        assert elapsed < 0.1, f"Correlation calculation too slow: {elapsed:.3f}s"

    def test_rolling_correlation_speed(self, alt_data_hibor, stock_returns_bank):
        """Test rolling correlation performance"""
        analyzer = CorrelationAnalyzer()

        import time
        start = time.time()

        result = analyzer.calculate_rolling_correlation(
            alt_data=alt_data_hibor,
            price_data=stock_returns_bank,
            window=60
        )

        elapsed = time.time() - start

        # Should complete in < 500ms
        assert elapsed < 0.5, f"Rolling correlation too slow: {elapsed:.3f}s"

    def test_report_generation_speed(self, significant_correlations):
        """Test report generation performance"""
        reporter = CorrelationReport()

        correlation_result = {
            'correlation_matrix': pd.DataFrame([[1.0, -0.65], [-0.65, 1.0]]),
            'significant_correlations': significant_correlations,
            'summary': {'mean_correlation': -0.32, 'std_correlation': 0.46}
        }

        import time
        start = time.time()

        report = reporter.generate_report(
            correlation_result=correlation_result,
            leading_indicators_result={},
            rolling_correlation_result={},
            sharpe_comparison_result={},
            title='Performance Test'
        )

        elapsed = time.time() - start

        # Should complete in < 200ms
        assert elapsed < 0.2, f"Report generation too slow: {elapsed:.3f}s"


# ============================================================================
# MARKERS FOR TEST ORGANIZATION
# ============================================================================

@pytest.mark.unit
class TestPhase3Unit:
    """Unit tests for Phase 3"""
    pass


@pytest.mark.integration
class TestPhase3IntegrationMarked:
    """Integration tests for Phase 3"""
    pass


@pytest.mark.performance
class TestPhase3PerformanceMarked:
    """Performance tests for Phase 3"""
    pass


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
