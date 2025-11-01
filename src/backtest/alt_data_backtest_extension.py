"""
Alternative Data Backtest Extension

Extends the EnhancedBacktestEngine to support alternative data signals
alongside price-based trading signals.

Features:
    - Alternative data signal processing
    - Signal merging (price + alt data)
    - Signal source tracking
    - Signal attribution to trades
    - Performance metrics by signal source

Usage:
    engine = AltDataBacktestEngine(config)
    result = await engine.run_backtest_with_alt_data(
        strategy_func,
        alt_data_signals={
            'HIBOR': hibor_series,
            'Visitor_Arrivals': visitor_series
        }
    )
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Callable, Tuple
import pandas as pd
import numpy as np
from enum import Enum
from pydantic import BaseModel, Field

try:
    from .enhanced_backtest_engine import EnhancedBacktestEngine, Trade, BacktestConfig, BacktestResult
except ImportError as e:
    # Handle cases where dependencies are not fully available
    EnhancedBacktestEngine = None
    Trade = None
    BacktestConfig = None
    BacktestResult = None

try:
    from ..analysis.correlation_analyzer import CorrelationAnalyzer
except ImportError:
    CorrelationAnalyzer = None


class SignalSource(str, Enum):
    """Signal source enumeration"""
    PRICE_ONLY = "price_only"
    ALT_DATA_ONLY = "alt_data_only"
    COMBINED = "combined"


class SignalTradeMap(BaseModel):
    """Mapping of signals to trades"""
    trade_id: str = Field(..., description="Unique trade identifier")
    signal_type: SignalSource = Field(..., description="Type of signal source")
    price_signal_strength: float = Field(default=0.0, description="Price signal strength (-1 to 1)")
    alt_signal_strength: float = Field(default=0.0, description="Alt data signal strength (-1 to 1)")
    confidence: float = Field(..., description="Signal confidence (0 to 1)")
    correlation_at_trade: Optional[float] = Field(None, description="Correlation at time of trade")
    pnl: Optional[float] = Field(None, description="Profit/loss from trade")
    signal_accuracy: Optional[bool] = Field(None, description="Whether trade was profitable")


class AltDataTradeExtension(BaseModel):
    """Extended Trade model with alternative data tracking"""
    base_trade: Trade = Field(..., description="Base trade object")
    signal_source: SignalSource = Field(..., description="Source of trading signal")
    price_signal: Optional[float] = Field(None, description="Price-based signal value")
    alt_signal: Optional[float] = Field(None, description="Alternative data signal value")
    merged_signal: float = Field(..., description="Merged signal value")
    confidence: float = Field(..., description="Signal confidence score")
    alt_indicators: Optional[Dict[str, float]] = Field(None, description="Alternative indicators at trade time")


class AltDataBacktestEngine(EnhancedBacktestEngine):
    """
    Enhanced Backtest Engine with Alternative Data Support

    Extends EnhancedBacktestEngine to process and integrate alternative data signals
    with price-based trading signals.
    """

    def __init__(self, config: BacktestConfig):
        """Initialize Alt Data Backtest Engine"""
        super().__init__(config)
        self.logger = logging.getLogger("hk_quant_system.alt_data_backtest")

        # Alternative data storage
        self.alt_data_signals: Dict[str, pd.Series] = {}
        self.alt_data_trades: List[AltDataTradeExtension] = []
        self.signal_trade_maps: List[SignalTradeMap] = []

        # Signal tracking
        self.price_signal_count: int = 0
        self.alt_signal_count: int = 0
        self.combined_signal_count: int = 0

        # Correlation analyzer
        self.correlation_analyzer = CorrelationAnalyzer()

    async def run_backtest_with_alt_data(
        self,
        strategy_func: Callable,
        alt_data_signals: Dict[str, pd.Series],
        alt_data_strategy_func: Optional[Callable] = None,
        signal_merge_strategy: str = "weighted"
    ) -> BacktestResult:
        """
        Run backtest with alternative data signals

        Args:
            strategy_func: Original price-based strategy function
            alt_data_signals: Dictionary mapping indicator names to time series
            alt_data_strategy_func: Optional alternative data strategy function
            signal_merge_strategy: How to merge signals ('weighted', 'voting', 'max')

        Returns:
            Enhanced BacktestResult with signal attribution
        """
        try:
            self.logger.info(f"Starting backtest with alternative data ({len(alt_data_signals)} indicators)...")

            # Store alternative data
            self.alt_data_signals = alt_data_signals

            # Reset state
            self._reset_backtest_state()
            self.alt_data_trades = []
            self.signal_trade_maps = []

            # Get all trading dates
            all_dates = set()
            for symbol_data in self.historical_data.values():
                all_dates.update(symbol_data.index.date)

            trading_dates = sorted(list(all_dates))
            self.logger.info(f"Running backtest with alt data for {len(trading_dates)} trading days")

            # Process each trading day
            for i, current_date in enumerate(trading_dates):
                await self._process_trading_day_with_alt_data(
                    current_date,
                    strategy_func,
                    alt_data_strategy_func,
                    signal_merge_strategy
                )

                # Update portfolio value
                portfolio_value = await self._calculate_portfolio_value(current_date)
                self.portfolio_values.append(portfolio_value)

                # Calculate daily returns
                if i > 0:
                    daily_return = (portfolio_value - self.portfolio_values[-2]) / self.portfolio_values[-2]
                    self.daily_returns.append(daily_return)

                    if hasattr(self, 'benchmark_data'):
                        benchmark_return = await self._calculate_benchmark_return(current_date)
                        self.benchmark_returns.append(benchmark_return)

                # Progress reporting
                if i % 50 == 0:
                    self.logger.info(f"Processed {i}/{len(trading_dates)} trading days")

            # Calculate results
            result = await self._calculate_backtest_results()

            # Add signal attribution metrics
            result = self._add_signal_attribution_metrics(result)

            self.logger.info("Backtest with alternative data completed successfully")
            return result

        except Exception as e:
            self.logger.exception(f"Error running backtest with alt data: {e}")
            raise

    async def _process_trading_day_with_alt_data(
        self,
        current_date: date,
        strategy_func: Callable,
        alt_data_strategy_func: Optional[Callable],
        merge_strategy: str
    ) -> None:
        """Process a trading day with alternative data signals"""
        try:
            # Get current market data
            current_data = {}
            for symbol, data in self.historical_data.items():
                if current_date in data.index.date:
                    current_data[symbol] = data.loc[data.index.date == current_date].iloc[0]

            if not current_data:
                return

            # Get price-based signals
            price_signals = await strategy_func(current_data, self.current_positions)

            # Get alternative data signals
            alt_signals = []
            if alt_data_strategy_func:
                # Get alt data values for current date
                alt_data_current = {}
                for indicator_name, indicator_series in self.alt_data_signals.items():
                    dates_match = indicator_series.index[indicator_series.index.date == current_date]
                    if len(dates_match) > 0:
                        alt_data_current[indicator_name] = indicator_series.loc[dates_match[0]]

                if alt_data_current:
                    alt_signals = await alt_data_strategy_func(alt_data_current, self.current_positions)

            # Merge signals
            merged_signals = self._merge_signals(
                price_signals,
                alt_signals,
                merge_strategy
            )

            # Execute trades from merged signals
            for merged_signal in merged_signals:
                await self._execute_trade_with_signal_tracking(
                    merged_signal,
                    current_date
                )

            # Update positions
            await self._update_positions()

        except Exception as e:
            self.logger.error(f"Error processing trading day with alt data {current_date}: {e}")

    def _merge_signals(
        self,
        price_signals: List[Dict[str, Any]],
        alt_signals: List[Dict[str, Any]],
        strategy: str = "weighted"
    ) -> List[Dict[str, Any]]:
        """
        Merge price-based and alternative data signals

        Args:
            price_signals: Signals from price-based strategy
            alt_signals: Signals from alternative data strategy
            strategy: Merging strategy ('weighted', 'voting', 'max')

        Returns:
            List of merged signals
        """
        merged_signals = []

        # Create maps by symbol for easier lookup
        price_signal_map = {sig.get('symbol'): sig for sig in price_signals}
        alt_signal_map = {sig.get('symbol'): sig for sig in alt_signals}

        # Get all symbols involved
        all_symbols = set(price_signal_map.keys()) | set(alt_signal_map.keys())

        for symbol in all_symbols:
            price_sig = price_signal_map.get(symbol)
            alt_sig = alt_signal_map.get(symbol)

            # Merge based on strategy
            if strategy == "weighted":
                merged = self._merge_signals_weighted(symbol, price_sig, alt_sig)
            elif strategy == "voting":
                merged = self._merge_signals_voting(symbol, price_sig, alt_sig)
            elif strategy == "max":
                merged = self._merge_signals_max(symbol, price_sig, alt_sig)
            else:
                merged = price_sig or alt_sig

            if merged:
                merged_signals.append(merged)

        return merged_signals

    def _merge_signals_weighted(
        self,
        symbol: str,
        price_sig: Optional[Dict],
        alt_sig: Optional[Dict]
    ) -> Optional[Dict[str, Any]]:
        """Merge signals using weighted average"""
        if not price_sig and not alt_sig:
            return None

        if price_sig and not alt_sig:
            self.price_signal_count += 1
            price_sig['signal_source'] = SignalSource.PRICE_ONLY
            price_sig['confidence'] = price_sig.get('confidence', 0.7)
            return price_sig

        if alt_sig and not price_sig:
            self.alt_signal_count += 1
            alt_sig['signal_source'] = SignalSource.ALT_DATA_ONLY
            alt_sig['confidence'] = alt_sig.get('confidence', 0.7)
            return alt_sig

        # Both signals present - weighted merge
        self.combined_signal_count += 1
        price_weight = 0.6
        alt_weight = 0.4

        price_strength = self._signal_to_strength(price_sig.get('side', 'hold'))
        alt_strength = self._signal_to_strength(alt_sig.get('side', 'hold'))

        merged_strength = price_weight * price_strength + alt_weight * alt_strength

        # Determine merged signal direction
        merged_side = 'hold'
        if merged_strength > 0.3:
            merged_side = 'buy'
        elif merged_strength < -0.3:
            merged_side = 'sell'

        price_conf = price_sig.get('confidence', 0.7)
        alt_conf = alt_sig.get('confidence', 0.7)
        merged_conf = (price_conf + alt_conf) / 2

        return {
            'symbol': symbol,
            'side': merged_side,
            'quantity': max(price_sig.get('quantity', 0), alt_sig.get('quantity', 0)),
            'confidence': merged_conf,
            'signal_source': SignalSource.COMBINED,
            'price_signal': price_strength,
            'alt_signal': alt_strength,
            'price_strength': price_sig.get('confidence', 0.7),
            'alt_strength': alt_sig.get('confidence', 0.7)
        }

    def _merge_signals_voting(
        self,
        symbol: str,
        price_sig: Optional[Dict],
        alt_sig: Optional[Dict]
    ) -> Optional[Dict[str, Any]]:
        """Merge signals using majority voting"""
        signals = [s for s in [price_sig, alt_sig] if s]
        if not signals:
            return None

        if len(signals) == 1:
            signals[0]['signal_source'] = SignalSource.PRICE_ONLY if price_sig else SignalSource.ALT_DATA_ONLY
            return signals[0]

        # Both signals - voting
        buy_votes = sum(1 for s in signals if s.get('side') == 'buy')
        sell_votes = sum(1 for s in signals if s.get('side') == 'sell')

        if buy_votes > sell_votes:
            side = 'buy'
        elif sell_votes > buy_votes:
            side = 'sell'
        else:
            side = 'hold'

        self.combined_signal_count += 1
        return {
            'symbol': symbol,
            'side': side,
            'quantity': max(s.get('quantity', 0) for s in signals),
            'confidence': min(s.get('confidence', 0.7) for s in signals),
            'signal_source': SignalSource.COMBINED
        }

    def _merge_signals_max(
        self,
        symbol: str,
        price_sig: Optional[Dict],
        alt_sig: Optional[Dict]
    ) -> Optional[Dict[str, Any]]:
        """Merge signals using max confidence"""
        signals = [s for s in [price_sig, alt_sig] if s]
        if not signals:
            return None

        best_signal = max(signals, key=lambda s: s.get('confidence', 0.5))
        best_signal['signal_source'] = SignalSource.PRICE_ONLY if price_sig == best_signal else SignalSource.ALT_DATA_ONLY

        if price_sig and alt_sig:
            best_signal['signal_source'] = SignalSource.COMBINED

        return best_signal

    @staticmethod
    def _signal_to_strength(side: str) -> float:
        """Convert signal side to strength value"""
        if side == 'buy':
            return 1.0
        elif side == 'sell':
            return -1.0
        else:
            return 0.0

    async def _execute_trade_with_signal_tracking(
        self,
        signal: Dict[str, Any],
        trade_date: date
    ) -> None:
        """Execute trade and track signal attribution"""
        try:
            symbol = signal.get('symbol')
            signal_source = signal.get('signal_source', SignalSource.PRICE_ONLY)

            # Execute base trade
            await self._execute_trade(signal, trade_date)

            # Track the signal for this trade
            if len(self.trades) > 0:
                latest_trade = self.trades[-1]

                # Create extended trade record
                alt_trade = AltDataTradeExtension(
                    base_trade=latest_trade,
                    signal_source=signal_source,
                    price_signal=signal.get('price_signal'),
                    alt_signal=signal.get('alt_signal'),
                    merged_signal=self._signal_to_strength(signal.get('side', 'hold')),
                    confidence=signal.get('confidence', 0.7),
                    alt_indicators=signal.get('alt_indicators')
                )

                self.alt_data_trades.append(alt_trade)

        except Exception as e:
            self.logger.error(f"Error executing trade with signal tracking: {e}")

    def _add_signal_attribution_metrics(self, result: BacktestResult) -> BacktestResult:
        """Add signal attribution metrics to backtest result"""
        # Calculate signal performance metrics
        signal_performance = self._calculate_signal_performance()

        # Add to result metadata
        if not hasattr(result, 'metadata'):
            result.metadata = {}

        result.metadata['signal_attribution'] = signal_performance
        result.metadata['price_signal_trades'] = self.price_signal_count
        result.metadata['alt_signal_trades'] = self.alt_signal_count
        result.metadata['combined_signal_trades'] = self.combined_signal_count

        return result

    def _calculate_signal_performance(self) -> Dict[str, Any]:
        """Calculate performance breakdown by signal source"""
        price_trades = [t for t in self.alt_data_trades if t.signal_source == SignalSource.PRICE_ONLY]
        alt_trades = [t for t in self.alt_data_trades if t.signal_source == SignalSource.ALT_DATA_ONLY]
        combined_trades = [t for t in self.alt_data_trades if t.signal_source == SignalSource.COMBINED]

        def calc_metrics(trades):
            if not trades:
                return None

            wins = sum(1 for t in trades if t.base_trade.pnl and t.base_trade.pnl > 0)
            losses = sum(1 for t in trades if t.base_trade.pnl and t.base_trade.pnl < 0)
            total_pnl = sum(t.base_trade.pnl or 0 for t in trades)
            avg_confidence = np.mean([t.confidence for t in trades]) if trades else 0

            return {
                'count': len(trades),
                'wins': wins,
                'losses': losses,
                'win_rate': wins / len(trades) if trades else 0,
                'total_pnl': total_pnl,
                'avg_pnl': total_pnl / len(trades) if trades else 0,
                'avg_confidence': avg_confidence
            }

        return {
            'price_only': calc_metrics(price_trades),
            'alt_data_only': calc_metrics(alt_trades),
            'combined': calc_metrics(combined_trades)
        }


# Export for use
__all__ = [
    'AltDataBacktestEngine',
    'AltDataTradeExtension',
    'SignalTradeMap',
    'SignalSource'
]
