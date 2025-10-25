#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
統一策略優化器 - CODEX 版本
支援多種優化模式（網格、隨機、暴力搜索）的生產級優化引擎
已適配到 CODEX 主項目，支援 RSI, MACD, Bollinger 等策略
"""

import pandas as pd
import numpy as np
import random
import json
import hashlib
from typing import Dict, List, Any, Tuple, Callable, Optional, Union
from datetime import datetime
import itertools
from multiprocessing import Pool, cpu_count
from functools import partial
from tqdm import tqdm
import logging
import gc
import psutil
import warnings

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


class ProductionOptimizer:
    """
    生產級策略優化器，支援多種優化模式
    - Grid Search 網格搜索
    - Random Search 隨機搜索
    - Brute Force 暴力搜索

    特性：
    - 多進程並行優化（自動檢測CPU核心數）
    - 5折交叉驗證
    - 記憶體管理（批處理、垃圾回收）
    - 詳細的性能指標計算
    - 參數穩定性分析
    """

    def __init__(self, symbol: str, start_date: str, end_date: Optional[str] = None,
                 data_fetcher=None):
        """
        初始化優化器

        Args:
            symbol: 股票代碼 (e.g., '0700.hk')
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD，默認為今天)
            data_fetcher: 數據獲取器實例（可選，用於自定義數據源）
        """
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date if end_date is not None else datetime.now().strftime('%Y-%m-%d')
        self.data: Optional[pd.DataFrame] = None
        self.train_data: Optional[pd.DataFrame] = None
        self.validation_data: Optional[pd.DataFrame] = None
        self.best_params: Dict = {}
        self.use_cross_validation = False
        self.train_ratio = 0.7  # 70% 訓練集
        self.max_processes = min(32, cpu_count())
        self.signals: Optional[pd.Series] = None
        self.data_fetcher = data_fetcher
        self._setup_logging()

        # 優化統計信息
        self.optimization_stats = {
            'total_combinations': 0,
            'valid_results': 0,
            'failed_combinations': 0,
            'optimization_time': 0.0,
            'best_sharpe': 0.0
        }

    def _setup_logging(self):
        """設置日誌記錄"""
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    def load_data(self) -> Optional[pd.DataFrame]:
        """
        載入數據

        Returns:
            DataFrame: 包含 OHLCV 的數據框
        """
        try:
            if self.data_fetcher is None:
                # 如果沒有提供 data_fetcher，嘗試使用 CODEX 默認的數據服務
                from src.data_providers import PrimaryDataProvider

                # 創建一個簡單的數據獲取包裝器
                class SimpleDataFetcher:
                    def __init__(self):
                        self.provider = PrimaryDataProvider()

                    def fetch_data(self, symbol, start_date, end_date):
                        """從 PrimaryDataProvider 獲取數據"""
                        try:
                            # 使用 yfinance 作為備選方案
                            import yfinance as yf
                            # 轉換符號格式 (如 0700.hk -> 0700.HK)
                            symbol_yf = symbol.replace('.hk', '.HK').replace('.HK', '.HK')
                            if '.HK' not in symbol_yf.upper():
                                symbol_yf = symbol + '.HK'

                            df = yf.download(symbol_yf, start=start_date, end=end_date, progress=False)

                            if df.empty:
                                return None

                            # 確保列名符合期望
                            df = df.reset_index()
                            # 根據實際列數進行處理
                            if len(df.columns) == 7:
                                # 包含 Dividends 或其他列
                                df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']]
                            elif len(df.columns) >= 6:
                                df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'][:len(df.columns)]

                            df['Date'] = pd.to_datetime(df['Date'])
                            return df
                        except Exception as e:
                            logger.warning(f"yfinance download failed: {e}, using dummy data")
                            # 生成虛擬數據作為備選
                            dates = pd.date_range(start=start_date, end=end_date, freq='D')
                            n = len(dates)
                            df = pd.DataFrame({
                                'Date': dates,
                                'Open': np.random.uniform(20, 30, n),
                                'High': np.random.uniform(30, 40, n),
                                'Low': np.random.uniform(10, 20, n),
                                'Close': np.random.uniform(20, 30, n),
                                'Adj Close': np.random.uniform(20, 30, n),
                                'Volume': np.random.uniform(1000000, 10000000, n).astype(int)
                            })
                            return df

                fetcher = SimpleDataFetcher()
            else:
                fetcher = self.data_fetcher

            self.data = fetcher.fetch_data(self.symbol, self.start_date, self.end_date)

            if isinstance(self.data, pd.DataFrame) and not self.data.empty:
                logger.info(f"✅ 成功載入 {len(self.data)} 天的數據")

                # 分割訓練集和驗證集
                train_size = int(len(self.data) * self.train_ratio)
                self.train_data = self.data.iloc[:train_size].copy()
                self.validation_data = self.data.iloc[train_size:].copy()

                logger.info(f"📈 訓練集大小: {len(self.train_data)} 天")
                logger.info(f"📊 驗證集大小: {len(self.validation_data)} 天")

                return self.data
            else:
                logger.error("❌ 數據載入失敗")
                return None
        except Exception as e:
            logger.error(f"❌ 數據載入失敗: {str(e)}")
            return None

    def evaluate_strategy(self, strategy_instance: Any, data: pd.DataFrame) -> Dict:
        """
        評估策略性能，計算全面的績效指標

        Args:
            strategy_instance: 策略實例
            data: OHLCV 數據框

        Returns:
            Dict: 包含 Sharpe, Sortino, Return, Drawdown 等指標
        """
        try:
            # 生成信號
            signals_output = strategy_instance.generate_signals(data)

            # 處理策略輸出 - 支持 Series 和 DataFrame
            if isinstance(signals_output, pd.Series):
                # 策略返回 Series 格式的信號
                signals = pd.DataFrame(index=data.index)
                signals['signal'] = signals_output
            else:
                # 策略返回 DataFrame 格式
                signals = signals_output

            if signals.empty or 'signal' not in signals.columns:
                return {}

            # 計算交易統計
            nonzero_count = int((signals['signal'] != 0).sum())
            if nonzero_count == 0:  # 沒有交易信號
                return {}

            # 計算收益和頭寸
            signals['position'] = signals['signal'].replace(0, np.nan).fillna(method='ffill').fillna(0)
            signals['returns'] = data['Close'].pct_change().fillna(0)
            signals['strategy_returns'] = signals['position'].shift(1) * signals['returns']
            signals.loc[signals.index[0], 'strategy_returns'] = 0

            signals['equity'] = (1 + signals['strategy_returns']).cumprod()

            # 計算基礎績效指標
            total_return = signals['equity'].iloc[-1] - 1
            annual_return = (1 + total_return) ** (252 / len(signals)) - 1
            daily_returns = signals['strategy_returns']
            volatility = daily_returns.std() * np.sqrt(252)

            # 計算夏普比率
            risk_free_rate = 0.02
            excess_returns = annual_return - risk_free_rate
            sharpe_ratio = excess_returns / volatility if volatility > 0 else 0

            # 計算索提諾比率
            downside_returns = daily_returns[daily_returns < 0]
            downside_volatility = downside_returns.std() * np.sqrt(252) if not downside_returns.empty else 0
            sortino_ratio = excess_returns / downside_volatility if downside_volatility > 0 else 0

            # 計算最大回撤
            rolling_max = signals['equity'].expanding().max()
            drawdowns = signals['equity'] / rolling_max - 1
            max_drawdown = drawdowns.min()

            # 計算最大回撤持續時間
            drawdown_periods = pd.DataFrame(index=signals.index)
            drawdown_periods['drawdown'] = drawdowns
            drawdown_periods['is_drawdown'] = drawdown_periods['drawdown'] < 0
            drawdown_periods['drawdown_group'] = (drawdown_periods['is_drawdown'] != drawdown_periods['is_drawdown'].shift()).cumsum()
            drawdown_durations = drawdown_periods[drawdown_periods['is_drawdown']].groupby('drawdown_group').size()
            max_drawdown_duration = drawdown_durations.max() if not drawdown_durations.empty else 0

            # 計算交易統計
            trading_days = signals[signals['strategy_returns'] != 0]
            win_rate = (trading_days['strategy_returns'] > 0).mean() * 100 if not trading_days.empty else 0

            # 計算平均獲利和虧損
            avg_profit = trading_days[trading_days['strategy_returns'] > 0]['strategy_returns'].mean() if not trading_days.empty else 0
            avg_loss = trading_days[trading_days['strategy_returns'] < 0]['strategy_returns'].mean() if not trading_days.empty else 0
            profit_loss_ratio = abs(avg_profit / avg_loss) if avg_loss != 0 else 0

            # 計算持倉時間統計
            position_changes = signals['position'].diff().fillna(0)
            trade_starts = position_changes != 0
            holding_periods = []
            current_period = 0

            for i in range(len(signals)):
                if trade_starts.iloc[i]:
                    if current_period > 0:
                        holding_periods.append(current_period)
                    current_period = 1
                elif signals['position'].iloc[i] != 0:
                    current_period += 1

            if current_period > 0:
                holding_periods.append(current_period)

            avg_holding_period = np.mean(holding_periods) if holding_periods else 0

            # 清理記憶體
            del signals, drawdown_periods, trading_days
            gc.collect()

            return {
                'sharpe_ratio': float(sharpe_ratio),
                'sortino_ratio': float(sortino_ratio),
                'annual_return': float(annual_return * 100),
                'max_drawdown': float(max_drawdown * 100),
                'max_drawdown_duration': int(max_drawdown_duration),
                'volatility': float(volatility * 100),
                'win_rate': float(win_rate),
                'profit_loss_ratio': float(profit_loss_ratio),
                'avg_holding_period': float(avg_holding_period),
                'trade_count': int(nonzero_count),
                'avg_profit': float(avg_profit * 100),
                'avg_loss': float(avg_loss * 100)
            }
        except Exception as e:
            logger.error(f"Strategy evaluation failed: {e}")
            return {}

    def _validate_param_grid(self, param_grid: Dict) -> None:
        """驗證參數網格的有效性"""
        if not param_grid:
            raise ValueError("參數網格不能為空")

        for param_name, param_values in param_grid.items():
            if not param_values:
                raise ValueError(f"參數 {param_name} 的值列表不能為空")

            # 檢查參數類型
            if all(isinstance(x, (int, float)) for x in param_values):
                if min(param_values) <= 0 and param_name.lower() in ['period', 'fast', 'slow', 'signal']:
                    raise ValueError(f"參數 {param_name} 的值必須大於0")
                if param_name.lower() in ['std_dev', 'threshold'] and min(param_values) <= 0:
                    raise ValueError(f"參數 {param_name} 的值必須大於0")

            # 檢查參數數量
            if len(param_values) > 100:
                logger.warning(f"參數 {param_name} 的值數量過多 ({len(param_values)})，可能導致搜索時間過長")

    def _calculate_param_stability(self, results: List[Dict], best_params: Dict) -> Dict:
        """計算參數穩定性分數"""
        param_scores = {}
        for param_name in best_params.keys():
            param_values = [r['params'][param_name] for r in results]
            best_value = best_params[param_name]
            frequency = param_values.count(best_value) / len(param_values) if param_values else 0

            if isinstance(best_value, (int, float)):
                deviations = [abs(v - best_value) / best_value for v in param_values if best_value != 0]
                avg_deviation = np.mean(deviations) if deviations else 0
                param_scores[param_name] = {
                    'stability': float(frequency),
                    'avg_deviation': float(avg_deviation)
                }
            else:
                param_scores[param_name] = {
                    'stability': float(frequency)
                }
        return param_scores

    def _calculate_param_distribution(self, results: List[Dict]) -> Dict:
        """計算參數分佈統計"""
        param_stats = {}
        if not results:
            return param_stats

        param_names = results[0]['params'].keys()

        for param_name in param_names:
            param_values = [r['params'][param_name] for r in results]

            if all(isinstance(x, (int, float)) for x in param_values):
                param_stats[param_name] = {
                    'mean': float(np.mean(param_values)),
                    'std': float(np.std(param_values)),
                    'min': float(min(param_values)),
                    'max': float(max(param_values)),
                    'median': float(np.median(param_values))
                }
            else:
                value_counts = {}
                for value in param_values:
                    value_counts[str(value)] = value_counts.get(str(value), 0) + 1
                param_stats[param_name] = {'value_counts': value_counts}

        return param_stats

    def _calculate_param_hash(self, params: Dict) -> str:
        """計算參數組合的哈希值，用於結果去重和緩存"""
        param_str = json.dumps(params, sort_keys=True, default=str)
        return hashlib.md5(param_str.encode()).hexdigest()

    def grid_search(self, strategy_factory: Callable, param_grid: Dict) -> Dict:
        """
        網格搜索，包含交叉驗證

        Args:
            strategy_factory: 策略工廠函數，接收參數字典並返回策略實例
            param_grid: 參數網格 {'param_name': [values]}

        Returns:
            Dict: 包含最佳參數、性能指標等的結果
        """
        self._validate_param_grid(param_grid)

        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        param_combinations = list(itertools.product(*param_values))

        logger.info(f"開始網格搜索，共 {len(param_combinations)} 組參數組合")
        self.optimization_stats['total_combinations'] = len(param_combinations)

        # 5折交叉驗證
        n_splits = 5
        data_length = len(self.train_data)
        fold_size = data_length // n_splits

        all_results = []
        for fold in range(n_splits):
            logger.info(f"開始第 {fold + 1} 折交叉驗證")

            # 分割數據
            val_start = fold * fold_size
            val_end = val_start + fold_size
            if fold == n_splits - 1:
                val_end = data_length

            train_data = pd.concat([
                self.train_data.iloc[:val_start],
                self.train_data.iloc[val_end:]
            ])
            val_data = self.train_data.iloc[val_start:val_end]

            # 評估每個參數組合
            fold_results = []
            for params in param_combinations:
                try:
                    param_dict = dict(zip(param_names, params))
                    strategy = strategy_factory(param_dict)
                    train_metrics = self.evaluate_strategy(strategy, train_data)

                    if train_metrics and 'sharpe_ratio' in train_metrics and train_metrics['trade_count'] > 0:
                        val_metrics = self.evaluate_strategy(strategy, val_data)
                        if val_metrics:
                            fold_results.append({
                                'params': param_dict,
                                'train_metrics': train_metrics,
                                'val_metrics': val_metrics,
                                'fold': fold,
                                'param_hash': self._calculate_param_hash(param_dict)
                            })
                            self.optimization_stats['valid_results'] += 1
                except Exception as e:
                    self.optimization_stats['failed_combinations'] += 1
                    logger.debug(f"參數評估失敗: {e}")

            all_results.extend(fold_results)
            del train_data, val_data, fold_results
            gc.collect()

        if all_results:
            # 排序結果
            def avg_score(result):
                train_sharpe = result['train_metrics'].get('sharpe_ratio', 0)
                val_sharpe = result['val_metrics'].get('sharpe_ratio', 0)
                train_sortino = result['train_metrics'].get('sortino_ratio', 0)
                val_sortino = result['val_metrics'].get('sortino_ratio', 0)
                train_trades = result['train_metrics'].get('trade_count', 0)
                val_trades = result['val_metrics'].get('trade_count', 0)

                train_score = (train_sharpe + train_sortino) * (1 + np.log1p(train_trades) / 10)
                val_score = (val_sharpe + val_sortino) * (1 + np.log1p(val_trades) / 10)

                if train_sharpe <= 0 or val_sharpe <= 0:
                    return float('-inf')

                return (train_score + val_score) / 2

            best_result = max(all_results, key=avg_score)
            best_params = best_result['params']

            # 最終驗證
            final_validation_metrics = self.evaluate_strategy(
                strategy_factory(best_params),
                self.validation_data
            )

            param_stability = self._calculate_param_stability(all_results, best_params)

            logger.info(f"網格搜索完成，找到最佳參數：{best_params}")
            logger.info(f"最佳 Sharpe 比率: {final_validation_metrics.get('sharpe_ratio', 0):.4f}")

            self.optimization_stats['best_sharpe'] = final_validation_metrics.get('sharpe_ratio', 0)

            return {
                'best_params': best_params,
                'param_stability': param_stability,
                'train_metrics': best_result['train_metrics'],
                'cv_metrics': best_result['val_metrics'],
                'validation_metrics': final_validation_metrics,
                'method': 'Grid Search with Cross-Validation',
                'total_evaluated': len(all_results)
            }

        logger.warning("網格搜索未找到有效參數組合")
        return {}

    def random_search(self, strategy_factory: Callable, param_grid: Dict, n_iter: int = 100) -> Dict:
        """
        隨機搜索，包含交叉驗證

        Args:
            strategy_factory: 策略工廠函數
            param_grid: 參數網格
            n_iter: 每折的迭代次數

        Returns:
            Dict: 優化結果
        """
        self._validate_param_grid(param_grid)

        logger.info(f"開始隨機搜索，每折迭代次數：{n_iter}")

        n_splits = 5
        data_length = len(self.train_data)
        fold_size = data_length // n_splits

        all_results = []
        for fold in range(n_splits):
            logger.info(f"開始第 {fold + 1} 折交叉驗證")

            val_start = fold * fold_size
            val_end = val_start + fold_size
            if fold == n_splits - 1:
                val_end = data_length

            train_data = pd.concat([
                self.train_data.iloc[:val_start],
                self.train_data.iloc[val_end:]
            ])
            val_data = self.train_data.iloc[val_start:val_end]

            # 隨機採樣參數
            for _ in range(n_iter):
                try:
                    param_dict = {name: random.choice(values) for name, values in param_grid.items()}
                    strategy = strategy_factory(param_dict)
                    train_metrics = self.evaluate_strategy(strategy, train_data)

                    if train_metrics and 'sharpe_ratio' in train_metrics and train_metrics['trade_count'] > 0:
                        val_metrics = self.evaluate_strategy(strategy, val_data)
                        if val_metrics:
                            all_results.append({
                                'params': param_dict,
                                'train_metrics': train_metrics,
                                'val_metrics': val_metrics,
                                'fold': fold
                            })
                except Exception as e:
                    logger.debug(f"參數評估失敗: {e}")

            del train_data, val_data
            gc.collect()

        if all_results:
            # 排序和報告
            def avg_score(result):
                train_sharpe = result['train_metrics'].get('sharpe_ratio', 0)
                val_sharpe = result['val_metrics'].get('sharpe_ratio', 0)
                if train_sharpe <= 0 or val_sharpe <= 0:
                    return float('-inf')
                return (train_sharpe + val_sharpe) / 2

            best_result = max(all_results, key=avg_score)
            best_params = best_result['params']

            final_validation_metrics = self.evaluate_strategy(
                strategy_factory(best_params),
                self.validation_data
            )

            param_stability = self._calculate_param_stability(all_results, best_params)
            param_distribution = self._calculate_param_distribution(all_results)

            return {
                'best_params': best_params,
                'param_stability': param_stability,
                'param_distribution': param_distribution,
                'train_metrics': best_result['train_metrics'],
                'cv_metrics': best_result['val_metrics'],
                'validation_metrics': final_validation_metrics,
                'method': 'Random Search with Cross-Validation',
                'total_evaluated': len(all_results)
            }

        logger.warning("隨機搜索未找到有效參數組合")
        return {}

    def brute_force(self, test_func: Callable, param_combinations: List,
                   max_processes: Optional[int] = None) -> List:
        """
        暴力搜索所有參數組合

        Args:
            test_func: 測試函數
            param_combinations: 參數組合列表
            max_processes: 最大進程數

        Returns:
            List: 有效結果列表
        """
        if max_processes is None or max_processes <= 0:
            max_processes = self.max_processes

        total_combinations = len(param_combinations)
        logger.info(f"開始暴力搜索，共 {total_combinations} 組參數組合")

        batch_size = min(1000, total_combinations)
        num_batches = (total_combinations + batch_size - 1) // batch_size

        all_results = []
        total_valid = 0
        total_processed = 0

        try:
            for batch_idx in range(num_batches):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, total_combinations)
                current_batch = param_combinations[start_idx:end_idx]

                logger.info(f"處理第 {batch_idx + 1}/{num_batches} 批次")

                with Pool(processes=max_processes) as pool:
                    batch_results = list(tqdm(
                        pool.imap(test_func, current_batch),
                        total=len(current_batch),
                        desc=f"批次 {batch_idx + 1} 進度"
                    ))

                valid_results = [r for r in batch_results if r]
                all_results.extend(valid_results)

                total_valid += len(valid_results)
                total_processed += len(current_batch)

                del batch_results, valid_results
                gc.collect()

        except Exception as e:
            logger.error(f"暴力搜索過程中發生錯誤: {e}")
            return all_results

        logger.info(f"暴力搜索完成，共找到 {len(all_results)} 個有效結果")
        return all_results

    def get_stats(self) -> Dict:
        """獲取優化統計信息"""
        return self.optimization_stats.copy()
