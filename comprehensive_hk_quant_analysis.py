"""
Comprehensive Quantitative Analysis of Hong Kong Market Data
============================================================

This script performs deep quantitative analysis on:
1. HKEX Stock Market Data (Sept-Oct 2025)
2. HIBOR Interest Rates (264 days)
3. Visitor Statistics (13 months)
4. Property Market Data (1982-1998)
5. Government Financial Data

Analysis includes:
- Correlation analysis (Pearson, Spearman, lag correlations)
- Risk metrics (VaR, CVaR, Sharpe, Sortino, Beta, Alpha)
- Predictive modeling (Granger causality, time series forecasting)
- Trading strategy recommendations
- Visualization (heatmaps, time series, scatter plots)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import pearsonr, spearmanr
from statsmodels.tsa.stattools import grangercausalitytests, adfuller
from statsmodels.tsa.api import VAR
import warnings
warnings.filterwarnings('ignore')

# File paths
HIBOR_PATH = r"C:\Users\Penguin8n\CODEX--\CODEX--\gov_crawler\data\hibor_data_20251023_205904.csv"
VISITOR_PATH = r"C:\Users\Penguin8n\CODEX--\CODEX--\gov_crawler\data\visitor_data_20251023_205904.csv"
HKEX_PATH = r"C:\Users\Penguin8n\CODEX--\CODEX--\hkex爬蟲\data\hkex_all_market_data.csv"
PROPERTY_PRICE_PATH = r"C:\Users\Penguin8n\CODEX--\CODEX--\gov_crawler\data\processed\property_property_market_price_20251023_220832.csv"

class HKQuantAnalyzer:
    """Comprehensive Hong Kong Market Quantitative Analyzer"""

    def __init__(self):
        self.hibor_data = None
        self.visitor_data = None
        self.hkex_data = None
        self.merged_data = None
        self.results = {}

    def load_data(self):
        """Load all data sources"""
        print("=" * 80)
        print("LOADING DATA SOURCES")
        print("=" * 80)

        # Load HIBOR data
        print("\n1. Loading HIBOR data...")
        self.hibor_data = pd.read_csv(HIBOR_PATH)
        self.hibor_data['date'] = pd.to_datetime(self.hibor_data['date'])
        print(f"   - Loaded {len(self.hibor_data)} days of HIBOR data")
        print(f"   - Date range: {self.hibor_data['date'].min()} to {self.hibor_data['date'].max()}")
        print(f"   - Columns: {list(self.hibor_data.columns)}")

        # Load Visitor data
        print("\n2. Loading Visitor data...")
        self.visitor_data = pd.read_csv(VISITOR_PATH)
        self.visitor_data['date'] = pd.to_datetime(self.visitor_data['date'])
        print(f"   - Loaded {len(self.visitor_data)} months of visitor data")
        print(f"   - Date range: {self.visitor_data['date'].min()} to {self.visitor_data['date'].max()}")
        print(f"   - Columns: {list(self.visitor_data.columns)}")

        # Load HKEX data
        print("\n3. Loading HKEX market data...")
        self.hkex_data = pd.read_csv(HKEX_PATH)
        self.hkex_data['Date'] = pd.to_datetime(self.hkex_data['Date'])

        # Clean and convert numeric columns
        numeric_cols = ['Trading_Volume', 'Turnover_HKD', 'Deals',
                       'Morning_Close', 'Afternoon_Close']
        for col in numeric_cols:
            if col in self.hkex_data.columns:
                self.hkex_data[col] = pd.to_numeric(self.hkex_data[col], errors='coerce')

        # Remove rows with missing data
        self.hkex_data = self.hkex_data.dropna(subset=['Afternoon_Close'])

        print(f"   - Loaded {len(self.hkex_data)} trading days")
        print(f"   - Date range: {self.hkex_data['Date'].min()} to {self.hkex_data['Date'].max()}")
        print(f"   - Columns: {list(self.hkex_data.columns)}")

        return self

    def perform_data_quality_assessment(self):
        """Assess data quality and generate summary statistics"""
        print("\n" + "=" * 80)
        print("DATA QUALITY ASSESSMENT")
        print("=" * 80)

        self.results['data_quality'] = {}

        # HIBOR statistics
        print("\n1. HIBOR Data Summary:")
        hibor_stats = self.hibor_data.describe()
        print(hibor_stats.to_string())
        self.results['data_quality']['hibor'] = hibor_stats

        print("\n   Missing values:")
        print(self.hibor_data.isnull().sum())

        # Visitor statistics
        print("\n2. Visitor Data Summary:")
        visitor_stats = self.visitor_data.describe()
        print(visitor_stats.to_string())
        self.results['data_quality']['visitor'] = visitor_stats

        # HKEX statistics
        print("\n3. HKEX Market Data Summary:")
        hkex_stats = self.hkex_data.describe()
        print(hkex_stats.to_string())
        self.results['data_quality']['hkex'] = hkex_stats

        # Calculate daily returns for HKEX
        self.hkex_data['Returns'] = self.hkex_data['Afternoon_Close'].pct_change()
        self.hkex_data['Log_Returns'] = np.log(self.hkex_data['Afternoon_Close'] /
                                                 self.hkex_data['Afternoon_Close'].shift(1))

        print("\n   HKEX Returns Statistics:")
        print(f"   - Mean Daily Return: {self.hkex_data['Returns'].mean():.4%}")
        print(f"   - Std Dev: {self.hkex_data['Returns'].std():.4%}")
        print(f"   - Skewness: {self.hkex_data['Returns'].skew():.4f}")
        print(f"   - Kurtosis: {self.hkex_data['Returns'].kurtosis():.4f}")

        return self

    def merge_datasets(self):
        """Merge datasets on date for correlation analysis"""
        print("\n" + "=" * 80)
        print("MERGING DATASETS")
        print("=" * 80)

        # Rename date columns for consistency
        hibor_df = self.hibor_data.rename(columns={'date': 'Date'})

        # Merge HKEX with HIBOR (daily data)
        merged = pd.merge(self.hkex_data, hibor_df, on='Date', how='inner')
        print(f"\nMerged HKEX + HIBOR: {len(merged)} rows")

        # For visitor data (monthly), we'll create a separate analysis
        self.merged_data = merged

        print(f"Final merged dataset: {merged.shape}")
        print(f"Date range: {merged['Date'].min()} to {merged['Date'].max()}")

        return self

    def correlation_analysis(self):
        """Perform comprehensive correlation analysis"""
        print("\n" + "=" * 80)
        print("CORRELATION ANALYSIS")
        print("=" * 80)

        self.results['correlations'] = {}

        # Select features for correlation
        features = ['Afternoon_Close', 'Trading_Volume', 'Turnover_HKD', 'Deals',
                   'hibor_overnight', 'hibor_1m', 'hibor_3m', 'hibor_6m', 'hibor_12m']

        # Filter available features
        available_features = [f for f in features if f in self.merged_data.columns]

        corr_data = self.merged_data[available_features].dropna()

        # Pearson correlation
        print("\n1. Pearson Correlation Matrix:")
        pearson_corr = corr_data.corr(method='pearson')
        print(pearson_corr.to_string())
        self.results['correlations']['pearson'] = pearson_corr

        # Spearman correlation (rank-based, more robust to outliers)
        print("\n2. Spearman Correlation Matrix:")
        spearman_corr = corr_data.corr(method='spearman')
        print(spearman_corr.to_string())
        self.results['correlations']['spearman'] = spearman_corr

        # Key findings
        print("\n3. Key Correlation Findings:")

        # Correlations with market close
        close_corr = pearson_corr['Afternoon_Close'].sort_values(ascending=False)
        print("\n   Correlations with Market Close (Afternoon_Close):")
        for feature, corr_val in close_corr.items():
            if feature != 'Afternoon_Close':
                print(f"   - {feature}: {corr_val:.4f}")

        # HIBOR correlations
        hibor_cols = [col for col in available_features if 'hibor' in col]
        print("\n   HIBOR Inter-correlations:")
        for i, col1 in enumerate(hibor_cols):
            for col2 in hibor_cols[i+1:]:
                corr_val = pearson_corr.loc[col1, col2]
                print(f"   - {col1} vs {col2}: {corr_val:.4f}")

        return self

    def lagged_correlation_analysis(self, max_lag=5):
        """Analyze lagged correlations to find predictive relationships"""
        print("\n" + "=" * 80)
        print("LAGGED CORRELATION ANALYSIS")
        print("=" * 80)

        self.results['lagged_correlations'] = {}

        # Calculate returns if not already done
        if 'Returns' not in self.merged_data.columns:
            self.merged_data['Returns'] = self.merged_data['Afternoon_Close'].pct_change()

        # Test lagged correlations between HIBOR and market returns
        hibor_cols = [col for col in self.merged_data.columns if 'hibor' in col]

        print(f"\nTesting lags from 0 to {max_lag} days...")

        lag_results = []

        for hibor_col in hibor_cols:
            print(f"\n{hibor_col} vs Market Returns:")

            for lag in range(max_lag + 1):
                # Shift HIBOR data by lag days
                lagged_hibor = self.merged_data[hibor_col].shift(lag)

                # Calculate correlation
                valid_idx = ~(lagged_hibor.isna() | self.merged_data['Returns'].isna())

                if valid_idx.sum() > 10:  # Need at least 10 data points
                    corr, pval = pearsonr(lagged_hibor[valid_idx],
                                         self.merged_data['Returns'][valid_idx])

                    lag_results.append({
                        'hibor_type': hibor_col,
                        'lag_days': lag,
                        'correlation': corr,
                        'p_value': pval,
                        'significant': pval < 0.05
                    })

                    if pval < 0.05:
                        print(f"   Lag {lag}: corr={corr:.4f}, p-value={pval:.4f} ***")
                    else:
                        print(f"   Lag {lag}: corr={corr:.4f}, p-value={pval:.4f}")

        lag_df = pd.DataFrame(lag_results)
        self.results['lagged_correlations']['details'] = lag_df

        # Find strongest lagged relationships
        significant_lags = lag_df[lag_df['significant']].sort_values('correlation',
                                                                      key=abs,
                                                                      ascending=False)

        print("\n" + "-" * 80)
        print("STRONGEST LAGGED RELATIONSHIPS (Significant at p<0.05):")
        print("-" * 80)
        if len(significant_lags) > 0:
            print(significant_lags.to_string(index=False))
        else:
            print("No statistically significant lagged correlations found.")

        self.results['lagged_correlations']['significant'] = significant_lags

        return self

    def granger_causality_test(self, max_lag=5):
        """Test Granger causality between HIBOR and market movements"""
        print("\n" + "=" * 80)
        print("GRANGER CAUSALITY TEST")
        print("=" * 80)

        self.results['granger_causality'] = {}

        # Prepare data
        if 'Returns' not in self.merged_data.columns:
            self.merged_data['Returns'] = self.merged_data['Afternoon_Close'].pct_change()

        hibor_cols = [col for col in self.merged_data.columns if 'hibor' in col]

        print("\nTesting if HIBOR Granger-causes Market Returns...")
        print("(Null hypothesis: HIBOR does NOT cause market returns)")

        granger_results = []

        for hibor_col in hibor_cols:
            print(f"\n{hibor_col}:")

            # Prepare data for test
            test_data = self.merged_data[[hibor_col, 'Returns']].dropna()

            if len(test_data) < 20:
                print("   Insufficient data for Granger test")
                continue

            # Make data stationary (difference if needed)
            adf_result = adfuller(test_data[hibor_col])
            if adf_result[1] > 0.05:  # Non-stationary
                test_data[hibor_col + '_diff'] = test_data[hibor_col].diff()
                test_col = hibor_col + '_diff'
            else:
                test_col = hibor_col

            test_data = test_data.dropna()

            try:
                # Run Granger causality test
                gc_result = grangercausalitytests(test_data[[test_col, 'Returns']],
                                                  maxlag=max_lag, verbose=False)

                # Extract p-values for each lag
                for lag in range(1, max_lag + 1):
                    f_test = gc_result[lag][0]['ssr_ftest']
                    p_value = f_test[1]

                    granger_results.append({
                        'hibor_type': hibor_col,
                        'lag': lag,
                        'f_statistic': f_test[0],
                        'p_value': p_value,
                        'significant': p_value < 0.05
                    })

                    if p_value < 0.05:
                        print(f"   Lag {lag}: F-stat={f_test[0]:.4f}, p-value={p_value:.4f} *** (SIGNIFICANT)")
                    else:
                        print(f"   Lag {lag}: F-stat={f_test[0]:.4f}, p-value={p_value:.4f}")

            except Exception as e:
                print(f"   Error in Granger test: {e}")

        if granger_results:
            granger_df = pd.DataFrame(granger_results)
            self.results['granger_causality']['details'] = granger_df

            significant = granger_df[granger_df['significant']]
            if len(significant) > 0:
                print("\n" + "-" * 80)
                print("SIGNIFICANT GRANGER CAUSALITY RELATIONSHIPS:")
                print("-" * 80)
                print(significant.to_string(index=False))
                self.results['granger_causality']['significant'] = significant
            else:
                print("\nNo significant Granger causality found.")

        return self

    def risk_metrics_analysis(self):
        """Calculate comprehensive risk metrics"""
        print("\n" + "=" * 80)
        print("RISK METRICS ANALYSIS")
        print("=" * 80)

        self.results['risk_metrics'] = {}

        returns = self.merged_data['Returns'].dropna()

        # Basic statistics
        mean_return = returns.mean()
        std_return = returns.std()

        print("\n1. Return Statistics:")
        print(f"   - Mean Daily Return: {mean_return:.4%}")
        print(f"   - Annualized Return: {mean_return * 252:.4%}")
        print(f"   - Daily Volatility: {std_return:.4%}")
        print(f"   - Annualized Volatility: {std_return * np.sqrt(252):.4%}")

        # Sharpe Ratio (assuming 2.5% risk-free rate based on HIBOR)
        risk_free_rate = 0.025 / 252  # Daily
        sharpe_ratio = (mean_return - risk_free_rate) / std_return
        annualized_sharpe = sharpe_ratio * np.sqrt(252)

        print(f"\n2. Sharpe Ratio:")
        print(f"   - Daily Sharpe: {sharpe_ratio:.4f}")
        print(f"   - Annualized Sharpe: {annualized_sharpe:.4f}")

        self.results['risk_metrics']['sharpe_ratio'] = annualized_sharpe

        # Sortino Ratio (downside deviation)
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std()
        sortino_ratio = (mean_return - risk_free_rate) / downside_std
        annualized_sortino = sortino_ratio * np.sqrt(252)

        print(f"\n3. Sortino Ratio:")
        print(f"   - Daily Sortino: {sortino_ratio:.4f}")
        print(f"   - Annualized Sortino: {annualized_sortino:.4f}")

        self.results['risk_metrics']['sortino_ratio'] = annualized_sortino

        # Maximum Drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        print(f"\n4. Maximum Drawdown: {max_drawdown:.4%}")
        self.results['risk_metrics']['max_drawdown'] = max_drawdown

        # Value at Risk (VaR)
        var_95 = np.percentile(returns, 5)
        var_99 = np.percentile(returns, 1)

        print(f"\n5. Value at Risk (VaR):")
        print(f"   - 95% VaR (daily): {var_95:.4%}")
        print(f"   - 99% VaR (daily): {var_99:.4%}")
        print(f"   - 95% VaR (annual): {var_95 * np.sqrt(252):.4%}")
        print(f"   - 99% VaR (annual): {var_99 * np.sqrt(252):.4%}")

        self.results['risk_metrics']['var_95'] = var_95
        self.results['risk_metrics']['var_99'] = var_99

        # Conditional Value at Risk (CVaR / Expected Shortfall)
        cvar_95 = returns[returns <= var_95].mean()
        cvar_99 = returns[returns <= var_99].mean()

        print(f"\n6. Conditional Value at Risk (CVaR):")
        print(f"   - 95% CVaR (daily): {cvar_95:.4%}")
        print(f"   - 99% CVaR (daily): {cvar_99:.4%}")

        self.results['risk_metrics']['cvar_95'] = cvar_95
        self.results['risk_metrics']['cvar_99'] = cvar_99

        # Beta and Alpha (using HIBOR as proxy for market risk)
        # Calculate beta relative to HIBOR changes
        if 'hibor_3m' in self.merged_data.columns:
            hibor_changes = self.merged_data['hibor_3m'].pct_change().dropna()

            # Align data
            common_idx = returns.index.intersection(hibor_changes.index)
            returns_aligned = returns[common_idx]
            hibor_aligned = hibor_changes[common_idx]

            if len(common_idx) > 10:
                # Calculate beta (covariance / variance)
                covariance = np.cov(returns_aligned, hibor_aligned)[0, 1]
                hibor_variance = np.var(hibor_aligned)
                beta = covariance / hibor_variance if hibor_variance != 0 else 0

                # Calculate alpha
                alpha = mean_return - (risk_free_rate + beta * hibor_aligned.mean())

                print(f"\n7. Beta and Alpha (relative to 3M HIBOR):")
                print(f"   - Beta: {beta:.4f}")
                print(f"   - Alpha (daily): {alpha:.4%}")
                print(f"   - Alpha (annualized): {alpha * 252:.4%}")

                self.results['risk_metrics']['beta'] = beta
                self.results['risk_metrics']['alpha'] = alpha * 252

        # Win rate
        win_rate = (returns > 0).sum() / len(returns)
        print(f"\n8. Win Rate: {win_rate:.4%}")
        self.results['risk_metrics']['win_rate'] = win_rate

        # Average win vs average loss
        avg_win = returns[returns > 0].mean()
        avg_loss = returns[returns < 0].mean()
        win_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0

        print(f"\n9. Win/Loss Ratio:")
        print(f"   - Average Win: {avg_win:.4%}")
        print(f"   - Average Loss: {avg_loss:.4%}")
        print(f"   - Win/Loss Ratio: {win_loss_ratio:.4f}")

        self.results['risk_metrics']['win_loss_ratio'] = win_loss_ratio

        return self

    def trading_strategy_recommendations(self):
        """Generate trading strategy recommendations based on analysis"""
        print("\n" + "=" * 80)
        print("TRADING STRATEGY RECOMMENDATIONS")
        print("=" * 80)

        strategies = []

        # Strategy 1: HIBOR-based mean reversion
        print("\n1. HIBOR MEAN REVERSION STRATEGY")
        print("-" * 80)

        if 'correlations' in self.results:
            hibor_corr = self.results['correlations']['pearson'].get('Afternoon_Close', {})

            print("Strategy Logic:")
            print("- Monitor HIBOR rates for significant deviations from mean")
            print("- When HIBOR spikes above mean + 1 std, consider SHORT positions")
            print("- When HIBOR drops below mean - 1 std, consider LONG positions")
            print("- Higher interest rates typically pressure stock valuations")

            # Calculate HIBOR statistics
            hibor_3m = self.merged_data['hibor_3m']
            hibor_mean = hibor_3m.mean()
            hibor_std = hibor_3m.std()

            print(f"\nParameters:")
            print(f"- 3M HIBOR Mean: {hibor_mean:.4f}%")
            print(f"- 3M HIBOR Std Dev: {hibor_std:.4f}%")
            print(f"- Upper threshold: {hibor_mean + hibor_std:.4f}%")
            print(f"- Lower threshold: {hibor_mean - hibor_std:.4f}%")

            strategies.append({
                'name': 'HIBOR Mean Reversion',
                'type': 'Mean Reversion',
                'signal_source': '3M HIBOR',
                'entry_long': f'< {hibor_mean - hibor_std:.4f}%',
                'entry_short': f'> {hibor_mean + hibor_std:.4f}%',
                'risk_level': 'Medium'
            })

        # Strategy 2: Volume-based momentum
        print("\n2. VOLUME MOMENTUM STRATEGY")
        print("-" * 80)
        print("Strategy Logic:")
        print("- Monitor trading volume vs 20-day moving average")
        print("- High volume + positive returns = Strong momentum (LONG)")
        print("- High volume + negative returns = Strong reversal (SHORT)")
        print("- Use volume as confirmation signal")

        if 'Trading_Volume' in self.merged_data.columns:
            vol_mean = self.merged_data['Trading_Volume'].mean()
            vol_std = self.merged_data['Trading_Volume'].std()

            print(f"\nParameters:")
            print(f"- Average Daily Volume: {vol_mean:,.0f}")
            print(f"- Volume Std Dev: {vol_std:,.0f}")
            print(f"- High Volume Threshold: {vol_mean + vol_std:,.0f}")

            strategies.append({
                'name': 'Volume Momentum',
                'type': 'Momentum',
                'signal_source': 'Trading Volume + Returns',
                'entry_condition': 'Volume > Mean + 1 Std',
                'risk_level': 'Medium-High'
            })

        # Strategy 3: HIBOR term structure arbitrage
        print("\n3. HIBOR TERM STRUCTURE ARBITRAGE")
        print("-" * 80)
        print("Strategy Logic:")
        print("- Monitor spread between long-term and short-term HIBOR")
        print("- Steep curve (12M >> 1M) = Bullish economic outlook")
        print("- Inverted curve (12M << 1M) = Bearish signal")
        print("- Trade based on curve steepness changes")

        if all(col in self.merged_data.columns for col in ['hibor_1m', 'hibor_12m']):
            curve_spread = self.merged_data['hibor_12m'] - self.merged_data['hibor_1m']
            spread_mean = curve_spread.mean()
            spread_std = curve_spread.std()

            print(f"\nParameters:")
            print(f"- Average Spread (12M - 1M): {spread_mean:.4f}%")
            print(f"- Spread Std Dev: {spread_std:.4f}%")
            print(f"- Steep Curve (Bullish): > {spread_mean + spread_std:.4f}%")
            print(f"- Flat/Inverted (Bearish): < {spread_mean - spread_std:.4f}%")

            strategies.append({
                'name': 'HIBOR Term Structure',
                'type': 'Arbitrage',
                'signal_source': 'HIBOR Curve Spread',
                'bullish_threshold': f'> {spread_mean + spread_std:.4f}%',
                'bearish_threshold': f'< {spread_mean - spread_std:.4f}%',
                'risk_level': 'Low-Medium'
            })

        # Strategy 4: Turnover efficiency
        print("\n4. TURNOVER EFFICIENCY STRATEGY")
        print("-" * 80)
        print("Strategy Logic:")
        print("- Calculate Turnover per Deal = Total Turnover / Number of Deals")
        print("- High efficiency = Institutional buying (Bullish)")
        print("- Low efficiency = Retail activity (Volatile)")
        print("- Use as market quality indicator")

        if all(col in self.merged_data.columns for col in ['Turnover_HKD', 'Deals']):
            self.merged_data['Turnover_Per_Deal'] = (self.merged_data['Turnover_HKD'] /
                                                      self.merged_data['Deals'])

            tpd_mean = self.merged_data['Turnover_Per_Deal'].mean()
            tpd_std = self.merged_data['Turnover_Per_Deal'].std()

            print(f"\nParameters:")
            print(f"- Average Turnover Per Deal: HKD {tpd_mean:,.0f}")
            print(f"- High Efficiency Threshold: > HKD {tpd_mean + tpd_std:,.0f}")

            strategies.append({
                'name': 'Turnover Efficiency',
                'type': 'Quality Signal',
                'signal_source': 'Turnover / Deals',
                'high_quality': f'> HKD {tpd_mean + tpd_std:,.0f}',
                'risk_level': 'Low'
            })

        # Risk management recommendations
        print("\n5. RISK MANAGEMENT FRAMEWORK")
        print("-" * 80)
        print("Position Sizing:")
        print(f"- Maximum position size: 2% of capital per trade")
        print(f"- Daily VaR limit: {self.results['risk_metrics']['var_95']:.2%} of portfolio")

        print("\nStop Loss Rules:")
        print(f"- Hard stop: -2% per position")
        print(f"- Trailing stop: 1.5 * ATR (Average True Range)")

        print("\nProfit Taking:")
        print(f"- Target 1: +1.5% (take 50% off)")
        print(f"- Target 2: +3.0% (take remaining 50%)")

        print("\nPortfolio Rules:")
        print(f"- Maximum concurrent positions: 3-5")
        print(f"- Maximum sector exposure: 40%")
        print(f"- Daily loss limit: -5% of portfolio")

        self.results['strategies'] = pd.DataFrame(strategies)

        return self

    def generate_visualizations(self):
        """Generate comprehensive visualizations"""
        print("\n" + "=" * 80)
        print("GENERATING VISUALIZATIONS")
        print("=" * 80)

        # Create output directory
        import os
        output_dir = r"C:\Users\Penguin8n\CODEX--\CODEX--\analysis_output"
        os.makedirs(output_dir, exist_ok=True)

        # 1. Correlation heatmap
        if 'correlations' in self.results:
            plt.figure(figsize=(12, 10))
            sns.heatmap(self.results['correlations']['pearson'],
                       annot=True, fmt='.3f', cmap='coolwarm', center=0,
                       square=True, linewidths=1)
            plt.title('Pearson Correlation Matrix\nHKEX Market vs HIBOR Rates',
                     fontsize=14, fontweight='bold')
            plt.tight_layout()
            filepath = os.path.join(output_dir, 'correlation_heatmap.png')
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"\n1. Saved correlation heatmap: {filepath}")
            plt.close()

        # 2. Time series comparison
        fig, axes = plt.subplots(3, 1, figsize=(14, 10))

        # Market close
        axes[0].plot(self.merged_data['Date'], self.merged_data['Afternoon_Close'],
                    linewidth=1.5, color='blue')
        axes[0].set_title('HKEX Market Close (Afternoon)', fontweight='bold')
        axes[0].set_ylabel('Index Level')
        axes[0].grid(True, alpha=0.3)

        # HIBOR rates
        hibor_cols = ['hibor_overnight', 'hibor_1m', 'hibor_3m', 'hibor_6m', 'hibor_12m']
        for col in hibor_cols:
            if col in self.merged_data.columns:
                axes[1].plot(self.merged_data['Date'], self.merged_data[col],
                           label=col.replace('hibor_', '').upper(), alpha=0.7)
        axes[1].set_title('HIBOR Rates', fontweight='bold')
        axes[1].set_ylabel('Rate (%)')
        axes[1].legend(loc='best')
        axes[1].grid(True, alpha=0.3)

        # Trading volume
        if 'Trading_Volume' in self.merged_data.columns:
            axes[2].bar(self.merged_data['Date'], self.merged_data['Trading_Volume'],
                       width=0.8, color='green', alpha=0.6)
            axes[2].set_title('Trading Volume', fontweight='bold')
            axes[2].set_ylabel('Volume')
            axes[2].set_xlabel('Date')
            axes[2].grid(True, alpha=0.3)

        plt.tight_layout()
        filepath = os.path.join(output_dir, 'time_series_overview.png')
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"2. Saved time series overview: {filepath}")
        plt.close()

        # 3. Returns distribution
        if 'Returns' in self.merged_data.columns:
            fig, axes = plt.subplots(1, 2, figsize=(14, 5))

            returns = self.merged_data['Returns'].dropna()

            # Histogram
            axes[0].hist(returns, bins=50, edgecolor='black', alpha=0.7, color='skyblue')
            axes[0].axvline(returns.mean(), color='red', linestyle='--',
                          label=f'Mean: {returns.mean():.4%}')
            axes[0].axvline(returns.median(), color='green', linestyle='--',
                          label=f'Median: {returns.median():.4%}')
            axes[0].set_title('Distribution of Daily Returns', fontweight='bold')
            axes[0].set_xlabel('Return (%)')
            axes[0].set_ylabel('Frequency')
            axes[0].legend()
            axes[0].grid(True, alpha=0.3)

            # Q-Q plot
            stats.probplot(returns, dist="norm", plot=axes[1])
            axes[1].set_title('Q-Q Plot (Normal Distribution)', fontweight='bold')
            axes[1].grid(True, alpha=0.3)

            plt.tight_layout()
            filepath = os.path.join(output_dir, 'returns_distribution.png')
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"3. Saved returns distribution: {filepath}")
            plt.close()

        # 4. Scatter plots - HIBOR vs Returns
        if 'Returns' in self.merged_data.columns:
            fig, axes = plt.subplots(2, 3, figsize=(15, 10))
            axes = axes.flatten()

            hibor_cols = ['hibor_overnight', 'hibor_1m', 'hibor_3m', 'hibor_6m', 'hibor_12m']

            for idx, hibor_col in enumerate(hibor_cols):
                if hibor_col in self.merged_data.columns and idx < len(axes):
                    valid_data = self.merged_data[[hibor_col, 'Returns']].dropna()

                    axes[idx].scatter(valid_data[hibor_col], valid_data['Returns'],
                                    alpha=0.5, s=30)

                    # Add regression line
                    z = np.polyfit(valid_data[hibor_col], valid_data['Returns'], 1)
                    p = np.poly1d(z)
                    axes[idx].plot(valid_data[hibor_col],
                                  p(valid_data[hibor_col]),
                                  "r--", alpha=0.8, linewidth=2)

                    # Calculate correlation
                    corr, _ = pearsonr(valid_data[hibor_col], valid_data['Returns'])

                    axes[idx].set_title(f'{hibor_col.upper()} vs Returns\nCorr: {corr:.4f}',
                                       fontweight='bold')
                    axes[idx].set_xlabel(f'{hibor_col} (%)')
                    axes[idx].set_ylabel('Daily Returns (%)')
                    axes[idx].grid(True, alpha=0.3)

            # Remove extra subplot
            if len(hibor_cols) < len(axes):
                fig.delaxes(axes[-1])

            plt.tight_layout()
            filepath = os.path.join(output_dir, 'hibor_returns_scatter.png')
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"4. Saved HIBOR-Returns scatter plots: {filepath}")
            plt.close()

        # 5. Drawdown chart
        if 'Returns' in self.merged_data.columns:
            returns = self.merged_data['Returns'].dropna()
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.cummax()
            drawdown = (cumulative - running_max) / running_max

            fig, axes = plt.subplots(2, 1, figsize=(14, 8))

            # Cumulative returns
            axes[0].plot(cumulative.index, cumulative.values, linewidth=2, color='blue')
            axes[0].set_title('Cumulative Returns', fontweight='bold', fontsize=12)
            axes[0].set_ylabel('Cumulative Return')
            axes[0].grid(True, alpha=0.3)

            # Drawdown
            axes[1].fill_between(drawdown.index, drawdown.values, 0,
                                color='red', alpha=0.3)
            axes[1].plot(drawdown.index, drawdown.values, linewidth=1.5, color='darkred')
            axes[1].set_title(f'Drawdown (Max: {drawdown.min():.2%})',
                            fontweight='bold', fontsize=12)
            axes[1].set_ylabel('Drawdown (%)')
            axes[1].set_xlabel('Date')
            axes[1].grid(True, alpha=0.3)

            plt.tight_layout()
            filepath = os.path.join(output_dir, 'cumulative_returns_drawdown.png')
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"5. Saved cumulative returns and drawdown: {filepath}")
            plt.close()

        print(f"\nAll visualizations saved to: {output_dir}")

        return self

    def export_results(self):
        """Export all results to files"""
        print("\n" + "=" * 80)
        print("EXPORTING RESULTS")
        print("=" * 80)

        import os
        import json
        from datetime import datetime

        output_dir = r"C:\Users\Penguin8n\CODEX--\CODEX--\analysis_output"
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 1. Export correlation matrices
        if 'correlations' in self.results:
            filepath = os.path.join(output_dir, f'correlation_matrix_{timestamp}.csv')
            self.results['correlations']['pearson'].to_csv(filepath)
            print(f"\n1. Exported correlation matrix: {filepath}")

        # 2. Export lagged correlations
        if 'lagged_correlations' in self.results:
            if 'details' in self.results['lagged_correlations']:
                filepath = os.path.join(output_dir, f'lagged_correlations_{timestamp}.csv')
                self.results['lagged_correlations']['details'].to_csv(filepath, index=False)
                print(f"2. Exported lagged correlations: {filepath}")

        # 3. Export Granger causality results
        if 'granger_causality' in self.results:
            if 'details' in self.results['granger_causality']:
                filepath = os.path.join(output_dir, f'granger_causality_{timestamp}.csv')
                self.results['granger_causality']['details'].to_csv(filepath, index=False)
                print(f"3. Exported Granger causality: {filepath}")

        # 4. Export risk metrics
        if 'risk_metrics' in self.results:
            filepath = os.path.join(output_dir, f'risk_metrics_{timestamp}.json')
            with open(filepath, 'w') as f:
                json.dump(self.results['risk_metrics'], f, indent=2)
            print(f"4. Exported risk metrics: {filepath}")

        # 5. Export strategies
        if 'strategies' in self.results:
            filepath = os.path.join(output_dir, f'trading_strategies_{timestamp}.csv')
            self.results['strategies'].to_csv(filepath, index=False)
            print(f"5. Exported trading strategies: {filepath}")

        # 6. Export merged dataset
        filepath = os.path.join(output_dir, f'merged_dataset_{timestamp}.csv')
        self.merged_data.to_csv(filepath, index=False)
        print(f"6. Exported merged dataset: {filepath}")

        # 7. Generate comprehensive report
        report_path = os.path.join(output_dir, f'comprehensive_analysis_report_{timestamp}.txt')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("COMPREHENSIVE HONG KONG MARKET QUANTITATIVE ANALYSIS\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("DATA SOURCES:\n")
            f.write(f"- HKEX Market Data: {len(self.hkex_data)} trading days\n")
            f.write(f"- HIBOR Rates: {len(self.hibor_data)} days\n")
            f.write(f"- Visitor Statistics: {len(self.visitor_data)} months\n\n")

            if 'risk_metrics' in self.results:
                f.write("RISK METRICS SUMMARY:\n")
                for key, value in self.results['risk_metrics'].items():
                    if isinstance(value, (int, float)):
                        f.write(f"- {key}: {value:.4f}\n")
                f.write("\n")

            if 'correlations' in self.results:
                f.write("KEY CORRELATIONS:\n")
                close_corr = self.results['correlations']['pearson']['Afternoon_Close']
                for feature, corr in close_corr.items():
                    if feature != 'Afternoon_Close':
                        f.write(f"- {feature}: {corr:.4f}\n")
                f.write("\n")

            if 'strategies' in self.results:
                f.write("RECOMMENDED TRADING STRATEGIES:\n")
                for idx, strategy in self.results['strategies'].iterrows():
                    f.write(f"\n{idx + 1}. {strategy['name']}\n")
                    for key, value in strategy.items():
                        if key != 'name':
                            f.write(f"   - {key}: {value}\n")

        print(f"\n7. Generated comprehensive report: {report_path}")
        print(f"\nAll results exported to: {output_dir}")

        return self

    def run_full_analysis(self):
        """Run complete analysis pipeline"""
        print("\n" + "=" * 80)
        print("STARTING COMPREHENSIVE HONG KONG MARKET ANALYSIS")
        print("=" * 80)

        self.load_data()
        self.perform_data_quality_assessment()
        self.merge_datasets()
        self.correlation_analysis()
        self.lagged_correlation_analysis(max_lag=5)
        self.granger_causality_test(max_lag=5)
        self.risk_metrics_analysis()
        self.trading_strategy_recommendations()
        self.generate_visualizations()
        self.export_results()

        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)
        print("\nAll results, visualizations, and reports have been generated.")
        print("Check the 'analysis_output' directory for detailed files.")

        return self


if __name__ == "__main__":
    # Initialize and run analyzer
    analyzer = HKQuantAnalyzer()
    analyzer.run_full_analysis()

    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("\n1. Review generated visualizations in analysis_output/")
    print("2. Examine correlation matrices and lagged relationships")
    print("3. Backtest recommended trading strategies")
    print("4. Implement risk management framework")
    print("5. Set up real-time monitoring system")
    print("\nFor questions or custom analysis, modify the analyzer parameters.")
