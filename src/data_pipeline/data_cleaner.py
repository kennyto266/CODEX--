"""
Data Cleaner Module - Alternative Data Pipeline

Handles missing values, outlier detection, and data quality assurance.

Features:
    - Missing value handling (forward-fill, interpolation, drop)
    - Outlier detection (z-score, IQR methods)
    - Outlier handling (removal, capping, flagging)
    - Configurable cleaning strategies
    - Comprehensive logging of quality issues
    - Statistical validation

Usage:
    cleaner = DataCleaner(strategy="hybrid")
    cleaned_df = cleaner.clean(df, columns=['volume', 'price'])
    quality_report = cleaner.get_quality_report()
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

import pandas as pd
import numpy as np
from scipy import stats

logger = logging.getLogger("hk_quant_system.data_cleaner")


class MissingValueStrategy(Enum):
    """Strategies for handling missing values"""
    DROP = "drop"  # Remove rows with missing values
    FORWARD_FILL = "forward_fill"  # Forward fill missing values
    BACKWARD_FILL = "backward_fill"  # Backward fill missing values
    INTERPOLATE = "interpolate"  # Linear interpolation
    MEAN = "mean"  # Fill with column mean
    MEDIAN = "median"  # Fill with column median
    HYBRID = "hybrid"  # Combination: interpolate, then forward-fill


class OutlierStrategy(Enum):
    """Strategies for handling outliers"""
    REMOVE = "remove"  # Remove rows with outliers
    CAP = "cap"  # Cap outliers to boundaries (IQR method)
    ZSCORE_CAP = "zscore_cap"  # Cap based on z-score
    FLAG = "flag"  # Flag without removing/modifying
    KEEP = "keep"  # Keep outliers as-is


class DataCleaner:
    """
    Data cleaner for alternative data series.

    Handles common data quality issues:
    - Missing values (NaN, None)
    - Outliers (statistical anomalies)
    - Data inconsistencies
    - Quality degradation

    Attributes:
        missing_value_strategy: How to handle missing values
        outlier_strategy: How to handle outliers
        z_score_threshold: Z-score threshold for outlier detection
        iqr_multiplier: IQR multiplier for outlier boundaries
    """

    def __init__(
        self,
        missing_value_strategy: str = "interpolate",
        outlier_strategy: str = "cap",
        z_score_threshold: float = 3.0,
        iqr_multiplier: float = 1.5,
    ):
        """
        Initialize DataCleaner.

        Args:
            missing_value_strategy: Strategy for missing values
            outlier_strategy: Strategy for outliers
            z_score_threshold: Z-score cutoff (default: 3.0 = 99.7% confidence)
            iqr_multiplier: IQR multiplier (default: 1.5 = standard boxplot)
        """
        self.missing_value_strategy = MissingValueStrategy(missing_value_strategy)
        self.outlier_strategy = OutlierStrategy(outlier_strategy)
        self.z_score_threshold = z_score_threshold
        self.iqr_multiplier = iqr_multiplier

        # Quality metrics tracking
        self.quality_report = {
            "original_rows": 0,
            "final_rows": 0,
            "missing_values_handled": 0,
            "outliers_detected": 0,
            "outliers_handled": 0,
            "quality_issues": [],
            "processing_timestamp": None,
        }

        logger.info(
            f"Initialized DataCleaner: "
            f"missing={missing_value_strategy}, "
            f"outlier={outlier_strategy}"
        )

    def clean(
        self,
        df: pd.DataFrame,
        numeric_columns: Optional[List[str]] = None,
        date_column: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Clean data by handling missing values and outliers.

        Args:
            df: Input DataFrame
            numeric_columns: Columns to check for quality (None = all numeric)
            date_column: Name of date column for time-series operations

        Returns:
            Cleaned DataFrame
        """
        if df.empty:
            logger.warning("Received empty DataFrame")
            return df

        # Reset quality report
        self.quality_report = {
            "original_rows": len(df),
            "final_rows": 0,
            "missing_values_handled": 0,
            "outliers_detected": 0,
            "outliers_handled": 0,
            "quality_issues": [],
            "processing_timestamp": datetime.now().isoformat(),
        }

        # Make a copy to avoid modifying original
        result = df.copy()

        # Identify numeric columns if not specified
        if numeric_columns is None:
            numeric_columns = result.select_dtypes(include=[np.number]).columns.tolist()

        if not numeric_columns:
            logger.warning("No numeric columns found for cleaning")
            return result

        logger.info(f"Cleaning {len(result)} rows, {len(numeric_columns)} columns")

        # Step 1: Handle missing values
        result = self._handle_missing_values(result, numeric_columns, date_column)

        # Step 2: Detect outliers
        outlier_flags = self._detect_outliers(result, numeric_columns)

        # Step 3: Handle outliers
        result = self._handle_outliers(result, numeric_columns, outlier_flags)

        # Update quality report
        self.quality_report["final_rows"] = len(result)

        logger.info(
            f"Cleaning complete: {self.quality_report['original_rows']} → "
            f"{self.quality_report['final_rows']} rows, "
            f"{self.quality_report['outliers_detected']} outliers detected"
        )

        return result

    def _handle_missing_values(
        self,
        df: pd.DataFrame,
        columns: List[str],
        date_column: Optional[str] = None,
    ) -> pd.DataFrame:
        """Handle missing values based on configured strategy."""
        result = df.copy()

        # Count initial missing values
        initial_missing = result[columns].isnull().sum().sum()
        if initial_missing == 0:
            return result

        logger.info(f"Detected {initial_missing} missing values")
        self.quality_report["quality_issues"].append(
            f"Initial missing values: {initial_missing}"
        )

        if self.missing_value_strategy == MissingValueStrategy.DROP:
            result = result.dropna(subset=columns)
            handled = initial_missing
            logger.info(f"Dropped {handled} rows with missing values")

        elif self.missing_value_strategy == MissingValueStrategy.FORWARD_FILL:
            result[columns] = result[columns].ffill()
            remaining = result[columns].isnull().sum().sum()
            handled = initial_missing - remaining
            logger.info(f"Forward-filled {handled} missing values")

        elif self.missing_value_strategy == MissingValueStrategy.BACKWARD_FILL:
            result[columns] = result[columns].bfill()
            remaining = result[columns].isnull().sum().sum()
            handled = initial_missing - remaining
            logger.info(f"Backward-filled {handled} missing values")

        elif self.missing_value_strategy == MissingValueStrategy.INTERPOLATE:
            # Linear interpolation for each column
            for col in columns:
                result[col] = result[col].interpolate(method="linear", limit_area="inside")
            remaining = result[columns].isnull().sum().sum()
            handled = initial_missing - remaining
            logger.info(f"Interpolated {handled} missing values")

        elif self.missing_value_strategy == MissingValueStrategy.MEAN:
            for col in columns:
                result[col] = result[col].fillna(result[col].mean())
            handled = initial_missing
            logger.info(f"Filled {handled} missing values with column means")

        elif self.missing_value_strategy == MissingValueStrategy.MEDIAN:
            for col in columns:
                result[col] = result[col].fillna(result[col].median())
            handled = initial_missing
            logger.info(f"Filled {handled} missing values with column medians")

        elif self.missing_value_strategy == MissingValueStrategy.HYBRID:
            # First try interpolation
            for col in columns:
                result[col] = result[col].interpolate(method="linear", limit_area="inside")
            # Then forward-fill remaining
            result[columns] = result[columns].ffill()
            # Finally backward-fill
            result[columns] = result[columns].bfill()
            remaining = result[columns].isnull().sum().sum()
            handled = initial_missing - remaining
            logger.info(f"Hybrid approach handled {handled} missing values")

        self.quality_report["missing_values_handled"] = handled
        return result

    def _detect_outliers(
        self,
        df: pd.DataFrame,
        columns: List[str],
    ) -> Dict[str, np.ndarray]:
        """
        Detect outliers using multiple methods.

        Returns:
            Dictionary mapping column names to boolean arrays of outlier flags
        """
        outlier_flags = {}

        for col in columns:
            # Skip if column has insufficient data
            if df[col].nunique() < 3:
                outlier_flags[col] = np.zeros(len(df), dtype=bool)
                continue

            # Z-score method
            z_scores = np.abs(stats.zscore(df[col].dropna()))
            z_outliers = z_scores > self.z_score_threshold

            # IQR method
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - self.iqr_multiplier * iqr
            upper_bound = q3 + self.iqr_multiplier * iqr
            iqr_outliers = (df[col] < lower_bound) | (df[col] > upper_bound)

            # Combine methods (flag if detected by either method)
            combined_outliers = np.zeros(len(df), dtype=bool)
            combined_outliers[df[col].notna()] = z_outliers | iqr_outliers.dropna().values

            outlier_flags[col] = combined_outliers

            # Count and log
            n_outliers = combined_outliers.sum()
            if n_outliers > 0:
                pct = 100 * n_outliers / len(df)
                logger.info(f"{col}: {n_outliers} outliers detected ({pct:.2f}%)")
                self.quality_report["quality_issues"].append(
                    f"{col}: {n_outliers} outliers ({pct:.2f}%)"
                )

        self.quality_report["outliers_detected"] = sum(
            f.sum() for f in outlier_flags.values()
        )
        return outlier_flags

    def _handle_outliers(
        self,
        df: pd.DataFrame,
        columns: List[str],
        outlier_flags: Dict[str, np.ndarray],
    ) -> pd.DataFrame:
        """Handle detected outliers based on configured strategy."""
        result = df.copy()
        handled = 0

        if self.outlier_strategy == OutlierStrategy.REMOVE:
            # Remove rows with any outliers
            for col in columns:
                result = result[~outlier_flags[col]]
            handled = self.quality_report["original_rows"] - len(result)
            logger.info(f"Removed {handled} rows with outliers")

        elif self.outlier_strategy == OutlierStrategy.CAP:
            # Cap outliers to IQR boundaries
            for col in columns:
                q1 = result[col].quantile(0.25)
                q3 = result[col].quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - self.iqr_multiplier * iqr
                upper_bound = q3 + self.iqr_multiplier * iqr
                result[col] = result[col].clip(lower_bound, upper_bound)
            handled = self.quality_report["outliers_detected"]
            logger.info(f"Capped {handled} outliers to IQR boundaries")

        elif self.outlier_strategy == OutlierStrategy.ZSCORE_CAP:
            # Cap outliers based on z-score
            for col in columns:
                mean = result[col].mean()
                std = result[col].std()
                lower_bound = mean - self.z_score_threshold * std
                upper_bound = mean + self.z_score_threshold * std
                result[col] = result[col].clip(lower_bound, upper_bound)
            handled = self.quality_report["outliers_detected"]
            logger.info(f"Capped {handled} outliers based on z-score")

        elif self.outlier_strategy == OutlierStrategy.FLAG:
            # Add flag columns without modifying values
            for col in columns:
                flag_col = f"{col}_outlier_flag"
                result[flag_col] = outlier_flags[col]
            handled = self.quality_report["outliers_detected"]
            logger.info(f"Flagged {handled} outliers (retained values)")

        elif self.outlier_strategy == OutlierStrategy.KEEP:
            # Do nothing
            handled = 0
            logger.info("Keeping all outliers (no modification)")

        self.quality_report["outliers_handled"] = handled
        return result

    def get_quality_report(self) -> Dict[str, Any]:
        """
        Get detailed quality report from last cleaning operation.

        Returns:
            Dictionary with quality metrics
        """
        return self.quality_report.copy()

    def validate_data_quality(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        min_completeness: float = 0.95,
    ) -> Tuple[bool, str]:
        """
        Validate data quality against thresholds.

        Args:
            df: DataFrame to validate
            columns: Columns to check (None = all numeric)
            min_completeness: Minimum completeness ratio (0-1)

        Returns:
            Tuple of (is_valid, message)
        """
        if df.empty:
            return False, "Empty DataFrame"

        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        # Calculate completeness
        total_cells = len(df) * len(columns)
        missing_cells = df[columns].isnull().sum().sum()
        completeness = 1 - (missing_cells / total_cells) if total_cells > 0 else 0

        if completeness < min_completeness:
            msg = f"Completeness {completeness:.1%} below threshold {min_completeness:.1%}"
            return False, msg

        return True, f"Data quality valid (completeness: {completeness:.1%})"


# Usage examples and integration
if __name__ == "__main__":
    # Create sample data with issues
    dates = pd.date_range("2025-09-01", periods=30, freq="D")
    np.random.seed(42)

    data = {
        "date": dates,
        "volume": np.random.randint(1000, 10000, 30),
        "price": np.random.uniform(50, 150, 30),
    }

    # Introduce some data quality issues
    df = pd.DataFrame(data)
    df.loc[5, "volume"] = np.nan  # Missing value
    df.loc[10, "volume"] = 100000  # Outlier
    df.loc[15, "price"] = np.nan  # Another missing

    print("Original DataFrame:")
    print(df.head(20))
    print(f"\nShape: {df.shape}, Missing: {df.isnull().sum().sum()}")

    # Clean data
    cleaner = DataCleaner(
        missing_value_strategy="interpolate",
        outlier_strategy="cap",
    )

    cleaned_df = cleaner.clean(df, numeric_columns=["volume", "price"])

    print("\nCleaned DataFrame:")
    print(cleaned_df.head(20))
    print(f"\nShape: {cleaned_df.shape}, Missing: {cleaned_df.isnull().sum().sum()}")

    # Quality report
    report = cleaner.get_quality_report()
    print("\nQuality Report:")
    for key, value in report.items():
        print(f"  {key}: {value}")

    # Validation
    is_valid, message = cleaner.validate_data_quality(cleaned_df)
    print(f"\nValidation: {message}")
