"""
6-Month HIBOR Prediction Strategy Backtester
==============================================

Based on Granger causality findings, this strategy uses 6M HIBOR changes
to predict market movements 1-5 days ahead.

Key Finding: 6M HIBOR Granger-causes market returns with statistical significance
at all lags from 1 to 5 days (p < 0.05).
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configuration
DATA_PATH = r"C:\Users\Penguin8n\CODEX--\CODEX--\analysis_output\merged_dataset_20251024_035022.csv"
OUTPUT_DIR = r"C:\Users\Penguin8n\CODEX--\CODEX--\analysis_output"


class HIBOR6MStrategy:
    """
    Trading strategy based on 6-month HIBOR changes
    """

    def __init__(self, hibor_threshold=0.0005, holding_period=3, position_size=0.30):
        """
        Parameters:
        -----------
        hibor_threshold : float
            Minimum HIBOR change to trigger signal (0.05%)
        holding_period : int
            Days to hold position after signal
        position_size : float
            Position size as fraction of capital (0.30 = 30%)
        """
        self.hibor_threshold = hibor_threshold
        self.holding_period = holding_period
        self.position_size = position_size
        self.data = None
        self.signals = None
        self.backtest_results = None

    def load_data(self):
        """Load merged dataset"""
        print("=" * 80)
        print("LOADING DATA")
        print("=" * 80)

        self.data = pd.read_csv(DATA_PATH)
        self.data['Date'] = pd.to_datetime(self.data['Date'])

        # Calculate returns if not present
        if 'Returns' not in self.data.columns:
            self.data['Returns'] = self.data['Afternoon_Close'].pct_change()

        # Calculate HIBOR changes
        self.data['hibor_6m_change'] = self.data['hibor_6m'].diff()
        self.data['hibor_6m_pct_change'] = self.data['hibor_6m'].pct_change()

        print(f"\nLoaded {len(self.data)} trading days")
        print(f"Date range: {self.data['Date'].min()} to {self.data['Date'].max()}")

        return self

    def generate_signals(self):
        """Generate trading signals based on 6M HIBOR changes"""
        print("\n" + "=" * 80)
        print("GENERATING TRADING SIGNALS")
        print("=" * 80)

        # Initialize signal column
        self.data['signal'] = 0  # 0 = No position, 1 = Long, -1 = Short

        # Logic:
        # - When 6M HIBOR rises significantly, market tends to fall -> SHORT
        # - When 6M HIBOR falls significantly, market tends to rise -> LONG

        for i in range(1, len(self.data)):
            hibor_change = self.data.loc[i, 'hibor_6m_change']

            # Generate signal
            if hibor_change < -self.hibor_threshold:
                # HIBOR falling -> LONG signal
                self.data.loc[i, 'signal'] = 1
            elif hibor_change > self.hibor_threshold:
                # HIBOR rising -> SHORT signal
                self.data.loc[i, 'signal'] = -1

        # Apply holding period
        self.data['position'] = 0

        for i in range(len(self.data)):
            if self.data.loc[i, 'signal'] != 0:
                # Hold position for specified days
                end_idx = min(i + self.holding_period, len(self.data))
                self.data.loc[i:end_idx, 'position'] = self.data.loc[i, 'signal']

        # Count signals
        long_signals = (self.data['signal'] == 1).sum()
        short_signals = (self.data['signal'] == -1).sum()
        total_signals = long_signals + short_signals

        print(f"\nSignal Summary:")
        print(f"- Total Signals: {total_signals}")
        print(f"- Long Signals: {long_signals} ({long_signals/total_signals*100:.1f}%)")
        print(f"- Short Signals: {short_signals} ({short_signals/total_signals*100:.1f}%)")
        print(f"- Signal Frequency: {total_signals/len(self.data)*100:.1f}% of days")

        self.signals = self.data.copy()
        return self

    def backtest(self, initial_capital=100000, transaction_cost=0.001):
        """
        Backtest the strategy

        Parameters:
        -----------
        initial_capital : float
            Starting capital in HKD
        transaction_cost : float
            Transaction cost as fraction (0.001 = 0.1%)
        """
        print("\n" + "=" * 80)
        print("RUNNING BACKTEST")
        print("=" * 80)

        # Initialize
        capital = initial_capital
        position = 0
        equity_curve = [capital]
        trades = []

        for i in range(1, len(self.data)):
            current_position = self.data.loc[i, 'position']
            previous_position = self.data.loc[i-1, 'position']

            # Check for position change
            if current_position != previous_position and current_position != 0:
                # Close previous position if exists
                if previous_position != 0:
                    # Calculate P&L
                    price_change = self.data.loc[i, 'Returns']
                    pnl = capital * self.position_size * previous_position * price_change
                    pnl -= abs(capital * self.position_size) * transaction_cost  # Exit cost
                    capital += pnl

                    trades.append({
                        'exit_date': self.data.loc[i, 'Date'],
                        'direction': 'LONG' if previous_position == 1 else 'SHORT',
                        'pnl': pnl,
                        'pnl_pct': (pnl / capital) * 100
                    })

                # Enter new position
                position = current_position
                capital -= abs(capital * self.position_size) * transaction_cost  # Entry cost

            # Calculate equity if in position
            if current_position != 0:
                price_change = self.data.loc[i, 'Returns']
                daily_pnl = capital * self.position_size * current_position * price_change
                capital += daily_pnl

            equity_curve.append(capital)

        # Store results
        self.data['equity'] = equity_curve

        # Calculate metrics
        total_return = (capital - initial_capital) / initial_capital
        num_trades = len(trades)

        if num_trades > 0:
            trades_df = pd.DataFrame(trades)
            win_trades = trades_df[trades_df['pnl'] > 0]
            loss_trades = trades_df[trades_df['pnl'] < 0]

            win_rate = len(win_trades) / num_trades
            avg_win = win_trades['pnl'].mean() if len(win_trades) > 0 else 0
            avg_loss = loss_trades['pnl'].mean() if len(loss_trades) > 0 else 0
            profit_factor = abs(win_trades['pnl'].sum() / loss_trades['pnl'].sum()) if len(loss_trades) > 0 else np.inf

            # Calculate drawdown
            equity_series = pd.Series(equity_curve)
            running_max = equity_series.cummax()
            drawdown = (equity_series - running_max) / running_max
            max_drawdown = drawdown.min()

            # Calculate Sharpe ratio
            daily_returns = equity_series.pct_change().dropna()
            sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252) if daily_returns.std() > 0 else 0

            # Print results
            print(f"\n{'BACKTEST RESULTS':^80}")
            print("=" * 80)
            print(f"\nCapital:")
            print(f"  Initial Capital:     HKD {initial_capital:,.2f}")
            print(f"  Final Capital:       HKD {capital:,.2f}")
            print(f"  Total Return:        {total_return:.2%}")
            print(f"  Annualized Return:   {(total_return / (len(self.data)/252)):.2%}")

            print(f"\nRisk Metrics:")
            print(f"  Max Drawdown:        {max_drawdown:.2%}")
            print(f"  Sharpe Ratio:        {sharpe_ratio:.4f}")
            print(f"  Volatility (daily):  {daily_returns.std():.2%}")
            print(f"  Volatility (annual): {daily_returns.std() * np.sqrt(252):.2%}")

            print(f"\nTrading Statistics:")
            print(f"  Total Trades:        {num_trades}")
            print(f"  Win Rate:            {win_rate:.2%}")
            print(f"  Profit Factor:       {profit_factor:.2f}")
            print(f"  Avg Win:             HKD {avg_win:,.2f} ({avg_win/capital*100:.2%})")
            print(f"  Avg Loss:            HKD {avg_loss:,.2f} ({avg_loss/capital*100:.2%})")

            # Compare to buy-and-hold
            bh_return = (self.data['Afternoon_Close'].iloc[-1] /
                        self.data['Afternoon_Close'].iloc[0]) - 1

            print(f"\nComparison to Buy & Hold:")
            print(f"  Buy & Hold Return:   {bh_return:.2%}")
            print(f"  Strategy Return:     {total_return:.2%}")
            print(f"  Excess Return:       {(total_return - bh_return):.2%}")

            self.backtest_results = {
                'initial_capital': initial_capital,
                'final_capital': capital,
                'total_return': total_return,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'num_trades': num_trades,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'trades': trades_df
            }

        else:
            print("\nNo trades executed during backtest period")
            self.backtest_results = None

        return self

    def plot_results(self):
        """Generate visualization plots"""
        print("\n" + "=" * 80)
        print("GENERATING VISUALIZATIONS")
        print("=" * 80)

        if self.backtest_results is None:
            print("No backtest results to plot")
            return self

        fig = plt.figure(figsize=(16, 12))

        # 1. Equity curve
        ax1 = plt.subplot(3, 2, 1)
        ax1.plot(self.data['Date'], self.data['equity'], linewidth=2, color='blue', label='Strategy')

        # Buy & Hold comparison
        bh_equity = (self.data['Afternoon_Close'] / self.data['Afternoon_Close'].iloc[0]) * self.backtest_results['initial_capital']
        ax1.plot(self.data['Date'], bh_equity, linewidth=2, color='gray', linestyle='--', label='Buy & Hold', alpha=0.7)

        ax1.set_title('Equity Curve Comparison', fontweight='bold', fontsize=12)
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Equity (HKD)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 2. Drawdown
        ax2 = plt.subplot(3, 2, 2)
        equity_series = pd.Series(self.data['equity'].values)
        running_max = equity_series.cummax()
        drawdown = (equity_series - running_max) / running_max

        ax2.fill_between(range(len(drawdown)), drawdown.values, 0, color='red', alpha=0.3)
        ax2.plot(drawdown.values, linewidth=1.5, color='darkred')
        ax2.set_title(f'Drawdown (Max: {self.backtest_results["max_drawdown"]:.2%})',
                     fontweight='bold', fontsize=12)
        ax2.set_xlabel('Trading Days')
        ax2.set_ylabel('Drawdown (%)')
        ax2.grid(True, alpha=0.3)

        # 3. 6M HIBOR changes
        ax3 = plt.subplot(3, 2, 3)
        ax3.plot(self.data['Date'], self.data['hibor_6m'], linewidth=1.5, color='green')
        ax3.set_title('6-Month HIBOR Rates', fontweight='bold', fontsize=12)
        ax3.set_xlabel('Date')
        ax3.set_ylabel('HIBOR 6M (%)')
        ax3.grid(True, alpha=0.3)

        # 4. Trading signals
        ax4 = plt.subplot(3, 2, 4)
        ax4.plot(self.data['Date'], self.data['Afternoon_Close'], linewidth=1, color='blue', alpha=0.5)

        # Mark long signals
        long_signals = self.data[self.data['signal'] == 1]
        ax4.scatter(long_signals['Date'], long_signals['Afternoon_Close'],
                   color='green', marker='^', s=100, label='Long Signal', zorder=5)

        # Mark short signals
        short_signals = self.data[self.data['signal'] == -1]
        ax4.scatter(short_signals['Date'], short_signals['Afternoon_Close'],
                   color='red', marker='v', s=100, label='Short Signal', zorder=5)

        ax4.set_title('Trading Signals on Price Chart', fontweight='bold', fontsize=12)
        ax4.set_xlabel('Date')
        ax4.set_ylabel('Market Close')
        ax4.legend()
        ax4.grid(True, alpha=0.3)

        # 5. Trade P&L distribution
        ax5 = plt.subplot(3, 2, 5)
        if self.backtest_results and 'trades' in self.backtest_results:
            trades_df = self.backtest_results['trades']
            ax5.hist(trades_df['pnl_pct'], bins=20, edgecolor='black', alpha=0.7, color='skyblue')
            ax5.axvline(0, color='red', linestyle='--', linewidth=2)
            ax5.set_title('Trade P&L Distribution', fontweight='bold', fontsize=12)
            ax5.set_xlabel('P&L (%)')
            ax5.set_ylabel('Frequency')
            ax5.grid(True, alpha=0.3)

        # 6. Cumulative returns comparison
        ax6 = plt.subplot(3, 2, 6)

        # Strategy returns
        strategy_returns = pd.Series(self.data['equity'].values).pct_change().fillna(0)
        cumulative_strategy = (1 + strategy_returns).cumprod()

        # Buy & Hold returns
        bh_returns = self.data['Afternoon_Close'].pct_change().fillna(0)
        cumulative_bh = (1 + bh_returns).cumprod()

        ax6.plot(cumulative_strategy.values, linewidth=2, color='blue', label='Strategy')
        ax6.plot(cumulative_bh.values, linewidth=2, color='gray', linestyle='--', label='Buy & Hold', alpha=0.7)
        ax6.set_title('Cumulative Returns Comparison', fontweight='bold', fontsize=12)
        ax6.set_xlabel('Trading Days')
        ax6.set_ylabel('Cumulative Return')
        ax6.legend()
        ax6.grid(True, alpha=0.3)

        plt.tight_layout()

        # Save
        filepath = f"{OUTPUT_DIR}/hibor_6m_strategy_results.png"
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"\nSaved strategy results: {filepath}")
        plt.close()

        return self

    def export_results(self):
        """Export detailed results"""
        print("\n" + "=" * 80)
        print("EXPORTING RESULTS")
        print("=" * 80)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Export trades
        if self.backtest_results and 'trades' in self.backtest_results:
            filepath = f"{OUTPUT_DIR}/hibor_6m_trades_{timestamp}.csv"
            self.backtest_results['trades'].to_csv(filepath, index=False)
            print(f"\n1. Exported trades: {filepath}")

        # Export signals
        filepath = f"{OUTPUT_DIR}/hibor_6m_signals_{timestamp}.csv"
        signal_data = self.data[['Date', 'Afternoon_Close', 'hibor_6m', 'hibor_6m_change',
                                  'signal', 'position', 'Returns']].copy()
        signal_data.to_csv(filepath, index=False)
        print(f"2. Exported signals: {filepath}")

        # Export summary report
        filepath = f"{OUTPUT_DIR}/hibor_6m_strategy_report_{timestamp}.txt"
        with open(filepath, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("6-MONTH HIBOR PREDICTION STRATEGY - BACKTEST REPORT\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("STRATEGY PARAMETERS:\n")
            f.write(f"- HIBOR Threshold: {self.hibor_threshold:.4%}\n")
            f.write(f"- Holding Period: {self.holding_period} days\n")
            f.write(f"- Position Size: {self.position_size:.1%}\n\n")

            if self.backtest_results:
                f.write("BACKTEST RESULTS:\n")
                for key, value in self.backtest_results.items():
                    if key != 'trades':
                        if isinstance(value, float):
                            if 'rate' in key or 'return' in key or 'drawdown' in key:
                                f.write(f"- {key}: {value:.2%}\n")
                            else:
                                f.write(f"- {key}: {value:.4f}\n")
                        else:
                            f.write(f"- {key}: {value}\n")

        print(f"3. Exported strategy report: {filepath}")

        return self

    def run_full_analysis(self):
        """Run complete strategy analysis"""
        print("\n" + "=" * 80)
        print("6-MONTH HIBOR PREDICTION STRATEGY ANALYSIS")
        print("=" * 80)

        self.load_data()
        self.generate_signals()
        self.backtest()
        self.plot_results()
        self.export_results()

        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)

        return self


if __name__ == "__main__":
    # Run strategy with default parameters
    strategy = HIBOR6MStrategy(
        hibor_threshold=0.0005,  # 0.05% change threshold
        holding_period=3,         # Hold for 3 days
        position_size=0.30        # 30% position size
    )

    strategy.run_full_analysis()

    print("\n" + "=" * 80)
    print("PARAMETER SENSITIVITY ANALYSIS")
    print("=" * 80)

    # Test different parameters
    print("\nTesting different holding periods...")

    results_summary = []

    for holding_period in [1, 2, 3, 5]:
        print(f"\n--- Holding Period: {holding_period} days ---")

        strat = HIBOR6MStrategy(
            hibor_threshold=0.0005,
            holding_period=holding_period,
            position_size=0.30
        )

        strat.load_data()
        strat.generate_signals()
        strat.backtest()

        if strat.backtest_results:
            results_summary.append({
                'holding_period': holding_period,
                'total_return': strat.backtest_results['total_return'],
                'sharpe_ratio': strat.backtest_results['sharpe_ratio'],
                'win_rate': strat.backtest_results['win_rate'],
                'max_drawdown': strat.backtest_results['max_drawdown']
            })

    # Print summary
    if results_summary:
        print("\n" + "=" * 80)
        print("PARAMETER SENSITIVITY SUMMARY")
        print("=" * 80)

        summary_df = pd.DataFrame(results_summary)
        print("\n" + summary_df.to_string(index=False))

        # Find best parameters
        best_sharpe = summary_df.loc[summary_df['sharpe_ratio'].idxmax()]
        print(f"\nBest Sharpe Ratio Configuration:")
        print(f"  Holding Period: {best_sharpe['holding_period']:.0f} days")
        print(f"  Sharpe Ratio: {best_sharpe['sharpe_ratio']:.4f}")
        print(f"  Total Return: {best_sharpe['total_return']:.2%}")
        print(f"  Win Rate: {best_sharpe['win_rate']:.2%}")

    print("\n" + "=" * 80)
    print("STRATEGY VALIDATION COMPLETE")
    print("=" * 80)
    print("\nReview the generated files in analysis_output/ for detailed results.")
