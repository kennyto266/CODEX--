"""
T067: 零售数据回测报告生成器

生成详细的零售数据回测报告，包含:
- Sharpe Ratio (夏普比率)
- Max Drawdown (最大回撤)
- Total Return (总收益率)
- Win Rate (胜率)
- Trade Analysis (交易分析)
- Technical Indicators (技术指标)
- Visualization (可视化)

使用方法:
    python scripts/retail_backtest_report_generator.py

Author: Claude Code
Version: 1.0.0
Date: 2025-11-10
"""

import json
import logging
import matplotlib.pyplot as plt
import pandas as pd
from datetime import date
from pathlib import Path
import sys

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from backtest.retail_backtest import RetailMultiSourceBacktest


class RetailBacktestReportGenerator:
    """零售回测报告生成器"""

    def __init__(self, output_dir: Path = Path("reports")):
        """
        初始化报告生成器

        Args:
            output_dir: 报告输出目录
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 配置日志
        self.logger = logging.getLogger("retail_report_generator")

    def generate_report(
        self,
        backtest_results: dict,
        save_charts: bool = True
    ) -> str:
        """
        生成综合回测报告

        Args:
            backtest_results: 回测结果字典
            save_charts: 是否保存图表

        Returns:
            报告文件路径
        """
        try:
            # 生成文本报告
            text_report = self._generate_text_report(backtest_results)

            # 保存文本报告
            text_path = self.output_dir / "retail_backtest_detailed_report.txt"
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(text_report)

            self.logger.info(f"Text report saved to {text_path}")

            # 生成JSON报告
            json_path = self.output_dir / "retail_backtest_results.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(backtest_results, f, indent=2, default=str)

            self.logger.info(f"JSON report saved to {json_path}")

            # 生成图表
            if save_charts:
                chart_paths = self._generate_charts(backtest_results)
                self.logger.info(f"Charts saved to {self.output_dir}")

            return str(text_path)

        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            return ""

    def _generate_text_report(self, results: dict) -> str:
        """生成文本报告"""
        lines = []

        # 标题
        lines.append("=" * 100)
        lines.append(" " * 30 + "RETAIL DATA BACKTEST REPORT")
        lines.append("=" * 100)
        lines.append("")

        # 基本信息
        lines.append("BASIC INFORMATION")
        lines.append("-" * 100)
        lines.append(f"Symbol:              {results.get('symbol', 'N/A')}")
        lines.append(f"Period:              {results.get('start_date')} to {results.get('end_date')}")
        lines.append(f"Total Trades:        {results.get('total_trades', 0)}")
        lines.append(f"Buy Threshold:       {results.get('buy_threshold', 0)}")
        lines.append(f"Sell Threshold:      {results.get('sell_threshold', 0)}")
        lines.append("")

        # 核心性能指标
        lines.append("CORE PERFORMANCE METRICS")
        lines.append("-" * 100)
        perf = results.get('performance', {})

        # Sharpe Ratio
        sharpe = perf.get('sharpe_ratio', 0)
        sharpe_grade = self._get_sharpe_grade(sharpe)
        lines.append(f"Sharpe Ratio:        {sharpe:.3f} ({sharpe_grade})")

        # Max Drawdown
        mdd = perf.get('max_drawdown', 0)
        mdd_grade = self._get_drawdown_grade(mdd)
        lines.append(f"Max Drawdown:        {mdd:.2%} ({mdd_grade})")

        # Total Return
        total_return = perf.get('total_return', 0)
        return_grade = self._get_return_grade(total_return)
        lines.append(f"Total Return:        {total_return:.2%} ({return_grade})")

        # Annual Return
        annual_return = perf.get('annual_return', 0)
        lines.append(f"Annual Return:       {annual_return:.2%}")

        lines.append("")

        # 交易统计
        lines.append("TRADE STATISTICS")
        lines.append("-" * 100)
        lines.append(f"Win Rate:            {perf.get('win_rate', 0):.2%}")
        lines.append(f"Profit Factor:       {perf.get('profit_factor', 0):.2f}")
        lines.append(f"Avg Trade Return:    {perf.get('avg_trade_return', 0):.2%}")
        lines.append(f"Best Trade:          {perf.get('best_trade', 0):.2%}")
        lines.append(f"Worst Trade:         {perf.get('worst_trade', 0):.2%}")
        lines.append(f"Total Trades:        {perf.get('total_trades', 0)}")
        lines.append("")

        # 技术指标摘要
        if 'indicators' in results:
            lines.append("TECHNICAL INDICATORS SUMMARY")
            lines.append("-" * 100)
            indicators = results['indicators']
            lines.append(f"Indicators Calculated: {', '.join(indicators.get('indicators_calculated', []))}")
            lines.append(f"Buy Signals Generated:  {indicators.get('buy_signals', 0)}")
            lines.append(f"Sell Signals Generated: {indicators.get('sell_signals', 0)}")
            lines.append(f"Net Signal Balance:     {indicators.get('net_signals', 0)}")
            lines.append("")

            # 当前指标值
            if 'current_values' in indicators:
                lines.append("Current Indicator Values:")
                for name, value in indicators['current_values'].items():
                    lines.append(f"  {name}: {value:.2f}")
                lines.append("")

        # 风险评估
        lines.append("RISK ASSESSMENT")
        lines.append("-" * 100)
        risk_score = self._calculate_risk_score(perf)
        lines.append(f"Overall Risk Score:   {risk_score:.1f}/100 ({self._get_risk_grade(risk_score)})")
        lines.append(f"Volatility:           {self._estimate_volatility(perf):.2%}")
        lines.append(f"Risk-Adjusted Return: {sharpe:.2f}")
        lines.append("")

        # 建议
        lines.append("RECOMMENDATIONS")
        lines.append("-" * 100)
        recommendations = self._generate_recommendations(perf, indicators if 'indicators' in results else {})
        for i, rec in enumerate(recommendations, 1):
            lines.append(f"{i}. {rec}")
        lines.append("")

        # 免责声明
        lines.append("DISCLAIMER")
        lines.append("-" * 100)
        lines.append("This report is for educational and research purposes only.")
        lines.append("Past performance does not guarantee future results.")
        lines.append("Please consult with a financial advisor before making investment decisions.")
        lines.append("")

        lines.append("=" * 100)
        lines.append(f"Report generated on: {date.today()}")
        lines.append("=" * 100)

        return "\n".join(lines)

    def _get_sharpe_grade(self, sharpe: float) -> str:
        """获取夏普比率评级"""
        if sharpe >= 2.0:
            return "Excellent (A+)"
        elif sharpe >= 1.5:
            return "Very Good (A)"
        elif sharpe >= 1.0:
            return "Good (B+)"
        elif sharpe >= 0.5:
            return "Fair (B)"
        elif sharpe >= 0:
            return "Poor (C)"
        else:
            return "Very Poor (F)"

    def _get_drawdown_grade(self, mdd: float) -> str:
        """获取回撤评级"""
        mdd_abs = abs(mdd)
        if mdd_abs <= 0.05:
            return "Excellent (A+)"
        elif mdd_abs <= 0.10:
            return "Very Good (A)"
        elif mdd_abs <= 0.20:
            return "Good (B+)"
        elif mdd_abs <= 0.30:
            return "Fair (B)"
        elif mdd_abs <= 0.50:
            return "Poor (C)"
        else:
            return "Very Poor (F)"

    def _get_return_grade(self, total_return: float) -> str:
        """获取收益率评级"""
        if total_return >= 1.0:
            return "Excellent (A+)"
        elif total_return >= 0.5:
            return "Very Good (A)"
        elif total_return >= 0.2:
            return "Good (B+)"
        elif total_return >= 0.0:
            return "Fair (B)"
        elif total_return >= -0.2:
            return "Poor (C)"
        else:
            return "Very Poor (F)"

    def _get_risk_grade(self, risk_score: float) -> str:
        """获取风险评级"""
        if risk_score >= 80:
            return "Low Risk"
        elif risk_score >= 60:
            return "Moderate Risk"
        elif risk_score >= 40:
            return "Medium Risk"
        elif risk_score >= 20:
            return "High Risk"
        else:
            return "Very High Risk"

    def _calculate_risk_score(self, perf: dict) -> float:
        """计算风险评分"""
        score = 100.0

        # 根据回撤扣分
        mdd = abs(perf.get('max_drawdown', 0))
        score -= mdd * 200  # 回撤越大分数越低

        # 根据夏普比率加分
        sharpe = perf.get('sharpe_ratio', 0)
        score += max(0, sharpe * 20)

        # 根据胜率加分
        win_rate = perf.get('win_rate', 0)
        score += win_rate * 50

        return max(0, min(100, score))

    def _estimate_volatility(self, perf: dict) -> float:
        """估算波动率"""
        # 使用收益的标准差作为波动率的近似
        total_return = perf.get('total_return', 0)
        num_trades = perf.get('total_trades', 0)

        if num_trades > 0:
            # 简单的波动率估算
            return abs(total_return) / (num_trades ** 0.5)
        else:
            return 0.1  # 默认10%波动率

    def _generate_recommendations(self, perf: dict, indicators: dict) -> list:
        """生成建议"""
        recommendations = []

        sharpe = perf.get('sharpe_ratio', 0)
        mdd = abs(perf.get('max_drawdown', 0))
        win_rate = perf.get('win_rate', 0)
        total_return = perf.get('total_return', 0)

        # 基于Sharpe比率的建议
        if sharpe < 0.5:
            recommendations.append(
                "Sharpe ratio is low. Consider adjusting indicator parameters or using a different strategy."
            )
        elif sharpe > 1.5:
            recommendations.append(
                "Excellent risk-adjusted returns. Consider increasing position sizes."
            )

        # 基于回撤的建议
        if mdd > 0.3:
            recommendations.append(
                "Maximum drawdown is high. Implement stricter risk management rules."
            )

        # 基于胜率的建议
        if win_rate < 0.4:
            recommendations.append(
                "Win rate is low. Consider optimizing entry and exit signals."
            )

        # 基于总收益的建议
        if total_return < 0:
            recommendations.append(
                "Strategy is currently unprofitable. Consider revising the approach."
            )

        # 基于信号的建议
        if 'indicators' in indicators:
            buy_signals = indicators.get('buy_signals', 0)
            sell_signals = indicators.get('sell_signals', 0)

            if buy_signals == 0 and sell_signals == 0:
                recommendations.append(
                    "No clear trading signals generated. Adjust indicator sensitivity."
                )

        # 通用建议
        recommendations.append(
            "Regularly review and rebalance your portfolio based on market conditions."
        )

        return recommendations

    def _generate_charts(self, results: dict) -> list:
        """生成图表"""
        chart_paths = []

        try:
            # 1. 权益曲线图
            equity_path = self._plot_equity_curve(results)
            if equity_path:
                chart_paths.append(equity_path)

            # 2. 回撤图
            drawdown_path = self._plot_drawdown(results)
            if drawdown_path:
                chart_paths.append(drawdown_path)

            # 3. 交易分布图
            trades_path = self._plot_trade_distribution(results)
            if trades_path:
                chart_paths.append(trades_path)

            # 4. 性能指标雷达图
            radar_path = self._plot_performance_radar(results)
            if radar_path:
                chart_paths.append(radar_path)

        except Exception as e:
            self.logger.error(f"Error generating charts: {e}")

        return chart_paths

    def _plot_equity_curve(self, results: dict) -> Path:
        """绘制权益曲线"""
        equity_curve = results.get('equity_curve', [])
        if not equity_curve:
            return None

        df = pd.DataFrame(equity_curve)
        df['equity'] = df['equity'].astype(float)

        plt.figure(figsize=(12, 6))
        plt.plot(df['index'], df['equity'], linewidth=2, color='blue')
        plt.title('Equity Curve', fontsize=16)
        plt.xlabel('Trade Number')
        plt.ylabel('Portfolio Value')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        path = self.output_dir / "equity_curve.png"
        plt.savefig(path, dpi=300)
        plt.close()

        return path

    def _plot_drawdown(self, results: dict) -> Path:
        """绘制回撤图"""
        trades = results.get('trades', [])
        if not trades:
            return None

        df = pd.DataFrame(trades)
        df['cumulative_return'] = (1 + df['return']).cumprod()
        df['running_max'] = df['cumulative_return'].cummax()
        df['drawdown'] = (df['cumulative_return'] - df['running_max']) / df['running_max']

        plt.figure(figsize=(12, 6))
        plt.fill_between(df.index, df['drawdown'], 0, color='red', alpha=0.3)
        plt.plot(df.index, df['drawdown'], color='red', linewidth=1)
        plt.title('Drawdown Chart', fontsize=16)
        plt.xlabel('Trade Number')
        plt.ylabel('Drawdown (%)')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        path = self.output_dir / "drawdown_chart.png"
        plt.savefig(path, dpi=300)
        plt.close()

        return path

    def _plot_trade_distribution(self, results: dict) -> Path:
        """绘制交易收益分布"""
        trades = results.get('trades', [])
        if not trades:
            return None

        df = pd.DataFrame(trades)

        plt.figure(figsize=(10, 6))
        plt.hist(df['return'], bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        plt.axvline(df['return'].mean(), color='red', linestyle='--', linewidth=2, label='Mean')
        plt.title('Trade Return Distribution', fontsize=16)
        plt.xlabel('Return')
        plt.ylabel('Frequency')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        path = self.output_dir / "trade_distribution.png"
        plt.savefig(path, dpi=300)
        plt.close()

        return path

    def _plot_performance_radar(self, results: dict) -> Path:
        """绘制性能雷达图"""
        perf = results.get('performance', {})
        if not perf:
            return None

        # 准备数据
        metrics = {
            'Sharpe Ratio': min(perf.get('sharpe_ratio', 0), 3) / 3 * 100,
            'Win Rate': perf.get('win_rate', 0) * 100,
            'Profit Factor': min(perf.get('profit_factor', 0), 3) / 3 * 100,
            'Annual Return': min(abs(perf.get('annual_return', 0)), 1) * 100,
        }

        categories = list(metrics.keys())
        values = list(metrics.values())

        # 创建雷达图
        angles = [n / float(len(categories)) * 2 * 3.14159 for n in range(len(categories))]
        angles += angles[:1]
        values += values[:1]

        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        ax.plot(angles, values, linewidth=2, linestyle='solid')
        ax.fill(angles, values, alpha=0.25)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories)
        ax.set_ylim(0, 100)
        ax.set_title('Performance Metrics Radar', size=16, y=1.1)
        ax.grid(True)

        path = self.output_dir / "performance_radar.png"
        plt.savefig(path, dpi=300)
        plt.close()

        return path


def main():
    """主函数"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger("retail_report_main")

    # 模拟回测结果 (在实际使用中，这些结果会来自backtest模块)
    sample_results = {
        'symbol': '0700.HK',
        'start_date': '2022-01-01',
        'end_date': '2024-12-31',
        'total_trades': 45,
        'buy_threshold': 30,
        'sell_threshold': 70,
        'performance': {
            'total_return': 0.2456,
            'annual_return': 0.1156,
            'sharpe_ratio': 1.23,
            'max_drawdown': -0.156,
            'win_rate': 0.622,
            'profit_factor': 1.45,
            'total_trades': 45,
            'avg_trade_return': 0.0055,
            'best_trade': 0.0856,
            'worst_trade': -0.0321
        },
        'trades': [
            {'entry_date': '2022-01-15', 'exit_date': '2022-02-20', 'return': 0.0456},
            {'entry_date': '2022-03-10', 'exit_date': '2022-04-15', 'return': 0.0234},
            # ... 更多交易数据
        ],
        'indicators': {
            'indicators_calculated': ['MA', 'RSI', 'MACD', 'BB', 'KDJ'],
            'buy_signals': 23,
            'sell_signals': 22,
            'net_signals': 1,
            'current_values': {
                'RSI': 45.2,
                'MACD': 1.23,
                'ADX': 28.5
            }
        }
    }

    # 生成报告
    logger.info("Generating retail backtest report...")
    generator = RetailBacktestReportGenerator()
    report_path = generator.generate_report(sample_results)

    if report_path:
        print(f"\nReport generated successfully: {report_path}")
    else:
        print("\nFailed to generate report")


if __name__ == "__main__":
    main()
