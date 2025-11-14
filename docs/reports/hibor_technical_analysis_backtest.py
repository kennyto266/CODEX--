#!/usr/bin/env python3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

print('=' * 80)
print('HIBOR TECHNICAL ANALYSIS BACKTEST')
print('Using Z-Score, SMA, EMA, RSI, MACD, Bollinger Bands')
print('=' * 80)

# Load the complete real HIBOR data
data_file = 'data/real_gov_data/hibor_real_20251103_094619.csv'
df = pd.read_csv(data_file)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

print(f'\nData loaded: {len(df)} records')
print(f'Date range: {df["date"].min().date()} to {df["date"].max().date()}')

# Technical Analysis Functions
def calculate_zscore(series, window=20):
    """Calculate Z-Score (number of standard deviations from mean)"""
    mean = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    return (series - mean) / std

def calculate_sma(series, window=20):
    """Calculate Simple Moving Average"""
    return series.rolling(window=window).mean()

def calculate_ema(series, window=20):
    """Calculate Exponential Moving Average"""
    return series.ewm(span=window).mean()

def calculate_rsi(series, window=14):
    """Calculate Relative Strength Index"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(series, fast=12, slow=26, signal=9):
    """Calculate MACD (Moving Average Convergence Divergence)"""
    ema_fast = series.ewm(span=fast).mean()
    ema_slow = series.ewm(span=slow).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_bollinger_bands(series, window=20, num_std=2):
    """Calculate Bollinger Bands"""
    sma = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    upper = sma + (std * num_std)
    lower = sma - (std * num_std)
    return upper, sma, lower

# Apply Technical Indicators to HIBOR Overnight
print(f'\n' + '=' * 80)
print('CALCULATING TECHNICAL INDICATORS')
print('=' * 80)

# Z-Score
df['hibor_zscore_20'] = calculate_zscore(df['hibor_overnight'], 20)
df['hibor_zscore_60'] = calculate_zscore(df['hibor_overnight'], 60)

# Moving Averages
df['hibor_sma_20'] = calculate_sma(df['hibor_overnight'], 20)
df['hibor_sma_50'] = calculate_sma(df['hibor_overnight'], 50)
df['hibor_ema_20'] = calculate_ema(df['hibor_overnight'], 20)
df['hibor_ema_50'] = calculate_ema(df['hibor_overnight'], 50)

# RSI
df['hibor_rsi_14'] = calculate_rsi(df['hibor_overnight'], 14)

# MACD
df['hibor_macd'], df['hibor_macd_signal'], df['hibor_macd_hist'] = calculate_macd(df['hibor_overnight'])

# Bollinger Bands
df['hibor_bb_upper'], df['hibor_bb_middle'], df['hibor_bb_lower'] = calculate_bollinger_bands(df['hibor_overnight'], 20, 2)

# Remove NaN values (first 60 days)
df = df.dropna().reset_index(drop=True)

print(f'After technical indicators: {len(df)} records')

# Latest values
latest = df.iloc[-1]
print(f'\n' + '=' * 80)
print('LATEST HIBOR TECHNICAL ANALYSIS (2025-10-23)')
print('=' * 80)
print(f'HIBOR Overnight: {latest["hibor_overnight"]:.4f}%')
print(f'Z-Score (20):    {latest["hibor_zscore_20"]:.4f}')
print(f'Z-Score (60):    {latest["hibor_zscore_60"]:.4f}')
print(f'SMA 20:          {latest["hibor_sma_20"]:.4f}%')
print(f'SMA 50:          {latest["hibor_sma_50"]:.4f}%')
print(f'EMA 20:          {latest["hibor_ema_20"]:.4f}%')
print(f'EMA 50:          {latest["hibor_ema_50"]:.4f}%')
print(f'RSI (14):        {latest["hibor_rsi_14"]:.4f}')
print(f'MACD:            {latest["hibor_macd"]:.6f}')
print(f'MACD Signal:     {latest["hibor_macd_signal"]:.6f}')
print(f'MACD Histogram:  {latest["hibor_macd_hist"]:.6f}')
print(f'BB Upper:        {latest["hibor_bb_upper"]:.4f}%')
print(f'BB Middle:       {latest["hibor_bb_middle"]:.4f}%')
print(f'BB Lower:        {latest["hibor_bb_lower"]:.4f}%')

# Trading Strategies
print(f'\n' + '=' * 80)
print('TECHNICAL ANALYSIS TRADING STRATEGIES')
print('=' * 80)

def strategy_zscore_threshold(df, z_threshold=2.0):
    """Z-Score Strategy: Buy when Z-Score < -threshold, Sell when Z-Score > threshold"""
    signals = []
    for i in range(len(df)):
        zscore = df.iloc[i]['hibor_zscore_20']
        if pd.isna(zscore):
            continue
        if zscore < -z_threshold:
            signals.append('BUY')
        elif zscore > z_threshold:
            signals.append('SELL')
        else:
            signals.append('HOLD')
    return signals

def strategy_rsi_oversold_overbought(df, rsi_oversold=30, rsi_overbought=70):
    """RSI Strategy: Buy when RSI < oversold, Sell when RSI > overbought"""
    signals = []
    for i in range(len(df)):
        rsi = df.iloc[i]['hibor_rsi_14']
        if pd.isna(rsi):
            continue
        if rsi < rsi_oversold:
            signals.append('BUY')
        elif rsi > rsi_overbought:
            signals.append('SELL')
        else:
            signals.append('HOLD')
    return signals

def strategy_ma_crossover(df, fast_window=20, slow_window=50):
    """Moving Average Crossover: Buy when fast MA > slow MA, Sell when fast MA < slow MA"""
    signals = []
    for i in range(len(df)):
        fast_ma = df.iloc[i]['hibor_ema_20'] if 'ema' in str(fast_window) else df.iloc[i]['hibor_sma_20']
        slow_ma = df.iloc[i]['hibor_ema_50'] if 'ema' in str(slow_window) else df.iloc[i]['hibor_sma_50']
        if pd.isna(fast_ma) or pd.isna(slow_ma):
            continue
        if fast_ma > slow_ma:
            signals.append('BUY')
        elif fast_ma < slow_ma:
            signals.append('SELL')
        else:
            signals.append('HOLD')
    return signals

def strategy_macd(df):
    """MACD Strategy: Buy when MACD > Signal, Sell when MACD < Signal"""
    signals = []
    for i in range(len(df)):
        macd = df.iloc[i]['hibor_macd']
        signal = df.iloc[i]['hibor_macd_signal']
        if pd.isna(macd) or pd.isna(signal):
            continue
        if macd > signal:
            signals.append('BUY')
        elif macd < signal:
            signals.append('SELL')
        else:
            signals.append('HOLD')
    return signals

def strategy_bollinger_bands(df):
    """Bollinger Bands Strategy: Buy when price < lower band, Sell when price > upper band"""
    signals = []
    for i in range(len(df)):
        price = df.iloc[i]['hibor_overnight']
        upper = df.iloc[i]['hibor_bb_upper']
        lower = df.iloc[i]['hibor_bb_lower']
        if pd.isna(price) or pd.isna(upper) or pd.isna(lower):
            continue
        if price < lower:
            signals.append('BUY')
        elif price > upper:
            signals.append('SELL')
        else:
            signals.append('HOLD')
    return signals

# Generate signals for each strategy
print(f'\nGenerating trading signals...')
df['signal_zscore'] = strategy_zscore_threshold(df, z_threshold=1.5)
df['signal_rsi'] = strategy_rsi_oversold_overbought(df, rsi_oversold=25, rsi_overbought=75)
df['signal_macrossover'] = strategy_ma_crossover(df)
df['signal_macd'] = strategy_macd(df)
df['signal_bb'] = strategy_bollinger_bands(df)

# Simulate Trading for Each Strategy
print(f'\n' + '=' * 80)
print('SIMULATING TRADING STRATEGIES')
print('=' * 80)

def simulate_trading(df, signal_col, initial_capital=100000):
    """Simulate trading based on signals"""
    capital = initial_capital
    position = 0
    trades = []
    equity_curve = [capital]

    for i in range(len(df)):
        signal = df.iloc[i][signal_col]
        hibor = df.iloc[i]['hibor_overnight']
        date = df.iloc[i]['date']

        if signal == 'BUY' and position == 0:
            position = capital / hibor
            capital = 0
            trades.append({
                'date': date, 'action': 'BUY', 'hibor': hibor, 'price': hibor
            })

        elif signal == 'SELL' and position > 0:
            capital = position * hibor
            position = 0
            trades.append({
                'date': date, 'action': 'SELL', 'hibor': hibor, 'price': hibor
            })

        current_value = capital if position == 0 else position * hibor
        equity_curve.append(current_value)

    # Final value
    if position > 0:
        final_value = position * df.iloc[-1]['hibor_overnight']
    else:
        final_value = capital

    # Calculate metrics
    total_return = (final_value - initial_capital) / initial_capital * 100
    years = (df.iloc[-1]['date'] - df.iloc[0]['date']).days / 365.25
    annual_return = (final_value / initial_capital) ** (1/years) - 1 if years > 0 else 0

    # Calculate Sharpe ratio
    returns = np.diff(equity_curve) / equity_curve[:-1]
    sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0

    # Calculate max drawdown
    peak = np.maximum.accumulate(equity_curve)
    drawdown = (equity_curve - peak) / peak
    max_drawdown = np.min(drawdown) * 100

    return {
        'strategy': signal_col,
        'total_return_pct': total_return,
        'annual_return_pct': annual_return * 100,
        'sharpe_ratio': sharpe,
        'max_drawdown_pct': max_drawdown,
        'total_trades': len(trades),
        'final_value': final_value,
        'trades': trades
    }

# Test all strategies
strategies = {
    'Z-Score (Threshold ±1.5)': 'signal_zscore',
    'RSI (25/75)': 'signal_rsi',
    'MA Crossover (20/50)': 'signal_macrossover',
    'MACD': 'signal_macd',
    'Bollinger Bands': 'signal_bb'
}

results = []
for strategy_name, signal_col in strategies.items():
    print(f'\n{strategy_name}:')
    try:
        result = simulate_trading(df, signal_col)
        print(f'  Total Return: {result["total_return_pct"]:.2f}%')
        print(f'  Annual Return: {result["annual_return_pct"]:.2f}%')
        print(f'  Sharpe Ratio: {result["sharpe_ratio"]:.4f}')
        print(f'  Max Drawdown: {result["max_drawdown_pct"]:.2f}%')
        print(f'  Total Trades: {result["total_trades"]}')
        results.append(result)
    except Exception as e:
        print(f'  Error: {e}')

# Sort by Sharpe ratio
results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)

# Best strategy
if results:
    best = results[0]
    print(f'\n' + '=' * 80)
    print('BEST TECHNICAL ANALYSIS STRATEGY')
    print('=' * 80)
    print(f'Strategy: {best["strategy"]}')
    print(f'Total Return: {best["total_return_pct"]:.2f}%')
    print(f'Annual Return: {best["annual_return_pct"]:.2f}%')
    print(f'Sharpe Ratio: {best["sharpe_ratio"]:.4f}')
    print(f'Max Drawdown: {best["max_drawdown_pct"]:.2f}%')
    print(f'Total Trades: {best["total_trades"]}')
    print(f'Final Value: ${best["final_value"]:,.2f}')

    print(f'\nTrade History (First 5):')
    for trade in best['trades'][:5]:
        print(f'  {trade["date"].date()}: {trade["action"]} at {trade["hibor"]:.4f}%')

# Save results
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = f'hibor_technical_analysis_backtest_{timestamp}.json'

# Convert to JSON-serializable
for result in results:
    result['trades'] = len(result['trades'])

with open(output_file, 'w') as f:
    json.dump({
        'best_strategy': best if results else None,
        'all_results': results,
        'data_info': {
            'total_records': len(df),
            'date_range': f'{df["date"].min().date()} to {df["date"].max().date()}',
            'data_source': 'Real HIBOR Data with Technical Analysis'
        }
    }, f, indent=2, default=str)

print(f'\n' + '=' * 80)
print('TECHNICAL ANALYSIS COMPLETE')
print('=' * 80)
print(f'Results saved to: {output_file}')
print(f'Best strategy: {best["strategy"] if results else "N/A"}')
print('=' * 80)
