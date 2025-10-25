"""
真實數據回測框架

使用真實HKEX歷史數據進行策略回測，包括性能計算、風險評估等功能
"""

import logging
import asyncio
from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
import pandas as pd
import numpy as np
from decimal import Decimal

from ..data_adapters.hkex_adapter import HKEXAdapter


class BacktestResults:
    """回測結果容器"""

    def __init__(self, symbol: str, strategy_name: str):
        self.symbol = symbol
        self.strategy_name = strategy_name
        self.trades: List[Dict[str, Any]] = []
        self.portfolio_values: List[float] = []
        self.dates: List[datetime] = []
        self.returns: List[float] = []
        self.start_date: Optional[date] = None
        self.end_date: Optional[date] = None
        self.initial_capital: float = 0
        self.final_capital: float = 0

    def add_trade(self, date: datetime, signal: str, price: float, quantity: int, pnl: float = 0):
        """添加交易記錄"""
        self.trades.append({
            'date': date,
            'signal': signal,
            'price': price,
            'quantity': quantity,
            'pnl': pnl
        })

    def add_portfolio_snapshot(self, date: datetime, value: float, return_val: float):
        """添加投資組合快照"""
        self.dates.append(date)
        self.portfolio_values.append(value)
        self.returns.append(return_val)

    def calculate_metrics(self) -> Dict[str, Any]:
        """計算性能指標"""
        if not self.portfolio_values:
            return {}

        total_return = (self.final_capital - self.initial_capital) / self.initial_capital
        returns_array = np.array(self.returns)

        # Sharpe比例
        sharpe_ratio = (
            np.mean(returns_array) / np.std(returns_array) * (252 ** 0.5)
            if np.std(returns_array) > 0 else 0
        )

        # 最大回撤
        cumulative = np.cumprod(1 + returns_array)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = np.min(drawdown)

        # 交易統計
        total_trades = len(self.trades)
        winning_trades = sum(1 for t in self.trades if t['pnl'] > 0)
        losing_trades = sum(1 for t in self.trades if t['pnl'] < 0)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0

        total_pnl = sum(t['pnl'] for t in self.trades)
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0

        return {
            'symbol': self.symbol,
            'strategy': self.strategy_name,
            'start_date': str(self.start_date),
            'end_date': str(self.end_date),
            'trading_days': len(self.dates),
            'initial_capital': self.initial_capital,
            'final_capital': self.final_capital,
            'total_return': float(total_return),
            'sharpe_ratio': float(sharpe_ratio),
            'max_drawdown': float(max_drawdown),
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': float(win_rate),
            'total_pnl': float(total_pnl),
            'avg_pnl': float(avg_pnl),
            'best_trade': max((t['pnl'] for t in self.trades), default=0),
            'worst_trade': min((t['pnl'] for t in self.trades), default=0),
        }


class RealDataBacktester:
    """使用真實HKEX數據的回測框架"""

    def __init__(self, initial_capital: float = 100000):
        """
        初始化回測框架

        Args:
            initial_capital: 初始資本
        """
        self.adapter = HKEXAdapter()
        self.initial_capital = initial_capital
        self.logger = logging.getLogger("hk_quant_system.real_data_backtest")

    async def backtest_single_stock(
        self,
        symbol: str,
        strategy_func: Callable,
        start_date: date,
        end_date: date,
        strategy_name: str = "unnamed_strategy",
        **strategy_params
    ) -> BacktestResults:
        """
        對單個股票進行回測

        Args:
            symbol: 股票代碼
            strategy_func: 策略函數
            start_date: 開始日期
            end_date: 結束日期
            strategy_name: 策略名稱
            **strategy_params: 策略參數

        Returns:
            BacktestResults: 回測結果
        """
        self.logger.info(f"Starting backtest for {symbol} from {start_date} to {end_date}")

        results = BacktestResults(symbol, strategy_name)
        results.initial_capital = self.initial_capital
        results.final_capital = self.initial_capital
        results.start_date = start_date
        results.end_date = end_date

        try:
            # 獲取真實歷史數據
            self.logger.info(f"[FETCHING] Real data for {symbol}...")
            historical_data = await self.adapter.get_hkex_stock_data(
                symbol, start_date, end_date
            )

            if historical_data.empty:
                self.logger.error(f"[ERROR] No data found for {symbol}")
                return results

            self.logger.info(
                f"[OK] Got {len(historical_data)} trading days\n"
                f"Price range: {historical_data['close'].min():.2f} - {historical_data['close'].max():.2f}"
            )

            # 初始化策略
            strategy = strategy_func(**strategy_params)

            # 逐日回測
            portfolio_value = self.initial_capital
            position = 0  # 持倉數量
            entry_price = 0

            for idx, row in historical_data.iterrows():
                current_date = row['date']
                current_price = row['close']

                # 生成交易信號
                signal = strategy.generate_signal(
                    price=current_price,
                    open=row['open'],
                    high=row['high'],
                    low=row['low'],
                    volume=row['volume']
                )

                # 執行交易
                if signal is not None and signal.lower() == 'buy' and position == 0:
                    quantity = int(portfolio_value / current_price * 0.8)  # 使用80%資金
                    if quantity > 0:
                        position = quantity
                        entry_price = current_price
                        results.add_trade(current_date, 'BUY', current_price, quantity)
                        self.logger.debug(
                            f"BUY: {current_date} @ {current_price:.2f}, qty={quantity}"
                        )

                elif signal is not None and signal.lower() == 'sell' and position > 0:
                    pnl = (current_price - entry_price) * position
                    portfolio_value += pnl
                    results.add_trade(
                        current_date, 'SELL', current_price, position, pnl
                    )
                    self.logger.debug(
                        f"SELL: {current_date} @ {current_price:.2f}, pnl={pnl:.2f}"
                    )
                    position = 0

                # 更新投資組合價值
                if position > 0:
                    portfolio_value_with_position = (
                        portfolio_value - (entry_price * position) + (current_price * position)
                    )
                else:
                    portfolio_value_with_position = portfolio_value

                daily_return = (portfolio_value_with_position - self.initial_capital) / self.initial_capital
                results.add_portfolio_snapshot(current_date, portfolio_value_with_position, daily_return)

            # 平倉任何開放持倉
            if position > 0:
                final_price = historical_data['close'].iloc[-1]
                pnl = (final_price - entry_price) * position
                portfolio_value += pnl
                results.add_trade(
                    historical_data['date'].iloc[-1], 'SELL (CLOSE)', final_price, position, pnl
                )
                results.final_capital = portfolio_value

            results.final_capital = portfolio_value

            # 記錄結果
            metrics = results.calculate_metrics()
            self.logger.info(f"\n[BACKTEST RESULTS] {symbol}")
            self.logger.info(f"  Total Return: {metrics['total_return']:.2%}")
            self.logger.info(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
            self.logger.info(f"  Max Drawdown: {metrics['max_drawdown']:.2%}")
            self.logger.info(f"  Total Trades: {metrics['total_trades']}")
            self.logger.info(f"  Win Rate: {metrics['win_rate']:.2%}")

            return results

        except Exception as e:
            self.logger.error(f"Error during backtest: {e}")
            return results

    async def backtest_portfolio(
        self,
        symbols: List[str],
        strategy_func: Callable,
        start_date: date,
        end_date: date,
        strategy_name: str = "unnamed_strategy",
        **strategy_params
    ) -> Dict[str, BacktestResults]:
        """
        對多個股票進行投資組合回測

        Args:
            symbols: 股票代碼列表
            strategy_func: 策略函數
            start_date: 開始日期
            end_date: 結束日期
            strategy_name: 策略名稱
            **strategy_params: 策略參數

        Returns:
            Dict[symbol -> BacktestResults]: 回測結果字典
        """
        self.logger.info(f"Starting portfolio backtest for {len(symbols)} symbols")

        results = {}

        # 使用信號量限制並發數量
        semaphore = asyncio.Semaphore(3)  # 同時進行3個回測

        async def backtest_with_semaphore(symbol):
            async with semaphore:
                return await self.backtest_single_stock(
                    symbol, strategy_func, start_date, end_date, strategy_name,
                    **strategy_params
                )

        tasks = [backtest_with_semaphore(symbol) for symbol in symbols]
        backtest_results = await asyncio.gather(*tasks)

        for symbol, result in zip(symbols, backtest_results):
            results[symbol] = result

        return results

    async def compare_strategies(
        self,
        symbol: str,
        strategies: Dict[str, Callable],
        start_date: date,
        end_date: date,
        **common_params
    ) -> Dict[str, Dict[str, Any]]:
        """
        對同一股票進行多個策略對比

        Args:
            symbol: 股票代碼
            strategies: 策略字典 {strategy_name: strategy_func}
            start_date: 開始日期
            end_date: 結束日期
            **common_params: 共享的策略參數

        Returns:
            比較結果
        """
        self.logger.info(f"Comparing {len(strategies)} strategies for {symbol}")

        comparison_results = {}

        for strategy_name, strategy_func in strategies.items():
            result = await self.backtest_single_stock(
                symbol, strategy_func, start_date, end_date, strategy_name,
                **common_params
            )
            metrics = result.calculate_metrics()
            comparison_results[strategy_name] = metrics

        return comparison_results

    async def optimize_parameters(
        self,
        symbol: str,
        strategy_func: Callable,
        param_grid: Dict[str, List[Any]],
        start_date: date,
        end_date: date,
        optimization_metric: str = "sharpe_ratio"
    ) -> Dict[str, Any]:
        """
        參數優化

        Args:
            symbol: 股票代碼
            strategy_func: 策略函數
            param_grid: 參數網格
            start_date: 開始日期
            end_date: 結束日期
            optimization_metric: 優化指標

        Returns:
            最優參數和結果
        """
        self.logger.info(f"Starting parameter optimization for {symbol}")

        best_result = None
        best_metric = -float('inf') if optimization_metric != "max_drawdown" else float('inf')
        best_params = None

        # 生成所有參數組合
        import itertools

        param_names = list(param_grid.keys())
        param_values = [param_grid[name] for name in param_names]

        total_combinations = np.prod([len(v) for v in param_values])
        self.logger.info(f"Testing {total_combinations} parameter combinations")

        for combination in itertools.product(*param_values):
            params = dict(zip(param_names, combination))

            result = await self.backtest_single_stock(
                symbol, strategy_func, start_date, end_date,
                strategy_name=f"opt_{params}",
                **params
            )

            metrics = result.calculate_metrics()
            current_metric = metrics.get(optimization_metric, 0)

            # 比較指標
            is_better = (
                current_metric > best_metric
                if optimization_metric != "max_drawdown"
                else current_metric < best_metric
            )

            if is_better:
                best_result = result
                best_metric = current_metric
                best_params = params

                self.logger.info(
                    f"New best: {params} -> {optimization_metric}={current_metric:.4f}"
                )

        return {
            "best_params": best_params,
            "best_metric": float(best_metric),
            "best_result": best_result.calculate_metrics() if best_result else None
        }

    def generate_report(self, results: BacktestResults) -> str:
        """生成回測報告"""
        metrics = results.calculate_metrics()

        report = f"""

╔════════════════════════════════════════════════════╗
║           回測結果報告                              ║
╚════════════════════════════════════════════════════╝

📊 基本信息
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  股票代碼：{metrics['symbol']}
  策略名稱：{metrics['strategy']}
  回測期間：{metrics['start_date']} to {metrics['end_date']}
  交易天數：{metrics['trading_days']}

💰 資金績效
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  初始資本：${metrics['initial_capital']:,.2f}
  最終資本：${metrics['final_capital']:,.2f}
  總收益率：{metrics['total_return']:+.2%}
  總收益額：${metrics['final_capital'] - metrics['initial_capital']:+,.2f}

📈 風險指標
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Sharpe比例：{metrics['sharpe_ratio']:.4f}
  最大回撤：{metrics['max_drawdown']:.2%}

🎯 交易統計
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  總交易數：{metrics['total_trades']}
  盈利交易：{metrics['winning_trades']}
  虧損交易：{metrics['losing_trades']}
  勝率：{metrics['win_rate']:.2%}

  平均交易盈利：${metrics['avg_pnl']:+,.2f}
  最大單筆盈利：${metrics['best_trade']:+,.2f}
  最大單筆虧損：${metrics['worst_trade']:+,.2f}
  總盈虧：${metrics['total_pnl']:+,.2f}

╚════════════════════════════════════════════════════╝
        """

        return report


# 簡單策略示例
class SimpleMovingAverageStrategy:
    """簡單移動平均策略"""

    def __init__(self, fast_period: int = 20, slow_period: int = 50, threshold: float = 0.01):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.threshold = threshold
        self.prices = []

    def generate_signal(
        self,
        price: float,
        open: float = None,
        high: float = None,
        low: float = None,
        volume: float = None
    ) -> Optional[str]:
        """生成交易信號"""
        self.prices.append(price)

        if len(self.prices) < self.slow_period:
            return None

        fast_ma = np.mean(self.prices[-self.fast_period:])
        slow_ma = np.mean(self.prices[-self.slow_period:])

        if fast_ma > slow_ma * (1 + self.threshold):
            return "buy"
        elif fast_ma < slow_ma * (1 - self.threshold):
            return "sell"

        return None


class MomentumStrategy:
    """動量策略"""

    def __init__(self, period: int = 20, momentum_threshold: float = 0.02):
        self.period = period
        self.momentum_threshold = momentum_threshold
        self.prices = []

    def generate_signal(
        self,
        price: float,
        open: float = None,
        high: float = None,
        low: float = None,
        volume: float = None
    ) -> Optional[str]:
        """生成交易信號"""
        self.prices.append(price)

        if len(self.prices) < self.period + 1:
            return None

        current_momentum = (self.prices[-1] - self.prices[-self.period - 1]) / self.prices[-self.period - 1]

        if current_momentum > self.momentum_threshold:
            return "buy"
        elif current_momentum < -self.momentum_threshold:
            return "sell"

        return None
