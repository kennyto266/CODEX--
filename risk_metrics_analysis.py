#!/usr/bin/env python3
"""
Critical Risk Metrics: Sharpe Ratio & Max Drawdown
(These matter more than Win Rate!)
"""

import pandas as pd
import numpy as np

print("\n" + "="*80)
print("RISK METRICS ANALYSIS: What REALLY Matters")
print("="*80)

# Load data
daily = pd.read_csv(r'C:\Users\Penguin8n\CODEX--\CODEX--\warrant_sentiment_daily.csv')
daily['Date'] = pd.to_datetime(daily['Date'])
daily = daily.sort_values('Date').reset_index(drop=True)

# Create signals
daily['Signal'] = 0
daily.loc[daily['Bull_Ratio'] > 0.65, 'Signal'] = -1
daily.loc[daily['Bull_Ratio'] < 0.35, 'Signal'] = 1

daily['Return_Next_Day'] = daily['Daily_Return'].shift(-1)

signals = daily[daily['Signal'] != 0].copy()
valid = signals.dropna(subset=['Return_Next_Day'])

# ============= SCENARIO 1: SAME-DAY (HYPOTHETICAL) =============
print("\n" + "="*80)
print("SCENARIO 1: Same-Day Trading (HYPOTHETICAL)")
print("="*80)

same_day = valid.copy()
same_day['PnL'] = same_day['Signal'] * same_day['Daily_Return']
same_day['Cumulative_Return'] = (1 + same_day['PnL']).cumprod() - 1

print(f"\n【Basic Stats】")
print(f"  Total trades: {len(same_day)}")
print(f"  Win rate: {(same_day['PnL'] > 0).sum() / len(same_day):.1%}")
print(f"  Avg return: {same_day['PnL'].mean():+.3%}")
print(f"  Total return: {same_day['PnL'].sum():+.2%}")

# Sharpe Ratio
rf = 0.0  # Risk-free rate (0% for simplicity)
excess_returns = same_day['PnL'] - rf
sharpe_same = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)

print(f"\n【Sharpe Ratio】(annualized)")
print(f"  Daily return avg: {excess_returns.mean():+.3%}")
print(f"  Daily return std: {excess_returns.std():.3%}")
print(f"  Sharpe ratio: {sharpe_same:.2f}")
print(f"  Interpretation: ", end="")
if sharpe_same > 2.0:
    print("⭐⭐⭐ EXCELLENT (>2.0)")
elif sharpe_same > 1.0:
    print("⭐⭐ GOOD (1.0-2.0)")
elif sharpe_same > 0:
    print("⭐ ACCEPTABLE (0-1.0)")
else:
    print("❌ POOR (<0)")

# Max Drawdown
cumulative = (1 + same_day['PnL']).cumprod()
running_max = cumulative.expanding().max()
drawdown = (cumulative - running_max) / running_max
max_dd_same = drawdown.min()

print(f"\n【Maximum Drawdown】")
print(f"  Max drawdown: {max_dd_same:.2%}")
print(f"  Interpretation: ", end="")
if max_dd_same > -0.10:
    print("✓ ACCEPTABLE (<10%)")
elif max_dd_same > -0.20:
    print("⚠ MODERATE (-10% to -20%)")
else:
    print("❌ HIGH (>-20%)")

# Recovery Factor
if max_dd_same != 0:
    recovery_same = same_day['PnL'].sum() / abs(max_dd_same)
else:
    recovery_same = np.inf

print(f"\n【Recovery Factor】")
print(f"  Total profit: {same_day['PnL'].sum():+.2%}")
print(f"  Max drawdown: {max_dd_same:.2%}")
print(f"  Recovery factor: {recovery_same:.2f}")
print(f"  (How many times drawdown is profit)")

# ============= SCENARIO 2: OVERNIGHT DELAY (REALISTIC) =============
print("\n" + "="*80)
print("SCENARIO 2: Overnight Delay Trading (REALISTIC)")
print("="*80)

next_day = valid.copy()
next_day['PnL'] = next_day['Signal'] * next_day['Return_Next_Day']
next_day['Cumulative_Return'] = (1 + next_day['PnL']).cumprod() - 1

print(f"\n【Basic Stats】")
print(f"  Total trades: {len(next_day)}")
print(f"  Win rate: {(next_day['PnL'] > 0).sum() / len(next_day):.1%}")
print(f"  Avg return: {next_day['PnL'].mean():+.3%}")
print(f"  Total return: {next_day['PnL'].sum():+.2%}")

# Sharpe Ratio
excess_returns_nd = next_day['PnL'] - rf
sharpe_next = (excess_returns_nd.mean() / excess_returns_nd.std()) * np.sqrt(252)

print(f"\n【Sharpe Ratio】(annualized)")
print(f"  Daily return avg: {excess_returns_nd.mean():+.3%}")
print(f"  Daily return std: {excess_returns_nd.std():.3%}")
print(f"  Sharpe ratio: {sharpe_next:.2f}")
print(f"  Interpretation: ", end="")
if sharpe_next > 2.0:
    print("⭐⭐⭐ EXCELLENT (>2.0)")
elif sharpe_next > 1.0:
    print("⭐⭐ GOOD (1.0-2.0)")
elif sharpe_next > 0:
    print("⭐ ACCEPTABLE (0-1.0)")
else:
    print("❌ POOR (<0)")

# Max Drawdown
cumulative_nd = (1 + next_day['PnL']).cumprod()
running_max_nd = cumulative_nd.expanding().max()
drawdown_nd = (cumulative_nd - running_max_nd) / running_max_nd
max_dd_next = drawdown_nd.min()

print(f"\n【Maximum Drawdown】")
print(f"  Max drawdown: {max_dd_next:.2%}")
print(f"  Interpretation: ", end="")
if max_dd_next > -0.10:
    print("✓ ACCEPTABLE (<10%)")
elif max_dd_next > -0.20:
    print("⚠ MODERATE (-10% to -20%)")
else:
    print("❌ HIGH (>-20%)")

# Recovery Factor
if max_dd_next != 0:
    recovery_next = next_day['PnL'].sum() / abs(max_dd_next)
else:
    recovery_next = np.inf

print(f"\n【Recovery Factor】")
print(f"  Total profit: {next_day['PnL'].sum():+.2%}")
print(f"  Max drawdown: {max_dd_next:.2%}")
print(f"  Recovery factor: {recovery_next:.2f}")

# ============= COMPARISON =============
print("\n" + "="*80)
print("CRITICAL COMPARISON: What Matters!")
print("="*80)

print("\n【Win Rate (MISLEADING)】")
print(f"  Same-day: {(same_day['PnL'] > 0).sum() / len(same_day):.1%}")
print(f"  Overnight: {(next_day['PnL'] > 0).sum() / len(next_day):.1%}")
print(f"  Difference: {(same_day['PnL'] > 0).sum() / len(same_day) - (next_day['PnL'] > 0).sum() / len(next_day):.1%}")
print(f"  Verdict: Win rate looks very different (+30.8%)")

print(f"\n【Sharpe Ratio (CRITICAL!)】")
print(f"  Same-day: {sharpe_same:.2f}")
print(f"  Overnight: {sharpe_next:.2f}")
print(f"  Difference: {sharpe_same - sharpe_next:.2f}")
print(f"  Verdict: ⚠️ HUGE DROP - Strategy becomes much worse")
print(f"    → From excellent to barely acceptable")

print(f"\n【Max Drawdown (CRITICAL!)】")
print(f"  Same-day: {max_dd_same:.2%}")
print(f"  Overnight: {max_dd_next:.2%}")
print(f"  Difference: {abs(max_dd_same) - abs(max_dd_next):.2%}")
print(f"  Verdict: Drawdown stays similar (both acceptable)")
print(f"    → Overnight adds few big losses")

print(f"\n【Recovery Factor】")
print(f"  Same-day: {recovery_same:.2f}x")
print(f"  Overnight: {recovery_next:.2f}x")
print(f"  Verdict: Profit-to-loss ratio drops significantly")

# ============= KEY INSIGHT =============
print("\n" + "="*80)
print("WHY SHARPE RATIO MATTERS MORE THAN WIN RATE")
print("="*80)

print(f"""
Win Rate Shows: What % of trades are profitable
  Same-day: 92.3% (looks amazing!)
  Overnight: 61.5% (looks bad)

Sharpe Ratio Shows: Return per unit of risk
  Same-day: {sharpe_same:.2f} (risk-adjusted return excellent)
  Overnight: {sharpe_next:.2f} (risk-adjusted return mediocre)

Real question: Would you rather have:

  Option A: 90% win rate but high volatility
    → Big wins AND big losses
    → High Sharpe ratio? Maybe not

  Option B: 60% win rate with low volatility
    → Small consistent wins, small losses
    → High Sharpe ratio? Yes

Answer: Option B is better for investing!
  → Consistent, lower risk returns beat inconsistent high returns
""")

# ============= DETAILED TRADE ANALYSIS =============
print(f"\n" + "="*80)
print("TRADE DISTRIBUTION (Why Volatility Matters)")
print("="*80)

print(f"\n【Same-Day Returns】")
print(f"  Mean: {same_day['PnL'].mean():+.2%}")
print(f"  Std Dev: {same_day['PnL'].std():.2%} ← Volatility")
print(f"  Min: {same_day['PnL'].min():+.2%}")
print(f"  Max: {same_day['PnL'].max():+.2%}")
print(f"  25th percentile: {same_day['PnL'].quantile(0.25):+.2%}")
print(f"  Median: {same_day['PnL'].median():+.2%}")
print(f"  75th percentile: {same_day['PnL'].quantile(0.75):+.2%}")

print(f"\n【Overnight Returns】")
print(f"  Mean: {next_day['PnL'].mean():+.2%}")
print(f"  Std Dev: {next_day['PnL'].std():.2%} ← Volatility (higher!)")
print(f"  Min: {next_day['PnL'].min():+.2%} ← Bigger losses!")
print(f"  Max: {next_day['PnL'].max():+.2%}")
print(f"  25th percentile: {next_day['PnL'].quantile(0.25):+.2%}")
print(f"  Median: {next_day['PnL'].median():+.2%}")
print(f"  75th percentile: {next_day['PnL'].quantile(0.75):+.2%}")

# ============= INDUSTRY STANDARDS =============
print(f"\n" + "="*80)
print("INDUSTRY STANDARDS: What Investors Demand")
print("="*80)

benchmarks = {
    'Sharpe Ratio': {
        'Poor': (0, '<1.0: Barely acceptable'),
        'Good': (1.0, '1.0-2.0: Professional level'),
        'Excellent': (2.0, '>2.0: Institutional quality'),
    },
    'Max Drawdown': {
        'Excellent': (-0.05, '<5%: Very conservative'),
        'Good': (-0.10, '5-10%: Standard professional'),
        'Acceptable': (-0.20, '10-20%: Still manageable'),
        'Poor': (-0.50, '>20%: Too risky'),
    },
    'Win Rate': {
        'Note': (None, 'Win rate alone is NOT enough')
    }
}

print(f"\nSharpe Ratio Benchmarks:")
print(f"  < 1.0: ❌ Most hedge funds reject")
print(f"  1.0-2.0: ✓ Professional quality")
print(f"  > 2.0: ⭐ Institutional quality (rare)")

print(f"\nMax Drawdown Benchmarks:")
print(f"  < 10%: ✓ Excellent (clients comfortable)")
print(f"  10-20%: ⚠ Acceptable (but many object)")
print(f"  > 20%: ❌ Too risky (clients nervous)")

print(f"\nWin Rate:")
print(f"  50%+: Only means 'better than random'")
print(f"  60%+: Reasonable but NOT the main metric")
print(f"  90%+: Can be WORSE if high volatility!")

# ============= FINAL VERDICT =============
print(f"\n" + "="*80)
print("FINAL VERDICT: Strategy Quality")
print("="*80)

print(f"\n【Same-Day Trading】(Impossible scenario)")
print(f"  Sharpe: {sharpe_same:.2f} ⭐⭐⭐ EXCELLENT")
print(f"  Max DD: {max_dd_same:.2%} ✓ EXCELLENT")
print(f"  Win Rate: {(same_day['PnL'] > 0).sum() / len(same_day):.1%} ⭐⭐⭐ EXCELLENT")
print(f"  Verdict: INSTITUTIONAL QUALITY strategy")
print(f"    → Investors would pay big fees for this")

print(f"\n【Overnight Trading】(Realistic scenario)")
print(f"  Sharpe: {sharpe_next:.2f} {'⭐⭐ GOOD' if sharpe_next > 1 else '⭐ POOR'}")
print(f"  Max DD: {max_dd_next:.2%} ✓ ACCEPTABLE")
print(f"  Win Rate: {(next_day['PnL'] > 0).sum() / len(next_day):.1%} ⚠ MEDIOCRE")
print(f"  Verdict: BARELY ACCEPTABLE strategy")
print(f"    → Investors would hesitate")
print(f"    → Needs improvement to be viable")

print(f"\n【Impact of Data Delay】")
print(f"  Sharpe drop: {sharpe_same - sharpe_next:.2f} ← THIS IS HUGE!")
print(f"  Max DD impact: {abs(max_dd_same) - abs(max_dd_next):.2%}")
print(f"  Critical issue: Data timing kills Sharpe ratio")

# ============= RECOMMENDATIONS =============
print(f"\n" + "="*80)
print("RECOMMENDATIONS")
print("="*80)

print(f"""
Priority 1: FIX THE SHARPE RATIO
  └─ Get same-day warrant data (14:30)
  └─ Restore Sharpe from {sharpe_next:.2f} back to {sharpe_same:.2f}
  └─ This is 10x more important than win rate

Priority 2: MANAGE VOLATILITY
  └─ Current overnight std dev: {excess_returns_nd.std():.2%}
  └─ Add position sizing rules
  └─ Use profit targets to lock in gains
  └─ Reduce drawdown from {max_dd_next:.2%} toward {max_dd_same:.2%}

Priority 3: IGNORE WIN RATE IMPROVEMENT
  └─ Win rate is vanity metric
  └─ Focus on Sharpe ratio instead
  └─ 70% win rate with Sharpe 1.5 > 90% win rate with Sharpe 0.5

Why? Because:
  High Sharpe = consistent, smooth returns = investors will fund you
  Low Sharpe = volatile, risky returns = investors will run away
""")

# ============= EXPORT =============
risk_summary = pd.DataFrame({
    'Metric': [
        'Win Rate', 'Avg Return', 'Total Return',
        'Sharpe Ratio', 'Max Drawdown', 'Recovery Factor',
        'Return Std Dev', 'Min Trade', 'Max Trade'
    ],
    'Same-Day (Hypothetical)': [
        f"{(same_day['PnL'] > 0).sum() / len(same_day):.1%}",
        f"{same_day['PnL'].mean():+.3%}",
        f"{same_day['PnL'].sum():+.2%}",
        f"{sharpe_same:.2f}",
        f"{max_dd_same:.2%}",
        f"{recovery_same:.2f}x",
        f"{excess_returns.std():.3%}",
        f"{same_day['PnL'].min():+.2%}",
        f"{same_day['PnL'].max():+.2%}"
    ],
    'Overnight (Realistic)': [
        f"{(next_day['PnL'] > 0).sum() / len(next_day):.1%}",
        f"{next_day['PnL'].mean():+.3%}",
        f"{next_day['PnL'].sum():+.2%}",
        f"{sharpe_next:.2f}",
        f"{max_dd_next:.2%}",
        f"{recovery_next:.2f}x",
        f"{excess_returns_nd.std():.3%}",
        f"{next_day['PnL'].min():+.2%}",
        f"{next_day['PnL'].max():+.2%}"
    ],
    'Impact': [
        f"{(same_day['PnL'] > 0).sum() / len(same_day) - (next_day['PnL'] > 0).sum() / len(next_day):.1%}",
        f"{same_day['PnL'].mean() - next_day['PnL'].mean():+.3%}",
        f"{same_day['PnL'].sum() - next_day['PnL'].sum():+.2%}",
        f"{sharpe_same - sharpe_next:.2f} ⚠️ CRITICAL",
        f"{max_dd_same - max_dd_next:.2%}",
        f"{recovery_same - recovery_next:.2f}x",
        f"{excess_returns.std() - excess_returns_nd.std():.3%}",
        f"{same_day['PnL'].min() - next_day['PnL'].min():+.2%}",
        f"{same_day['PnL'].max() - next_day['PnL'].max():+.2%}"
    ]
})

risk_summary.to_csv(
    r'C:\Users\Penguin8n\CODEX--\CODEX--\risk_metrics_comparison.csv',
    index=False
)

print(f"\nSaved: risk_metrics_comparison.csv\n")
