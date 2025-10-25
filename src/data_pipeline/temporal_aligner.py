"""
Temporal Aligner Module - Alternative Data Pipeline

Handles time-series alignment, frequency conversion, and calendar management.

Features:
    - Hong Kong trading calendar (weekends, holidays)
    - Alignment to trading days
    - Frequency conversion (daily → weekly → monthly)
    - Forward-fill and interpolation
    - Lagged feature generation
    - Look-ahead bias prevention

Usage:
    aligner = TemporalAligner()
    aligned_df = aligner.align_to_trading_days(df, date_column='date')
    lagged_df = aligner.generate_lagged_features(aligned_df, lags=[1, 5, 20])
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set

import pandas as pd
import numpy as np

logger = logging.getLogger("hk_quant_system.temporal_aligner")


class HKTradingCalendar:
    """
    Hong Kong Stock Exchange trading calendar.

    Defines trading days, holidays, and special closures.
    """

    # Hong Kong public holidays and market closures (2025)
    HK_HOLIDAYS_2025 = {
        datetime(2025, 1, 1),  # New Year's Day
        datetime(2025, 1, 29),  # Chinese New Year
        datetime(2025, 1, 30),  # Chinese New Year
        datetime(2025, 1, 31),  # Chinese New Year (substitute)
        datetime(2025, 4, 4),  # Children's Day (Ching Ming Festival)
        datetime(2025, 4, 11),  # Good Friday
        datetime(2025, 4, 12),  # Easter Monday
        datetime(2025, 5, 1),  # Labour Day
        datetime(2025, 5, 15),  # Buddha's Birthday
        datetime(2025, 6, 10),  # Dragon Boat Festival
        datetime(2025, 9, 18),  # Day after Mid-Autumn Festival
        datetime(2025, 10, 1),  # National Day
        datetime(2025, 10, 11),  # Chong Yeung Festival
        datetime(2025, 12, 25),  # Christmas Day
    }

    @staticmethod
    def is_trading_day(date: datetime) -> bool:
        """Check if date is a trading day (not weekend or holiday)."""
        if isinstance(date, pd.Timestamp):
            date = date.to_pydatetime()

        # Weekend check (Saturday=5, Sunday=6)
        if date.weekday() >= 5:
            return False

        # Holiday check
        date_only = datetime(date.year, date.month, date.day)
        if date_only in HKTradingCalendar.HK_HOLIDAYS_2025:
            return False

        return True

    @staticmethod
    def get_trading_days(start_date: datetime, end_date: datetime) -> pd.DatetimeIndex:
        """Get all trading days in a date range."""
        all_dates = pd.date_range(start_date, end_date, freq="D")
        trading_dates = [d for d in all_dates if HKTradingCalendar.is_trading_day(d)]
        return pd.DatetimeIndex(trading_dates)


class TemporalAligner:
    """
    Temporal aligner for alternative data.

    Handles:
    - Alignment to trading days (no weekends/holidays)
    - Frequency conversion (daily/weekly/monthly)
    - Missing data imputation
    - Lagged feature generation
    - Look-ahead bias prevention
    """

    def __init__(self):
        """Initialize TemporalAligner."""
        self.trading_calendar = HKTradingCalendar()
        logger.info("Initialized TemporalAligner with HK trading calendar")

    def align_to_trading_days(
        self,
        df: pd.DataFrame,
        date_column: str,
        fill_method: str = "forward_fill",
    ) -> pd.DataFrame:
        """
        Align data to trading days only.

        Removes weekends and holidays, optionally fills gaps.

        Args:
            df: Input DataFrame
            date_column: Name of date column
            fill_method: How to handle gaps ("forward_fill", "interpolate", "drop")

        Returns:
            DataFrame aligned to trading days
        """
        if df.empty:
            logger.warning("Empty DataFrame provided")
            return df

        # Convert date column to datetime
        df_copy = df.copy()
        df_copy[date_column] = pd.to_datetime(df_copy[date_column])

        # Get all unique dates
        unique_dates = df_copy[date_column].unique()
        date_range = pd.date_range(
            unique_dates.min(),
            unique_dates.max(),
            freq="D",
        )

        # Filter to trading days
        trading_days = self.trading_calendar.get_trading_days(
            unique_dates.min(),
            unique_dates.max(),
        )

        logger.info(
            f"Aligning to trading days: {len(date_range)} calendar days "
            f"→ {len(trading_days)} trading days"
        )

        # Create template with all trading days
        template_df = pd.DataFrame({date_column: trading_days})

        # Merge with original data
        aligned_df = template_df.merge(
            df_copy,
            on=date_column,
            how="left",
        )

        # Handle gaps
        numeric_columns = aligned_df.select_dtypes(include=[np.number]).columns

        if fill_method == "forward_fill":
            aligned_df[numeric_columns] = aligned_df[numeric_columns].ffill()
            logger.info("Filled gaps with forward-fill")

        elif fill_method == "interpolate":
            aligned_df[numeric_columns] = aligned_df[numeric_columns].interpolate(
                method="linear"
            )
            logger.info("Filled gaps with interpolation")

        elif fill_method == "drop":
            aligned_df = aligned_df.dropna()
            logger.info("Dropped rows with missing values")

        return aligned_df

    def resample_data(
        self,
        df: pd.DataFrame,
        date_column: str,
        target_frequency: str = "W",
        agg_functions: Optional[Dict[str, str]] = None,
    ) -> pd.DataFrame:
        """
        Resample data to different frequency.

        Args:
            df: Input DataFrame with trading day alignment
            date_column: Name of date column
            target_frequency: Target frequency ("D", "W", "M", "Q", "Y")
            agg_functions: Aggregation functions per column (default: "last")

        Returns:
            Resampled DataFrame
        """
        if df.empty:
            return df

        # Set date as index
        df_indexed = df.set_index(date_column)

        # Define default aggregation
        if agg_functions is None:
            # For most metrics, take the last value of the period
            numeric_columns = df_indexed.select_dtypes(include=[np.number]).columns
            agg_functions = {col: "last" for col in numeric_columns}

        # Resample
        resampled = df_indexed.resample(target_frequency).agg(agg_functions)

        # Reset index
        resampled = resampled.reset_index()

        freq_names = {"D": "daily", "W": "weekly", "M": "monthly", "Q": "quarterly", "Y": "yearly"}
        logger.info(
            f"Resampled data from {len(df)} to {len(resampled)} records "
            f"(target: {freq_names.get(target_frequency, 'unknown')})"
        )

        return resampled

    def generate_lagged_features(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        lags: Optional[List[int]] = None,
        date_column: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Generate lagged features for time-series modeling.

        Creates shifted versions of columns for use in ML models.
        Prevents look-ahead bias by not shifting forward.

        Args:
            df: Input DataFrame
            columns: Columns to lag (None = all numeric)
            lags: List of lags to create [1, 5, 20]
            date_column: Date column (for reference)

        Returns:
            DataFrame with original and lagged columns
        """
        if df.empty:
            return df

        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        if lags is None:
            lags = [1, 5, 20]

        result = df.copy()

        # Ensure lags are sorted
        lags = sorted(lags)

        for col in columns:
            for lag in lags:
                lagged_col_name = f"{col}_lag_{lag}"
                result[lagged_col_name] = result[col].shift(lag)

        # Log creation
        n_lagged_features = len(columns) * len(lags)
        logger.info(
            f"Generated {n_lagged_features} lagged features "
            f"({len(columns)} columns × {len(lags)} lags)"
        )

        return result

    def generate_rolling_features(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        windows: Optional[List[int]] = None,
        functions: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Generate rolling window features.

        Creates rolling statistics (mean, std, etc.) over specified windows.

        Args:
            df: Input DataFrame
            columns: Columns to compute rolling stats
            windows: Window sizes [5, 20, 60] (in trading days)
            functions: Statistics to compute ["mean", "std", "min", "max"]

        Returns:
            DataFrame with rolling features
        """
        if df.empty:
            return df

        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        if windows is None:
            windows = [5, 20, 60]

        if functions is None:
            functions = ["mean", "std", "min", "max"]

        result = df.copy()

        for col in columns:
            for window in windows:
                for func in functions:
                    feature_name = f"{col}_roll_{window}d_{func}"

                    if func == "mean":
                        result[feature_name] = result[col].rolling(window).mean()
                    elif func == "std":
                        result[feature_name] = result[col].rolling(window).std()
                    elif func == "min":
                        result[feature_name] = result[col].rolling(window).min()
                    elif func == "max":
                        result[feature_name] = result[col].rolling(window).max()
                    elif func == "sum":
                        result[feature_name] = result[col].rolling(window).sum()

        # Log creation
        n_rolling_features = len(columns) * len(windows) * len(functions)
        logger.info(
            f"Generated {n_rolling_features} rolling features "
            f"({len(columns)} columns × {len(windows)} windows × {len(functions)} functions)"
        )

        return result

    def compute_returns(
        self,
        df: pd.DataFrame,
        price_columns: Optional[List[str]] = None,
        return_type: str = "log",
        periods: Optional[List[int]] = None,
    ) -> pd.DataFrame:
        """
        Compute returns from price series.

        Args:
            df: Input DataFrame
            price_columns: Columns with price data
            return_type: "simple" or "log"
            periods: Periods for return calculation [1, 5, 20]

        Returns:
            DataFrame with original data and returns columns
        """
        if df.empty:
            return df

        if price_columns is None:
            price_columns = df.select_dtypes(include=[np.number]).columns.tolist()

        if periods is None:
            periods = [1, 5, 20]

        result = df.copy()

        for col in price_columns:
            for period in periods:
                return_col = f"{col}_return_{period}d"

                if return_type == "log":
                    # Log returns: ln(P_t / P_{t-period})
                    result[return_col] = np.log(result[col] / result[col].shift(period))
                else:
                    # Simple returns: (P_t - P_{t-period}) / P_{t-period}
                    result[return_col] = result[col].pct_change(periods=period)

        logger.info(
            f"Computed {len(price_columns) * len(periods)} return series "
            f"(type: {return_type})"
        )

        return result

    def get_trading_days_range(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> pd.DatetimeIndex:
        """
        Get all trading days in a range.

        Useful for creating templates and validating alignments.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            DatetimeIndex of trading days
        """
        return self.trading_calendar.get_trading_days(start_date, end_date)

    def is_trading_day(self, date: datetime) -> bool:
        """Check if a date is a trading day."""
        return self.trading_calendar.is_trading_day(date)


# Usage examples
if __name__ == "__main__":
    # Create sample data
    dates = pd.date_range("2025-09-01", "2025-10-31", freq="D")
    dates_trading_only = [d for d in dates if HKTradingCalendar.is_trading_day(d)]

    data = {
        "date": dates_trading_only[:30],  # Use first 30 trading days
        "volume": np.random.randint(1000, 10000, 30),
        "price": np.random.uniform(50, 150, 30),
    }

    df = pd.DataFrame(data)
    print("Original DataFrame:")
    print(df.head(10))

    # Initialize aligner
    aligner = TemporalAligner()

    # Generate lagged features
    df_lagged = aligner.generate_lagged_features(
        df,
        columns=["volume", "price"],
        lags=[1, 5, 10],
    )

    print("\nWith Lagged Features:")
    print(df_lagged.head(10))

    # Generate rolling features
    df_rolling = aligner.generate_rolling_features(
        df_lagged,
        columns=["volume", "price"],
        windows=[5, 10],
        functions=["mean", "std"],
    )

    print(f"\nWith Rolling Features (shape): {df_rolling.shape}")

    # Compute returns
    df_returns = aligner.compute_returns(
        df_rolling,
        price_columns=["price"],
        return_type="log",
        periods=[1, 5],
    )

    print(f"\nWith Returns (shape): {df_returns.shape}")
    print(f"Columns: {list(df_returns.columns)[:15]}...")  # Show first 15 columns
