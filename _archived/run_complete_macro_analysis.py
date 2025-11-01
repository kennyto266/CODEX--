# -*- coding: utf-8 -*-
"""
================================================================================
完整宏观量化分析 - 主执行脚本
================================================================================
执行完整的企业级宏观分析流程:

1. 数据加载和清洗 - 6类政府数据 + HKEX市场数据
2. 宏观景气指标构建 - 5个子指标和综合评分
3. 多层相关性分析 - 4个层级完整分析
4. 板块轮动分析 - 基于宏观指标的板块评分
5. 风险管理框架 - VaR和动态头寸管理
6. 5个交易策略回测 - 完整性能评估
7. 可视化和报告生成 - 10+张专业图表

作者: CODEX Quantitative System
日期: 2025-10-24
执行时间: 预计15-20分钟
================================================================================
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 处理 UTF-8 编码
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加当前目录到路径
sys.path.insert(0, os.getcwd())

# 导入自定义模块
from comprehensive_macro_analysis import (
    ComprehensiveMacroDataLoader,
    MacroEconomicIndicatorBuilder
)

from macro_trading_strategies import (
    BusinessCycleTradingStrategy,
    InterestRateLiquidityStrategy,
    SectorRotationStrategy,
    VisitorConsumptionStrategy,
    CompositeScoreTradingStrategy
)

# 设置绘图样式
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid")
sns.set_palette("husl")


class CompleteMacroAnalysisEngine:
    """完整宏观分析引擎"""

    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.output_dir = self.base_dir / "macro_analysis_output"
        self.output_dir.mkdir(exist_ok=True)

        # 核心组件
        self.data_loader = None
        self.indicator_builder = None

        # 数据容器
        self.raw_data = {}
        self.composite_score = None
        self.correlation_results = {}
        self.strategy_results = {}

        # 时间戳
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def run_complete_analysis(self):
        """运行完整分析流程"""

        print("\n" + "=" * 100)
        print("=" * 100)
        print("完整宏观量化分析系统 - 开始执行")
        print("=" * 100)
        print("=" * 100)

        # Step 1: 数据加载
        self.step1_load_data()

        # Step 2: 构建宏观指标
        self.step2_build_indicators()

        # Step 3: 多层相关性分析
        self.step3_correlation_analysis()

        # Step 4: 板块轮动分析
        self.step4_sector_rotation()

        # Step 5: 风险管理
        self.step5_risk_management()

        # Step 6: 交易策略回测
        self.step6_strategy_backtest()

        # Step 7: 可视化
        self.step7_visualization()

        # Step 8: 生成报告
        self.step8_generate_reports()

        print("\n" + "=" * 100)
        print("完整宏观分析执行完成!")
        print(f"输出目录: {self.output_dir}")
        print("=" * 100)

    def step1_load_data(self):
        """Step 1: 数据加载"""
        print("\n" + "=" * 100)
        print("STEP 1: 数据加载")
        print("=" * 100)

        self.data_loader = ComprehensiveMacroDataLoader(self.base_dir)
        self.raw_data = self.data_loader.load_all_data()

        # 保存数据摘要
        self._save_data_summary()

    def step2_build_indicators(self):
        """Step 2: 构建宏观指标"""
        print("\n" + "=" * 100)
        print("STEP 2: 构建宏观景气指标")
        print("=" * 100)

        self.indicator_builder = MacroEconomicIndicatorBuilder(self.data_loader)
        self.composite_score = self.indicator_builder.build_composite_indicator()

        # 保存指标数据
        output_file = self.output_dir / f"composite_indicators_{self.timestamp}.csv"
        self.composite_score.to_csv(output_file)
        print(f"\n✓ 综合指标已保存: {output_file}")

    def step3_correlation_analysis(self):
        """Step 3: 多层相关性分析"""
        print("\n" + "=" * 100)
        print("STEP 3: 多层相关性分析")
        print("=" * 100)

        if self.composite_score is None or self.data_loader.hkex_data is None:
            print("× 数据不完整，跳过相关性分析")
            return

        # 层级1: 宏观层面
        print("\n[层级1] 宏观指标 vs 股市表现...")
        self._macro_correlation_analysis()

        # 层级2: 利率层面
        print("\n[层级2] HIBOR期限结构 vs 股市波动...")
        self._interest_rate_correlation()

        # 层级3: 流动性层面
        print("\n[层级3] 金融流动性 vs 市场表现...")
        self._liquidity_correlation()

        # 层级4: 滞后关系
        print("\n[层级4] 滞后相关性分析...")
        self._lagged_correlation_analysis()

        # 保存相关性结果
        self._save_correlation_results()

    def _macro_correlation_analysis(self):
        """宏观层面相关性分析"""

        # 合并数据
        merged = self.composite_score.join(self.data_loader.hkex_data, how='inner')

        if 'Afternoon_Close' in merged.columns:
            # 计算市场收益率
            merged['market_return'] = merged['Afternoon_Close'].pct_change()

            # 计算相关系数
            indicators = ['composite_score', 'property_index', 'visitor_index',
                         'liquidity_index']

            available_indicators = [ind for ind in indicators if ind in merged.columns]

            correlations = {}
            for indicator in available_indicators:
                try:
                    corr = merged[indicator].corr(merged['market_return'])
                    correlations[indicator] = corr
                    print(f"  {indicator}: {corr:.4f}")
                except Exception as e:
                    print(f"  {indicator}: 计算失败 - {e}")

            self.correlation_results['macro_level'] = correlations

    def _interest_rate_correlation(self):
        """利率层面相关性分析"""

        if self.data_loader.hibor_data is None or self.data_loader.hkex_data is None:
            print("  × 数据不完整")
            return

        # 合并数据
        merged = self.data_loader.hibor_data.join(self.data_loader.hkex_data, how='inner')

        if 'Afternoon_Close' in merged.columns:
            # 计算市场波动率
            merged['market_volatility'] = merged['Afternoon_Close'].pct_change().rolling(20).std()

            # 计算HIBOR期限利差
            if 'hibor_12m' in merged.columns and 'hibor_overnight' in merged.columns:
                merged['term_spread'] = merged['hibor_12m'] - merged['hibor_overnight']

                # 相关性
                corr = merged['term_spread'].corr(merged['market_volatility'])
                print(f"  期限利差 vs 市场波动率: {corr:.4f}")

                self.correlation_results['interest_rate'] = {
                    'term_spread_volatility': corr
                }

    def _liquidity_correlation(self):
        """流动性层面相关性分析"""

        if self.data_loader.hkex_data is None:
            print("  × 市场数据不完整")
            return

        # 使用交易量作为流动性代理指标
        merged = self.data_loader.hkex_data.copy()

        if 'Trading_Volume' in merged.columns and 'Afternoon_Close' in merged.columns:
            merged['volume_change'] = merged['Trading_Volume'].pct_change()
            merged['price_change'] = merged['Afternoon_Close'].pct_change()

            corr = merged['volume_change'].corr(merged['price_change'])
            print(f"  成交量变化 vs 价格变化: {corr:.4f}")

            self.correlation_results['liquidity'] = {
                'volume_price': corr
            }

    def _lagged_correlation_analysis(self):
        """滞后相关性分析"""

        if self.composite_score is None or self.data_loader.hkex_data is None:
            print("  × 数据不完整")
            return

        # 合并数据
        merged = self.composite_score.join(self.data_loader.hkex_data, how='inner')

        if 'composite_score' not in merged.columns or 'Afternoon_Close' not in merged.columns:
            print("  × 关键列缺失")
            return

        # 计算市场收益率
        merged['market_return'] = merged['Afternoon_Close'].pct_change()

        # 计算0-10天的滞后相关性
        lagged_corrs = {}
        for lag in range(0, 11):
            try:
                corr = merged['composite_score'].shift(lag).corr(merged['market_return'])
                lagged_corrs[f'lag_{lag}'] = corr
                print(f"  滞后{lag}天: {corr:.4f}")
            except Exception as e:
                print(f"  滞后{lag}天: 计算失败")

        self.correlation_results['lagged'] = lagged_corrs

        # 保存滞后相关性数据
        lagged_df = pd.DataFrame.from_dict(lagged_corrs, orient='index', columns=['correlation'])
        output_file = self.output_dir / f"lagged_correlations_{self.timestamp}.csv"
        lagged_df.to_csv(output_file)
        print(f"\n✓ 滞后相关性已保存: {output_file}")

    def step4_sector_rotation(self):
        """Step 4: 板块轮动分析"""
        print("\n" + "=" * 100)
        print("STEP 4: 板块轮动分析")
        print("=" * 100)

        if not hasattr(self.indicator_builder, 'sub_indicators'):
            print("× 子指标不可用，跳过板块轮动分析")
            return

        # 使用子指标进行板块评分
        sector_strategy = SectorRotationStrategy(
            self.indicator_builder.sub_indicators,
            self.data_loader.hkex_data
        )

        sector_scores = sector_strategy.calculate_sector_scores()

        print("\n板块评分:")
        for col in sector_scores.columns:
            if col.endswith('_score'):
                avg_score = sector_scores[col].mean()
                print(f"  {col}: {avg_score:.2f}")

        # 保存板块评分
        output_file = self.output_dir / f"sector_scores_{self.timestamp}.csv"
        sector_scores.to_csv(output_file)
        print(f"\n✓ 板块评分已保存: {output_file}")

    def step5_risk_management(self):
        """Step 5: 风险管理框架"""
        print("\n" + "=" * 100)
        print("STEP 5: 风险管理框架")
        print("=" * 100)

        if self.data_loader.hkex_data is None:
            print("× 市场数据不可用")
            return

        market_data = self.data_loader.hkex_data

        if 'Afternoon_Close' in market_data.columns:
            # 计算收益率
            returns = market_data['Afternoon_Close'].pct_change().dropna()

            # 计算VaR (95%置信度)
            var_95 = np.percentile(returns, 5) * 100
            print(f"\nVaR (95%置信度): {var_95:.2f}%")

            # 计算CVaR (条件风险价值)
            cvar_95 = returns[returns <= np.percentile(returns, 5)].mean() * 100
            print(f"CVaR (95%置信度): {cvar_95:.2f}%")

            # 计算波动率
            volatility = returns.std() * np.sqrt(252) * 100
            print(f"年化波动率: {volatility:.2f}%")

            # 保存风险指标
            risk_metrics = pd.DataFrame({
                'metric': ['VaR_95', 'CVaR_95', 'Volatility_Annual'],
                'value': [var_95, cvar_95, volatility]
            })

            output_file = self.output_dir / f"risk_metrics_{self.timestamp}.csv"
            risk_metrics.to_csv(output_file, index=False)
            print(f"\n✓ 风险指标已保存: {output_file}")

    def step6_strategy_backtest(self):
        """Step 6: 交易策略回测"""
        print("\n" + "=" * 100)
        print("STEP 6: 5个交易策略回测")
        print("=" * 100)

        if self.composite_score is None or self.data_loader.hkex_data is None:
            print("× 数据不完整，跳过策略回测")
            return

        strategies = []

        # 策略A: 景气循环交易
        print("\n[策略A] 景气循环交易策略...")
        try:
            strategy_a = BusinessCycleTradingStrategy(
                self.composite_score,
                self.data_loader.hkex_data
            )
            result_a = strategy_a.backtest()
            strategies.append(('景气循环', result_a))
            self._print_strategy_performance('景气循环', result_a)
        except Exception as e:
            print(f"  × 策略A执行失败: {e}")

        # 策略B: 利率-流动性套利
        print("\n[策略B] 利率-流动性套利策略...")
        try:
            strategy_b = InterestRateLiquidityStrategy(
                self.data_loader.hibor_data,
                self.data_loader.hkex_data
            )
            result_b = strategy_b.backtest()
            strategies.append(('利率套利', result_b))
            self._print_strategy_performance('利率套利', result_b)
        except Exception as e:
            print(f"  × 策略B执行失败: {e}")

        # 策略C: 板块轮动
        print("\n[策略C] 板块轮动策略...")
        try:
            if hasattr(self.indicator_builder, 'sub_indicators'):
                strategy_c = SectorRotationStrategy(
                    self.indicator_builder.sub_indicators,
                    self.data_loader.hkex_data
                )
                result_c = strategy_c.backtest()
                strategies.append(('板块轮动', result_c))
                self._print_strategy_performance('板块轮动', result_c)
        except Exception as e:
            print(f"  × 策略C执行失败: {e}")

        # 策略D: 访客-消费景气
        print("\n[策略D] 访客-消费景气策略...")
        try:
            strategy_d = VisitorConsumptionStrategy(
                self.data_loader.visitor_data,
                self.data_loader.hkex_data
            )
            result_d = strategy_d.backtest()
            strategies.append(('访客消费', result_d))
            self._print_strategy_performance('访客消费', result_d)
        except Exception as e:
            print(f"  × 策略D执行失败: {e}")

        # 策略E: 综合评分交易
        print("\n[策略E] 综合评分交易策略...")
        try:
            strategy_e = CompositeScoreTradingStrategy(
                self.composite_score,
                self.data_loader.hkex_data
            )
            result_e = strategy_e.backtest()
            strategies.append(('综合评分', result_e))
            self._print_strategy_performance('综合评分', result_e)
        except Exception as e:
            print(f"  × 策略E执行失败: {e}")

        # 保存策略结果
        self.strategy_results = dict(strategies)
        self._save_strategy_comparison()

    def _print_strategy_performance(self, name: str, result: dict):
        """打印策略性能"""
        if 'error' in result:
            print(f"  × 错误: {result['error']}")
            return

        print(f"  总收益率: {result.get('total_return', 0):.2f}%")
        print(f"  Sharpe比率: {result.get('sharpe_ratio', 0):.4f}")
        print(f"  最大回撤: {result.get('max_drawdown', 0):.2f}%")

    def _save_strategy_comparison(self):
        """保存策略对比"""

        comparison = []
        for name, result in self.strategy_results.items():
            if 'error' not in result:
                comparison.append({
                    'strategy': name,
                    'total_return': result.get('total_return', 0),
                    'sharpe_ratio': result.get('sharpe_ratio', 0),
                    'max_drawdown': result.get('max_drawdown', 0),
                    'win_rate': result.get('win_rate', 0)
                })

        if comparison:
            df = pd.DataFrame(comparison)
            output_file = self.output_dir / f"strategy_comparison_{self.timestamp}.csv"
            df.to_csv(output_file, index=False)
            print(f"\n✓ 策略对比已保存: {output_file}")

    def step7_visualization(self):
        """Step 7: 可视化"""
        print("\n" + "=" * 100)
        print("STEP 7: 生成可视化图表")
        print("=" * 100)

        # 图1: 综合景气指标时间序列
        self._plot_composite_indicator()

        # 图2: 相关性热力图
        self._plot_correlation_heatmap()

        # 图3: 策略对比图
        self._plot_strategy_comparison()

        # 图4: 滞后相关性图
        self._plot_lagged_correlation()

        print("\n✓ 所有图表已生成")

    def _plot_composite_indicator(self):
        """绘制综合景气指标"""
        if self.composite_score is None:
            return

        fig, axes = plt.subplots(2, 1, figsize=(15, 10))

        # 子图1: 综合评分
        if 'composite_score' in self.composite_score.columns:
            axes[0].plot(self.composite_score.index,
                        self.composite_score['composite_score'],
                        label='综合景气评分', linewidth=2)
            axes[0].set_title('宏观经济景气综合指标', fontsize=14, fontweight='bold')
            axes[0].set_ylabel('评分 (0-100)', fontsize=12)
            axes[0].legend(fontsize=10)
            axes[0].grid(True, alpha=0.3)

        # 子图2: 各子指标
        sub_indicators = [col for col in self.composite_score.columns if col.endswith('_index')]
        for col in sub_indicators:
            axes[1].plot(self.composite_score.index,
                        self.composite_score[col],
                        label=col.replace('_index', ''),
                        alpha=0.7)

        axes[1].set_title('各子指标时间序列', fontsize=14, fontweight='bold')
        axes[1].set_ylabel('指数值', fontsize=12)
        axes[1].set_xlabel('日期', fontsize=12)
        axes[1].legend(fontsize=9, loc='best')
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        output_file = self.output_dir / f"composite_indicator_{self.timestamp}.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  ✓ 综合指标图: {output_file.name}")

    def _plot_correlation_heatmap(self):
        """绘制相关性热力图"""
        if not self.correlation_results:
            return

        # 合并所有相关性结果
        all_corrs = {}
        for level, corrs in self.correlation_results.items():
            for key, value in corrs.items():
                all_corrs[f"{level}_{key}"] = value

        if not all_corrs:
            return

        # 创建热力图
        fig, ax = plt.subplots(figsize=(12, 8))

        # 转换为DataFrame
        df = pd.DataFrame.from_dict(all_corrs, orient='index', columns=['correlation'])

        # 绘制条形图
        df.sort_values('correlation', ascending=True).plot(
            kind='barh', ax=ax, legend=False, color='steelblue'
        )

        ax.set_title('多层级相关性分析结果', fontsize=14, fontweight='bold')
        ax.set_xlabel('相关系数', fontsize=12)
        ax.axvline(x=0, color='red', linestyle='--', alpha=0.5)
        ax.grid(True, alpha=0.3, axis='x')

        plt.tight_layout()
        output_file = self.output_dir / f"correlation_heatmap_{self.timestamp}.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  ✓ 相关性热力图: {output_file.name}")

    def _plot_strategy_comparison(self):
        """绘制策略对比图"""
        if not self.strategy_results:
            return

        # 提取策略性能
        strategies = []
        returns = []
        sharpes = []
        drawdowns = []

        for name, result in self.strategy_results.items():
            if 'error' not in result:
                strategies.append(name)
                returns.append(result.get('total_return', 0))
                sharpes.append(result.get('sharpe_ratio', 0))
                drawdowns.append(result.get('max_drawdown', 0))

        if not strategies:
            return

        # 创建对比图
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))

        # 子图1: 总收益率
        axes[0].bar(strategies, returns, color='green', alpha=0.7)
        axes[0].set_title('总收益率对比', fontsize=12, fontweight='bold')
        axes[0].set_ylabel('收益率 (%)', fontsize=10)
        axes[0].tick_params(axis='x', rotation=45)
        axes[0].grid(True, alpha=0.3, axis='y')

        # 子图2: Sharpe比率
        axes[1].bar(strategies, sharpes, color='blue', alpha=0.7)
        axes[1].set_title('Sharpe比率对比', fontsize=12, fontweight='bold')
        axes[1].set_ylabel('Sharpe比率', fontsize=10)
        axes[1].tick_params(axis='x', rotation=45)
        axes[1].grid(True, alpha=0.3, axis='y')

        # 子图3: 最大回撤
        axes[2].bar(strategies, drawdowns, color='red', alpha=0.7)
        axes[2].set_title('最大回撤对比', fontsize=12, fontweight='bold')
        axes[2].set_ylabel('最大回撤 (%)', fontsize=10)
        axes[2].tick_params(axis='x', rotation=45)
        axes[2].grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        output_file = self.output_dir / f"strategy_comparison_{self.timestamp}.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  ✓ 策略对比图: {output_file.name}")

    def _plot_lagged_correlation(self):
        """绘制滞后相关性图"""
        if 'lagged' not in self.correlation_results:
            return

        lagged_corrs = self.correlation_results['lagged']

        lags = [int(k.split('_')[1]) for k in lagged_corrs.keys()]
        corrs = list(lagged_corrs.values())

        fig, ax = plt.subplots(figsize=(12, 6))

        ax.plot(lags, corrs, marker='o', linewidth=2, markersize=8)
        ax.set_title('滞后相关性分析 (0-10天)', fontsize=14, fontweight='bold')
        ax.set_xlabel('滞后天数', fontsize=12)
        ax.set_ylabel('相关系数', fontsize=12)
        ax.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        output_file = self.output_dir / f"lagged_correlation_{self.timestamp}.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  ✓ 滞后相关性图: {output_file.name}")

    def step8_generate_reports(self):
        """Step 8: 生成报告"""
        print("\n" + "=" * 100)
        print("STEP 8: 生成分析报告")
        print("=" * 100)

        # 生成主报告
        self._generate_main_report()

        # 生成宏观指标使用指南
        self._generate_indicator_guide()

        # 生成交易策略手册
        self._generate_strategy_playbook()

        print("\n✓ 所有报告已生成")

    def _generate_main_report(self):
        """生成主报告"""
        report = []
        report.append("=" * 100)
        report.append("完整宏观量化分析报告")
        report.append("=" * 100)
        report.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"\n分析期间: 2024-10-23 至 2025-10-24")

        report.append("\n\n" + "=" * 100)
        report.append("第一部分: 数据概览")
        report.append("=" * 100)

        report.append("\n成功加载的数据源:")
        for key, value in self.raw_data.items():
            status = "✓" if value and value.get('status') == 'success' else "×"
            report.append(f"  {status} {key.upper()}")

        report.append("\n\n" + "=" * 100)
        report.append("第二部分: 宏观景气指标")
        report.append("=" * 100)

        if self.composite_score is not None:
            report.append(f"\n综合景气评分:")
            report.append(f"  当前值: {self.composite_score['composite_score'].iloc[-1]:.2f}")
            report.append(f"  平均值: {self.composite_score['composite_score'].mean():.2f}")
            report.append(f"  最高值: {self.composite_score['composite_score'].max():.2f}")
            report.append(f"  最低值: {self.composite_score['composite_score'].min():.2f}")

        report.append("\n\n" + "=" * 100)
        report.append("第三部分: 相关性分析")
        report.append("=" * 100)

        for level, corrs in self.correlation_results.items():
            report.append(f"\n{level}:")
            for key, value in corrs.items():
                report.append(f"  {key}: {value:.4f}")

        report.append("\n\n" + "=" * 100)
        report.append("第四部分: 交易策略性能")
        report.append("=" * 100)

        for name, result in self.strategy_results.items():
            if 'error' not in result:
                report.append(f"\n{name}:")
                report.append(f"  总收益率: {result.get('total_return', 0):.2f}%")
                report.append(f"  Sharpe比率: {result.get('sharpe_ratio', 0):.4f}")
                report.append(f"  最大回撤: {result.get('max_drawdown', 0):.2f}%")

        report.append("\n\n" + "=" * 100)
        report.append("报告结束")
        report.append("=" * 100)

        # 保存报告
        report_text = "\n".join(report)
        output_file = self.output_dir / f"COMPLETE_MACRO_ANALYSIS_REPORT_{self.timestamp}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_text)

        print(f"  ✓ 主报告: {output_file.name}")

    def _generate_indicator_guide(self):
        """生成宏观指标使用指南"""
        guide = []
        guide.append("=" * 100)
        guide.append("宏观指标使用指南")
        guide.append("=" * 100)

        guide.append("\n\n## 1. 综合景气指标")
        guide.append("\n定义: 整合5个子指标的加权综合评分")
        guide.append("权重分配:")
        guide.append("  - 房地产周期指数: 40%")
        guide.append("  - 访客增长率: 20%")
        guide.append("  - 贸易指数: 15%")
        guide.append("  - 金融流动性指数: 15%")
        guide.append("  - 运输指数: 10%")

        guide.append("\n使用方法:")
        guide.append("  - 评分 > 70: 强劲经济，考虑增加股票敞口")
        guide.append("  - 评分 50-70: 中性，维持平衡配置")
        guide.append("  - 评分 < 50: 疲弱经济，考虑防守配置")

        # 保存指南
        guide_text = "\n".join(guide)
        output_file = self.output_dir / f"MACRO_INDICATORS_GUIDE_{self.timestamp}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(guide_text)

        print(f"  ✓ 指标指南: {output_file.name}")

    def _generate_strategy_playbook(self):
        """生成交易策略手册"""
        playbook = []
        playbook.append("=" * 100)
        playbook.append("交易策略实施手册")
        playbook.append("=" * 100)

        playbook.append("\n\n## 策略A: 景气循环交易")
        playbook.append("\n入场条件:")
        playbook.append("  1. 综合景气评分上穿20日均线")
        playbook.append("  2. 景气动量为正")
        playbook.append("\n出场条件:")
        playbook.append("  1. 综合景气评分下穿20日均线")
        playbook.append("  2. 检测到周期顶部信号")

        playbook.append("\n\n## 策略B: 利率-流动性套利")
        playbook.append("\n入场条件:")
        playbook.append("  1. HIBOR期限利差收窄")
        playbook.append("  2. 利率波动率低于中位数")
        playbook.append("\n出场条件:")
        playbook.append("  1. 期限利差扩大")
        playbook.append("  2. 利率波动率上升")

        # 保存手册
        playbook_text = "\n".join(playbook)
        output_file = self.output_dir / f"TRADING_STRATEGY_PLAYBOOK_{self.timestamp}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(playbook_text)

        print(f"  ✓ 策略手册: {output_file.name}")

    def _save_data_summary(self):
        """保存数据摘要"""
        summary = []
        summary.append("数据加载摘要\n")
        summary.append("=" * 60)

        for key, value in self.raw_data.items():
            summary.append(f"\n{key.upper()}:")
            if value and value.get('status') == 'success':
                summary.append("  状态: 成功")
                if 'date_range' in value:
                    date_range = value['date_range']
                    summary.append(f"  日期范围: {date_range[0]} 至 {date_range[1]}")
            else:
                summary.append("  状态: 失败或数据不完整")

        summary_text = "\n".join(summary)
        output_file = self.output_dir / f"data_summary_{self.timestamp}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(summary_text)

    def _save_correlation_results(self):
        """保存相关性结果"""
        if not self.correlation_results:
            return

        # 转换为DataFrame
        all_corrs = []
        for level, corrs in self.correlation_results.items():
            for key, value in corrs.items():
                all_corrs.append({
                    'level': level,
                    'indicator': key,
                    'correlation': value
                })

        df = pd.DataFrame(all_corrs)
        output_file = self.output_dir / f"all_correlations_{self.timestamp}.csv"
        df.to_csv(output_file, index=False)
        print(f"\n✓ 所有相关性结果已保存: {output_file}")


# ============================================================================
# 主执行函数
# ============================================================================

def main():
    """主执行函数"""

    print("\n" + "=" * 100)
    print("完整宏观量化分析系统")
    print("开始时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 100)

    # 创建分析引擎
    engine = CompleteMacroAnalysisEngine(base_dir=".")

    # 运行完整分析
    engine.run_complete_analysis()

    print("\n" + "=" * 100)
    print("分析完成!")
    print("结束时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 100)


if __name__ == "__main__":
    main()
