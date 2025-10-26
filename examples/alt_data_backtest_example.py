"""
Example: Using Alternative Data in Backtest

This example demonstrates how to use alternative data sources
to enhance trading strategies in a backtest.

Scenario: HIBOR-Based Bank Stock Trading Strategy
- Use HIBOR rate changes to signal interest rate risk
- Trade bank stocks (0700.HK, 0388.HK) based on HIBOR trends
- Compare backtest with and without alternative data
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.data_pipeline.data_cleaner import DataCleaner
from src.data_pipeline.temporal_aligner import TemporalAligner
from src.data_pipeline.data_normalizer import DataNormalizer
from src.data_pipeline.quality_scorer import QualityScorer
from src.data_pipeline.pipeline_processor import PipelineProcessor
from src.backtest.signal_attribution_metrics import SignalAttributionAnalyzer
from src.backtest.signal_validation import SignalValidator


def generate_sample_price_data(symbol: str, periods: int = 252) -> pd.DataFrame:
    """
    Generate sample price data for demonstration.

    In real scenarios, this would come from your data provider.
    """
    dates = pd.date_range(end=datetime.now(), periods=periods, freq='D')

    # Simulate price movement
    np.random.seed(42)
    returns = np.random.normal(0.0005, 0.015, periods)
    prices = 100 * np.exp(np.cumsum(returns))

    return pd.DataFrame({
        'open': prices + np.random.randn(periods) * 2,
        'high': prices + np.random.uniform(0, 5, periods),
        'low': prices - np.random.uniform(0, 5, periods),
        'close': prices,
        'volume': np.random.uniform(1e6, 5e6, periods),
        'symbol': symbol
    }, index=dates)


def generate_sample_alt_data(periods: int = 252) -> dict:
    """
    Generate sample alternative data (HIBOR rates).

    In real scenarios, this would come from HKMA or other data providers.
    """
    dates = pd.date_range(end=datetime.now(), periods=periods, freq='D')

    # Simulate HIBOR changes (inverse of economic growth)
    hibor_base = np.random.normal(4.0, 0.3, periods)
    hibor_rate = np.cumsum(hibor_base) / 100 + 4.0  # Add trend

    # Normalize to -1 to 1 range (higher HIBOR = higher rates = bearish)
    hibor_normalized = (hibor_rate - hibor_rate.mean()) / hibor_rate.std()

    return {
        'hibor_rate': pd.Series(hibor_rate, index=dates, name='hibor_rate'),
        'hibor_signal': pd.Series(-hibor_normalized, index=dates, name='hibor_signal'),
        # Positive signal when HIBOR falls (good for banks)
    }


def create_price_only_signals(price_data: pd.DataFrame) -> pd.Series:
    """
    Generate trading signals based on price data only.

    Strategy: Simple moving average crossover
    - Buy: 5-day MA > 20-day MA
    - Sell: 5-day MA < 20-day MA
    """
    ma5 = price_data['close'].rolling(window=5).mean()
    ma20 = price_data['close'].rolling(window=20).mean()

    signals = pd.Series(0.0, index=price_data.index)
    signals[ma5 > ma20] = 1.0   # Buy signal
    signals[ma5 < ma20] = -1.0  # Sell signal

    return signals


def create_alt_data_signals(alt_data: dict) -> pd.Series:
    """
    Generate trading signals based on alternative data.

    Strategy: HIBOR-based interest rate view
    - Buy: HIBOR falling (falling rates = good for equities)
    - Sell: HIBOR rising (rising rates = bad for equities)
    """
    hibor_signal = alt_data['hibor_signal']

    # Apply smoothing to reduce noise
    smoothed = hibor_signal.rolling(window=5).mean()

    signals = pd.Series(0.0, index=hibor_signal.index)
    signals[smoothed > 0.2] = 1.0    # Buy
    signals[smoothed < -0.2] = -1.0  # Sell

    return signals


def merge_signals(
    price_signals: pd.Series,
    alt_signals: pd.Series,
    price_weight: float = 0.6,
    alt_weight: float = 0.4
) -> pd.Series:
    """
    Merge price and alternative data signals.

    Weighted combination:
    - 60% from price signal
    - 40% from alternative data signal
    """
    merged = price_signals * price_weight + alt_signals * alt_weight

    # Normalize to -1 to 1 range
    merged = merged / (price_weight + alt_weight)

    return merged


def generate_trades_from_signals(
    signals: pd.Series,
    price_data: pd.DataFrame,
    signal_source: str,
    signal_threshold: float = 0.3
) -> list:
    """
    Convert signals to trade records.

    Each trade entry logs:
    - timestamp, symbol, direction, price
    - profit/loss (simulated)
    - confidence (signal strength)
    """
    trades = []
    position = None

    # Align signals with price data by date
    common_dates = price_data.index.intersection(signals.index)

    for date in common_dates:
        signal = signals[date]
        price = price_data.loc[date, 'close']

        if signal > signal_threshold and position is None:
            # Open buy position
            position = {
                'entry_date': date,
                'entry_price': price,
                'side': 'buy',
                'source': signal_source,
                'signal_strength': signal
            }

        elif signal < -signal_threshold and position is not None:
            # Close position
            exit_price = price
            pnl = (exit_price - position['entry_price']) * 100  # 100 shares

            trade = {
                'symbol': '0700.HK',
                'entry_date': position['entry_date'],
                'exit_date': date,
                'entry_price': position['entry_price'],
                'exit_price': exit_price,
                'side': position['side'],
                'pnl': pnl,
                'source': signal_source,
                'confidence': abs(signal) / 1.0,  # Confidence = signal strength
                'duration_days': (date - position['entry_date']).days
            }

            trades.append(trade)
            position = None

    return trades


def calculate_metrics(trades: list) -> dict:
    """
    Calculate performance metrics from trades.
    """
    if not trades:
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'win_rate': 0.0,
            'total_pnl': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'sharpe_ratio': 0.0
        }

    total_pnl = sum(t['pnl'] for t in trades)
    winning = [t for t in trades if t['pnl'] > 0]
    losing = [t for t in trades if t['pnl'] < 0]

    return {
        'total_trades': len(trades),
        'winning_trades': len(winning),
        'losing_trades': len(losing),
        'win_rate': len(winning) / len(trades) if trades else 0.0,
        'total_pnl': total_pnl,
        'avg_win': sum(t['pnl'] for t in winning) / len(winning) if winning else 0.0,
        'avg_loss': sum(t['pnl'] for t in losing) / len(losing) if losing else 0.0,
        'sharpe_ratio': (total_pnl / len(trades)) / 100 if trades else 0.0,
        'max_pnl': max(t['pnl'] for t in trades) if trades else 0.0,
        'min_pnl': min(t['pnl'] for t in trades) if trades else 0.0,
    }


async def main():
    """
    Main example workflow.
    """
    print("=" * 80)
    print("Alternative Data Backtest Example")
    print("Strategy: HIBOR-Based Bank Stock Trading")
    print("=" * 80)

    # Generate sample data
    print("\n[1/7] Generating sample data...")
    price_data = generate_sample_price_data('0700.HK', periods=252)
    alt_data = generate_sample_alt_data(periods=252)

    print(f"  - Price data: {len(price_data)} days")
    print(f"  - HIBOR data: {len(alt_data['hibor_rate'])} days")

    # Clean price data
    print("\n[2/7] Cleaning price data...")
    cleaner = DataCleaner()
    cleaned_prices = cleaner.clean(price_data)
    print(f"  - Cleaned data: {len(cleaned_prices)} days")

    # Align temporal data
    print("\n[3/7] Aligning to trading days...")
    aligner = TemporalAligner()
    aligned_prices = aligner.align_to_trading_days(cleaned_prices)
    print(f"  - Aligned data: {len(aligned_prices)} days")

    # Normalize data
    print("\n[4/7] Normalizing data...")
    normalizer = DataNormalizer()
    normalized_prices = normalizer.fit_transform(aligned_prices)
    print(f"  - Normalized data: {len(normalized_prices)} days")

    # Score quality
    print("\n[5/7] Scoring data quality...")
    scorer = QualityScorer()
    quality = scorer.calculate_overall_grade(normalized_prices)
    print(f"  - Quality grade: {quality}")

    # Generate trading signals
    print("\n[6/7] Generating trading signals...")

    # Price-only strategy
    price_signals = create_price_only_signals(price_data)
    price_trades = generate_trades_from_signals(
        price_signals, price_data, 'price_only'
    )
    price_metrics = calculate_metrics(price_trades)

    print(f"\n  Price-Only Strategy:")
    print(f"    - Total trades: {price_metrics['total_trades']}")
    print(f"    - Win rate: {price_metrics['win_rate']:.1%}")
    print(f"    - Total P&L: {price_metrics['total_pnl']:,.0f}")
    print(f"    - Sharpe ratio: {price_metrics['sharpe_ratio']:.2f}")

    # Alt-data strategy
    alt_signals = create_alt_data_signals(alt_data)
    alt_trades = generate_trades_from_signals(
        alt_signals, price_data, 'alt_data_only'
    )
    alt_metrics = calculate_metrics(alt_trades)

    print(f"\n  Alternative Data Strategy:")
    print(f"    - Total trades: {alt_metrics['total_trades']}")
    print(f"    - Win rate: {alt_metrics['win_rate']:.1%}")
    print(f"    - Total P&L: {alt_metrics['total_pnl']:,.0f}")
    print(f"    - Sharpe ratio: {alt_metrics['sharpe_ratio']:.2f}")

    # Combined strategy
    merged_signals = merge_signals(price_signals, alt_signals)
    merged_trades = generate_trades_from_signals(
        merged_signals, price_data, 'combined'
    )
    merged_metrics = calculate_metrics(merged_trades)

    print(f"\n  Combined Strategy (60/40 weighted):")
    print(f"    - Total trades: {merged_metrics['total_trades']}")
    print(f"    - Win rate: {merged_metrics['win_rate']:.1%}")
    print(f"    - Total P&L: {merged_metrics['total_pnl']:,.0f}")
    print(f"    - Sharpe ratio: {merged_metrics['sharpe_ratio']:.2f}")

    # Analyze signal attribution
    print("\n[7/7] Analyzing signal attribution...")
    all_trades = price_trades + alt_trades + merged_trades

    analyzer = SignalAttributionAnalyzer()
    accuracy = analyzer.calculate_signal_accuracy(all_trades)

    print(f"\n  Signal Attribution Analysis:")
    print(f"    - Overall accuracy: {accuracy.get('overall_accuracy', 0):.1%}")
    print(f"    - Total trades analyzed: {len(all_trades)}")

    # Calculate improvement
    if price_metrics['total_pnl'] > 0:
        improvement = (merged_metrics['total_pnl'] - price_metrics['total_pnl']) / price_metrics['total_pnl']
        print(f"\n  Alternative Data Impact:")
        print(f"    - P&L improvement: {improvement:+.1%}")
        print(f"    - Sharpe improvement: {(merged_metrics['sharpe_ratio'] - price_metrics['sharpe_ratio']):+.2f}")

    # Validate signals
    print("\n[Validation] Checking for overfitting...")
    validator = SignalValidator()

    train_size = int(len(merged_trades) * 0.7)
    train_trades = merged_trades[:train_size]
    test_trades = merged_trades[train_size:]

    if train_trades and test_trades:
        train_metrics = calculate_metrics(train_trades)
        test_metrics = calculate_metrics(test_trades)

        overfitting = validator.detect_overfitting(
            train_metrics={'sharpe': train_metrics['sharpe_ratio'], 'win_rate': train_metrics['win_rate']},
            test_metrics={'sharpe': test_metrics['sharpe_ratio'], 'win_rate': test_metrics['win_rate']}
        )

        print(f"  - Overfitting level: {overfitting.level}")
        print(f"  - Risk score: {overfitting.risk_score:.2f}")

    print("\n" + "=" * 80)
    print("Example completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
