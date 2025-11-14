"""
Comprehensive Test Configuration and Fixtures
Quant Trading System - Phase 1 Week 7-8
"""

import asyncio
import json
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pandas as pd
import pytest
import pytest_asyncio

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# ============================================================================
# Pytest Configuration and Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Data Fixtures
# ============================================================================

@pytest.fixture
def sample_price_data() -> pd.DataFrame:
    """Generate sample OHLCV price data for testing"""
    dates = pd.date_range(start="2020-01-01", periods=1000, freq="D")
    np.random.seed(42)
    
    # Generate realistic price data
    initial_price = 100.0
    returns = np.random.normal(0.0005, 0.02, len(dates))
    prices = initial_price * (1 + returns).cumprod()
    
    data = pd.DataFrame({
        "open": prices * (1 + np.random.normal(0, 0.005, len(dates))),
        "high": prices * (1 + np.abs(np.random.normal(0, 0.01, len(dates)))),
        "low": prices * (1 - np.abs(np.random.normal(0, 0.01, len(dates)))),
        "close": prices,
        "volume": np.random.randint(1000000, 10000000, len(dates)),
        "date": dates
    })
    
    return data


@pytest.fixture
def sample_hibor_data() -> pd.DataFrame:
    """Generate sample HIBOR data"""
    dates = pd.date_range(start="2020-01-01", periods=1000, freq="D")
    np.random.seed(42)
    
    # HIBOR rates typically range from 0.5% to 5%
    base_rate = 2.0
    rates = base_rate + np.random.normal(0, 0.5, len(dates))
    rates = np.clip(rates, 0.1, 6.0)
    
    return pd.DataFrame({
        "date": dates,
        "hibor_1m": rates + np.random.normal(0, 0.1, len(dates)),
        "hibor_3m": rates + 0.2 + np.random.normal(0, 0.1, len(dates)),
        "hibor_6m": rates + 0.4 + np.random.normal(0, 0.1, len(dates)),
        "hibor_12m": rates + 0.8 + np.random.normal(0, 0.1, len(dates)),
    })


@pytest.fixture
def sample_technical_indicators() -> pd.DataFrame:
    """Generate sample technical indicators data"""
    dates = pd.date_range(start="2020-01-01", periods=1000, freq="D")
    np.random.seed(42)
    
    return pd.DataFrame({
        "date": dates,
        "rsi": np.random.uniform(20, 80, len(dates)),
        "macd": np.random.normal(0, 2, len(dates)),
        "macd_signal": np.random.normal(0, 2, len(dates)),
        "macd_histogram": np.random.normal(0, 1, len(dates)),
        "bb_upper": np.random.uniform(100, 120, len(dates)),
        "bb_middle": np.random.uniform(90, 110, len(dates)),
        "bb_lower": np.random.uniform(80, 100, len(dates)),
        "sma_20": np.random.uniform(95, 105, len(dates)),
        "sma_50": np.random.uniform(90, 110, len(dates)),
        "ema_12": np.random.uniform(95, 105, len(dates)),
        "ema_26": np.random.uniform(90, 110, len(dates)),
        "atr": np.random.uniform(1, 5, len(dates)),
    })


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_data_adapter():
    """Mock data adapter for testing"""
    adapter = MagicMock()
    adapter.fetch_data.return_value = pd.DataFrame({
        "open": [100, 101, 102],
        "high": [105, 106, 107],
        "low": [95, 96, 97],
        "close": [102, 103, 104],
        "volume": [1000000, 1100000, 1200000],
        "date": pd.date_range(start="2020-01-01", periods=3, freq="D")
    })
    adapter.validate_data.return_value = True
    adapter.convert_to_ohlcv.return_value = True
    return adapter


@pytest.fixture
def mock_backtest_engine():
    """Mock backtest engine"""
    engine = MagicMock()
    engine.run_backtest.return_value = {
        "total_return": 0.25,
        "annualized_return": 0.12,
        "sharpe_ratio": 1.5,
        "max_drawdown": -0.15,
        "win_rate": 0.65,
        "trades": 100,
    }
    engine.get_metrics.return_value = {
        "total_return": 0.25,
        "volatility": 0.20,
        "sharpe_ratio": 1.5,
        "max_drawdown": -0.15,
        "calmar_ratio": 0.8,
        "sortino_ratio": 2.0,
    }
    return engine


# ============================================================================
# Helper Functions
# ============================================================================

def assert_dataframe_equal(df1: pd.DataFrame, df2: pd.DataFrame, check_dtype: bool = True):
    """Helper to assert two DataFrames are equal"""
    pd.testing.assert_frame_equal(df1, df2, check_dtype=check_dtype)


def assert_series_equal(s1: pd.Series, s2: pd.Series, check_dtype: bool = True):
    """Helper to assert two Series are equal"""
    pd.testing.assert_series_equal(s1, s2, check_dtype=check_dtype)


pytest.assert_dataframe_equal = assert_dataframe_equal
pytest.assert_series_equal = assert_series_equal
