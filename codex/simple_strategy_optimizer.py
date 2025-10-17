#!/usr/bin/env python3
"""
極致簡潔的股票回測策略優化器
支援離線優先，計算最佳Sharpe ratio
參數範圍: 1-300，步距: 1
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict
import argparse
from pathlib import Path


class SimpleStrategyOptimizer:
    """簡單策略優化器 - 使用移動平均線交叉策略"""

    def __init__(self, data_path: str):
        """
        初始化優化器

        Args:
            data_path: CSV數據文件路徑
        """
        self.df = pd.read_csv(data_path)
        self.df['date'] = pd.to_datetime(self.df['date'])
        self.df = self.df.sort_values(['symbol', 'date'])

    def calculate_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算收益率"""
        df = df.copy()
        df['returns'] = df.groupby('symbol')['close'].pct_change()
        return df

    def moving_average_strategy(self, df: pd.DataFrame, period: int) -> pd.DataFrame:
        """
        移動平均線策略

        Args:
            df: 數據DataFrame
            period: 移動平均線週期

        Returns:
            包含信號的DataFrame
        """
        df = df.copy()
        df['ma'] = df.groupby('symbol')['close'].transform(
            lambda x: x.rolling(window=period, min_periods=1).mean()
        )

        # 生成交易信號: 價格 > MA 則買入(1)，否則賣出(0)
        df['signal'] = (df['close'] > df['ma']).astype(int)

        # 計算策略收益
        df['strategy_returns'] = df['signal'].shift(1) * df['returns']

        return df

    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.0) -> float:
        """
        計算Sharpe比率

        Args:
            returns: 收益率序列
            risk_free_rate: 無風險利率（年化）

        Returns:
            Sharpe比率
        """
        returns = returns.dropna()

        if len(returns) == 0 or returns.std() == 0:
            return -np.inf

        # 年化收益率（假設日數據）
        annual_return = returns.mean() * 252
        annual_std = returns.std() * np.sqrt(252)

        sharpe = (annual_return - risk_free_rate) / annual_std
        return sharpe

    def optimize(self, start_period: int = 1, end_period: int = 300,
                 step: int = 1) -> Tuple[int, float, Dict]:
        """
        優化策略參數以獲得最佳Sharpe ratio

        Args:
            start_period: 起始週期
            end_period: 結束週期
            step: 步距

        Returns:
            (最佳週期, 最佳Sharpe比率, 詳細結果字典)
        """
        print(f"開始優化: 週期範圍 {start_period}-{end_period}, 步距 {step}")
        print("=" * 60)

        # 計算基礎收益率
        df = self.calculate_returns(self.df)

        results = []
        best_sharpe = -np.inf
        best_period = None

        # 遍歷所有週期參數
        for period in range(start_period, end_period + 1, step):
            # 執行策略回測
            strategy_df = self.moving_average_strategy(df, period)

            # 計算Sharpe比率
            sharpe = self.calculate_sharpe_ratio(strategy_df['strategy_returns'])

            # 計算其他指標
            total_return = (1 + strategy_df['strategy_returns'].dropna()).prod() - 1
            annual_return = strategy_df['strategy_returns'].mean() * 252
            annual_vol = strategy_df['strategy_returns'].std() * np.sqrt(252)

            results.append({
                'period': period,
                'sharpe_ratio': sharpe,
                'total_return': total_return,
                'annual_return': annual_return,
                'annual_volatility': annual_vol
            })

            # 更新最佳參數
            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_period = period

            # 每10個週期輸出一次進度
            if period % 10 == 0:
                print(f"進度: 週期 {period}/{end_period}, 當前最佳Sharpe: {best_sharpe:.4f} (週期 {best_period})")

        print("=" * 60)
        print(f"[OK] 優化完成！")
        print(f"最佳週期: {best_period}")
        print(f"最佳Sharpe比率: {best_sharpe:.4f}")

        # 轉換結果為DataFrame
        results_df = pd.DataFrame(results)

        # 獲取前10名結果
        top_10 = results_df.nlargest(10, 'sharpe_ratio')

        print("\n" + "=" * 60)
        print("前10名策略參數:")
        print("=" * 60)
        for idx, row in top_10.iterrows():
            print(f"週期: {int(row['period']):3d} | Sharpe: {row['sharpe_ratio']:7.4f} | "
                  f"年化收益: {row['annual_return']:7.2%} | 年化波動: {row['annual_volatility']:7.2%}")

        return best_period, best_sharpe, {
            'all_results': results_df,
            'top_10': top_10,
            'best_period': best_period,
            'best_sharpe': best_sharpe
        }

    def backtest_with_period(self, period: int) -> pd.DataFrame:
        """
        使用指定週期進行完整回測

        Args:
            period: 移動平均線週期

        Returns:
            回測結果DataFrame
        """
        df = self.calculate_returns(self.df)
        result_df = self.moving_average_strategy(df, period)

        # 計算累計收益
        result_df['cumulative_returns'] = (1 + result_df['strategy_returns'].fillna(0)).cumprod()

        return result_df

    def save_results(self, results: Dict, output_dir: str = "results"):
        """
        保存優化結果

        Args:
            results: 優化結果字典
            output_dir: 輸出目錄
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # 保存所有結果
        all_results_path = output_path / "optimization_results.csv"
        results['all_results'].to_csv(all_results_path, index=False)
        print(f"\n所有結果已保存至: {all_results_path}")

        # 保存前10名結果
        top_10_path = output_path / "top_10_strategies.csv"
        results['top_10'].to_csv(top_10_path, index=False)
        print(f"前10名策略已保存至: {top_10_path}")

        # 使用最佳週期進行回測並保存詳細結果
        best_backtest = self.backtest_with_period(results['best_period'])
        backtest_path = output_path / "best_strategy_backtest.csv"
        best_backtest.to_csv(backtest_path, index=False)
        print(f"最佳策略回測詳情已保存至: {backtest_path}")


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='股票回測策略優化器')
    parser.add_argument('--data', type=str, required=True, help='CSV數據文件路徑')
    parser.add_argument('--start', type=int, default=1, help='起始週期（默認: 1）')
    parser.add_argument('--end', type=int, default=300, help='結束週期（默認: 300）')
    parser.add_argument('--step', type=int, default=1, help='步距（默認: 1）')
    parser.add_argument('--output', type=str, default='results', help='輸出目錄（默認: results）')

    args = parser.parse_args()

    # 檢查數據文件是否存在
    if not Path(args.data).exists():
        print(f"錯誤: 數據文件不存在: {args.data}")
        return

    # 創建優化器
    optimizer = SimpleStrategyOptimizer(args.data)

    # 執行優化
    best_period, best_sharpe, results = optimizer.optimize(
        start_period=args.start,
        end_period=args.end,
        step=args.step
    )

    # 保存結果
    optimizer.save_results(results, output_dir=args.output)

    print("\n" + "=" * 60)
    print("優化完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
