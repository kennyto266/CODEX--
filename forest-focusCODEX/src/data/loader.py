"""
Data loader module for RSI Backtest Optimizer.

Loads OHLCV price data from CSV files and converts to pandas DataFrame.
"""

import logging
from pathlib import Path
from typing import Union

import pandas as pd

logger = logging.getLogger("rsi_backtest.data.loader")


def load_csv(file_path: Union[str, Path]) -> pd.DataFrame:
    """
    Load OHLCV data from CSV file.

    Args:
        file_path: Path to CSV file containing OHLCV data

    Returns:
        pandas DataFrame with columns: date, open, high, low, close, volume

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If required columns are missing or file is empty
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    logger.info(f"Loading data from {file_path}")

    try:
        # Read CSV with automatic type inference
        df = pd.read_csv(file_path)

        if df.empty:
            raise ValueError(f"CSV file is empty: {file_path}")

        # Normalize column names to lowercase
        df.columns = df.columns.str.lower().str.strip()

        # Check for required columns
        required_columns = {'date', 'open', 'high', 'low', 'close', 'volume'}
        missing_columns = required_columns - set(df.columns)

        if missing_columns:
            raise ValueError(
                f"Missing required columns: {missing_columns}. "
                f"Found columns: {set(df.columns)}"
            )

        # Convert date column to datetime
        df['date'] = pd.to_datetime(df['date'])

        # Convert price/volume columns to numeric
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Check for NaN values after conversion
        if df[['open', 'high', 'low', 'close', 'volume']].isnull().any().any():
            nan_count = df[['open', 'high', 'low', 'close', 'volume']].isnull().sum().sum()
            logger.warning(f"Found {nan_count} NaN values after type conversion")

        # Select only required columns in standard order
        df = df[['date', 'open', 'high', 'low', 'close', 'volume']]

        logger.info(
            f"Loaded {len(df)} trading days "
            f"({df['date'].min().date()} to {df['date'].max().date()})"
        )

        return df

    except pd.errors.EmptyDataError:
        raise ValueError(f"CSV file is empty: {file_path}")
    except Exception as e:
        logger.error(f"Error loading data from {file_path}: {e}")
        raise
