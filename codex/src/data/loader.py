"""
Data loader module for CSV price data.

This module handles loading OHLCV price data from CSV files,
parsing dates, and returning pandas DataFrames.
"""

import pandas as pd
import logging
from pathlib import Path

logger = logging.getLogger("rsi_backtest.data.loader")


def load_csv(file_path: str) -> pd.DataFrame:
    """
    Load OHLCV price data from CSV file.

    Args:
        file_path: Path to CSV file containing OHLCV data

    Returns:
        pandas DataFrame with columns: date, open, high, low, close, volume

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If required columns are missing
        pd.errors.ParserError: If CSV format is invalid
    """
    logger.info(f"Loading data from {file_path}")

    # Check file exists
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    # Load CSV
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        logger.error(f"Failed to parse CSV: {e}")
        raise

    # Normalize column names (case-insensitive)
    df.columns = df.columns.str.lower().str.strip()

    # Check required columns
    required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    missing_columns = set(required_columns) - set(df.columns)

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    # Select only required columns (ignore extras)
    df = df[required_columns].copy()

    # Parse dates
    try:
        df['date'] = pd.to_datetime(df['date'])
    except Exception as e:
        logger.error(f"Failed to parse dates: {e}")
        raise ValueError(f"Invalid date format: {e}")

    # Convert numeric columns to appropriate types
    numeric_columns = ['open', 'high', 'low', 'close', 'volume']
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Check for NaN values after conversion
    if df[numeric_columns].isnull().any().any():
        null_counts = df[numeric_columns].isnull().sum()
        logger.warning(f"Found NaN values after conversion: {null_counts.to_dict()}")

    logger.info(f"Loaded {len(df)} trading days ({df['date'].min().date()} to {df['date'].max().date()})")

    return df
