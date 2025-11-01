"""
特征工程模块
为机器学习模型生成和转换特征
"""

import pandas as pd
import numpy as np
import talib
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FeatureEngine:
    """特征工程类"""

    def __init__(self):
        """初始化特征工程"""
        self.feature_config = {
            'price_features': True,
            'volume_features': True,
            'technical_indicators': True,
            'volatility_features': True,
            'momentum_features': True,
            'price_pattern_features': True,
            'time_features': True,
            'lag_features': True,
            'rolling_features': True
        }

    def create_all_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        创建所有特征

        Args:
            data: 原始股票数据 (必须包含: open, high, low, close, volume)

        Returns:
            包含所有特征的数据框
        """
        if data.empty:
            logger.warning("输入数据为空")
            return data

        # 确保数据按日期排序
        data = data.sort_values('timestamp').reset_index(drop=True)

        # 创建特征副本
        features = data.copy()

        # 价格特征
        if self.feature_config['price_features']:
            features = self._create_price_features(features)

        # 成交量特征
        if self.feature_config['volume_features']:
            features = self._create_volume_features(features)

        # 技术指标
        if self.feature_config['technical_indicators']:
            features = self._create_technical_indicators(features)

        # 波动率特征
        if self.feature_config['volatility_features']:
            features = self._create_volatility_features(features)

        # 动量特征
        if self.feature_config['momentum_features']:
            features = self._create_momentum_features(features)

        # 价格形态特征
        if self.feature_config['price_pattern_features']:
            features = self._create_price_pattern_features(features)

        # 时间特征
        if self.feature_config['time_features']:
            features = self._create_time_features(features)

        # 滞后特征
        if self.feature_config['lag_features']:
            features = self._create_lag_features(features)

        # 滚动窗口特征
        if self.feature_config['rolling_features']:
            features = self._create_rolling_features(features)

        # 移除原始数据列
        columns_to_remove = ['open', 'high', 'low', 'close', 'volume', 'timestamp']
        features = features.drop(columns=columns_to_remove, errors='ignore')

        logger.info(f"生成了 {len(features.columns)} 个特征")
        return features

    def _create_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """创建价格相关特征"""
        try:
            # 价格变化
            df['price_change'] = df['close'].pct_change()
            df['price_change_abs'] = df['price_change'].abs()

            # 高低价差
            df['high_low_pct'] = (df['high'] - df['low']) / df['close']

            # 开盘价与收盘价差
            df['open_close_pct'] = (df['close'] - df['open']) / df['open']

            # 上一日收盘价
            df['prev_close'] = df['close'].shift(1)

            # 相对于昨日收盘价的涨跌
            df['gap'] = (df['open'] - df['prev_close']) / df['prev_close']

            # 最高价、最低价、开盘价的相对位置
            df['close_position'] = (df['close'] - df['low']) / (df['high'] - df['low'])
            df['close_position'] = df['close_position'].fillna(0.5)

            return df
        except Exception as e:
            logger.error(f"创建价格特征失败: {e}")
            return df

    def _create_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """创建成交量相关特征"""
        try:
            # 成交量变化
            df['volume_change'] = df['volume'].pct_change()
            df['volume_change_abs'] = df['volume_change'].abs()

            # 成交量移动平均
            for window in [5, 10, 20]:
                df[f'volume_sma_{window}'] = df['volume'].rolling(window=window).mean()
                df[f'volume_ratio_{window}'] = df['volume'] / df[f'volume_sma_{window}']

            # 价格-成交量关系
            df['price_volume'] = df['close'] * df['volume']

            # 成交量的移动平均
            df['volume_price_trend'] = df['volume'].rolling(window=10).apply(
                lambda x: (x * df['close'][:len(x)]).sum() / x.sum() if len(x) > 0 else 0
            )

            return df
        except Exception as e:
            logger.error(f"创建成交量特征失败: {e}")
            return df

    def _create_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """创建技术指标特征"""
        try:
            close = df['close'].values
            high = df['high'].values
            low = df['low'].values
            volume = df['volume'].values

            # 移动平均线
            for period in [5, 10, 20, 50]:
                df[f'sma_{period}'] = talib.SMA(close, timeperiod=period)
                df[f'ema_{period}'] = talib.EMA(close, timeperiod=period)

            # 相对强弱指数 (RSI)
            df['rsi_14'] = talib.RSI(close, timeperiod=14)
            df['rsi_7'] = talib.RSI(close, timeperiod=7)

            # MACD
            macd, macdsignal, macdhist = talib.MACD(close)
            df['macd'] = macd
            df['macd_signal'] = macdsignal
            df['macd_hist'] = macdhist

            # 布林带
            upper, middle, lower = talib.BBANDS(close, timeperiod=20)
            df['bb_upper'] = upper
            df['bb_middle'] = middle
            df['bb_lower'] = lower
            df['bb_width'] = (upper - lower) / middle
            df['bb_position'] = (close - lower) / (upper - lower)

            # 随机指标 (KDJ)
            slowk, slowd = talib.STOCH(high, low, close)
            df['k_percent'] = slowk
            df['d_percent'] = slowd
            df['j_percent'] = 3 * slowk - 2 * slowd

            # 商品通道指数 (CCI)
            df['cci'] = talib.CCI(high, low, close, timeperiod=14)

            # 平均方向指数 (ADX)
            df['adx'] = talib.ADX(high, low, close, timeperiod=14)

            # 真实范围 (ATR)
            df['atr'] = talib.ATR(high, low, close, timeperiod=14)

            # 威廉指标 (%R)
            df['willr'] = talib.WILLR(high, low, close, timeperiod=14)

            # 动量指标 (MOM)
            df['mom_10'] = talib.MOM(close, timeperiod=10)

            return df
        except Exception as e:
            logger.error(f"创建技术指标失败: {e}")
            return df

    def _create_volatility_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """创建波动率特征"""
        try:
            # 价格标准差
            for window in [5, 10, 20]:
                df[f'volatility_{window}'] = df['close'].rolling(window=window).std()
                df[f'log_return_std_{window}'] = np.log(df['close'] / df['close'].shift(1)).rolling(window=window).std()

            # 历史波动率
            df['historical_volatility_20'] = df['close'].pct_change().rolling(window=20).std()

            # 波动率比率
            df['volatility_ratio_5_20'] = df['volatility_5'] / df['volatility_20']
            df['volatility_ratio_10_20'] = df['volatility_10'] / df['volatility_20']

            # 价格偏离
            df['price_deviation'] = (df['close'] - df['close'].rolling(window=20).mean()) / df['close'].rolling(window=20).std()

            return df
        except Exception as e:
            logger.error(f"创建波动率特征失败: {e}")
            return df

    def _create_momentum_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """创建动量特征"""
        try:
            # 价格动量
            for period in [5, 10, 20]:
                df[f'momentum_{period}'] = df['close'] / df['close'].shift(period) - 1

            # 成交量动量
            df['volume_momentum_10'] = df['volume'] / df['volume'].shift(10) - 1

            # 相对强弱
            df['relative_strength'] = df['close'] / df['close'].rolling(window=20).mean()

            return df
        except Exception as e:
            logger.error(f"创建动量特征失败: {e}")
            return df

    def _create_price_pattern_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """创建价格形态特征"""
        try:
            # 影线特征
            df['upper_shadow'] = df['high'] - np.maximum(df['open'], df['close'])
            df['lower_shadow'] = np.minimum(df['open'], df['close']) - df['low']
            df['body'] = np.abs(df['close'] - df['open'])

            # 影线比例
            df['upper_shadow_ratio'] = df['upper_shadow'] / df['body']
            df['lower_shadow_ratio'] = df['lower_shadow'] / df['body']

            # K线形态
            df['is_doji'] = (df['body'] / (df['high'] - df['low']) < 0.1).astype(int)
            df['is_hammer'] = ((df['lower_shadow'] > 2 * df['body']) & (df['upper_shadow'] < df['body'])).astype(int)
            df['is_shooting_star'] = ((df['upper_shadow'] > 2 * df['body']) & (df['lower_shadow'] < df['body'])).astype(int)

            # 趋势特征
            df['trend_5'] = np.where(df['close'] > df['close'].shift(5), 1,
                                    np.where(df['close'] < df['close'].shift(5), -1, 0))
            df['trend_10'] = np.where(df['close'] > df['close'].shift(10), 1,
                                     np.where(df['close'] < df['close'].shift(10), -1, 0))

            return df
        except Exception as e:
            logger.error(f"创建价格形态特征失败: {e}")
            return df

    def _create_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """创建时间特征"""
        try:
            # 确保timestamp是datetime类型
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])

                # 星期几 (0=周一, 6=周日)
                df['day_of_week'] = df['timestamp'].dt.dayofweek

                # 月份
                df['month'] = df['timestamp'].dt.month

                # 一年中的第几天
                df['day_of_year'] = df['timestamp'].dt.dayofyear

                # 是否月初、月末
                df['is_month_start'] = df['timestamp'].dt.is_month_start.astype(int)
                df['is_month_end'] = df['timestamp'].dt.is_month_end.astype(int)

                # 是否周一、周五
                df['is_monday'] = (df['day_of_week'] == 0).astype(int)
                df['is_friday'] = (df['day_of_week'] == 4).astype(int)

            return df
        except Exception as e:
            logger.error(f"创建时间特征失败: {e}")
            return df

    def _create_lag_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """创建滞后特征"""
        try:
            # 价格滞后特征
            for lag in [1, 2, 3, 5, 10]:
                df[f'close_lag_{lag}'] = df['close'].shift(lag)
                df[f'volume_lag_{lag}'] = df['volume'].shift(lag)
                df[f'price_change_lag_{lag}'] = df['price_change'].shift(lag)

            # 技术指标滞后
            for col in ['rsi_14', 'macd', 'bb_position', 'atr']:
                if col in df.columns:
                    for lag in [1, 2, 3]:
                        df[f'{col}_lag_{lag}'] = df[col].shift(lag)

            return df
        except Exception as e:
            logger.error(f"创建滞后特征失败: {e}")
            return df

    def _create_rolling_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """创建滚动窗口特征"""
        try:
            # 滚动统计
            for window in [5, 10, 20]:
                # 价格滚动统计
                df[f'close_roll_mean_{window}'] = df['close'].rolling(window=window).mean()
                df[f'close_roll_std_{window}'] = df['close'].rolling(window=window).std()
                df[f'close_roll_skew_{window}'] = df['close'].rolling(window=window).skew()
                df[f'close_roll_kurt_{window}'] = df['close'].rolling(window=window).kurt()

                # 成交量滚动统计
                df[f'volume_roll_mean_{window}'] = df['volume'].rolling(window=window).mean()

            # 滚动相关性
            if len(df) >= 20:
                df['price_volume_corr_20'] = df['close'].rolling(window=20).corr(df['volume'])

            return df
        except Exception as e:
            logger.error(f"创建滚动特征失败: {e}")
            return df

    def select_features(self, df: pd.DataFrame, method: str = 'all', top_n: int = 50) -> pd.DataFrame:
        """
        特征选择

        Args:
            df: 特征数据框
            method: 选择方法 ('all', 'variance', 'correlation')
            top_n: 选择前N个特征

        Returns:
            选择的特征
        """
        if method == 'all':
            return df

        elif method == 'variance':
            # 方差选择
            numeric_df = df.select_dtypes(include=[np.number])
            variances = numeric_df.var()
            selected_features = variances.sort_values(ascending=False).head(top_n).index
            return df[selected_features]

        elif method == 'correlation':
            # 相关性选择
            numeric_df = df.select_dtypes(include=[np.number])
            corr_matrix = numeric_df.corr().abs()
            upper_triangle = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
            high_corr_features = [column for column in upper_triangle.columns if any(upper_triangle[column] > 0.9)]
            selected_features = [col for col in numeric_df.columns if col not in high_corr_features]
            return df[selected_features[:top_n]]

        return df

    def create_target(self, data: pd.DataFrame, target_type: str = 'next_return',
                     periods: int = 1, threshold: float = 0.02) -> pd.Series:
        """
        创建目标变量

        Args:
            data: 原始数据
            target_type: 目标类型 ('next_return', 'direction', 'price_change')
            periods: 预测周期
            threshold: 分类阈值

        Returns:
            目标变量
        """
        try:
            if target_type == 'next_return':
                # 下一个周期的收益率
                target = data['close'].shift(-periods) / data['close'] - 1
                return target

            elif target_type == 'direction':
                # 价格方向 (1: 涨, 0: 跌)
                future_return = data['close'].shift(-periods) / data['close'] - 1
                target = (future_return > threshold).astype(int)
                return target

            elif target_type == 'price_change':
                # 价格变化
                target = data['close'].shift(-periods) - data['close']
                return target

        except Exception as e:
            logger.error(f"创建目标变量失败: {e}")
            return pd.Series()

        return pd.Series()
