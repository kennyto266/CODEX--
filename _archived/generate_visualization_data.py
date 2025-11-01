"""
Generate visualization data for HKEX correlation analysis
"""

import pandas as pd
import numpy as np
from scipy.stats import pearsonr
import warnings
warnings.filterwarnings('ignore')

# Load data
print("Loading HKEX market data...")
df = pd.read_csv(r'C:\Users\Penguin8n\CODEX--\CODEX--\hkex爬蟲\data\hkex_all_market_data.csv')

# Data preprocessing
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df = df.dropna(subset=['Afternoon_Close', 'Trading_Volume'])
df['Change_Percent'] = df['Change_Percent'].astype(str).str.replace('+', '').astype(float)
df['Change'] = df['Change'].astype(str).str.replace('+', '').astype(float)
df = df.sort_values('Date').reset_index(drop=True)

# Calculate derived metrics
df['Daily_Return'] = df['Change_Percent']
df['AD_Ratio'] = df['Advanced_Stocks'] / (df['Declined_Stocks'] + 1)
df['Market_Breadth'] = (df['Advanced_Stocks'] - df['Declined_Stocks']) / (df['Advanced_Stocks'] + df['Declined_Stocks'])
df['Volume_MA20'] = df['Trading_Volume'].rolling(window=20, min_periods=1).mean()
df['Volume_Ratio'] = df['Trading_Volume'] / df['Volume_MA20']
df['Volatility_20D'] = df['Daily_Return'].rolling(window=20, min_periods=1).std()

# RSI
def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=1).mean()
    rs = gain / (loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return rsi

df['RSI_14'] = calculate_rsi(df['Afternoon_Close'])

# MACD
exp1 = df['Afternoon_Close'].ewm(span=12, adjust=False).mean()
exp2 = df['Afternoon_Close'].ewm(span=26, adjust=False).mean()
df['MACD'] = exp1 - exp2

# Turnover per deal
df['Turnover_Per_Deal'] = df['Turnover_HKD'] / (df['Deals'] + 1)

# Clean data
df_clean = df.dropna()

# Select key metrics
metrics = [
    'Afternoon_Close',
    'Daily_Return',
    'Trading_Volume',
    'Turnover_HKD',
    'Deals',
    'Advanced_Stocks',
    'Declined_Stocks',
    'AD_Ratio',
    'Market_Breadth',
    'Volatility_20D',
    'RSI_14',
    'MACD',
    'Volume_Ratio',
    'Turnover_Per_Deal'
]

df_metrics = df_clean[metrics].copy()

# 1. Generate correlation matrix
print("\n1. Generating correlation matrix...")
corr_matrix = df_metrics.corr(method='pearson')
corr_matrix.to_csv('correlation_matrix.csv')
print("   Saved: correlation_matrix.csv")

# 2. Generate scatter plot data for top 3 predictive metrics
print("\n2. Generating scatter plot data...")
top_metrics = ['Trading_Volume', 'Afternoon_Close', 'Turnover_Per_Deal']

for i, metric in enumerate(top_metrics, 1):
    scatter_data = df_clean[['Date', 'Daily_Return', metric]].copy()
    filename = f'scatter_data_{i}_{metric}.csv'
    scatter_data.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"   Saved: {filename}")

# 3. Generate rolling correlation data
print("\n3. Generating rolling correlation data...")
for metric in top_metrics:
    rolling_5d = df_clean['Daily_Return'].rolling(5).corr(df_clean[metric])
    rolling_10d = df_clean['Daily_Return'].rolling(10).corr(df_clean[metric])

    rolling_df = pd.DataFrame({
        'Date': df_clean['Date'],
        'Metric': metric,
        'Rolling_5D': rolling_5d,
        'Rolling_10D': rolling_10d
    })
    filename = f'rolling_corr_{metric}.csv'
    rolling_df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"   Saved: {filename}")

# 4. Generate lagged correlation table
print("\n4. Generating lagged correlation table...")
lagged_results = []

for metric in metrics:
    if metric != 'Daily_Return':
        row = {'Metric': metric}
        for lag in [-2, -1, 0, 1, 2]:
            if lag < 0:
                shifted = df_clean[metric].shift(-lag)
                corr, _ = pearsonr(shifted.dropna(), df_clean['Daily_Return'].iloc[:len(shifted.dropna())])
            elif lag > 0:
                shifted = df_clean[metric].shift(lag)
                corr, _ = pearsonr(df_clean['Daily_Return'].iloc[lag:], shifted.iloc[lag:].dropna())
            else:
                corr, _ = pearsonr(df_clean[metric], df_clean['Daily_Return'])
            row[f'Lag_{lag}'] = corr
        lagged_results.append(row)

lagged_df = pd.DataFrame(lagged_results)
lagged_df.to_csv('lagged_correlations.csv', index=False, encoding='utf-8-sig')
print("   Saved: lagged_correlations.csv")

# 5. Generate 1-day ahead predictions table
print("\n5. Generating 1-day ahead prediction table...")
pred_results = []

for metric in metrics:
    if metric != 'Daily_Return':
        shifted = df_clean[metric].shift(1)
        valid_idx = ~shifted.isna() & ~df_clean['Daily_Return'].isna()
        if valid_idx.sum() > 2:
            corr, p_val = pearsonr(shifted[valid_idx], df_clean['Daily_Return'][valid_idx])
            pred_results.append({
                'Metric': metric,
                'Correlation': corr,
                'P_value': p_val,
                'Significant': 'Yes' if p_val < 0.05 else 'No'
            })

pred_df = pd.DataFrame(pred_results).sort_values('Correlation', key=abs, ascending=False)
pred_df.to_csv('predictive_power_1day.csv', index=False, encoding='utf-8-sig')
print("   Saved: predictive_power_1day.csv")

# 6. Generate strong correlation pairs
print("\n6. Generating strong correlation pairs...")
strong_pairs = []

for i in range(len(corr_matrix.columns)):
    for j in range(i+1, len(corr_matrix.columns)):
        corr_val = corr_matrix.iloc[i, j]
        if abs(corr_val) > 0.7:
            strong_pairs.append({
                'Metric_1': corr_matrix.columns[i],
                'Metric_2': corr_matrix.columns[j],
                'Correlation': corr_val,
                'Abs_Correlation': abs(corr_val)
            })

strong_df = pd.DataFrame(strong_pairs).sort_values('Abs_Correlation', ascending=False)
strong_df.to_csv('strong_correlations.csv', index=False, encoding='utf-8-sig')
print("   Saved: strong_correlations.csv")

print("\n" + "="*60)
print("All visualization data files generated successfully!")
print("="*60)
print("\nGenerated files:")
print("1. correlation_matrix.csv - Full 14x14 correlation matrix")
print("2. scatter_data_*.csv - Scatter plot data (3 files)")
print("3. rolling_corr_*.csv - Rolling correlation time series (3 files)")
print("4. lagged_correlations.csv - Lagged correlation analysis")
print("5. predictive_power_1day.csv - 1-day ahead predictions")
print("6. strong_correlations.csv - All correlation pairs |r| > 0.7")
print("\nTotal: 11 CSV files")
