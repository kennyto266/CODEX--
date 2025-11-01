"""
波动率计算器 - 动态阈值调整的核心组件

用于计算市场波动率，以便动态调整累积回报阈值
"""

from typing import Optional
import pandas as pd
import numpy as np
import logging


class VolatilityCalculator:
    """
    波动率计算器

    支持多种波动率计算方法：
    1. 标准差波动率
    2. EWMA波动率（指数加权移动平均）
    3. GARCH风格波动率
    """

    def __init__(self):
        self.logger = logging.getLogger("cross_market_quant.VolatilityCalculator")

    def calculate_volatility(
        self,
        prices: pd.Series,
        method: str = 'std',
        window: Optional[int] = None,
        alpha: float = 0.94
    ) -> float:
        """
        计算波动率

        Args:
            prices: 价格序列
            method: 计算方法 ('std', 'ewma', 'garch')
            window: 计算窗口（对于std方法）
            alpha: EWMA衰减因子

        Returns:
            波动率（年化）
        """
        try:
            if method == 'std':
                return self._calculate_std_volatility(prices, window)
            elif method == 'ewma':
                return self._calculate_ewma_volatility(prices, alpha)
            elif method == 'garch':
                return self._calculate_garch_volatility(prices, alpha)
            else:
                raise ValueError(f"不支持的波动率计算方法: {method}")

        except Exception as e:
            self.logger.error(f"计算波动率失败: {e}")
            return 0.0

    def _calculate_std_volatility(self, prices: pd.Series, window: Optional[int] = None) -> float:
        """
        使用标准差计算波动率

        Args:
            prices: 价格序列
            window: 计算窗口

        Returns:
            年化波动率
        """
        try:
            if len(prices) < 2:
                return 0.0

            # 计算日收益率
            returns = prices.pct_change().dropna()

            if len(returns) == 0:
                return 0.0

            # 使用指定窗口或全部数据
            if window and len(returns) >= window:
                returns = returns.tail(window)

            # 计算标准差（年化）
            daily_vol = returns.std()
            annualized_vol = daily_vol * np.sqrt(252)  # 252个交易日

            return annualized_vol

        except Exception as e:
            self.logger.error(f"计算标准差波动率失败: {e}")
            return 0.0

    def _calculate_ewma_volatility(self, prices: pd.Series, alpha: float = 0.94) -> float:
        """
        使用指数加权移动平均计算波动率

        Args:
            prices: 价格序列
            alpha: 衰减因子

        Returns:
            年化EWMA波动率
        """
        try:
            if len(prices) < 2:
                return 0.0

            # 计算日收益率
            returns = prices.pct_change().dropna()

            if len(returns) == 0:
                return 0.0

            # EWMA波动率
            ewma_var = returns.ewm(alpha=alpha, adjust=False).var().iloc[-1]
            annualized_vol = np.sqrt(ewma_var * 252)

            return annualized_vol

        except Exception as e:
            self.logger.error(f"计算EWMA波动率失败: {e}")
            return 0.0

    def _calculate_garch_volatility(self, prices: pd.Series, alpha: float = 0.94) -> float:
        """
        简化的GARCH风格波动率计算

        Args:
            prices: 价格序列
            alpha: 衰减因子

        Returns:
            年化GARCH风格波动率
        """
        try:
            if len(prices) < 2:
                return 0.0

            # 计算日收益率
            returns = prices.pct_change().dropna()

            if len(returns) == 0:
                return 0.0

            # 简化的GARCH计算（实际上应该使用专门的GARCH库）
            squared_returns = returns ** 2

            # EWMA方差作为GARCH的近似
            ewma_var = squared_returns.ewm(alpha=alpha, adjust=False).mean().iloc[-1]
            annualized_vol = np.sqrt(ewma_var * 252)

            return annualized_vol

        except Exception as e:
            self.logger.error(f"计算GARCH波动率失败: {e}")
            return 0.0

    def calculate_rolling_volatility(
        self,
        prices: pd.Series,
        window: int = 20,
        method: str = 'std'
    ) -> pd.Series:
        """
        计算滚动波动率

        Args:
            prices: 价格序列
            window: 滚动窗口
            method: 计算方法

        Returns:
            滚动波动率序列
        """
        try:
            if len(prices) < window:
                self.logger.warning(f"数据长度不足{window}天")
                return pd.Series(index=prices.index, dtype=float)

            rolling_vol = pd.Series(index=prices.index, dtype=float)

            for i in range(window - 1, len(prices)):
                start_idx = i - window + 1
                price_window = prices.iloc[start_idx:i + 1]

                vol = self.calculate_volatility(price_window, method=method)
                rolling_vol.iloc[i] = vol

            self.logger.info(f"计算{len(rolling_vol)}个滚动波动率")
            return rolling_vol

        except Exception as e:
            self.logger.error(f"计算滚动波动率失败: {e}")
            return pd.Series(index=prices.index, dtype=float)

    def get_volatility_adjusted_threshold(
        self,
        base_threshold: float,
        current_volatility: float,
        typical_volatility: float = 0.20,
        adjustment_factor: float = 1.5
    ) -> float:
        """
        根据波动率调整阈值

        Args:
            base_threshold: 基础阈值
            current_volatility: 当前波动率
            typical_volatility: 典型波动率
            adjustment_factor: 调整系数

        Returns:
            调整后的阈值
        """
        try:
            # 波动率比例
            vol_ratio = current_volatility / typical_volatility

            # 调整阈值
            # 高波动率时增加阈值，低波动率时降低阈值
            adjustment = 1 + (vol_ratio - 1) * adjustment_factor
            adjusted_threshold = base_threshold * adjustment

            self.logger.info(
                f"阈值调整: {base_threshold:.4f} -> {adjusted_threshold:.4f} "
                f"(波动率: {current_volatility:.4f}, 比例: {vol_ratio:.2f})"
            )

            return adjusted_threshold

        except Exception as e:
            self.logger.error(f"调整阈值失败: {e}")
            return base_threshold
