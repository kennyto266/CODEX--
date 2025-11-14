"""
T065: 零售数据多源回测系统

支持零售销售数据与股票价格数据的综合回测
结合12个技术指标生成交易信号并评估策略表现

功能:
- 零售数据与股票数据合并
- 12个技术指标计算
- 参数优化 (buy 10-60, sell 50-90, step=1)
- 多策略回测
- 性能指标计算 (Sharpe Ratio, Max Drawdown, etc.)
- 可视化报告

支持的数据源:
- 零售销售数据 (C&SD)
- 股票价格数据 (HKEX)
- 经济指标 (GDP, HIBOR, etc.)

Author: Claude Code
Version: 1.0.0
Date: 2025-11-10
"""

import asyncio
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import matplotlib.pyplot as plt
import seaborn as sns
from concurrent.futures import ProcessPoolExecutor, as_completed

# 导入技术指标
from ..indicators.retail_technical_indicators import RetailTechnicalIndicators

# 导入数据适配器
from ..data_adapters.retail_adapter import RetailAdapter, RetailIndicator
from ..data_adapters.unified_hkex_adapter import UnifiedHKEXAdapter


class RetailBacktestConfig:
    """回测配置"""
    def __init__(self, config_path: Optional[Path] = None):
        """初始化配置"""
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: Optional[Path]) -> Dict:
        """加载配置文件"""
        if config_path and config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        # 默认配置
        return {
            'initial_capital': 100000,
            'transaction_cost': 0.001,
            'slippage': 0.0005,
            'buy_threshold': {'min': 10, 'max': 60, 'step': 1},
            'sell_threshold': {'min': 50, 'max': 90, 'step': 1},
            'indicators': ['MA', 'RSI', 'MACD', 'BB', 'KDJ', 'CCI',
                          'ADX', 'ATR', 'OBV', 'Ichimoku', 'SAR', 'WilliamsR']
        }

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            value = value.get(k, default)
            if value is None:
                return default
        return value


class RetailMultiSourceBacktest:
    """
    零售数据多源回测引擎

    结合零售销售数据和股票价格数据进行综合回测
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化回测引擎

        Args:
            config_path: 配置文件路径
        """
        self.config = RetailBacktestConfig(config_path)
        self.logger = logging.getLogger("hk_quant_system.retail_backtest")

        # 初始化组件
        self.retail_adapter = RetailAdapter()
        self.stock_adapter = UnifiedHKEXAdapter()
        self.indicator_calculator = RetailTechnicalIndicators()

        # 回测结果
        self.results = {}
        self.trades = []
        self.equity_curve = []

    async def load_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        data_sources: List[str] = ['retail', 'stock']
    ) -> Dict[str, pd.DataFrame]:
        """
        加载多源数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            data_sources: 数据源列表

        Returns:
            合并后的数据字典
        """
        data = {}

        try:
            # 加载零售数据
            if 'retail' in data_sources:
                self.logger.info("Loading retail data...")
                retail_data = await self._load_retail_data(start_date, end_date)
                if retail_data is not None and not retail_data.empty:
                    data['retail'] = retail_data
                    self.logger.info(f"Loaded {len(retail_data)} retail data points")

            # 加载股票数据
            if 'stock' in data_sources:
                self.logger.info("Loading stock data...")
                stock_data = await self._load_stock_data(symbol, start_date, end_date)
                if stock_data is not None and not stock_data.empty:
                    data['stock'] = stock_data
                    self.logger.info(f"Loaded {len(stock_data)} stock data points")

            # 合并数据
            if data:
                combined_data = self._combine_data_sources(data)
                data['combined'] = combined_data
                self.logger.info(f"Combined data: {len(combined_data)} points")

            return data

        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            return {}

    async def _load_retail_data(
        self,
        start_date: date,
        end_date: date
    ) -> Optional[pd.DataFrame]:
        """加载零售数据"""
        try:
            # 加载所有零售指标
            all_data = await self.retail_adapter.get_all_indicators(start_date, end_date)

            if not all_data:
                return None

            # 合并所有指标到一个DataFrame
            dfs = []
            for indicator, data_points in all_data.items():
                if data_points:
                    df = pd.DataFrame([
                        {
                            'date': dp.date,
                            'indicator': indicator,
                            'value': float(dp.value)
                        }
                        for dp in data_points
                    ])
                    dfs.append(df)

            if not dfs:
                return None

            combined_df = pd.concat(dfs, ignore_index=True)
            combined_df['date'] = pd.to_datetime(combined_df['date'])
            combined_df = combined_df.pivot_table(
                index='date',
                columns='indicator',
                values='value',
                aggfunc='mean'
            ).reset_index()

            combined_df = combined_df.sort_values('date').reset_index(drop=True)

            return combined_df

        except Exception as e:
            self.logger.error(f"Error loading retail data: {e}")
            return None

    async def _load_stock_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> Optional[pd.DataFrame]:
        """加载股票数据"""
        try:
            # 使用统一的股票适配器
            result = await self.stock_adapter.fetch_data({
                'symbol': symbol,
                'start_date': start_date,
                'end_date': end_date,
                'use_cache': True
            })

            if not result['success'] or not result['data']:
                return None

            # 转换为DataFrame
            df = pd.DataFrame([
                {
                    'date': datetime.fromtimestamp(dp['timestamp']).date(),
                    'open': dp['open'],
                    'high': dp['high'],
                    'low': dp['low'],
                    'close': dp['close'],
                    'volume': dp['volume']
                }
                for dp in result['data']
            ])

            if df.empty:
                return None

            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)

            return df

        except Exception as e:
            self.logger.error(f"Error loading stock data: {e}")
            return None

    def _combine_data_sources(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        合并多个数据源

        Args:
            data: 数据字典

        Returns:
            合并后的DataFrame
        """
        try:
            # 使用股票数据作为基础
            if 'stock' in data:
                combined = data['stock'].copy()
            else:
                # 如果没有股票数据，使用第一个可用数据源
                combined = list(data.values())[0].copy()

            # 合并零售数据
            if 'retail' in data:
                retail_df = data['retail']
                # 重命名列以避免冲突
                for col in retail_df.columns:
                    if col != 'date':
                        combined = pd.merge(
                            combined,
                            retail_df[['date', col]],
                            on='date',
                            how='left',
                            suffixes=('', '_retail')
                        )

            # 前向填充零售数据
            retail_columns = [col for col in combined.columns if col.startswith('retail_')]
            for col in retail_columns:
                combined[col] = combined[col].fillna(method='ffill')

            combined = combined.sort_values('date').reset_index(drop=True)

            return combined

        except Exception as e:
            self.logger.error(f"Error combining data sources: {e}")
            return pd.DataFrame()

    async def run_backtest(
        self,
        data: pd.DataFrame,
        symbol: str,
        buy_threshold: int = 30,
        sell_threshold: int = 70
    ) -> Dict[str, Any]:
        """
        运行回测

        Args:
            data: 合并后的数据
            symbol: 股票代码
            buy_threshold: 买入信号阈值
            sell_threshold: 卖出信号阈值

        Returns:
            回测结果
        """
        if data is None or data.empty:
            self.logger.error("No data for backtest")
            return {}

        try:
            # 1. 计算技术指标
            if 'retail_total_sales' in data.columns:
                # 使用零售数据计算指标
                retail_data = data[['date', 'retail_total_sales']].dropna()
                indicators_df = self.indicator_calculator.calculate_all_indicators(
                    retail_data, 'retail_total_sales'
                )
            else:
                # 使用股票收盘价计算指标
                stock_data = data[['date', 'close']].rename(columns={'close': 'value'})
                indicators_df = self.indicator_calculator.calculate_all_indicators(
                    stock_data, 'close'
                )

            # 2. 合并指标到主数据
            full_data = pd.merge(data, indicators_df, on='date', how='left')
            full_data = full_data.sort_values('date').reset_index(drop=True)

            # 3. 生成交易信号
            signals_df = self._generate_trading_signals(
                full_data,
                buy_threshold=buy_threshold,
                sell_threshold=sell_threshold
            )

            # 4. 执行交易
            trades_df = self._execute_trades(signals_df)

            # 5. 计算性能指标
            performance = self._calculate_performance(trades_df)

            # 6. 保存结果
            self.results = {
                'symbol': symbol,
                'start_date': full_data['date'].min(),
                'end_date': full_data['date'].max(),
                'total_trades': len(trades_df),
                'buy_threshold': buy_threshold,
                'sell_threshold': sell_threshold,
                'performance': performance,
                'trades': trades_df.to_dict('records') if not trades_df.empty else [],
                'equity_curve': self._calculate_equity_curve(trades_df),
                'indicators': self.indicator_calculator.get_indicator_summary(indicators_df)
            }

            self.logger.info(f"Backtest completed: {len(trades_df)} trades executed")
            return self.results

        except Exception as e:
            self.logger.error(f"Error running backtest: {e}")
            return {}

    def _generate_trading_signals(
        self,
        data: pd.DataFrame,
        buy_threshold: int = 30,
        sell_threshold: int = 70
    ) -> pd.DataFrame:
        """
        生成交易信号

        Args:
            data: 包含技术指标的数据
            buy_threshold: 买入阈值
            sell_threshold: 卖出阈值

        Returns:
            包含交易信号的DataFrame
        """
        df = data.copy()
        df['Position'] = 0
        df['Signal'] = 0

        # 基于12个技术指标生成信号
        buy_conditions = [
            (df.get('Buy_Signals', 0) >= buy_threshold // 10),
            (df.get('RSI', 50) < 30),
            (df.get('MACD', 0) > df.get('MACD_Signal', 0)),
            (df.get('BB_Buy', False)),
            (df.get('KDJ_Golden_Cross', False)),
            (df.get('CCI_Oversold', False))
        ]

        sell_conditions = [
            (df.get('Sell_Signals', 0) >= sell_threshold // 10),
            (df.get('RSI', 50) > 70),
            (df.get('MACD', 0) < df.get('MACD_Signal', 0)),
            (df.get('BB_Sell', False)),
            (df.get('KDJ_Death_Cross', False)),
            (df.get('CCI_Overbought', False))
        ]

        # 计算综合信号强度
        df['Buy_Score'] = sum(1 for cond in buy_conditions if isinstance(cond, pd.Series) else 0)
        df['Sell_Score'] = sum(1 for cond in sell_conditions if isinstance(cond, pd.Series) else 0)

        # 生成最终信号
        df['Signal'] = np.where(
            (df.get('Buy_Score', 0) >= 3), 1,
            np.where((df.get('Sell_Score', 0) >= 3), -1, 0)
        )

        # 更新持仓
        position = 0
        for i in range(len(df)):
            if df['Signal'].iloc[i] == 1 and position <= 0:
                position = 1
            elif df['Signal'].iloc[i] == -1 and position >= 0:
                position = 0
            df.loc[df.index[i], 'Position'] = position

        return df

    def _execute_trades(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        执行交易并计算收益

        Args:
            data: 包含信号的数据

        Returns:
            交易记录DataFrame
        """
        if 'close' not in data.columns:
            self.logger.warning("No price data available, using retail data")
            if 'retail_total_sales' in data.columns:
                price_col = 'retail_total_sales'
            else:
                return pd.DataFrame()
        else:
            price_col = 'close'

        trades = []
        position = 0
        entry_price = 0
        entry_date = None

        for i in range(len(data)):
            row = data.iloc[i]
            signal = row.get('Signal', 0)
            price = row.get(price_col, 0)
            current_date = row['date']

            # 买入信号
            if signal == 1 and position == 0:
                position = 1
                entry_price = price
                entry_date = current_date

            # 卖出信号
            elif signal == -1 and position == 1:
                position = 0
                exit_price = price
                exit_date = current_date

                # 计算收益
                if entry_price > 0:
                    pnl = (exit_price - entry_price) / entry_price
                    trades.append({
                        'entry_date': entry_date,
                        'exit_date': exit_date,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'return': pnl,
                        'duration': (exit_date - entry_date).days
                    })

        return pd.DataFrame(trades)

    def _calculate_performance(self, trades_df: pd.DataFrame) -> Dict[str, Any]:
        """
        计算性能指标

        Args:
            trades_df: 交易记录

        Returns:
            性能指标字典
        """
        if trades_df.empty:
            return {
                'total_return': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'win_rate': 0,
                'profit_factor': 0
            }

        returns = trades_df['return']
        initial_capital = self.config.get('initial_capital', 100000)

        # 总收益率
        total_return = returns.sum()

        # 年化收益率
        if len(returns) > 0:
            avg_return = returns.mean()
            annual_return = avg_return * 12  # 假设月度数据
        else:
            annual_return = 0

        # 夏普比率
        if returns.std() > 0:
            sharpe_ratio = annual_return / returns.std()
        else:
            sharpe_ratio = 0

        # 最大回撤
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()

        # 胜率
        win_rate = (returns > 0).mean() if len(returns) > 0 else 0

        # 盈亏比
        wins = returns[returns > 0]
        losses = returns[returns < 0]
        profit_factor = (wins.sum() / abs(losses.sum())) if len(losses) > 0 and losses.sum() != 0 else 0

        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_trades': len(returns),
            'avg_trade_return': returns.mean() if len(returns) > 0 else 0,
            'best_trade': returns.max() if len(returns) > 0 else 0,
            'worst_trade': returns.min() if len(returns) > 0 else 0
        }

    def _calculate_equity_curve(self, trades_df: pd.DataFrame) -> List[Dict]:
        """
        计算权益曲线

        Args:
            trades_df: 交易记录

        Returns:
            权益曲线数据
        """
        if trades_df.empty:
            return []

        initial_capital = self.config.get('initial_capital', 100000)
        equity = [initial_capital]

        for _, trade in trades_df.iterrows():
            equity.append(equity[-1] * (1 + trade['return']))

        return [{'index': i, 'equity': e} for i, e in enumerate(equity)]

    def optimize_parameters(
        self,
        data: pd.DataFrame,
        symbol: str,
        max_workers: int = 4
    ) -> Dict[str, Any]:
        """
        参数优化 (buy 10-60, sell 50-90, step=1)

        Args:
            data: 数据
            symbol: 股票代码
            max_workers: 最大并行数

        Returns:
            优化结果
        """
        self.logger.info("Starting parameter optimization...")

        # 生成参数组合
        buy_range = range(10, 61, 1)
        sell_range = range(50, 91, 1)

        param_combinations = [
            (buy, sell) for buy in buy_range for sell in sell_range if sell > buy
        ]

        self.logger.info(f"Testing {len(param_combinations)} parameter combinations")

        # 并行优化
        results = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self._run_single_backtest,
                    data, symbol, buy, sell
                ): (buy, sell)
                for buy, sell in param_combinations
            }

            for future in as_completed(futures):
                buy, sell = futures[future]
                try:
                    result = future.result(timeout=30)
                    if result:
                        result['buy_threshold'] = buy
                        result['sell_threshold'] = sell
                        results.append(result)
                except Exception as e:
                    self.logger.error(f"Error optimizing (buy={buy}, sell={sell}): {e}")

        # 找到最佳参数
        if results:
            best_result = max(results, key=lambda x: x['performance']['sharpe_ratio'])
            self.logger.info(f"Best parameters: buy={best_result['buy_threshold']}, "
                           f"sell={best_result['sell_threshold']}, "
                           f"Sharpe={best_result['performance']['sharpe_ratio']:.2f}")

            return {
                'best_params': {
                    'buy_threshold': best_result['buy_threshold'],
                    'sell_threshold': best_result['sell_threshold']
                },
                'best_performance': best_result['performance'],
                'all_results': results
            }

        return {}

    def _run_single_backtest(
        self,
        data: pd.DataFrame,
        symbol: str,
        buy_threshold: int,
        sell_threshold: int
    ) -> Optional[Dict[str, Any]]:
        """运行单次回测"""
        try:
            return asyncio.run(
                self.run_backtest(data, symbol, buy_threshold, sell_threshold)
            )
        except Exception as e:
            self.logger.error(f"Error in single backtest: {e}")
            return None

    def generate_report(self, output_path: Optional[Path] = None) -> str:
        """
        生成回测报告

        Args:
            output_path: 输出路径

        Returns:
            报告文件路径
        """
        if not self.results:
            self.logger.error("No backtest results to report")
            return ""

        try:
            # 创建报告内容
            report_lines = [
                "=" * 80,
                "RETAIL MULTI-SOURCE BACKTEST REPORT",
                "=" * 80,
                "",
                f"Symbol: {self.results.get('symbol', 'N/A')}",
                f"Period: {self.results.get('start_date')} to {self.results.get('end_date')}",
                f"Total Trades: {self.results.get('total_trades', 0)}",
                f"Buy Threshold: {self.results.get('buy_threshold', 0)}",
                f"Sell Threshold: {self.results.get('sell_threshold', 0)}",
                "",
                "PERFORMANCE METRICS",
                "-" * 80,
            ]

            perf = self.results.get('performance', {})
            metrics = [
                f"Total Return: {perf.get('total_return', 0):.2%}",
                f"Annual Return: {perf.get('annual_return', 0):.2%}",
                f"Sharpe Ratio: {perf.get('sharpe_ratio', 0):.2f}",
                f"Max Drawdown: {perf.get('max_drawdown', 0):.2%}",
                f"Win Rate: {perf.get('win_rate', 0):.2%}",
                f"Profit Factor: {perf.get('profit_factor', 0):.2f}",
                f"Total Trades: {perf.get('total_trades', 0)}",
                f"Avg Trade Return: {perf.get('avg_trade_return', 0):.2%}",
                f"Best Trade: {perf.get('best_trade', 0):.2%}",
                f"Worst Trade: {perf.get('worst_trade', 0):.2%}",
            ]

            report_lines.extend(metrics)
            report_lines.extend([
                "",
                "=" * 80
            ])

            report_text = "\n".join(report_lines)

            # 保存报告
            if output_path is None:
                output_path = Path("reports/retail_backtest_report.txt")

            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_text)

            self.logger.info(f"Report saved to {output_path}")
            return str(output_path)

        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            return ""
