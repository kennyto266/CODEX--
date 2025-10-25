"""
Signal Validation Framework

Provides comprehensive signal validation including out-of-sample testing,
overfitting detection, statistical significance testing, and signal stability analysis.

Features:
    - Out-of-sample (OOS) testing and analysis
    - Overfitting detection and quantification
    - Walk-forward analysis
    - Statistical significance testing
    - Signal stability assessment
    - Degradation analysis

Usage:
    validator = SignalValidator()

    train_data, test_data = validator.split_data(data, train_ratio=0.7)

    overfitting = validator.detect_overfitting(
        train_metrics={'sharpe': 1.5, 'win_rate': 0.65},
        test_metrics={'sharpe': 0.8, 'win_rate': 0.55}
    )

    significance = validator.validate_statistical_significance(trades)
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
import pandas as pd
from scipy import stats
from datetime import datetime, timedelta


class ValidationResult(str, Enum):
    """Signal validation result"""
    VALID = "valid"
    NEEDS_REVIEW = "needs_review"
    INVALID = "invalid"
    INSUFFICIENT_DATA = "insufficient_data"


class OverfittingLevel(str, Enum):
    """Level of overfitting detected"""
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"


@dataclass
class OutOfSampleResult:
    """Out-of-sample testing results"""
    train_metrics: Dict[str, float]
    test_metrics: Dict[str, float]
    degradation: Dict[str, float]
    max_degradation_pct: float
    avg_degradation_pct: float
    oos_valid: bool
    oos_confidence: float


@dataclass
class OverfittingAnalysis:
    """Overfitting analysis results"""
    level: OverfittingLevel
    sharpe_degradation: float
    win_rate_degradation: float
    max_loss_expansion: float
    is_overfitted: bool
    risk_score: float  # 0-1, higher = more overfitting risk


@dataclass
class StatisticalSignificance:
    """Statistical significance test results"""
    p_value: float
    is_significant: bool
    confidence_level: float
    effect_size: float
    minimum_sample_size: int
    current_sample_size: int
    power: float


@dataclass
class SignalStability:
    """Signal stability analysis"""
    monthly_consistency: float
    quarterly_consistency: float
    correlation_over_time: float
    degradation_trend: float
    is_stable: bool
    stability_score: float


class SignalValidator:
    """
    Signal Validation Framework

    Validates trading signals through multiple statistical and empirical tests
    to assess robustness and avoid overfitting issues.
    """

    def __init__(
        self,
        min_sample_size: int = 30,
        overfitting_threshold: float = 0.2,
        significance_level: float = 0.05,
        degradation_threshold: float = 0.25
    ):
        """
        Initialize Signal Validator

        Args:
            min_sample_size: Minimum trades needed for statistical validity
            overfitting_threshold: Max allowed degradation ratio (20%)
            significance_level: Statistical significance level (alpha)
            degradation_threshold: Max allowed test degradation
        """
        assert min_sample_size >= 20, "Minimum 20 sample size"
        assert 0 < overfitting_threshold <= 1, "Invalid threshold"
        assert 0 < significance_level < 1, "Invalid significance level"

        self.min_sample_size = min_sample_size
        self.overfitting_threshold = overfitting_threshold
        self.significance_level = significance_level
        self.degradation_threshold = degradation_threshold

        self.logger = logging.getLogger("hk_quant_system.signal_validation")

    def split_data(
        self,
        data: pd.DataFrame,
        train_ratio: float = 0.7,
        method: str = "sequential"
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split data into training and testing sets

        Args:
            data: Full dataset
            train_ratio: Fraction for training (0-1)
            method: Split method ('sequential', 'random', 'time-based')

        Returns:
            Tuple of (train_data, test_data)
        """
        try:
            if not isinstance(data, pd.DataFrame) or len(data) < 20:
                raise ValueError("Invalid data: need DataFrame with >= 20 rows")

            train_size = int(len(data) * train_ratio)

            if method == "sequential":
                # Chronological split (forward-looking)
                train_data = data.iloc[:train_size]
                test_data = data.iloc[train_size:]

            elif method == "random":
                # Random split (shuffled indices)
                indices = np.random.permutation(len(data))
                train_indices = sorted(indices[:train_size])
                test_indices = sorted(indices[train_size:])
                train_data = data.iloc[train_indices]
                test_data = data.iloc[test_indices]

            elif method == "time-based":
                # Time-based expansion window
                train_data = data.iloc[:train_size]
                test_data = data.iloc[train_size:]

            else:
                raise ValueError(f"Unknown split method: {method}")

            self.logger.info(f"Data split: {len(train_data)} train, {len(test_data)} test samples")
            return train_data, test_data

        except Exception as e:
            self.logger.error(f"Error splitting data: {e}")
            raise

    def detect_overfitting(
        self,
        train_metrics: Dict[str, float],
        test_metrics: Dict[str, float]
    ) -> OverfittingAnalysis:
        """
        Detect and quantify overfitting

        Args:
            train_metrics: Performance metrics on training set
            test_metrics: Performance metrics on test set

        Returns:
            OverfittingAnalysis with detailed assessment
        """
        try:
            analysis = OverfittingAnalysis(
                level=OverfittingLevel.NONE,
                sharpe_degradation=0.0,
                win_rate_degradation=0.0,
                max_loss_expansion=0.0,
                is_overfitted=False,
                risk_score=0.0
            )

            if not train_metrics or not test_metrics:
                return analysis

            # Calculate Sharpe degradation
            train_sharpe = train_metrics.get('sharpe', 0.0)
            test_sharpe = test_metrics.get('sharpe', 0.0)

            if train_sharpe > 0:
                sharpe_deg = (train_sharpe - test_sharpe) / train_sharpe
                analysis.sharpe_degradation = max(sharpe_deg, 0.0)

            # Calculate win rate degradation
            train_wr = train_metrics.get('win_rate', 0.0)
            test_wr = test_metrics.get('win_rate', 0.0)

            if train_wr > 0:
                wr_deg = (train_wr - test_wr) / train_wr
                analysis.win_rate_degradation = max(wr_deg, 0.0)

            # Calculate max loss expansion
            train_max_loss = abs(train_metrics.get('max_loss', 0.0))
            test_max_loss = abs(test_metrics.get('max_loss', 0.0))

            if train_max_loss > 0:
                loss_exp = (test_max_loss - train_max_loss) / train_max_loss
                analysis.max_loss_expansion = max(loss_exp, 0.0)

            # Determine overfitting level
            avg_degradation = (
                analysis.sharpe_degradation +
                analysis.win_rate_degradation
            ) / 2

            if avg_degradation < 0.05:
                analysis.level = OverfittingLevel.NONE
                analysis.risk_score = 0.0
            elif avg_degradation < 0.15:
                analysis.level = OverfittingLevel.LOW
                analysis.risk_score = 0.2
            elif avg_degradation < 0.30:
                analysis.level = OverfittingLevel.MODERATE
                analysis.risk_score = 0.5
            elif avg_degradation < 0.50:
                analysis.level = OverfittingLevel.HIGH
                analysis.risk_score = 0.75
            else:
                analysis.level = OverfittingLevel.SEVERE
                analysis.risk_score = 1.0

            # Determine if overfitted
            analysis.is_overfitted = analysis.risk_score > 0.5

            self.logger.info(
                f"Overfitting Analysis: {analysis.level.value}, "
                f"Sharpe deg={analysis.sharpe_degradation:.1%}, "
                f"WR deg={analysis.win_rate_degradation:.1%}"
            )

            return analysis

        except Exception as e:
            self.logger.error(f"Error detecting overfitting: {e}")
            return OverfittingAnalysis(
                level=OverfittingLevel.NONE,
                sharpe_degradation=0.0,
                win_rate_degradation=0.0,
                max_loss_expansion=0.0,
                is_overfitted=False,
                risk_score=0.0
            )

    def validate_statistical_significance(
        self,
        trades: List[Dict[str, Any]]
    ) -> StatisticalSignificance:
        """
        Validate statistical significance of trade results

        Args:
            trades: List of trade records with pnl

        Returns:
            StatisticalSignificance test results
        """
        try:
            if len(trades) < self.min_sample_size:
                return StatisticalSignificance(
                    p_value=1.0,
                    is_significant=False,
                    confidence_level=0.0,
                    effect_size=0.0,
                    minimum_sample_size=self.min_sample_size,
                    current_sample_size=len(trades),
                    power=0.0
                )

            # Extract PnL
            pnls = np.array([t.get('pnl', 0) for t in trades])

            # Test if mean PnL is significantly different from zero
            t_stat, p_value = stats.ttest_1samp(pnls, 0)

            # Calculate effect size (Cohen's d)
            mean_pnl = np.mean(pnls)
            std_pnl = np.std(pnls)
            cohens_d = mean_pnl / std_pnl if std_pnl > 0 else 0

            # Determine significance
            is_significant = p_value < self.significance_level

            # Calculate statistical power (approximation)
            n = len(pnls)
            power = self._calculate_power(cohens_d, n)

            # Minimum sample size needed for 80% power
            min_n = self._calculate_minimum_sample_size(cohens_d)

            return StatisticalSignificance(
                p_value=p_value,
                is_significant=is_significant,
                confidence_level=1.0 - p_value if is_significant else 0.0,
                effect_size=abs(cohens_d),
                minimum_sample_size=min_n,
                current_sample_size=n,
                power=power
            )

        except Exception as e:
            self.logger.error(f"Error validating statistical significance: {e}")
            return StatisticalSignificance(
                p_value=1.0,
                is_significant=False,
                confidence_level=0.0,
                effect_size=0.0,
                minimum_sample_size=self.min_sample_size,
                current_sample_size=len(trades),
                power=0.0
            )

    def analyze_signal_stability(
        self,
        trades: List[Dict[str, Any]],
        group_by_period: str = "monthly"
    ) -> SignalStability:
        """
        Analyze signal stability over time

        Args:
            trades: List of trades with dates
            group_by_period: 'monthly', 'quarterly', or 'daily'

        Returns:
            SignalStability assessment
        """
        try:
            if not trades or len(trades) < 10:
                return SignalStability(
                    monthly_consistency=0.0,
                    quarterly_consistency=0.0,
                    correlation_over_time=0.0,
                    degradation_trend=0.0,
                    is_stable=False,
                    stability_score=0.0
                )

            # Create DataFrame for easier analysis
            df = pd.DataFrame(trades)

            # Convert dates to datetime if needed
            for date_col in ['entry_date', 'exit_date']:
                if date_col in df.columns:
                    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

            # Group wins by period
            if 'entry_date' in df.columns:
                df['date'] = df['entry_date']
                df['month'] = df['date'].dt.to_period('M')
                df['quarter'] = df['date'].dt.to_period('Q')

                # Monthly win rates
                monthly_wr = (df.groupby('month')['pnl'].apply(lambda x: (x > 0).mean()))
                monthly_consistency = monthly_wr.std()  # Lower = more consistent

                # Quarterly win rates
                quarterly_wr = (df.groupby('quarter')['pnl'].apply(lambda x: (x > 0).mean()))
                quarterly_consistency = quarterly_wr.std()

                # Correlation of returns over time
                if len(monthly_wr) > 1:
                    correlation = monthly_wr.corr(pd.Series(range(len(monthly_wr))))
                else:
                    correlation = 0.0

                # Trend analysis (degradation)
                if len(monthly_wr) > 2:
                    x = np.arange(len(monthly_wr))
                    y = monthly_wr.values
                    z = np.polyfit(x, y, 1)
                    degradation_trend = z[0]  # Negative = deteriorating
                else:
                    degradation_trend = 0.0
            else:
                monthly_consistency = 0.0
                quarterly_consistency = 0.0
                correlation = 0.0
                degradation_trend = 0.0

            # Calculate stability score
            stability_score = 1.0 - min(monthly_consistency, 1.0)
            is_stable = stability_score > 0.5 and degradation_trend > -0.05

            return SignalStability(
                monthly_consistency=monthly_consistency,
                quarterly_consistency=quarterly_consistency,
                correlation_over_time=correlation,
                degradation_trend=degradation_trend,
                is_stable=is_stable,
                stability_score=stability_score
            )

        except Exception as e:
            self.logger.error(f"Error analyzing signal stability: {e}")
            return SignalStability(
                monthly_consistency=0.0,
                quarterly_consistency=0.0,
                correlation_over_time=0.0,
                degradation_trend=0.0,
                is_stable=False,
                stability_score=0.0
            )

    def run_walk_forward_analysis(
        self,
        data: pd.DataFrame,
        strategy_func,
        window_size: int = 60,
        step_size: int = 10
    ) -> Dict[str, Any]:
        """
        Run walk-forward analysis

        Args:
            data: Full historical data
            strategy_func: Function to apply to each window
            window_size: Training window size (days)
            step_size: Step size for moving window

        Returns:
            Walk-forward analysis results
        """
        try:
            results = {
                'windows': [],
                'avg_train_sharpe': 0.0,
                'avg_test_sharpe': 0.0,
                'sharpe_degradation': 0.0,
                'realized_trades': 0,
                'win_rate': 0.0
            }

            if len(data) < window_size * 2:
                return results

            all_trades = []
            train_sharpes = []
            test_sharpes = []

            # Walk forward through data
            for i in range(0, len(data) - window_size * 2, step_size):
                train_end = i + window_size
                test_end = min(train_end + step_size, len(data))

                train_data = data.iloc[i:train_end]
                test_data = data.iloc[train_end:test_end]

                # Run strategy on both windows
                try:
                    train_metrics = strategy_func(train_data)
                    test_metrics = strategy_func(test_data)

                    train_sharpes.append(train_metrics.get('sharpe', 0.0))
                    test_sharpes.append(test_metrics.get('sharpe', 0.0))

                except Exception as e:
                    self.logger.debug(f"Skipping window: {e}")
                    continue

            # Calculate aggregate metrics
            if train_sharpes:
                results['avg_train_sharpe'] = np.mean(train_sharpes)
                results['avg_test_sharpe'] = np.mean(test_sharpes)
                results['sharpe_degradation'] = (
                    results['avg_train_sharpe'] - results['avg_test_sharpe']
                ) / max(results['avg_train_sharpe'], 0.01)

            return results

        except Exception as e:
            self.logger.error(f"Error in walk-forward analysis: {e}")
            return {}

    def generate_validation_report(
        self,
        train_data: pd.DataFrame,
        test_data: pd.DataFrame,
        train_metrics: Dict[str, float],
        test_metrics: Dict[str, float],
        trades: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive validation report

        Args:
            train_data: Training dataset
            test_data: Test dataset
            train_metrics: Training metrics
            test_metrics: Test metrics
            trades: Trade records

        Returns:
            Comprehensive validation report
        """
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'validation_result': ValidationResult.VALID,
                'score': 0.0,
                'detailed_findings': {}
            }

            # Test 1: Overfitting
            overfitting = self.detect_overfitting(train_metrics, test_metrics)
            report['detailed_findings']['overfitting'] = {
                'level': overfitting.level.value,
                'risk_score': overfitting.risk_score,
                'is_overfitted': overfitting.is_overfitted
            }

            # Test 2: Statistical significance
            significance = self.validate_statistical_significance(trades)
            report['detailed_findings']['significance'] = {
                'is_significant': significance.is_significant,
                'p_value': significance.p_value,
                'effect_size': significance.effect_size
            }

            # Test 3: Signal stability
            stability = self.analyze_signal_stability(trades)
            report['detailed_findings']['stability'] = {
                'is_stable': stability.is_stable,
                'stability_score': stability.stability_score,
                'degradation_trend': stability.degradation_trend
            }

            # Determine overall validation result
            if overfitting.is_overfitted or not significance.is_significant:
                report['validation_result'] = ValidationResult.INVALID
                report['score'] = 0.3
            elif not stability.is_stable:
                report['validation_result'] = ValidationResult.NEEDS_REVIEW
                report['score'] = 0.6
            else:
                report['validation_result'] = ValidationResult.VALID
                report['score'] = 0.9

            self.logger.info(f"Validation Report: {report['validation_result'].value}")
            return report

        except Exception as e:
            self.logger.error(f"Error generating validation report: {e}")
            return {'validation_result': ValidationResult.INVALID, 'score': 0.0}

    @staticmethod
    def _calculate_power(effect_size: float, n: int, alpha: float = 0.05) -> float:
        """Approximate statistical power using effect size"""
        if effect_size == 0:
            return 0.0
        # Simplified power calculation
        t_crit = stats.t.ppf(1 - alpha/2, n - 1)
        power = 1 - stats.nct.cdf(t_crit, n - 1, effect_size * np.sqrt(n))
        return float(np.clip(power, 0.0, 1.0))

    @staticmethod
    def _calculate_minimum_sample_size(effect_size: float, power: float = 0.8) -> int:
        """Calculate minimum sample size for desired power"""
        if effect_size <= 0:
            return 30
        # Approximation for minimum n
        n = int((2.8 / (effect_size ** 2)) * ((1.96 + stats.norm.ppf(power)) ** 2))
        return max(n, 20)


__all__ = [
    'SignalValidator',
    'ValidationResult',
    'OverfittingAnalysis',
    'OutOfSampleResult',
    'StatisticalSignificance',
    'SignalStability',
    'OverfittingLevel'
]
