"""
HKMA数据质量监控系统
监控HIBOR数据的质量、新鲜度和异常情况

功能:
- 数据新鲜度监控
- 质量评分
- 异常检测
- 质量报告
- 性能监控
- 趋势分析
- 告警系统
"""

import asyncio
import logging
import os
import json
import statistics
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import pandas as pd
import numpy as np
from collections import deque

logger = logging.getLogger(__name__)


class QualityLevel(Enum):
    """数据质量等级"""
    EXCELLENT = "excellent"  # 90-100
    GOOD = "good"  # 70-89
    FAIR = "fair"  # 50-69
    POOR = "poor"  # 30-49
    CRITICAL = "critical"  # 0-29


class MetricType(Enum):
    """指标类型"""
    FRESHNESS = "freshness"
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    TREND = "trend"
    VOLATILITY = "volatility"
    AVAILABILITY = "availability"


@dataclass
class DataQualityMetrics:
    """数据质量指标"""
    overall_score: float  # 总体评分 (0-100)
    freshness_score: float  # 新鲜度评分
    completeness_score: float  # 完整性评分
    accuracy_score: float  # 准确性评分
    consistency_score: float  # 一致性评分
    trend_score: float  # 趋势评分
    volatility_score: float  # 波动性评分
    availability_score: float  # 可用性评分
    last_update: datetime
    data_points: int
    missing_count: int
    anomalies_count: int

    def get_quality_level(self) -> QualityLevel:
        """获取质量等级"""
        score = self.overall_score
        if score >= 90:
            return QualityLevel.EXCELLENT
        elif score >= 70:
            return QualityLevel.GOOD
        elif score >= 50:
            return QualityLevel.FAIR
        elif score >= 30:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            **asdict(self),
            'quality_level': self.get_quality_level().value
        }


@dataclass
class QualityAlert:
    """质量告警"""
    id: str
    metric_type: MetricType
    level: QualityLevel
    message: str
    timestamp: datetime
    value: float
    threshold: float
    resolved: bool = False
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'metric_type': self.metric_type.value,
            'level': self.level.value,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'value': self.value,
            'threshold': self.threshold,
            'resolved': self.resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }


class HKMAMonitor:
    """HKMA数据质量监控器"""

    # 质量阈值配置
    QUALITY_THRESHOLDS = {
        MetricType.FRESHNESS: {
            'excellent': 24,  # 24小时内
            'good': 48,  # 48小时内
            'fair': 72,  # 72小时内
            'poor': 168,  # 1周内
            'critical': float('inf')  # 超过1周
        },
        MetricType.COMPLETENESS: {
            'excellent': 0.95,  # 95%以上
            'good': 0.90,  # 90%以上
            'fair': 0.80,  # 80%以上
            'poor': 0.70,  # 70%以上
            'critical': 0.0
        },
        MetricType.ACCURACY: {
            'excellent': 0.98,  # 98%以上
            'good': 0.95,  # 95%以上
            'fair': 0.90,  # 90%以上
            'poor': 0.85,  # 85%以上
            'critical': 0.0
        },
        MetricType.CONSISTENCY: {
            'excellent': 0.97,  # 97%以上
            'good': 0.93,  # 93%以上
            'fair': 0.88,  # 88%以上
            'poor': 0.80,  # 80%以上
            'critical': 0.0
        },
        MetricType.TREND: {
            'excellent': 0.95,  # 95%以上符合预期趋势
            'good': 0.90,
            'fair': 0.80,
            'poor': 0.70,
            'critical': 0.0
        },
        MetricType.VOLATILITY: {
            'excellent': 0.05,  # 波动性低于5%
            'good': 0.10,  # 波动性低于10%
            'fair': 0.15,  # 波动性低于15%
            'poor': 0.20,  # 波动性低于20%
            'critical': float('inf')
        },
        MetricType.AVAILABILITY: {
            'excellent': 0.99,  # 99%以上可用
            'good': 0.95,
            'fair': 0.90,
            'poor': 0.85,
            'critical': 0.0
        }
    }

    # 监控存储文件
    MONITOR_STORE_FILE = "data/hkma_monitor_store.json"

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化数据质量监控器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # 告警回调
        self.alert_callbacks: List[Callable] = []

        # 数据质量历史
        self.quality_history: deque = deque(maxlen=100)

        # 当前告警
        self.active_alerts: Dict[str, QualityAlert] = {}
        self.alert_history: List[QualityAlert] = []

        # 数据点
        self.data_points: List[Dict] = []
        self.max_data_points = self.config.get('max_data_points', 1000)

        # 监控间隔
        self.monitor_interval = self.config.get('monitor_interval', 300)  # 5分钟
        self.auto_monitoring = self.config.get('auto_monitoring', True)

        # 监控任务
        self.monitor_task: Optional[asyncio.Task] = None

        # 加载历史数据
        self._load_monitor_store()

    def add_alert_callback(self, callback: Callable):
        """
        添加告警回调

        Args:
            callback: 告警回调函数 (alert: QualityAlert)
        """
        self.alert_callbacks.append(callback)

    async def _trigger_alert(self, alert: QualityAlert):
        """触发告警"""
        self.logger.warning(
            f"数据质量告警 [{alert.level.value}]: {alert.message}"
        )

        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                self.logger.error(f"告警回调执行失败: {e}")

    async def add_data_point(self, data: Dict[str, Any]):
        """
        添加数据点用于监控

        Args:
            data: 数据字典，包含date、rate等字段
        """
        # 规范化数据
        normalized_data = self._normalize_data(data)
        self.data_points.append(normalized_data)

        # 限制数据点数量
        if len(self.data_points) > self.max_data_points:
            self.data_points.pop(0)

        # 记录日志
        self.logger.debug(f"添加数据点: {normalized_data.get('date', 'unknown')}")

    def _normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """规范化数据"""
        normalized = data.copy()

        # 确保有date字段
        if 'date' in normalized:
            if isinstance(normalized['date'], str):
                try:
                    normalized['date'] = pd.to_datetime(normalized['date'])
                except:
                    normalized['date'] = datetime.now()
            elif isinstance(normalized['date'], datetime):
                pass
            else:
                normalized['date'] = datetime.now()

        # 确保有rate字段
        if 'rate' not in normalized and 'hibor_overnight' in normalized:
            normalized['rate'] = normalized['hibor_overnight']

        # 添加元数据
        normalized['ingested_at'] = datetime.now()

        return normalized

    async def calculate_quality_metrics(
        self,
        data: Optional[List[Dict]] = None
    ) -> DataQualityMetrics:
        """
        计算数据质量指标

        Args:
            data: 要分析的数据（默认使用缓存数据）

        Returns:
            DataQualityMetrics质量指标
        """
        if data is None:
            data = self.data_points

        if not data:
            self.logger.warning("没有数据点可用于质量分析")
            return DataQualityMetrics(
                overall_score=0,
                freshness_score=0,
                completeness_score=0,
                accuracy_score=0,
                consistency_score=0,
                trend_score=0,
                volatility_score=0,
                availability_score=0,
                last_update=datetime.now(),
                data_points=0,
                missing_count=0,
                anomalies_count=0
            )

        self.logger.info(f"计算 {len(data)} 个数据点的质量指标")

        # 转换为DataFrame
        df = self._to_dataframe(data)

        # 计算各项指标
        freshness_score = self._calculate_freshness_score(df)
        completeness_score = self._calculate_completeness_score(df)
        accuracy_score = self._calculate_accuracy_score(df)
        consistency_score = self._calculate_consistency_score(df)
        trend_score = self._calculate_trend_score(df)
        volatility_score = self._calculate_volatility_score(df)
        availability_score = self._calculate_availability_score(df)

        # 计算总体评分（加权平均）
        weights = {
            'freshness': 0.20,
            'completeness': 0.20,
            'accuracy': 0.20,
            'consistency': 0.15,
            'trend': 0.10,
            'volatility': 0.10,
            'availability': 0.05
        }

        overall_score = (
            freshness_score * weights['freshness'] +
            completeness_score * weights['completeness'] +
            accuracy_score * weights['accuracy'] +
            consistency_score * weights['consistency'] +
            trend_score * weights['trend'] +
            volatility_score * weights['volatility'] +
            availability_score * weights['availability']
        )

        # 统计
        missing_count = self._count_missing_values(df)
        anomalies_count = self._detect_anomalies(df)

        metrics = DataQualityMetrics(
            overall_score=overall_score,
            freshness_score=freshness_score,
            completeness_score=completeness_score,
            accuracy_score=accuracy_score,
            consistency_score=consistency_score,
            trend_score=trend_score,
            volatility_score=volatility_score,
            availability_score=availability_score,
            last_update=datetime.now(),
            data_points=len(data),
            missing_count=missing_count,
            anomalies_count=anomalies_count
        )

        # 保存到历史
        self.quality_history.append(metrics)

        return metrics

    def _to_dataframe(self, data: List[Dict]) -> pd.DataFrame:
        """将数据转换为DataFrame"""
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # 确保日期列存在
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')

        # 确保rate列存在
        if 'rate' not in df.columns and 'hibor_overnight' in df.columns:
            df['rate'] = df['hibor_overnight']

        return df

    def _calculate_freshness_score(self, df: pd.DataFrame) -> float:
        """计算新鲜度评分"""
        if df.empty or 'date' not in df.columns:
            return 0.0

        # 获取最新数据时间
        latest_date = df['date'].max()
        if pd.isna(latest_date):
            return 0.0

        # 计算时间差（小时）
        now = datetime.now()
        if isinstance(latest_date, pd.Timestamp):
            latest_date = latest_date.to_pydatetime()

        age_hours = (now - latest_date).total_seconds() / 3600

        # 评分（0-100）
        if age_hours <= 24:
            return 100.0
        elif age_hours <= 48:
            return 90.0
        elif age_hours <= 72:
            return 80.0
        elif age_hours <= 168:
            return 60.0
        else:
            return 30.0

    def _calculate_completeness_score(self, df: pd.DataFrame) -> float:
        """计算完整性评分"""
        if df.empty:
            return 0.0

        # 计算每列的缺失率
        total_rows = len(df)
        missing_rates = {}

        for col in df.columns:
            if col not in ['date', 'ingested_at']:
                missing_count = df[col].isna().sum()
                missing_rates[col] = missing_count / total_rows

        # 计算总体缺失率
        if not missing_rates:
            return 100.0

        avg_missing_rate = sum(missing_rates.values()) / len(missing_rates)

        # 评分（0-100，缺失率越低分数越高）
        return max(0.0, 100.0 - (avg_missing_rate * 100))

    def _calculate_accuracy_score(self, df: pd.DataFrame) -> float:
        """计算准确性评分"""
        if df.empty or 'rate' not in df.columns:
            return 0.0

        rates = df['rate'].dropna()

        if len(rates) == 0:
            return 0.0

        # 检查数值范围
        valid_rates = rates[(rates >= 0) & (rates <= 50)]

        if len(rates) == 0:
            return 0.0

        # 有效值比例
        valid_ratio = len(valid_rates) / len(rates)

        # 评分（0-100）
        return valid_ratio * 100

    def _calculate_consistency_score(self, df: pd.DataFrame) -> float:
        """计算一致性评分"""
        if df.empty or 'date' not in df.columns:
            return 0.0

        # 检查日期连续性
        df_sorted = df.sort_values('date')

        if len(df_sorted) < 2:
            return 100.0

        # 计算日期间隔
        date_gaps = df_sorted['date'].diff().dt.days

        # 正常间隔为1天（工作日）
        # 计算与正常间隔的偏差
        deviations = abs(date_gaps - 1).fillna(0)

        # 计算一致性指标
        avg_deviation = deviations.mean()

        # 评分（0-100，偏差越小分数越高）
        if avg_deviation <= 0.5:
            return 100.0
        elif avg_deviation <= 1.0:
            return 90.0
        elif avg_deviation <= 2.0:
            return 80.0
        elif avg_deviation <= 3.0:
            return 70.0
        else:
            return 50.0

    def _calculate_trend_score(self, df: pd.DataFrame) -> float:
        """计算趋势评分"""
        if df.empty or 'rate' not in df.columns or len(df) < 5:
            return 80.0  # 数据不足时给中等分数

        rates = df['rate'].dropna()

        if len(rates) < 5:
            return 80.0

        # 计算趋势相关性
        x = np.arange(len(rates))
        y = rates.values

        # 线性回归
        try:
            slope, intercept = np.polyfit(x, y, 1)
            y_pred = slope * x + intercept

            # 计算R²
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

            # 评分（0-100，R²越高分数越高）
            return max(0.0, min(100.0, r_squared * 100))

        except Exception as e:
            self.logger.warning(f"趋势计算失败: {e}")
            return 70.0

    def _calculate_volatility_score(self, df: pd.DataFrame) -> float:
        """计算波动性评分"""
        if df.empty or 'rate' not in df.columns or len(df) < 2:
            return 80.0  # 数据不足时给中等分数

        rates = df['rate'].dropna()

        if len(rates) < 2:
            return 80.0

        # 计算波动性（标准差）
        volatility = rates.std()

        # 计算变异系数
        mean_rate = rates.mean()
        cv = volatility / mean_rate if mean_rate != 0 else 0

        # 评分（0-100，波动性越低分数越高）
        if cv <= 0.05:
            return 100.0
        elif cv <= 0.10:
            return 90.0
        elif cv <= 0.15:
            return 80.0
        elif cv <= 0.20:
            return 70.0
        else:
            return 50.0

    def _calculate_availability_score(self, df: pd.DataFrame) -> float:
        """计算可用性评分"""
        if df.empty:
            return 0.0

        # 基于数据点数量和时间跨度计算
        time_span_days = 0
        if 'date' in df.columns and len(df) > 1:
            dates = pd.to_datetime(df['date'], errors='coerce').dropna()
            if len(dates) > 1:
                time_span_days = (dates.max() - dates.min()).days + 1

        # 期望的数据点数量（假设每天一个数据点）
        expected_points = max(time_span_days, 1)
        actual_points = len(df)

        # 可用性比例
        availability = min(1.0, actual_points / expected_points)

        # 评分（0-100）
        return availability * 100

    def _count_missing_values(self, df: pd.DataFrame) -> int:
        """计算缺失值数量"""
        return df.isna().sum().sum()

    def _detect_anomalies(self, df: pd.DataFrame) -> int:
        """检测异常值"""
        if df.empty or 'rate' not in df.columns:
            return 0

        rates = df['rate'].dropna()

        if len(rates) < 3:
            return 0

        # 使用Z-Score检测异常值
        z_scores = np.abs((rates - rates.mean()) / rates.std())
        anomalies = (z_scores > 3).sum()

        return anomalies

    async def check_quality_thresholds(
        self,
        metrics: DataQualityMetrics
    ) -> List[QualityAlert]:
        """
        检查质量阈值

        Args:
            metrics: 质量指标

        Returns:
            告警列表
        """
        alerts = []

        # 检查各项指标
        checks = [
            (MetricType.FRESHNESS, metrics.freshness_score),
            (MetricType.COMPLETENESS, metrics.completeness_score),
            (MetricType.ACCURACY, metrics.accuracy_score),
            (MetricType.CONSISTENCY, metrics.consistency_score),
            (MetricType.TREND, metrics.trend_score),
            (MetricType.VOLATILITY, metrics.volatility_score),
            (MetricType.AVAILABILITY, metrics.availability_score),
        ]

        for metric_type, score in checks:
            level = self._score_to_quality_level(metric_type, score)

            if level in [QualityLevel.POOR, QualityLevel.CRITICAL]:
                # 生成告警
                alert_id = f"{metric_type.value}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                alert = QualityAlert(
                    id=alert_id,
                    metric_type=metric_type,
                    level=level,
                    message=f"{metric_type.value} 质量{level.value}",
                    timestamp=datetime.now(),
                    value=score,
                    threshold=self._get_threshold(metric_type, level)
                )

                alerts.append(alert)

                # 触发告警
                await self._trigger_alert(alert)

        return alerts

    def _score_to_quality_level(
        self,
        metric_type: MetricType,
        score: float
    ) -> QualityLevel:
        """根据分数获取质量等级"""
        thresholds = self.QUALITY_THRESHOLDS[metric_type]

        if metric_type in [MetricType.VOLATILITY]:
            # 波动性越低越好
            if score <= thresholds['excellent']:
                return QualityLevel.EXCELLENT
            elif score <= thresholds['good']:
                return QualityLevel.GOOD
            elif score <= thresholds['fair']:
                return QualityLevel.FAIR
            elif score <= thresholds['poor']:
                return QualityLevel.POOR
            else:
                return QualityLevel.CRITICAL
        else:
            # 其他指标越高越好
            if score >= thresholds['excellent']:
                return QualityLevel.EXCELLENT
            elif score >= thresholds['good']:
                return QualityLevel.GOOD
            elif score >= thresholds['fair']:
                return QualityLevel.FAIR
            elif score >= thresholds['poor']:
                return QualityLevel.POOR
            else:
                return QualityLevel.CRITICAL

    def _get_threshold(
        self,
        metric_type: MetricType,
        level: QualityLevel
    ) -> float:
        """获取质量等级的阈值"""
        return self.QUALITY_THRESHOLDS[metric_type][level.value]

    async def start_monitoring(self):
        """启动自动监控"""
        if self.monitor_task and not self.monitor_task.done():
            self.logger.warning("监控已在运行")
            return

        self.logger.info("启动HKMA数据质量监控...")
        self.monitor_task = asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self):
        """停止自动监控"""
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

        self.logger.info("已停止数据质量监控")

    async def _monitoring_loop(self):
        """监控循环"""
        self.logger.info("数据质量监控循环已启动")

        while True:
            try:
                # 计算质量指标
                metrics = await self.calculate_quality_metrics()

                # 检查阈值
                await self.check_quality_thresholds(metrics)

                # 记录监控结果
                self.logger.info(
                    f"数据质量评分: {metrics.overall_score:.1f} "
                    f"({metrics.get_quality_level().value})"
                )

                # 保存监控数据
                await self._save_monitor_store()

                # 等待下次监控
                await asyncio.sleep(self.monitor_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"监控循环错误: {e}")
                await asyncio.sleep(60)

    async def _save_monitor_store(self):
        """保存监控数据"""
        try:
            import os
            os.makedirs(os.path.dirname(self.MONITOR_STORE_FILE), exist_ok=True)

            data = {
                'quality_history': [qm.to_dict() for qm in list(self.quality_history)],
                'active_alerts': {k: v.to_dict() for k, v in self.active_alerts.items()},
                'alert_history': [a.to_dict() for a in self.alert_history],
                'updated_at': datetime.now().isoformat()
            }

            with open(self.MONITOR_STORE_FILE, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"保存监控数据失败: {e}")

    def _load_monitor_store(self):
        """加载监控数据"""
        try:
            if os.path.exists(self.MONITOR_STORE_FILE):
                with open(self.MONITOR_STORE_FILE, 'r') as f:
                    data = json.load(f)

                # 加载质量历史
                for qm_data in data.get('quality_history', []):
                    # 这里可以重建DataQualityMetrics对象
                    pass

        except Exception as e:
            self.logger.error(f"加载监控数据失败: {e}")

    async def get_quality_report(self) -> Dict[str, Any]:
        """
        生成质量报告

        Returns:
            质量报告字典
        """
        metrics = await self.calculate_quality_metrics()

        # 质量趋势
        trend = "稳定"
        if len(self.quality_history) >= 2:
            recent_scores = [qm.overall_score for qm in list(self.quality_history)[-5:]]
            if recent_scores[-1] > recent_scores[0] + 5:
                trend = "改善"
            elif recent_scores[-1] < recent_scores[0] - 5:
                trend = "下降"

        return {
            'timestamp': datetime.now().isoformat(),
            'overall_score': metrics.overall_score,
            'quality_level': metrics.get_quality_level().value,
            'metrics': metrics.to_dict(),
            'quality_trend': trend,
            'active_alerts': len(self.active_alerts),
            'total_alerts': len(self.alert_history),
            'data_points': len(self.data_points),
            'recommendations': self._generate_recommendations(metrics)
        }

    def _generate_recommendations(
        self,
        metrics: DataQualityMetrics
    ) -> List[str]:
        """生成改进建议"""
        recommendations = []

        if metrics.freshness_score < 70:
            recommendations.append("数据更新不及时，建议检查数据源连接")

        if metrics.completeness_score < 70:
            recommendations.append("数据缺失较多，建议检查数据提取逻辑")

        if metrics.accuracy_score < 70:
            recommendations.append("数据准确性较低，建议验证数据源")

        if metrics.consistency_score < 70:
            recommendations.append("数据不一致，建议检查数据处理流程")

        if metrics.volatility_score < 70:
            recommendations.append("数据波动性异常，建议检查异常值处理")

        if not recommendations:
            recommendations.append("数据质量良好，保持当前状态")

        return recommendations

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """获取活跃告警"""
        return [alert.to_dict() for alert in self.active_alerts.values()]

    def get_quality_trend(self, days: int = 7) -> Dict[str, Any]:
        """获取质量趋势"""
        if len(self.quality_history) == 0:
            return {'trend': '无数据', 'scores': []}

        # 获取最近N天的数据
        recent_metrics = list(self.quality_history)[-days:] if len(self.quality_history) >= days else list(self.quality_history)

        scores = [qm.overall_score for qm in recent_metrics]

        if len(scores) < 2:
            return {
                'trend': '数据不足',
                'scores': scores,
                'avg_score': scores[0] if scores else 0
            }

        # 计算趋势
        slope = (scores[-1] - scores[0]) / (len(scores) - 1)

        if slope > 1:
            trend = '上升'
        elif slope < -1:
            trend = '下降'
        else:
            trend = '稳定'

        return {
            'trend': trend,
            'scores': scores,
            'avg_score': statistics.mean(scores),
            'min_score': min(scores),
            'max_score': max(scores)
        }


# 全局监控器实例
monitor: Optional[HKMAMonitor] = None


def get_monitor() -> HKMAMonitor:
    """获取全局监控器实例"""
    global monitor
    if monitor is None:
        monitor = HKMAMonitor()
    return monitor


if __name__ == "__main__":
    # 测试代码
    async def test():
        monitor = HKMAMonitor()

        # 添加测试数据
        test_data = [
            {'date': '2023-12-01', 'rate': 0.5},
            {'date': '2023-12-02', 'rate': 0.55},
            {'date': '2023-12-03', 'rate': 0.6},
            {'date': '2023-12-04', 'rate': 0.65},
            {'date': '2023-12-05', 'rate': 0.7},
        ]

        for data in test_data:
            await monitor.add_data_point(data)

        # 生成报告
        report = await monitor.get_quality_report()
        print(json.dumps(report, indent=2, default=str))

    asyncio.run(test())
