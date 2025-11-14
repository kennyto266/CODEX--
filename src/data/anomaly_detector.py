"""
T351: 数据异常检测系统
智能异常检测系统，集成统计方法、机器学习算法和业务规则检测
支持多维度异常检测、实时监控和可视化分析

作者: Claude Code
日期: 2025-11-09
版本: 1.0.0
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union, Callable, Protocol
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import asyncio
import json
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
import pickle
import io
import base64

from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from scipy import stats
from scipy.stats import zscore, iqr, chi2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

logger = logging.getLogger('quant_system.data.anomaly_detector')

__all__ = [
    "AnomalyDetector", "AnomalyResult", "AnomalyType",
    "StatisticalAnomalyDetector", "MLAnomalyDetector",
    "RuleBasedAnomalyDetector", "RealtimeAnomalyMonitor",
    "AnomalyVisualizer", "AnomalyDetectionConfig"
]

class AnomalyType(Enum):
    """异常类型枚举"""
    STATISTICAL = "statistical"     # 统计异常
    PATTERN = "pattern"             # 模式异常
    STRUCTURAL = "structural"       # 结构异常
    TEMPORAL = "temporal"           # 时序异常
    VALUE = "value"                 # 数值异常
    MISSING = "missing"             # 缺失值异常
    DUPLICATE = "duplicate"         # 重复数据异常
    SEASONAL = "seasonal"           # 季节性异常
    RANGE = "range"                 # 范围异常
    TREND = "trend"                 # 趋势异常

class AnomalySeverity(Enum):
    """异常严重程度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class AnomalyDetectionConfig:
    """异常检测配置"""
    # 统计方法配置
    z_threshold: float = 3.0           # Z-Score阈值
    iqr_multiplier: float = 1.5        # IQR倍数
    mad_threshold: float = 3.5         # MAD阈值

    # ML方法配置
    isolation_contamination: float = 0.1    # Isolation Forest污染率
    lof_n_neighbors: int = 20               # LOF邻居数
    dbscan_eps: float = 0.5                 # DBSCAN eps
    dbscan_min_samples: int = 5             # DBSCAN最小样本数

    # 业务规则配置
    price_change_threshold: float = 0.2     # 价格变化阈值 (20%)
    volume_spike_multiplier: float = 3.0    # 成交量突增倍数
    min_data_points: int = 30               # 最小数据点数

    # 全局配置
    parallel: bool = True                   # 是否并行检测
    max_workers: int = 4                    # 最大工作进程数
    window_size: int = 100                  # 滑动窗口大小

class AnomalyResult:
    """异常检测结果"""

    def __init__(self,
                 type: AnomalyType,
                 score: float,
                 confidence: float,
                 index: Union[int, str, List[Union[int, str]]],
                 column: Optional[str] = None,
                 value: Any = None,
                 expected_value: Optional[Any] = None,
                 severity: AnomalySeverity = AnomalySeverity.MEDIUM,
                 description: str = "",
                 metadata: Optional[Dict[str, Any]] = None):
        self.type = type
        self.score = score
        self.confidence = confidence
        self.index = index if isinstance(index, list) else [index]
        self.column = column
        self.value = value
        self.expected_value = expected_value
        self.severity = severity
        self.description = description
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'type': self.type.value,
            'score': self.score,
            'confidence': self.confidence,
            'index': self.index,
            'column': self.column,
            'value': self.value,
            'expected_value': self.expected_value,
            'severity': self.severity.value,
            'description': self.description,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat()
        }

    def __repr__(self) -> str:
        return (f"AnomalyResult(type={self.type.value}, score={self.score:.3f}, "
                f"severity={self.severity.value}, column={self.column})")

class AnomalyDetector(Protocol):
    """异常检测器基类协议"""

    async def detect(self, data: Union[pd.DataFrame, pd.Series]) -> List[AnomalyResult]:
        """执行异常检测"""
        ...

    def get_config(self) -> AnomalyDetectionConfig:
        """获取配置"""
        ...

class StatisticalAnomalyDetector:
    """统计方法异常检测器"""

    def __init__(self, config: Optional[AnomalyDetectionConfig] = None):
        self.config = config or AnomalyDetectionConfig()
        self.name = "statistical_detector"

    async def detect(self, data: Union[pd.DataFrame, pd.Series]) -> List[AnomalyResult]:
        """执行统计异常检测"""
        results = []

        if isinstance(data, pd.DataFrame):
            # 多列检测
            for column in data.columns:
                if pd.api.types.is_numeric_dtype(data[column]):
                    column_results = await self._detect_column_anomalies(
                        data[column], column
                    )
                    results.extend(column_results)
        else:
            # 单列检测
            results = await self._detect_column_anomalies(data, None)

        return results

    async def _detect_column_anomalies(self, series: pd.Series,
                                       column: Optional[str]) -> List[AnomalyResult]:
        """检测单列异常"""
        results = []
        clean_series = series.dropna()

        if len(clean_series) < self.config.min_data_points:
            return results

        # Z-Score检测
        z_scores = np.abs(zscore(clean_series))
        z_anomalies = np.where(z_scores > self.config.z_threshold)[0]

        for idx in z_anomalies:
            original_idx = clean_series.index[idx]
            results.append(AnomalyResult(
                type=AnomalyType.STATISTICAL,
                score=float(z_scores[idx]),
                confidence=min(1.0, z_scores[idx] / self.config.z_threshold),
                index=original_idx,
                column=column,
                value=clean_series.iloc[idx],
                expected_value=None,
                severity=AnomalySeverity.HIGH if z_scores[idx] > 5.0 else AnomalySeverity.MEDIUM,
                description=f"Z-Score异常: {z_scores[idx]:.2f}",
                metadata={'method': 'zscore', 'threshold': self.config.z_threshold}
            ))

        # IQR检测
        Q1 = clean_series.quantile(0.25)
        Q3 = clean_series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - self.config.iqr_multiplier * IQR
        upper_bound = Q3 + self.config.iqr_multiplier * IQR

        iqr_anomalies = clean_series[
            (clean_series < lower_bound) | (clean_series > upper_bound)
        ]

        for idx, value in iqr_anomalies.items():
            score = max((lower_bound - value) / IQR, (value - upper_bound) / IQR)
            results.append(AnomalyResult(
                type=AnomalyType.STATISTICAL,
                score=float(score),
                confidence=min(1.0, score),
                index=idx,
                column=column,
                value=value,
                expected_value=(lower_bound, upper_bound),
                severity=AnomalySeverity.MEDIUM,
                description=f"IQR异常: 超出范围 [{lower_bound:.2f}, {upper_bound:.2f}]",
                metadata={
                    'method': 'iqr',
                    'lower_bound': lower_bound,
                    'upper_bound': upper_bound
                }
            ))

        # MAD检测 (Median Absolute Deviation)
        median = clean_series.median()
        mad = np.median(np.abs(clean_series - median))
        modified_z_scores = 0.6745 * (clean_series - median) / mad

        mad_anomalies = np.where(np.abs(modified_z_scores) > self.config.mad_threshold)[0]

        for idx in mad_anomalies:
            original_idx = clean_series.index[idx]
            results.append(AnomalyResult(
                type=AnomalyType.STATISTICAL,
                score=float(np.abs(modified_z_scores[idx])),
                confidence=min(1.0, np.abs(modified_z_scores[idx]) / self.config.mad_threshold),
                index=original_idx,
                column=column,
                value=clean_series.iloc[idx],
                expected_value=median,
                severity=AnomalySeverity.MEDIUM,
                description=f"MAD异常: {np.abs(modified_z_scores[idx]):.2f}",
                metadata={'method': 'mad', 'median': median, 'mad': mad}
            ))

        return results

    def get_config(self) -> AnomalyDetectionConfig:
        """获取配置"""
        return self.config

class MLAnomalyDetector:
    """机器学习异常检测器"""

    def __init__(self, config: Optional[AnomalyDetectionConfig] = None):
        self.config = config or AnomalyDetectionConfig()
        self.name = "ml_detector"
        self.models = {}

    async def detect(self, data: Union[pd.DataFrame, pd.Series]) -> List[AnomalyResult]:
        """执行机器学习异常检测"""
        results = []

        if isinstance(data, pd.DataFrame):
            # 确保只处理数值列
            numeric_data = data.select_dtypes(include=[np.number])

            if numeric_data.empty:
                return results

            # 数据标准化
            scaler = RobustScaler()
            scaled_data = scaler.fit_transform(numeric_data)

            # Isolation Forest
            iso_results = await self._isolation_forest_detection(scaled_data, numeric_data)
            results.extend(iso_results)

            # Local Outlier Factor
            lof_results = await self._lof_detection(scaled_data, numeric_data)
            results.extend(lof_results)

            # DBSCAN聚类
            dbscan_results = await self._dbscan_detection(scaled_data, numeric_data)
            results.extend(dbscan_results)

            # PCA重构
            pca_results = await self._pca_detection(scaled_data, numeric_data, scaler)
            results.extend(pca_results)

        return results

    async def _isolation_forest_detection(self,
                                          scaled_data: np.ndarray,
                                          original_data: pd.DataFrame) -> List[AnomalyResult]:
        """Isolation Forest检测"""
        results = []

        try:
            iso_forest = IsolationForest(
                contamination=self.config.isolation_contamination,
                random_state=42,
                n_jobs=-1
            )

            anomaly_labels = iso_forest.fit_predict(scaled_data)
            anomaly_scores = iso_forest.decision_function(scaled_data)

            for idx, (label, score) in enumerate(zip(anomaly_labels, anomaly_scores)):
                if label == -1:  # 异常点
                    # 计算严重程度
                    severity = self._calculate_severity(score, anomaly_scores, 'isolation')

                    results.append(AnomalyResult(
                        type=AnomalyType.PATTERN,
                        score=float(-score),  # 转换为正分数
                        confidence=min(1.0, abs(score) / np.max(np.abs(anomaly_scores))),
                        index=original_data.index[idx],
                        column=None,
                        value=None,
                        expected_value=None,
                        severity=severity,
                        description="Isolation Forest检测到异常模式",
                        metadata={
                            'method': 'isolation_forest',
                            'decision_score': score,
                            'contamination': self.config.isolation_contamination
                        }
                    ))

        except Exception as e:
            logger.error(f"Isolation Forest检测失败: {e}")

        return results

    async def _lof_detection(self,
                             scaled_data: np.ndarray,
                             original_data: pd.DataFrame) -> List[AnomalyResult]:
        """Local Outlier Factor检测"""
        results = []

        try:
            lof = LocalOutlierFactor(
                n_neighbors=self.config.lof_n_neighbors,
                contamination=self.config.isolation_contamination,
                n_jobs=-1
            )

            anomaly_labels = lof.fit_predict(scaled_data)
            lof_scores = lof.negative_outlier_factor_

            for idx, (label, score) in enumerate(zip(anomaly_labels, lof_scores)):
                if label == -1:  # 异常点
                    severity = self._calculate_severity(-score, lof_scores, 'lof')

                    results.append(AnomalyResult(
                        type=AnomalyType.PATTERN,
                        score=float(-score),
                        confidence=min(1.0, (np.max(lof_scores) - score) / np.max(lof_scores)),
                        index=original_data.index[idx],
                        column=None,
                        value=None,
                        expected_value=None,
                        severity=severity,
                        description="LOF检测到局部异常",
                        metadata={
                            'method': 'lof',
                            'lof_score': score,
                            'n_neighbors': self.config.lof_n_neighbors
                        }
                    ))

        except Exception as e:
            logger.error(f"LOF检测失败: {e}")

        return results

    async def _dbscan_detection(self,
                                scaled_data: np.ndarray,
                                original_data: pd.DataFrame) -> List[AnomalyResult]:
        """DBSCAN聚类检测"""
        results = []

        try:
            dbscan = DBSCAN(
                eps=self.config.dbscan_eps,
                min_samples=self.config.dbscan_min_samples,
                n_jobs=-1
            )

            cluster_labels = dbscan.fit_predict(scaled_data)

            # 标记为噪声的点 (-1标签) 为异常
            for idx, label in enumerate(cluster_labels):
                if label == -1:
                    results.append(AnomalyResult(
                        type=AnomalyType.STRUCTURAL,
                        score=1.0,
                        confidence=0.8,
                        index=original_data.index[idx],
                        column=None,
                        value=None,
                        expected_value=None,
                        severity=AnomalySeverity.HIGH,
                        description="DBSCAN检测到噪声点（异常聚类）",
                        metadata={
                            'method': 'dbscan',
                            'eps': self.config.dbscan_eps,
                            'min_samples': self.config.dbscan_min_samples
                        }
                    ))

        except Exception as e:
            logger.error(f"DBSCAN检测失败: {e}")

        return results

    async def _pca_detection(self,
                            scaled_data: np.ndarray,
                            original_data: pd.DataFrame,
                            scaler: RobustScaler) -> List[AnomalyResult]:
        """PCA重构误差检测"""
        results = []

        try:
            # 使用95%方差解释率的组件数
            pca = PCA(n_components=0.95)
            pca.fit(scaled_data)

            # 重构数据
            transformed = pca.transform(scaled_data)
            reconstructed = pca.inverse_transform(transformed)
            reconstruction_error = np.mean((scaled_data - reconstructed) ** 2, axis=1)

            # 计算重构误差的阈值
            error_threshold = np.mean(reconstruction_error) + 2 * np.std(reconstruction_error)

            for idx, error in enumerate(reconstruction_error):
                if error > error_threshold:
                    severity = AnomalySeverity.MEDIUM
                    if error > error_threshold * 2:
                        severity = AnomalySeverity.HIGH

                    results.append(AnomalyResult(
                        type=AnomalyType.STRUCTURAL,
                        score=float(error / error_threshold),
                        confidence=min(1.0, error / (error_threshold * 2)),
                        index=original_data.index[idx],
                        column=None,
                        value=None,
                        expected_value=None,
                        severity=severity,
                        description="PCA重构误差异常",
                        metadata={
                            'method': 'pca',
                            'reconstruction_error': error,
                            'threshold': error_threshold,
                            'n_components': pca.n_components_
                        }
                    ))

        except Exception as e:
            logger.error(f"PCA检测失败: {e}")

        return results

    def _calculate_severity(self, score: float, all_scores: np.ndarray,
                           method: str) -> AnomalySeverity:
        """计算异常严重程度"""
        score_percentile = stats.percentileofscore(all_scores, score)

        if score_percentile > 99:
            return AnomalySeverity.CRITICAL
        elif score_percentile > 95:
            return AnomalySeverity.HIGH
        elif score_percentile > 90:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW

    def get_config(self) -> AnomalyDetectionConfig:
        """获取配置"""
        return self.config

class RuleBasedAnomalyDetector:
    """基于规则的异常检测器"""

    def __init__(self, config: Optional[AnomalyDetectionConfig] = None):
        self.config = config or AnomalyDetectionConfig()
        self.name = "rule_detector"

    async def detect(self, data: Union[pd.DataFrame, pd.Series]) -> List[AnomalyResult]:
        """执行规则基异常检测"""
        results = []

        if not isinstance(data, pd.DataFrame):
            # 转换为DataFrame
            data = pd.DataFrame({'value': data})

        # 检查价格列
        price_columns = [col for col in data.columns
                        if any(keyword in col.lower()
                              for keyword in ['price', 'close', 'open', 'high', 'low'])]

        for col in price_columns:
            results.extend(await self._detect_price_anomalies(data, col))

        # 检查成交量列
        volume_columns = [col for col in data.columns
                         if 'volume' in col.lower()]

        for col in volume_columns:
            results.extend(await self._detect_volume_anomalies(data, col))

        # 检查通用数值异常
        numeric_columns = data.select_dtypes(include=[np.number]).columns

        for col in numeric_columns:
            results.extend(await self._detect_generic_anomalies(data, col))

        return results

    async def _detect_price_anomalies(self, data: pd.DataFrame,
                                      column: str) -> List[AnomalyResult]:
        """检测价格相关异常"""
        results = []
        series = data[column].dropna()

        if len(series) < 2:
            return results

        # 检测价格跳变
        price_changes = series.pct_change().abs()
        threshold = self.config.price_change_threshold

        anomalies = price_changes[price_changes > threshold]

        for idx, change in anomalies.items():
            severity = AnomalySeverity.HIGH if change > threshold * 2 else AnomalySeverity.MEDIUM

            results.append(AnomalyResult(
                type=AnomalyType.VALUE,
                score=float(change / threshold),
                confidence=min(1.0, change / (threshold * 2)),
                index=idx,
                column=column,
                value=series.loc[idx],
                expected_value=series.loc[idx] * (1 - threshold),
                severity=severity,
                description=f"价格跳变异常: {change:.2%}",
                metadata={
                    'method': 'price_change',
                    'change_pct': change,
                    'threshold': threshold
                }
            ))

        # 检测负价格
        negative_prices = series[series < 0]

        for idx, value in negative_prices.items():
            results.append(AnomalyResult(
                type=AnomalyType.VALUE,
                score=1.0,
                confidence=1.0,
                index=idx,
                column=column,
                value=value,
                expected_value=0,
                severity=AnomalySeverity.CRITICAL,
                description="负价格异常",
                metadata={'method': 'negative_price', 'value': value}
            ))

        return results

    async def _detect_volume_anomalies(self, data: pd.DataFrame,
                                       column: str) -> List[AnomalyResult]:
        """检测成交量异常"""
        results = []
        series = data[column].dropna()

        if len(series) < 10:
            return results

        # 计算移动平均和标准差
        window = min(20, len(series) // 2)
        rolling_mean = series.rolling(window=window).mean()
        rolling_std = series.rolling(window=window).std()

        # 检测成交量突增
        spike_threshold = self.config.volume_spike_multiplier
        spikes = series > (rolling_mean + spike_threshold * rolling_std)

        for idx in spikes[spikes].index:
            score = (series.loc[idx] - rolling_mean.loc[idx]) / rolling_std.loc[idx]

            results.append(AnomalyResult(
                type=AnomalyType.VALUE,
                score=float(abs(score)),
                confidence=min(1.0, abs(score) / 5.0),
                index=idx,
                column=column,
                value=series.loc[idx],
                expected_value=rolling_mean.loc[idx],
                severity=AnomalySeverity.MEDIUM,
                description=f"成交量突增异常: {series.loc[idx]:.0f}",
                metadata={
                    'method': 'volume_spike',
                    'spike_ratio': series.loc[idx] / rolling_mean.loc[idx],
                    'z_score': score
                }
            ))

        return results

    async def _detect_generic_anomalies(self, data: pd.DataFrame,
                                        column: str) -> List[AnomalyResult]:
        """检测通用数值异常"""
        results = []
        series = data[column].dropna()

        if len(series) < 2:
            return results

        # 检测零值
        zero_indices = series[series == 0].index
        for idx in zero_indices:
            results.append(AnomalyResult(
                type=AnomalyType.VALUE,
                score=1.0,
                confidence=0.9,
                index=idx,
                column=column,
                value=0,
                expected_value=series.mean(),
                severity=AnomalySeverity.LOW,
                description="零值异常",
                metadata={'method': 'zero_value'}
            ))

        # 检测重复值（连续重复）
        consecutive_duplicates = 0
        max_consecutive = 0
        last_value = None

        for value in series:
            if value == last_value:
                consecutive_duplicates += 1
                max_consecutive = max(max_consecutive, consecutive_duplicates)
            else:
                consecutive_duplicates = 1
            last_value = value

        if max_consecutive >= 5:  # 连续5个或以上相同值
            # 找到连续重复的起始位置
            start_idx = None
            consecutive_count = 0
            last_value = None

            for idx, value in series.items():
                if value == last_value:
                    consecutive_count += 1
                else:
                    if consecutive_count >= 5 and start_idx is None:
                        start_idx = series.index[series.index.get_loc(idx) - consecutive_count]
                    consecutive_count = 1
                last_value = value

            if start_idx is not None:
                results.append(AnomalyResult(
                    type=AnomalyType.PATTERN,
                    score=min(1.0, max_consecutive / 20.0),
                    confidence=0.8,
                    index=start_idx,
                    column=column,
                    value=None,
                    expected_value=None,
                    severity=AnomalySeverity.MEDIUM,
                    description=f"检测到连续重复值: {max_consecutive}个",
                    metadata={
                        'method': 'consecutive_duplicates',
                        'count': max_consecutive
                    }
                ))

        return results

    def get_config(self) -> AnomalyDetectionConfig:
        """获取配置"""
        return self.config

class RealtimeAnomalyMonitor:
    """实时异常监控器"""

    def __init__(self,
                 window_size: int = 100,
                 config: Optional[AnomalyDetectionConfig] = None):
        self.window_size = window_size
        self.config = config or AnomalyDetectionConfig()
        self.data_buffer = pd.DataFrame()
        self.anomaly_history = []
        self.monitoring = False
        self.callbacks = []

    async def start_monitoring(self,
                              data_stream: Any,
                              callback: Optional[Callable] = None):
        """开始实时监控"""
        self.monitoring = True

        if callback:
            self.callbacks.append(callback)

        try:
            async for new_data in data_stream:
                await self._process_new_data(new_data)

                if callback:
                    await callback(self.get_latest_results())

        except Exception as e:
            logger.error(f"实时监控异常: {e}")
        finally:
            self.monitoring = False

    async def _process_new_data(self, new_data: Union[pd.Series, Dict, Any]):
        """处理新数据"""
        if isinstance(new_data, dict):
            new_data = pd.Series(new_data)
        elif not isinstance(new_data, pd.Series):
            new_data = pd.Series([new_data])

        # 添加到缓冲区
        self.data_buffer = pd.concat([self.data_buffer, new_data.to_frame().T],
                                   ignore_index=True)

        # 保持窗口大小
        if len(self.data_buffer) > self.window_size:
            self.data_buffer = self.data_buffer.tail(self.window_size)

        # 执行检测
        if len(self.data_buffer) >= 10:  # 最小数据点
            detector = StatisticalAnomalyDetector(self.config)
            anomalies = await detector.detect(self.data_buffer)

            # 过滤出最新数据的异常
            latest_anomalies = [
                a for a in anomalies
                if len(self.data_buffer) - 1 in a.index
            ]

            self.anomaly_history.extend(latest_anomalies)

            # 保持历史记录
            if len(self.anomaly_history) > 1000:
                self.anomaly_history = self.anomaly_history[-1000:]

    def get_latest_results(self) -> List[AnomalyResult]:
        """获取最新检测结果"""
        if not self.anomaly_history:
            return []

        # 返回最近的异常
        recent_cutoff = datetime.utcnow() - timedelta(minutes=5)
        return [
            a for a in self.anomaly_history
            if a.timestamp >= recent_cutoff
        ]

    def get_anomaly_statistics(self) -> Dict[str, Any]:
        """获取异常统计信息"""
        if not self.anomaly_history:
            return {
                'total_anomalies': 0,
                'by_type': {},
                'by_severity': {},
                'by_column': {}
            }

        # 统计异常类型
        type_counts = {}
        for result in self.anomaly_history:
            type_name = result.type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        # 统计严重程度
        severity_counts = {}
        for result in self.anomaly_history:
            severity = result.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # 统计异常列
        column_counts = {}
        for result in self.anomaly_history:
            column = result.column or 'unknown'
            column_counts[column] = column_counts.get(column, 0) + 1

        return {
            'total_anomalies': len(self.anomaly_history),
            'by_type': type_counts,
            'by_severity': severity_counts,
            'by_column': column_counts,
            'monitoring': self.monitoring,
            'buffer_size': len(self.data_buffer)
        }

class AnomalyVisualizer:
    """异常检测结果可视化器"""

    def __init__(self):
        self.name = "visualizer"

    def create_anomaly_plot(self,
                           data: Union[pd.DataFrame, pd.Series],
                           anomalies: List[AnomalyResult],
                           column: Optional[str] = None) -> go.Figure:
        """创建异常检测图表"""
        if isinstance(data, pd.Series):
            data = data.to_frame()

        # 选择要绘制的列
        if column:
            plot_columns = [column]
        else:
            # 选择第一个数值列
            numeric_columns = data.select_dtypes(include=[np.number]).columns
            plot_columns = [numeric_columns[0]] if len(numeric_columns) > 0 else []

        if not plot_columns:
            raise ValueError("没有可绘制的数值列")

        fig = make_subplots(
            rows=len(plot_columns), cols=1,
            subplot_titles=plot_columns,
            vertical_spacing=0.05
        )

        for i, col in enumerate(plot_columns, 1):
            series = data[col].dropna()

            # 绘制原始数据
            fig.add_trace(
                go.Scatter(
                    x=series.index,
                    y=series.values,
                    mode='lines+markers',
                    name=f'{col} - 数据',
                    line=dict(color='blue', width=1),
                    marker=dict(size=4)
                ),
                row=i, col=1
            )

            # 标记异常点
            col_anomalies = [a for a in anomalies if a.column == col]

            if col_anomalies:
                anomaly_indices = []
                anomaly_values = []

                for anomaly in col_anomalies:
                    anomaly_indices.extend(anomaly.index)
                    for idx in anomaly.index:
                        if idx in series.index:
                            anomaly_values.append(series.loc[idx])

                if anomaly_indices and anomaly_values:
                    fig.add_trace(
                        go.Scatter(
                            x=anomaly_indices,
                            y=anomaly_values,
                            mode='markers',
                            name=f'{col} - 异常',
                            marker=dict(
                                color='red',
                                size=10,
                                symbol='x',
                                line=dict(width=2, color='darkred')
                            )
                        ),
                        row=i, col=1
                    )

        fig.update_layout(
            title='异常检测结果',
            height=300 * len(plot_columns),
            showlegend=True,
            hovermode='x unified'
        )

        return fig

    def create_anomaly_dashboard(self,
                                data: pd.DataFrame,
                                all_anomalies: List[AnomalyResult]) -> go.Figure:
        """创建异常检测仪表板"""
        # 按类型统计
        type_counts = {}
        for anomaly in all_anomalies:
            type_name = anomaly.type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        # 按严重程度统计
        severity_counts = {}
        for anomaly in all_anomalies:
            severity = anomaly.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('异常类型分布', '严重程度分布', '时间序列', '异常热力图'),
            specs=[[{"type": "pie"}, {"type": "pie"}],
                   [{"type": "scatter"}, {"type": "heatmap"}]]
        )

        # 异常类型饼图
        if type_counts:
            fig.add_trace(
                go.Pie(
                    labels=list(type_counts.keys()),
                    values=list(type_counts.values()),
                    name="异常类型"
                ),
                row=1, col=1
            )

        # 严重程度饼图
        if severity_counts:
            fig.add_trace(
                go.Pie(
                    labels=list(severity_counts.keys()),
                    values=list(severity_counts.values()),
                    name="严重程度"
                ),
                row=1, col=2
            )

        # 时间序列
        if data.shape[1] > 0:
            first_col = data.columns[0]
            series = data[first_col].dropna()

            fig.add_trace(
                go.Scatter(
                    x=series.index,
                    y=series.values,
                    mode='lines',
                    name=first_col
                ),
                row=2, col=1
            )

        # 异常热力图（简化版）
        if all_anomalies:
            # 创建异常矩阵
            anomaly_matrix = np.zeros((10, min(20, len(all_anomalies))))
            for i, anomaly in enumerate(all_anomalies[:200]):  # 最多显示200个异常
                if isinstance(anomaly.index, list) and anomaly.index:
                    idx = anomaly.index[0]
                    if isinstance(idx, int) and 0 <= idx < 10:
                        col_idx = min(i // 10, anomaly_matrix.shape[1] - 1)
                        anomaly_matrix[idx, col_idx] = anomaly.score

            fig.add_trace(
                go.Heatmap(
                    z=anomaly_matrix,
                    colorscale='Reds',
                    name="异常热力图"
                ),
                row=2, col=2
            )

        fig.update_layout(
            title="异常检测仪表板",
            height=800,
            showlegend=True
        )

        return fig

    def save_plot_as_html(self, fig: go.Figure, filepath: str):
        """保存图表为HTML文件"""
        fig.write_html(filepath)
        logger.info(f"异常检测图表已保存到: {filepath}")

    def plot_to_base64(self, fig: go.Figure) -> str:
        """将图表转换为base64字符串"""
        img_buffer = io.BytesIO()
        fig.write_image(img_buffer, format='png', width=1200, height=800, scale=2)
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.read()).decode()
        return img_base64

# 集成检测器类
class IntegratedAnomalyDetector:
    """集成异常检测器"""

    def __init__(self, config: Optional[AnomalyDetectionConfig] = None):
        self.config = config or AnomalyDetectionConfig()
        self.detectors = [
            StatisticalAnomalyDetector(self.config),
            MLAnomalyDetector(self.config),
            RuleBasedAnomalyDetector(self.config)
        ]
        self.visualizer = AnomalyVisualizer()

    async def detect(self, data: Union[pd.DataFrame, pd.Series]) -> Dict[str, Any]:
        """执行集成异常检测"""
        all_results = []
        detector_results = {}

        if self.config.parallel and len(self.detectors) > 1:
            # 并行检测
            tasks = []
            for detector in self.detectors:
                task = asyncio.create_task(detector.detect(data))
                tasks.append((detector.name, task))

            for detector_name, task in tasks:
                try:
                    results = await task
                    detector_results[detector_name] = results
                    all_results.extend(results)
                except Exception as e:
                    logger.error(f"检测器 {detector_name} 执行失败: {e}")
                    detector_results[detector_name] = []
        else:
            # 串行检测
            for detector in self.detectors:
                try:
                    results = await detector.detect(data)
                    detector_results[detector.name] = results
                    all_results.extend(results)
                except Exception as e:
                    logger.error(f"检测器 {detector.name} 执行失败: {e}")
                    detector_results[detector.name] = []

        # 去重（相同位置的异常）
        unique_results = self._deduplicate_results(all_results)

        # 生成可视化
        visualization = None
        try:
            if isinstance(data, pd.DataFrame) and not data.empty:
                visualization = self.visualizer.create_anomaly_plot(data, unique_results)
        except Exception as e:
            logger.error(f"生成可视化失败: {e}")

        return {
            'anomalies': [r.to_dict() for r in unique_results],
            'detector_results': {
                name: [r.to_dict() for r in results]
                for name, results in detector_results.items()
            },
            'statistics': {
                'total_anomalies': len(unique_results),
                'by_type': self._count_by_type(unique_results),
                'by_severity': self._count_by_severity(unique_results),
                'by_column': self._count_by_column(unique_results)
            },
            'visualization': visualization
        }

    def _deduplicate_results(self, results: List[AnomalyResult]) -> List[AnomalyResult]:
        """去重异常结果"""
        unique_results = []
        seen_combinations = set()

        for result in results:
            # 创建唯一标识
            combination = (result.index, result.column, result.type)

            if combination not in seen_combinations:
                seen_combinations.add(combination)
                unique_results.append(result)
            else:
                # 合并相同位置的异常
                existing = next(
                    r for r in unique_results
                    if (r.index, r.column, r.type) == combination
                )
                # 保留分数更高的
                if result.score > existing.score:
                    unique_results.remove(existing)
                    unique_results.append(result)

        return unique_results

    def _count_by_type(self, results: List[AnomalyResult]) -> Dict[str, int]:
        """按类型统计"""
        counts = {}
        for result in results:
            type_name = result.type.value
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts

    def _count_by_severity(self, results: List[AnomalyResult]) -> Dict[str, int]:
        """按严重程度统计"""
        counts = {}
        for result in results:
            severity = result.severity.value
            counts[severity] = counts.get(severity, 0) + 1
        return counts

    def _count_by_column(self, results: List[AnomalyResult]) -> Dict[str, int]:
        """按列统计"""
        counts = {}
        for result in results:
            column = result.column or 'unknown'
            counts[column] = counts.get(column, 0) + 1
        return counts

# 便捷函数
async def detect_anomalies(data: Union[pd.DataFrame, pd.Series],
                          config: Optional[AnomalyDetectionConfig] = None,
                          use_ml: bool = True,
                          use_rules: bool = True) -> Dict[str, Any]:
    """
    便捷的异常检测函数

    Args:
        data: 待检测数据
        config: 配置参数
        use_ml: 是否使用机器学习检测
        use_rules: 是否使用规则检测

    Returns:
        异常检测结果
    """
    detector = IntegratedAnomalyDetector(config)

    # 可选择性禁用某些检测器
    if not use_ml:
        detector.detectors = [d for d in detector.detectors
                             if not isinstance(d, MLAnomalyDetector)]
    if not use_rules:
        detector.detectors = [d for d in detector.detectors
                             if not isinstance(d, RuleBasedAnomalyDetector)]

    return await detector.detect(data)

def create_anomaly_detector(config: Optional[AnomalyDetectionConfig] = None) -> IntegratedAnomalyDetector:
    """创建异常检测器实例"""
    return IntegratedAnomalyDetector(config)

# 使用示例
if __name__ == "__main__":
    import asyncio

    async def test_anomaly_detection():
        # 创建测试数据
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=200, freq='D')
        test_data = pd.DataFrame({
            'close': np.random.normal(100, 10, 200) + np.sin(np.arange(200) * 0.1) * 5,
            'volume': np.random.lognormal(10, 1, 200)
        }, index=dates)

        # 注入一些异常
        test_data.loc[test_data.index[50], 'close'] = 200  # 跳变
        test_data.loc[test_data.index[100], 'volume'] = test_data['volume'].max() * 5  # 成交量突增
        test_data.loc[test_data.index[150], 'close'] = -50  # 负值

        # 执行检测
        config = AnomalyDetectionConfig()
        detector = IntegratedAnomalyDetector(config)
        results = await detector.detect(test_data)

        # 打印结果
        print(f"\n=== 异常检测结果 ===")
        print(f"总异常数: {results['statistics']['total_anomalies']}")
        print(f"按类型: {results['statistics']['by_type']}")
        print(f"按严重程度: {results['statistics']['by_severity']}")
        print(f"按列: {results['statistics']['by_column']}")

        if results['anomalies']:
            print("\n前5个异常:")
            for anomaly in results['anomalies'][:5]:
                print(f"  - {anomaly['description']} (分数: {anomaly['score']:.2f})")

        # 生成可视化
        if results['visualization']:
            detector.visualizer.save_plot_as_html(
                results['visualization'],
                'anomaly_detection_result.html'
            )
            print("\n可视化图表已保存到: anomaly_detection_result.html")

    # 运行测试
    asyncio.run(test_anomaly_detection())
