"""
多时间框架策略 (T179)
支持日线、周线、月线数据同步分析
实现框架间信号确认和趋势对齐

Author: Claude Code
Date: 2025-11-09
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging

try:
    from core.base_strategy import IStrategy, Signal, SignalType
    from strategy.traits import StrategyTraits
except ImportError:
    # 相对导入
    from ..core.base_strategy import IStrategy, Signal, SignalType
    from .traits import StrategyTraits

logger = logging.getLogger(__name__)


class MultiTimeframeStrategy(IStrategy):
    """
    多时间框架策略

    同时分析多个时间框架（日线、周线、月线），
    通过多时间框架确认机制生成高质量交易信号。

    核心逻辑：
    1. 高频信号（5分钟/15分钟）提供入场时机
    2. 中频信号（1小时/4小时）确认趋势方向
    3. 低频信号（1天/1周）提供长期趋势
    4. 信号同步：只有当多个时间框架一致时才生成信号

    策略特点：
    - 降低虚假信号，提高信号质量
    - 适应不同市场周期
    - 灵活的时间框架配置
    """

    def __init__(
        self,
        timeframes: List[str] = None,
        primary_timeframe: str = '1D',
        confirmation_levels: int = 2,
        trend_alignment_threshold: float = 0.6,
        min_confidence: float = 0.5
    ):
        """
        初始化多时间框架策略

        Args:
            timeframes: 时间框架列表 ['1D', '1W', '1M']
            primary_timeframe: 主要时间框架（信号生成基于此）
            confirmation_levels: 确认所需的时间框架数量
            trend_alignment_threshold: 趋势对齐阈值
            min_confidence: 最小信号置信度
        """
        self.timeframes = timeframes or ['1D', '1W', '1M']
        self.primary_timeframe = primary_timeframe
        self.confirmation_levels = confirmation_levels
        self.trend_alignment_threshold = trend_alignment_threshold
        self.min_confidence = min_confidence

        # 数据存储
        self.data_by_timeframe: Dict[str, pd.DataFrame] = {}
        self.indicators_by_timeframe: Dict[str, Dict] = {}
        self.trend_signals: Dict[str, int] = {}  # -1, 0, 1

        # 特征标记
        self.traits = StrategyTraits(
            name="多时间框架策略",
            timeframe=primary_timeframe,
            market_regime适应性=True,
            信号过滤=True,
            多时间框架分析=True
        )

    @property
    def strategy_name(self) -> str:
        return f"MultiTimeframe-{self.primary_timeframe}"

    @property
    def supported_symbols(self) -> List[str]:
        return ['0700.HK', '0388.HK', '1398.HK', '0939.HK', '3988.HK']

    def initialize(self, historical_data: pd.DataFrame, **kwargs) -> None:
        """
        初始化策略

        Args:
            historical_data: 主要时间框架的历史数据
            **kwargs: 包含其他时间框架数据的字典
        """
        try:
            # 存储主要时间框架数据
            self.data_by_timeframe[self.primary_timeframe] = historical_data.copy()

            # 存储其他时间框架数据
            for tf_name, tf_data in kwargs.get('timeframe_data', {}).items():
                if tf_name in self.timeframes:
                    self.data_by_timeframe[tf_name] = tf_data

            # 确保所有时间框架都有数据
            for tf in self.timeframes:
                if tf not in self.data_by_timeframe:
                    logger.warning(f"缺少时间框架数据: {tf}")

            # 计算各时间框架的技术指标
            self._calculate_indicators()

            logger.info(f"多时间框架策略初始化完成: {self.timeframes}")

        except Exception as e:
            logger.error(f"策略初始化失败: {e}")
            raise

    def _calculate_indicators(self) -> None:
        """计算各时间框架的技术指标"""
        for tf in self.timeframes:
            if tf not in self.data_by_timeframe:
                continue

            data = self.data_by_timeframe[tf]
            indicators = {}

            # 计算移动平均线
            indicators['sma_20'] = data['Close'].rolling(20).mean()
            indicators['sma_50'] = data['Close'].rolling(50).mean()
            indicators['ema_12'] = data['Close'].ewm(span=12).mean()
            indicators['ema_26'] = data['Close'].ewm(span=26).mean()

            # 计算MACD
            indicators['macd'] = indicators['ema_12'] - indicators['ema_26']
            indicators['macd_signal'] = indicators['macd'].ewm(span=9).mean()
            indicators['macd_histogram'] = indicators['macd'] - indicators['macd_signal']

            # 计算RSI
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss.replace(0, 1e-10)
            indicators['rsi'] = 100 - (100 / (1 + rs))

            # 计算布林带
            sma_20 = indicators['sma_20']
            std_20 = data['Close'].rolling(20).std()
            indicators['bb_upper'] = sma_20 + (std_20 * 2)
            indicators['bb_lower'] = sma_20 - (std_20 * 2)
            indicators['bb_width'] = (indicators['bb_upper'] - indicators['bb_lower']) / sma_20

            self.indicators_by_timeframe[tf] = indicators

    def _determine_trend_direction(self, tf: str) -> int:
        """
        确定单个时间框架的趋势方向

        Args:
            tf: 时间框架

        Returns:
            趋势方向: 1 (上涨), -1 (下跌), 0 (震荡)
        """
        if tf not in self.indicators_by_timeframe:
            return 0

        indicators = self.indicators_by_timeframe[tf]
        latest_idx = -1

        # 趋势判断条件
        sma_20 = indicators['sma_20'].iloc[latest_idx]
        sma_50 = indicators['sma_50'].iloc[latest_idx] if len(indicators['sma_50']) > 20 else np.nan
        macd = indicators['macd'].iloc[latest_idx]
        macd_signal = indicators['macd_signal'].iloc[latest_idx]
        rsi = indicators['rsi'].iloc[latest_idx]

        trend_score = 0

        # 移动平均线趋势
        if not np.isnan(sma_50):
            if sma_20 > sma_50:
                trend_score += 1
            else:
                trend_score -= 1

        # MACD趋势
        if macd > macd_signal:
            trend_score += 1
        else:
            trend_score -= 1

        # RSI趋势过滤
        if rsi > 50:
            trend_score += 0.5
        else:
            trend_score -= 0.5

        # 根据得分确定趋势
        if trend_score >= 1.5:
            return 1
        elif trend_score <= -1.5:
            return -1
        else:
            return 0

    def _calculate_trend_alignment(self) -> float:
        """
        计算多时间框架趋势对齐度

        Returns:
            对齐度: 0-1之间，1表示完全对齐
        """
        trend_directions = []

        for tf in self.timeframes:
            if tf in self.indicators_by_timeframe:
                direction = self._determine_trend_direction(tf)
                trend_directions.append(direction)
                self.trend_signals[tf] = direction

        if not trend_directions:
            return 0.0

        # 计算趋势一致性
        positive = sum(1 for d in trend_directions if d > 0)
        negative = sum(1 for d in trend_directions if d < 0)
        total = len(trend_directions)

        # 对齐度 = max(正对齐, 负对齐) / total
        alignment = max(positive, negative) / total
        return alignment

    def _get_signal_strength(self, tf: str) -> float:
        """
        计算单个时间框架的信号强度

        Args:
            tf: 时间框架

        Returns:
            信号强度: 0-1之间
        """
        if tf not in self.indicators_by_timeframe:
            return 0.0

        indicators = self.indicators_by_timeframe[tf]
        latest_idx = -1

        strength = 0.0
        count = 0

        # MACD信号强度
        macd = indicators['macd'].iloc[latest_idx]
        macd_signal = indicators['macd_signal'].iloc[latest_idx]
        histogram = indicators['macd_histogram'].iloc[latest_idx]

        if not np.isnan(histogram):
            if histogram > 0 and macd > macd_signal:
                strength += 0.3
            elif histogram < 0 and macd < macd_signal:
                strength += 0.3
            count += 0.3

        # RSI信号强度
        rsi = indicators['rsi'].iloc[latest_idx]
        if not np.isnan(rsi):
            if 30 < rsi < 70:  # 正常范围
                strength += 0.2
            count += 0.2

        # 布林带信号强度
        bb_width = indicators['bb_width'].iloc[latest_idx]
        if not np.isnan(bb_width):
            if bb_width > 0.02:  # 波动性适中
                strength += 0.2
            count += 0.2

        # 价格与移动平均线关系
        data = self.data_by_timeframe[tf]
        price = data['Close'].iloc[latest_idx]
        sma_20 = indicators['sma_20'].iloc[latest_idx]

        if not np.isnan(sma_20):
            if abs(price - sma_20) / sma_20 < 0.05:  # 价格接近均线
                strength += 0.3
            count += 0.3

        return strength / count if count > 0 else 0.0

    def generate_signals(self, current_data: pd.DataFrame) -> List[Signal]:
        """
        生成多时间框架确认的交易信号

        Args:
            current_data: 当前数据（主要时间框架）

        Returns:
            信号列表
        """
        signals = []

        try:
            # 更新主时间框架数据
            self.data_by_timeframe[self.primary_timeframe] = current_data.copy()

            # 重新计算指标
            self._calculate_indicators()

            # 计算趋势对齐度
            alignment = self._calculate_trend_alignment()

            # 检查是否满足确认条件
            if alignment < self.trend_alignment_threshold:
                logger.debug(f"趋势对齐度不足: {alignment:.2f} < {self.trend_alignment_threshold}")
                return signals

            # 确定主要趋势方向
            primary_trend = self._determine_trend_direction(self.primary_timeframe)

            if primary_trend == 0:
                return signals

            # 计算信号强度
            strength = self._get_signal_strength(self.primary_timeframe)

            # 计算综合置信度
            confidence = (alignment * 0.6 + strength * 0.4)

            # 检查最小置信度
            if confidence < self.min_confidence:
                return signals

            # 生成信号
            latest_data = current_data.iloc[-1]
            symbol = latest_data.get('Symbol', 'UNKNOWN')

            # 根据主要趋势方向生成信号
            if primary_trend > 0:  # 上涨趋势
                # 检查是否有买入确认
                confirmation_count = sum(
                    1 for tf in self.timeframes
                    if self.trend_signals.get(tf, 0) > 0
                )

                if confirmation_count >= self.confirmation_levels:
                    signal = Signal(
                        symbol=symbol,
                        timestamp=latest_data.name if isinstance(latest_data.name, pd.Timestamp) else pd.Timestamp.now(),
                        signal_type=SignalType.BUY,
                        confidence=confidence,
                        reason=f"多时间框架确认上涨 - 对齐度: {alignment:.2f}, 确认框架: {confirmation_count}/{len(self.timeframes)}",
                        price=float(latest_data['Close']),
                        metadata={
                            'timeframes': self.timeframes,
                            'alignment': alignment,
                            'strength': strength,
                            'trend_signals': self.trend_signals,
                            'primary_timeframe': self.primary_timeframe
                        }
                    )
                    signals.append(signal)

            elif primary_trend < 0:  # 下跌趋势
                # 检查是否有卖出确认
                confirmation_count = sum(
                    1 for tf in self.timeframes
                    if self.trend_signals.get(tf, 0) < 0
                )

                if confirmation_count >= self.confirmation_levels:
                    signal = Signal(
                        symbol=symbol,
                        timestamp=latest_data.name if isinstance(latest_data.name, pd.Timestamp) else pd.Timestamp.now(),
                        signal_type=SignalType.SELL,
                        confidence=confidence,
                        reason=f"多时间框架确认下跌 - 对齐度: {alignment:.2f}, 确认框架: {confirmation_count}/{len(self.timeframes)}",
                        price=float(latest_data['Close']),
                        metadata={
                            'timeframes': self.timeframes,
                            'alignment': alignment,
                            'strength': strength,
                            'trend_signals': self.trend_signals,
                            'primary_timeframe': self.primary_timeframe
                        }
                    )
                    signals.append(signal)

        except Exception as e:
            logger.error(f"信号生成失败: {e}")
            import traceback
            logger.error(traceback.format_exc())

        return signals

    def get_parameters(self) -> Dict[str, Any]:
        """获取策略参数"""
        return {
            'timeframes': self.timeframes,
            'primary_timeframe': self.primary_timeframe,
            'confirmation_levels': self.confirmation_levels,
            'trend_alignment_threshold': self.trend_alignment_threshold,
            'min_confidence': self.min_confidence
        }

    def set_parameters(self, parameters: Dict[str, Any]) -> None:
        """设置策略参数"""
        if 'timeframes' in parameters:
            self.timeframes = parameters['timeframes']
        if 'primary_timeframe' in parameters:
            self.primary_timeframe = parameters['primary_timeframe']
        if 'confirmation_levels' in parameters:
            self.confirmation_levels = parameters['confirmation_levels']
        if 'trend_alignment_threshold' in parameters:
            self.trend_alignment_threshold = parameters['trend_alignment_threshold']
        if 'min_confidence' in parameters:
            self.min_confidence = parameters['min_confidence']

    def get_trend_summary(self) -> Dict[str, Any]:
        """
        获取趋势摘要

        Returns:
            包含各时间框架趋势的字典
        """
        summary = {
            'timeframes': self.timeframes,
            'trend_signals': self.trend_signals,
            'alignment': self._calculate_trend_alignment(),
            'primary_timeframe': self.primary_timeframe,
            'primary_trend': self._determine_trend_direction(self.primary_timeframe)
        }

        # 添加各时间框架详细信息
        for tf in self.timeframes:
            if tf in self.indicators_by_timeframe:
                indicators = self.indicators_by_timeframe[tf]
                summary[tf] = {
                    'trend': self.trend_signals.get(tf, 0),
                    'sma_20': float(indicators['sma_20'].iloc[-1]) if not indicators['sma_20'].empty else None,
                    'sma_50': float(indicators['sma_50'].iloc[-1]) if len(indicators['sma_50']) > 20 else None,
                    'rsi': float(indicators['rsi'].iloc[-1]) if not indicators['rsi'].empty else None,
                    'signal_strength': self._get_signal_strength(tf)
                }

        return summary


# 导出策略类
__all__ = ['MultiTimeframeStrategy']
