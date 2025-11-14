"""
T174: Ichimoku Cloud (一目均衡表) 技术指标

完整的一目均衡表指标实现，包含5条线的计算和云图信号。

## 组成
1. 转换线 (Tenkan-sen) - 9日周期
2. 基准线 (Kijun-sen) - 26日周期
3. 先行带A (Senkou Span A) - 转换线与基准线的平均值，向前偏移26日
4. 先行带B (Senkou Span B) - 52日周期最高价和最低价的平均值，向前偏移26日
5. 延迟线 (Chikou Span) - 收盘价向前偏移26日

## 交易信号
- 价格在云图上方：上升趋势
- 价格在云图下方：下降趋势
- 云图缩窄：趋势可能反转
- 转换线与基准线交叉：金叉/死叉
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class IchimokuIndicator:
    """
    一目均衡表指标计算器

    提供完整的一目均衡表分析，包括5条线和云图信号。
    """

    def __init__(self, tenkan_period: int = 9, kijun_period: int = 26, senkou_b_period: int = 52):
        """
        初始化一目均衡表指标

        Args:
            tenkan_period: 转换线周期，默认9
            kijun_period: 基准线周期，默认26
            senkou_b_period: 先行带B周期，默认52
        """
        self.tenkan_period = tenkan_period
        self.kijun_period = kijun_period
        self.senkou_b_period = senkou_b_period

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算一目均衡表的所有组件

        Args:
            data: 包含OHLCV的DataFrame

        Returns:
            包含所有一目均衡表指标的DataFrame
        """
        if data is None or data.empty:
            logger.error("输入数据为空")
            return pd.DataFrame()

        df = data.copy()

        try:
            # 1. 转换线 (Tenkan-sen) - 9日最高价和最低价的平均值
            tenkan_high = df['High'].rolling(window=self.tenkan_period).max()
            tenkan_low = df['Low'].rolling(window=self.tenkan_period).min()
            df['Ichimoku_Tenkan'] = (tenkan_high + tenkan_low) / 2

            # 2. 基准线 (Kijun-sen) - 26日最高价和最低价的平均值
            kijun_high = df['High'].rolling(window=self.kijun_period).max()
            kijun_low = df['Low'].rolling(window=self.kijun_period).min()
            df['Ichimoku_Kijun'] = (kijun_high + kijun_low) / 2

            # 3. 先行带A (Senkou Span A) - 转换线与基准线的平均值，向前偏移26日
            df['Ichimoku_Senkou_A'] = ((df['Ichimoku_Tenkan'] + df['Ichimoku_Kijun']) / 2).shift(self.kijun_period)

            # 4. 先行带B (Senkou Span B) - 52日最高价和最低价的平均值，向前偏移26日
            senkou_b_high = df['High'].rolling(window=self.senkou_b_period).max()
            senkou_b_low = df['Low'].rolling(window=self.senkou_b_period).min()
            df['Ichimoku_Senkou_B'] = ((senkou_b_high + senkou_b_low) / 2).shift(self.kijun_period)

            # 5. 延迟线 (Chikou Span) - 收盘价向前偏移26日
            df['Ichimoku_Chikou'] = df['Close'].shift(-self.kijun_period)

            # 6. 计算云图信号
            df['Ichimoku_Cloud_Color'] = self._calculate_cloud_color(df)
            df['Ichimoku_Cloud_Thickness'] = self._calculate_cloud_thickness(df)
            df['Ichimoku_Price_Position'] = self._calculate_price_position(df)

            # 7. 计算交易信号
            df['Ichimoku_Trend_Signal'] = self._calculate_trend_signal(df)
            df['Ichimoku_Entry_Signal'] = self._calculate_entry_signal(df)

            # 8. 计算综合信号强度
            df['Ichimoku_Signal_Strength'] = self._calculate_signal_strength(df)

            logger.info("一目均衡表计算完成")

        except Exception as e:
            logger.error(f"一目均衡表计算错误: {e}")
            # 返回部分结果或NaN

        return df

    def _calculate_cloud_color(self, df: pd.DataFrame) -> pd.Series:
        """
        计算云图颜色

        Args:
            df: 包含一目均衡表数据的DataFrame

        Returns:
            云图颜色序列 (1=绿云, -1=红云, 0=中性)
        """
        try:
            # 绿云：先行带A > 先行带B
            # 红云：先行带A < 先行带B
            cloud_color = np.where(
                df['Ichimoku_Senkou_A'] > df['Ichimoku_Senkou_B'], 1, -1
            )
            return pd.Series(cloud_color, index=df.index)
        except:
            return pd.Series(0, index=df.index)

    def _calculate_cloud_thickness(self, df: pd.DataFrame) -> pd.Series:
        """
        计算云图厚度

        Args:
            df: 包含一目均衡表数据的DataFrame

        Returns:
            云图厚度序列
        """
        try:
            thickness = abs(df['Ichimoku_Senkou_A'] - df['Ichimoku_Senkou_B']) / df['Close']
            return thickness
        except:
            return pd.Series(0, index=df.index)

    def _calculate_price_position(self, df: pd.DataFrame) -> pd.Series:
        """
        计算价格相对于云图的位置

        Args:
            df: 包含一目均衡表数据的DataFrame

        Returns:
            价格位置序列 (1=云上, -1=云下, 0=云中)
        """
        try:
            # 价格在云图上方
            above_cloud = (df['Close'] > df['Ichimoku_Senkou_A']) & (df['Close'] > df['Ichimoku_Senkou_B'])
            # 价格在云图下方
            below_cloud = (df['Close'] < df['Ichimoku_Senkou_A']) & (df['Close'] < df['Ichimoku_Senkou_B'])
            # 价格在云图中
            in_cloud = ~above_cloud & ~below_cloud

            position = np.where(above_cloud, 1, np.where(below_cloud, -1, 0))
            return pd.Series(position, index=df.index)
        except:
            return pd.Series(0, index=df.index)

    def _calculate_trend_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        计算趋势信号

        Args:
            df: 包含一目均衡表数据的DataFrame

        Returns:
            趋势信号序列 (1=上升, -1=下降, 0=横盘)
        """
        try:
            # 转换线与基准线交叉
            tenkan_above_kijun = df['Ichimoku_Tenkan'] > df['Ichimoku_Kijun']
            tenkan_cross_kijun = tenkan_above_kijun != tenkan_above_kijun.shift(1)

            # 价格与云图关系
            price_above_cloud = df['Ichimoku_Price_Position'] == 1
            price_below_cloud = df['Ichimoku_Price_Position'] == -1

            # 云图颜色
            cloud_bullish = df['Ichimoku_Cloud_Color'] == 1
            cloud_bearish = df['Ichimoku_Cloud_Color'] == -1

            # 综合趋势判断
            signal = np.zeros(len(df))

            # 强上升趋势：价格云上 + 转换线上穿基准线 + 绿云
            strong_up = price_above_cloud & tenkan_cross_kijun & cloud_bullish
            signal[strong_up] = 1

            # 强下降趋势：价格云下 + 转换线下穿基准线 + 红云
            strong_down = price_below_cloud & tenkan_cross_kijun & cloud_bearish
            signal[strong_down] = -1

            return pd.Series(signal, index=df.index)
        except:
            return pd.Series(0, index=df.index)

    def _calculate_entry_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        计算入场信号

        Args:
            df: 包含一目均衡表数据的DataFrame

        Returns:
            入场信号序列 (1=买入, -1=卖出, 0=无信号)
        """
        try:
            signal = np.zeros(len(df))

            # 买入信号条件
            buy_condition_1 = (
                (df['Ichimoku_Price_Position'] == 1) &  # 价格在云上
                (df['Ichimoku_Price_Position'].shift(1) != 1) &  # 刚上穿云
                (df['Ichimoku_Cloud_Color'] == 1)  # 绿云
            )

            buy_condition_2 = (
                (df['Ichimoku_Tenkan'] > df['Ichimoku_Kijun']) &
                (df['Ichimoku_Tenkan'].shift(1) <= df['Ichimoku_Kijun'].shift(1)) &
                (df['Ichimoku_Price_Position'] >= 0)  # 价格不在云下
            )

            signal[buy_condition_1 | buy_condition_2] = 1

            # 卖出信号条件
            sell_condition_1 = (
                (df['Ichimoku_Price_Position'] == -1) &  # 价格在云下
                (df['Ichimoku_Price_Position'].shift(1) != -1) &  # 刚下穿云
                (df['Ichimoku_Cloud_Color'] == -1)  # 红云
            )

            sell_condition_2 = (
                (df['Ichimoku_Tenkan'] < df['Ichimoku_Kijun']) &
                (df['Ichimoku_Tenkan'].shift(1) >= df['Ichimoku_Kijun'].shift(1)) &
                (df['Ichimoku_Price_Position'] <= 0)  # 价格不在云上
            )

            signal[sell_condition_1 | sell_condition_2] = -1

            return pd.Series(signal, index=df.index)
        except:
            return pd.Series(0, index=df.index)

    def _calculate_signal_strength(self, df: pd.DataFrame) -> pd.Series:
        """
        计算信号强度

        Args:
            df: 包含一目均衡表数据的DataFrame

        Returns:
            信号强度序列 (0-1)
        """
        try:
            # 多个信号因子的加权组合
            signals = {
                'trend': abs(df['Ichimoku_Trend_Signal']),
                'price_position': abs(df['Ichimoku_Price_Position']) * 0.8,
                'cloud_color': abs(df['Ichimoku_Cloud_Color']) * 0.6,
                'cloud_thickness': (df['Ichimoku_Cloud_Thickness'] / df['Ichimoku_Cloud_Thickness'].rolling(50).max()).fillna(0) * 0.4,
            }

            # 加权平均
            strength = (
                signals['trend'] * 0.4 +
                signals['price_position'] * 0.3 +
                signals['cloud_color'] * 0.2 +
                signals['cloud_thickness'] * 0.1
            )

            # 限制在0-1范围
            strength = strength.clip(0, 1)
            return strength
        except:
            return pd.Series(0, index=df.index)

    def get_latest_signal(self, data: pd.DataFrame) -> Dict:
        """
        获取最新交易信号

        Args:
            data: 包含一目均衡表数据的DataFrame

        Returns:
            包含最新信号的字典
        """
        if data is None or data.empty:
            return {'signal': 0, 'strength': 0, 'description': '数据不足'}

        try:
            latest = data.iloc[-1]
            prev = data.iloc[-2] if len(data) > 1 else latest

            signal = int(latest['Ichimoku_Entry_Signal'])
            strength = float(latest['Ichimoku_Signal_Strength'])

            # 生成描述
            descriptions = {
                1: f"买入信号 (强度: {strength:.2f}, 价格在云{'上' if latest['Ichimoku_Price_Position'] == 1 else '中'})",
                -1: f"卖出信号 (强度: {strength:.2f}, 价格在云{'下' if latest['Ichimoku_Price_Position'] == -1 else '中'})",
                0: f"无信号 (强度: {strength:.2f}, 云图{'收缩' if latest['Ichimoku_Cloud_Thickness'] < data['Ichimoku_Cloud_Thickness'].rolling(20).mean().iloc[-1] else '扩张'})"
            }

            return {
                'signal': signal,
                'strength': strength,
                'description': descriptions.get(signal, '未知信号'),
                'trend': int(latest['Ichimoku_Trend_Signal']),
                'price_position': int(latest['Ichimoku_Price_Position']),
                'cloud_color': int(latest['Ichimoku_Cloud_Color']),
                'cloud_thickness': float(latest['Ichimoku_Cloud_Thickness']),
                'tenkan': float(latest['Ichimoku_Tenkan']),
                'kijun': float(latest['Ichimoku_Kijun']),
                'senkou_a': float(latest['Ichimoku_Senkou_A']) if not pd.isna(latest['Ichimoku_Senkou_A']) else None,
                'senkou_b': float(latest['Ichimoku_Senkou_B']) if not pd.isna(latest['Ichimoku_Senkou_B']) else None,
            }
        except Exception as e:
            logger.error(f"获取最新信号错误: {e}")
            return {'signal': 0, 'strength': 0, 'description': f'错误: {e}'}

    def get_visualization_data(self, data: pd.DataFrame, periods: int = 50) -> Dict:
        """
        获取用于可视化的数据

        Args:
            data: 包含一目均衡表数据的DataFrame
            periods: 返回的周期数

        Returns:
            用于可视化的数据字典
        """
        if data is None or data.empty:
            return {}

        try:
            recent_data = data.tail(periods)
            close = recent_data['Close'].values.tolist()
            dates = recent_data.index.strftime('%Y-%m-%d').tolist()

            return {
                'dates': dates,
                'close': close,
                'tenkan': recent_data['Ichimoku_Tenkan'].fillna(0).tolist(),
                'kijun': recent_data['Ichimoku_Kijun'].fillna(0).tolist(),
                'senkou_a': recent_data['Ichimoku_Senkou_A'].fillna(0).tolist(),
                'senkou_b': recent_data['Ichimoku_Senkou_B'].fillna(0).tolist(),
                'chikou': recent_data['Ichimoku_Chikou'].fillna(0).tolist(),
                'cloud_color': recent_data['Ichimoku_Cloud_Color'].tolist(),
                'cloud_thickness': recent_data['Ichimoku_Cloud_Thickness'].fillna(0).tolist(),
                'signals': recent_data['Ichimoku_Entry_Signal'].tolist(),
            }
        except Exception as e:
            logger.error(f"获取可视化数据错误: {e}")
            return {}


def calculate_ichimoku(data: pd.DataFrame, tenkan_period: int = 9, kijun_period: int = 26, senkou_b_period: int = 52) -> pd.DataFrame:
    """
    一目均衡表快速计算函数

    Args:
        data: 包含OHLCV的DataFrame
        tenkan_period: 转换线周期
        kijun_period: 基准线周期
        senkou_b_period: 先行带B周期

    Returns:
        包含一目均衡表指标的DataFrame
    """
    indicator = IchimokuIndicator(tenkan_period, kijun_period, senkou_b_period)
    return indicator.calculate(data)
