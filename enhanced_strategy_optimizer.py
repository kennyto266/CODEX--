#!/usr/bin/env python3
"""
增強策略優化器 - 使用多進程加速優化
獨立Python腳本，可本地執行以提高策略優化真實性
"""

import pandas as pd
import numpy as np
import requests
import logging
from datetime import datetime, timedelta
from multiprocessing import Pool, cpu_count
from functools import partial
import time
import os
import json
from typing import Dict, List, Optional

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_optimizer.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedStrategyOptimizer:
    """增強策略優化器 - 使用多進程提高效率"""

    def __init__(self):
        self.initial_capital = 100000
        self.commission_rate = 0.001
        self.max_processes = min(8, cpu_count())  # 限制進程數避免過載

    def get_stock_data(self, symbol: str, duration: int = 1825) -> Optional[List[Dict]]:
        """獲取股票數據"""
        try:
            url = 'http://18.180.162.113:9191/inst/getInst'
            params = {'symbol': symbol.lower(), 'duration': duration}

            logger.info(f"獲取股票數據: {symbol}")
            response = requests.get(url, params=params, timeout=10)

            if response.status_code != 200:
                logger.error(f"API請求失敗: {response.status_code}")
                return None

            data = response.json()

            if 'data' not in data or not isinstance(data['data'], dict):
                logger.error(f"數據格式錯誤: {data}")
                return None

            # 轉換數據格式
            time_series = data['data']
            timestamps = set()

            for key in time_series.keys():
                if key in ['open', 'high', 'low', 'close', 'volume']:
                    timestamps.update(time_series[key].keys())

            timestamps = sorted(list(timestamps))
            formatted_data = []

            for ts in timestamps:
                row = {'timestamp': ts}
                for price_type in ['open', 'high', 'low', 'close', 'volume']:
                    if price_type in time_series and ts in time_series[price_type]:
                        row[price_type] = time_series[price_type][ts]
                    else:
                        row[price_type] = None

                if all(row[key] is not None for key in ['open', 'high', 'low', 'close', 'volume']):
                    formatted_data.append(row)

            logger.info(f"成功獲取 {len(formatted_data)} 條記錄 for {symbol}")
            return formatted_data

        except Exception as e:
            logger.error(f"獲取數據失敗 for {symbol}: {str(e)}")
            return None

    def optimize_strategies_parallel(self, data: List[Dict], strategy_types: List[str] = None) -> List[Dict]:
        """使用多進程並行優化策略"""
        if strategy_types is None:
            strategy_types = ['ma', 'rsi', 'macd', 'bollinger']

        all_results = []

        start_time = time.time()

        for strategy_type in strategy_types:
            logger.info(f"開始優化 {strategy_type} 策略...")

            if strategy_type == 'ma':
                results = self._optimize_ma_parallel(data)
            elif strategy_type == 'rsi':
                results = self._optimize_rsi_parallel(data)
            elif strategy_type == 'macd':
                results = self._optimize_macd_parallel(data)
            elif strategy_type == 'bollinger':
                results = self._optimize_bollinger_parallel(data)
            else:
                continue

            all_results.extend(results)
            logger.info(f"{strategy_type} 策略優化完成，找到 {len(results)} 個有效策略")

        # 按Sharpe比率排序
        all_results.sort(key=lambda x: x.get('sharpe_ratio', 0), reverse=True)

        elapsed_time = time.time() - start_time
        logger.info(f"總優化完成，耗時 {elapsed_time:.2f} 秒，總共 {len(all_results)} 個策略")

        return all_results

    def _optimize_ma_parallel(self, data: List[Dict]) -> List[Dict]:
        """並行優化MA策略"""
        df = pd.DataFrame(data)

        # 生成參數組合
        param_combinations = []
        for short_window in range(5, 21, 2):  # 5, 7, 9, ..., 19
            for long_window in range(20, 51, 5):  # 20, 25, 30, ..., 50
                if short_window < long_window:
                    param_combinations.append((short_window, long_window))

        logger.info(f"MA策略參數組合數: {len(param_combinations)}")

        # 使用多進程
        with Pool(processes=self.max_processes) as pool:
            func = partial(self._evaluate_ma_strategy, df)
            results = pool.map(func, param_combinations)

        return [r for r in results if r is not None]

    def _optimize_rsi_parallel(self, data: List[Dict]) -> List[Dict]:
        """並行優化RSI策略"""
        df = pd.DataFrame(data)

        # 生成參數組合
        param_combinations = []
        for oversold in range(20, 41, 5):  # 20, 25, 30, 35, 40
            for overbought in range(60, 81, 5):  # 60, 65, 70, 75, 80
                if oversold < overbought:
                    param_combinations.append((oversold, overbought))

        logger.info(f"RSI策略參數組合數: {len(param_combinations)}")

        # 使用多進程
        with Pool(processes=self.max_processes) as pool:
            func = partial(self._evaluate_rsi_strategy, df)
            results = pool.map(func, param_combinations)

        return [r for r in results if r is not None]

    def _optimize_macd_parallel(self, data: List[Dict]) -> List[Dict]:
        """並行優化MACD策略"""
        df = pd.DataFrame(data)

        # MACD參數組合
        param_combinations = [
            (12, 26, 9), (8, 21, 8), (10, 22, 9), (15, 30, 10)
        ]

        logger.info(f"MACD策略參數組合數: {len(param_combinations)}")

        # 使用多進程
        with Pool(processes=self.max_processes) as pool:
            func = partial(self._evaluate_macd_strategy, df)
            results = pool.map(func, param_combinations)

        return [r for r in results if r is not None]

    def _optimize_bollinger_parallel(self, data: List[Dict]) -> List[Dict]:
        """並行優化布林帶策略"""
        df = pd.DataFrame(data)

        # 生成參數組合
        param_combinations = []
        for period in range(15, 26, 2):  # 15, 17, 19, 21, 23, 25
            for std_dev in [1.5, 2.0, 2.5]:
                param_combinations.append((period, std_dev))

        logger.info(f"布林帶策略參數組合數: {len(param_combinations)}")

        # 使用多進程
        with Pool(processes=self.max_processes) as pool:
            func = partial(self._evaluate_bollinger_strategy, df)
            results = pool.map(func, param_combinations)

        return [r for r in results if r is not None]

    def _evaluate_ma_strategy(self, df: pd.DataFrame, params: tuple) -> Optional[Dict]:
        """評估單個MA策略"""
        try:
            short_window, long_window = params
            df_copy = df.copy()

            df_copy[f'ma_short_{short_window}'] = df_copy['close'].rolling(short_window).mean()
            df_copy[f'ma_long_{long_window}'] = df_copy['close'].rolling(long_window).mean()
            df_copy.dropna(inplace=True)

            if len(df_copy) < 50:
                return None

            # 生成交易信號
            df_copy['signal'] = np.where(df_copy[f'ma_short_{short_window}'] > df_copy[f'ma_long_{long_window}'], 1, -1)
            df_copy['position'] = df_copy['signal'].diff().fillna(0)

            return self._calculate_performance(df_copy, f'MA交叉({short_window},{long_window})')

        except Exception as e:
            logger.error(f"MA策略評估失敗: {e}")
            return None

    def _evaluate_rsi_strategy(self, df: pd.DataFrame, params: tuple) -> Optional[Dict]:
        """評估單個RSI策略"""
        try:
            oversold, overbought = params
            df_copy = df.copy()

            # 計算RSI
            delta = df_copy['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df_copy['rsi'] = 100 - (100 / (1 + rs))
            df_copy.dropna(inplace=True)

            if len(df_copy) < 50:
                return None

            # 生成交易信號
            df_copy['signal'] = 0
            df_copy.loc[df_copy['rsi'] < oversold, 'signal'] = 1
            df_copy.loc[df_copy['rsi'] > overbought, 'signal'] = -1
            df_copy['position'] = df_copy['signal'].diff().fillna(0)

            return self._calculate_performance(df_copy, f'RSI({oversold},{overbought})')

        except Exception as e:
            logger.error(f"RSI策略評估失敗: {e}")
            return None

    def _evaluate_macd_strategy(self, df: pd.DataFrame, params: tuple) -> Optional[Dict]:
        """評估單個MACD策略"""
        try:
            fast, slow, signal = params
            df_copy = df.copy()

            # 計算MACD
            ema_fast = df_copy['close'].ewm(span=fast).mean()
            ema_slow = df_copy['close'].ewm(span=slow).mean()
            df_copy['macd'] = ema_fast - ema_slow
            df_copy['macd_signal'] = df_copy['macd'].ewm(span=signal).mean()
            df_copy.dropna(inplace=True)

            if len(df_copy) < 50:
                return None

            # 生成交易信號
            df_copy['signal'] = np.where(df_copy['macd'] > df_copy['macd_signal'], 1, -1)
            df_copy['position'] = df_copy['signal'].diff().fillna(0)

            return self._calculate_performance(df_copy, f'MACD({fast},{slow},{signal})')

        except Exception as e:
            logger.error(f"MACD策略評估失敗: {e}")
            return None

    def _evaluate_bollinger_strategy(self, df: pd.DataFrame, params: tuple) -> Optional[Dict]:
        """評估單個布林帶策略"""
        try:
            period, std_dev = params
            df_copy = df.copy()

            # 計算布林帶
            df_copy['bb_middle'] = df_copy['close'].rolling(window=period).mean()
            bb_std = df_copy['close'].rolling(window=period).std()
            df_copy['bb_upper'] = df_copy['bb_middle'] + (bb_std * std_dev)
            df_copy['bb_lower'] = df_copy['bb_middle'] - (bb_std * std_dev)
            df_copy.dropna(inplace=True)

            if len(df_copy) < 50:
                return None

            # 生成交易信號
            df_copy['signal'] = 0
            df_copy.loc[df_copy['close'] < df_copy['bb_lower'], 'signal'] = 1
            df_copy.loc[df_copy['close'] > df_copy['bb_upper'], 'signal'] = -1
            df_copy['position'] = df_copy['signal'].diff().fillna(0)

            return self._calculate_performance(df_copy, f'布林帶({period},{std_dev})')

        except Exception as e:
            logger.error(f"布林帶策略評估失敗: {e}")
            return None

    def _calculate_performance(self, df: pd.DataFrame, strategy_name: str) -> Dict:
        """計算策略績效"""
        try:
            # 計算回報
            df['returns'] = df['close'].pct_change()
            df['strategy_returns'] = df['position'].shift(1) * df['returns']
            df['cumulative_returns'] = (1 + df['strategy_returns']).cumprod()

            # 基本指標
            total_return = (df['cumulative_returns'].iloc[-1] - 1) * 100
            annual_return = ((df['cumulative_returns'].iloc[-1] ** (252 / len(df))) - 1) * 100
            volatility = df['strategy_returns'].std() * np.sqrt(252) * 100
            sharpe_ratio = annual_return / volatility if volatility > 0 else 0

            # 最大回撤
            cumulative = df['cumulative_returns']
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min() * 100

            # 勝率
            winning_trades = (df['strategy_returns'] > 0).sum()
            total_trades = (df['strategy_returns'] != 0).sum()
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

            # 交易次數
            trade_count = (df['position'] != 0).sum()

            return {
                'strategy_name': strategy_name,
                'sharpe_ratio': round(sharpe_ratio, 3),
                'total_return': round(total_return, 2),
                'annual_return': round(annual_return, 2),
                'volatility': round(volatility, 2),
                'max_drawdown': round(max_drawdown, 2),
                'win_rate': round(win_rate, 2),
                'trade_count': int(trade_count),
                'final_value': round(df['cumulative_returns'].iloc[-1] * self.initial_capital, 2)
            }

        except Exception as e:
            logger.error(f"績效計算失敗: {e}")
            return None


def save_results_to_file(results: List[Dict], symbol: str, filename: str = None):
    """保存結果到文件"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"strategy_optimization_{symbol}_{timestamp}.json"

    # 確保輸出目錄存在
    output_dir = "optimization_results"
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    # 保存完整結果
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump({
            'symbol': symbol,
            'total_strategies': len(results),
            'timestamp': datetime.now().isoformat(),
            'best_strategies': results[:20],  # 保存前20個最佳策略
            'all_results': results
        }, f, indent=2, ensure_ascii=False)

    print(f"結果已保存到: {filepath}")


def print_summary(results: List[Dict], symbol: str):
    """打印優化總結"""
    if not results:
        print(f"⚠️  沒有找到有效的策略 for {symbol}")
        return

    print(f"\n{'='*80}")
    print(f"🎯 {symbol} 策略優化完成")
    print(f"📊 測試策略數量: {len(results)}")
    print(f"🏆 最佳Sharpe比率: {results[0]['sharpe_ratio']}")
    print(f"⏰ 優化時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")

    print("📋 策略優化結果 (前10名)")
    print("-" * 100)
    print("<10"    print("-" * 100)

    for i, strategy in enumerate(results[:10], 1):
        print("<10")

    print(f"{'='*80}\n")


def main():
    """主函數"""
    print("🚀 增強策略優化器 - 使用多進程加速")
    print("=" * 60)

    # 設置參數
    symbol = "0700.HK"  # 可以修改為其他股票代碼
    strategy_types = ['ma', 'rsi', 'macd', 'bollinger']

    print(f"📈 優化股票: {symbol}")
    print(f"🎯 策略類型: {', '.join(strategy_types)}")
    print(f"⚡ 使用進程數: {min(8, cpu_count())}")
    print("-" * 60)

    # 初始化優化器
    optimizer = EnhancedStrategyOptimizer()

    # 獲取數據
    print("📊 獲取股票數據...")
    data = optimizer.get_stock_data(symbol)

    if not data:
        print(f"❌ 無法獲取 {symbol} 的數據")
        return

    print(f"✅ 成功獲取 {len(data)} 條數據記錄")

    # 執行優化
    print("🔬 開始策略優化...")
    start_time = time.time()

    results = optimizer.optimize_strategies_parallel(data, strategy_types)

    elapsed_time = time.time() - start_time
    print(".2f"
    # 輸出結果
    print_summary(results, symbol)

    # 保存結果
    save_results_to_file(results, symbol)

    print("✅ 優化完成！")


if __name__ == "__main__":
    main()