"""
Mock data generators for testing.

This module provides utilities to generate mock OHLCV data, asset profiles,
strategy results, and other test data needed for unit and integration tests.

Used by: data_layer, calculation_layer, visualization_layer tests
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import random


class MockOHLCVGenerator:
    """Generate realistic mock OHLCV (Open, High, Low, Close, Volume) data."""

    def __init__(self, seed: int = 42):
        """Initialize with random seed for reproducibility."""
        random.seed(seed)
        np.random.seed(seed)

    def generate(
        self,
        symbol: str = "0700.HK",
        start_date: datetime = None,
        end_date: datetime = None,
        num_days: int = 100,
        start_price: float = 100.0,
        volatility: float = 0.02,
    ) -> pd.DataFrame:
        """
        Generate mock OHLCV data.

        Args:
            symbol: Stock symbol
            start_date: Start date (if None, uses num_days from today)
            end_date: End date (if None, uses today)
            num_days: Number of trading days to generate
            start_price: Starting price
            volatility: Daily volatility (std deviation of returns)

        Returns:
            DataFrame with columns: Date, Open, High, Low, Close, Volume

        Example:
            >>> gen = MockOHLCVGenerator()
            >>> df = gen.generate("0700.HK", num_days=252)
            >>> print(df.head())
        """
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=num_days)

        # Generate trading dates (exclude weekends)
        dates = pd.bdate_range(start=start_date, end=end_date, freq='B')[:num_days]

        # Generate price series using geometric Brownian motion
        returns = np.random.normal(0.0005, volatility, size=len(dates))
        prices = start_price * np.exp(np.cumsum(returns))

        # Generate OHLCV data
        data = []
        for i, (date, price) in enumerate(zip(dates, prices)):
            # Random intraday movement
            open_price = price * (1 + np.random.normal(0, volatility / 2))
            close_price = price * (1 + np.random.normal(0, volatility / 2))
            high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, volatility / 3)))
            low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, volatility / 3)))

            # Random volume (in units)
            volume = int(np.random.lognormal(mean=14, sigma=0.5))

            data.append({
                'Date': date,
                'Open': round(open_price, 2),
                'High': round(high_price, 2),
                'Low': round(low_price, 2),
                'Close': round(close_price, 2),
                'Volume': volume,
            })

        df = pd.DataFrame(data)
        df.set_index('Date', inplace=True)
        return df

    def generate_multiple(
        self,
        symbols: List[str],
        num_days: int = 100,
    ) -> Dict[str, pd.DataFrame]:
        """
        Generate mock data for multiple symbols.

        Args:
            symbols: List of stock symbols
            num_days: Number of trading days

        Returns:
            Dictionary with symbol as key, DataFrame as value
        """
        return {symbol: self.generate(symbol, num_days=num_days) for symbol in symbols}


class MockAssetProfileGenerator:
    """Generate mock asset profile data."""

    @staticmethod
    def generate(
        symbol: str = "0700.HK",
        sector: str = "Technology",
        industry: str = "Internet Services",
        market_cap: float = 5e11,
    ) -> Dict[str, Any]:
        """
        Generate mock asset profile.

        Args:
            symbol: Stock symbol
            sector: Industry sector
            industry: Industry classification
            market_cap: Market capitalization in base currency

        Returns:
            Dictionary with asset profile data

        Example:
            >>> profile = MockAssetProfileGenerator.generate("0700.HK")
            >>> print(f"Market Cap: {profile['market_cap']}")
        """
        return {
            'symbol': symbol,
            'name': f'Company {symbol}',
            'sector': sector,
            'industry': industry,
            'market_cap': market_cap,
            'employees': int(np.random.uniform(1000, 100000)),
            'website': f'https://company-{symbol.lower()}.com',
            'currency': 'HKD' if '.HK' in symbol else 'USD',
            'exchange': 'HKEX' if '.HK' in symbol else 'NYSE',
        }


class MockStrategyResultsGenerator:
    """Generate mock strategy results."""

    @staticmethod
    def generate(
        symbol: str = "0700.HK",
        num_trades: int = 50,
        win_rate: float = 0.55,
        avg_win: float = 0.05,
        avg_loss: float = -0.03,
    ) -> Dict[str, Any]:
        """
        Generate mock strategy backtest results.

        Args:
            symbol: Stock symbol
            num_trades: Number of trades in backtest
            win_rate: Proportion of winning trades (0-1)
            avg_win: Average return on winning trades
            avg_loss: Average return on losing trades

        Returns:
            Dictionary with strategy results

        Example:
            >>> results = MockStrategyResultsGenerator.generate(
            ...     symbol="0700.HK",
            ...     num_trades=100,
            ...     win_rate=0.6
            ... )
            >>> print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        """
        # Calculate trade results
        num_wins = int(num_trades * win_rate)
        num_losses = num_trades - num_wins

        trade_returns = (
            [avg_win] * num_wins +
            [avg_loss] * num_losses
        )
        random.shuffle(trade_returns)

        # Calculate metrics
        total_return = sum(trade_returns)
        avg_return = np.mean(trade_returns)
        std_return = np.std(trade_returns)
        sharpe_ratio = (avg_return / std_return * np.sqrt(252)) if std_return > 0 else 0

        # Calculate drawdown
        cumulative_returns = np.cumprod([1 + r for r in trade_returns])
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = np.min(drawdown)

        return {
            'symbol': symbol,
            'total_return': total_return,
            'num_trades': num_trades,
            'num_wins': num_wins,
            'num_losses': num_losses,
            'win_rate': win_rate,
            'avg_return': avg_return,
            'std_return': std_return,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sharpe_ratio * 1.5,  # Simplified
            'max_drawdown': max_drawdown,
            'profit_factor': abs(np.sum([r for r in trade_returns if r > 0]) /
                                np.sum([r for r in trade_returns if r < 0]))
                            if any(r < 0 for r in trade_returns) else float('inf'),
        }


class MockPerformanceMetricsGenerator:
    """Generate mock performance metrics."""

    @staticmethod
    def generate(
        symbol: str = "0700.HK",
        period_days: int = 252,
        annual_return: float = 0.15,
    ) -> Dict[str, Any]:
        """
        Generate mock performance metrics.

        Args:
            symbol: Stock symbol
            period_days: Number of trading days in period
            annual_return: Expected annual return

        Returns:
            Dictionary with performance metrics
        """
        daily_return = annual_return / 252
        daily_std = annual_return / np.sqrt(252)

        returns = np.random.normal(daily_return, daily_std, size=period_days)
        cumulative_returns = np.cumprod([1 + r for r in returns])

        return {
            'symbol': symbol,
            'period_days': period_days,
            'total_return': (cumulative_returns[-1] - 1) * 100,
            'annual_return': annual_return * 100,
            'max_drawdown': -np.min((cumulative_returns - np.maximum.accumulate(cumulative_returns)) /
                                     np.maximum.accumulate(cumulative_returns)) * 100,
            'volatility': np.std(returns) * np.sqrt(252) * 100,
            'sharpe_ratio': annual_return / (daily_std * np.sqrt(252)),
            'sortino_ratio': annual_return / (np.std([r for r in returns if r < 0]) * np.sqrt(252)),
            'calmar_ratio': (annual_return / abs(np.min((cumulative_returns - np.maximum.accumulate(cumulative_returns)) /
                                                        np.maximum.accumulate(cumulative_returns)))) if True else 0,
        }


# Convenient shortcuts
def mock_ohlcv_data(symbol: str = "0700.HK", num_days: int = 100) -> pd.DataFrame:
    """Quick function to generate mock OHLCV data."""
    return MockOHLCVGenerator().generate(symbol, num_days=num_days)


def mock_asset_profile(symbol: str = "0700.HK") -> Dict[str, Any]:
    """Quick function to generate mock asset profile."""
    return MockAssetProfileGenerator.generate(symbol)


def mock_strategy_results(symbol: str = "0700.HK", num_trades: int = 50) -> Dict[str, Any]:
    """Quick function to generate mock strategy results."""
    return MockStrategyResultsGenerator.generate(symbol, num_trades=num_trades)


def mock_performance_metrics(symbol: str = "0700.HK") -> Dict[str, Any]:
    """Quick function to generate mock performance metrics."""
    return MockPerformanceMetricsGenerator.generate(symbol)
