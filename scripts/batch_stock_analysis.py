#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量股票分析脚本 - 演示如何分析多个股票

这个脚本展示了如何使用通用 API 来分析多个股票代码，
对每个股票进行技术分析、风险评估和策略优化。
"""

import requests
import json
import sys
import io
from datetime import datetime
from typing import List, Dict, Optional

# 设置 stdout 编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_BASE_URL = "http://localhost:8001/api"


class BatchAnalyzer:
    """批量分析器"""

    def __init__(self, base_url: str = API_BASE_URL, timeout: int = 60):
        self.base_url = base_url
        self.timeout = timeout
        self.results = []

    def analyze_stocks(self, symbols: List[str], optimize: bool = False,
                      strategy: str = 'all') -> List[Dict]:
        """分析多个股票

        Args:
            symbols: 股票代码列表
            optimize: 是否进行策略优化
            strategy: 策略类型

        Returns:
            结果列表
        """
        print(f"\n{'='*70}")
        print(f"📊 批量分析开始")
        print(f"{'='*70}")
        print(f"目标股票: {', '.join(symbols)}")
        print(f"优化: {'是' if optimize else '否'}")
        print(f"策略: {self._get_strategy_name(strategy)}")
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")

        results = []

        for symbol in symbols:
            print(f"\n⏳ 处理 {symbol}...\n")

            try:
                if optimize:
                    data = self._optimize_stock(symbol, strategy)
                else:
                    data = self._analyze_stock(symbol)

                if data:
                    results.append(data)
                    print(f"✅ {symbol} 完成\n")
                else:
                    print(f"❌ {symbol} 失败\n")

            except Exception as e:
                print(f"❌ {symbol} 错误: {e}\n")

        self.results = results
        return results

    def _analyze_stock(self, symbol: str) -> Optional[Dict]:
        """分析单个股票"""
        try:
            response = requests.get(
                f"{self.base_url}/analysis/{symbol}",
                timeout=self.timeout
            )

            if response.status_code != 200:
                return None

            data = response.json()
            if not data.get('success'):
                return None

            return data['data']

        except Exception as e:
            print(f"API 错误: {e}")
            return None

    def _optimize_stock(self, symbol: str, strategy: str) -> Optional[Dict]:
        """优化单个股票的策略"""
        try:
            response = requests.get(
                f"{self.base_url}/strategy-optimization/{symbol}",
                params={"strategy_type": strategy},
                timeout=self.timeout
            )

            if response.status_code != 200:
                return None

            data = response.json()
            if not data.get('success'):
                return None

            return data['data']

        except Exception as e:
            print(f"API 错误: {e}")
            return None

    def generate_summary_report(self):
        """生成汇总报告"""
        if not self.results:
            print("❌ 没有分析结果")
            return

        print(f"\n{'='*70}")
        print(f"📈 分析汇总报告")
        print(f"{'='*70}\n")

        # 按 Sharpe 比率排序
        sorted_results = sorted(
            self.results,
            key=lambda x: x.get('backtest', {}).get('sharpe_ratio', 0),
            reverse=True
        )

        print("📊 按 Sharpe 比率排名:\n")
        print(f"{'排名':<6} {'股票':<10} {'Sharpe':<10} {'年化收益':<12} {'风险等级':<10}")
        print("-" * 60)

        for i, result in enumerate(sorted_results, 1):
            symbol = result.get('symbol', 'N/A')
            sharpe = result.get('backtest', {}).get('sharpe_ratio', 0)
            annual_return = result.get('backtest', {}).get('volatility', 0)
            risk_level = result.get('risk', {}).get('risk_level', 'UNKNOWN')

            print(f"{i:<6} {symbol:<10} {sharpe:>9.3f} {annual_return:>11.2f}% {risk_level:<10}")

        print(f"\n{'='*70}\n")

    def generate_detailed_report(self, save_to_file: bool = False):
        """生成详细报告"""
        if not self.results:
            print("❌ 没有分析结果")
            return

        report = []
        report.append(f"\n{'='*70}")
        report.append(f"📊 详细分析报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"{'='*70}\n")

        for result in self.results:
            symbol = result.get('symbol', 'N/A')

            report.append(f"\n{'─'*70}")
            report.append(f"📈 {symbol} 详细分析")
            report.append(f"{'─'*70}\n")

            # 基本信息
            report.append(f"💰 价格信息:")
            report.append(f"   当前价格: ¥{result.get('current_price', 'N/A'):.2f}")
            report.append(f"   数据点数: {result.get('data_count', 'N/A')}\n")

            # 技术指标
            indicators = result.get('indicators', {})
            report.append(f"📊 技术指标:")
            for key, value in list(indicators.items())[:6]:
                if value is not None:
                    label = self._get_indicator_label(key)
                    report.append(f"   {label}: {value:.2f}")
            report.append("")

            # 回测结果
            backtest = result.get('backtest', {})
            report.append(f"💹 策略回测:")
            report.append(f"   总收益率: {backtest.get('total_return', 0):.2f}%")
            report.append(f"   Sharpe 比率: {backtest.get('sharpe_ratio', 0):.3f}")
            report.append(f"   最大回撤: {backtest.get('max_drawdown', 0):.2f}%")
            report.append(f"   交易次数: {backtest.get('total_trades', 0)}")
            report.append("")

            # 风险评估
            risk = result.get('risk', {})
            report.append(f"⚠️  风险评估:")
            report.append(f"   风险等级: {risk.get('risk_level', 'UNKNOWN')}")
            report.append(f"   风险评分: {risk.get('risk_score', 0):.1f}/100")
            report.append(f"   波动率: {risk.get('volatility', 0):.2f}%")
            report.append("")

            # 市场情绪
            sentiment = result.get('sentiment', {})
            report.append(f"😊 市场情绪:")
            report.append(f"   情绪等级: {sentiment.get('level', 'Unknown')}")
            report.append(f"   情绪分数: {sentiment.get('score', 0):.1f}/100")
            report.append(f"   趋势强度: {sentiment.get('trend_strength', 0):.2f}%")

        report_text = '\n'.join(report)
        print(report_text)

        if save_to_file:
            filename = f"stock_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"\n✅ 报告已保存到: {filename}")

    @staticmethod
    def _get_indicator_label(key: str) -> str:
        """获取指标标签"""
        labels = {
            'sma_20': 'SMA(20)',
            'sma_50': 'SMA(50)',
            'ema_20': 'EMA(20)',
            'rsi': 'RSI(14)',
            'macd': 'MACD',
            'macd_signal': 'MACD Signal',
            'bollinger_upper': 'Bollinger Upper',
            'bollinger_middle': 'Bollinger Middle',
            'bollinger_lower': 'Bollinger Lower',
        }
        return labels.get(key, key)

    @staticmethod
    def _get_strategy_name(strategy_type: str) -> str:
        """获取策略名称"""
        names = {
            'all': '全部策略',
            'ma': '移动平均交叉',
            'rsi': 'RSI 策略',
            'macd': 'MACD 策略',
            'bb': '布林带策略'
        }
        return names.get(strategy_type, strategy_type)


def main():
    """主函数"""

    # 示例 1: 分析多个股票
    print("\n" + "="*70)
    print("示例 1: 分析多个股票")
    print("="*70)

    analyzer = BatchAnalyzer()

    # 只分析 0700.HK（其他股票需要确保数据源支持）
    stocks = ["0700.HK"]
    results = analyzer.analyze_stocks(stocks)
    analyzer.generate_summary_report()
    analyzer.generate_detailed_report(save_to_file=True)

    # 示例 2: 优化 MACD 策略
    print("\n" + "="*70)
    print("示例 2: 优化 MACD 策略")
    print("="*70)

    analyzer2 = BatchAnalyzer()
    results = analyzer2.analyze_stocks(["0700.HK"], optimize=True, strategy='macd')

    if results and len(results) > 0:
        data = results[0]
        strategies = data.get('best_strategies', [])

        print(f"\n最佳 MACD 策略:")
        print(f"策略名称: {strategies[0].get('strategy_name', 'N/A')}")
        print(f"Sharpe 比率: {strategies[0].get('sharpe_ratio', 0):.3f}")
        print(f"年化收益率: {strategies[0].get('annual_return', 0):.2f}%")
        print(f"最大回撤: {strategies[0].get('max_drawdown', 0):.2f}%")


if __name__ == "__main__":
    main()
