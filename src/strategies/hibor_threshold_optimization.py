#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 HIBOR 6M 策略 - 完整閾值優化系統
支援網格搜索、參數組合優化、Sharpe比率優化
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import json
from itertools import product
from multiprocessing import Pool, cpu_count
import warnings
warnings.filterwarnings('ignore')

# 導入HIBOR策略
from hibor_6m_prediction_strategy import HIBOR6MStrategy

class HIBORThresholdOptimizer:
    """HIBOR 6M 策略參數優化器"""

    def __init__(self, output_dir='analysis_output'):
        self.output_dir = output_dir
        self.results = []
        self.best_params = None
        os.makedirs(output_dir, exist_ok=True)

    def optimize_single_param(self, args):
        """優化單個參數組合"""
        hibor_threshold, holding_period, position_size = args

        try:
            strategy = HIBOR6MStrategy(
                hibor_threshold=hibor_threshold,
                holding_period=holding_period,
                position_size=position_size
            )

            # 運行回測（靜默模式）
            strategy.load_data()
            strategy.generate_signals()
            strategy.backtest()

            if strategy.backtest_results:
                return {
                    'hibor_threshold': hibor_threshold,
                    'holding_period': holding_period,
                    'position_size': position_size,
                    'total_return': strategy.backtest_results['total_return'],
                    'sharpe_ratio': strategy.backtest_results['sharpe_ratio'],
                    'max_drawdown': strategy.backtest_results['max_drawdown'],
                    'win_rate': strategy.backtest_results['win_rate'],
                    'num_trades': strategy.backtest_results['num_trades'],
                    'profit_factor': strategy.backtest_results['profit_factor'],
                    'avg_win': strategy.backtest_results['avg_win'],
                    'avg_loss': strategy.backtest_results['avg_loss'],
                }
            else:
                return None
        except Exception as e:
            print(f"優化 threshold={hibor_threshold}, period={holding_period}, size={position_size} 失敗: {e}")
            return None

    def grid_search(self,
                   hibor_thresholds=None,
                   holding_periods=None,
                   position_sizes=None,
                   max_workers=None,
                   metric='sharpe_ratio'):
        """
        網格搜索多參數組合

        Args:
            hibor_thresholds: HIBOR變化閾值列表 (%)
            holding_periods: 持倉週期列表 (天)
            position_sizes: 頭寸規模列表 (%)
            max_workers: 並行進程數
            metric: 優化指標 ('sharpe_ratio', 'total_return', 'profit_factor')
        """
        # 默認參數範圍
        if hibor_thresholds is None:
            hibor_thresholds = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30]  # 0.05% - 0.30%

        if holding_periods is None:
            holding_periods = [1, 3, 5, 7, 10]  # 1-10 天

        if position_sizes is None:
            position_sizes = [0.10, 0.20, 0.30, 0.40, 0.50]  # 10% - 50%

        if max_workers is None:
            max_workers = min(8, cpu_count())

        # 轉換百分比為小數
        hibor_thresholds_decimal = [t / 100 for t in hibor_thresholds]

        print("=" * 100)
        print(f"🎯 開始HIBOR 6M 策略參數網格搜索")
        print("=" * 100)
        print(f"\n搜索空間:")
        print(f"  HIBOR閾值: {hibor_thresholds} %")
        print(f"  持倉週期: {holding_periods} 天")
        print(f"  頭寸規模: {position_sizes} %")
        print(f"  總組合數: {len(hibor_thresholds) * len(holding_periods) * len(position_sizes)}")
        print(f"  並行進程: {max_workers}")
        print(f"  優化指標: {metric}\n")

        # 生成所有參數組合
        param_combinations = list(product(
            hibor_thresholds_decimal,
            holding_periods,
            position_sizes
        ))

        print(f"開始優化... (預計 {len(param_combinations)} 個組合)")

        # 多進程優化
        with Pool(processes=max_workers) as pool:
            results = pool.map(self.optimize_single_param, param_combinations)

        # 篩選有效結果
        valid_results = [r for r in results if r is not None]

        print(f"\n✅ 完成優化，有效組合: {len(valid_results)}/{len(param_combinations)}")

        # 排序結果
        self.results = sorted(valid_results, key=lambda x: x[metric], reverse=True)

        # 找最佳參數
        if self.results:
            self.best_params = self.results[0]
            print(f"\n🏆 最佳參數 (按 {metric}):")
            self._print_param_result(self.best_params)

        return self.results

    def optimize_single_param_group(self,
                                   hibor_threshold_range,
                                   holding_period_range,
                                   position_size_range,
                                   metric='sharpe_ratio'):
        """
        優化單個參數範圍內的最佳值

        Args:
            hibor_threshold_range: (min, max, step) 元組，百分比
            holding_period_range: (min, max, step) 元組，天數
            position_size_range: (min, max, step) 元組，百分比
        """
        print("=" * 100)
        print(f"🎯 細粒度參數優化")
        print("=" * 100)

        # 生成參數列表
        hibor_min, hibor_max, hibor_step = hibor_threshold_range
        holding_min, holding_max, holding_step = holding_period_range
        position_min, position_max, position_step = position_size_range

        hibor_thresholds = np.arange(hibor_min, hibor_max + hibor_step, hibor_step)
        holding_periods = np.arange(holding_min, holding_max + holding_step, holding_step, dtype=int)
        position_sizes = np.arange(position_min, position_max + position_step, position_step)

        print(f"\nHIBOR閾值: {hibor_thresholds.tolist()}")
        print(f"持倉週期: {holding_periods.tolist()}")
        print(f"頭寸規模: {position_sizes.tolist()}\n")

        return self.grid_search(
            hibor_thresholds=hibor_thresholds,
            holding_periods=holding_periods,
            position_sizes=position_sizes,
            metric=metric
        )

    def sensitivity_analysis(self):
        """
        單變量敏感性分析
        分別優化每個參數，固定其他參數
        """
        print("\n" + "=" * 100)
        print("📊 單變量敏感性分析")
        print("=" * 100)

        if not self.best_params:
            print("請先運行 grid_search() 來找到最佳基礎參數")
            return {}

        base_threshold = self.best_params['hibor_threshold']
        base_period = self.best_params['holding_period']
        base_size = self.best_params['position_size']

        sensitivity_results = {}

        # 1. HIBOR閾值敏感性
        print(f"\n1️⃣ HIBOR閾值敏感性分析 (固定period={base_period}, size={base_size})...")
        threshold_results = []
        for threshold in np.arange(0.001, 0.051, 0.005):
            result = self.optimize_single_param((threshold, base_period, base_size))
            if result:
                threshold_results.append(result)

        sensitivity_results['threshold'] = sorted(threshold_results, key=lambda x: x['sharpe_ratio'], reverse=True)

        # 2. 持倉週期敏感性
        print(f"2️⃣ 持倉週期敏感性分析 (固定threshold={base_threshold:.4f}, size={base_size})...")
        period_results = []
        for period in range(1, 21):
            result = self.optimize_single_param((base_threshold, period, base_size))
            if result:
                period_results.append(result)

        sensitivity_results['holding_period'] = sorted(period_results, key=lambda x: x['sharpe_ratio'], reverse=True)

        # 3. 頭寸規模敏感性
        print(f"3️⃣ 頭寸規模敏感性分析 (固定threshold={base_threshold:.4f}, period={base_period})...")
        size_results = []
        for size in np.arange(0.05, 0.55, 0.05):
            result = self.optimize_single_param((base_threshold, base_period, size))
            if result:
                size_results.append(result)

        sensitivity_results['position_size'] = sorted(size_results, key=lambda x: x['sharpe_ratio'], reverse=True)

        # 打印結果
        self._print_sensitivity_results(sensitivity_results)

        return sensitivity_results

    def get_top_combos(self, top_n=10, metric='sharpe_ratio'):
        """獲取TOP N 最佳組合"""
        if not self.results:
            return pd.DataFrame()

        df = pd.DataFrame(self.results)
        df = df.sort_values(metric, ascending=False)
        return df.head(top_n)

    def save_results(self, filename=None):
        """保存優化結果"""
        if filename is None:
            filename = f"hibor_optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        filepath = os.path.join(self.output_dir, filename)

        if self.results:
            df = pd.DataFrame(self.results)
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            print(f"\n✅ 結果已保存: {filepath}")

            # 也保存JSON格式
            json_path = filepath.replace('.csv', '.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'best_params': self.best_params,
                    'results': self.results[:100],  # 前100個結果
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
            print(f"✅ JSON結果已保存: {json_path}")

        return filepath

    def _print_param_result(self, result):
        """打印單個參數結果"""
        print(f"  HIBOR閾值: {result['hibor_threshold']:.4f} ({result['hibor_threshold']*100:.2f}%)")
        print(f"  持倉週期: {result['holding_period']} 天")
        print(f"  頭寸規模: {result['position_size']:.0%}")
        print(f"  Sharpe比率: {result['sharpe_ratio']:.4f} ⭐")
        print(f"  年化收益: {result['total_return']:.2%}")
        print(f"  最大回撤: {result['max_drawdown']:.2%}")
        print(f"  勝率: {result['win_rate']:.2%}")
        print(f"  盈利因子: {result['profit_factor']:.2f}")
        print(f"  交易次數: {result['num_trades']}")

    def _print_sensitivity_results(self, sensitivity_results):
        """打印敏感性分析結果"""
        print("\n" + "=" * 100)
        print("📈 敏感性分析結果")
        print("=" * 100)

        for param_name, results in sensitivity_results.items():
            print(f"\n{param_name.upper()} 敏感性:")
            print("-" * 100)

            if results:
                top_5 = results[:5]
                for i, result in enumerate(top_5, 1):
                    print(f"\n  {i}. ", end="")
                    if param_name == 'threshold':
                        print(f"HIBOR閾值={result['hibor_threshold']*100:.3f}%")
                    elif param_name == 'holding_period':
                        print(f"持倉週期={result['holding_period']} 天")
                    else:
                        print(f"頭寸規模={result['position_size']:.0%}")

                    print(f"     Sharpe={result['sharpe_ratio']:.4f}, 收益={result['total_return']:.2%}, 勝率={result['win_rate']:.2%}")


def main():
    """主函數 - 演示不同的優化策略"""

    print("\n" + "=" * 100)
    print("🚀 HIBOR 6M 策略參數優化演示")
    print("=" * 100)

    optimizer = HIBORThresholdOptimizer()

    # 方案1: 完整網格搜索
    print("\n\n【方案1: 完整網格搜索】")
    results_grid = optimizer.grid_search(
        hibor_thresholds=[0.05, 0.10, 0.15, 0.20, 0.25, 0.30],
        holding_periods=[1, 3, 5, 7, 10],
        position_sizes=[0.15, 0.20, 0.30, 0.40],
        metric='sharpe_ratio'
    )

    # 顯示TOP 10
    print("\n\n🏆 TOP 10 最佳組合 (按Sharpe比率):")
    print("=" * 100)
    top_combos = optimizer.get_top_combos(top_n=10, metric='sharpe_ratio')
    print(top_combos[['hibor_threshold', 'holding_period', 'position_size',
                      'sharpe_ratio', 'total_return', 'max_drawdown', 'win_rate']].to_string())

    # 方案2: 細粒度優化 (圍繞最佳參數)
    if optimizer.best_params:
        print("\n\n【方案2: 細粒度優化 (圍繞最佳參數)】")

        best_threshold = optimizer.best_params['hibor_threshold']
        best_period = optimizer.best_params['holding_period']
        best_size = optimizer.best_params['position_size']

        print(f"\n基礎最佳參數:")
        print(f"  HIBOR閾值: {best_threshold*100:.3f}%")
        print(f"  持倉週期: {best_period} 天")
        print(f"  頭寸規模: {best_size:.0%}")

        # 在最佳參數附近細化搜索
        refined_results = optimizer.optimize_single_param_group(
            hibor_threshold_range=(max(0.001, best_threshold - 0.005), best_threshold + 0.005, 0.001),
            holding_period_range=(max(1, best_period - 2), best_period + 2, 1),
            position_size_range=(max(0.05, best_size - 0.05), best_size + 0.05, 0.01),
            metric='sharpe_ratio'
        )

    # 方案3: 敏感性分析
    print("\n\n【方案3: 單變量敏感性分析】")
    sensitivity = optimizer.sensitivity_analysis()

    # 保存結果
    optimizer.save_results()

    print("\n\n" + "=" * 100)
    print("✅ 優化完成！")
    print("=" * 100)
    print("\n💡 優化支援功能:")
    print("  ✓ 完整網格搜索 (多參數組合)")
    print("  ✓ 細粒度優化 (圍繞最佳點)")
    print("  ✓ 敏感性分析 (單變量)")
    print("  ✓ 多指標優化 (Sharpe, 收益, 盈利因子等)")
    print("  ✓ 並行計算 (加速優化)")
    print("  ✓ 結果導出 (CSV/JSON)")


if __name__ == '__main__':
    main()
