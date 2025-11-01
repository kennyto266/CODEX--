"""
Comprehensive HKEX Market Correlation Analysis
Performs detailed correlation analysis on HKEX market data
"""

import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import pearsonr
import warnings
warnings.filterwarnings('ignore')

# Load data
print("Loading HKEX market data...")
df = pd.read_csv(r'C:\Users\Penguin8n\CODEX--\CODEX--\hkex爬蟲\data\hkex_all_market_data.csv')

# Data preprocessing
print("\n" + "="*80)
print("DATA PREPROCESSING")
print("="*80)

# Convert Date to datetime
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

# Remove rows with missing critical data
df = df.dropna(subset=['Afternoon_Close', 'Trading_Volume'])

# Clean Change_Percent (remove '+' and convert to float)
df['Change_Percent'] = df['Change_Percent'].astype(str).str.replace('+', '').astype(float)

# Clean Change (remove '+' and convert to float)
df['Change'] = df['Change'].astype(str).str.replace('+', '').astype(float)

# Sort by date
df = df.sort_values('Date').reset_index(drop=True)

print(f"Total records: {len(df)}")
print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")

# Calculate derived metrics
print("\nCalculating derived metrics...")

# Daily return (percentage)
df['Daily_Return'] = df['Change_Percent']

# Advance-Decline Ratio
df['AD_Ratio'] = df['Advanced_Stocks'] / (df['Declined_Stocks'] + 1)  # +1 to avoid division by zero

# Market Breadth
df['Market_Breadth'] = (df['Advanced_Stocks'] - df['Declined_Stocks']) / (df['Advanced_Stocks'] + df['Declined_Stocks'])

# Volume Ratio (current volume / 20-day average)
df['Volume_MA20'] = df['Trading_Volume'].rolling(window=20, min_periods=1).mean()
df['Volume_Ratio'] = df['Trading_Volume'] / df['Volume_MA20']

# Price-based indicators
df['Price_Change'] = df['Afternoon_Close'].pct_change() * 100

# Volatility (20-day rolling standard deviation of returns)
df['Volatility_20D'] = df['Daily_Return'].rolling(window=20, min_periods=1).std()

# RSI (14-day)
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
df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

# Turnover per deal
df['Turnover_Per_Deal'] = df['Turnover_HKD'] / (df['Deals'] + 1)

# Drop NaN values for correlation analysis
df_clean = df.dropna()

print(f"Records after cleaning: {len(df_clean)}")

# Select key metrics for correlation analysis
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

print("\n" + "="*80)
print("1. CORRELATION MATRIX ANALYSIS")
print("="*80)

# Calculate correlation matrix
corr_matrix = df_metrics.corr(method='pearson')

print("\nFull Correlation Matrix:")
print(corr_matrix.round(3).to_string())

# Calculate p-values for correlations
def calculate_pvalues(df):
    """Calculate p-values for all pairwise correlations"""
    cols = df.columns
    p_matrix = pd.DataFrame(np.zeros((len(cols), len(cols))), columns=cols, index=cols)

    for i, col1 in enumerate(cols):
        for j, col2 in enumerate(cols):
            if i != j:
                _, p_value = pearsonr(df[col1].dropna(), df[col2].dropna())
                p_matrix.iloc[i, j] = p_value

    return p_matrix

p_values = calculate_pvalues(df_metrics)

print("\n" + "="*80)
print("2. CORRELATION STRENGTH ANALYSIS")
print("="*80)

# Extract correlations with Daily_Return
daily_return_corr = corr_matrix['Daily_Return'].drop('Daily_Return').sort_values(ascending=False)
daily_return_pvals = p_values['Daily_Return'].drop('Daily_Return')

print("\nCorrelations with Daily_Return (sorted by strength):")
print("-" * 80)
print(f"{'Metric':<25} {'Correlation':>12} {'P-value':>12} {'Significance':>15}")
print("-" * 80)

for metric in daily_return_corr.index:
    corr_val = daily_return_corr[metric]
    p_val = daily_return_pvals[metric]
    sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "NS"
    print(f"{metric:<25} {corr_val:>12.4f} {p_val:>12.6f} {sig:>15}")

print("\n*** p < 0.001, ** p < 0.01, * p < 0.05, NS = Not Significant")

# Strong correlations (>0.7 or <-0.7)
print("\n" + "="*80)
print("STRONG CORRELATIONS (|r| > 0.7)")
print("="*80)

strong_corr_pairs = []
for i in range(len(corr_matrix.columns)):
    for j in range(i+1, len(corr_matrix.columns)):
        corr_val = corr_matrix.iloc[i, j]
        if abs(corr_val) > 0.7:
            metric1 = corr_matrix.columns[i]
            metric2 = corr_matrix.columns[j]
            p_val = p_values.iloc[i, j]
            strong_corr_pairs.append({
                'Metric 1': metric1,
                'Metric 2': metric2,
                'Correlation': corr_val,
                'P-value': p_val
            })

if strong_corr_pairs:
    strong_df = pd.DataFrame(strong_corr_pairs)
    print(strong_df.to_string(index=False))
else:
    print("No strong correlations found (|r| > 0.7)")

# Moderate correlations (0.4-0.7 or -0.4 to -0.7)
print("\n" + "="*80)
print("MODERATE CORRELATIONS (0.4 < |r| < 0.7)")
print("="*80)

moderate_corr_pairs = []
for i in range(len(corr_matrix.columns)):
    for j in range(i+1, len(corr_matrix.columns)):
        corr_val = corr_matrix.iloc[i, j]
        if 0.4 <= abs(corr_val) < 0.7:
            metric1 = corr_matrix.columns[i]
            metric2 = corr_matrix.columns[j]
            p_val = p_values.iloc[i, j]
            moderate_corr_pairs.append({
                'Metric 1': metric1,
                'Metric 2': metric2,
                'Correlation': corr_val,
                'P-value': p_val
            })

if moderate_corr_pairs:
    moderate_df = pd.DataFrame(moderate_corr_pairs)
    # Sort by absolute correlation
    moderate_df['Abs_Corr'] = moderate_df['Correlation'].abs()
    moderate_df = moderate_df.sort_values('Abs_Corr', ascending=False).drop('Abs_Corr', axis=1)
    print(moderate_df.to_string(index=False))
else:
    print("No moderate correlations found")

print("\n" + "="*80)
print("3. LEADING vs LAGGING INDICATORS")
print("="*80)

# Calculate lagged correlations to identify leading/lagging indicators
print("\nLagged Correlation Analysis (Daily_Return as target):")
print("-" * 80)
print(f"{'Metric':<25} {'Lag -2':>10} {'Lag -1':>10} {'Lag 0':>10} {'Lag +1':>10} {'Lag +2':>10}")
print("-" * 80)

for metric in metrics:
    if metric != 'Daily_Return':
        lag_corrs = []
        for lag in [-2, -1, 0, 1, 2]:
            if lag < 0:
                # Metric leads returns
                shifted = df_clean[metric].shift(-lag)
                corr, _ = pearsonr(shifted.dropna(), df_clean['Daily_Return'].iloc[:len(shifted.dropna())])
            elif lag > 0:
                # Metric lags returns
                shifted = df_clean[metric].shift(lag)
                corr, _ = pearsonr(df_clean['Daily_Return'].iloc[lag:], shifted.iloc[lag:].dropna())
            else:
                # No lag
                corr, _ = pearsonr(df_clean[metric], df_clean['Daily_Return'])
            lag_corrs.append(corr)

        print(f"{metric:<25} {lag_corrs[0]:>10.4f} {lag_corrs[1]:>10.4f} {lag_corrs[2]:>10.4f} {lag_corrs[3]:>10.4f} {lag_corrs[4]:>10.4f}")

print("\nInterpretation:")
print("- Negative lag: Metric LEADS returns (predictive)")
print("- Positive lag: Metric LAGS returns (reactive)")
print("- Lag 0: Contemporaneous correlation")

print("\n" + "="*80)
print("4. PREDICTIVE POWER ANALYSIS")
print("="*80)

# Identify top predictive metrics
print("\nTop Predictive Metrics (1-day ahead correlation):")
print("-" * 80)

predictive_metrics = []
for metric in metrics:
    if metric != 'Daily_Return':
        # Shift metric back by 1 day to test if it predicts next day's return
        shifted = df_clean[metric].shift(1)
        valid_idx = ~shifted.isna() & ~df_clean['Daily_Return'].isna()
        if valid_idx.sum() > 2:
            corr, p_val = pearsonr(shifted[valid_idx], df_clean['Daily_Return'][valid_idx])
            predictive_metrics.append({
                'Metric': metric,
                'Correlation': corr,
                'P-value': p_val,
                'Abs_Corr': abs(corr)
            })

pred_df = pd.DataFrame(predictive_metrics).sort_values('Abs_Corr', ascending=False)
print(pred_df[['Metric', 'Correlation', 'P-value']].to_string(index=False))

print("\n" + "="*80)
print("5. ROLLING CORRELATION ANALYSIS")
print("="*80)

# Calculate rolling correlations for top 3 metrics
top_3_metrics = pred_df.head(3)['Metric'].tolist()

print(f"\nRolling Correlations with Daily_Return (5-day and 10-day windows):")
print(f"Top 3 Metrics: {', '.join(top_3_metrics)}")

for window in [5, 10]:
    print(f"\n{window}-day Rolling Window:")
    print("-" * 80)

    for metric in top_3_metrics:
        rolling_corr = df_clean['Daily_Return'].rolling(window).corr(df_clean[metric])
        mean_corr = rolling_corr.mean()
        std_corr = rolling_corr.std()
        min_corr = rolling_corr.min()
        max_corr = rolling_corr.max()

        print(f"{metric:<25} Mean: {mean_corr:>7.4f}  Std: {std_corr:>7.4f}  Range: [{min_corr:>7.4f}, {max_corr:>7.4f}]")

print("\n" + "="*80)
print("6. CONFIDENCE INTERVALS")
print("="*80)

# Calculate 95% confidence intervals for key correlations
print("\n95% Confidence Intervals for Correlations with Daily_Return:")
print("-" * 80)
print(f"{'Metric':<25} {'Correlation':>12} {'95% CI Lower':>15} {'95% CI Upper':>15}")
print("-" * 80)

for metric in daily_return_corr.index[:10]:  # Top 10
    r = daily_return_corr[metric]
    n = len(df_clean)

    # Fisher's Z transformation for confidence interval
    z = 0.5 * np.log((1 + r) / (1 - r))
    se = 1 / np.sqrt(n - 3)
    z_lower = z - 1.96 * se
    z_upper = z + 1.96 * se

    # Transform back
    r_lower = (np.exp(2 * z_lower) - 1) / (np.exp(2 * z_lower) + 1)
    r_upper = (np.exp(2 * z_upper) - 1) / (np.exp(2 * z_upper) + 1)

    print(f"{metric:<25} {r:>12.4f} {r_lower:>15.4f} {r_upper:>15.4f}")

print("\n" + "="*80)
print("7. MULTI-METRIC PREDICTIVE COMBINATIONS")
print("="*80)

# Test combinations of metrics for best predictive power
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

print("\nMulti-Metric Linear Regression Analysis:")
print("Testing combinations of metrics to predict Daily_Return")
print("-" * 80)

# Prepare data (use lagged values to avoid look-ahead bias)
X_data = df_clean[['AD_Ratio', 'Market_Breadth', 'Volume_Ratio', 'RSI_14', 'MACD']].shift(1).dropna()
y_data = df_clean['Daily_Return'].loc[X_data.index]

# Split into train/test
split_idx = int(len(X_data) * 0.7)
X_train, X_test = X_data.iloc[:split_idx], X_data.iloc[split_idx:]
y_train, y_test = y_data.iloc[:split_idx], y_data.iloc[split_idx:]

# Fit model
model = LinearRegression()
model.fit(X_train, y_train)

# Predictions
y_pred_train = model.predict(X_train)
y_pred_test = model.predict(X_test)

r2_train = r2_score(y_train, y_pred_train)
r2_test = r2_score(y_test, y_pred_test)

print(f"\nLinear Regression Results:")
print(f"Training R²: {r2_train:.4f}")
print(f"Testing R²: {r2_test:.4f}")
print(f"\nFeature Importance (Coefficients):")
for feature, coef in zip(X_data.columns, model.coef_):
    print(f"  {feature:<20}: {coef:>10.6f}")

print("\n" + "="*80)
print("8. ACTIONABLE INSIGHTS")
print("="*80)

print("\n🎯 KEY FINDINGS:")
print("-" * 80)

# Best single predictor
best_predictor = pred_df.iloc[0]
print(f"\n1. BEST SINGLE PREDICTOR:")
print(f"   Metric: {best_predictor['Metric']}")
print(f"   1-Day Ahead Correlation: {best_predictor['Correlation']:.4f}")
print(f"   Statistical Significance: p = {best_predictor['P-value']:.6f}")
if best_predictor['P-value'] < 0.05:
    print(f"   ✓ Statistically significant (p < 0.05)")
else:
    print(f"   ✗ NOT statistically significant (p >= 0.05)")

# Strongest contemporaneous correlations
print(f"\n2. STRONGEST CONTEMPORANEOUS CORRELATIONS WITH RETURNS:")
top_3_contemp = daily_return_corr.head(3)
for i, (metric, corr) in enumerate(top_3_contemp.items(), 1):
    print(f"   {i}. {metric}: r = {corr:.4f} (p = {daily_return_pvals[metric]:.6f})")

# Reliability assessment
print(f"\n3. RELIABILITY ASSESSMENT:")
print(f"   Sample Size: {len(df_clean)} trading days")
if len(df_clean) < 30:
    print(f"   ⚠ WARNING: Small sample size - correlations may be unstable")
elif len(df_clean) < 100:
    print(f"   ⚠ CAUTION: Moderate sample size - use with care")
else:
    print(f"   ✓ Good sample size for reliable correlation estimates")

# Multicollinearity warning
print(f"\n4. MULTICOLLINEARITY CHECK:")
high_corr_count = len([p for p in strong_corr_pairs if p['Metric 1'] != 'Daily_Return' and p['Metric 2'] != 'Daily_Return'])
if high_corr_count > 0:
    print(f"   ⚠ Found {high_corr_count} pairs of non-return metrics with |r| > 0.7")
    print(f"   → Avoid using highly correlated metrics together in models")

# Trading signal recommendations
print(f"\n5. TRADING SIGNAL RECOMMENDATIONS:")
significant_predictors = pred_df[pred_df['P-value'] < 0.05]
if len(significant_predictors) > 0:
    print(f"   ✓ {len(significant_predictors)} metrics show significant predictive power")
    print(f"   → Consider using: {', '.join(significant_predictors.head(3)['Metric'].tolist())}")
else:
    print(f"   ✗ No metrics show statistically significant predictive power")
    print(f"   → Market may be efficient or sample size too small")

print("\n" + "="*80)
print("9. VISUALIZATION DATA EXPORT")
print("="*80)

# Export correlation matrix for heatmap
corr_matrix.to_csv('correlation_matrix.csv')
print(f"\n✓ Correlation matrix saved to: correlation_matrix.csv")

# Export scatter plot data for top 3 correlations
print(f"\n✓ Scatter plot data for top 3 correlations:")
for i, metric in enumerate(top_3_metrics, 1):
    scatter_data = df_clean[['Daily_Return', metric]].copy()
    scatter_data.to_csv(f'scatter_data_{i}_{metric}.csv', index=False)
    print(f"   {i}. {metric} vs Daily_Return → scatter_data_{i}_{metric}.csv")

# Export rolling correlation data
print(f"\n✓ Rolling correlation data:")
for metric in top_3_metrics:
    rolling_5d = df_clean['Daily_Return'].rolling(5).corr(df_clean[metric])
    rolling_10d = df_clean['Daily_Return'].rolling(10).corr(df_clean[metric])

    rolling_df = pd.DataFrame({
        'Date': df_clean['Date'],
        'Rolling_5D': rolling_5d,
        'Rolling_10D': rolling_10d
    })
    rolling_df.to_csv(f'rolling_corr_{metric}.csv', index=False)
    print(f"   {metric} → rolling_corr_{metric}.csv")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
print(f"\nTotal metrics analyzed: {len(metrics)}")
print(f"Total correlation pairs: {len(metrics) * (len(metrics) - 1) // 2}")
print(f"Strong correlations found: {len(strong_corr_pairs)}")
print(f"Moderate correlations found: {len(moderate_corr_pairs)}")
print(f"\nAll output files saved to current directory.")
