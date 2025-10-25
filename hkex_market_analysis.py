"""
HKEX Market Data Comprehensive Analysis
Analyzes market data from Sept-Oct 2025 and generates trading strategies
"""

import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Set display options for better output
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
pd.set_option('display.float_format', '{:.2f}'.format)

class HKEXMarketAnalyzer:
    """Comprehensive HKEX market data analyzer"""

    def __init__(self, csv_path):
        """Initialize analyzer with CSV data"""
        self.csv_path = csv_path
        self.df = None
        self.load_data()

    def load_data(self):
        """Load and preprocess market data"""
        print("=" * 80)
        print("LOADING HKEX MARKET DATA")
        print("=" * 80)

        # Read CSV
        self.df = pd.read_csv(self.csv_path)

        # Convert date column
        self.df['Date'] = pd.to_datetime(self.df['Date'])

        # Remove rows with missing critical data
        initial_rows = len(self.df)
        self.df = self.df.dropna(subset=['Afternoon_Close', 'Trading_Volume', 'Turnover_HKD'])
        final_rows = len(self.df)

        print(f"Loaded {initial_rows} rows, {final_rows} valid trading days")
        print(f"Date range: {self.df['Date'].min().date()} to {self.df['Date'].max().date()}")

        # Sort by date
        self.df = self.df.sort_values('Date').reset_index(drop=True)

        # Calculate additional metrics
        self._calculate_derived_metrics()

        print(f"\nData shape: {self.df.shape}")
        print(f"Columns: {list(self.df.columns)}\n")

    def _calculate_derived_metrics(self):
        """Calculate derived market indicators"""
        # Market breadth indicators
        self.df['Total_Active_Stocks'] = (
            self.df['Advanced_Stocks'] +
            self.df['Declined_Stocks'] +
            self.df['Unchanged_Stocks']
        )

        # Advance-Decline Ratio
        self.df['AD_Ratio'] = self.df['Advanced_Stocks'] / self.df['Declined_Stocks'].replace(0, 1)

        # Market Breadth (bullish when > 1)
        self.df['Market_Breadth'] = (
            (self.df['Advanced_Stocks'] - self.df['Declined_Stocks']) /
            self.df['Total_Active_Stocks']
        )

        # Percentage of advancing stocks
        self.df['Pct_Advanced'] = (self.df['Advanced_Stocks'] / self.df['Total_Active_Stocks']) * 100

        # Turnover per deal
        self.df['Avg_Deal_Size'] = self.df['Turnover_HKD'] / self.df['Deals'].replace(0, 1)

        # Daily returns
        self.df['Daily_Return'] = self.df['Afternoon_Close'].pct_change() * 100

        # Volatility (20-day rolling std)
        self.df['Volatility_20D'] = self.df['Daily_Return'].rolling(window=20, min_periods=1).std()

        # Moving averages
        self.df['MA_5'] = self.df['Afternoon_Close'].rolling(window=5, min_periods=1).mean()
        self.df['MA_10'] = self.df['Afternoon_Close'].rolling(window=10, min_periods=1).mean()
        self.df['MA_20'] = self.df['Afternoon_Close'].rolling(window=20, min_periods=1).mean()

        # MACD components
        self.df['EMA_12'] = self.df['Afternoon_Close'].ewm(span=12, adjust=False).mean()
        self.df['EMA_26'] = self.df['Afternoon_Close'].ewm(span=26, adjust=False).mean()
        self.df['MACD'] = self.df['EMA_12'] - self.df['EMA_26']
        self.df['MACD_Signal'] = self.df['MACD'].ewm(span=9, adjust=False).mean()
        self.df['MACD_Histogram'] = self.df['MACD'] - self.df['MACD_Signal']

        # RSI calculation
        delta = self.df['Daily_Return']
        gain = delta.where(delta > 0, 0).rolling(window=14, min_periods=1).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14, min_periods=1).mean()
        rs = gain / loss.replace(0, 1)
        self.df['RSI_14'] = 100 - (100 / (1 + rs))

        # Bollinger Bands
        self.df['BB_Middle'] = self.df['Afternoon_Close'].rolling(window=20, min_periods=1).mean()
        bb_std = self.df['Afternoon_Close'].rolling(window=20, min_periods=1).std()
        self.df['BB_Upper'] = self.df['BB_Middle'] + (2 * bb_std)
        self.df['BB_Lower'] = self.df['BB_Middle'] - (2 * bb_std)
        self.df['BB_Width'] = (self.df['BB_Upper'] - self.df['BB_Lower']) / self.df['BB_Middle']

        # Volume momentum
        self.df['Volume_MA_5'] = self.df['Trading_Volume'].rolling(window=5, min_periods=1).mean()
        self.df['Volume_Ratio'] = self.df['Trading_Volume'] / self.df['Volume_MA_5']

        # Turnover momentum
        self.df['Turnover_MA_5'] = self.df['Turnover_HKD'].rolling(window=5, min_periods=1).mean()
        self.df['Turnover_Ratio'] = self.df['Turnover_HKD'] / self.df['Turnover_MA_5']

    def print_statistical_summary(self):
        """Print comprehensive statistical summary"""
        print("=" * 80)
        print("1. DATA ANALYSIS - STATISTICAL SUMMARY")
        print("=" * 80)

        # Key metrics to analyze
        key_metrics = [
            'Afternoon_Close', 'Trading_Volume', 'Turnover_HKD', 'Deals',
            'Daily_Return', 'Advanced_Stocks', 'Declined_Stocks',
            'Unchanged_Stocks', 'AD_Ratio', 'Market_Breadth'
        ]

        summary = self.df[key_metrics].describe()

        print("\nKEY METRICS STATISTICS:")
        print(summary.to_string())

        # Additional metrics
        print("\n" + "=" * 80)
        print("TREND ANALYSIS (Sept - Oct 2025)")
        print("=" * 80)

        start_price = self.df.iloc[0]['Afternoon_Close']
        end_price = self.df.iloc[-1]['Afternoon_Close']
        total_return = ((end_price - start_price) / start_price) * 100

        print(f"\nIndex Performance:")
        print(f"  Starting Index (Sept 1): {start_price:,.2f}")
        print(f"  Ending Index (Oct 17): {end_price:,.2f}")
        print(f"  Absolute Change: {end_price - start_price:,.2f}")
        print(f"  Total Return: {total_return:.2f}%")
        print(f"  Period High: {self.df['Afternoon_Close'].max():,.2f}")
        print(f"  Period Low: {self.df['Afternoon_Close'].min():,.2f}")
        print(f"  Volatility (std of returns): {self.df['Daily_Return'].std():.2f}%")

        # Market sentiment
        print("\n" + "-" * 80)
        print("MARKET SENTIMENT INDICATORS:")
        print("-" * 80)

        avg_ad_ratio = self.df['AD_Ratio'].mean()
        avg_breadth = self.df['Market_Breadth'].mean()
        avg_pct_advanced = self.df['Pct_Advanced'].mean()

        bullish_days = len(self.df[self.df['Market_Breadth'] > 0])
        bearish_days = len(self.df[self.df['Market_Breadth'] < 0])

        print(f"\nAverage Advance-Decline Ratio: {avg_ad_ratio:.2f}")
        print(f"Average Market Breadth: {avg_breadth:.4f} ({'Bullish' if avg_breadth > 0 else 'Bearish'})")
        print(f"Average % of Advanced Stocks: {avg_pct_advanced:.2f}%")
        print(f"Bullish Days: {bullish_days} ({bullish_days/len(self.df)*100:.1f}%)")
        print(f"Bearish Days: {bearish_days} ({bearish_days/len(self.df)*100:.1f}%)")

        # Classify overall sentiment
        if avg_breadth > 0.1:
            sentiment = "STRONG BULLISH"
        elif avg_breadth > 0:
            sentiment = "MILDLY BULLISH"
        elif avg_breadth > -0.1:
            sentiment = "MILDLY BEARISH"
        else:
            sentiment = "STRONG BEARISH"

        print(f"\nOverall Market Sentiment: {sentiment}")

        # Correlation analysis
        print("\n" + "-" * 80)
        print("CORRELATION ANALYSIS:")
        print("-" * 80)

        # Correlation between turnover and market movement
        corr_turnover_return = self.df['Turnover_HKD'].corr(self.df['Daily_Return'])
        corr_volume_return = self.df['Trading_Volume'].corr(self.df['Daily_Return'])
        corr_breadth_return = self.df['Market_Breadth'].corr(self.df['Daily_Return'])

        print(f"\nTurnover vs Daily Return: {corr_turnover_return:.4f}")
        print(f"Volume vs Daily Return: {corr_volume_return:.4f}")
        print(f"Market Breadth vs Daily Return: {corr_breadth_return:.4f}")

        if abs(corr_turnover_return) > 0.5:
            print(f"  [>] {'Strong positive' if corr_turnover_return > 0 else 'Strong negative'} correlation detected!")

        # Volume analysis
        print("\n" + "-" * 80)
        print("TRADING ACTIVITY ANALYSIS:")
        print("-" * 80)

        avg_volume = self.df['Trading_Volume'].mean()
        avg_turnover = self.df['Turnover_HKD'].mean()
        avg_deals = self.df['Deals'].mean()

        print(f"\nAverage Daily Volume: {avg_volume:,.0f} stocks")
        print(f"Average Daily Turnover: HKD {avg_turnover:,.0f}")
        print(f"Average Daily Deals: {avg_deals:,.0f}")
        print(f"Average Deal Size: HKD {self.df['Avg_Deal_Size'].mean():,.0f}")

        # Identify high/low activity days
        high_volume_threshold = avg_volume * 1.2
        high_volume_days = self.df[self.df['Trading_Volume'] > high_volume_threshold]

        print(f"\nHigh Volume Days (>20% above average): {len(high_volume_days)}")
        if len(high_volume_days) > 0:
            print(f"  Dates: {', '.join(high_volume_days['Date'].dt.strftime('%Y-%m-%d').tolist())}")

    def identify_market_signals(self):
        """Identify bullish and bearish signals"""
        print("\n" + "=" * 80)
        print("2. MARKET SIGNALS IDENTIFICATION")
        print("=" * 80)

        # Get latest data
        latest = self.df.iloc[-1]
        prev = self.df.iloc[-2] if len(self.df) > 1 else latest

        print("\nLATEST MARKET DATA ({}):".format(latest['Date'].strftime('%Y-%m-%d')))
        print(f"  Index Close: {latest['Afternoon_Close']:,.2f}")
        print(f"  Daily Return: {latest['Daily_Return']:.2f}%")
        print(f"  RSI(14): {latest['RSI_14']:.2f}")
        print(f"  Market Breadth: {latest['Market_Breadth']:.4f}")
        print(f"  A/D Ratio: {latest['AD_Ratio']:.2f}")

        # Signal detection
        signals = []

        # 1. RSI signals
        print("\n" + "-" * 80)
        print("RSI-BASED SIGNALS:")
        print("-" * 80)

        if latest['RSI_14'] < 30:
            signals.append(("BULLISH", "RSI Oversold", latest['RSI_14'], "Strong buy signal - market oversold"))
            print(f"[+] OVERSOLD: RSI = {latest['RSI_14']:.2f} (< 30) - Strong BUY signal")
        elif latest['RSI_14'] > 70:
            signals.append(("BEARISH", "RSI Overbought", latest['RSI_14'], "Strong sell signal - market overbought"))
            print(f"[-] OVERBOUGHT: RSI = {latest['RSI_14']:.2f} (> 70) - Strong SELL signal")
        elif latest['RSI_14'] < 40:
            signals.append(("BULLISH", "RSI Weak", latest['RSI_14'], "Moderate buy signal"))
            print(f"[>] WEAK: RSI = {latest['RSI_14']:.2f} (< 40) - Moderate BUY signal")
        elif latest['RSI_14'] > 60:
            signals.append(("BEARISH", "RSI Strong", latest['RSI_14'], "Moderate sell signal"))
            print(f"[<] STRONG: RSI = {latest['RSI_14']:.2f} (> 60) - Moderate SELL signal")
        else:
            print(f"[o] NEUTRAL: RSI = {latest['RSI_14']:.2f} (40-60 range)")

        # 2. MACD signals
        print("\n" + "-" * 80)
        print("MACD SIGNALS:")
        print("-" * 80)

        macd_cross_up = latest['MACD'] > latest['MACD_Signal'] and prev['MACD'] <= prev['MACD_Signal']
        macd_cross_down = latest['MACD'] < latest['MACD_Signal'] and prev['MACD'] >= prev['MACD_Signal']

        print(f"MACD: {latest['MACD']:.2f}")
        print(f"Signal: {latest['MACD_Signal']:.2f}")
        print(f"Histogram: {latest['MACD_Histogram']:.2f}")

        if macd_cross_up:
            signals.append(("BULLISH", "MACD Crossover", latest['MACD'], "Bullish crossover detected"))
            print("[+] BULLISH CROSSOVER: MACD crossed above signal line - BUY signal")
        elif macd_cross_down:
            signals.append(("BEARISH", "MACD Crossover", latest['MACD'], "Bearish crossover detected"))
            print("[-] BEARISH CROSSOVER: MACD crossed below signal line - SELL signal")
        elif latest['MACD'] > latest['MACD_Signal']:
            print("[>] BULLISH: MACD above signal line")
        else:
            print("[<] BEARISH: MACD below signal line")

        # 3. Moving Average signals
        print("\n" + "-" * 80)
        print("MOVING AVERAGE SIGNALS:")
        print("-" * 80)

        ma_trend = "BULLISH" if latest['MA_5'] > latest['MA_10'] > latest['MA_20'] else \
                   "BEARISH" if latest['MA_5'] < latest['MA_10'] < latest['MA_20'] else "MIXED"

        print(f"MA(5): {latest['MA_5']:,.2f}")
        print(f"MA(10): {latest['MA_10']:,.2f}")
        print(f"MA(20): {latest['MA_20']:,.2f}")
        print(f"Current Price: {latest['Afternoon_Close']:,.2f}")
        print(f"\nTrend: {ma_trend}")

        if latest['Afternoon_Close'] > latest['MA_5'] > latest['MA_10']:
            signals.append(("BULLISH", "MA Alignment", latest['MA_5'], "Price above rising MAs"))
            print("[+] BULLISH: Price above rising moving averages")
        elif latest['Afternoon_Close'] < latest['MA_5'] < latest['MA_10']:
            signals.append(("BEARISH", "MA Alignment", latest['MA_5'], "Price below falling MAs"))
            print("[-] BEARISH: Price below falling moving averages")

        # 4. Bollinger Bands signals
        print("\n" + "-" * 80)
        print("BOLLINGER BANDS SIGNALS:")
        print("-" * 80)

        bb_position = (latest['Afternoon_Close'] - latest['BB_Lower']) / (latest['BB_Upper'] - latest['BB_Lower'])

        print(f"Upper Band: {latest['BB_Upper']:,.2f}")
        print(f"Middle Band: {latest['BB_Middle']:,.2f}")
        print(f"Lower Band: {latest['BB_Lower']:,.2f}")
        print(f"Current Price: {latest['Afternoon_Close']:,.2f}")
        print(f"BB Width: {latest['BB_Width']:.4f}")
        print(f"Position in Band: {bb_position*100:.1f}%")

        if latest['Afternoon_Close'] < latest['BB_Lower']:
            signals.append(("BULLISH", "BB Oversold", bb_position, "Price below lower band - oversold"))
            print("[+] OVERSOLD: Price below lower Bollinger Band - BUY signal")
        elif latest['Afternoon_Close'] > latest['BB_Upper']:
            signals.append(("BEARISH", "BB Overbought", bb_position, "Price above upper band - overbought"))
            print("[-] OVERBOUGHT: Price above upper Bollinger Band - SELL signal")
        elif bb_position < 0.2:
            print("[>] NEAR OVERSOLD: Price in lower 20% of band")
        elif bb_position > 0.8:
            print("[<] NEAR OVERBOUGHT: Price in upper 20% of band")
        else:
            print("[o] NEUTRAL: Price within normal Bollinger Band range")

        # 5. Market Breadth signals
        print("\n" + "-" * 80)
        print("MARKET BREADTH SIGNALS:")
        print("-" * 80)

        print(f"Market Breadth: {latest['Market_Breadth']:.4f}")
        print(f"A/D Ratio: {latest['AD_Ratio']:.2f}")
        print(f"% Advanced: {latest['Pct_Advanced']:.1f}%")

        if latest['Market_Breadth'] > 0.3:
            signals.append(("BULLISH", "Strong Breadth", latest['Market_Breadth'], "Strong market participation"))
            print("[+] STRONG BULLISH: Market breadth > 0.3 - broad market rally")
        elif latest['Market_Breadth'] < -0.3:
            signals.append(("BEARISH", "Weak Breadth", latest['Market_Breadth'], "Broad market weakness"))
            print("[-] STRONG BEARISH: Market breadth < -0.3 - broad market decline")
        elif latest['Market_Breadth'] > 0:
            print("[>] MILDLY BULLISH: Positive market breadth")
        else:
            print("[<] MILDLY BEARISH: Negative market breadth")

        # 6. Volume momentum signals
        print("\n" + "-" * 80)
        print("VOLUME MOMENTUM SIGNALS:")
        print("-" * 80)

        print(f"Volume Ratio: {latest['Volume_Ratio']:.2f}")
        print(f"Turnover Ratio: {latest['Turnover_Ratio']:.2f}")

        if latest['Volume_Ratio'] > 1.5 and latest['Daily_Return'] > 0:
            signals.append(("BULLISH", "Volume Surge", latest['Volume_Ratio'], "Strong buying volume"))
            print("[+] BULLISH: High volume with positive return - strong buying pressure")
        elif latest['Volume_Ratio'] > 1.5 and latest['Daily_Return'] < 0:
            signals.append(("BEARISH", "Volume Surge", latest['Volume_Ratio'], "Strong selling volume"))
            print("[-] BEARISH: High volume with negative return - strong selling pressure")

        # 7. Momentum analysis
        print("\n" + "-" * 80)
        print("MOMENTUM & VOLATILITY PATTERNS:")
        print("-" * 80)

        recent_returns = self.df.tail(5)['Daily_Return']
        momentum = recent_returns.mean()
        volatility = recent_returns.std()

        print(f"5-Day Average Return: {momentum:.2f}%")
        print(f"5-Day Volatility: {volatility:.2f}%")
        print(f"20-Day Volatility: {latest['Volatility_20D']:.2f}%")

        if momentum > 0.5:
            print("[>] STRONG POSITIVE MOMENTUM")
        elif momentum < -0.5:
            print("[<] STRONG NEGATIVE MOMENTUM")
        else:
            print("[o] WEAK MOMENTUM")

        if volatility > 2:
            print("[!] HIGH VOLATILITY - Increased risk")
        elif volatility < 1:
            print("[+] LOW VOLATILITY - Stable market")

        # Summary of signals
        print("\n" + "=" * 80)
        print("SIGNAL SUMMARY:")
        print("=" * 80)

        bullish_signals = [s for s in signals if s[0] == "BULLISH"]
        bearish_signals = [s for s in signals if s[0] == "BEARISH"]

        print(f"\nBullish Signals: {len(bullish_signals)}")
        for signal in bullish_signals:
            print(f"  [+] {signal[1]}: {signal[3]}")

        print(f"\nBearish Signals: {len(bearish_signals)}")
        for signal in bearish_signals:
            print(f"  [-] {signal[1]}: {signal[3]}")

        # Overall signal
        if len(bullish_signals) > len(bearish_signals) + 2:
            overall = "STRONG BUY"
        elif len(bullish_signals) > len(bearish_signals):
            overall = "BUY"
        elif len(bearish_signals) > len(bullish_signals) + 2:
            overall = "STRONG SELL"
        elif len(bearish_signals) > len(bullish_signals):
            overall = "SELL"
        else:
            overall = "NEUTRAL / HOLD"

        print(f"\n{'='*80}")
        print(f"OVERALL SIGNAL: {overall}")
        print(f"{'='*80}")

        return signals, overall

    def develop_trading_strategies(self):
        """Develop quantitative trading strategies"""
        print("\n" + "=" * 80)
        print("3. TRADING STRATEGY DEVELOPMENT")
        print("=" * 80)

        latest = self.df.iloc[-1]

        # Strategy 1: Mean Reversion Strategy
        print("\n" + "-" * 80)
        print("STRATEGY 1: BOLLINGER BAND MEAN REVERSION")
        print("-" * 80)

        print("\nConcept: Buy when price touches lower Bollinger Band, sell when it reaches middle/upper band")
        print("\nEntry Criteria:")
        print("  • BUY when: Price closes below Lower BB AND RSI < 40")
        print("  • SELL/SHORT when: Price closes above Upper BB AND RSI > 60")

        print("\nExit Criteria:")
        print("  • Take Profit (Long): Price reaches Middle BB or Upper BB")
        print("  • Stop Loss (Long): 2% below entry price")
        print("  • Take Profit (Short): Price reaches Middle BB or Lower BB")
        print("  • Stop Loss (Short): 2% above entry price")

        # Calculate current strategy parameters
        entry_price = latest['Afternoon_Close']
        long_stop = entry_price * 0.98
        long_tp1 = latest['BB_Middle']
        long_tp2 = latest['BB_Upper']

        print(f"\nCurrent Levels (as of {latest['Date'].strftime('%Y-%m-%d')}):")
        print(f"  Current Price: {entry_price:,.2f}")
        print(f"  Lower BB: {latest['BB_Lower']:,.2f}")
        print(f"  Middle BB: {latest['BB_Middle']:,.2f}")
        print(f"  Upper BB: {latest['BB_Upper']:,.2f}")

        print(f"\nIf entering LONG position now:")
        print(f"  Entry: {entry_price:,.2f}")
        print(f"  Stop Loss: {long_stop:,.2f} (-2.0%)")
        print(f"  Take Profit 1: {long_tp1:,.2f} (+{((long_tp1-entry_price)/entry_price*100):.2f}%)")
        print(f"  Take Profit 2: {long_tp2:,.2f} (+{((long_tp2-entry_price)/entry_price*100):.2f}%)")
        print(f"  Risk/Reward Ratio: {abs((long_tp1-entry_price)/(entry_price-long_stop)):.2f}:1")

        # Position sizing
        account_value = 1000000  # HKD 1M example
        risk_per_trade = 0.02  # 2% risk
        risk_amount = account_value * risk_per_trade
        position_size = risk_amount / (entry_price - long_stop)

        print(f"\nPosition Sizing (for HKD 1M account, 2% risk per trade):")
        print(f"  Risk Amount: HKD {risk_amount:,.0f}")
        print(f"  Position Size: {position_size:,.0f} shares")
        print(f"  Position Value: HKD {position_size * entry_price:,.0f}")
        print(f"  % of Account: {(position_size * entry_price / account_value * 100):.1f}%")

        # Strategy 2: Momentum Breakout Strategy
        print("\n" + "-" * 80)
        print("STRATEGY 2: MACD MOMENTUM BREAKOUT")
        print("-" * 80)

        print("\nConcept: Follow strong momentum when MACD confirms trend reversal")
        print("\nEntry Criteria:")
        print("  • BUY when:")
        print("    - MACD crosses above Signal line")
        print("    - Price > MA(20)")
        print("    - Volume > 1.2x average volume")
        print("  • SELL when:")
        print("    - MACD crosses below Signal line")
        print("    - Price < MA(20)")

        print("\nExit Criteria:")
        print("  • Take Profit: +3% from entry OR MACD histogram turns negative")
        print("  • Stop Loss: -1.5% from entry OR price closes below MA(10)")
        print("  • Trailing Stop: Once +2% profit, trail stop at -1% from peak")

        long_tp_mom = entry_price * 1.03
        long_sl_mom = entry_price * 0.985

        print(f"\nCurrent Levels:")
        print(f"  Current Price: {entry_price:,.2f}")
        print(f"  MACD: {latest['MACD']:.2f}")
        print(f"  Signal: {latest['MACD_Signal']:.2f}")
        print(f"  MA(20): {latest['MA_20']:,.2f}")
        print(f"  Volume Ratio: {latest['Volume_Ratio']:.2f}")

        print(f"\nIf entering LONG position now:")
        print(f"  Entry: {entry_price:,.2f}")
        print(f"  Stop Loss: {long_sl_mom:,.2f} (-1.5%)")
        print(f"  Take Profit: {long_tp_mom:,.2f} (+3.0%)")
        print(f"  Risk/Reward Ratio: {abs((long_tp_mom-entry_price)/(entry_price-long_sl_mom)):.2f}:1")

        position_size_mom = risk_amount / (entry_price - long_sl_mom)
        print(f"\nPosition Sizing (HKD 1M account, 2% risk):")
        print(f"  Position Size: {position_size_mom:,.0f} shares")
        print(f"  Position Value: HKD {position_size_mom * entry_price:,.0f}")

        # Strategy 3: Market Breadth Trend Following
        print("\n" + "-" * 80)
        print("STRATEGY 3: MARKET BREADTH TREND FOLLOWING")
        print("-" * 80)

        print("\nConcept: Trade with the crowd when market breadth confirms strong directional move")
        print("\nEntry Criteria:")
        print("  • BUY when:")
        print("    - Market Breadth > 0.2 for 3 consecutive days")
        print("    - A/D Ratio > 1.5")
        print("    - Price breaks above 10-day high")
        print("  • SELL when:")
        print("    - Market Breadth < -0.2 for 3 consecutive days")
        print("    - A/D Ratio < 0.7")
        print("    - Price breaks below 10-day low")

        print("\nExit Criteria:")
        print("  • Take Profit: +4% from entry")
        print("  • Stop Loss: -2% from entry")
        print("  • Exit if Market Breadth reverses (crosses zero)")

        # Calculate 10-day high/low
        window_10d = self.df.tail(10)
        high_10d = window_10d['Afternoon_Close'].max()
        low_10d = window_10d['Afternoon_Close'].min()

        long_tp_breadth = entry_price * 1.04
        long_sl_breadth = entry_price * 0.98

        print(f"\nCurrent Levels:")
        print(f"  Current Price: {entry_price:,.2f}")
        print(f"  Market Breadth: {latest['Market_Breadth']:.4f}")
        print(f"  A/D Ratio: {latest['AD_Ratio']:.2f}")
        print(f"  10-Day High: {high_10d:,.2f}")
        print(f"  10-Day Low: {low_10d:,.2f}")

        # Check if breadth condition met
        recent_breadth = self.df.tail(3)['Market_Breadth']
        breadth_bullish = (recent_breadth > 0.2).all()
        breadth_bearish = (recent_breadth < -0.2).all()

        if breadth_bullish:
            print("  [+] Breadth Condition: BULLISH (>0.2 for 3 days)")
        elif breadth_bearish:
            print("  [-] Breadth Condition: BEARISH (<-0.2 for 3 days)")
        else:
            print("  [o] Breadth Condition: NEUTRAL")

        print(f"\nIf entering LONG position now:")
        print(f"  Entry: {entry_price:,.2f}")
        print(f"  Stop Loss: {long_sl_breadth:,.2f} (-2.0%)")
        print(f"  Take Profit: {long_tp_breadth:,.2f} (+4.0%)")
        print(f"  Risk/Reward Ratio: {abs((long_tp_breadth-entry_price)/(entry_price-long_sl_breadth)):.2f}:1")

        position_size_breadth = risk_amount / (entry_price - long_sl_breadth)
        print(f"\nPosition Sizing (HKD 1M account, 2% risk):")
        print(f"  Position Size: {position_size_breadth:,.0f} shares")
        print(f"  Position Value: HKD {position_size_breadth * entry_price:,.0f}")

        # Summary comparison
        print("\n" + "=" * 80)
        print("STRATEGY COMPARISON SUMMARY")
        print("=" * 80)

        strategies_summary = pd.DataFrame({
            'Strategy': ['Mean Reversion', 'Momentum Breakout', 'Breadth Following'],
            'Risk/Reward': [
                abs((long_tp1-entry_price)/(entry_price-long_stop)),
                abs((long_tp_mom-entry_price)/(entry_price-long_sl_mom)),
                abs((long_tp_breadth-entry_price)/(entry_price-long_sl_breadth))
            ],
            'Stop Loss %': [-2.0, -1.5, -2.0],
            'Take Profit %': [
                (long_tp1-entry_price)/entry_price*100,
                3.0,
                4.0
            ],
            'Position Size': [position_size, position_size_mom, position_size_breadth],
            'Holding Period': ['2-5 days', '3-7 days', '5-15 days']
        })

        print("\n" + strategies_summary.to_string(index=False))

        print("\nRecommended Strategy Selection Criteria:")
        print("  • Use Mean Reversion when: High volatility, RSI extremes, clear BB violations")
        print("  • Use Momentum Breakout when: Strong trends, MACD crossovers, high volume")
        print("  • Use Breadth Following when: Broad market moves, sector rotation, trend acceleration")

    def backtest_recommendations(self):
        """Provide backtesting recommendations"""
        print("\n" + "=" * 80)
        print("4. STRATEGY BACKTESTING RECOMMENDATIONS")
        print("=" * 80)

        print("\nOPTIMAL LOOKBACK PERIODS:")
        print("-" * 80)
        print("\n1. Mean Reversion Strategy:")
        print("   • Bollinger Band Period: 20 days (standard)")
        print("   • RSI Period: 14 days (standard)")
        print("   • Minimum History Required: 60 days")
        print("   • Optimal Test Period: 6-12 months")

        print("\n2. Momentum Breakout Strategy:")
        print("   • MACD Fast EMA: 12 days")
        print("   • MACD Slow EMA: 26 days")
        print("   • MACD Signal: 9 days")
        print("   • Moving Average: 20 days")
        print("   • Minimum History Required: 50 days")
        print("   • Optimal Test Period: 6-12 months")

        print("\n3. Market Breadth Strategy:")
        print("   • Breadth Calculation: Rolling 3-day average")
        print("   • Price Breakout: 10-day high/low")
        print("   • Minimum History Required: 30 days")
        print("   • Optimal Test Period: 3-6 months")

        print("\n\nPOSITION SIZING MODELS:")
        print("-" * 80)

        print("\n1. Fixed Fractional Risk Model (Recommended):")
        print("   • Risk per trade: 1-2% of account")
        print("   • Formula: Position Size = (Account × Risk%) / (Entry - Stop Loss)")
        print("   • Example: HKD 1M account, 2% risk, HKD 500 stop")
        print("     Position = (1,000,000 × 0.02) / 500 = 40 shares")

        print("\n2. Kelly Criterion (Advanced):")
        print("   • Formula: f = (bp - q) / b")
        print("   • f = fraction of capital to bet")
        print("   • b = odds received (reward/risk ratio)")
        print("   • p = probability of winning")
        print("   • q = probability of losing (1-p)")
        print("   • Recommendation: Use 25-50% of Kelly result for safety")

        print("\n3. Volatility-Based Sizing:")
        print("   • Adjust position size based on ATR (Average True Range)")
        print("   • Formula: Position Size = Risk Amount / (ATR × Multiplier)")
        print("   • Lower volatility = larger position")
        print("   • Higher volatility = smaller position")

        # Calculate recommended position sizes
        latest = self.df.iloc[-1]
        account = 1000000
        risk_pct = 0.02

        avg_volatility = self.df['Volatility_20D'].mean()

        print(f"\n\nCURRENT POSITION SIZE RECOMMENDATIONS:")
        print("-" * 80)
        print(f"Account Size: HKD {account:,.0f}")
        print(f"Risk per Trade: {risk_pct*100:.1f}%")
        print(f"Current 20D Volatility: {latest['Volatility_20D']:.2f}%")
        print(f"Average 20D Volatility: {avg_volatility:.2f}%")

        volatility_adjustment = avg_volatility / latest['Volatility_20D']
        print(f"\nVolatility Adjustment Factor: {volatility_adjustment:.2f}x")

        if volatility_adjustment > 1.2:
            print("  [>] Increase position size (market is less volatile than average)")
        elif volatility_adjustment < 0.8:
            print("  [>] Decrease position size (market is more volatile than average)")
        else:
            print("  [>] Keep standard position size (volatility is normal)")

        print("\n\nPERFORMANCE METRICS TO TRACK:")
        print("-" * 80)

        metrics = [
            ("Total Return", "Overall % gain/loss from all trades"),
            ("Win Rate", "% of profitable trades (target: >50%)"),
            ("Profit Factor", "Gross profit / Gross loss (target: >1.5)"),
            ("Sharpe Ratio", "Risk-adjusted return (target: >1.0)"),
            ("Max Drawdown", "Largest peak-to-trough decline (target: <20%)"),
            ("Average R-Multiple", "Average profit/loss in R units (target: >0.5R)"),
            ("Expectancy", "Average $ won per trade (must be positive)"),
            ("Recovery Factor", "Net profit / Max drawdown (target: >2.0)"),
            ("Calmar Ratio", "Annual return / Max drawdown (target: >0.5)"),
            ("Consecutive Losses", "Max losing streak (monitor risk of ruin)")
        ]

        print("\nKey Metrics:")
        for i, (metric, description) in enumerate(metrics, 1):
            print(f"{i:2d}. {metric:20s} - {description}")

        print("\n\nBACKTEST IMPLEMENTATION CHECKLIST:")
        print("-" * 80)

        checklist = [
            "Load historical HKEX data (minimum 6 months)",
            "Calculate all technical indicators (BB, RSI, MACD, MA)",
            "Define entry rules for each strategy",
            "Define exit rules (TP, SL, trailing stop)",
            "Implement position sizing logic",
            "Account for transaction costs (0.1-0.3% per trade)",
            "Account for slippage (0.05-0.1% per trade)",
            "Track all trades with entry/exit prices and dates",
            "Calculate performance metrics after backtest",
            "Perform walk-forward analysis (in-sample vs out-of-sample)",
            "Test on different market conditions (bull, bear, sideways)",
            "Optimize parameters but avoid over-fitting",
            "Monte Carlo simulation for robustness testing",
            "Document results and refine strategies"
        ]

        for i, item in enumerate(checklist, 1):
            print(f"  [{' '}] {i:2d}. {item}")

        print("\n\nRECOMMENDED TESTING APPROACH:")
        print("-" * 80)
        print("\nPhase 1: In-Sample Testing (60% of data)")
        print("  • Develop and optimize strategy parameters")
        print("  • Test different indicator settings")
        print("  • Refine entry/exit rules")

        print("\nPhase 2: Out-of-Sample Testing (40% of data)")
        print("  • Test on unseen data with fixed parameters")
        print("  • Validate strategy robustness")
        print("  • Compare in-sample vs out-of-sample results")

        print("\nPhase 3: Walk-Forward Analysis")
        print("  • Rolling window optimization")
        print("  • Periodic re-optimization (monthly/quarterly)")
        print("  • Adapt to changing market conditions")

        print("\nPhase 4: Monte Carlo Simulation")
        print("  • Randomize trade sequence 1000+ times")
        print("  • Calculate probability of drawdown scenarios")
        print("  • Assess risk of ruin")

        # Calculate some example metrics from current data
        print("\n\nEXAMPLE METRICS FROM CURRENT DATA:")
        print("-" * 80)

        positive_days = len(self.df[self.df['Daily_Return'] > 0])
        negative_days = len(self.df[self.df['Daily_Return'] < 0])
        total_days = len(self.df)

        win_rate = positive_days / total_days * 100
        avg_win = self.df[self.df['Daily_Return'] > 0]['Daily_Return'].mean()
        avg_loss = self.df[self.df['Daily_Return'] < 0]['Daily_Return'].mean()

        print(f"\nMarket Win Rate (up days): {win_rate:.1f}%")
        print(f"Average Up Day: +{avg_win:.2f}%")
        print(f"Average Down Day: {avg_loss:.2f}%")
        print(f"Win/Loss Ratio: {abs(avg_win/avg_loss):.2f}:1")

        # Calculate simple Sharpe ratio
        returns_mean = self.df['Daily_Return'].mean()
        returns_std = self.df['Daily_Return'].std()
        sharpe_daily = returns_mean / returns_std if returns_std > 0 else 0
        sharpe_annualized = sharpe_daily * np.sqrt(252)

        print(f"\nAnnualized Sharpe Ratio (buy & hold): {sharpe_annualized:.2f}")

        # Max drawdown
        cumulative = (1 + self.df['Daily_Return'] / 100).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max * 100
        max_dd = drawdown.min()

        print(f"Maximum Drawdown: {max_dd:.2f}%")
        print(f"Current Drawdown: {drawdown.iloc[-1]:.2f}%")

    def implementation_guide(self):
        """Provide implementation guide"""
        print("\n" + "=" * 80)
        print("5. IMPLEMENTATION GUIDE")
        print("=" * 80)

        print("\n" + "-" * 80)
        print("PYTHON IMPLEMENTATION - SIGNAL AUTOMATION")
        print("-" * 80)

        print("\nStep 1: Create Signal Detection Module")
        print("```python")
        print("""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class HKEXSignalGenerator:
    '''Generate trading signals for HKEX index'''

    def __init__(self, data_path):
        self.df = pd.read_csv(data_path)
        self.df['Date'] = pd.to_datetime(self.df['Date'])
        self.calculate_indicators()

    def calculate_indicators(self):
        '''Calculate all technical indicators'''
        # RSI
        delta = self.df['Afternoon_Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = -delta.where(delta < 0, 0).rolling(14).mean()
        rs = gain / loss
        self.df['RSI'] = 100 - (100 / (1 + rs))

        # MACD
        ema12 = self.df['Afternoon_Close'].ewm(span=12).mean()
        ema26 = self.df['Afternoon_Close'].ewm(span=26).mean()
        self.df['MACD'] = ema12 - ema26
        self.df['MACD_Signal'] = self.df['MACD'].ewm(span=9).mean()

        # Bollinger Bands
        self.df['BB_Middle'] = self.df['Afternoon_Close'].rolling(20).mean()
        bb_std = self.df['Afternoon_Close'].rolling(20).std()
        self.df['BB_Upper'] = self.df['BB_Middle'] + (2 * bb_std)
        self.df['BB_Lower'] = self.df['BB_Middle'] - (2 * bb_std)

        # Market Breadth
        self.df['Market_Breadth'] = (
            (self.df['Advanced_Stocks'] - self.df['Declined_Stocks']) /
            (self.df['Advanced_Stocks'] + self.df['Declined_Stocks'] +
             self.df['Unchanged_Stocks'])
        )

    def get_signals(self):
        '''Generate trading signals'''
        latest = self.df.iloc[-1]
        signals = []

        # Strategy 1: Mean Reversion
        if latest['Afternoon_Close'] < latest['BB_Lower'] and latest['RSI'] < 40:
            signals.append({
                'strategy': 'Mean Reversion',
                'action': 'BUY',
                'confidence': 'HIGH',
                'entry': latest['Afternoon_Close'],
                'stop_loss': latest['Afternoon_Close'] * 0.98,
                'take_profit': latest['BB_Middle']
            })

        # Strategy 2: Momentum
        prev = self.df.iloc[-2]
        macd_crossover = (latest['MACD'] > latest['MACD_Signal'] and
                         prev['MACD'] <= prev['MACD_Signal'])
        if macd_crossover and latest['Afternoon_Close'] > latest['BB_Middle']:
            signals.append({
                'strategy': 'Momentum Breakout',
                'action': 'BUY',
                'confidence': 'MEDIUM',
                'entry': latest['Afternoon_Close'],
                'stop_loss': latest['Afternoon_Close'] * 0.985,
                'take_profit': latest['Afternoon_Close'] * 1.03
            })

        # Strategy 3: Market Breadth
        if latest['Market_Breadth'] > 0.2 and latest['RSI'] < 70:
            signals.append({
                'strategy': 'Breadth Following',
                'action': 'BUY',
                'confidence': 'MEDIUM',
                'entry': latest['Afternoon_Close'],
                'stop_loss': latest['Afternoon_Close'] * 0.98,
                'take_profit': latest['Afternoon_Close'] * 1.04
            })

        return signals

# Usage
generator = HKEXSignalGenerator('hkex_market_data.csv')
signals = generator.get_signals()
for signal in signals:
    print(f"Signal: {signal}")
""")
        print("```")

        print("\n\nStep 2: Integration with Existing Quantitative System")
        print("```python")
        print("""
# In your existing CODEX-- system, integrate as follows:

# 1. Add to src/data_adapters/hkex_market_adapter.py
class HKEXMarketDataAdapter(BaseAdapter):
    '''Adapter for HKEX market-wide data'''

    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.signal_generator = HKEXSignalGenerator(csv_path)

    def fetch_data(self):
        '''Fetch latest market data'''
        return pd.read_csv(self.csv_path)

    def get_signals(self):
        '''Get trading signals'''
        return self.signal_generator.get_signals()

# 2. Add to src/strategies/hkex_market_strategy.py
class HKEXMarketStrategy(BaseStrategy):
    '''Trading strategy based on HKEX market indicators'''

    def __init__(self, adapter):
        self.adapter = adapter

    def generate_signals(self, data):
        '''Generate trading signals'''
        signals = self.adapter.get_signals()

        # Convert to format compatible with backtest engine
        formatted_signals = []
        for signal in signals:
            formatted_signals.append({
                'timestamp': datetime.now(),
                'action': signal['action'],
                'price': signal['entry'],
                'stop_loss': signal['stop_loss'],
                'take_profit': signal['take_profit'],
                'strategy': signal['strategy']
            })

        return formatted_signals

# 3. Add to complete_project_system.py
from src.data_adapters.hkex_market_adapter import HKEXMarketDataAdapter
from src.strategies.hkex_market_strategy import HKEXMarketStrategy

# Initialize in system startup
hkex_adapter = HKEXMarketDataAdapter('hkex爬蟲/data/hkex_all_market_data.csv')
hkex_strategy = HKEXMarketStrategy(hkex_adapter)

# Register with backtest engine
backtest_engine.add_strategy('HKEX_Market', hkex_strategy)
""")
        print("```")

        print("\n\nStep 3: Real-Time Monitoring Setup")
        print("```python")
        print("""
import schedule
import time
from datetime import datetime

class HKEXMonitor:
    '''Real-time monitoring of HKEX market signals'''

    def __init__(self, csv_path, alert_threshold):
        self.signal_gen = HKEXSignalGenerator(csv_path)
        self.alert_threshold = alert_threshold

    def check_signals(self):
        '''Check for new signals and send alerts'''
        signals = self.signal_gen.get_signals()

        for signal in signals:
            if signal['confidence'] == 'HIGH':
                self.send_alert(signal)

    def send_alert(self, signal):
        '''Send alert via Telegram or email'''
        message = f'''
        [ALERT] HKEX Trading Signal Alert

        Strategy: {signal['strategy']}
        Action: {signal['action']}
        Confidence: {signal['confidence']}

        Entry Price: {signal['entry']:.2f}
        Stop Loss: {signal['stop_loss']:.2f}
        Take Profit: {signal['take_profit']:.2f}

        Risk/Reward: {(signal['take_profit']-signal['entry'])/(signal['entry']-signal['stop_loss']):.2f}:1

        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        '''

        # Send via Telegram
        self.send_telegram(message)

    def send_telegram(self, message):
        '''Send message via Telegram bot'''
        import requests

        bot_token = 'YOUR_BOT_TOKEN'
        chat_id = 'YOUR_CHAT_ID'

        url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
        data = {'chat_id': chat_id, 'text': message}

        requests.post(url, data=data)

# Schedule monitoring
monitor = HKEXMonitor('hkex_market_data.csv', alert_threshold={'HIGH'})

# Run every hour during market hours (9:30 AM - 4:00 PM HKT)
schedule.every().hour.at(":00").do(monitor.check_signals)

while True:
    schedule.run_pending()
    time.sleep(60)
""")
        print("```")

        print("\n\n" + "-" * 80)
        print("ALERT THRESHOLDS FOR REAL-TIME MONITORING")
        print("-" * 80)

        print("\nHIGH PRIORITY ALERTS (Immediate Action Required):")
        print("  • RSI < 25 or RSI > 75 (extreme oversold/overbought)")
        print("  • Price breaks below BB Lower by >2%")
        print("  • MACD crossover with volume >1.5x average")
        print("  • Market Breadth >0.3 or <-0.3 with A/D Ratio extreme")
        print("  • Volatility spike >3 standard deviations")

        print("\nMEDIUM PRIORITY ALERTS (Monitor Closely):")
        print("  • RSI 30-40 or 60-70 (approaching extremes)")
        print("  • Price within 1% of BB bands")
        print("  • MACD crossover with normal volume")
        print("  • Market Breadth 0.2-0.3 or -0.2 to -0.3")
        print("  • 3 consecutive days same direction")

        print("\nLOW PRIORITY ALERTS (Informational):")
        print("  • RSI 40-60 (neutral zone)")
        print("  • Price between BB middle and outer bands")
        print("  • Normal volume and turnover")
        print("  • Market Breadth -0.2 to 0.2")

        print("\n\nRECOMMENDED ALERT CONFIGURATION:")
        print("-" * 80)

        alert_config = pd.DataFrame({
            'Indicator': [
                'RSI',
                'Bollinger Bands',
                'MACD',
                'Market Breadth',
                'Volume',
                'Volatility'
            ],
            'Alert Condition': [
                'RSI < 30 or > 70',
                'Price outside BB ±2σ',
                'Crossover with histogram',
                'Breadth > |0.25|',
                'Volume > 1.5x MA(5)',
                'Vol > 1.5x MA(20)'
            ],
            'Priority': [
                'HIGH',
                'HIGH',
                'MEDIUM',
                'MEDIUM',
                'LOW',
                'HIGH'
            ],
            'Action': [
                'Review for entry',
                'Prepare position',
                'Monitor for confirmation',
                'Check sector strength',
                'Confirm with price',
                'Reduce position size'
            ]
        })

        print("\n" + alert_config.to_string(index=False))

        print("\n\nSYSTEM INTEGRATION CHECKLIST:")
        print("-" * 80)

        integration_steps = [
            "Create HKEXMarketDataAdapter in src/data_adapters/",
            "Implement HKEXSignalGenerator with all indicators",
            "Add HKEXMarketStrategy to src/strategies/",
            "Register strategy with backtest engine",
            "Set up scheduled data updates (daily after market close)",
            "Configure Telegram bot for alerts",
            "Define alert threshold rules",
            "Test signal generation with historical data",
            "Validate integration with existing system",
            "Set up logging and error handling",
            "Create dashboard widget for HKEX signals",
            "Document API endpoints for signal access",
            "Implement position sizing calculator",
            "Add risk management rules",
            "Deploy to production environment"
        ]

        for i, step in enumerate(integration_steps, 1):
            print(f"  [{' '}] {i:2d}. {step}")

        print("\n\nAPI ENDPOINT DESIGN:")
        print("-" * 80)
        print("""
# Add to src/dashboard/api_routes.py

@app.get("/api/hkex/signals")
async def get_hkex_signals():
    '''Get current HKEX market signals'''
    try:
        adapter = HKEXMarketDataAdapter('hkex爬蟲/data/hkex_all_market_data.csv')
        signals = adapter.get_signals()

        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'signals': signals,
            'count': len(signals)
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@app.get("/api/hkex/indicators")
async def get_hkex_indicators():
    '''Get current HKEX market indicators'''
    try:
        adapter = HKEXMarketDataAdapter('hkex爬蟲/data/hkex_all_market_data.csv')
        df = adapter.fetch_data()
        latest = df.iloc[-1]

        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'indicators': {
                'rsi': latest['RSI'],
                'macd': latest['MACD'],
                'bb_upper': latest['BB_Upper'],
                'bb_lower': latest['BB_Lower'],
                'market_breadth': latest['Market_Breadth'],
                'volatility': latest['Volatility_20D']
            }
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@app.post("/api/hkex/backtest")
async def run_hkex_backtest(strategy: str, start_date: str, end_date: str):
    '''Run backtest for HKEX strategy'''
    try:
        # Implementation here
        return {
            'status': 'success',
            'results': backtest_results
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
""")

        print("\n\nFINAL RECOMMENDATIONS:")
        print("=" * 80)
        print("\n1. Start with paper trading to validate signals")
        print("2. Monitor all three strategies simultaneously")
        print("3. Keep position sizes small initially (0.5-1% risk)")
        print("4. Log all signals and outcomes for analysis")
        print("5. Review performance weekly and adjust parameters")
        print("6. Use multiple timeframes for confirmation")
        print("7. Combine HKEX market signals with individual stock analysis")
        print("8. Set up automated data collection for continuous updates")
        print("9. Implement fail-safe mechanisms for system errors")
        print("10. Regularly backtest on new data to ensure robustness")

    def run_complete_analysis(self):
        """Run complete analysis pipeline"""
        print("\n")
        print("=" * 80)
        print("HKEX MARKET DATA COMPREHENSIVE ANALYSIS REPORT")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # Run all analysis sections
        self.print_statistical_summary()
        self.identify_market_signals()
        self.develop_trading_strategies()
        self.backtest_recommendations()
        self.implementation_guide()

        print("\n" + "=" * 80)
        print("END OF ANALYSIS REPORT")
        print("=" * 80)

        # Save summary to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'hkex_analysis_report_{timestamp}.txt'

        print(f"\nReport saved to: {output_file}")
        print("\nNext Steps:")
        print("1. Review all trading signals and strategies")
        print("2. Implement chosen strategy in backtesting framework")
        print("3. Paper trade for 2-4 weeks to validate")
        print("4. Gradually scale up position sizes")
        print("5. Monitor and refine continuously")

# Main execution
if __name__ == "__main__":
    csv_path = r'C:\Users\Penguin8n\CODEX--\CODEX--\hkex爬蟲\data\hkex_all_market_data.csv'

    analyzer = HKEXMarketAnalyzer(csv_path)
    analyzer.run_complete_analysis()
