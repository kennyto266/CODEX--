# -*- coding: utf-8 -*-
"""
================================================================================
宏观驱动交易策略模块 - 5个完整策略实现
================================================================================
包含策略:
1. 景气循环交易策略 - 基于综合景气指标
2. 利率-流动性套利策略 - HIBOR期限结构
3. 板块轮动策略 - 多宏观指标驱动
4. 访客-消费景气策略 - 旅游零售板块
5. 综合评分交易策略 - 全指标整合

作者: CODEX Quantitative System
日期: 2025-10-24
================================================================================
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


# ============================================================================
# 策略A: 景气循环交易策略
# ============================================================================

class BusinessCycleTradingStrategy:
    """
    景气循环交易策略

    逻辑:
    - 景气指数上升 → 增加仓位
    - 景气指数下降 → 减少仓位
    - 识别周期顶部和底部
    """

    def __init__(self, composite_score: pd.DataFrame, market_data: pd.DataFrame):
        self.composite_score = composite_score
        self.market_data = market_data
        self.signals = None
        self.positions = None

    def generate_signals(self) -> pd.DataFrame:
        """生成交易信号"""

        df = self.composite_score.copy()

        # 计算景气指数的移动平均
        df['score_ma_short'] = df['composite_score'].rolling(window=5).mean()
        df['score_ma_long'] = df['composite_score'].rolling(window=20).mean()

        # 计算动量
        df['score_momentum'] = df['composite_score'].pct_change(periods=5)

        # 生成信号
        df['signal'] = 0

        # 条件1: 短期MA上穿长期MA，且动量为正
        df.loc[(df['score_ma_short'] > df['score_ma_long']) &
               (df['score_momentum'] > 0), 'signal'] = 1

        # 条件2: 短期MA下穿长期MA，或动量为负
        df.loc[(df['score_ma_short'] < df['score_ma_long']) |
               (df['score_momentum'] < 0), 'signal'] = -1

        # 识别周期顶部和底部
        df['cycle_top'] = (df['composite_score'] > df['composite_score'].quantile(0.8)) & \
                         (df['score_momentum'] < 0)

        df['cycle_bottom'] = (df['composite_score'] < df['composite_score'].quantile(0.2)) & \
                            (df['score_momentum'] > 0)

        # 在顶部卖出，底部买入
        df.loc[df['cycle_top'], 'signal'] = -1
        df.loc[df['cycle_bottom'], 'signal'] = 1

        self.signals = df

        return df

    def calculate_positions(self, initial_capital: float = 1000000) -> pd.DataFrame:
        """计算持仓"""

        if self.signals is None:
            self.generate_signals()

        df = self.signals.copy()

        # 根据信号调整仓位
        df['position'] = df['signal'].rolling(window=3).mean()  # 平滑信号

        # 仓位范围: 0% - 100%
        df['position'] = df['position'].clip(-1, 1)
        df['position'] = (df['position'] + 1) / 2  # 转换到0-1

        self.positions = df

        return df

    def backtest(self, initial_capital: float = 1000000) -> Dict:
        """回测策略"""

        if self.positions is None:
            self.calculate_positions(initial_capital)

        # 合并市场数据
        backtest_df = self.positions.join(self.market_data, how='inner')

        # 计算收益
        if 'Afternoon_Close' in backtest_df.columns:
            backtest_df['market_return'] = backtest_df['Afternoon_Close'].pct_change()
            backtest_df['strategy_return'] = backtest_df['position'].shift(1) * backtest_df['market_return']

            # 累计收益
            backtest_df['cumulative_market'] = (1 + backtest_df['market_return']).cumprod()
            backtest_df['cumulative_strategy'] = (1 + backtest_df['strategy_return']).cumprod()

            # 计算性能指标
            total_return = (backtest_df['cumulative_strategy'].iloc[-1] - 1) * 100
            sharpe_ratio = self._calculate_sharpe(backtest_df['strategy_return'])
            max_drawdown = self._calculate_max_drawdown(backtest_df['cumulative_strategy'])

            results = {
                'total_return': total_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'backtest_df': backtest_df
            }

            return results

        else:
            return {'error': 'Market data not available'}

    def _calculate_sharpe(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """计算Sharpe比率"""
        returns = returns.dropna()
        if len(returns) == 0:
            return 0.0

        excess_returns = returns - risk_free_rate / 252
        if excess_returns.std() == 0:
            return 0.0

        return np.sqrt(252) * excess_returns.mean() / excess_returns.std()

    def _calculate_max_drawdown(self, cumulative_returns: pd.Series) -> float:
        """计算最大回撤"""
        cumulative_returns = cumulative_returns.dropna()
        if len(cumulative_returns) == 0:
            return 0.0

        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        return abs(drawdown.min()) * 100


# ============================================================================
# 策略B: 利率-流动性套利策略
# ============================================================================

class InterestRateLiquidityStrategy:
    """
    利率-流动性套利策略

    逻辑:
    - HIBOR期限结构陡峭 (长端-短端利差大) → 防守配置
    - HIBOR期限结构平坦 (利差小) → 进攻配置
    - 结合银行信贷数据判断流动性
    """

    def __init__(self, hibor_data: pd.DataFrame, market_data: pd.DataFrame):
        self.hibor_data = hibor_data
        self.market_data = market_data
        self.signals = None

    def generate_signals(self) -> pd.DataFrame:
        """生成交易信号"""

        df = self.hibor_data.copy()

        # 计算期限利差
        if 'hibor_12m' in df.columns and 'hibor_overnight' in df.columns:
            df['term_spread'] = df['hibor_12m'] - df['hibor_overnight']

        if 'hibor_6m' in df.columns and 'hibor_1m' in df.columns:
            df['mid_spread'] = df['hibor_6m'] - df['hibor_1m']

        # 计算利率波动率
        df['hibor_volatility'] = df[['hibor_overnight', 'hibor_1m', 'hibor_3m']].std(axis=1)

        # 生成信号
        df['signal'] = 0

        # 条件1: 期限利差收窄 → 进攻 (买入)
        if 'term_spread' in df.columns:
            spread_mean = df['term_spread'].mean()
            df.loc[df['term_spread'] < spread_mean, 'signal'] = 1
            df.loc[df['term_spread'] > spread_mean, 'signal'] = -1

        # 条件2: 利率波动率低 → 增加仓位
        vol_threshold = df['hibor_volatility'].quantile(0.5)
        df.loc[df['hibor_volatility'] < vol_threshold, 'signal'] += 0.5

        self.signals = df

        return df

    def backtest(self, initial_capital: float = 1000000) -> Dict:
        """回测策略"""

        if self.signals is None:
            self.generate_signals()

        # 合并市场数据
        backtest_df = self.signals.join(self.market_data, how='inner')

        # 计算仓位
        backtest_df['position'] = backtest_df['signal'].rolling(window=5).mean().clip(-1, 1)
        backtest_df['position'] = (backtest_df['position'] + 1) / 2

        # 计算收益
        if 'Afternoon_Close' in backtest_df.columns:
            backtest_df['market_return'] = backtest_df['Afternoon_Close'].pct_change()
            backtest_df['strategy_return'] = backtest_df['position'].shift(1) * backtest_df['market_return']

            # 累计收益
            backtest_df['cumulative_strategy'] = (1 + backtest_df['strategy_return']).cumprod()

            # 性能指标
            total_return = (backtest_df['cumulative_strategy'].iloc[-1] - 1) * 100
            sharpe_ratio = self._calculate_sharpe(backtest_df['strategy_return'])
            max_drawdown = self._calculate_max_drawdown(backtest_df['cumulative_strategy'])

            return {
                'total_return': total_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'backtest_df': backtest_df
            }

        return {'error': 'Market data not available'}

    def _calculate_sharpe(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """计算Sharpe比率"""
        returns = returns.dropna()
        if len(returns) == 0:
            return 0.0

        excess_returns = returns - risk_free_rate / 252
        if excess_returns.std() == 0:
            return 0.0

        return np.sqrt(252) * excess_returns.mean() / excess_returns.std()

    def _calculate_max_drawdown(self, cumulative_returns: pd.Series) -> float:
        """计算最大回撤"""
        cumulative_returns = cumulative_returns.dropna()
        if len(cumulative_returns) == 0:
            return 0.0

        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        return abs(drawdown.min()) * 100


# ============================================================================
# 策略C: 板块轮动策略
# ============================================================================

class SectorRotationStrategy:
    """
    板块轮动策略

    逻辑:
    - 房地产周期上升 → 地产股
    - 访客增长加速 → 零售/酒店股
    - 贸易额上升 → 出口导向股
    - 利率下降 → 成长股
    - 信贷宽松 → 金融股
    """

    def __init__(self, macro_indicators: Dict, market_data: pd.DataFrame):
        self.macro_indicators = macro_indicators
        self.market_data = market_data
        self.sector_scores = None

    def calculate_sector_scores(self) -> pd.DataFrame:
        """计算各板块评分"""

        # 创建板块评分DataFrame
        scores = pd.DataFrame()

        # 地产板块评分
        if 'property' in self.macro_indicators:
            property_idx = self.macro_indicators['property']
            scores['real_estate_score'] = property_idx

        # 零售/酒店板块评分
        if 'visitor' in self.macro_indicators:
            visitor_idx = self.macro_indicators['visitor']
            scores['retail_hospitality_score'] = visitor_idx

        # 出口板块评分
        if 'trade' in self.macro_indicators:
            trade_idx = self.macro_indicators['trade']
            scores['export_score'] = trade_idx

        # 成长股评分 (利率反向指标)
        if 'liquidity' in self.macro_indicators:
            liquidity_idx = self.macro_indicators['liquidity']
            scores['growth_score'] = liquidity_idx

        # 金融板块评分
        if 'liquidity' in self.macro_indicators:
            liquidity_idx = self.macro_indicators['liquidity']
            scores['financial_score'] = liquidity_idx * 0.8

        self.sector_scores = scores

        return scores

    def generate_rotation_signals(self) -> pd.DataFrame:
        """生成板块轮动信号"""

        if self.sector_scores is None:
            self.calculate_sector_scores()

        df = self.sector_scores.copy()

        # 找到每个时期得分最高的板块
        df['best_sector'] = df.idxmax(axis=1)

        # 计算板块动量
        for col in df.columns:
            if col.endswith('_score'):
                df[f'{col}_momentum'] = df[col].pct_change(periods=5)

        # 生成轮动信号
        df['rotation_signal'] = 0

        # 如果最佳板块在改变，发出轮动信号
        df['sector_changed'] = df['best_sector'] != df['best_sector'].shift(1)
        df.loc[df['sector_changed'], 'rotation_signal'] = 1

        return df

    def backtest(self, initial_capital: float = 1000000) -> Dict:
        """回测板块轮动策略"""

        rotation_df = self.generate_rotation_signals()

        # 合并市场数据
        backtest_df = rotation_df.join(self.market_data, how='inner')

        # 简化逻辑: 持有得分最高板块对应的市场
        # 实际应该有不同板块的ETF或指数
        backtest_df['position'] = 1.0  # 满仓持有最佳板块

        # 计算收益
        if 'Afternoon_Close' in backtest_df.columns:
            backtest_df['market_return'] = backtest_df['Afternoon_Close'].pct_change()
            backtest_df['strategy_return'] = backtest_df['position'] * backtest_df['market_return']

            # 累计收益
            backtest_df['cumulative_strategy'] = (1 + backtest_df['strategy_return']).cumprod()

            # 性能指标
            total_return = (backtest_df['cumulative_strategy'].iloc[-1] - 1) * 100
            sharpe_ratio = self._calculate_sharpe(backtest_df['strategy_return'])

            return {
                'total_return': total_return,
                'sharpe_ratio': sharpe_ratio,
                'backtest_df': backtest_df
            }

        return {'error': 'Market data not available'}

    def _calculate_sharpe(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """计算Sharpe比率"""
        returns = returns.dropna()
        if len(returns) == 0:
            return 0.0

        excess_returns = returns - risk_free_rate / 252
        if excess_returns.std() == 0:
            return 0.0

        return np.sqrt(252) * excess_returns.mean() / excess_returns.std()


# ============================================================================
# 策略D: 访客-消费景气策略
# ============================================================================

class VisitorConsumptionStrategy:
    """
    访客-消费景气策略

    逻辑:
    - 访客增长率加速 → 买入零售/酒店板块
    - 内地访客占比上升 → 增加仓位
    - 访客增长率下降 → 减仓
    """

    def __init__(self, visitor_data: pd.DataFrame, market_data: pd.DataFrame):
        self.visitor_data = visitor_data
        self.market_data = market_data
        self.signals = None

    def generate_signals(self) -> pd.DataFrame:
        """生成交易信号"""

        df = self.visitor_data.copy()

        # 计算访客增长率
        if 'visitor_arrivals_total' in df.columns:
            df['visitor_growth'] = df['visitor_arrivals_total'].pct_change() * 100

        # 计算内地访客占比
        if 'visitor_arrivals_mainland' in df.columns and 'visitor_arrivals_total' in df.columns:
            df['mainland_ratio'] = (df['visitor_arrivals_mainland'] / df['visitor_arrivals_total']) * 100

        # 生成信号
        df['signal'] = 0

        # 条件1: 访客增长率为正且加速
        if 'visitor_arrivals_growth' in df.columns:
            df['growth_acceleration'] = df['visitor_arrivals_growth'].diff()
            df.loc[(df['visitor_arrivals_growth'] > 0) &
                   (df['growth_acceleration'] > 0), 'signal'] = 1

        # 条件2: 内地访客占比上升
        if 'mainland_ratio' in df.columns:
            df['mainland_ratio_change'] = df['mainland_ratio'].diff()
            df.loc[df['mainland_ratio_change'] > 0, 'signal'] += 0.5

        self.signals = df

        return df

    def backtest(self, initial_capital: float = 1000000) -> Dict:
        """回测策略"""

        if self.signals is None:
            self.generate_signals()

        # 重采样到日度频率以匹配市场数据
        daily_signals = self.signals.resample('D').ffill()

        # 合并市场数据
        backtest_df = daily_signals.join(self.market_data, how='inner')

        # 计算仓位
        backtest_df['position'] = backtest_df['signal'].clip(0, 1)

        # 计算收益
        if 'Afternoon_Close' in backtest_df.columns:
            backtest_df['market_return'] = backtest_df['Afternoon_Close'].pct_change()
            backtest_df['strategy_return'] = backtest_df['position'].shift(1) * backtest_df['market_return']

            # 累计收益
            backtest_df['cumulative_strategy'] = (1 + backtest_df['strategy_return']).cumprod()

            # 性能指标
            total_return = (backtest_df['cumulative_strategy'].iloc[-1] - 1) * 100
            sharpe_ratio = self._calculate_sharpe(backtest_df['strategy_return'])

            return {
                'total_return': total_return,
                'sharpe_ratio': sharpe_ratio,
                'backtest_df': backtest_df
            }

        return {'error': 'Market data not available'}

    def _calculate_sharpe(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """计算Sharpe比率"""
        returns = returns.dropna()
        if len(returns) == 0:
            return 0.0

        excess_returns = returns - risk_free_rate / 252
        if excess_returns.std() == 0:
            return 0.0

        return np.sqrt(252) * excess_returns.mean() / excess_returns.std()

    def _calculate_max_drawdown(self, cumulative_returns: pd.Series) -> float:
        """计算最大回撤"""
        cumulative_returns = cumulative_returns.dropna()
        if len(cumulative_returns) == 0:
            return 0.0

        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        return abs(drawdown.min()) * 100


# ============================================================================
# 策略E: 综合评分交易策略
# ============================================================================

class CompositeScoreTradingStrategy:
    """
    综合评分交易策略

    逻辑:
    - 综合所有宏观指标的评分
    - 评分上升 → 增加敞口
    - 评分下降 → 减少敞口
    - 动态调整仓位
    """

    def __init__(self, composite_score: pd.DataFrame, market_data: pd.DataFrame):
        self.composite_score = composite_score
        self.market_data = market_data
        self.signals = None

    def generate_signals(self) -> pd.DataFrame:
        """生成交易信号"""

        df = self.composite_score.copy()

        # 计算评分动量
        df['score_momentum_5d'] = df['composite_score'].pct_change(periods=5)
        df['score_momentum_20d'] = df['composite_score'].pct_change(periods=20)

        # 计算评分相对位置
        df['score_percentile'] = df['composite_score'].rolling(window=60).apply(
            lambda x: stats.percentileofscore(x, x.iloc[-1]) if len(x) > 0 else 50
        )

        # 生成仓位信号 (0-1)
        df['position_signal'] = 0.5  # 基础仓位50%

        # 根据评分百分位调整
        df.loc[df['score_percentile'] > 80, 'position_signal'] = 1.0  # 高评分 → 满仓
        df.loc[df['score_percentile'] < 20, 'position_signal'] = 0.2  # 低评分 → 轻仓

        # 根据动量微调
        df.loc[df['score_momentum_5d'] > 0.05, 'position_signal'] *= 1.1
        df.loc[df['score_momentum_5d'] < -0.05, 'position_signal'] *= 0.9

        # 限制仓位范围
        df['position_signal'] = df['position_signal'].clip(0, 1)

        self.signals = df

        return df

    def backtest(self, initial_capital: float = 1000000) -> Dict:
        """回测策略"""

        if self.signals is None:
            self.generate_signals()

        # 合并市场数据
        backtest_df = self.signals.join(self.market_data, how='inner')

        # 使用position_signal作为仓位
        backtest_df['position'] = backtest_df['position_signal']

        # 计算收益
        if 'Afternoon_Close' in backtest_df.columns:
            backtest_df['market_return'] = backtest_df['Afternoon_Close'].pct_change()
            backtest_df['strategy_return'] = backtest_df['position'].shift(1) * backtest_df['market_return']

            # 累计收益
            backtest_df['cumulative_market'] = (1 + backtest_df['market_return']).cumprod()
            backtest_df['cumulative_strategy'] = (1 + backtest_df['strategy_return']).cumprod()

            # 性能指标
            total_return = (backtest_df['cumulative_strategy'].iloc[-1] - 1) * 100
            sharpe_ratio = self._calculate_sharpe(backtest_df['strategy_return'])
            max_drawdown = self._calculate_max_drawdown(backtest_df['cumulative_strategy'])

            # 计算额外指标
            win_rate = (backtest_df['strategy_return'] > 0).sum() / len(backtest_df) * 100

            return {
                'total_return': total_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'backtest_df': backtest_df
            }

        return {'error': 'Market data not available'}

    def _calculate_sharpe(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """计算Sharpe比率"""
        returns = returns.dropna()
        if len(returns) == 0:
            return 0.0

        excess_returns = returns - risk_free_rate / 252
        if excess_returns.std() == 0:
            return 0.0

        return np.sqrt(252) * excess_returns.mean() / excess_returns.std()

    def _calculate_max_drawdown(self, cumulative_returns: pd.Series) -> float:
        """计算最大回撤"""
        cumulative_returns = cumulative_returns.dropna()
        if len(cumulative_returns) == 0:
            return 0.0

        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        return abs(drawdown.min()) * 100


print("Module 2: Trading Strategies - Created")
