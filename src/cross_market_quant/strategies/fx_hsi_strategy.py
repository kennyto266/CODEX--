"""
USD/CNH → HSI 跨市场策略实现

基于阿程策略12的逻辑：
使用USD/CNH汇率的累积回报来预测HSI的走势

策略逻辑：
- USD/CNH 4天累积回报 >= 0.5% → HSI卖出信号
- USD/CNH 4天累积回报 <= -0.5% → HSI买入信号

示例：
Given: USD/CNH 4天累积回报 = 0.005 (0.5%)
When: Running FXHsiStrategy.generate_signals()
Then: Return SELL signal for HSI
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
import logging

from adapters.fx_adapter import FXAdapter
from adapters.hkex_adapter import HKEXAdapter
from utils.cumulative_filter import CumulativeReturnFilter


class FXHsiStrategy:
    """
    USD/CNH到HSI的跨市场策略

    核心逻辑：
    1. 获取USD/CNH数据
    2. 计算4天累积回报
    3. 与阈值比较生成HSI交易信号
    """

    def __init__(
        self,
        fx_symbol: str = 'USD_CNH',
        hsi_symbol: str = '0700.HK',  # 默认腾讯作为HSI代表
        window: int = 4,
        threshold: float = 0.005,  # ±0.5%阈值
        holding_period: int = 14,  # 14天固定持仓期
        enable_dynamic_threshold: bool = True
    ):
        """
        初始化USD/CNH → HSI策略

        Args:
            fx_symbol: 外汇符号（默认USD_CNH）
            hsi_symbol: HSI股票符号（默认0700.HK）
            window: 累积回报计算窗口（默认4天）
            threshold: 信号触发阈值（默认±0.5%）
            holding_period: 持仓期（默认14天）
            enable_dynamic_threshold: 启用动态阈值
        """
        self.fx_symbol = fx_symbol
        self.hsi_symbol = hsi_symbol
        self.window = window
        self.threshold = threshold
        self.holding_period = holding_period
        self.enable_dynamic_threshold = enable_dynamic_threshold

        # 初始化组件
        self.fx_adapter = FXAdapter()
        self.hkex_adapter = HKEXAdapter()
        self.cumulative_filter = CumulativeReturnFilter(
            window=window,
            threshold=threshold,
            enable_dynamic_threshold=enable_dynamic_threshold
        )

        self.logger = logging.getLogger("cross_market_quant.FXHsiStrategy")

    async def generate_signals(
        self,
        start_date: str,
        end_date: str,
        **kwargs
    ) -> pd.DataFrame:
        """
        生成交易信号

        Args:
            start_date: 开始日期
            end_date: 结束日期
            **kwargs: 额外参数

        Returns:
            包含信号的数据框
        """
        try:
            self.logger.info(
                f"生成{self.fx_symbol} -> {self.hsi_symbol}信号 "
                f"({start_date} 到 {end_date})"
            )

            # 获取FX数据
            fx_data = await self.fx_adapter.fetch_data(
                self.fx_symbol, start_date, end_date
            )

            if fx_data.empty:
                raise Exception(f"未能获取到{self.fx_symbol}数据")

            # 计算累积回报
            cumulative_returns = self.cumulative_filter.calculate_cumulative_returns(
                fx_data['Close']
            )

            # 生成信号（自动模式适用于跨市场预测）
            signals = self.cumulative_filter.filter_signals(
                cumulative_returns=cumulative_returns,
                price_data=fx_data['Close'],
                signal_type='auto'
            )

            # 构建结果
            result = pd.DataFrame({
                'Date': fx_data['Date'],
                'FX_Price': fx_data['Close'],
                'Cumulative_Return': cumulative_returns,
                'Signal': signals,
                'Action': signals.map(self._signal_to_action),
                'Position': 0  # 初始持仓为0
            })

            # 计算持仓（基于14天固定持仓期）
            result['Position'] = self._calculate_positions(result['Signal'])

            # 分析信号
            analysis = self.cumulative_filter.analyze_signals(
                signals, cumulative_returns
            )

            self.logger.info(f"信号生成完成: {analysis}")

            return result

        except Exception as e:
            self.logger.error(f"生成信号失败: {e}")
            return pd.DataFrame()

    async def backtest(
        self,
        start_date: str,
        end_date: str,
        initial_capital: float = 100000.0,
        **kwargs
    ) -> Dict:
        """
        回测策略表现

        Args:
            start_date: 回测开始日期
            end_date: 回测结束日期
            initial_capital: 初始资金

        Returns:
            回测结果
        """
        try:
            self.logger.info(f"开始回测: {start_date} 到 {end_date}")

            # 获取信号
            signals_data = await self.generate_signals(start_date, end_date)

            if signals_data.empty:
                raise Exception("没有生成信号")

            # 获取HSI价格数据（用于计算收益）
            hsi_data = await self.hkex_adapter.fetch_data(
                self.hsi_symbol, start_date, end_date
            )

            if hsi_data.empty:
                raise Exception(f"未能获取到{self.hsi_symbol}数据")

            # 合并数据
            merged_data = pd.merge(
                signals_data,
                hsi_data[['Date', 'Close']],
                on='Date',
                how='left',
                suffixes=('_FX', '_HSI')
            )

            # 计算策略收益
            returns_data = self._calculate_strategy_returns(
                merged_data, initial_capital
            )

            # 计算性能指标
            performance = self._calculate_performance_metrics(returns_data)

            # 记录交易
            trades = self._extract_trades(merged_data)

            result = {
                'strategy_name': 'USD/CNH → HSI (阿程策略12)',
                'parameters': {
                    'fx_symbol': self.fx_symbol,
                    'hsi_symbol': self.hsi_symbol,
                    'window': self.window,
                    'threshold': self.threshold,
                    'holding_period': self.holding_period
                },
                'performance': performance,
                'trades': trades,
                'data': returns_data
            }

            self.logger.info(f"回测完成: 总收益 {performance['total_return']:.2%}")
            return result

        except Exception as e:
            self.logger.error(f"回测失败: {e}")
            return {'error': str(e)}

    def _signal_to_action(self, signal: float) -> str:
        """
        将信号转换为操作描述

        Args:
            signal: 信号值

        Returns:
            操作描述
        """
        if signal == 1:
            return 'BUY'
        elif signal == -1:
            return 'SELL'
        elif signal == 0:
            return 'HOLD'
        else:
            return 'NONE'

    def _calculate_positions(self, signals: pd.Series) -> pd.Series:
        """
        计算持仓（基于14天固定持仓期）

        Args:
            signals: 信号序列

        Returns:
            持仓序列
        """
        positions = pd.Series(index=signals.index, dtype=float)
        current_position = 0
        days_in_position = 0

        for i, signal in enumerate(signals):
            if pd.isna(signal):
                positions.iloc[i] = current_position
                continue

            # 检查是否需要开仓
            if signal != 0 and current_position == 0:
                current_position = signal
                days_in_position = 1
            # 检查是否需要平仓
            elif days_in_position >= self.holding_period or signal == 0:
                current_position = 0
                days_in_position = 0
            else:
                days_in_position += 1

            positions.iloc[i] = current_position

        return positions

    def _calculate_strategy_returns(
        self,
        data: pd.DataFrame,
        initial_capital: float
    ) -> pd.DataFrame:
        """
        计算策略收益

        Args:
            data: 合并后的数据
            initial_capital: 初始资金

        Returns:
            包含收益的数据
        """
        try:
            data = data.copy()

            # 计算HSI日收益率
            data['HSI_Returns'] = data['Close_HSI'].pct_change()

            # 计算策略收益（简化版：假设按收盘价执行）
            data['Strategy_Returns'] = data['Position'].shift(1) * data['HSI_Returns']

            # 计算累计收益
            data['Cumulative_Returns'] = (1 + data['Strategy_Returns']).cumprod() - 1

            # 计算资产价值
            data['Portfolio_Value'] = initial_capital * (1 + data['Cumulative_Returns'])

            # 计算基准收益（买入持有）
            data['Benchmark_Returns'] = data['HSI_Returns']
            data['Benchmark_Cumulative'] = (1 + data['Benchmark_Returns']).cumprod() - 1
            data['Benchmark_Value'] = initial_capital * (1 + data['Benchmark_Cumulative'])

            return data

        except Exception as e:
            self.logger.error(f"计算策略收益失败: {e}")
            return pd.DataFrame()

    def _calculate_performance_metrics(self, data: pd.DataFrame) -> Dict:
        """
        计算性能指标

        Args:
            data: 包含收益的数据

        Returns:
            性能指标
        """
        try:
            strategy_returns = data['Strategy_Returns'].dropna()
            benchmark_returns = data['Benchmark_Returns'].dropna()

            if len(strategy_returns) == 0:
                return {'error': '没有有效收益数据'}

            # 基础指标
            total_return = data['Cumulative_Returns'].iloc[-1] if len(data) > 0 else 0
            benchmark_total_return = data['Benchmark_Cumulative'].iloc[-1] if len(data) > 0 else 0

            # 年化收益率
            trading_days = len(strategy_returns)
            years = trading_days / 252
            annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

            # 波动率
            volatility = strategy_returns.std() * np.sqrt(252)

            # 夏普比率（假设无风险利率为2%）
            risk_free_rate = 0.02
            sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility > 0 else 0

            # 最大回撤
            cumulative_returns = 1 + data['Cumulative_Returns']
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = drawdown.min()

            # 胜率
            win_rate = len(strategy_returns[strategy_returns > 0]) / len(strategy_returns)

            # 交易次数
            trade_count = len(data[data['Signal'].diff() != 0])

            metrics = {
                'total_return': total_return,
                'benchmark_return': benchmark_total_return,
                'excess_return': total_return - benchmark_total_return,
                'annualized_return': annualized_return,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'trade_count': trade_count,
                'trading_days': trading_days
            }

            return metrics

        except Exception as e:
            self.logger.error(f"计算性能指标失败: {e}")
            return {'error': str(e)}

    def _extract_trades(self, data: pd.DataFrame) -> List[Dict]:
        """
        提取交易记录

        Args:
            data: 数据

        Returns:
            交易记录列表
        """
        try:
            trades = []
            position_changes = data[data['Signal'].diff() != 0]

            for i, (idx, row) in enumerate(position_changes.iterrows()):
                trades.append({
                    'trade_id': i + 1,
                    'date': row['Date'].strftime('%Y-%m-%d'),
                    'action': self._signal_to_action(row['Signal']),
                    'price': row['Close_HSI'],
                    'fx_price': row['Close_FX'],
                    'fx_cumulative_return': row['Cumulative_Return']
                })

            return trades

        except Exception as e:
            self.logger.error(f"提取交易记录失败: {e}")
            return []

    async def get_cross_market_correlation(
        self,
        start_date: str,
        end_date: str,
        window: int = 20
    ) -> pd.DataFrame:
        """
        获取跨市场相关性分析

        Args:
            start_date: 开始日期
            end_date: 结束日期
            window: 滚动窗口

        Returns:
            相关性数据
        """
        try:
            correlation_data = await self.fx_adapter.calculate_cross_market_correlation(
                fx_symbol=self.fx_symbol,
                stock_symbol=self.hsi_symbol,
                start_date=start_date,
                end_date=end_date,
                window=window
            )

            self.logger.info(f"获取到{len(correlation_data)}个相关性数据点")
            return correlation_data

        except Exception as e:
            self.logger.error(f"获取相关性失败: {e}")
            return pd.DataFrame()
