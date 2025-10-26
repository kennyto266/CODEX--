"""
Quality Scorer Module - Alternative Data Pipeline

Calculates data quality metrics and assigns quality grades.

Features:
    - Completeness scoring (% of non-null values)
    - Freshness scoring (how recent the data is)
    - Consistency scoring (variance and uniformity)
    - Overall quality grade (A-F or 0-1 score)
    - Detailed quality reports
    - Configurable thresholds

Quality Grade Scale:
    A (0.9-1.0):  Excellent quality, ready for production
    B (0.8-0.9):  Good quality, minor issues
    C (0.7-0.8):  Fair quality, acceptable with caution
    D (0.6-0.7):  Poor quality, significant issues
    F (0.0-0.6):  Very poor quality, not recommended

Usage:
    scorer = QualityScorer()
    score = scorer.calculate_quality(df, date_column='date')
    grade = scorer.get_grade()
    report = scorer.get_report()
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

import pandas as pd
import numpy as np

logger = logging.getLogger("hk_quant_system.quality_scorer")


class QualityGrade(Enum):
    """Data quality grades"""
    A = "A"  # Excellent
    B = "B"  # Good
    C = "C"  # Fair
    D = "D"  # Poor
    F = "F"  # Very Poor


class QualityScorer:
    """
    Quality scorer for alternative data.

    Evaluates data quality across multiple dimensions:
    - Completeness: percentage of non-null values
    - Freshness: recency of the data
    - Consistency: uniformity and stability
    - Statistical properties: distribution, outliers

    Attributes:
        completeness_weight: Weight for completeness (0-1)
        freshness_weight: Weight for freshness (0-1)
        consistency_weight: Weight for consistency (0-1)
    """

    def __init__(
        self,
        completeness_weight: float = 0.5,
        freshness_weight: float = 0.3,
        consistency_weight: float = 0.2,
        max_age_hours: int = 24,
    ):
        """
        Initialize QualityScorer.

        Args:
            completeness_weight: Weight for completeness metric
            freshness_weight: Weight for freshness metric
            consistency_weight: Weight for consistency metric
            max_age_hours: Maximum acceptable age in hours
        """
        # Validate weights sum to 1
        total_weight = completeness_weight + freshness_weight + consistency_weight
        if not np.isclose(total_weight, 1.0):
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")

        self.completeness_weight = completeness_weight
        self.freshness_weight = freshness_weight
        self.consistency_weight = consistency_weight
        self.max_age_hours = max_age_hours

        # Storage for last calculation
        self.last_report = None
        self.last_score = None
        self.last_grade = None

        logger.info(
            f"Initialized QualityScorer: "
            f"completeness={completeness_weight:.1%}, "
            f"freshness={freshness_weight:.1%}, "
            f"consistency={consistency_weight:.1%}"
        )

    def calculate_quality(
        self,
        df: pd.DataFrame,
        date_column: Optional[str] = None,
        numeric_columns: Optional[List[str]] = None,
    ) -> float:
        """
        Calculate overall quality score.

        Args:
            df: Input DataFrame
            date_column: Name of date column for freshness scoring
            numeric_columns: Columns to analyze (None = all numeric)

        Returns:
            Quality score between 0 and 1
        """
        if df.empty:
            self.last_score = 0.0
            logger.warning("Empty DataFrame - score = 0.0")
            return 0.0

        # Identify numeric columns
        if numeric_columns is None:
            numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()

        # Calculate component scores
        completeness_score = self._calculate_completeness(df, numeric_columns)
        freshness_score = self._calculate_freshness(df, date_column)
        consistency_score = self._calculate_consistency(df, numeric_columns)

        # Weighted combination
        overall_score = (
            self.completeness_weight * completeness_score
            + self.freshness_weight * freshness_score
            + self.consistency_weight * consistency_score
        )

        # Determine grade
        grade = self._score_to_grade(overall_score)

        # Store results
        self.last_score = overall_score
        self.last_grade = grade
        self.last_report = {
            "timestamp": datetime.now().isoformat(),
            "overall_score": overall_score,
            "grade": grade.value,
            "completeness_score": completeness_score,
            "freshness_score": freshness_score,
            "consistency_score": consistency_score,
            "dataframe_shape": df.shape,
            "total_missing": df[numeric_columns].isnull().sum().sum(),
            "numeric_columns": numeric_columns,
        }

        logger.info(
            f"Quality calculation: score={overall_score:.3f}, "
            f"grade={grade.value}, "
            f"completeness={completeness_score:.1%}, "
            f"freshness={freshness_score:.1%}, "
            f"consistency={consistency_score:.1%}"
        )

        return overall_score

    def _calculate_completeness(
        self,
        df: pd.DataFrame,
        columns: List[str],
    ) -> float:
        """
        Calculate completeness score.

        Completeness = % of non-null values in numeric columns

        Returns:
            Score between 0 and 1
        """
        if not columns:
            return 1.0

        total_cells = len(df) * len(columns)
        missing_cells = df[columns].isnull().sum().sum()
        completeness = 1.0 - (missing_cells / total_cells) if total_cells > 0 else 0.0

        return max(0.0, min(1.0, completeness))

    def _calculate_freshness(
        self,
        df: pd.DataFrame,
        date_column: Optional[str] = None,
    ) -> float:
        """
        Calculate freshness score.

        Freshness based on how recent the most recent data point is.
        - 1.0 = data less than 1 hour old
        - 0.5 = data exactly max_age_hours old
        - 0.0 = data older than 2x max_age_hours

        Returns:
            Score between 0 and 1
        """
        if date_column is None or date_column not in df.columns:
            # No date column, assume current data
            logger.debug("No date column provided for freshness scoring")
            return 1.0

        try:
            # Get most recent date
            df_dates = pd.to_datetime(df[date_column], errors="coerce")
            latest_date = df_dates.max()

            if pd.isna(latest_date):
                logger.warning("No valid dates found in date column")
                return 0.5

            # Calculate age
            now = pd.Timestamp.now(tz=None)
            if latest_date.tzinfo is None:
                # Make both timezone-naive or timezone-aware
                age = now - latest_date
            else:
                age = now - latest_date

            age_hours = age.total_seconds() / 3600

            # Freshness scoring
            if age_hours <= 1:
                freshness = 1.0
            elif age_hours <= self.max_age_hours:
                # Linear decay from 1.0 to 0.5
                freshness = 1.0 - (0.5 * age_hours / self.max_age_hours)
            elif age_hours <= 2 * self.max_age_hours:
                # Linear decay from 0.5 to 0.0
                freshness = 0.5 * (1.0 - (age_hours - self.max_age_hours) / self.max_age_hours)
            else:
                freshness = 0.0

            logger.debug(
                f"Freshness scoring: latest_date={latest_date}, "
                f"age={age_hours:.1f}h, freshness={freshness:.1%}"
            )

            return max(0.0, min(1.0, freshness))

        except Exception as e:
            logger.warning(f"Error calculating freshness: {e}")
            return 0.5

    def _calculate_consistency(
        self,
        df: pd.DataFrame,
        columns: List[str],
    ) -> float:
        """
        Calculate consistency score.

        Consistency based on:
        - Value distribution (low variance = more consistent)
        - Absence of extreme outliers
        - Stable time-series properties (if time-ordered)

        Returns:
            Score between 0 and 1
        """
        if not columns:
            return 1.0

        consistency_scores = []

        for col in columns:
            # Skip if column has < 2 values
            valid_values = df[col].dropna()
            if len(valid_values) < 2:
                consistency_scores.append(0.5)
                continue

            # Check for zero variance
            if valid_values.std() == 0:
                consistency_scores.append(1.0)  # Perfectly consistent (constant)
                continue

            # Coefficient of variation (CV) - normalized standard deviation
            cv = valid_values.std() / (valid_values.mean() + 1e-10)

            # CV-based consistency score
            # cv=0 → score=1.0 (perfect consistency)
            # cv=1.0 → score=0.5 (moderate)
            # cv>2.0 → score=0.0 (highly variable)
            consistency = 1.0 / (1.0 + cv)

            # Check for extreme outliers (z-score > 4)
            z_scores = np.abs((valid_values - valid_values.mean()) / (valid_values.std() + 1e-10))
            extreme_outliers = (z_scores > 4).sum()

            if extreme_outliers > 0:
                extreme_penalty = min(0.3, 0.1 * extreme_outliers)
                consistency = max(0.0, consistency - extreme_penalty)

            consistency_scores.append(consistency)

        # Average consistency across columns
        avg_consistency = np.mean(consistency_scores) if consistency_scores else 0.5
        return max(0.0, min(1.0, avg_consistency))

    def _score_to_grade(self, score: float) -> QualityGrade:
        """Convert numeric score to letter grade."""
        if score >= 0.9:
            return QualityGrade.A
        elif score >= 0.8:
            return QualityGrade.B
        elif score >= 0.7:
            return QualityGrade.C
        elif score >= 0.6:
            return QualityGrade.D
        else:
            return QualityGrade.F

    def get_grade(self) -> Optional[str]:
        """Get letter grade from last calculation."""
        if self.last_grade is None:
            return None
        return self.last_grade.value

    def get_score(self) -> Optional[float]:
        """Get numeric score from last calculation."""
        return self.last_score

    def get_report(self) -> Optional[Dict[str, Any]]:
        """Get detailed report from last calculation."""
        return self.last_report.copy() if self.last_report else None

    def generate_quality_report_text(self) -> str:
        """Generate human-readable quality report."""
        if self.last_report is None:
            return "No quality calculation performed yet"

        report = self.last_report
        lines = [
            "=" * 60,
            "DATA QUALITY REPORT",
            "=" * 60,
            f"Timestamp: {report['timestamp']}",
            f"DataFrame Shape: {report['dataframe_shape']} (rows, columns)",
            "",
            "OVERALL QUALITY",
            "-" * 60,
            f"Score: {report['overall_score']:.1%}",
            f"Grade: {report['grade']}",
            "",
            "COMPONENT SCORES",
            "-" * 60,
            f"Completeness: {report['completeness_score']:.1%} "
            f"(weight: {self.completeness_weight:.1%})",
            f"Freshness:    {report['freshness_score']:.1%} "
            f"(weight: {self.freshness_weight:.1%})",
            f"Consistency:  {report['consistency_score']:.1%} "
            f"(weight: {self.consistency_weight:.1%})",
            "",
            "DATA STATISTICS",
            "-" * 60,
            f"Total Missing Values: {report['total_missing']}",
            f"Numeric Columns Analyzed: {len(report['numeric_columns'])}",
            "=" * 60,
        ]

        return "\n".join(lines)

    def is_quality_acceptable(self, min_grade: str = "C") -> bool:
        """
        Check if quality meets minimum grade requirement.

        Args:
            min_grade: Minimum acceptable grade ("A", "B", "C", "D", "F")

        Returns:
            True if last score meets minimum, False otherwise
        """
        if self.last_score is None:
            return False

        grade_thresholds = {
            "A": 0.9,
            "B": 0.8,
            "C": 0.7,
            "D": 0.6,
            "F": 0.0,
        }

        min_threshold = grade_thresholds.get(min_grade, 0.7)
        return self.last_score >= min_threshold

    # =========================================================================
    # OpenSpec Compatibility Aliases
    # =========================================================================

    def calculate_completeness_score(self, series: pd.Series) -> float:
        """
        OpenSpec-compatible method for calculating completeness of a single series.

        Args:
            series: Pandas Series to analyze

        Returns:
            Completeness score between 0 and 1
        """
        if series.empty:
            return 0.0

        total_values = len(series)
        non_null_values = series.count()
        completeness = non_null_values / total_values if total_values > 0 else 0.0

        return max(0.0, min(1.0, completeness))

    def calculate_freshness_score(self, df: pd.DataFrame, date_column: Optional[str] = None) -> float:
        """
        OpenSpec-compatible alias for freshness scoring.

        Args:
            df: Input DataFrame
            date_column: Name of date column

        Returns:
            Freshness score between 0 and 1
        """
        return self._calculate_freshness(df, date_column)

    def calculate_overall_grade(self, df: pd.DataFrame, date_column: Optional[str] = None) -> Dict[str, Any]:
        """
        OpenSpec-compatible method for overall quality grading.

        Args:
            df: Input DataFrame
            date_column: Name of date column for freshness

        Returns:
            Dictionary with 'score' and 'grade' keys
        """
        score = self.calculate_quality(df, date_column)
        grade = self.get_grade()

        return {
            "score": score,
            "grade": grade,
        }


# Usage examples
if __name__ == "__main__":
    # Create sample data
    dates = pd.date_range("2025-10-01", periods=100, freq="D")
    np.random.seed(42)

    data = {
        "date": dates,
        "volume": np.random.randint(1000, 10000, 100),
        "price": np.random.uniform(50, 150, 100),
    }

    df = pd.DataFrame(data)

    # Introduce some quality issues
    df.loc[10:15, "volume"] = np.nan  # Missing values
    df.loc[25, "price"] = 500  # Outlier

    print("Sample DataFrame:")
    print(df.head(10))

    # Score quality
    scorer = QualityScorer(
        completeness_weight=0.5,
        freshness_weight=0.3,
        consistency_weight=0.2,
    )

    score = scorer.calculate_quality(df, date_column="date")

    print(f"\nQuality Score: {score:.1%}")
    print(f"Grade: {scorer.get_grade()}")

    # Print detailed report
    print("\n" + scorer.generate_quality_report_text())

    # Check if acceptable
    acceptable = scorer.is_quality_acceptable(min_grade="B")
    print(f"Quality Acceptable (Grade B+): {acceptable}")
