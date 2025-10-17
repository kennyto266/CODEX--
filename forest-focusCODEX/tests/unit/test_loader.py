"""
Unit tests for data loader module.
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import os

from src.data.loader import load_csv


@pytest.fixture
def sample_csv_file():
    """Create a temporary CSV file with valid OHLCV data."""
    content = """date,open,high,low,close,volume
2023-01-03,320.00,325.60,318.40,324.20,15234000
2023-01-04,324.80,328.00,322.60,327.40,18921000
2023-01-05,327.00,330.20,325.80,329.60,21045000"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(content)
        temp_path = f.name

    yield temp_path

    # Cleanup
    os.unlink(temp_path)


@pytest.fixture
def invalid_columns_csv():
    """CSV with missing required columns."""
    content = """date,open,high,low
2023-01-03,320.00,325.60,318.40"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(content)
        temp_path = f.name

    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def empty_csv():
    """Empty CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("")
        temp_path = f.name

    yield temp_path
    os.unlink(temp_path)


@pytest.mark.unit
def test_load_csv_success(sample_csv_file):
    """Test successful CSV loading."""
    df = load_csv(sample_csv_file)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert list(df.columns) == ['date', 'open', 'high', 'low', 'close', 'volume']

    # Check types
    assert pd.api.types.is_datetime64_any_dtype(df['date'])
    assert pd.api.types.is_numeric_dtype(df['open'])
    assert pd.api.types.is_numeric_dtype(df['close'])


@pytest.mark.unit
def test_load_csv_file_not_found():
    """Test error handling for non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_csv("/nonexistent/path/file.csv")


@pytest.mark.unit
def test_load_csv_missing_columns(invalid_columns_csv):
    """Test error handling for missing required columns."""
    with pytest.raises(ValueError, match="Missing required columns"):
        load_csv(invalid_columns_csv)


@pytest.mark.unit
def test_load_csv_empty_file(empty_csv):
    """Test error handling for empty CSV."""
    with pytest.raises(ValueError, match="empty"):
        load_csv(empty_csv)


@pytest.mark.unit
def test_load_csv_date_conversion(sample_csv_file):
    """Test that dates are correctly converted to datetime."""
    df = load_csv(sample_csv_file)

    assert df['date'].dtype == 'datetime64[ns]'
    assert df['date'].iloc[0] == pd.Timestamp('2023-01-03')


@pytest.mark.unit
def test_load_csv_column_normalization():
    """Test that column names are normalized to lowercase."""
    content = """DATE,Open,HIGH,low,Close,VOLUME
2023-01-03,320.00,325.60,318.40,324.20,15234000"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        df = load_csv(temp_path)
        assert all(col.islower() for col in df.columns)
    finally:
        os.unlink(temp_path)


@pytest.mark.unit
def test_load_csv_extra_columns():
    """Test that extra columns are ignored."""
    content = """date,open,high,low,close,volume,adjusted_close,symbol
2023-01-03,320.00,325.60,318.40,324.20,15234000,324.20,0700.HK"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        df = load_csv(temp_path)
        # Should only have required columns
        assert list(df.columns) == ['date', 'open', 'high', 'low', 'close', 'volume']
    finally:
        os.unlink(temp_path)
