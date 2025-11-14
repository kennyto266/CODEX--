"""
Helper utilities
"""
import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

def validate_dataframe(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """Validate DataFrame has required columns and is not empty"""
    if df is None or df.empty:
        return False
    return all(col in df.columns for col in required_columns)

def format_currency(value: float, currency: str = "USD") -> str:
    """Format currency value"""
    return f"{currency} {value:,.2f}"

def format_percentage(value: float, decimals: int = 2) -> str:
    """Format percentage value"""
    return f"{value:.{decimals}f}%"

def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
    """Calculate Sharpe ratio"""
    excess_returns = returns - risk_free_rate / 252
    return np.sqrt(252) * excess_returns.mean() / excess_returns.std()

def calculate_max_drawdown(cumulative_returns: pd.Series) -> float:
    """Calculate maximum drawdown"""
    peak = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - peak) / peak
    return drawdown.min()
