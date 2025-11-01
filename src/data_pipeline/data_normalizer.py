"""
Data Normalizer Module - Alternative Data Pipeline

Handles data standardization and normalization for ML models.

Features:
    - Z-score normalization (standardization)
    - Min-max scaling (0-1 normalization)
    - Log returns calculation
    - Metadata preservation for inverse transforms
    - Edge case handling (zero variance, all NA)
    - Per-group normalization support

Usage:
    normalizer = DataNormalizer(method="zscore")
    normalized_df = normalizer.fit_transform(df, columns=['volume', 'price'])
    original_df = normalizer.inverse_transform(normalized_df)
"""

import logging
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import numpy as np

logger = logging.getLogger("hk_quant_system.data_normalizer")


class DataNormalizer:
    """
    Data normalizer for alternative data.

    Handles different normalization strategies:
    - Z-score: (x - mean) / std → mean≈0, std≈1
    - Min-max: (x - min) / (max - min) → range [0, 1]
    - Log: log(x) → reduces skewness
    - Robust: (x - median) / IQR → resistant to outliers

    Stores normalization parameters for inverse transforms (no look-ahead bias).
    """

    def __init__(
        self,
        method: str = "zscore",
        eps: float = 1e-8,
    ):
        """
        Initialize DataNormalizer.

        Args:
            method: Normalization method ("zscore", "minmax", "log", "robust")
            eps: Small value to prevent division by zero
        """
        self.method = method
        self.eps = eps
        self.params = {}  # Store normalization parameters
        self.is_fitted = False

        logger.info(f"Initialized DataNormalizer (method: {method})")

    def fit(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
    ) -> "DataNormalizer":
        """
        Learn normalization parameters from data.

        Args:
            df: Input DataFrame
            columns: Columns to fit (None = all numeric)

        Returns:
            Self for chaining
        """
        if df.empty:
            logger.warning("Empty DataFrame provided for fitting")
            return self

        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        self.params = {}

        for col in columns:
            valid_values = df[col].dropna()

            if len(valid_values) == 0:
                logger.warning(f"Column '{col}' has no valid values, skipping")
                continue

            if self.method == "zscore":
                self.params[col] = {
                    "mean": valid_values.mean(),
                    "std": valid_values.std(),
                }

            elif self.method == "minmax":
                self.params[col] = {
                    "min": valid_values.min(),
                    "max": valid_values.max(),
                }

            elif self.method == "log":
                self.params[col] = {
                    "min_value": valid_values.min(),
                    "method": "log",
                }

            elif self.method == "robust":
                self.params[col] = {
                    "median": valid_values.median(),
                    "iqr": valid_values.quantile(0.75) - valid_values.quantile(0.25),
                }

        self.is_fitted = True
        logger.info(f"Fitted {len(self.params)} columns using {self.method} normalization")
        return self

    def transform(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Apply learned normalization to data.

        Args:
            df: Input DataFrame
            columns: Columns to transform (None = use fitted columns)

        Returns:
            Normalized DataFrame
        """
        if not self.is_fitted:
            logger.warning("Normalizer not fitted, fitting on provided data")
            self.fit(df, columns)

        if df.empty:
            return df

        if columns is None:
            columns = list(self.params.keys())

        result = df.copy()

        for col in columns:
            if col not in self.params:
                logger.debug(f"Column '{col}' not in fitted parameters, skipping")
                continue

            if col not in result.columns:
                logger.warning(f"Column '{col}' not in DataFrame, skipping")
                continue

            params = self.params[col]

            if self.method == "zscore":
                mean = params["mean"]
                std = params["std"]
                if std > self.eps:
                    result[col] = (result[col] - mean) / std
                else:
                    logger.warning(f"Column '{col}' has zero variance")
                    result[col] = 0.0

            elif self.method == "minmax":
                min_val = params["min"]
                max_val = params["max"]
                range_val = max_val - min_val
                if range_val > self.eps:
                    result[col] = (result[col] - min_val) / range_val
                else:
                    logger.warning(f"Column '{col}' has zero range")
                    result[col] = 0.5

            elif self.method == "log":
                # Ensure positive values
                min_val = params["min_value"]
                if min_val <= 0:
                    # Shift to positive
                    result[col] = np.log(result[col] - min_val + 1)
                else:
                    result[col] = np.log(result[col])

            elif self.method == "robust":
                median = params["median"]
                iqr = params["iqr"]
                if iqr > self.eps:
                    result[col] = (result[col] - median) / iqr
                else:
                    logger.warning(f"Column '{col}' has zero IQR")
                    result[col] = 0.0

        return result

    def fit_transform(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Fit and transform in one step.

        Args:
            df: Input DataFrame
            columns: Columns to normalize

        Returns:
            Normalized DataFrame
        """
        return self.fit(df, columns).transform(df, columns)

    def inverse_transform(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Reverse the normalization (recover original values).

        Args:
            df: Normalized DataFrame
            columns: Columns to denormalize

        Returns:
            Denormalized DataFrame
        """
        if not self.is_fitted:
            logger.error("Cannot inverse transform: normalizer not fitted")
            return df

        if df.empty:
            return df

        if columns is None:
            columns = list(self.params.keys())

        result = df.copy()

        for col in columns:
            if col not in self.params:
                continue

            if col not in result.columns:
                continue

            params = self.params[col]

            if self.method == "zscore":
                mean = params["mean"]
                std = params["std"]
                result[col] = result[col] * std + mean

            elif self.method == "minmax":
                min_val = params["min"]
                max_val = params["max"]
                range_val = max_val - min_val
                result[col] = result[col] * range_val + min_val

            elif self.method == "log":
                min_val = params["min_value"]
                if min_val <= 0:
                    result[col] = np.exp(result[col]) + min_val - 1
                else:
                    result[col] = np.exp(result[col])

            elif self.method == "robust":
                median = params["median"]
                iqr = params["iqr"]
                result[col] = result[col] * iqr + median

        return result

    def get_params(self, column: Optional[str] = None) -> Dict[str, Any]:
        """
        Get normalization parameters.

        Args:
            column: Specific column (None = all)

        Returns:
            Dictionary of parameters
        """
        if column is None:
            return self.params.copy()
        return self.params.get(column, {})

    def validate_normalization(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
    ) -> Tuple[bool, str]:
        """
        Validate that normalized data has expected properties.

        Args:
            df: Normalized DataFrame
            columns: Columns to check (None = fitted columns)

        Returns:
            Tuple of (is_valid, message)
        """
        if columns is None:
            columns = list(self.params.keys())

        issues = []

        for col in columns:
            if col not in df.columns:
                continue

            values = df[col].dropna()
            if len(values) == 0:
                continue

            if self.method == "zscore":
                # Check mean ≈ 0 and std ≈ 1
                mean = values.mean()
                std = values.std()

                if abs(mean) > 0.1:
                    issues.append(f"{col}: mean={mean:.3f} (expected ≈0)")
                if abs(std - 1.0) > 0.2:
                    issues.append(f"{col}: std={std:.3f} (expected ≈1)")

            elif self.method == "minmax":
                # Check range [0, 1]
                min_val = values.min()
                max_val = values.max()

                if min_val < -0.01 or max_val > 1.01:
                    issues.append(
                        f"{col}: range=[{min_val:.3f}, {max_val:.3f}] (expected [0, 1])"
                    )

        if issues:
            message = "Normalization validation issues:\n" + "\n".join(issues)
            return False, message

        return True, f"Normalization validation passed for {len(columns)} columns"

    # =========================================================================
    # OpenSpec Compatibility Aliases
    # =========================================================================

    def zscore_normalize(self, df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        OpenSpec-compatible alias for Z-score normalization.

        Args:
            df: Input DataFrame
            columns: Columns to normalize

        Returns:
            Z-score normalized DataFrame
        """
        # Create a new normalizer with zscore method and fit_transform
        normalizer = DataNormalizer(method="zscore")
        return normalizer.fit_transform(df, columns)

    def minmax_scale(self, df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        OpenSpec-compatible alias for Min-Max scaling.

        Args:
            df: Input DataFrame
            columns: Columns to scale

        Returns:
            Min-Max scaled DataFrame
        """
        # Create a new normalizer with minmax method and fit_transform
        normalizer = DataNormalizer(method="minmax")
        return normalizer.fit_transform(df, columns)

    def inverse_zscore_normalize(self, df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        OpenSpec-compatible alias for inverse Z-score normalization.

        Note: This requires the normalizer to have been previously fitted.
        If not fitted, will try to use parameters stored from previous fit.

        Args:
            df: Z-score normalized DataFrame
            columns: Columns to denormalize

        Returns:
            Original scale DataFrame
        """
        if not self.is_fitted or self.method != "zscore":
            logger.warning("Normalizer not fitted for zscore or method mismatch")

        return self.inverse_transform(df, columns)


class DataNormalizerPipeline:
    """
    Pipeline for sequential normalization of multiple columns.

    Useful for normalizing different columns with different strategies.
    """

    def __init__(self):
        """Initialize pipeline."""
        self.normalizers = {}
        logger.info("Initialized DataNormalizerPipeline")

    def add_normalizer(
        self,
        name: str,
        columns: List[str],
        method: str = "zscore",
    ) -> "DataNormalizerPipeline":
        """
        Add normalizer for specific columns.

        Args:
            name: Name of this normalizer step
            columns: Columns to normalize
            method: Normalization method

        Returns:
            Self for chaining
        """
        self.normalizers[name] = {
            "normalizer": DataNormalizer(method=method),
            "columns": columns,
            "method": method,
        }
        logger.info(f"Added normalizer '{name}' for {len(columns)} columns ({method})")
        return self

    def fit_transform(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Fit and transform all normalizers.

        Args:
            df: Input DataFrame

        Returns:
            Normalized DataFrame
        """
        result = df.copy()

        for name, config in self.normalizers.items():
            normalizer = config["normalizer"]
            columns = config["columns"]

            result = normalizer.fit_transform(result, columns)
            logger.info(f"Applied normalizer '{name}' ({config['method']})")

        return result

    def inverse_transform(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Reverse all normalizations in reverse order.

        Args:
            df: Normalized DataFrame

        Returns:
            Denormalized DataFrame
        """
        result = df.copy()

        # Apply in reverse order
        for name in reversed(list(self.normalizers.keys())):
            config = self.normalizers[name]
            normalizer = config["normalizer"]
            columns = config["columns"]

            result = normalizer.inverse_transform(result, columns)
            logger.info(f"Reversed normalizer '{name}'")

        return result


# Usage examples
if __name__ == "__main__":
    # Create sample data
    np.random.seed(42)
    data = {
        "date": pd.date_range("2025-10-01", periods=100),
        "volume": np.random.randint(1000, 100000, 100),
        "price": np.random.uniform(50, 150, 100),
    }
    df = pd.DataFrame(data)

    print("Original DataFrame:")
    print(df.describe())

    # Z-score normalization
    normalizer_z = DataNormalizer(method="zscore")
    df_z = normalizer_z.fit_transform(df, columns=["volume", "price"])

    print("\nZ-score Normalized:")
    print(df_z.describe())

    # Validate
    is_valid, msg = normalizer_z.validate_normalization(df_z)
    print(f"\nValidation: {msg}")

    # Min-max normalization
    normalizer_mm = DataNormalizer(method="minmax")
    df_mm = normalizer_mm.fit_transform(df, columns=["volume", "price"])

    print("\nMin-max Normalized:")
    print(df_mm.describe())

    # Inverse transform
    df_recovered = normalizer_z.inverse_transform(df_z)
    print("\nRecovered (should match original):")
    print(df_recovered.describe())

    # Pipeline example
    pipeline = DataNormalizerPipeline()
    pipeline.add_normalizer("volume_zscore", ["volume"], method="zscore")
    pipeline.add_normalizer("price_minmax", ["price"], method="minmax")

    df_pipeline = pipeline.fit_transform(df)
    print("\nPipeline Result:")
    print(df_pipeline.describe())
