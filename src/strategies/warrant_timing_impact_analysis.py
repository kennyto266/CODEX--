#!/usr/bin/env python3
"""
Impact of Data Delay on Warrant Contrarian Strategy
Analysis: Signal on Day 20 (after close) → Execution on Day 21 (open)
"""

import pandas as pd
import numpy as np

print("\n" + "="*80)
print("HKEX DATA TIMING IMPACT ANALYSIS")
print("="*80)

# Load data
print("\n[1] Loading warrant sentiment data...")
daily = pd.read_csv(r'C:\Users\Penguin8n\CODEX--\CODEX--\warrant_sentiment_daily.csv')
daily['Date'] = pd.to_datetime(daily['Date'])
daily = daily.sort_values('Date').reset_index(drop=True)

print(f"    Loaded {len(daily)} rows")

# ============= PROBLEM SETUP =============
print("\n[2] Understanding the timing problem:")
print("    |-- Day 20 15:00: Market closes")
print("    |-- Day 20 17:00: CSV data released (warrant sentiment calculated)")
print("    |-- Day 20-21: Overnight (potential news/gap risk)")
print("    |-- Day 21 09:30: Market opens")
print("    |-- Day 21 09:30-10:00: We execute trades")
print("    `-- Result: Day 21 full day return")

# ============= SCENARIO COMPARISON =============
print("\n" + "="*80)
print("SCENARIO COMPARISON")
print("="*80)

# Add next day return
daily['Return_Next_Day'] = daily['Daily_Return'].shift(-1)
daily['Signal_Day'] = daily['Date']
daily['Execution_Day'] = daily['Signal_Day'].shift(-1)

# ============= CASE 1: REAL-TIME (IMPOSSIBLE) =============
print("\n[3A] SCENARIO 1: Real-Time Signal (HYPOTHETICAL - Not Achievable)")
print("    |-- Signal: Day 20 close warrant sentiment known")
print("    |-- Execution: Day 20 close trade immediately")
print("    |-- Return: Day 20 return")
print("    `-- Status: IMPOSSIBLE (Market already closed)")

# ============= CASE 2: OVERNIGHT DELAY (REALISTIC) =============
print("\n[3B] SCENARIO 2: Overnight Delay (REALISTIC - ACTUAL SITUATION)")
print("    |-- Signal Day: Day 20 (warrant data released after close)")
print("    |-- Execution: Day 21 open")
print("    |-- Entry Price: Day 21 open (unknown until market opens)")
print("    |-- Return Captured: Day 21 full day return")
print("    |-- Gap Risk: Day 20 close -> Day 21 open")
print("    `-- Status: THIS IS WHAT ACTUALLY HAPPENS")

# Identify extreme warrant signals
daily['Signal'] = 0
daily.loc[daily['Bull_Ratio'] > 0.65, 'Signal'] = -1  # Short
daily.loc[daily['Bull_Ratio'] < 0.35, 'Signal'] = 1   # Long

# Get signals and check NEXT day return
signals = daily[daily['Signal'] != 0].copy()
signals['Execution_Return'] = signals['Return_Next_Day']  # This is what we'd get
signals['Missed_Return'] = signals['Daily_Return']  # This is what already happened

# ============= ANALYSIS =============
print("\n" + "="*80)
print("EXECUTION IMPACT ANALYSIS")
print("="*80)

print("\n[4] If we follow the strategy with data delay:")

valid_signals = signals.dropna(subset=['Execution_Return'])
print(f"    Valid signals with next-day data: {len(valid_signals)}")

if len(valid_signals) > 0:
    # Calculate outcomes
    trades = valid_signals.copy()
    trades['PnL'] = trades['Signal'] * trades['Execution_Return']

    wins = (trades['PnL'] > 0).sum()
    losses = (trades['PnL'] < 0).sum()

    print(f"\n    【Real Execution Results (21号 open trade)】")
    print(f"    Total Trades: {len(trades)}")
    print(f"    Wins: {wins}")
    print(f"    Losses: {losses}")
    print(f"    Win Rate: {wins/len(trades):.1%}")
    print(f"    Avg Return: {trades['PnL'].mean():+.2%}")
    print(f"    Total Return: {trades['PnL'].sum():+.2%}")

    print(f"\n    【What We'd Miss (Same day return)】")
    trades['Missed_PnL'] = trades['Signal'] * trades['Missed_Return']
    print(f"    Avg Return if traded same day: {trades['Missed_PnL'].mean():+.2%}")
    print(f"    Total Return if traded same day: {trades['Missed_PnL'].sum():+.2%}")

    print(f"\n    【The Gap (Overnight Impact)】")
    trades['Gap_Impact'] = trades['Missed_PnL'] - trades['PnL']
    avg_gap = trades['Gap_Impact'].mean()
    print(f"    Average overnight gap: {avg_gap:+.2%}")
    print(f"    → If positive: overnight helps us (price moves in our favor)")
    print(f"    → If negative: overnight hurts us (price moves against us)")

    # Detailed trade log
    print(f"\n[5] Trade-by-Trade Breakdown:")
    print(f"    Date        | Signal | Day_Ret | Next_Ret | Gap  | PnL")
    print(f"    ────────────┼────────┼─────────┼──────────┼──────┼──────")

    for _, row in trades.iterrows():
        date_str = row['Signal_Day'].strftime('%Y-%m-%d')
        sig_str = "SHORT" if row['Signal'] == -1 else "LONG"
        day_ret = row['Missed_Return'] * 100
        next_ret = row['Execution_Return'] * 100
        gap = (row['Execution_Return'] - row['Missed_Return']) * 100
        pnl = row['PnL'] * 100

        print(f"    {date_str} | {sig_str:>5} | {day_ret:+6.2f}% | {next_ret:+7.2f}% | {gap:+5.2f}% | {pnl:+5.2f}%")

# ============= GAP ANALYSIS =============
print(f"\n" + "="*80)
print("OVERNIGHT GAP RISK ANALYSIS")
print("="*80)

gap_analysis = trades.copy()
gap_analysis['Gap_Direction'] = gap_analysis['Gap_Impact'].apply(
    lambda x: 'POSITIVE' if x > 0.002 else ('NEGATIVE' if x < -0.002 else 'NEUTRAL')
)

print(f"\n[6] Gap Distribution:")
print(f"    Average Gap: {gap_analysis['Gap_Impact'].mean():+.2%}")
print(f"    Max Gap (favorable): {gap_analysis['Gap_Impact'].max():+.2%}")
print(f"    Min Gap (adverse): {gap_analysis['Gap_Impact'].min():+.2%}")
print(f"    Std Dev: {gap_analysis['Gap_Impact'].std():.2%}")

pos_gaps = (gap_analysis['Gap_Impact'] > 0).sum()
neg_gaps = (gap_analysis['Gap_Impact'] < 0).sum()

print(f"\n    Favorable gaps: {pos_gaps} ({pos_gaps/len(gap_analysis):.1%})")
print(f"    Adverse gaps: {neg_gaps} ({neg_gaps/len(gap_analysis):.1%})")

# ============= KEY METRICS =============
print(f"\n" + "="*80)
print("IMPACT SUMMARY")
print("="*80)

print(f"\n[7] Strategy Performance with Data Delay:")
print(f"    ")
print(f"    Win Rate:           {wins/len(trades):.1%}")
print(f"    Avg Trade:          {trades['PnL'].mean():+.2%}")
print(f"    Avg Overnight Gap:  {gap_analysis['Gap_Impact'].mean():+.2%}")
print(f"    ")
print(f"    If overnight gap was NOT there:")
print(f"    Avg Trade:          {trades['Missed_PnL'].mean():+.2%}")
print(f"    Difference:         {(trades['Missed_PnL'].mean() - trades['PnL'].mean()):+.2%}")
print(f"    → {('HELPS' if gap_analysis['Gap_Impact'].mean() > 0 else 'HURTS')} our strategy")

# ============= IMPLICATIONS =============
print(f"\n" + "="*80)
print("TRADING IMPLICATIONS")
print("="*80)

print(f"\n[8] Key Findings:")

if len(valid_signals) >= 5:
    if gap_analysis['Gap_Impact'].mean() > 0.001:
        print(f"    ✓ POSITIVE: Overnight gaps favor our strategy on average")
        print(f"      Action: Continue with overnight hold strategy")
    elif gap_analysis['Gap_Impact'].mean() < -0.001:
        print(f"    ✗ NEGATIVE: Overnight gaps work against our strategy")
        print(f"      Action: Consider alternatives (see below)")
    else:
        print(f"    ⊖ NEUTRAL: Overnight gaps roughly cancel out")
        print(f"      Action: Proceed as planned")

print(f"\n[9] Alternative Approaches to Overcome Data Delay:")

print(f"\n    【Option A】 Paper Trade First")
print(f"    ├─ Signal Day 20号 after close: Calculate warrant sentiment")
print(f"    ├─ Decision: Wait vs trade")
print(f"    ├─ Execution Day 21号: Execute on actual open")
print(f"    ├─ Benefit: Validate real execution prices")
print(f"    └─ Timeline: Paper trade for 1 month before live")

print(f"\n    【Option B】 Use Intraday Estimate (If available)")
print(f"    ├─ If can get 14:30 warrant data (before close)")
print(f"    ├─ Can estimate today's sentiment and trade today")
print(f"    ├─ Avoid overnight gap")
print(f"    └─ Data source: Check if broker provides intraday warrant data")

print(f"\n    【Option C】 Adjust Entry Points")
print(f"    ├─ 20号: Calculate signal but DON'T trade yet")
print(f"    ├─ 21号 09:30-10:00: Market opens, check for gap")
print(f"    ├─ If favorable gap: Enter trade")
print(f"    ├─ If adverse gap: Wait for reversal or skip signal")
print(f"    └─ Benefit: Adaptive entry based on actual opening")

print(f"\n    【Option D】 Combine with Market Breadth (RECOMMENDED)")
print(f"    ├─ Warrant signal: 收市后 known")
print(f"    ├─ Market breadth: 可能 有 intraday data")
print(f"    ├─ Strategy: Double-confirm with breadth on 21号 open")
print(f"    ├─ Entry: Only if both signals align")
print(f"    └─ Benefit: Filter false signals, reduce gap risk")

# ============= SLIPPAGE ESTIMATE =============
print(f"\n" + "="*80)
print("EXECUTION SLIPPAGE ESTIMATE")
print("="*80)

print(f"\n[10] Expected Slippage Factors:")

print(f"\n    【Opening Gap】")
print(f"    Average: {gap_analysis['Gap_Impact'].mean():+.2%}")
print(f"    1σ Range: {gap_analysis['Gap_Impact'].mean()-gap_analysis['Gap_Impact'].std():+.2%} to {gap_analysis['Gap_Impact'].mean()+gap_analysis['Gap_Impact'].std():+.2%}")

print(f"\n    【Bid-Ask Spread】")
print(f"    Typical HSI spread: 0.05-0.10 pts")
print(f"    % impact: ~0.0002-0.0004%")

print(f"\n    【Market Impact】")
print(f"    For small 40-50 share position: ~0.01-0.05%")

print(f"\n    【Total Expected Slippage】")
total_slippage = abs(gap_analysis['Gap_Impact'].mean()) + 0.0003 + 0.0003
print(f"    Gap + spread + impact ≈ {total_slippage:+.2%}")
print(f"    Action: Add {total_slippage:.2%} buffer to profit targets")

# ============= EXPORT DETAILED ANALYSIS =============
analysis_df = trades[[
    'Signal_Day', 'Execution_Day', 'Signal', 'Bull_Ratio',
    'Missed_Return', 'Execution_Return', 'Gap_Impact',
    'Missed_PnL', 'PnL'
]].copy()

analysis_df.columns = [
    'Signal_Date', 'Execution_Date', 'Signal_Type', 'Warrant_Ratio',
    'Same_Day_Return', 'Next_Day_Return', 'Overnight_Gap',
    'If_Traded_SameDay', 'Actual_Execution_PnL'
]

analysis_df.to_csv(
    r'C:\Users\Penguin8n\CODEX--\CODEX--\warrant_timing_impact_analysis.csv',
    index=False
)

print(f"\n" + "="*80)
print("EXPORT")
print("="*80)
print(f"\n    Saved: warrant_timing_impact_analysis.csv")
print(f"    Detailed trade-by-trade timing analysis")

print(f"\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80 + "\n")
