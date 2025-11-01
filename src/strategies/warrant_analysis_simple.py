#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# ============== LOAD DATA ==============
print("\n[LOAD] Market data...")
market_df = pd.read_csv(r'C:\Users\Penguin8n\CODEX--\CODEX--\hkex爬蟲\data\hkex_all_market_data.csv')
market_df['Date'] = pd.to_datetime(market_df['Date'])
market_df = market_df.sort_values('Date').reset_index(drop=True)
print(f"  Loaded {len(market_df)} days")

# ============== LOAD WARRANT DATA ==============
print("\n[LOAD] Warrant data...")
top_stocks_dir = Path(r'C:\Users\Penguin8n\CODEX--\CODEX--\hkex爬蟲\data\top_stocks')
warrant_files = sorted(top_stocks_dir.glob('top_stocks_by_shares_*.csv'))
print(f"  Found {len(warrant_files)} warrant files")

warrant_daily = []

for fpath in warrant_files:
    try:
        df = pd.read_csv(fpath)
        date_str = fpath.stem.split('_')[-1]
        date = pd.to_datetime(date_str)

        # Position 5 (0-indexed) = 6th character for Bull/Bear detection
        df['Type'] = df['Name_CHI'].str[5]

        bull = df[df['Type'] == '牛']['Turnover_HKD'].sum()
        bear = df[df['Type'] == '熊']['Turnover_HKD'].sum()
        total = bull + bear

        if total > 0:
            bull_ratio = bull / total
            bb_ratio = bull / bear if bear > 0 else np.inf
        else:
            bull_ratio = 0.5
            bb_ratio = 1.0

        warrant_daily.append({
            'Date': date,
            'Bull_Turnover': bull,
            'Bear_Turnover': bear,
            'Total_Turnover': total,
            'Bull_Ratio': bull_ratio,
            'Bull_Bear_Ratio': bb_ratio,
            'Bull_Count': len(df[df['Type'] == '牛']),
            'Bear_Count': len(df[df['Type'] == '熊']),
        })
    except Exception as e:
        print(f"  Error in {fpath.name}: {e}")

warrant_df = pd.DataFrame(warrant_daily)
warrant_df = warrant_df.sort_values('Date').reset_index(drop=True)
print(f"  Processed {len(warrant_df)} days")

# ============== MERGE DATA ==============
print("\n[MERGE] Combining datasets...")
merged = market_df.merge(warrant_df, on='Date', how='inner')
print(f"  Merged dataset: {len(merged)} rows")

# ============== ANALYSIS ==============
print("\n" + "="*70)
print("WARRANT SENTIMENT ANALYSIS - CONTRARIAN INDICATOR")
print("="*70)

# Statistics
print("\n[STATS] Bull Ratio Distribution:")
print(f"  Mean: {merged['Bull_Ratio'].mean():.2%}")
print(f"  Std:  {merged['Bull_Ratio'].std():.2%}")
print(f"  Min:  {merged['Bull_Ratio'].min():.2%}")
print(f"  Max:  {merged['Bull_Ratio'].max():.2%}")

# Identify extremes
extreme_bull = merged[merged['Bull_Ratio'] > 0.65]
extreme_bear = merged[merged['Bull_Ratio'] < 0.35]

print(f"\n[EXTREMES] Warrant Sentiment:")
print(f"  Extreme BULL (>0.65): {len(extreme_bull)} days")
if len(extreme_bull) > 0:
    print(f"    Avg Return: {extreme_bull['Daily_Return'].mean():+.2%}")
    print(f"    Positive days: {(extreme_bull['Daily_Return'] > 0).sum()}/{len(extreme_bull)}")

print(f"\n  Extreme BEAR (<0.35): {len(extreme_bear)} days")
if len(extreme_bear) > 0:
    print(f"    Avg Return: {extreme_bear['Daily_Return'].mean():+.2%}")
    print(f"    Positive days: {(extreme_bear['Daily_Return'] > 0).sum()}/{len(extreme_bear)}")

# Correlation - Same day
print(f"\n[CORRELATION] Same-Day Analysis:")
r_same = merged['Bull_Ratio'].corr(merged['Daily_Return'])
print(f"  Bull_Ratio vs Daily_Return: {r_same:+.4f}")

# Correlation - 1-day lead (contrarian test)
if len(merged) > 1:
    merged['Bull_Ratio_Lag'] = merged['Bull_Ratio'].shift(1)
    merged['Return_Lead'] = merged['Daily_Return'].shift(-1)
    valid = merged[['Bull_Ratio_Lag', 'Return_Lead']].dropna()

    if len(valid) > 2:
        r_lead = valid['Bull_Ratio_Lag'].corr(valid['Return_Lead'])
        print(f"\n[LEAD] Next-Day Analysis (Yesterday's Warrant → Today's Return):")
        print(f"  Bull_Ratio(t-1) vs Return(t): {r_lead:+.4f}")

        # Interpretation
        if r_lead < -0.3:
            print(f"  CONTRARIAN SIGNAL DETECTED: Strong negative correlation")
            print(f"  → High bull warrant yesterday → Lower returns today")
        elif r_lead > 0.3:
            print(f"  TREND-FOLLOWING: Positive correlation")
        else:
            print(f"  WEAK SIGNAL: Correlation too close to zero")

# Contrarian strategy backtest
print(f"\n[STRATEGY] Contrarian Backtest:")
merged['Signal'] = 0
merged.loc[merged['Bull_Ratio'] > 0.65, 'Signal'] = -1  # Short (retail too bullish)
merged.loc[merged['Bull_Ratio'] < 0.35, 'Signal'] = 1   # Long (retail too bearish)

trades = merged[merged['Signal'] != 0].copy()
if len(trades) > 0:
    trades['Return_Next'] = trades['Daily_Return'].shift(-1)
    trades['PnL'] = trades['Signal'] * trades['Return_Next']

    wins = (trades['PnL'] > 0).sum()
    total = len(trades)
    wr = wins / total if total > 0 else 0

    print(f"  Trade Count: {total}")
    print(f"  Win Rate: {wr:.1%} ({wins}/{total})")
    print(f"  Avg Return: {trades['PnL'].mean():+.2%}")
    print(f"  Total Return: {trades['PnL'].sum():+.2%}")

# Current reading
print(f"\n[CURRENT] Latest Warrant Sentiment:")
latest = merged.iloc[-1]
print(f"  Date: {latest['Date'].date()}")
print(f"  Bull_Ratio: {latest['Bull_Ratio']:.1%}")
print(f"  Bull/Bear Ratio: {latest['Bull_Bear_Ratio']:.2f}x")
print(f"  Bull Turnover: {latest['Bull_Turnover']/1e9:.1f}B HKD")
print(f"  Bear Turnover: {latest['Bear_Turnover']/1e9:.1f}B HKD")

if latest['Bull_Ratio'] > 0.65:
    print(f"  >>> SIGNAL: Retail EXTREMELY BULLISH → Contrarian: CAUTION/SHORT")
elif latest['Bull_Ratio'] < 0.35:
    print(f"  >>> SIGNAL: Retail EXTREMELY BEARISH → Contrarian: BUY opportunity")
else:
    print(f"  >>> SIGNAL: Neutral")

# Export
print(f"\n[EXPORT] Saving results...")
merged[['Date', 'Afternoon_Close', 'Daily_Return', 'Market_Breadth',
         'Bull_Ratio', 'Bull_Bear_Ratio', 'Bull_Turnover', 'Bear_Turnover']].to_csv(
    r'C:\Users\Penguin8n\CODEX--\CODEX--\warrant_sentiment_merged.csv',
    index=False
)

# Daily warrant log
warrant_log = merged[[
    'Date', 'Bull_Ratio', 'Bull_Bear_Ratio', 'Bull_Turnover', 'Bear_Turnover',
    'Daily_Return', 'Market_Breadth'
]].copy()

warrant_log['Sentiment'] = warrant_log['Bull_Ratio'].apply(
    lambda x: 'EXTREME BULL' if x > 0.65 else ('EXTREME BEAR' if x < 0.35 else 'NEUTRAL')
)

print(f"  warrant_sentiment_merged.csv")
print(f"  warrant_sentiment_daily.csv")

warrant_log.to_csv(
    r'C:\Users\Penguin8n\CODEX--\CODEX--\warrant_sentiment_daily.csv',
    index=False
)

print("\n[DONE] Analysis complete!")
print("="*70)
