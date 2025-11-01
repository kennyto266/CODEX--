# -*- coding: utf-8 -*-
"""
HKEX Bull/Bear Warrant Sentiment Analysis - Contrarian Indicator
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
from datetime import datetime, timedelta
import warnings
import sys
warnings.filterwarnings('ignore')

# Force UTF-8 output
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("="*80)
print("HKEX Bull/Bear Warrant Sentiment Analysis - Contrarian Indicator")
print("="*80)

# ==================== 1. 加载市场数据 ====================
market_data = pd.read_csv(
    r'C:\Users\Penguin8n\CODEX--\CODEX--\hkex爬蟲\data\hkex_all_market_data.csv'
)
market_data['Date'] = pd.to_datetime(market_data['Date'])
market_data = market_data.sort_values('Date').reset_index(drop=True)

print(f"\n✓ 市场数据: {len(market_data)} 行")
print(f"  日期范围: {market_data['Date'].min().date()} 至 {market_data['Date'].max().date()}")

# ==================== 2. 加载并解析权证数据 ====================
top_stocks_dir = Path(r'C:\Users\Penguin8n\CODEX--\CODEX--\hkex爬蟲\data\top_stocks')
warrant_files = sorted(top_stocks_dir.glob('top_stocks_by_shares_*.csv'))

print(f"\n✓ 发现权证文件: {len(warrant_files)} 个")

warrant_summary = []

for file_path in warrant_files:
    try:
        df = pd.read_csv(file_path)
        date_str = file_path.stem.split('_')[-1]
        date = pd.to_datetime(date_str)

        # 提取牛/熊标记 - 检查Name_CHI的第6位字符
        df['Type'] = df['Name_CHI'].str[5:6]  # Python索引从0开始，第6位是index 5

        # 计算牛熊成交
        bull_data = df[df['Type'] == '牛']
        bear_data = df[df['Type'] == '熊']

        bull_turnover = bull_data['Turnover_HKD'].sum() if len(bull_data) > 0 else 0
        bear_turnover = bear_data['Turnover_HKD'].sum() if len(bear_data) > 0 else 0

        bull_shares = bull_data['Shares_Traded'].sum() if len(bull_data) > 0 else 0
        bear_shares = bear_data['Shares_Traded'].sum() if len(bear_data) > 0 else 0

        total_turnover = bull_turnover + bear_turnover

        if total_turnover > 0:
            bull_ratio = bull_turnover / total_turnover
            warrant_sentiment = bull_ratio - 0.5  # -0.5 to +0.5
        else:
            bull_ratio = 0.5
            warrant_sentiment = 0

        # 计算比例
        if bear_turnover > 0:
            bull_bear_ratio = bull_turnover / bear_turnover
        else:
            bull_bear_ratio = np.inf if bull_turnover > 0 else 1.0

        warrant_summary.append({
            'Date': date,
            'Bull_Turnover_HKD': bull_turnover,
            'Bear_Turnover_HKD': bear_turnover,
            'Total_Warrant_Turnover': total_turnover,
            'Bull_Ratio': bull_ratio,  # 0.5表示平衡，>0.5看涨，<0.5看跌
            'Bull_Bear_Ratio': bull_bear_ratio,  # 1.0表示平衡
            'Warrant_Sentiment': warrant_sentiment,  # -0.5 to +0.5
            'Bull_Count': len(bull_data),
            'Bear_Count': len(bear_data),
            'Bull_Shares': bull_shares,
            'Bear_Shares': bear_shares,
        })

    except Exception as e:
        print(f"  ⚠ 错误处理 {file_path.name}: {e}")

warrant_df = pd.DataFrame(warrant_summary)
warrant_df = warrant_df.sort_values('Date').reset_index(drop=True)

print(f"\n✓ 权证数据: {len(warrant_df)} 天")
print(f"  日期范围: {warrant_df['Date'].min().date()} 至 {warrant_df['Date'].max().date()}")

# ==================== 3. 合并数据 ====================
merged = market_data.merge(warrant_df, on='Date', how='inner')
merged = merged.sort_values('Date').reset_index(drop=True)

print(f"\n✓ 合并后: {len(merged)} 行")

# ==================== 4. 提取相反信号 ====================
print("\n" + "="*80)
print("牛熊权证情绪分析")
print("="*80)

# 计算极端读数
bull_ratio_mean = merged['Bull_Ratio'].mean()
bull_ratio_std = merged['Bull_Ratio'].std()

print(f"\n【权证比例统计】")
print(f"  平均牛比例: {bull_ratio_mean:.2%}")
print(f"  标准差: {bull_ratio_std:.2%}")
print(f"  极度看涨阈值 (>0.65): 零售极度乐观")
print(f"  极度看跌阈值 (<0.35): 零售极度悲观")

# ==================== 5. 相关性分析 ====================
print(f"\n【相关性分析 - 权证 vs 市场】\n")

# 同日相关性
corr_bull_return_same = merged['Bull_Ratio'].corr(merged['Daily_Return'])
corr_bear_return_same = merged['Bear_Turnover_HKD'].corr(merged['Daily_Return'])
corr_sentiment_return_same = merged['Warrant_Sentiment'].corr(merged['Daily_Return'])
corr_bullebear_return_same = merged['Bull_Bear_Ratio'].corr(merged['Daily_Return'])

# p-值计算
n = len(merged)
t_bull = corr_bull_return_same * np.sqrt(n-2) / np.sqrt(1-corr_bull_return_same**2) if corr_bull_return_same**2 < 1 else 0
p_bull = 2 * (1 - stats.t.cdf(abs(t_bull), n-2))

print(f"同日相关性 (Current Day):")
print(f"  牛比例 vs 日收益率:")
print(f"    相关系数: {corr_bull_return_same:+.4f}")
print(f"    P值: {p_bull:.4f} {'✓ 显著' if p_bull < 0.05 else '✗ 不显著'}")
print(f"  ")
print(f"  权证情绪 vs 日收益率:")
print(f"    相关系数: {corr_sentiment_return_same:+.4f}")

# 1日领先分析 (Lagged)
if len(merged) > 1:
    merged['Bull_Ratio_Lag1'] = merged['Bull_Ratio'].shift(1)
    merged['Daily_Return_Lead1'] = merged['Daily_Return'].shift(-1)

    valid_data = merged[['Bull_Ratio_Lag1', 'Daily_Return_Lead1']].dropna()
    if len(valid_data) > 2:
        corr_bull_return_lead = valid_data['Bull_Ratio_Lag1'].corr(valid_data['Daily_Return_Lead1'])
        n_lead = len(valid_data)
        t_lead = corr_bull_return_lead * np.sqrt(n_lead-2) / np.sqrt(1-corr_bull_return_lead**2) if corr_bull_return_lead**2 < 1 else 0
        p_lead = 2 * (1 - stats.t.cdf(abs(t_lead), n_lead-2))

        print(f"\n1日领先分析 (前日 → 次日):")
        print(f"  前日牛比例 → 次日收益率:")
        print(f"    相关系数: {corr_bull_return_lead:+.4f}")
        print(f"    P值: {p_lead:.4f} {'✓ 显著' if p_lead < 0.05 else '✗ 不显著'}")

# ==================== 6. 极端读数分析 ====================
print(f"\n【极端权证读数 - 相反信号强度】\n")

# 识别极端看涨日
extreme_bull = merged[merged['Bull_Ratio'] > 0.65].copy()
extreme_bear = merged[merged['Bull_Ratio'] < 0.35].copy()

print(f"极度看涨日 (Bull_Ratio > 0.65):")
print(f"  发生次数: {len(extreme_bull)}")
if len(extreme_bull) > 0:
    print(f"  当日收益率: {extreme_bull['Daily_Return'].mean():+.2%} (平均)")
    print(f"  胜率: {(extreme_bull['Daily_Return'] > 0).sum()}/{len(extreme_bull)}")

print(f"\n极度看跌日 (Bull_Ratio < 0.35):")
print(f"  发生次数: {len(extreme_bear)}")
if len(extreme_bear) > 0:
    print(f"  当日收益率: {extreme_bear['Daily_Return'].mean():+.2%} (平均)")
    print(f"  胜率: {(extreme_bear['Daily_Return'] > 0).sum()}/{len(extreme_bear)}")

# ==================== 7. 相反策略模拟 ====================
print(f"\n【相反交易策略回测】\n")

merged['Contrarian_Signal'] = 0
merged.loc[merged['Bull_Ratio'] > 0.65, 'Contrarian_Signal'] = -1  # 零售看涨 → 我们看跌
merged.loc[merged['Bull_Ratio'] < 0.35, 'Contrarian_Signal'] = 1   # 零售看跌 → 我们看涨

# 计算次日收益
merged['Return_Next_Day'] = merged['Daily_Return'].shift(-1)

contrarian_trades = merged[merged['Contrarian_Signal'] != 0].copy()
if len(contrarian_trades) > 0:
    contrarian_trades['Trade_Result'] = contrarian_trades['Contrarian_Signal'] * contrarian_trades['Return_Next_Day']

    win_count = (contrarian_trades['Trade_Result'] > 0).sum()
    total_count = len(contrarian_trades)
    win_rate = win_count / total_count if total_count > 0 else 0
    avg_return = contrarian_trades['Trade_Result'].mean()

    print(f"相反策略 (仅在极端读数时交易):")
    print(f"  交易次数: {total_count}")
    print(f"  胜率: {win_rate:.1%} ({win_count}/{total_count})")
    print(f"  平均收益: {avg_return:+.2%}")
    print(f"  累计收益: {contrarian_trades['Trade_Result'].sum():+.2%}")

# ==================== 8. 当前情绪 ====================
print(f"\n【当前权证情绪】\n")

latest = merged.iloc[-1]
print(f"最新日期: {latest['Date'].date()}")
print(f"  牛比例: {latest['Bull_Ratio']:.1%}")
print(f"  牛/熊成交额: {latest['Bull_Turnover_HKD']:.2e} / {latest['Bear_Turnover_HKD']:.2e}")
print(f"  权证情绪: {latest['Warrant_Sentiment']:+.4f}")

if latest['Bull_Ratio'] > 0.65:
    print(f"  ⚠ 信号: 零售极度看涨 → 相反信号: 警惕调整")
elif latest['Bull_Ratio'] < 0.35:
    print(f"  ⚠ 信号: 零售极度看跌 → 相反信号: 注意反弹机会")
else:
    print(f"  ⊖ 信号: 中性")

# ==================== 9. 导出数据 ====================
output_cols = [
    'Date', 'Afternoon_Close', 'Daily_Return', 'Market_Breadth',
    'Bull_Turnover_HKD', 'Bear_Turnover_HKD', 'Bull_Ratio',
    'Bull_Bear_Ratio', 'Warrant_Sentiment'
]

merged[output_cols].to_csv(
    r'C:\Users\Penguin8n\CODEX--\CODEX--\warrant_sentiment_merged.csv',
    index=False
)

print(f"\n✓ 已保存: warrant_sentiment_merged.csv")

# 保存汇总统计
summary_stats = pd.DataFrame({
    'Metric': [
        'Bull_Ratio_Mean', 'Bull_Ratio_Std', 'Bull_Ratio_Min', 'Bull_Ratio_Max',
        'Corr_Bull_Ratio_vs_Return', 'P_Value',
        'Extreme_Bull_Days', 'Extreme_Bear_Days',
        'Contrarian_Win_Rate', 'Contrarian_Avg_Return'
    ],
    'Value': [
        bull_ratio_mean,
        bull_ratio_std,
        merged['Bull_Ratio'].min(),
        merged['Bull_Ratio'].max(),
        corr_bull_return_same,
        p_bull,
        len(extreme_bull),
        len(extreme_bear),
        win_rate if len(contrarian_trades) > 0 else 0,
        avg_return if len(contrarian_trades) > 0 else 0
    ]
})

summary_stats.to_csv(
    r'C:\Users\Penguin8n\CODEX--\CODEX--\warrant_sentiment_summary.csv',
    index=False
)

print(f"✓ 已保存: warrant_sentiment_summary.csv")

# ==================== 10. 权证情绪日志 ====================
warrant_daily = merged[[
    'Date', 'Bull_Ratio', 'Bull_Bear_Ratio', 'Warrant_Sentiment',
    'Bull_Turnover_HKD', 'Bear_Turnover_HKD', 'Total_Warrant_Turnover',
    'Daily_Return', 'Market_Breadth', 'Contrarian_Signal'
]].copy()

warrant_daily['Sentiment_Level'] = warrant_daily['Bull_Ratio'].apply(
    lambda x: '极度看涨' if x > 0.65 else ('极度看跌' if x < 0.35 else '中性')
)

print(f"\n【权证情绪日志】\n")
print(warrant_daily[['Date', 'Bull_Ratio', 'Sentiment_Level', 'Daily_Return']].to_string(index=False))

warrant_daily.to_csv(
    r'C:\Users\Penguin8n\CODEX--\CODEX--\warrant_sentiment_daily.csv',
    index=False
)

print(f"\n✓ 已保存: warrant_sentiment_daily.csv")

print("\n" + "="*80)
print("分析完成!")
print("="*80)
