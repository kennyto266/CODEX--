#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
访客数据多源回测系统
集成访客数据、技术指标和交易策略的完整回测框架
支持参数优化和性能报告生成

Author: Claude Code
Version: 1.0.0
Date: 2025-11-10
"""

import asyncio
import json
import logging
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd


@dataclass
class BacktestConfig:
    """回测配置"""
    initial_capital: float = 100000.0
    transaction_cost: float = 0.001
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    benchmark: str = 'visitor_total'
    rebalance_frequency: str = 'monthly'
    max_positions: int = 1
    min_data_points: int = 50
    min_trades: int = 5


@dataclass
class BacktestResult:
    """回测结果"""
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    final_value: float
    start_date: str
    end_date: str
    parameters: Dict[str, Any]
    equity_curve: List[Dict[str, Any]]
    trades: List[Dict[str, Any]]
    metrics: Dict[str, Any]


class VisitorDataBacktester:
    """访客数据回测器"""

    def __init__(self, config: Optional[BacktestConfig] = None):
        """
        初始化回测器

        Args:
            config: 回测配置
        """
        self.config = config or BacktestConfig()
        self.logger = logging.getLogger(__name__)

    def run_backtest(
        self,
        data: pd.DataFrame,
        indicator: str = 'visitor_total',
        buy_threshold: float = 30,
        sell_threshold: float = 70
    ) -> BacktestResult:
        """
        运行回测

        Args:
            data: 访客数据
            indicator: 指标名称
            buy_threshold: 买入阈值
            sell_threshold: 卖出阈值

        Returns:
            BacktestResult: 回测结果
        """
        # 1. 预处理数据
        processed_data = self._preprocess_data(data, indicator)

        if len(processed_data) < self.config.min_data_points:
            raise ValueError(f"Insufficient data: {len(processed_data)} < {self.config.min_data_points}")

        # 2. 计算技术指标
        from ..indicators.visitor_technical_indicators import VisitorTechnicalIndicators
        calculator = VisitorTechnicalIndicators()
        indicators_df = calculator.calculate_all_indicators(processed_data, indicator)

        # 3. 生成交易信号
        signals_df = calculator.generate_signals(indicators_df, buy_threshold, sell_threshold)

        # 4. 执行回测
        equity_curve, trades = self._execute_backtest(signals_df)

        # 5. 计算性能指标
        result = self._calculate_performance(equity_curve, trades, {
            'indicator': indicator,
            'buy_threshold': buy_threshold,
            'sell_threshold': sell_threshold
        })

        return result

    def _preprocess_data(self, data: pd.DataFrame, indicator: str) -> pd.DataFrame:
        """预处理数据"""
        # 过滤指定指标
        filtered = data[data['symbol'] == indicator].copy()

        # 过滤日期范围
        if self.config.start_date:
            filtered = filtered[filtered['date'] >= self.config.start_date]
        if self.config.end_date:
            filtered = filtered[filtered['date'] <= self.config.end_date]

        # 排序
        filtered = filtered.sort_values('date').reset_index(drop=True)

        return filtered

    def _execute_backtest(
        self,
        signals_df: pd.DataFrame
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """执行回测逻辑"""
        equity_curve = []
        trades = []
        capital = self.config.initial_capital
        position = 0
        entry_price = 0
        entry_date = None

        for idx, row in signals_df.iterrows():
            current_date = row['date']
            current_price = row['close']
            signal = row.get('signal', 'HOLD')
            current_value = capital + (position * current_price if position > 0 else 0)

            equity_curve.append({
                'date': current_date,
                'value': current_value,
                'price': current_price,
                'position': position
            })

            # 交易逻辑
            if signal == 'BUY' and position == 0:
                # 买入
                shares = int(capital * (1 - self.config.transaction_cost) / current_price)
                if shares > 0:
                    position = shares
                    entry_price = current_price
                    entry_date = current_date
                    capital = capital - (shares * current_price * (1 + self.config.transaction_cost))

            elif signal == 'SELL' and position > 0:
                # 卖出
                capital = capital + (position * current_price * (1 - self.config.transaction_cost))
                trade_return = (current_price - entry_price) / entry_price
                trade = {
                    'entry_date': entry_date,
                    'exit_date': current_date,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'shares': position,
                    'return': trade_return,
                    'pct_return': trade_return * 100
                }
                trades.append(trade)
                position = 0
                entry_price = 0
                entry_date = None

        # 处理未平仓位置
        if position > 0:
            final_price = signals_df.iloc[-1]['close']
            capital = capital + (position * final_price * (1 - self.config.transaction_cost))

        return equity_curve, trades

    def _calculate_performance(
        self,
        equity_curve: List[Dict[str, Any]],
        trades: List[Dict[str, Any]],
        parameters: Dict[str, Any]
    ) -> BacktestResult:
        """计算性能指标"""
        if not equity_curve:
            raise ValueError("No equity curve data")

        # 提取数据
        dates = [item['date'] for item in equity_curve]
        values = [item['value'] for item in equity_curve]

        # 基本统计
        start_value = self.config.initial_capital
        end_value = values[-1]
        total_return = (end_value - start_value) / start_value

        # 年化收益率
        start_date = dates[0]
        end_date = dates[-1]
        years = (end_date - start_date).days / 365.25
        annualized_return = (end_value / start_value) ** (1 / years) - 1 if years > 0 else 0

        # 波动率
        returns = np.diff(values) / values[:-1]
        volatility = np.std(returns) * np.sqrt(12)  # 月度数据年化

        # Sharpe比率
        risk_free_rate = 0.02  # 假设无风险利率2%
        sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility > 0 else 0

        # 最大回撤
        peak = start_value
        max_drawdown = 0
        for value in values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, drawdown)

        # 胜率
        winning_trades = sum(1 for trade in trades if trade['return'] > 0)
        win_rate = winning_trades / len(trades) if trades else 0

        return BacktestResult(
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            total_trades=len(trades),
            final_value=end_value,
            start_date=str(start_date),
            end_date=str(end_date),
            parameters=parameters,
            equity_curve=equity_curve,
            trades=trades,
            metrics={
                'start_value': start_value,
                'end_value': end_value,
                'years': years,
                'winning_trades': winning_trades,
                'losing_trades': len(trades) - winning_trades,
                'avg_return': np.mean([t['return'] for t in trades]) if trades else 0,
                'best_trade': max([t['return'] for t in trades]) if trades else 0,
                'worst_trade': min([t['return'] for t in trades]) if trades else 0
            }
        )


class ParameterOptimizer:
    """参数优化器"""

    def __init__(
        self,
        data: pd.DataFrame,
        indicator: str = 'visitor_total',
        max_workers: int = 8
    ):
        """
        初始化优化器

        Args:
            data: 访客数据
            indicator: 指标名称
            max_workers: 最大工作线程数
        """
        self.data = data
        self.indicator = indicator
        self.max_workers = max_workers
        self.logger = logging.getLogger(__name__)

    def optimize_parameters(
        self,
        buy_range: Tuple[int, int, int] = (10, 60, 1),
        sell_range: Tuple[int, int, int] = (50, 90, 1),
        metric: str = 'sharpe_ratio'
    ) -> List[BacktestResult]:
        """
        参数优化

        Args:
            buy_range: 买入阈值范围 (min, max, step)
            sell_range: 卖出阈值范围 (min, max, step)
            metric: 优化指标

        Returns:
            List[BacktestResult]: 优化结果列表
        """
        buy_min, buy_max, buy_step = buy_range
        sell_min, sell_max, sell_step = sell_range

        # 生成参数组合
        param_combinations = []
        for buy_thresh in range(buy_min, buy_max + 1, buy_step):
            for sell_thresh in range(sell_min, sell_max + 1, sell_step):
                if sell_thresh > buy_thresh:  # 确保逻辑合理
                    param_combinations.append((buy_thresh, sell_thresh))

        self.logger.info(f"Testing {len(param_combinations)} parameter combinations")

        # 并行优化
        results = []
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交任务
            future_to_params = {
                executor.submit(
                    self._run_single_backtest,
                    buy_threshold,
                    sell_threshold
                ): (buy_threshold, sell_threshold)
                for buy_threshold, sell_threshold in param_combinations
            }

            # 收集结果
            for future in as_completed(future_to_params):
                params = future_to_params[future]
                try:
                    result = future.result()
                    if result and len(result.trades) >= 5:  # 过滤交易次数过少的结果
                        results.append(result)
                except Exception as e:
                    self.logger.warning(f"Failed to optimize parameters {params}: {e}")

        # 按指标排序
        results.sort(key=lambda x: getattr(x, metric), reverse=True)

        self.logger.info(f"Optimization complete. {len(results)} valid results.")
        return results

    def _run_single_backtest(
        self,
        buy_threshold: float,
        sell_threshold: float
    ) -> Optional[BacktestResult]:
        """运行单个参数组合的回测"""
        try:
            backtester = VisitorDataBacktester()
            result = backtester.run_backtest(
                self.data,
                self.indicator,
                buy_threshold,
                sell_threshold
            )
            return result
        except Exception as e:
            self.logger.debug(f"Backtest failed for ({buy_threshold}, {sell_threshold}): {e}")
            return None

    def get_best_parameters(
        self,
        results: List[BacktestResult],
        top_n: int = 10
    ) -> List[BacktestResult]:
        """
        获取最佳参数

        Args:
            results: 优化结果
            top_n: 返回前N个结果

        Returns:
            List[BacktestResult]: 最佳结果列表
        """
        return results[:top_n]


class BacktestReportGenerator:
    """回测报告生成器"""

    def __init__(self):
        """初始化报告生成器"""
        self.logger = logging.getLogger(__name__)

    def generate_report(
        self,
        result: BacktestResult,
        output_dir: str = 'reports/visitor_backtest'
    ) -> str:
        """
        生成回测报告

        Args:
            result: 回测结果
            output_dir: 输出目录

        Returns:
            str: 报告文件路径
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = output_path / f'backtest_report_{timestamp}.txt'

        # 生成报告内容
        report_content = self._generate_report_content(result)

        # 保存报告
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        # 保存JSON数据
        json_file = output_path / f'backtest_data_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(result), f, indent=2, default=str)

        self.logger.info(f"Report generated: {report_file}")
        return str(report_file)

    def _generate_report_content(self, result: BacktestResult) -> str:
        """生成报告内容"""
        lines = []

        lines.append("=" * 80)
        lines.append("访客数据回测报告")
        lines.append("=" * 80)
        lines.append("")

        # 基本信息
        lines.append("回测期间:")
        lines.append(f"  开始日期: {result.start_date}")
        lines.append(f"  结束日期: {result.end_date}")
        lines.append(f"  策略参数: {json.dumps(result.parameters, ensure_ascii=False, indent=2)}")
        lines.append("")

        # 核心指标
        lines.append("核心绩效指标:")
        lines.append(f"  总收益率: {result.total_return:.2%}")
        lines.append(f"  年化收益率: {result.annualized_return:.2%}")
        lines.append(f"  波动率: {result.volatility:.2%}")
        lines.append(f"  夏普比率: {result.sharpe_ratio:.4f}")
        lines.append(f"  最大回撤: {result.max_drawdown:.2%}")
        lines.append(f"  胜率: {result.win_rate:.2%}")
        lines.append("")

        # 交易统计
        lines.append("交易统计:")
        lines.append(f"  总交易次数: {result.total_trades}")
        lines.append(f"  盈利交易: {result.metrics.get('winning_trades', 0)}")
        lines.append(f"  亏损交易: {result.metrics.get('losing_trades', 0)}")
        lines.append(f"  平均收益率: {result.metrics.get('avg_return', 0):.2%}")
        lines.append(f"  最佳交易: {result.metrics.get('best_trade', 0):.2%}")
        lines.append(f"  最差交易: {result.metrics.get('worst_trade', 0):.2%}")
        lines.append("")

        # 资金变化
        lines.append("资金变化:")
        lines.append(f"  初始资金: ${result.metrics.get('start_value', 0):,.2f}")
        lines.append(f"  最终价值: ${result.final_value:,.2f}")
        lines.append(f"  绝对收益: ${result.final_value - result.metrics.get('start_value', 0):,.2f}")
        lines.append("")

        return "\n".join(lines)

    def generate_comparison_report(
        self,
        results: List[BacktestResult],
        output_dir: str = 'reports/visitor_backtest'
    ) -> str:
        """
        生成参数优化对比报告

        Args:
            results: 优化结果列表
            output_dir: 输出目录

        Returns:
            str: 报告文件路径
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = output_path / f'optimization_report_{timestamp}.txt'

        # 生成报告内容
        lines = []
        lines.append("=" * 80)
        lines.append("访客数据参数优化报告")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"测试参数组合数: {len(results)}")
        lines.append("")

        # Top 10 结果
        lines.append("Top 10 最佳参数组合:")
        lines.append("-" * 80)
        lines.append(f"{'排名':<4} {'买入阈值':<8} {'卖出阈值':<8} {'年化收益':<10} {'夏普比率':<10} {'最大回撤':<10} {'胜率':<8}")
        lines.append("-" * 80)

        for i, result in enumerate(results[:10], 1):
            params = result.parameters
            lines.append(
                f"{i:<4} "
                f"{params.get('buy_threshold', 0):<8.0f} "
                f"{params.get('sell_threshold', 0):<8.0f} "
                f"{result.annualized_return:<10.2%} "
                f"{result.sharpe_ratio:<10.4f} "
                f"{result.max_drawdown:<10.2%} "
                f"{result.win_rate:<8.2%}"
            )

        lines.append("")

        # 最佳参数
        best = results[0]
        lines.append("最佳参数配置:")
        lines.append(f"  买入阈值: {best.parameters.get('buy_threshold', 0)}")
        lines.append(f"  卖出阈值: {best.parameters.get('sell_threshold', 0)}")
        lines.append(f"  夏普比率: {best.sharpe_ratio:.4f}")
        lines.append(f"  年化收益: {best.annualized_return:.2%}")
        lines.append(f"  最大回撤: {best.max_drawdown:.2%}")
        lines.append("")

        # 保存报告
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

        self.logger.info(f"Comparison report generated: {report_file}")
        return str(report_file)


# 便捷函数
async def run_visitor_backtest(
    data: pd.DataFrame,
    indicator: str = 'visitor_total',
    buy_threshold: float = 30,
    sell_threshold: float = 70
) -> BacktestResult:
    """
    运行访客数据回测的便捷函数

    Args:
        data: 访客数据
        indicator: 指标名称
        buy_threshold: 买入阈值
        sell_threshold: 卖出阈值

    Returns:
        BacktestResult: 回测结果
    """
    backtester = VisitorDataBacktester()
    return backtester.run_backtest(data, indicator, buy_threshold, sell_threshold)


async def optimize_visitor_parameters(
    data: pd.DataFrame,
    indicator: str = 'visitor_total',
    max_workers: int = 8
) -> List[BacktestResult]:
    """
    优化访客数据策略参数的便捷函数

    Args:
        data: 访客数据
        indicator: 指标名称
        max_workers: 最大工作线程数

    Returns:
        List[BacktestResult]: 优化结果
    """
    optimizer = ParameterOptimizer(data, indicator, max_workers)
    return optimizer.optimize_parameters()


if __name__ == '__main__':
    # 测试代码
    import asyncio
    from datetime import date, timedelta

    async def test():
        # 创建测试数据
        dates = [date(2020, 1, 1) + timedelta(days=i*30) for i in range(60)]
        values = [500000 + i*1000 + np.sin(i/5)*50000 for i in range(60)]

        data = {
            'symbol': ['visitor_total'] * 60,
            'date': dates,
            'value': values,
            'source': ['test'] * 60
        }
        df = pd.DataFrame(data)

        # 运行回测
        backtester = VisitorDataBacktester()
        result = backtester.run_backtest(df, 'visitor_total', 30, 70)

        print("Backtest Result:")
        print(f"Total Return: {result.total_return:.2%}")
        print(f"Annualized Return: {result.annualized_return:.2%}")
        print(f"Sharpe Ratio: {result.sharpe_ratio:.4f}")
        print(f"Max Drawdown: {result.max_drawdown:.2%}")
        print(f"Total Trades: {result.total_trades}")

        # 生成报告
        generator = BacktestReportGenerator()
        report_file = generator.generate_report(result)
        print(f"\nReport generated: {report_file}")

    asyncio.run(test())
