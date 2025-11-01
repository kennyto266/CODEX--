#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用股票分析命令行工具

使用方法：
    python analyze_stock_cli.py 0700.HK              # 分析股票
    python analyze_stock_cli.py 0700.HK --optimize   # 优化策略
    python analyze_stock_cli.py 0700.HK --optimize --strategy macd  # 优化特定策略
    python analyze_stock_cli.py 2800.HK 0939.HK 0001.HK  # 批量分析多个股票
"""

import requests
import json
import sys
import argparse
from datetime import datetime
from typing import List, Dict, Optional
import time
import io

# 设置 stdout 编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# API 基础 URL
API_BASE_URL = "http://localhost:8001/api"

class StockAnalyzer:
    """股票分析工具类"""

    def __init__(self, base_url: str = API_BASE_URL, timeout: int = 60):
        """初始化分析器

        Args:
            base_url: API 基础 URL
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url
        self.timeout = timeout

    def check_server(self) -> bool:
        """检查服务器是否运行"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ 错误: 无法连接到服务器")
            print(f"   请确保系统运行: python complete_project_system.py")
            print(f"   错误: {e}")
            return False

    def analyze_stock(self, symbol: str) -> Optional[Dict]:
        """分析单个股票

        Args:
            symbol: 股票代码（如 0700.HK）

        Returns:
            分析结果字典或 None
        """
        try:
            print(f"📊 正在分析 {symbol}...")
            response = requests.get(
                f"{self.base_url}/analysis/{symbol}",
                timeout=self.timeout
            )

            if response.status_code != 200:
                print(f"❌ 错误: HTTP {response.status_code}")
                return None

            data = response.json()
            if not data.get('success'):
                print(f"❌ 分析失败: {data.get('detail', '未知错误')}")
                return None

            return data['data']

        except requests.Timeout:
            print(f"❌ 请求超时（{self.timeout}秒）")
            return None
        except Exception as e:
            print(f"❌ 错误: {e}")
            return None

    def optimize_strategies(self, symbol: str, strategy_type: str = 'all') -> Optional[Dict]:
        """优化策略参数

        Args:
            symbol: 股票代码
            strategy_type: 策略类型 (all, ma, rsi, macd, bb)

        Returns:
            优化结果字典或 None
        """
        try:
            print(f"🚀 正在优化 {symbol} 的 {strategy_type} 策略...")
            response = requests.get(
                f"{self.base_url}/strategy-optimization/{symbol}",
                params={"strategy_type": strategy_type},
                timeout=self.timeout
            )

            if response.status_code != 200:
                print(f"❌ 错误: HTTP {response.status_code}")
                return None

            data = response.json()
            if not data.get('success'):
                print(f"❌ 优化失败: {data.get('detail', '未知错误')}")
                return None

            return data['data']

        except requests.Timeout:
            print(f"❌ 请求超时（{self.timeout}秒）")
            return None
        except Exception as e:
            print(f"❌ 错误: {e}")
            return None

    def print_analysis_report(self, symbol: str, data: Dict):
        """打印分析报告

        Args:
            symbol: 股票代码
            data: 分析数据
        """
        print("\n" + "="*70)
        print(f"📈 {symbol} 分析报告")
        print("="*70)

        # 基本信息
        print(f"\n📍 基本信息:")
        print(f"   当前价格: ¥{data.get('current_price', 'N/A'):.2f}")
        print(f"   数据点数: {data.get('data_count', 'N/A')}")
        print(f"   分析耗时: {data.get('analysis_time', 'N/A'):.2f}s")

        # 技术指标
        indicators = data.get('indicators', {})
        print(f"\n📊 技术指标:")
        if indicators:
            for key, value in indicators.items():
                if value is not None:
                    label = self._get_indicator_label(key)
                    print(f"   {label}: {value:.2f}")
        else:
            print("   数据不足")

        # 回测结果
        backtest = data.get('backtest', {})
        print(f"\n💰 回测结果 (SMA 交叉策略):")
        print(f"   总收益率: {backtest.get('total_return', 0):.2f}%")
        print(f"   年化收益率: {backtest.get('volatility', 0):.2f}%")
        print(f"   Sharpe 比率: {backtest.get('sharpe_ratio', 0):.3f}")
        print(f"   最大回撤: {backtest.get('max_drawdown', 0):.2f}%")
        print(f"   交易次数: {backtest.get('total_trades', 0)}")
        print(f"   最终价值: ¥{backtest.get('final_value', 100000):.2f}")

        # 风险评估
        risk = data.get('risk', {})
        print(f"\n⚠️  风险评估:")
        risk_level = risk.get('risk_level', 'UNKNOWN')
        risk_emoji = {'LOW': '🟢', 'MEDIUM': '🟡', 'HIGH': '🔴'}.get(risk_level, '⚪')
        print(f"   风险等级: {risk_emoji} {risk_level}")
        print(f"   风险评分: {risk.get('risk_score', 0):.1f}/100")
        print(f"   波动率: {risk.get('volatility', 0):.2f}%")
        print(f"   VaR (95%): {risk.get('var_95', 0):.2f}%")
        print(f"   建议: {risk.get('recommendation', '无')}")

        # 市场情绪
        sentiment = data.get('sentiment', {})
        print(f"\n😊 市场情绪:")
        sentiment_level = sentiment.get('level', 'Unknown')
        sentiment_emoji = {'Bullish': '📈', 'Bearish': '📉', 'Neutral': '➡️'}.get(sentiment_level, '❓')
        print(f"   情绪: {sentiment_emoji} {sentiment_level}")
        print(f"   分数: {sentiment.get('score', 0):.1f}/100")
        print(f"   趋势强度: {sentiment.get('trend_strength', 0):.2f}%")
        print(f"   上涨天数: {sentiment.get('positive_days', 0)}")
        print(f"   下跌天数: {sentiment.get('negative_days', 0)}")

        print("\n" + "="*70)

    def print_optimization_report(self, symbol: str, strategy_type: str, data: Dict):
        """打印优化报告

        Args:
            symbol: 股票代码
            strategy_type: 策略类型
            data: 优化数据
        """
        print("\n" + "="*70)
        print(f"🚀 {symbol} - {self._get_strategy_name(strategy_type)} 优化报告")
        print("="*70)

        total = data.get('total_strategies', 0)
        best_sharpe = data.get('best_sharpe_ratio', 0)

        print(f"\n📊 优化统计:")
        print(f"   测试策略数: {total}")
        print(f"   最佳 Sharpe 比率: {best_sharpe:.3f}")
        print(f"   优化时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        print(f"\n🏆 前 10 最佳策略:")
        print(f"{'排名':<6} {'策略名称':<25} {'Sharpe':<10} {'年化收益':<12} {'最大回撤':<10}")
        print("-" * 70)

        strategies = data.get('best_strategies', [])
        for i, strategy in enumerate(strategies[:10], 1):
            name = strategy.get('strategy_name', 'Unknown')[:22]
            sharpe = strategy.get('sharpe_ratio', 0)
            annual = strategy.get('annual_return', 0)
            drawdown = strategy.get('max_drawdown', 0)

            print(f"{i:<6} {name:<25} {sharpe:>9.3f} {annual:>11.2f}% {drawdown:>9.2f}%")

        print("\n" + "="*70)

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
            'macd_histogram': 'MACD Histogram',
            'bollinger_upper': 'Bollinger Upper',
            'bollinger_middle': 'Bollinger Middle',
            'bollinger_lower': 'Bollinger Lower',
            'atr': 'ATR(14)',
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
    parser = argparse.ArgumentParser(
        description='通用股票分析命令行工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python analyze_stock_cli.py 0700.HK              # 分析股票
  python analyze_stock_cli.py 0700.HK --optimize   # 优化策略
  python analyze_stock_cli.py 0700.HK --optimize --strategy macd  # 优化特定策略
  python analyze_stock_cli.py 2800.HK 0939.HK 0001.HK  # 批量分析
        '''
    )

    parser.add_argument(
        'symbols',
        nargs='+',
        help='股票代码（如 0700.HK, 2800.HK）'
    )
    parser.add_argument(
        '--optimize',
        action='store_true',
        help='运行策略优化'
    )
    parser.add_argument(
        '--strategy',
        choices=['all', 'ma', 'rsi', 'macd', 'bb'],
        default='all',
        help='策略类型（默认: all）'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=60,
        help='请求超时时间（秒，默认: 60）'
    )

    args = parser.parse_args()

    # 创建分析器
    analyzer = StockAnalyzer(timeout=args.timeout)

    # 检查服务器
    if not analyzer.check_server():
        sys.exit(1)

    print("✅ 服务器已连接\n")

    # 处理每个股票
    for symbol in args.symbols:
        if args.optimize:
            # 运行优化
            data = analyzer.optimize_strategies(symbol, args.strategy)
            if data:
                analyzer.print_optimization_report(symbol, args.strategy, data)
        else:
            # 运行分析
            data = analyzer.analyze_stock(symbol)
            if data:
                analyzer.print_analysis_report(symbol, data)

        # 在多个股票之间添加延迟
        if symbol != args.symbols[-1]:
            print("\n⏳ 等待 2 秒再处理下一个股票...\n")
            time.sleep(2)


if __name__ == "__main__":
    main()
