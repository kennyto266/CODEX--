"""Backtest engine interface and base classes.

This module defines the abstract base class for backtest engines
and core backtest result structures.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Protocol
import pandas as pd

from .data import OHLCV, Signal, Position, Trade, BacktestConfig


class Strategy(Protocol):
    """Protocol for strategy implementations.
    
    All strategies must implement this protocol to be compatible
    with the backtest engine.
    """
    
    def generate_signals(self, data: List[OHLCV]) -> List[Signal]:
        """Generate trading signals for the given data.
        
        Args:
            data: Historical price data
            
        Returns:
            List of trading signals
        """
        ...
    
    def get_indicators(self) -> List[str]:
        """Get list of required indicators.
        
        Returns:
            List of indicator names
        """
        ...


@dataclass
class BacktestResult:
    """Results from a backtest run.
    
    Contains all performance metrics and trade history.
    """
    config: BacktestConfig
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    profit_factor: float
    trades: List[Trade] = field(default_factory=list)
    equity_curve: pd.DataFrame = field(default_factory=pd.DataFrame)
    drawdown_curve: pd.DataFrame = field(default_factory=pd.DataFrame)
    monthly_returns: pd.DataFrame = field(default_factory=pd.DataFrame)
    trade_summary: Dict = field(default_factory=dict)
    benchmark_return: Optional[float] = None
    alpha: Optional[float] = None
    beta: Optional[float] = None
    
    @property
    def total_pnl(self) -> float:
        """Total P&L."""
        return self.final_capital - self.initial_capital
    
    @property
    def is_profitable(self) -> bool:
        """Check if strategy is profitable."""
        return self.total_return > 0


class BacktestEngine(ABC):
    """Abstract base class for backtest engines.
    
    All backtest engines must inherit from this class and implement
    the abstract methods.
    """
    
    def __init__(self, config: BacktestConfig):
        """Initialize backtest engine.
        
        Args:
            config: Backtest configuration
        """
        self.config = config
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.equity_curve = []
        self.signals = []
    
    @abstractmethod
    def run(self, data: List[OHLCV], strategy) -> BacktestResult:
        """Run backtest.
        
        Args:
            data: Historical price data
            strategy: Trading strategy to test
            
        Returns:
            Backtest results
        """
        pass
    
    @abstractmethod
    def run_with_optimization(self, data: List[OHLCV], 
                            strategy_class,
                            parameter_grid: Dict) -> List[BacktestResult]:
        """Run backtest with parameter optimization.
        
        Args:
            data: Historical price data
            strategy_class: Strategy class to optimize
            parameter_grid: Dictionary of parameter ranges
            
        Returns:
            List of backtest results for different parameter combinations
        """
        pass
