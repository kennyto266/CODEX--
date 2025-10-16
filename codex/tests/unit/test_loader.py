"""
Unit tests for data loader module.
"""

import pytest
import pandas as pd
import tempfile
from pathlib import Path
from src.data.loader import load_csv


@pytest.mark.unit
class TestDataLoader:
    """Test suite for CSV data loader."""

    def test_load_valid_csv(self, tmp_path):
        """Test loading a valid CSV file."""
        # Create temporary CSV file
        csv_content = """date,open,high,low,close,volume
2023-01-03,320.00,325.60,318.40,324.20,15234000
2023-01-04,324.80,328.00,322.60,327.40,18921000
2023-01-05,327.00,330.20,325.80,329.60,21045000"""

        csv_file = tmp_path / "test_data.csv"
        csv_file.write_text(csv_content)

        # Load data
        df = load_csv(str(csv_file))

        # Assertions
        assert len(df) == 3
        assert list(df.columns) == ['date', 'open', 'high', 'low', 'close', 'volume']
        assert df['date'].dtype == 'datetime64[ns]'
        assert df['close'].iloc[0] == 324.20
        assert df['volume'].iloc[2] == 21045000

    def test_load_case_insensitive_columns(self, tmp_path):
        """Test that column names are case-insensitive."""
        csv_content = """Date,OPEN,High,low,Close,VOLUME
2023-01-03,320.00,325.60,318.40,324.20,15234000"""

        csv_file = tmp_path / "test_data.csv"
        csv_file.write_text(csv_content)

        df = load_csv(str(csv_file))

        assert list(df.columns) == ['date', 'open', 'high', 'low', 'close', 'volume']

    def test_load_missing_required_column(self, tmp_path):
        """Test that missing required columns raise ValueError."""
        csv_content = """date,open,high,low,volume
2023-01-03,320.00,325.60,318.40,15234000"""

        csv_file = tmp_path / "test_data.csv"
        csv_file.write_text(csv_content)

        with pytest.raises(ValueError, match="Missing required columns"):
            load_csv(str(csv_file))

    def test_load_file_not_found(self):
        """Test that FileNotFoundError is raised for non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_csv("/nonexistent/path/data.csv")

    def test_load_invalid_date_format(self, tmp_path):
        """Test that invalid date formats raise ValueError."""
        csv_content = """date,open,high,low,close,volume
not-a-date,320.00,325.60,318.40,324.20,15234000"""

        csv_file = tmp_path / "test_data.csv"
        csv_file.write_text(csv_content)

        with pytest.raises(ValueError, match="Invalid date format"):
            load_csv(str(csv_file))

    def test_load_extra_columns_ignored(self, tmp_path):
        """Test that extra columns are ignored."""
        csv_content = """date,open,high,low,close,volume,symbol,adjusted_close
2023-01-03,320.00,325.60,318.40,324.20,15234000,0700.HK,324.20"""

        csv_file = tmp_path / "test_data.csv"
        csv_file.write_text(csv_content)

        df = load_csv(str(csv_file))

        # Only required columns should be present
        assert list(df.columns) == ['date', 'open', 'high', 'low', 'close', 'volume']

    def test_load_numeric_conversion(self, tmp_path):
        """Test that numeric columns are properly converted."""
        csv_content = """date,open,high,low,close,volume
2023-01-03,320.00,325.60,318.40,324.20,15234000"""

        csv_file = tmp_path / "test_data.csv"
        csv_file.write_text(csv_content)

        df = load_csv(str(csv_file))

        assert df['open'].dtype in [float, 'float64']
        assert df['volume'].dtype in [float, 'float64', int, 'int64']
