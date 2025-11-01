#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xlsx Stock Analysis - Main Analyzer
使用 xlsx 技能進行股票數據分析和可視化
"""

import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class XlsxStockAnalyzer:
    """xlsx 股票分析器"""

    def __init__(self, data_dir: str = "."):
        """初始化分析器

        Args:
            data_dir: 數據目錄路徑
        """
        self.data_dir = data_dir
        self.test_data_dir = "test_data"
        self.processed_data_dir = "processed_data"
        self.stock_data = None
        self.strategy_data = {}
        self.analysis_results = {}

    def load_test_data(self) -> bool:
        """載入測試數據

        Returns:
            bool: 載入是否成功
        """
        logger.info("Loading test data using xlsx skills...")

        try:
            # 讀取股票數據
            stock_file = f"{self.test_data_dir}/test_stock_0001_HK.csv"
            self.stock_data = pd.read_csv(stock_file, index_col=0, parse_dates=True)
            logger.info(f"Loaded stock data: {self.stock_data.shape}")

            # 讀取策略數據
            strategies = ['boll', 'rsi']
            for strategy in strategies:
                strategy_file = f"{self.test_data_dir}/test_strategy_{strategy}.csv"
                self.strategy_data[strategy] = pd.read_csv(
                    strategy_file, index_col=0, parse_dates=True
                )
                logger.info(f"Loaded {strategy} strategy: {self.strategy_data[strategy].shape}")

            # 讀取策略摘要
            summary_file = f"{self.test_data_dir}/test_strategy_summary.json"
            with open(summary_file, 'r') as f:
                self.analysis_results['strategy_summary'] = json.load(f)

            logger.info("Test data loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load test data: {str(e)}")
            return False

    def calculate_performance_metrics(self) -> Dict:
        """計算績效指標

        Returns:
            Dict: 績效指標字典
        """
        logger.info("Calculating performance metrics...")

        metrics = {
            'stock': {},
            'strategies': {}
        }

        # 計算股票指標
        if self.stock_data is not None:
            prices = self.stock_data['close']
            returns = prices.pct_change().dropna()

            # 基礎指標
            total_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
            annualized_return = ((prices.iloc[-1] / prices.iloc[0]) ** (252 / len(returns)) - 1) * 100
            volatility = returns.std() * np.sqrt(252) * 100

            # 最大回撤
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min() * 100

            # 夏普比率（假設無風險利率為 0）
            sharpe_ratio = annualized_return / volatility if volatility > 0 else 0

            metrics['stock'] = {
                'total_return': round(total_return, 2),
                'annualized_return': round(annualized_return, 2),
                'volatility': round(volatility, 2),
                'sharpe_ratio': round(sharpe_ratio, 2),
                'max_drawdown': round(max_drawdown, 2),
                'trading_days': len(returns)
            }

            logger.info(f"Stock metrics: {metrics['stock']}")

        # 計算策略指標
        for strategy_name, strategy_df in self.strategy_data.items():
            strategy_returns = strategy_df.iloc[:, 1]  # 第二列是策略收益
            stock_returns = strategy_df.iloc[:, 0]     # 第一列是買入持有收益

            # 策略總收益
            strategy_total_return = (strategy_returns.iloc[-1] - 1) * 100

            # 超額收益
            stock_total_return = (stock_returns.iloc[-1] - 1) * 100
            excess_return = strategy_total_return - stock_total_return

            # 最大回撤
            cumulative_strategy = strategy_returns
            running_max = cumulative_strategy.expanding().max()
            drawdown = (cumulative_strategy - running_max) / running_max
            max_drawdown = drawdown.min() * 100

            # 勝率
            winning_days = (strategy_returns.diff() > 0).sum()
            win_rate = (winning_days / len(strategy_returns)) * 100

            metrics['strategies'][strategy_name] = {
                'total_return': round(strategy_total_return, 2),
                'excess_return': round(excess_return, 2),
                'max_drawdown': round(max_drawdown, 2),
                'win_rate': round(win_rate, 2),
                'final_value': round(strategy_returns.iloc[-1], 4)
            }

            logger.info(f"{strategy_name.upper()} metrics: {metrics['strategies'][strategy_name]}")

        self.analysis_results['performance_metrics'] = metrics
        return metrics

    def analyze_correlations(self) -> Dict:
        """分析策略間相關性

        Returns:
            Dict: 相關性分析結果
        """
        logger.info("Analyzing strategy correlations...")

        if len(self.strategy_data) < 2:
            logger.warning("Need at least 2 strategies for correlation analysis")
            return {}

        # 合併所有策略數據
        merged_df = pd.DataFrame()
        for name, df in self.strategy_data.items():
            merged_df[name] = df.iloc[:, 1]  # 策略收益列

        # 計算相關性矩陣
        correlation_matrix = merged_df.corr()
        logger.info(f"Correlation matrix:\n{correlation_matrix}")

        # 計算滾動相關性（30日）
        rolling_corr = merged_df.rolling(window=30).corr()

        self.analysis_results['correlations'] = {
            'correlation_matrix': correlation_matrix.to_dict(),
            'average_correlation': correlation_matrix.mean().mean()
        }

        return self.analysis_results['correlations']

    def generate_monthly_returns(self) -> Dict:
        """生成月度收益數據

        Returns:
            Dict: 月度收益數據
        """
        logger.info("Generating monthly returns...")

        monthly_returns = {}

        # 股票月度收益
        if self.stock_data is not None:
            stock_monthly = self.stock_data['close'].resample('M').last().pct_change().dropna()
            monthly_returns['stock'] = {
                'returns': stock_monthly.to_dict(),
                'avg_monthly': stock_monthly.mean() * 100,
                'best_month': stock_monthly.max() * 100,
                'worst_month': stock_monthly.min() * 100
            }

        # 策略月度收益
        for name, df in self.strategy_data.items():
            monthly_strategy = df.iloc[:, 1].resample('M').last().pct_change().dropna()
            monthly_returns[name] = {
                'returns': monthly_strategy.to_dict(),
                'avg_monthly': monthly_strategy.mean() * 100,
                'best_month': monthly_strategy.max() * 100,
                'worst_month': monthly_strategy.min() * 100
            }

        self.analysis_results['monthly_returns'] = monthly_returns
        return monthly_returns

    def create_summary_data(self) -> Dict:
        """創建摘要數據（用於Excel報告）

        Returns:
            Dict: 摘要數據
        """
        logger.info("Creating summary data...")

        summary = {
            'report_info': {
                'title': 'xlsx Stock Analysis Report',
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'stock_symbol': '0001.HK',
                'period': f"{self.stock_data.index[0].strftime('%Y-%m-%d')} to {self.stock_data.index[-1].strftime('%Y-%m-%d')}",
                'trading_days': len(self.stock_data)
            },
            'key_metrics': self.analysis_results.get('performance_metrics', {}),
            'strategy_comparison': self._create_strategy_comparison(),
            'risk_analysis': self._create_risk_analysis(),
            'recommendations': self._generate_recommendations()
        }

        self.analysis_results['summary'] = summary
        return summary

    def _create_strategy_comparison(self) -> List[Dict]:
        """創建策略比較表

        Returns:
            List[Dict]: 策略比較數據
        """
        comparison = []
        metrics = self.analysis_results.get('performance_metrics', {}).get('strategies', {})

        for strategy_name, data in metrics.items():
            comparison.append({
                'strategy': strategy_name.upper(),
                'total_return': data['total_return'],
                'excess_return': data['excess_return'],
                'max_drawdown': data['max_drawdown'],
                'win_rate': data['win_rate'],
                'sharpe_estimate': data['total_return'] / abs(data['max_drawdown']) if data['max_drawdown'] != 0 else 0
            })

        return comparison

    def _create_risk_analysis(self) -> Dict:
        """創建風險分析

        Returns:
            Dict: 風險分析數據
        """
        risk = {
            'stock_risk_level': 'High' if self.analysis_results.get('performance_metrics', {}).get('stock', {}).get('volatility', 0) > 30 else 'Medium',
            'strategy_risk_levels': {},
            'correlation_risk': 'Low' if self.analysis_results.get('correlations', {}).get('average_correlation', 1) < 0.7 else 'Medium'
        }

        # 分析各策略風險級別
        for name, data in self.analysis_results.get('performance_metrics', {}).get('strategies', {}).items():
            if abs(data['max_drawdown']) > 30:
                risk['strategy_risk_levels'][name] = 'High'
            elif abs(data['max_drawdown']) > 15:
                risk['strategy_risk_levels'][name] = 'Medium'
            else:
                risk['strategy_risk_levels'][name] = 'Low'

        return risk

    def _generate_recommendations(self) -> List[str]:
        """生成投資建議

        Returns:
            List[str]: 建議列表
        """
        recommendations = []
        metrics = self.analysis_results.get('performance_metrics', {})

        # 基於策略表現給出建議
        if 'strategies' in metrics:
            best_strategy = max(
                metrics['strategies'].items(),
                key=lambda x: x[1]['total_return']
            )[0]

            recommendations.append(f"Best performing strategy: {best_strategy.upper()}")

            # 基於夏普比率建議
            if 'stock' in metrics and metrics['stock']['sharpe_ratio'] < 0.5:
                recommendations.append("Consider using technical strategies to improve risk-adjusted returns")

            # 基於最大回撤建議
            if 'stock' in metrics and metrics['stock']['max_drawdown'] < -20:
                recommendations.append("High volatility detected - consider position sizing and stop-loss strategies")

        return recommendations

    def export_analysis_results(self, output_file: str = "analysis_results.json"):
        """導出分析結果

        Args:
            output_file: 輸出文件名
        """
        output_path = f"{self.data_dir}/{output_file}"

        # 轉換所有 Timestamp 對象為字符串
        def convert_timestamps(obj):
            if isinstance(obj, dict):
                return {str(k): convert_timestamps(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_timestamps(item) for item in obj]
            elif pd.isna(obj):
                return None
            else:
                return obj

        cleaned_results = convert_timestamps(self.analysis_results)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_results, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Analysis results exported to: {output_path}")

    def run_full_analysis(self) -> bool:
        """運行完整分析

        Returns:
            bool: 分析是否成功
        """
        logger.info("Starting full analysis...")

        # 1. 載入數據
        if not self.load_test_data():
            return False

        # 2. 計算績效指標
        self.calculate_performance_metrics()

        # 3. 分析相關性
        self.analyze_correlations()

        # 4. 生成月度收益
        self.generate_monthly_returns()

        # 5. 創建摘要
        self.create_summary_data()

        # 6. 導出結果
        self.export_analysis_results()

        logger.info("Full analysis completed successfully")
        return True

    def print_summary(self):
        """打印分析摘要"""
        if 'summary' not in self.analysis_results:
            print("No analysis results available. Run analysis first.")
            return

        summary = self.analysis_results['summary']

        print("\n" + "=" * 60)
        print(" xlsx STOCK ANALYSIS SUMMARY")
        print("=" * 60)

        print(f"\nReport Info:")
        info = summary['report_info']
        print(f"  Title: {info['title']}")
        print(f"  Stock: {info['stock_symbol']}")
        print(f"  Period: {info['period']}")
        print(f"  Trading Days: {info['trading_days']}")

        print(f"\nKey Metrics:")
        if 'stock' in summary['key_metrics']:
            stock = summary['key_metrics']['stock']
            print(f"  Stock Performance:")
            print(f"    Total Return: {stock['total_return']}%")
            print(f"    Annualized Return: {stock['annualized_return']}%")
            print(f"    Volatility: {stock['volatility']}%")
            print(f"    Sharpe Ratio: {stock['sharpe_ratio']}")
            print(f"    Max Drawdown: {stock['max_drawdown']}%")

        if 'strategies' in summary['key_metrics']:
            print(f"\n  Strategy Performance:")
            for name, data in summary['key_metrics']['strategies'].items():
                print(f"    {name.upper()}:")
                print(f"      Total Return: {data['total_return']}%")
                print(f"      Excess Return: {data['excess_return']}%")
                print(f"      Max Drawdown: {data['max_drawdown']}%")
                print(f"      Win Rate: {data['win_rate']}%")

        print(f"\nRecommendations:")
        for i, rec in enumerate(summary['recommendations'], 1):
            print(f"  {i}. {rec}")

        print("\n" + "=" * 60)


def main():
    """主函數"""
    analyzer = XlsxStockAnalyzer()

    # 運行完整分析
    if analyzer.run_full_analysis():
        # 打印摘要
        analyzer.print_summary()
        print("\nAnalysis results saved to 'analysis_results.json'")
    else:
        print("Analysis failed. Check logs for details.")


if __name__ == "__main__":
    main()
