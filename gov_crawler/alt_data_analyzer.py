"""
Hong Kong Alternative Data Quantitative Analysis
Analyze 35 economic indicators for trading signals
"""

import json
import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class AltDataAnalyzer:
    def __init__(self, data_path):
        self.data_path = data_path
        self.raw_data = None
        self.df = None
        self.correlation_matrix = None

    def load_data(self):
        """Load JSON data"""
        print("Loading alternative data...")
        with open(self.data_path, 'r', encoding='utf-8') as f:
            self.raw_data = json.load(f)

        # Count total indicators
        total_indicators = 0
        for category, data in self.raw_data.items():
            if isinstance(data, dict):
                total_indicators += len(data)

        print(f"Loaded {len(self.raw_data)} categories")
        print(f"Found {total_indicators} indicators")
        return True

    def prepare_dataframe(self):
        """Prepare data for analysis"""
        print("\nPreparing data...")
        data_dict = {}

        # Process the new data structure
        for category, indicators in self.raw_data.items():
            if not isinstance(indicators, dict):
                continue

            for indicator_name, indicator_data in indicators.items():
                if isinstance(indicator_data, dict):
                    # Check for 'values' array (time series)
                    if 'values' in indicator_data:
                        values = indicator_data['values']
                        if isinstance(values, list) and len(values) > 0:
                            # Create time index (assuming daily data going backwards)
                            dates = pd.date_range(end=pd.Timestamp.now(), periods=len(values), freq='D')
                            ts = pd.Series(values, index=dates)
                            full_name = f"{category}_{indicator_name}"
                            data_dict[full_name] = ts
                    else:
                        # Try to extract scalar value
                        for key, val in indicator_data.items():
                            if isinstance(val, (int, float)):
                                # Store as single value with current date
                                ts = pd.Series([val], index=[pd.Timestamp.now()])
                                full_name = f"{category}_{indicator_name}_{key}"
                                data_dict[full_name] = ts

        if data_dict:
            self.df = pd.DataFrame(data_dict)
            print(f"Created DataFrame: {self.df.shape}")
            print(f"Date range: {self.df.index.min()} to {self.df.index.max()}")
            return self.df
        else:
            print("No valid data extracted")
            return None

    def calculate_statistics(self):
        """Calculate basic statistics"""
        print("\nCalculating statistics...")
        stats_dict = {}

        for col in self.df.columns:
            series = self.df[col].dropna()

            if len(series) < 2:
                continue

            stats_dict[col] = {
                'count': len(series),
                'mean': series.mean(),
                'std': series.std(),
                'min': series.min(),
                'max': series.max(),
                'latest': series.iloc[-1],
                'change_pct': ((series.iloc[-1] / series.iloc[0]) - 1) * 100 if len(series) > 1 else 0,
                'volatility': series.pct_change().std() * np.sqrt(252) * 100 if len(series) > 1 else 0,
            }

            if len(series) >= 10:
                x = np.arange(len(series))
                slope, _, r_value, _, _ = stats.linregress(x, series.values)
                stats_dict[col]['trend_slope'] = slope
                stats_dict[col]['trend_r2'] = r_value ** 2

        return stats_dict

    def correlation_analysis(self):
        """Correlation analysis"""
        print("\nPerforming correlation analysis...")

        self.correlation_matrix = self.df.corr(method='pearson', min_periods=30)
        strong_corr = []

        for i in range(len(self.correlation_matrix.columns)):
            for j in range(i+1, len(self.correlation_matrix.columns)):
                corr_val = self.correlation_matrix.iloc[i, j]

                if abs(corr_val) > 0.7:
                    strong_corr.append({
                        'Indicator_1': self.correlation_matrix.columns[i],
                        'Indicator_2': self.correlation_matrix.columns[j],
                        'Correlation': corr_val,
                        'Strength': 'Very Strong' if abs(corr_val) > 0.9 else 'Strong'
                    })

        strong_corr_df = pd.DataFrame(strong_corr)
        if not strong_corr_df.empty:
            strong_corr_df = strong_corr_df.sort_values('Correlation', ascending=False, key=abs)

        print(f"Found {len(strong_corr_df)} strong correlation pairs")
        return strong_corr_df

    def generate_hibor_signals(self):
        """Generate HIBOR signals"""
        print("\nGenerating HIBOR signals...")
        signals = {}

        hibor_cols = [col for col in self.df.columns if 'HIBOR' in col.upper() or 'INTEREST' in col.upper()]

        for col in hibor_cols:
            series = self.df[col].dropna()

            if len(series) < 30:
                continue

            latest = series.iloc[-1]
            ma_30 = series.tail(30).mean()
            ma_90 = series.tail(90).mean() if len(series) >= 90 else ma_30

            if latest < ma_30 * 0.95:
                signal = 'BUY'
                confidence = min((ma_30 - latest) / ma_30 * 100, 100)
            elif latest > ma_30 * 1.05:
                signal = 'SELL'
                confidence = min((latest - ma_30) / ma_30 * 100, 100)
            else:
                signal = 'HOLD'
                confidence = 50

            signals[col] = {
                'signal': signal,
                'confidence': confidence,
                'latest_value': latest,
                'ma_30': ma_30,
                'ma_90': ma_90,
                'trend': 'DOWN' if latest < ma_30 else 'UP'
            }

        return signals

    def generate_retail_signals(self):
        """Generate retail signals"""
        print("\nGenerating retail signals...")
        signals = {}

        retail_cols = [col for col in self.df.columns if 'RETAIL' in col.upper()]

        for col in retail_cols:
            series = self.df[col].dropna()

            if len(series) < 12:
                continue

            if len(series) >= 13:
                yoy_growth = ((series.iloc[-1] / series.iloc[-13]) - 1) * 100
            else:
                yoy_growth = 0

            momentum = series.pct_change(3).iloc[-1] * 100 if len(series) >= 4 else 0

            if yoy_growth > 5 and momentum > 0:
                signal = 'STRONG_BUY'
                confidence = min(yoy_growth * 10, 100)
            elif yoy_growth > 0:
                signal = 'BUY'
                confidence = min(yoy_growth * 15, 100)
            elif yoy_growth < -5:
                signal = 'SELL'
                confidence = min(abs(yoy_growth) * 10, 100)
            else:
                signal = 'HOLD'
                confidence = 50

            signals[col] = {
                'signal': signal,
                'confidence': confidence,
                'yoy_growth': yoy_growth,
                'momentum': momentum,
                'latest_value': series.iloc[-1]
            }

        return signals

    def generate_tourism_signals(self):
        """Generate tourism signals"""
        print("\nGenerating tourism signals...")
        signals = {}

        tourism_cols = [col for col in self.df.columns if 'VISITOR' in col.upper() or 'TOURISM' in col.upper()]

        for col in tourism_cols:
            series = self.df[col].dropna()

            if len(series) < 12:
                continue

            growth_3m = ((series.iloc[-1] / series.iloc[-4]) - 1) * 100 if len(series) >= 4 else 0
            growth_6m = ((series.iloc[-1] / series.iloc[-7]) - 1) * 100 if len(series) >= 7 else 0
            volatility = series.pct_change().std() * 100

            if growth_3m > 10:
                signal = 'STRONG_BUY'
                confidence = min(growth_3m * 5, 100)
            elif growth_3m > 0:
                signal = 'BUY'
                confidence = min(growth_3m * 10, 100)
            elif growth_3m < -10:
                signal = 'SELL'
                confidence = min(abs(growth_3m) * 5, 100)
            else:
                signal = 'HOLD'
                confidence = 50

            signals[col] = {
                'signal': signal,
                'confidence': confidence,
                'growth_3m': growth_3m,
                'growth_6m': growth_6m,
                'volatility': volatility,
                'latest_value': series.iloc[-1]
            }

        return signals

    def generate_traffic_signals(self):
        """Generate traffic signals"""
        print("\nGenerating traffic signals...")
        signals = {}

        traffic_cols = [col for col in self.df.columns if 'TRAFFIC' in col.upper() or 'VEHICLE' in col.upper()]

        for col in traffic_cols:
            series = self.df[col].dropna()

            if len(series) < 30:
                continue

            ma_7 = series.tail(7).mean()
            ma_30 = series.tail(30).mean()
            trend_strength = ((ma_7 / ma_30) - 1) * 100

            if trend_strength > 5:
                signal = 'BULLISH'
                confidence = min(trend_strength * 10, 100)
            elif trend_strength < -5:
                signal = 'BEARISH'
                confidence = min(abs(trend_strength) * 10, 100)
            else:
                signal = 'NEUTRAL'
                confidence = 50

            signals[col] = {
                'signal': signal,
                'confidence': confidence,
                'trend_strength': trend_strength,
                'ma_7': ma_7,
                'ma_30': ma_30,
                'latest_value': series.iloc[-1]
            }

        return signals

    def risk_assessment(self, stats_dict):
        """Risk assessment"""
        print("\nPerforming risk assessment...")
        risk_scores = {}

        for indicator, stat in stats_dict.items():
            volatility = stat.get('volatility', 0)
            data_count = stat.get('count', 0)

            reliability = min((data_count / 365) * 100, 100)
            vol_risk = min(volatility * 2, 100) if volatility else 0
            risk_score = (vol_risk * 0.7 + (100 - reliability) * 0.3)
            risk_level = 'LOW' if risk_score < 30 else 'MEDIUM' if risk_score < 60 else 'HIGH'

            risk_scores[indicator] = {
                'risk_score': risk_score,
                'risk_level': risk_level,
                'volatility': volatility,
                'reliability': reliability,
                'data_points': data_count
            }

        return risk_scores

    def generate_trading_strategies(self, signals):
        """Generate trading strategies"""
        print("\nGenerating trading strategies...")
        strategies = []

        if 'hibor_signals' in signals and signals['hibor_signals']:
            hibor_signal = list(signals['hibor_signals'].values())[0]

            if hibor_signal['signal'] == 'BUY':
                strategies.append({
                    'name': 'Low Interest Rate Strategy',
                    'type': 'Interest Rate Play',
                    'signal': 'BUY',
                    'target_sectors': ['Banks', 'Real Estate', 'Utilities'],
                    'rationale': 'HIBOR declining favors leveraged sectors',
                    'confidence': hibor_signal['confidence'],
                    'estimated_sharpe': 1.2
                })

        if 'retail_signals' in signals and signals['retail_signals']:
            retail_signal = list(signals['retail_signals'].values())[0]

            if retail_signal['signal'] in ['BUY', 'STRONG_BUY']:
                strategies.append({
                    'name': 'Consumption Recovery Strategy',
                    'type': 'Retail Momentum',
                    'signal': 'BUY',
                    'target_sectors': ['Retail', 'Consumer Discretionary', 'Luxury'],
                    'rationale': f"Retail sales YoY growth {retail_signal['yoy_growth']:.1f}%",
                    'confidence': retail_signal['confidence'],
                    'estimated_sharpe': 1.5
                })

        if 'tourism_signals' in signals and signals['tourism_signals']:
            tourism_signal = list(signals['tourism_signals'].values())[0]

            if tourism_signal['signal'] in ['BUY', 'STRONG_BUY']:
                strategies.append({
                    'name': 'Tourism Recovery Strategy',
                    'type': 'Tourism Momentum',
                    'signal': 'BUY',
                    'target_sectors': ['Hotels', 'Airlines', 'Entertainment', 'Retail'],
                    'rationale': f"Visitor arrivals 3m growth {tourism_signal['growth_3m']:.1f}%",
                    'confidence': tourism_signal['confidence'],
                    'estimated_sharpe': 1.3
                })

        if 'traffic_signals' in signals and signals['traffic_signals']:
            traffic_signal = list(signals['traffic_signals'].values())[0]

            if traffic_signal['signal'] == 'BULLISH':
                strategies.append({
                    'name': 'Economic Activity Strategy',
                    'type': 'Leading Indicator',
                    'signal': 'BUY',
                    'target_sectors': ['Broad Market', 'Cyclicals'],
                    'rationale': f"Traffic trend strength +{traffic_signal['trend_strength']:.1f}%",
                    'confidence': traffic_signal['confidence'],
                    'estimated_sharpe': 1.1
                })

        return strategies

    def generate_report(self, stats_dict, strong_corr_df, signals, risk_scores, strategies):
        """Generate analysis report"""
        print("\nGenerating analysis report...")
        report = []

        report.append("# Hong Kong Alternative Data Analysis Report")
        report.append(f"\n**Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"\n**Data Range**: {self.df.index.min().strftime('%Y-%m-%d')} to {self.df.index.max().strftime('%Y-%m-%d')}")
        report.append(f"\n**Indicators Analyzed**: {len(stats_dict)}")
        report.append("\n---\n")

        # Executive Summary
        report.append("## 1. Executive Summary\n")

        buy_signals = sum(1 for s in signals.values() for sig in s.values()
                         if isinstance(sig, dict) and sig.get('signal') in ['BUY', 'STRONG_BUY', 'BULLISH'])
        sell_signals = sum(1 for s in signals.values() for sig in s.values()
                          if isinstance(sig, dict) and sig.get('signal') in ['SELL', 'BEARISH'])

        if buy_signals > sell_signals * 1.5:
            market_outlook = "**BULLISH**"
        elif sell_signals > buy_signals * 1.5:
            market_outlook = "**BEARISH**"
        else:
            market_outlook = "**NEUTRAL**"

        report.append(f"**Market Outlook**: {market_outlook}\n")
        report.append(f"- Buy signals: {buy_signals}")
        report.append(f"- Sell signals: {sell_signals}")
        report.append(f"- Strong correlations: {len(strong_corr_df)}")
        report.append(f"- Trading strategies: {len(strategies)}\n")

        # Statistics Overview
        report.append("\n## 2. Key Indicators Statistics\n")
        report.append("| Indicator | Latest | Change% | Volatility% | Trend | Data Points |")
        report.append("|-----------|--------|---------|-------------|-------|-------------|")

        sorted_indicators = sorted(stats_dict.items(),
                                  key=lambda x: abs(x[1].get('change_pct', 0)),
                                  reverse=True)[:20]

        for indicator, stat in sorted_indicators:
            name = indicator.split('_')[-1][:30]
            latest = stat.get('latest', 0)
            change = stat.get('change_pct', 0)
            volatility = stat.get('volatility', 0)
            slope = stat.get('trend_slope', 0)
            trend = 'UP' if slope > 0 else 'DOWN' if slope < 0 else 'FLAT'
            count = stat.get('count', 0)

            report.append(f"| {name} | {latest:.2f} | {change:+.1f}% | {volatility:.1f}% | {trend} | {count} |")

        # Correlation Analysis
        report.append("\n## 3. Correlation Analysis\n")

        if len(strong_corr_df) > 0:
            report.append("### Strong Correlation Pairs (|r| > 0.7)\n")
            report.append("| Indicator 1 | Indicator 2 | Correlation | Strength |")
            report.append("|-------------|-------------|-------------|----------|")

            for _, row in strong_corr_df.head(15).iterrows():
                ind1 = row['Indicator_1'].split('_')[-1][:25]
                ind2 = row['Indicator_2'].split('_')[-1][:25]
                corr = row['Correlation']
                strength = row['Strength']

                report.append(f"| {ind1} | {ind2} | {corr:.3f} | {strength} |")
        else:
            report.append("*No strong correlations found*\n")

        # Quantitative Signals
        report.append("\n## 4. Quantitative Signals\n")

        if 'hibor_signals' in signals and signals['hibor_signals']:
            report.append("### 4.1 HIBOR Signals\n")
            report.append("| Indicator | Signal | Confidence | Latest | MA30 | Trend |")
            report.append("|-----------|--------|------------|--------|------|-------|")

            for indicator, sig in signals['hibor_signals'].items():
                name = indicator.split('_')[-1][:20]
                report.append(f"| {name} | {sig['signal']} | {sig['confidence']:.1f}% | "
                            f"{sig['latest_value']:.3f} | {sig['ma_30']:.3f} | {sig['trend']} |")

        if 'retail_signals' in signals and signals['retail_signals']:
            report.append("\n### 4.2 Retail Signals\n")
            report.append("| Indicator | Signal | Confidence | YoY Growth% | Momentum% |")
            report.append("|-----------|--------|------------|-------------|-----------|")

            for indicator, sig in signals['retail_signals'].items():
                name = indicator.split('_')[-1][:25]
                report.append(f"| {name} | {sig['signal']} | {sig['confidence']:.1f}% | "
                            f"{sig['yoy_growth']:+.1f}% | {sig['momentum']:+.1f}% |")

        if 'tourism_signals' in signals and signals['tourism_signals']:
            report.append("\n### 4.3 Tourism Signals\n")
            report.append("| Indicator | Signal | Confidence | 3M Growth% | 6M Growth% |")
            report.append("|-----------|--------|------------|------------|------------|")

            for indicator, sig in signals['tourism_signals'].items():
                name = indicator.split('_')[-1][:25]
                report.append(f"| {name} | {sig['signal']} | {sig['confidence']:.1f}% | "
                            f"{sig['growth_3m']:+.1f}% | {sig['growth_6m']:+.1f}% |")

        if 'traffic_signals' in signals and signals['traffic_signals']:
            report.append("\n### 4.4 Traffic Signals (Economic Activity)\n")
            report.append("| Indicator | Signal | Confidence | Trend Strength% |")
            report.append("|-----------|--------|------------|-----------------|")

            for indicator, sig in signals['traffic_signals'].items():
                name = indicator.split('_')[-1][:25]
                report.append(f"| {name} | {sig['signal']} | {sig['confidence']:.1f}% | "
                            f"{sig['trend_strength']:+.1f}% |")

        # Trading Strategies
        report.append("\n## 5. Trading Strategies\n")

        if strategies:
            for i, strategy in enumerate(strategies, 1):
                report.append(f"\n### 5.{i} {strategy['name']}\n")
                report.append(f"**Type**: {strategy['type']}")
                report.append(f"**Signal**: {strategy['signal']}")
                report.append(f"**Target Sectors**: {', '.join(strategy['target_sectors'])}")
                report.append(f"**Rationale**: {strategy['rationale']}")
                report.append(f"**Confidence**: {strategy['confidence']:.1f}%")
                report.append(f"**Estimated Sharpe Ratio**: {strategy['estimated_sharpe']:.2f}\n")
        else:
            report.append("*No clear trading strategies in current market*\n")

        # Portfolio Weights
        report.append("\n## 6. Portfolio Weights Recommendation\n")

        indicator_weights = {}
        for signal_type, signal_dict in signals.items():
            if signal_dict:
                avg_confidence = np.mean([s['confidence'] for s in signal_dict.values()
                                        if isinstance(s, dict) and 'confidence' in s])
                indicator_weights[signal_type] = avg_confidence

        total_confidence = sum(indicator_weights.values())

        if total_confidence > 0:
            report.append("| Indicator Type | Avg Confidence | Recommended Weight |")
            report.append("|----------------|----------------|--------------------|")

            for indicator, confidence in sorted(indicator_weights.items(),
                                               key=lambda x: x[1], reverse=True):
                weight = (confidence / total_confidence) * 100
                name = indicator.replace('_signals', '').upper()
                report.append(f"| {name} | {confidence:.1f}% | {weight:.1f}% |")

        # Risk Assessment
        report.append("\n## 7. Risk Assessment\n")

        avg_risk = np.mean([r['risk_score'] for r in risk_scores.values()])
        avg_reliability = np.mean([r['reliability'] for r in risk_scores.values()])

        report.append(f"**Overall Data Reliability**: {avg_reliability:.1f}%")
        report.append(f"**Average Risk Score**: {avg_risk:.1f}/100\n")

        report.append("| Risk Level | Count | Percentage |")
        report.append("|------------|-------|------------|")

        risk_distribution = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0}
        for r in risk_scores.values():
            risk_distribution[r['risk_level']] += 1

        total_indicators = len(risk_scores)
        for level, count in risk_distribution.items():
            pct = (count / total_indicators) * 100 if total_indicators > 0 else 0
            report.append(f"| {level} | {count} | {pct:.1f}% |")

        # Risk Management
        report.append("\n### 7.2 Risk Management Recommendations\n")

        if avg_risk < 40:
            report.append("**Overall Risk: LOW**")
            report.append("- Data quality is good")
            report.append("- Recommended position: 70-80%")
            report.append("- Stop loss: -5%")
        elif avg_risk < 60:
            report.append("**Overall Risk: MEDIUM**")
            report.append("- Some data shows high volatility")
            report.append("- Recommended position: 50-60%")
            report.append("- Stop loss: -7%")
        else:
            report.append("**Overall Risk: HIGH**")
            report.append("- High data volatility, be cautious")
            report.append("- Recommended position: 30-40%")
            report.append("- Stop loss: -10%")

        # Sector Allocation
        report.append("\n## 8. Sector Allocation Recommendations\n")

        sector_scores = {
            'Banks': 0,
            'Real Estate': 0,
            'Retail': 0,
            'Tourism & Hospitality': 0,
            'Utilities': 0,
            'Technology': 0,
            'Consumer': 0
        }

        if 'hibor_signals' in signals and signals['hibor_signals']:
            hibor_signal = list(signals['hibor_signals'].values())[0]
            if hibor_signal['signal'] == 'BUY':
                sector_scores['Banks'] += 2
                sector_scores['Real Estate'] += 2
                sector_scores['Utilities'] += 1
            elif hibor_signal['signal'] == 'SELL':
                sector_scores['Banks'] -= 2
                sector_scores['Real Estate'] -= 2

        if 'retail_signals' in signals and signals['retail_signals']:
            retail_signal = list(signals['retail_signals'].values())[0]
            if retail_signal['signal'] in ['BUY', 'STRONG_BUY']:
                sector_scores['Retail'] += 2
                sector_scores['Consumer'] += 2
            elif retail_signal['signal'] == 'SELL':
                sector_scores['Retail'] -= 2
                sector_scores['Consumer'] -= 1

        if 'tourism_signals' in signals and signals['tourism_signals']:
            tourism_signal = list(signals['tourism_signals'].values())[0]
            if tourism_signal['signal'] in ['BUY', 'STRONG_BUY']:
                sector_scores['Tourism & Hospitality'] += 2
                sector_scores['Retail'] += 1

        report.append("| Sector | Rating | Allocation% |")
        report.append("|--------|--------|-------------|")

        for sector, score in sorted(sector_scores.items(), key=lambda x: x[1], reverse=True):
            if score >= 2:
                rating = 'STRONG BUY'
                allocation = 20
            elif score >= 1:
                rating = 'BUY'
                allocation = 15
            elif score >= 0:
                rating = 'NEUTRAL'
                allocation = 10
            else:
                rating = 'AVOID'
                allocation = 5

            report.append(f"| {sector} | {rating} | {allocation}% |")

        # Conclusions
        report.append("\n## 9. Conclusions and Action Items\n")

        report.append("### 9.1 Key Findings\n")

        key_findings = []

        if buy_signals > sell_signals:
            key_findings.append(f"- Market shows **{buy_signals - sell_signals} net bullish signals**")
        elif sell_signals > buy_signals:
            key_findings.append(f"- Market shows **{sell_signals - buy_signals} net bearish signals**")
        else:
            key_findings.append("- Market signals are neutral, recommend wait and see")

        if 'retail_signals' in signals and signals['retail_signals']:
            retail_signal = list(signals['retail_signals'].values())[0]
            if retail_signal['yoy_growth'] > 5:
                key_findings.append(f"- Retail sales strong growth **{retail_signal['yoy_growth']:.1f}%**, consumption recovery evident")

        if 'tourism_signals' in signals and signals['tourism_signals']:
            tourism_signal = list(signals['tourism_signals'].values())[0]
            if tourism_signal['growth_3m'] > 10:
                key_findings.append(f"- Visitor arrivals surged **{tourism_signal['growth_3m']:.1f}%**, tourism recovery strong")

        if len(strong_corr_df) > 10:
            key_findings.append(f"- Found **{len(strong_corr_df)} strong correlations**, data consistency high")

        for finding in key_findings:
            report.append(finding)

        report.append("\n### 9.2 Immediate Action Items\n")

        if strategies:
            report.append("**Recommended strategies (by priority)**:\n")
            for i, strategy in enumerate(sorted(strategies,
                                               key=lambda x: x['confidence'],
                                               reverse=True)[:3], 1):
                report.append(f"{i}. **{strategy['name']}**")
                report.append(f"   - Target: {', '.join(strategy['target_sectors'][:3])}")
                report.append(f"   - Confidence: {strategy['confidence']:.0f}%")
                report.append(f"   - Expected Sharpe: {strategy['estimated_sharpe']:.2f}\n")

        # Appendix
        report.append("\n## 10. Appendix: Data Sources\n")

        data_sources = self.raw_data.get('data_sources', {})
        report.append(f"**Total Data Sources**: {len(data_sources)}\n")

        for source_name, source_data in data_sources.items():
            datasets = source_data.get('datasets', [])
            report.append(f"### {source_name}")
            report.append(f"- Datasets: {len(datasets)}")

            if datasets:
                total_records = sum(len(ds.get('data', [])) for ds in datasets)
                report.append(f"- Total records: {total_records}")

            report.append("")

        report.append("\n---")
        report.append("\n*Report generated by Alternative Data Analyzer*")
        report.append(f"\n*Analysis completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        return '\n'.join(report)

    def run_analysis(self):
        """Run full analysis"""
        print("="*80)
        print("Starting comprehensive alternative data analysis...")
        print("="*80)

        self.load_data()
        self.prepare_dataframe()

        if self.df is None or self.df.empty:
            print("No valid data to analyze")
            return None

        stats_dict = self.calculate_statistics()
        strong_corr_df = self.correlation_analysis()

        signals = {
            'hibor_signals': self.generate_hibor_signals(),
            'retail_signals': self.generate_retail_signals(),
            'tourism_signals': self.generate_tourism_signals(),
            'traffic_signals': self.generate_traffic_signals()
        }

        risk_scores = self.risk_assessment(stats_dict)
        strategies = self.generate_trading_strategies(signals)
        report_md = self.generate_report(stats_dict, strong_corr_df, signals, risk_scores, strategies)

        # Save outputs
        output_path = r"C:\Users\Penguin8n\CODEX--\CODEX--\gov_crawler\ALTERNATIVE_DATA_ANALYSIS_REPORT.md"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_md)
        print(f"\nAnalysis complete! Report saved to:")
        print(f"   {output_path}")

        if self.correlation_matrix is not None:
            corr_path = r"C:\Users\Penguin8n\CODEX--\CODEX--\gov_crawler\correlation_matrix.csv"
            self.correlation_matrix.to_csv(corr_path, encoding='utf-8-sig')
            print(f"   Correlation matrix: {corr_path}")

        if not strong_corr_df.empty:
            strong_corr_path = r"C:\Users\Penguin8n\CODEX--\CODEX--\gov_crawler\strong_correlations.csv"
            strong_corr_df.to_csv(strong_corr_path, index=False, encoding='utf-8-sig')
            print(f"   Strong correlations: {strong_corr_path}")

        signals_path = r"C:\Users\Penguin8n\CODEX--\CODEX--\gov_crawler\trading_signals.json"
        with open(signals_path, 'w', encoding='utf-8') as f:
            json.dump(signals, f, indent=2, ensure_ascii=False)
        print(f"   Trading signals: {signals_path}")

        print("\n" + "="*80)
        print("Analysis Summary:")
        print("="*80)
        print(f"Total Indicators: {len(stats_dict)}")
        print(f"Strong Correlations: {len(strong_corr_df)}")
        print(f"Trading Strategies: {len(strategies)}")
        print(f"Risk Assessment: {len(risk_scores)} indicators")
        print("="*80)

        return {
            'stats': stats_dict,
            'correlations': strong_corr_df,
            'signals': signals,
            'risk_scores': risk_scores,
            'strategies': strategies,
            'report': report_md
        }


def main():
    data_path = r"C:\Users\Penguin8n\CODEX--\CODEX--\gov_crawler\data\all_alternative_data_20251023_210419.json"

    analyzer = AltDataAnalyzer(data_path)
    results = analyzer.run_analysis()

    if results:
        print("\nAll analysis tasks completed successfully!")
        print("\nOutput files:")
        print("   1. ALTERNATIVE_DATA_ANALYSIS_REPORT.md (Main report)")
        print("   2. correlation_matrix.csv (Full correlation matrix)")
        print("   3. strong_correlations.csv (Strong correlation pairs)")
        print("   4. trading_signals.json (Quantitative trading signals)")
        print("\nPlease review the main report for detailed analysis and trading recommendations!")
    else:
        print("\nAnalysis failed. Please check the data file.")


if __name__ == "__main__":
    main()
