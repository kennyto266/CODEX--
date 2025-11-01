"""
Correlation Analysis Module - Alternative Data Analysis Framework

Calculates statistical correlations between alternative data indicators
and stock returns, identifying relationships and leading indicators.

Features:
    - Pearson correlation coefficient calculation
    - Sharpe ratio with/without alternative data
    - Rolling correlation analysis for regime detection
    - Leading/lagging indicator identification
    - Statistical significance testing (p-values, confidence intervals)
    - Correlation matrix generation
    - Multi-lag correlation analysis

Usage:
    analyzer = CorrelationAnalyzer()

    # Calculate correlation matrix
    corr_matrix = analyzer.calculate_correlation_matrix(
        alt_data_df,
        returns_df
    )

    # Identify leading indicators
    leading_indicators = analyzer.identify_leading_indicators(
        visitor_data,
        stock_returns,
        max_lag=20
    )

    # Calculate rolling correlation
    rolling_corr = analyzer.calculate_rolling_correlation(
        alt_data_df,
        stock_prices,
        window=60
    )

    # Calculate Sharpe ratios
    sharpe_comparison = analyzer.calculate_sharpe_comparison(
        returns_without_signal,
        returns_with_signal,
        risk_free_rate=0.02
    )
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

import pandas as pd
import numpy as np
from scipy import stats

logger = logging.getLogger("hk_quant_system.correlation_analyzer")


class CorrelationMethod(Enum):
    """Correlation calculation methods"""
    PEARSON = "pearson"  # Linear correlation
    SPEARMAN = "spearman"  # Rank-based correlation
    KENDALL = "kendall"  # Rank-based, more robust to outliers


class CorrelationAnalyzer:
    """
    Correlation analyzer for alternative data relationships.

    Calculates various correlation metrics between alternative data
    indicators and stock returns to identify useful signals.

    Attributes:
        correlation_method: Pearson, Spearman, or Kendall
        min_periods: Minimum observations required for calculation
        significance_level: p-value threshold for significance
    """

    def __init__(
        self,
        correlation_method: str = "pearson",
        min_periods: int = 20,
        significance_level: float = 0.05,
    ):
        """
        Initialize CorrelationAnalyzer.

        Args:
            correlation_method: "pearson", "spearman", or "kendall"
            min_periods: Minimum data points required
            significance_level: p-value threshold for statistical significance
        """
        self.correlation_method = CorrelationMethod(correlation_method)
        self.min_periods = min_periods
        self.significance_level = significance_level

        # Cache for analysis results
        self.last_analysis = None
        self.correlations = {}
        self.p_values = {}

        logger.info(
            f"Initialized CorrelationAnalyzer: method={correlation_method}, "
            f"min_periods={min_periods}, significance_level={significance_level}"
        )

    def calculate_correlation_matrix(
        self,
        alt_data: pd.DataFrame,
        returns: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        Calculate correlation matrix between alternative data and returns.

        Args:
            alt_data: Alternative data indicators (multiple columns)
            returns: Stock returns or price changes (multiple columns)

        Returns:
            Dictionary with:
                - correlation_matrix: correlations between each alt_data
                  and each return series
                - p_values: statistical significance
                - significant_correlations: pairs with p < threshold
                - summary: statistics on correlations
        """
        if alt_data.empty or returns.empty:
            logger.warning("Empty DataFrames provided")
            return {
                "correlation_matrix": pd.DataFrame(),
                "p_values": pd.DataFrame(),
                "significant_correlations": [],
                "summary": {},
            }

        # Align dates
        common_dates = alt_data.index.intersection(returns.index)
        if len(common_dates) < self.min_periods:
            logger.error(f"Insufficient data: only {len(common_dates)} common dates")
            return None

        alt_data_aligned = alt_data.loc[common_dates]
        returns_aligned = returns.loc[common_dates]

        # Calculate correlation matrix
        correlations = pd.DataFrame(
            index=alt_data_aligned.columns, columns=returns_aligned.columns
        )
        p_values = pd.DataFrame(
            index=alt_data_aligned.columns, columns=returns_aligned.columns
        )
        significant_pairs = []

        for alt_col in alt_data_aligned.columns:
            for ret_col in returns_aligned.columns:
                # Remove NaN values
                valid_mask = (
                    alt_data_aligned[alt_col].notna()
                    & returns_aligned[ret_col].notna()
                )
                valid_alt = alt_data_aligned.loc[valid_mask, alt_col]
                valid_ret = returns_aligned.loc[valid_mask, ret_col]

                if len(valid_alt) < self.min_periods:
                    correlations.loc[alt_col, ret_col] = np.nan
                    p_values.loc[alt_col, ret_col] = np.nan
                    continue

                # Calculate correlation based on method
                if self.correlation_method == CorrelationMethod.PEARSON:
                    corr, pval = stats.pearsonr(valid_alt, valid_ret)
                elif self.correlation_method == CorrelationMethod.SPEARMAN:
                    corr, pval = stats.spearmanr(valid_alt, valid_ret)
                else:  # KENDALL
                    corr, pval = stats.kendalltau(valid_alt, valid_ret)

                correlations.loc[alt_col, ret_col] = corr
                p_values.loc[alt_col, ret_col] = pval

                # Check significance
                if pval < self.significance_level:
                    significant_pairs.append({
                        "indicator": alt_col,
                        "stock": ret_col,
                        "correlation": corr,
                        "p_value": pval,
                        "strength": self._correlation_strength(corr),
                    })

        # Convert to numeric
        correlations = correlations.astype(float)
        p_values = p_values.astype(float)

        # Calculate summary statistics
        all_corrs = correlations.values.flatten()
        all_corrs = all_corrs[~np.isnan(all_corrs)]

        summary = {
            "mean_correlation": np.mean(all_corrs),
            "std_correlation": np.std(all_corrs),
            "min_correlation": np.min(all_corrs),
            "max_correlation": np.max(all_corrs),
            "significant_pairs": len(significant_pairs),
            "total_pairs": correlations.size - np.isnan(correlations.values).sum(),
        }

        result = {
            "correlation_matrix": correlations,
            "p_values": p_values,
            "significant_correlations": significant_pairs,
            "summary": summary,
            "analysis_date": datetime.now().isoformat(),
            "method": self.correlation_method.value,
        }

        self.last_analysis = result
        logger.info(f"Calculated correlation matrix: {len(significant_pairs)} significant pairs")

        return result

    def identify_leading_indicators(
        self,
        indicator_data: pd.Series,
        returns_data: pd.Series,
        max_lag: int = 20,
    ) -> Dict[str, Any]:
        """
        Identify if indicator leads or lags stock returns.

        Tests correlation at various lags to detect leading indicators.

        Args:
            indicator_data: Alternative data time series
            returns_data: Stock returns time series
            max_lag: Maximum lag to test in days

        Returns:
            Dictionary with:
                - lag_correlations: correlation at each lag
                - peak_lag: lag with highest correlation
                - peak_correlation: correlation at peak lag
                - is_leading: True if indicator leads returns
                - interpretation: Human-readable description
        """
        if indicator_data.empty or returns_data.empty:
            logger.warning("Empty data provided")
            return None

        # Align data
        common_dates = indicator_data.index.intersection(returns_data.index)
        if len(common_dates) < self.min_periods:
            logger.error(f"Insufficient data: only {len(common_dates)} common dates")
            return None

        indicator_aligned = indicator_data.loc[common_dates]
        returns_aligned = returns_data.loc[common_dates]

        # Calculate correlation at various lags
        lag_correlations = {}
        lag_pvalues = {}

        for lag in range(-max_lag, max_lag + 1):
            if lag < 0:
                # Indicator lags (returns lead)
                ind = indicator_aligned.shift(-lag)
                ret = returns_aligned
            elif lag > 0:
                # Indicator leads (returns lag)
                ind = indicator_aligned
                ret = returns_aligned.shift(lag)
            else:
                # No lag
                ind = indicator_aligned
                ret = returns_aligned

            # Remove NaN
            valid_mask = ind.notna() & ret.notna()
            valid_ind = ind[valid_mask]
            valid_ret = ret[valid_mask]

            if len(valid_ind) < self.min_periods:
                lag_correlations[lag] = np.nan
                lag_pvalues[lag] = np.nan
                continue

            # Calculate correlation
            if self.correlation_method == CorrelationMethod.PEARSON:
                corr, pval = stats.pearsonr(valid_ind, valid_ret)
            elif self.correlation_method == CorrelationMethod.SPEARMAN:
                corr, pval = stats.spearmanr(valid_ind, valid_ret)
            else:
                corr, pval = stats.kendalltau(valid_ind, valid_ret)

            lag_correlations[lag] = corr
            lag_pvalues[lag] = pval

        # Find peak correlation
        valid_lags = {k: v for k, v in lag_correlations.items() if not np.isnan(v)}
        if not valid_lags:
            logger.warning("No valid correlations calculated")
            return None

        peak_lag = max(valid_lags, key=lambda k: abs(valid_lags[k]))
        peak_correlation = valid_lags[peak_lag]
        peak_pvalue = lag_pvalues[peak_lag]

        # Interpret results
        is_leading = peak_lag > 0
        is_significant = peak_pvalue < self.significance_level

        if is_leading:
            interpretation = (
                f"Indicator leads returns by {peak_lag} days "
                f"(corr={peak_correlation:.3f}, p={peak_pvalue:.4f})"
            )
        else:
            interpretation = (
                f"Indicator lags returns by {abs(peak_lag)} days "
                f"(corr={peak_correlation:.3f}, p={peak_pvalue:.4f})"
            )

        result = {
            "lag_correlations": lag_correlations,
            "lag_pvalues": lag_pvalues,
            "peak_lag": peak_lag,
            "peak_correlation": peak_correlation,
            "peak_pvalue": peak_pvalue,
            "is_leading": is_leading,
            "is_significant": is_significant,
            "interpretation": interpretation,
            "analysis_date": datetime.now().isoformat(),
        }

        logger.info(f"Leading indicator analysis: {interpretation}")
        return result

    def calculate_rolling_correlation(
        self,
        alt_data: pd.Series,
        price_data: pd.Series,
        window: int = 60,
    ) -> Dict[str, Any]:
        """
        Calculate rolling correlation to detect regime changes.

        Args:
            alt_data: Alternative data time series
            price_data: Price or return series
            window: Rolling window size in days

        Returns:
            Dictionary with:
                - rolling_correlation: rolling correlation series
                - correlation_regime: HIGH/MEDIUM/LOW/DECOUPLING
                - regime_changes: dates where regime changed
                - stability_score: how stable correlation is
        """
        if alt_data.empty or price_data.empty:
            logger.warning("Empty data provided")
            return None

        # Align data
        common_dates = alt_data.index.intersection(price_data.index)
        if len(common_dates) < window:
            logger.error(f"Insufficient data for {window}-day window")
            return None

        alt_aligned = alt_data.loc[common_dates]
        price_aligned = price_data.loc[common_dates]

        # Calculate rolling correlation
        rolling_corr = []
        rolling_dates = []

        for i in range(len(alt_aligned) - window + 1):
            window_alt = alt_aligned.iloc[i : i + window]
            window_price = price_aligned.iloc[i : i + window]

            # Remove NaN
            valid_mask = window_alt.notna() & window_price.notna()
            valid_alt = window_alt[valid_mask]
            valid_price = window_price[valid_mask]

            if len(valid_alt) < self.min_periods:
                rolling_corr.append(np.nan)
                rolling_dates.append(alt_aligned.index[i + window - 1])
                continue

            # Calculate correlation
            if self.correlation_method == CorrelationMethod.PEARSON:
                corr, _ = stats.pearsonr(valid_alt, valid_price)
            elif self.correlation_method == CorrelationMethod.SPEARMAN:
                corr, _ = stats.spearmanr(valid_alt, valid_price)
            else:
                corr, _ = stats.kendalltau(valid_alt, valid_price)

            rolling_corr.append(corr)
            rolling_dates.append(alt_aligned.index[i + window - 1])

        rolling_corr_series = pd.Series(rolling_corr, index=rolling_dates)

        # Detect regime changes
        regime_changes = []
        current_regime = None

        for i, corr in enumerate(rolling_corr_series):
            if np.isnan(corr):
                continue

            # Classify regime
            regime = self._classify_correlation_regime(corr)

            if regime != current_regime and current_regime is not None:
                regime_changes.append({
                    "date": rolling_corr_series.index[i],
                    "from_regime": current_regime,
                    "to_regime": regime,
                    "correlation": corr,
                })

            current_regime = regime

        # Calculate stability score
        valid_corrs = rolling_corr_series.dropna()
        if len(valid_corrs) > 1:
            # Low std = high stability
            corr_std = valid_corrs.std()
            stability_score = 1.0 / (1.0 + corr_std)  # Range [0, 1]
        else:
            stability_score = np.nan

        result = {
            "rolling_correlation": rolling_corr_series,
            "regime_changes": regime_changes,
            "stability_score": stability_score,
            "mean_correlation": valid_corrs.mean() if len(valid_corrs) > 0 else np.nan,
            "min_correlation": valid_corrs.min() if len(valid_corrs) > 0 else np.nan,
            "max_correlation": valid_corrs.max() if len(valid_corrs) > 0 else np.nan,
            "analysis_date": datetime.now().isoformat(),
            "window": window,
        }

        logger.info(
            f"Rolling correlation: {len(regime_changes)} regime changes detected, "
            f"stability_score={stability_score:.3f}"
        )

        return result

    def calculate_sharpe_comparison(
        self,
        returns_without_signal: pd.Series,
        returns_with_signal: pd.Series,
        risk_free_rate: float = 0.02,
    ) -> Dict[str, Any]:
        """
        Compare Sharpe ratios with and without alternative data signals.

        Args:
            returns_without_signal: Returns from baseline strategy
            returns_with_signal: Returns from strategy using alt data
            risk_free_rate: Annual risk-free rate (e.g., 0.02 for 2%)

        Returns:
            Dictionary with:
                - sharpe_without_signal: baseline Sharpe ratio
                - sharpe_with_signal: Sharpe ratio with alt data
                - sharpe_improvement: absolute and percentage improvement
                - volatility_without: baseline volatility
                - volatility_with: volatility with alt data
                - summary: human-readable summary
        """
        if returns_without_signal.empty or returns_with_signal.empty:
            logger.warning("Empty returns data provided")
            return None

        # Calculate annual metrics
        # Assume daily returns, 252 trading days per year
        annual_scale = 252

        # Without signal
        mean_return_without = returns_without_signal.mean() * annual_scale
        vol_without = returns_without_signal.std() * np.sqrt(annual_scale)
        sharpe_without = (mean_return_without - risk_free_rate) / vol_without if vol_without > 0 else 0

        # With signal
        mean_return_with = returns_with_signal.mean() * annual_scale
        vol_with = returns_with_signal.std() * np.sqrt(annual_scale)
        sharpe_with = (mean_return_with - risk_free_rate) / vol_with if vol_with > 0 else 0

        # Calculate improvements
        sharpe_improvement_abs = sharpe_with - sharpe_without
        sharpe_improvement_pct = (sharpe_improvement_abs / sharpe_without * 100) if sharpe_without != 0 else 0
        return_improvement_pct = ((mean_return_with - mean_return_without) / mean_return_without * 100) if mean_return_without != 0 else 0
        volatility_reduction_pct = ((vol_without - vol_with) / vol_without * 100) if vol_without != 0 else 0

        summary = (
            f"Without alt data: Return={mean_return_without:.1%}, "
            f"Volatility={vol_without:.1%}, Sharpe={sharpe_without:.3f}. "
            f"With alt data: Return={mean_return_with:.1%}, "
            f"Volatility={vol_with:.1%}, Sharpe={sharpe_with:.3f}. "
            f"Improvement: Sharpe +{sharpe_improvement_pct:+.1f}%, "
            f"Return +{return_improvement_pct:+.1f}%, "
            f"Volatility {volatility_reduction_pct:.1f}% lower."
        )

        result = {
            "sharpe_without_signal": sharpe_without,
            "sharpe_with_signal": sharpe_with,
            "sharpe_improvement_absolute": sharpe_improvement_abs,
            "sharpe_improvement_percentage": sharpe_improvement_pct,
            "return_without_signal": mean_return_without,
            "return_with_signal": mean_return_with,
            "return_improvement_percentage": return_improvement_pct,
            "volatility_without_signal": vol_without,
            "volatility_with_signal": vol_with,
            "volatility_reduction_percentage": volatility_reduction_pct,
            "summary": summary,
            "analysis_date": datetime.now().isoformat(),
        }

        logger.info(f"Sharpe comparison: {summary}")
        return result

    @staticmethod
    def _correlation_strength(correlation: float) -> str:
        """Classify correlation strength."""
        abs_corr = abs(correlation)
        if abs_corr >= 0.7:
            return "strong"
        elif abs_corr >= 0.5:
            return "moderate"
        elif abs_corr >= 0.3:
            return "weak"
        else:
            return "very_weak"

    @staticmethod
    def _classify_correlation_regime(correlation: float) -> str:
        """Classify correlation regime."""
        if correlation >= 0.7:
            return "HIGH"
        elif correlation >= 0.4:
            return "MEDIUM"
        elif correlation >= 0.1:
            return "LOW"
        else:
            return "DECOUPLING"

    def get_last_analysis(self) -> Optional[Dict[str, Any]]:
        """Get most recent analysis results."""
        return self.last_analysis


# Usage examples
if __name__ == "__main__":
    import numpy as np

    # Create sample data
    dates = pd.date_range("2025-01-01", "2025-10-18", freq="D")

    # Alternative data (e.g., HIBOR rates)
    alt_data_df = pd.DataFrame({
        "HIBOR_Overnight": np.random.uniform(3.0, 4.5, len(dates)),
        "HIBOR_3M": np.random.uniform(3.5, 5.0, len(dates)),
    }, index=dates)

    # Stock returns (e.g., Bank stocks)
    returns_df = pd.DataFrame({
        "0939.HK": np.random.normal(-0.001, 0.02, len(dates)),  # CCB
        "1398.HK": np.random.normal(-0.0005, 0.025, len(dates)),  # ICBC
    }, index=dates)

    # Create analyzer
    analyzer = CorrelationAnalyzer()

    # Calculate correlation matrix
    corr_result = analyzer.calculate_correlation_matrix(alt_data_df, returns_df)
    print("Correlation Matrix:")
    print(corr_result["correlation_matrix"])
    print(f"\nSignificant correlations: {len(corr_result['significant_correlations'])}")

    # Test rolling correlation
    rolling_result = analyzer.calculate_rolling_correlation(
        alt_data_df["HIBOR_Overnight"], returns_df["0939.HK"], window=30
    )
    print(f"\nRolling correlation stability score: {rolling_result['stability_score']:.3f}")

    # Test Sharpe comparison
    returns_base = pd.Series(np.random.normal(0.0005, 0.02, 252))
    returns_signal = pd.Series(np.random.normal(0.001, 0.018, 252))

    sharpe_result = analyzer.calculate_sharpe_comparison(returns_base, returns_signal)
    print(f"\nSharpe Comparison:")
    print(f"Without signal: {sharpe_result['sharpe_without_signal']:.3f}")
    print(f"With signal: {sharpe_result['sharpe_with_signal']:.3f}")
    print(f"Improvement: {sharpe_result['sharpe_improvement_percentage']:+.1f}%")
