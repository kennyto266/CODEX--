"""
DataChunker Integration Example
Demonstrates practical usage with real trading data processing
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from performance.data_chunker import DataChunker, ChunkConfig, ChunkStrategy

def create_sample_trading_data(symbol="0700.HK", years=5):
    """Create realistic trading data for demonstration"""
    print(f"\nCreating {years}-year trading dataset for {symbol}...")

    # Business days (trading days only)
    dates = pd.date_range('2020-01-01', periods=years * 252, freq='B')

    # Generate realistic OHLCV data
    np.random.seed(42)  # For reproducible results

    # Price simulation with trend and volatility
    n = len(dates)
    returns = np.random.normal(0.0005, 0.02, n)  # Daily returns

    # Add some autocorrelation
    for i in range(1, n):
        returns[i] += 0.1 * returns[i-1]

    # Generate price series
    close_prices = [100.0]
    for r in returns[1:]:
        close_prices.append(close_prices[-1] * (1 + r))

    close = np.array(close_prices)

    # Generate OHLC from close
    high = close * (1 + np.abs(np.random.normal(0, 0.01, n)))
    low = close * (1 - np.abs(np.random.normal(0, 0.01, n)))
    open_price = close * (1 + np.random.normal(0, 0.005, n))
    volume = np.random.randint(1000000, 10000000, n)

    df = pd.DataFrame({
        'date': dates,
        'symbol': symbol,
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    })

    print(f"   Created {len(df)} rows ({years} years of trading data)")
    print(f"   Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
    print(f"   Memory usage: {df.memory_usage(deep=True).sum() / (1024*1024):.2f} MB")

    return df

def example_1_basic_chunking():
    """Example 1: Basic chunking operations"""
    print("\n" + "="*80)
    print("Example 1: Basic Data Chunking")
    print("="*80)

    # Create 5-year dataset
    df = create_sample_trading_data("0700.HK", years=5)

    # Create chunker with ADAPTIVE strategy
    config = ChunkConfig(
        strategy=ChunkStrategy.ADAPTIVE,
        max_memory_mb=512.0,
        overlap_rows=0
    )
    chunker = DataChunker(config)

    # Split into chunks
    print("\n1. Chunking DataFrame...")
    chunks = chunker.chunk_dataframe(df, chunk_column='date')
    print(f"   Created {len(chunks)} chunks")

    # Display chunk information
    print("\n2. Chunk Details:")
    for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
        print(f"   Chunk {i}: {chunk.rows} rows, {chunk.memory_estimate_mb:.2f} MB")
        print(f"            Date range: {chunk.start_date} to {chunk.end_date}")

    return chunker, df

def example_2_indicator_calculation(chunker, df):
    """Example 2: Calculate technical indicators on chunks"""
    print("\n" + "="*80)
    print("Example 2: Technical Indicator Calculation (SMA, RSI)")
    print("="*80)

    def calculate_indicators(chunk_df):
        """Calculate SMA and RSI for a chunk"""
        close = chunk_df['close']

        # Simple Moving Average
        sma_20 = close.rolling(window=20, min_periods=1).mean()
        sma_50 = close.rolling(window=50, min_periods=1).mean()

        # RSI calculation
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return {
            'chunk_start': chunk_df.index[0],
            'chunk_end': chunk_df.index[-1],
            'sma_20_last': sma_20.iloc[-1],
            'sma_50_last': sma_50.iloc[-1],
            'rsi_last': rsi.iloc[-1],
            'close_last': close.iloc[-1]
        }

    # Process chunks sequentially
    print("\n1. Sequential Processing...")
    results = []
    for i, chunk_df in enumerate(chunker.iterate_chunks(df, chunk_column='date')):
        result = calculate_indicators(chunk_df)
        results.append(result)

        if i >= 2:  # Only process first 3 chunks for demo
            break

    print(f"   Processed {len(results)} chunks")
    print("\n2. Results (first chunk):")
    for key, value in results[0].items():
        print(f"   {key}: {value:.2f}")

    return results

def example_3_parallel_backtest(chunker, df):
    """Example 3: Parallel backtest simulation"""
    print("\n" + "="*80)
    print("Example 3: Parallel Backtest Simulation")
    print("="*80)

    def backtest_strategy(chunk_df):
        """Simulate a simple moving average crossover strategy"""
        close = chunk_df['close']
        sma_short = close.rolling(20).mean()
        sma_long = close.rolling(50).mean()

        # Generate signals
        signal = (sma_short > sma_long).astype(int)
        signal_change = signal.diff()

        # Calculate returns
        returns = close.pct_change()
        strategy_returns = returns * signal.shift(1)

        # Calculate performance metrics
        total_return = (1 + strategy_returns).prod() - 1
        volatility = strategy_returns.std() * np.sqrt(252)
        sharpe = (strategy_returns.mean() * 252) / volatility if volatility > 0 else 0

        return {
            'chunk_id': chunk_df.index[0],
            'total_return': total_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe,
            'trades': signal_change.abs().sum()
        }

    # Get backtest optimization recommendations
    print("\n1. Backtest Optimization Recommendations:")
    optimization = chunker.optimize_for_backtest(df, 'sma')
    for key, value in optimization.items():
        print(f"   {key}: {value}")

    # Run parallel backtest
    print("\n2. Running Parallel Backtest...")
    print(f"   Using {optimization['recommended_workers']} workers")

    start_time = datetime.now()
    results = chunker.parallel_process_chunks(
        df,
        backtest_strategy,
        chunk_column='date',
        num_workers=optimization['recommended_workers']
    )
    duration = (datetime.now() - start_time).total_seconds()

    print(f"\n3. Backtest Results:")
    print(f"   Processed {len(results)} chunks in {duration:.2f}s")
    print(f"   Average return: {np.mean([r['total_return'] for r in results if r]):.4f}")
    print(f"   Average Sharpe: {np.mean([r['sharpe_ratio'] for r in results if r]):.4f}")
    print(f"   Total trades: {sum([r['trades'] for r in results if r])}")

    return results

def example_4_memory_monitoring(chunker, df):
    """Example 4: Memory monitoring and statistics"""
    print("\n" + "="*80)
    print("Example 4: Memory Monitoring and Statistics")
    print("="*80)

    # Process all chunks
    print("\n1. Processing all chunks...")
    chunk_count = 0
    for chunk_df in chunker.iterate_chunks(df, chunk_column='date'):
        chunk_count += 1

    # Get memory statistics
    print("\n2. Memory Usage Statistics:")
    stats = chunker.get_memory_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    # Monitor system memory
    print("\n3. System Memory Status:")
    import psutil
    memory = psutil.virtual_memory()
    print(f"   Total: {memory.total / (1024**3):.2f} GB")
    print(f"   Available: {memory.available / (1024**3):.2f} GB")
    print(f"   Used: {memory.percent}%")
    print(f"   Free: {memory.free / (1024**3):.2f} GB")

    return stats

def example_5_different_strategies(df):
    """Example 5: Compare different chunking strategies"""
    print("\n" + "="*80)
    print("Example 5: Comparing Chunking Strategies")
    print("="*80)

    strategies = [
        (ChunkStrategy.TIME_BASED, "Time-based (by date)"),
        (ChunkStrategy.SIZE_BASED, "Size-based (by rows)"),
        (ChunkStrategy.ADAPTIVE, "Adaptive (automatic)")
    ]

    print("\n1. Strategy Comparison:")
    for strategy, name in strategies:
        config = ChunkConfig(
            strategy=strategy,
            max_memory_mb=512.0
        )
        chunker = DataChunker(config)

        start_time = datetime.now()
        chunks = chunker.chunk_dataframe(df, chunk_column='date')
        duration = (datetime.now() - start_time).total_seconds()

        total_memory = sum(c.memory_estimate_mb for c in chunks)

        print(f"\n   {name}:")
        print(f"      Chunks: {len(chunks)}")
        print(f"      Time: {duration:.4f}s")
        print(f"      Total memory: {total_memory:.2f} MB")

        if chunks[0].start_date:
            print(f"      Date range: {chunks[0].start_date} to {chunks[-1].end_date}")

def main():
    """Run all examples"""
    print("\n" + "#"*80)
    print("# DataChunker - Practical Integration Examples")
    print("#"*80)

    # Example 1: Basic chunking
    chunker, df = example_1_basic_chunking()

    # Example 2: Indicator calculation
    results_indicators = example_2_indicator_calculation(chunker, df)

    # Example 3: Parallel backtest
    results_backtest = example_3_parallel_backtest(chunker, df)

    # Example 4: Memory monitoring
    stats = example_4_memory_monitoring(chunker, df)

    # Example 5: Strategy comparison
    example_5_different_strategies(df)

    # Cleanup
    print("\n" + "="*80)
    print("Cleanup")
    print("="*80)
    chunker.cleanup()
    print("[OK] Resources cleaned up successfully")

    print("\n" + "#"*80)
    print("# All Examples Completed Successfully!")
    print("#"*80)

if __name__ == "__main__":
    main()
