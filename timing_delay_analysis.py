#!/usr/bin/env python3
"""Warrant Strategy: Impact of Data Release Delay"""

import pandas as pd
import numpy as np

print("\n" + "="*80)
print("DATA TIMING IMPACT: Signal on Day 20 (after close)")
print("                    Execution on Day 21 (at open)")
print("="*80)

# Load data
daily = pd.read_csv(r'C:\Users\Penguin8n\CODEX--\CODEX--\warrant_sentiment_daily.csv')
daily['Date'] = pd.to_datetime(daily['Date'])
daily = daily.sort_values('Date').reset_index(drop=True)

print(f"\nLoaded {len(daily)} data points")

# Create signals
daily['Signal'] = 0
daily.loc[daily['Bull_Ratio'] > 0.65, 'Signal'] = -1  # SHORT
daily.loc[daily['Bull_Ratio'] < 0.35, 'Signal'] = 1   # LONG

# Get next day return
daily['Return_Next_Day'] = daily['Daily_Return'].shift(-1)
daily['Return_Today'] = daily['Daily_Return']

# Filter signals with next day data
signals = daily[daily['Signal'] != 0].copy()
valid = signals.dropna(subset=['Return_Next_Day'])

print(f"Total extreme warrant signals: {len(signals)}")
print(f"With next-day data available: {len(valid)}")

# ============= SCENARIO ANALYSIS =============
print("\n" + "="*80)
print("SCENARIO A: If we could trade immediately (IMPOSSIBLE)")
print("="*80)

result_same_day = valid.copy()
result_same_day['PnL'] = result_same_day['Signal'] * result_same_day['Return_Today']

wr_same = (result_same_day['PnL'] > 0).sum() / len(result_same_day)
avg_same = result_same_day['PnL'].mean()

print(f"\nTrade TODAY (20) at close:")
print(f"  Win rate: {wr_same:.1%} ({(result_same_day['PnL'] > 0).sum()}/{len(result_same_day)})")
print(f"  Avg return: {avg_same:+.2%}")
print(f"  Total return: {result_same_day['PnL'].sum():+.2%}")
print(f"  Status: IMPOSSIBLE - Market closed!")

# ============= REALISTIC SCENARIO =============
print("\n" + "="*80)
print("SCENARIO B: With overnight delay (ACTUAL REALITY)")
print("="*80)

result_next_day = valid.copy()
result_next_day['PnL'] = result_next_day['Signal'] * result_next_day['Return_Next_Day']
result_next_day['Gap'] = result_next_day['Return_Next_Day'] - result_next_day['Return_Today']

wr_next = (result_next_day['PnL'] > 0).sum() / len(result_next_day)
avg_next = result_next_day['PnL'].mean()
avg_gap = result_next_day['Gap'].mean()

print(f"\nTrade TOMORROW (21) at open:")
print(f"  Win rate: {wr_next:.1%} ({(result_next_day['PnL'] > 0).sum()}/{len(result_next_day)})")
print(f"  Avg return: {avg_next:+.2%}")
print(f"  Total return: {result_next_day['PnL'].sum():+.2%}")
print(f"  Status: REALISTIC - This is what happens!")

# ============= IMPACT ANALYSIS =============
print("\n" + "="*80)
print("TIMING IMPACT ANALYSIS")
print("="*80)

print(f"\nOvernight Gap Impact:")
print(f"  Average gap: {avg_gap:+.2%}")
print(f"  Gap Std Dev: {result_next_day['Gap'].std():.2%}")
print(f"  Worst case gap: {result_next_day['Gap'].min():+.2%}")
print(f"  Best case gap: {result_next_day['Gap'].max():+.2%}")

favorable_gaps = (result_next_day['Gap'] > 0).sum()
adverse_gaps = (result_next_day['Gap'] < 0).sum()

print(f"\n  Gaps favor us: {favorable_gaps} times ({favorable_gaps/len(result_next_day):.1%})")
print(f"  Gaps hurt us: {adverse_gaps} times ({adverse_gaps/len(result_next_day):.1%})")

# ============= PERFORMANCE COMPARISON =============
print("\n" + "="*80)
print("PERFORMANCE COMPARISON")
print("="*80)

print(f"\nIf we could trade TODAY (same-day):")
print(f"  Win rate: {wr_same:.1%}")
print(f"  Avg PnL: {avg_same:+.3%}")
print(f"  [Hypothetical - impossible to execute]")

print(f"\nWhat we ACTUALLY get (overnight delay):")
print(f"  Win rate: {wr_next:.1%}")
print(f"  Avg PnL: {avg_next:+.3%}")
print(f"  Impact from overnight gap: {avg_gap:+.3%}")
print(f"  [Realistic execution scenario]")

print(f"\nDifference due to data delay:")
diff_wr = wr_same - wr_next
diff_pnl = avg_same - avg_next
print(f"  Win rate change: {diff_wr:+.1%} points")
print(f"  Avg PnL change: {diff_pnl:+.3%}")

# ============= TRADE DETAILS =============
print("\n" + "="*80)
print("TRADE-BY-TRADE BREAKDOWN")
print("="*80)

print(f"\n{'Date':<12} {'Signal':<6} {'Today%':<7} {'Tomorrow%':<9} {'Gap%':<6} {'Actual PnL':<10}")
print("-" * 60)

for _, row in result_next_day.iterrows():
    date_str = row['Date'].strftime('%Y-%m-%d')
    sig = 'SHORT' if row['Signal'] == -1 else 'LONG'
    today = row['Return_Today'] * 100
    tomorrow = row['Return_Next_Day'] * 100
    gap = row['Gap'] * 100
    pnl = row['PnL'] * 100

    marker = ""
    if pnl > 0:
        marker = " WIN"
    else:
        marker = " LOSS"

    print(f"{date_str:<12} {sig:<6} {today:+6.2f}% {tomorrow:+8.2f}% {gap:+5.2f}% {pnl:+8.2f}%{marker}")

# ============= KEY INSIGHT =============
print("\n" + "="*80)
print("KEY INSIGHT")
print("="*80)

improvement = avg_same - avg_next

print(f"\nWarrant Signal Data Delay Impact:")
print(f"  Signal Generated: Day 20 (after market close)")
print(f"  Execution: Day 21 (at market open)")
print(f"  Data Gap: 12-16 hours of overnight risk")
print(f"  ")
print(f"  Impact on our strategy:")
print(f"    Expected return (with immediate execution): {avg_same:+.2%}")
print(f"    Actual return (overnight delay): {avg_next:+.2%}")
print(f"    Loss due to overnight: {improvement:+.2%}")
print(f"    ")

if improvement > 0.001:
    print(f"  Verdict: OVERNIGHT HURTS US")
    print(f"    -> Overnight gaps move market AGAINST our positions")
    print(f"    -> Need to address this timing issue!")
    print(f"    ")
    print(f"  Solutions:")
    print(f"    1. Use intraday warrant data (14:30 close) if available")
    print(f"    2. Get data early and trade same day")
    print(f"    3. Add gap filters (only trade favorable gaps)")
    print(f"    4. Combine with other signals for confirmation")
elif improvement < -0.001:
    print(f"  Verdict: OVERNIGHT HELPS US")
    print(f"    -> Overnight gaps move market FOR our positions")
    print(f"    -> Overnight delay is actually beneficial!")
    print(f"    -> Proceed with overnight strategy")
else:
    print(f"  Verdict: OVERNIGHT NEUTRAL")
    print(f"    -> Overnight gaps roughly neutral")
    print(f"    -> Data delay has minimal impact")

# ============= RECOMMENDATIONS =============
print("\n" + "="*80)
print("RECOMMENDATIONS")
print("="*80)

print(f"\n[1] IMMEDIATE ACTION")
print(f"    Monitor next 5-10 signals for actual overnight gaps")
print(f"    Track real execution prices vs theoretical close prices")
print(f"    Document any slippage patterns")

print(f"\n[2] DATA OPTIMIZATION")
print(f"    Try to access warrant data earlier (14:30 instead of 17:00)")
print(f"    Check with broker for intraday warrant turnover data")
print(f"    Consider calculating sentiment from end-of-day trades")

print(f"\n[3] TRADING OPTIMIZATION")
print(f"    Add gap filter: Only trade if gap is favorable")
print(f"    Adjust position size for gap risk")
print(f"    Consider limit orders instead of market orders at open")

print(f"\n[4] STRATEGY REFINEMENT")
print(f"    Combine warrant signals with market breadth for confirmation")
print(f"    Use today's market breadth (available intraday) as filter")
print(f"    Only execute if both signals align")

# ============= EXPORT =============
export_data = result_next_day[[
    'Date', 'Signal', 'Bull_Ratio', 'Return_Today', 'Return_Next_Day',
    'Gap', 'PnL'
]].copy()

export_data.columns = ['Date', 'Signal', 'Warrant_Ratio', 'Same_Day_Return',
                       'Next_Day_Return', 'Overnight_Gap', 'Actual_PnL']

export_data.to_csv(
    r'C:\Users\Penguin8n\CODEX--\CODEX--\timing_delay_analysis.csv',
    index=False
)

print(f"\n" + "="*80)
print("Saved: timing_delay_analysis.csv")
print("="*80 + "\n")
