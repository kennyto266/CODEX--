#!/usr/bin/env python3
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

print("\n" + "="*70)
print("HKEX Bull/Bear Warrant Sentiment - Contrarian Indicator Analysis")
print("="*70)

# ============== LOAD MARKET DATA ==============
print("\n[1] Loading market data...")
mkt = pd.read_csv(r'C:\Users\Penguin8n\CODEX--\CODEX--\hkex爬蟲\data\hkex_all_market_data.csv')
mkt['Date'] = pd.to_datetime(mkt['Date'])
mkt = mkt.sort_values('Date').reset_index(drop=True)

# Calculate daily return
mkt['Daily_Return'] = mkt['Afternoon_Close'].pct_change()

print(f"    Loaded {len(mkt)} market days")
print(f"    Date range: {mkt['Date'].min().date()} to {mkt['Date'].max().date()}")

# ============== LOAD WARRANT DATA ==============
print("\n[2] Loading warrant data...")
top_dir = Path(r'C:\Users\Penguin8n\CODEX--\CODEX--\hkex爬蟲\data\top_stocks')
warrant_files = sorted([f for f in top_dir.glob('*.csv') if '2025-' in f.name])

print(f"    Found {len(warrant_files)} warrant files")

warrant_data = []

for fpath in warrant_files:
    try:
        date_str = fpath.stem.split('_')[-1]
        date = pd.to_datetime(date_str)

        df = pd.read_csv(fpath)

        # Position 1 (0-indexed) = 2nd character in Product code
        df['Type'] = df['Product'].str[1]

        bull = df[df['Type'] == 'C']['Turnover_HKD'].sum()  # RC = Bull
        bear = df[df['Type'] == 'P']['Turnover_HKD'].sum()  # RP = Bear
        total = bull + bear

        if total > 0:
            bull_ratio = bull / total
            bb_ratio = bull / bear if bear > 0 else np.inf
        else:
            bull_ratio = 0.5
            bb_ratio = 1.0

        warrant_data.append({
            'Date': date,
            'Bull_Turnover_HKD': bull,
            'Bear_Turnover_HKD': bear,
            'Total_Warrant_Turnover': total,
            'Bull_Ratio': bull_ratio,
            'Bull_Bear_Ratio': bb_ratio,
            'Bull_Count': len(df[df['Type'] == 'C']),
            'Bear_Count': len(df[df['Type'] == 'P']),
        })

    except Exception as e:
        print(f"    Error in {fpath.name}: {str(e)[:50]}")

warrant_df = pd.DataFrame(warrant_data)
warrant_df = warrant_df.sort_values('Date').reset_index(drop=True)

print(f"    Processed {len(warrant_df)} warrant days")
print(f"    Date range: {warrant_df['Date'].min().date()} to {warrant_df['Date'].max().date()}")

# ============== MERGE DATA ==============
print("\n[3] Merging datasets...")
merged = mkt.merge(warrant_df, on='Date', how='inner')
merged = merged.sort_values('Date').reset_index(drop=True)

print(f"    Merged dataset: {len(merged)} rows")

# ============== STATISTICS ==============
print("\n" + "="*70)
print("WARRANT SENTIMENT STATISTICS")
print("="*70)

print(f"\n[STATS] Bull Warrant Ratio Distribution:")
print(f"    Mean:  {merged['Bull_Ratio'].mean():.2%}")
print(f"    Std:   {merged['Bull_Ratio'].std():.2%}")
print(f"    Min:   {merged['Bull_Ratio'].min():.2%}")
print(f"    Max:   {merged['Bull_Ratio'].max():.2%}")

print(f"\n[STATS] Bull/Bear Ratio Distribution:")
print(f"    Mean:  {merged['Bull_Bear_Ratio'].mean():.3f}x")
print(f"    Std:   {merged['Bull_Bear_Ratio'].std():.3f}x")
print(f"    Min:   {merged['Bull_Bear_Ratio'].min():.3f}x")
print(f"    Max:   {merged['Bull_Bear_Ratio'].max():.3f}x")

# ============== EXTREME READINGS ==============
print("\n" + "="*70)
print("EXTREME WARRANT SENTIMENT - CONTRARIAN SIGNAL")
print("="*70)

extreme_bull = merged[merged['Bull_Ratio'] > 0.65]
extreme_bear = merged[merged['Bull_Ratio'] < 0.35]

print(f"\n[EXTREME BULL] Retail EXTREMELY BULLISH (Bull_Ratio > 0.65):")
print(f"    Occurrences: {len(extreme_bull)} days")
if len(extreme_bull) > 0:
    print(f"    Dates: {extreme_bull['Date'].dt.date.tolist()}")
    print(f"    Avg Return (same day): {extreme_bull['Daily_Return'].mean():+.2%}")
    wins = (extreme_bull['Daily_Return'] > 0).sum()
    print(f"    Win rate: {wins}/{len(extreme_bull)} ({wins/len(extreme_bull):.1%})")

print(f"\n[EXTREME BEAR] Retail EXTREMELY BEARISH (Bull_Ratio < 0.35):")
print(f"    Occurrences: {len(extreme_bear)} days")
if len(extreme_bear) > 0:
    print(f"    Dates: {extreme_bear['Date'].dt.date.tolist()}")
    print(f"    Avg Return (same day): {extreme_bear['Daily_Return'].mean():+.2%}")
    wins = (extreme_bear['Daily_Return'] > 0).sum()
    print(f"    Win rate: {wins}/{len(extreme_bear)} ({wins/len(extreme_bear):.1%})")

# ============== CORRELATION ANALYSIS ==============
print("\n" + "="*70)
print("CORRELATION ANALYSIS - Warrant vs Market Return")
print("="*70)

# Same day correlation
r_bull = merged['Bull_Ratio'].corr(merged['Daily_Return'])
r_bb = merged['Bull_Bear_Ratio'].corr(merged['Daily_Return'])

print(f"\n[SAME-DAY] Correlation:")
print(f"    Bull_Ratio vs Daily_Return: {r_bull:+.4f}")
print(f"    Bull_Bear_Ratio vs Daily_Return: {r_bb:+.4f}")
print(f"    Interpretation: {'Contrarian' if r_bull < -0.2 else ('Trend-following' if r_bull > 0.2 else 'Weak')}")

# 1-day lead (contrarian opportunity)
if len(merged) > 1:
    merged['Bull_Ratio_t1'] = merged['Bull_Ratio'].shift(1)
    merged['Return_t1'] = merged['Daily_Return'].shift(-1)

    valid = merged[['Bull_Ratio_t1', 'Return_t1']].dropna()
    if len(valid) > 2:
        r_lead = valid['Bull_Ratio_t1'].corr(valid['Return_t1'])

        print(f"\n[NEXT-DAY] Warrant Lead Analysis:")
        print(f"    Yesterday Bull_Ratio → Today Daily_Return: {r_lead:+.4f}")

        if abs(r_lead) > 0.3:
            direction = "NEGATIVE (Contrarian)" if r_lead < -0.3 else "POSITIVE (Trend-follow)"
            print(f"    Signal Strength: {direction}")
            print(f"    >>> High bull yesterday → {'Lower' if r_lead < 0 else 'Higher'} returns today")
        else:
            print(f"    Signal Strength: WEAK (|r| < 0.3)")

# ============== CONTRARIAN STRATEGY BACKTEST ==============
print("\n" + "="*70)
print("CONTRARIAN TRADING STRATEGY BACKTEST")
print("="*70)

merged['Signal'] = 0
merged.loc[merged['Bull_Ratio'] > 0.65, 'Signal'] = -1  # Retail too bullish → We short
merged.loc[merged['Bull_Ratio'] < 0.35, 'Signal'] = 1   # Retail too bearish → We long

# Get next day return
merged['Return_Next'] = merged['Daily_Return'].shift(-1)

trades = merged[merged['Signal'] != 0].copy()
trades['PnL'] = trades['Signal'] * trades['Return_Next']

if len(trades) > 0:
    wins = (trades['PnL'] > 0).sum()
    total = len(trades)
    wr = wins / total
    avg_return = trades['PnL'].mean()
    total_return = trades['PnL'].sum()

    print(f"\n[BACKTEST] Contrarian Strategy Results:")
    print(f"    Total Signals: {total}")
    print(f"    Win Rate: {wr:.1%} ({wins}/{total})")
    print(f"    Avg Return per Trade: {avg_return:+.2%}")
    print(f"    Total Return: {total_return:+.2%}")
    print(f"    Sharpe (annualized): {avg_return / trades['PnL'].std() * np.sqrt(252) if trades['PnL'].std() > 0 else 0:.2f}")

# ============== CURRENT SENTIMENT ==============
print("\n" + "="*70)
print("CURRENT WARRANT SENTIMENT")
print("="*70)

latest = merged.iloc[-1]
print(f"\nDate: {latest['Date'].date()}")
print(f"    Bull_Ratio: {latest['Bull_Ratio']:.1%}")
print(f"    Bull Turnover: {latest['Bull_Turnover_HKD']/1e9:.2f}B HKD")
print(f"    Bear Turnover: {latest['Bear_Turnover_HKD']/1e9:.2f}B HKD")
print(f"    Bull/Bear Ratio: {latest['Bull_Bear_Ratio']:.2f}x")

print(f"\n    Market Close: {latest['Afternoon_Close']:.2f}")
print(f"    Market Breadth: {latest.get('Market_Breadth', np.nan):+.2%}")

print(f"\n[SIGNAL]:")
if latest['Bull_Ratio'] > 0.65:
    print(f"    EXTREME BULL - Retail EXTREMELY BULLISH (>65%)")
    print(f"    Contrarian Action: CAUTION - Consider selling/shorting")
    print(f"    >>> Retail may be wrong - prepare for pullback")

elif latest['Bull_Ratio'] < 0.35:
    print(f"    EXTREME BEAR - Retail EXTREMELY BEARISH (<35%)")
    print(f"    Contrarian Action: BUY OPPORTUNITY - Consider going long")
    print(f"    >>> Retail fear may create bounce opportunity")

elif latest['Bull_Ratio'] > 0.55:
    print(f"    MODERATE BULL - Retail leaning bullish ({latest['Bull_Ratio']:.1%})")
    print(f"    Contrarian Action: WATCH - Light selling bias")

elif latest['Bull_Ratio'] < 0.45:
    print(f"    MODERATE BEAR - Retail leaning bearish ({latest['Bull_Ratio']:.1%})")
    print(f"    Contrarian Action: WATCH - Light buying bias")

else:
    print(f"    NEUTRAL - Balanced warrant sentiment ({latest['Bull_Ratio']:.1%})")

# ============== EXPORT ==============
print(f"\n" + "="*70)
print("EXPORTING DATA")
print("="*70)

# Merged data
export_cols = [
    'Date', 'Afternoon_Close', 'Daily_Return',
    'Bull_Ratio', 'Bull_Bear_Ratio', 'Bull_Turnover_HKD', 'Bear_Turnover_HKD',
    'Signal'
]

# Only include columns that exist
export_cols = [c for c in export_cols if c in merged.columns]
export_df = merged[export_cols].copy()
export_df.to_csv(
    r'C:\Users\Penguin8n\CODEX--\CODEX--\warrant_sentiment_merged.csv',
    index=False
)
print(f"    Saved: warrant_sentiment_merged.csv")

# Daily log
daily_cols = [
    'Date', 'Bull_Ratio', 'Bull_Bear_Ratio',
    'Bull_Turnover_HKD', 'Bear_Turnover_HKD',
    'Afternoon_Close', 'Daily_Return', 'Signal'
]
daily_cols = [c for c in daily_cols if c in merged.columns]
daily_log = merged[daily_cols].copy()

daily_log['Sentiment_Level'] = daily_log['Bull_Ratio'].apply(
    lambda x: 'EXTREME BULL' if x > 0.65 else (
        'EXTREME BEAR' if x < 0.35 else (
            'MOD BULL' if x > 0.55 else (
                'MOD BEAR' if x < 0.45 else 'NEUTRAL'
            )
        )
    )
)

daily_log.to_csv(
    r'C:\Users\Penguin8n\CODEX--\CODEX--\warrant_sentiment_daily.csv',
    index=False
)
print(f"    Saved: warrant_sentiment_daily.csv")

# Summary stats
summary = pd.DataFrame({
    'Metric': [
        'Bull_Ratio_Mean', 'Bull_Ratio_Std', 'Bull_Ratio_Min', 'Bull_Ratio_Max',
        'Extreme_Bull_Days', 'Extreme_Bear_Days',
        'Corr_Bull_vs_Return', 'Corr_Lead_Bull_vs_Return',
        'Contrarian_Win_Rate', 'Contrarian_Avg_Return'
    ],
    'Value': [
        merged['Bull_Ratio'].mean(),
        merged['Bull_Ratio'].std(),
        merged['Bull_Ratio'].min(),
        merged['Bull_Ratio'].max(),
        len(extreme_bull),
        len(extreme_bear),
        r_bull,
        r_lead if len(valid) > 2 else np.nan,
        wr if len(trades) > 0 else np.nan,
        avg_return if len(trades) > 0 else np.nan
    ]
})

summary.to_csv(
    r'C:\Users\Penguin8n\CODEX--\CODEX--\warrant_sentiment_summary.csv',
    index=False
)
print(f"    Saved: warrant_sentiment_summary.csv")

print(f"\n[DONE] Analysis complete!")
print("="*70 + "\n")
