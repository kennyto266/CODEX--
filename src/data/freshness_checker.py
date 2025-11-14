"""
Phase 8b - T353: 数据新鲜度检查系统
实现数据更新时间检查、延迟监控和缺失数据检测
"""

__all__ = [
    "FreshnessChecker",
    "FreshnessResult",
    "UpdateStatus",
    "DataLatencyMonitor",
    "UpdateFrequencyAnalyzer",
    "MissingDataDetector",
    "FreshnessAlertManager"
]

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path

logger = logging.getLogger('quant_system.data.freshness_checker')


class UpdateStatus(Enum):
    """更新状态"""
    UP_TO_DATE = "up_to_date"
    SLIGHTLY_STALE = "slightly_stale"
    STALE = "stale"
    VERY_STALE = "very_stale"
    UNKNOWN = "unknown"
    ERROR = "error"


@dataclass
class FreshnessResult:
    """数据新鲜度结果"""
    symbol: str
    timestamp: datetime
    last_update: Optional[datetime]
    status: UpdateStatus
    age_hours: float
    expected_frequency: str
    freshness_score: float
    missing_periods: List[Tuple[datetime, datetime]] = field(default_factory=list)
    anomalies: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'status': self.status.value,
            'age_hours': self.age_hours,
            'expected_frequency': self.expected_frequency,
            'freshness_score': self.freshness_score,
            'missing_periods': [(start.isoformat(), end.isoformat())
                               for start, end in self.missing_periods],
            'anomalies': self.anomalies,
            'recommendations': self.recommendations,
            'metadata': self.metadata
        }


class DataLatencyMonitor:
    """数据延迟监控器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化数据延迟监控器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.thresholds = self.config.get('thresholds', {
            'real_time': 0.5,  # 30分钟
            'daily': 2.0,  # 2小时
            'weekly': 24.0,  # 24小时
            'monthly': 72.0  # 72小时
        })

    def check_update_latency(self, last_update: Optional[datetime],
                           expected_frequency: str) -> Dict[str, Any]:
        """
        检查更新延迟

        Args:
            last_update: 最后更新时间
            expected_frequency: 预期更新频率

        Returns:
            延迟检查结果
        """
        result = {
            'is_within_threshold': False,
            'latency_hours': 0.0,
            'threshold_hours': 0.0,
            'severity': 'none',
            'status': UpdateStatus.UP_TO_DATE
        }

        try:
            if last_update is None:
                result['status'] = UpdateStatus.UNKNOWN
                result['severity'] = 'critical'
                return result

            now = datetime.utcnow()
            latency = (now - last_update).total_seconds() / 3600
            result['latency_hours'] = latency

            # 获取阈值
            threshold = self.thresholds.get(expected_frequency, 24.0)
            result['threshold_hours'] = threshold

            # 判断状态
            if latency <= threshold * 0.5:
                result['status'] = UpdateStatus.UP_TO_DATE
                result['severity'] = 'none'
            elif latency <= threshold:
                result['status'] = UpdateStatus.SLIGHTLY_STALE
                result['severity'] = 'low'
            elif latency <= threshold * 2:
                result['status'] = UpdateStatus.STALE
                result['severity'] = 'medium'
            else:
                result['status'] = UpdateStatus.VERY_STALE
                result['severity'] = 'high'

            result['is_within_threshold'] = latency <= threshold

        except Exception as e:
            logger.error(f"延迟检查失败: {str(e)}")
            result['status'] = UpdateStatus.ERROR
            result['severity'] = 'critical'

        return result

    def monitor_multiple_sources(self, sources: Dict[str, Optional[datetime]],
                                expected_frequency: str) -> Dict[str, Any]:
        """
        监控多个数据源的延迟

        Args:
            sources: 数据源字典 {source_name: last_update}
            expected_frequency: 预期更新频率

        Returns:
            监控结果
        """
        result = {
            'sources_monitored': len(sources),
            'overall_status': UpdateStatus.UP_TO_DATE,
            'source_statuses': {},
            'stale_sources': [],
            'most_recent': None,
            'least_recent': None
        }

        try:
            source_results = {}
            for source_name, last_update in sources.items():
                source_result = self.check_update_latency(last_update, expected_frequency)
                source_results[source_name] = source_result
                result['source_statuses'][source_name] = source_result

                if source_result['status'] in [UpdateStatus.STALE, UpdateStatus.VERY_STALE]:
                    result['stale_sources'].append(source_name)

            # 找到最新和最旧的数据
            valid_updates = [dt for dt in sources.values() if dt is not None]
            if valid_updates:
                result['most_recent'] = max(valid_updates)
                result['least_recent'] = min(valid_updates)

            # 整体状态
            if result['stale_sources']:
                if len(result['stale_sources']) == len(sources):
                    result['overall_status'] = UpdateStatus.VERY_STALE
                elif len(result['stale_sources']) > len(sources) / 2:
                    result['overall_status'] = UpdateStatus.STALE
                else:
                    result['overall_status'] = UpdateStatus.SLIGHTLY_STALE

        except Exception as e:
            logger.error(f"多源延迟监控失败: {str(e)}")
            result['overall_status'] = UpdateStatus.ERROR

        return result


class UpdateFrequencyAnalyzer:
    """更新频率分析器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化更新频率分析器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.frequency_rules = self.config.get('frequency_rules', {
            'realtime': {'min_interval': 0.1, 'max_interval': 1.0, 'unit': 'hours'},
            'hourly': {'min_interval': 0.5, 'max_interval': 2.0, 'unit': 'hours'},
            'daily': {'min_interval': 20, 'max_interval': 30, 'unit': 'hours'},
            'weekly': {'min_interval': 6, 'max_interval': 8, 'unit': 'days'},
            'monthly': {'min_interval': 28, 'max_interval': 35, 'unit': 'days'}
        })

    def analyze_update_pattern(self, timestamps: List[datetime]) -> Dict[str, Any]:
        """
        分析更新模式

        Args:
            timestamps: 时间戳列表

        Returns:
            分析结果
        """
        result = {
            'pattern_type': 'unknown',
            'average_interval': 0.0,
            'interval_std': 0.0,
            'consistency_score': 0.0,
            'is_regular': False,
            'anomalies': []
        }

        try:
            if len(timestamps) < 2:
                return result

            # 排序时间戳
            sorted_timestamps = sorted(timestamps)

            # 计算间隔
            intervals = []
            for i in range(1, len(sorted_timestamps)):
                interval = (sorted_timestamps[i] - sorted_timestamps[i-1]).total_seconds() / 3600
                intervals.append(interval)

            if not intervals:
                return result

            # 统计间隔
            avg_interval = np.mean(intervals)
            std_interval = np.std(intervals)
            cv = std_interval / avg_interval if avg_interval > 0 else float('inf')

            # 识别模式
            pattern_type = self._identify_pattern(avg_interval)

            # 一致性分数 (CV越小越一致)
            consistency_score = max(0.0, 1.0 - min(cv, 1.0))

            result.update({
                'pattern_type': pattern_type,
                'average_interval': avg_interval,
                'interval_std': std_interval,
                'consistency_score': consistency_score,
                'is_regular': consistency_score >= 0.7
            })

            # 检测异常
            anomalies = self._detect_interval_anomalies(intervals, avg_interval)
            result['anomalies'] = anomalies

        except Exception as e:
            logger.error(f"更新模式分析失败: {str(e)}")

        return result

    def _identify_pattern(self, avg_interval_hours: float) -> str:
        """识别更新模式"""
        if avg_interval_hours <= 1:
            return 'hourly'
        elif avg_interval_hours <= 24:
            return 'daily'
        elif avg_interval_hours <= 168:  # 7天
            return 'weekly'
        elif avg_interval_hours <= 720:  # 30天
            return 'monthly'
        else:
            return 'irregular'

    def _detect_interval_anomalies(self, intervals: List[float],
                                  avg_interval: float) -> List[Dict[str, Any]]:
        """检测间隔异常"""
        anomalies = []

        if len(intervals) < 3:
            return anomalies

        std_interval = np.std(intervals)
        threshold = avg_interval + 2 * std_interval

        for i, interval in enumerate(intervals):
            if interval > threshold:
                anomalies.append({
                    'type': 'unusually_long_interval',
                    'index': i,
                    'interval': interval,
                    'description': f"间隔异常长: {interval:.2f}小时 (平均: {avg_interval:.2f}小时)",
                    'severity': 'medium' if interval < 2 * threshold else 'high'
                })

        return anomalies

    def compare_with_expected(self, timestamps: List[datetime],
                             expected_frequency: str) -> Dict[str, Any]:
        """
        与预期频率比较

        Args:
            timestamps: 时间戳列表
            expected_frequency: 预期频率

        Returns:
            比较结果
        """
        result = {
            'is_compliant': False,
            'compliance_score': 0.0,
            'deviation': 0.0,
            'expected_interval': 0.0,
            'actual_interval': 0.0
        }

        try:
            if expected_frequency not in self.frequency_rules:
                return result

            expected = self.frequency_rules[expected_frequency]
            expected_interval = expected['min_interval']
            result['expected_interval'] = expected_interval

            # 分析实际模式
            pattern_analysis = self.analyze_update_pattern(timestamps)
            actual_interval = pattern_analysis['average_interval']
            result['actual_interval'] = actual_interval

            # 计算偏差
            deviation = abs(actual_interval - expected_interval) / expected_interval
            result['deviation'] = deviation

            # 合规性分数
            if deviation <= 0.1:
                result['compliance_score'] = 1.0
                result['is_compliant'] = True
            elif deviation <= 0.3:
                result['compliance_score'] = 0.7
                result['is_compliant'] = True
            else:
                result['compliance_score'] = 0.3

        except Exception as e:
            logger.error(f"频率比较失败: {str(e)}")

        return result


class MissingDataDetector:
    """缺失数据检测器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化缺失数据检测器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.gap_thresholds = self.config.get('gap_thresholds', {
            'real_time': 0.5,  # 30分钟
            'daily': 4.0,  # 4小时
            'weekly': 48.0,  # 48小时
            'monthly': 168.0  # 1周
        })

    def detect_missing_periods(self, timestamps: List[datetime],
                              expected_frequency: str) -> List[Tuple[datetime, datetime]]:
        """
        检测缺失时间段

        Args:
            timestamps: 时间戳列表
            expected_frequency: 预期频率

        Returns:
            缺失时间段列表 [(start, end), ...]
        """
        missing_periods = []

        try:
            if len(timestamps) < 2:
                return missing_periods

            # 排序时间戳
            sorted_timestamps = sorted(timestamps)

            # 获取阈值
            threshold = self.gap_thresholds.get(expected_frequency, 24.0)

            # 检测间隔超过阈值的期间
            for i in range(len(sorted_timestamps) - 1):
                current = sorted_timestamps[i]
                next_ts = sorted_timestamps[i + 1]
                gap_hours = (next_ts - current).total_seconds() / 3600

                if gap_hours > threshold:
                    missing_periods.append((current, next_ts))

        except Exception as e:
            logger.error(f"缺失期检测失败: {str(e)}")

        return missing_periods

    def detect_data_gaps(self, data: pd.DataFrame,
                        expected_frequency: str) -> Dict[str, Any]:
        """
        检测数据缺口

        Args:
            data: 数据DataFrame
            expected_frequency: 预期频率

        Returns:
            缺口检测结果
        """
        result = {
            'has_gaps': False,
            'gap_count': 0,
            'total_missing_hours': 0.0,
            'largest_gap': None,
            'gap_periods': [],
            'completeness': 1.0
        }

        try:
            if data.empty or len(data) < 2:
                return result

            # 获取时间戳
            if 'date' in data.columns:
                timestamps = pd.to_datetime(data['date']).tolist()
            else:
                timestamps = data.index.tolist()

            # 检测缺失期间
            missing_periods = self.detect_missing_periods(timestamps, expected_frequency)
            result['gap_periods'] = missing_periods
            result['gap_count'] = len(missing_periods)

            if missing_periods:
                result['has_gaps'] = True
                result['largest_gap'] = max(
                    missing_periods,
                    key=lambda x: (x[1] - x[0]).total_seconds()
                )

                # 计算总缺失时间
                total_missing = 0
                for start, end in missing_periods:
                    total_missing += (end - start).total_seconds() / 3600

                result['total_missing_hours'] = total_missing

            # 计算完整性
            expected_data_points = self._estimate_expected_data_points(
                data, expected_frequency
            )
            actual_data_points = len(data)
            result['completeness'] = actual_data_points / expected_data_points if expected_data_points > 0 else 0

        except Exception as e:
            logger.error(f"数据缺口检测失败: {str(e)}")

        return result

    def _estimate_expected_data_points(self, data: pd.DataFrame,
                                      expected_frequency: str) -> int:
        """估算预期数据点数"""
        if len(data) < 2:
            return len(data)

        # 获取时间范围
        if 'date' in data.columns:
            timestamps = pd.to_datetime(data['date'])
            time_range = (timestamps.max() - timestamps.min()).total_seconds()
        else:
            time_range = (data.index.max() - data.index.min()).total_seconds()

        # 转换为小时
        time_range_hours = time_range / 3600

        # 根据频率估算数据点数
        hours_per_point = {
            'real_time': 0.5,
            'hourly': 1.0,
            'daily': 24.0,
            'weekly': 168.0,
            'monthly': 720.0
        }

        expected_hours_per_point = hours_per_point.get(expected_frequency, 24.0)
        return max(1, int(time_range_hours / expected_hours_per_point))


class FreshnessAlertManager:
    """新鲜度告警管理器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化新鲜度告警管理器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.alert_rules = self.config.get('alert_rules', {
            UpdateStatus.UP_TO_DATE: {'enabled': False, 'channels': []},
            UpdateStatus.SLIGHTLY_STALE: {'enabled': True, 'channels': ['log']},
            UpdateStatus.STALE: {'enabled': True, 'channels': ['log', 'email']},
            UpdateStatus.VERY_STALE: {'enabled': True, 'channels': ['log', 'email', 'webhook']},
            UpdateStatus.UNKNOWN: {'enabled': True, 'channels': ['log', 'email']},
            UpdateStatus.ERROR: {'enabled': True, 'channels': ['log', 'email', 'webhook']}
        })
        self.alert_history = []
        self.alert_cooldown = self.config.get('alert_cooldown', 3600)  # 1小时

    async def check_and_alert(self, result: FreshnessResult) -> List[Dict[str, Any]]:
        """
        检查并发送告警

        Args:
            result: 新鲜度结果

        Returns:
            触发的告警列表
        """
        alerts = []

        try:
            alert_config = self.alert_rules.get(result.status)

            if not alert_config or not alert_config.get('enabled', False):
                return alerts

            # 检查冷却期
            if self._is_in_cooldown(result.symbol, result.status):
                return alerts

            # 创建告警
            alert = {
                'symbol': result.symbol,
                'status': result.status.value,
                'severity': self._get_severity(result.status),
                'message': self._generate_alert_message(result),
                'timestamp': datetime.utcnow().isoformat(),
                'actions_taken': []
            }

            # 执行告警动作
            for channel in alert_config.get('channels', []):
                action_result = await self._send_alert(channel, alert)
                alert['actions_taken'].append({
                    'channel': channel,
                    'success': action_result['success'],
                    'details': action_result
                })

            alerts.append(alert)
            self.alert_history.append(alert)

            # 清理历史（保留最近100条）
            if len(self.alert_history) > 100:
                self.alert_history = self.alert_history[-100:]

        except Exception as e:
            logger.error(f"告警检查失败: {str(e)}")

        return alerts

    def _is_in_cooldown(self, symbol: str, status: UpdateStatus) -> bool:
        """检查是否在冷却期"""
        # 简化的冷却检查
        # 实际实现中应该使用时间窗口查询
        return False

    def _get_severity(self, status: UpdateStatus) -> str:
        """获取告警严重程度"""
        severity_map = {
            UpdateStatus.UP_TO_DATE: 'info',
            UpdateStatus.SLIGHTLY_STALE: 'low',
            UpdateStatus.STALE: 'medium',
            UpdateStatus.VERY_STALE: 'high',
            UpdateStatus.UNKNOWN: 'medium',
            UpdateStatus.ERROR: 'critical'
        }
        return severity_map.get(status, 'unknown')

    def _generate_alert_message(self, result: FreshnessResult) -> str:
        """生成告警消息"""
        return (
            f"数据新鲜度告警: {result.symbol}\n"
            f"状态: {result.status.value}\n"
            f"数据年龄: {result.age_hours:.1f}小时\n"
            f"预期频率: {result.expected_frequency}\n"
            f"新鲜度分数: {result.freshness_score:.2f}\n"
            f"建议: {', '.join(result.recommendations) if result.recommendations else '无'}"
        )

    async def _send_alert(self, channel: str, alert: Dict[str, Any]) -> Dict[str, Any]:
        """发送告警"""
        try:
            if channel == 'log':
                logger.warning(alert['message'])
                return {'channel': channel, 'success': True}
            elif channel == 'email':
                # TODO: 实现邮件发送
                logger.info(f"模拟发送邮件告警: {alert['message']}")
                return {'channel': channel, 'success': True, 'action': 'email_sent'}
            elif channel == 'webhook':
                # TODO: 实现webhook发送
                logger.info(f"模拟发送webhook: {alert['message']}")
                return {'channel': channel, 'success': True, 'action': 'webhook_sent'}
            else:
                return {'channel': channel, 'success': False, 'error': 'unknown_channel'}
        except Exception as e:
            logger.error(f"告警发送失败 ({channel}): {str(e)}")
            return {'channel': channel, 'success': False, 'error': str(e)}


class FreshnessChecker:
    """数据新鲜度检查系统"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化新鲜度检查器

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 初始化组件
        self.latency_monitor = DataLatencyMonitor(
            self.config.get('latency', {})
        )
        self.frequency_analyzer = UpdateFrequencyAnalyzer(
            self.config.get('frequency', {})
        )
        self.missing_detector = MissingDataDetector(
            self.config.get('missing', {})
        )
        self.alert_manager = FreshnessAlertManager(
            self.config.get('alert', {})
        )

        # 配置
        self.default_frequencies = self.config.get('default_frequencies', {
            '0700.HK': 'daily',
            '0388.HK': 'daily',
            'default': 'daily'
        })

        # 统计信息
        self.stats = {
            'total_checks': 0,
            'alerts_sent': 0,
            'stale_detected': 0,
            'gaps_detected': 0,
            'status_distribution': {
                'up_to_date': 0,
                'slightly_stale': 0,
                'stale': 0,
                'very_stale': 0,
                'unknown': 0
            }
        }

        logger.info("数据新鲜度检查器初始化完成")

    async def check(self, symbol: str, data: Optional[pd.DataFrame] = None,
                   last_update: Optional[datetime] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> FreshnessResult:
        """
        执行数据新鲜度检查

        Args:
            symbol: 股票代码
            data: 数据DataFrame (可选)
            last_update: 最后更新时间 (可选)
            metadata: 元数据 (可选)

        Returns:
            新鲜度检查结果
        """
        self.stats['total_checks'] += 1

        try:
            # 确定预期频率
            expected_frequency = self._get_expected_frequency(symbol)

            # 如果没有提供last_update，从数据中推断
            if last_update is None and data is not None:
                last_update = self._extract_last_update(data)

            # 延迟检查
            latency_result = self.latency_monitor.check_update_latency(
                last_update, expected_frequency
            )

            # 更新频率分析
            frequency_analysis = {'pattern_type': 'unknown', 'consistency_score': 0.0}
            if data is not None:
                timestamps = self._extract_timestamps(data)
                if timestamps:
                    frequency_analysis = self.frequency_analyzer.analyze_update_pattern(
                        timestamps
                    )
                    frequency_compliance = self.frequency_analyzer.compare_with_expected(
                        timestamps, expected_frequency
                    )

            # 缺失数据检测
            missing_data = {'has_gaps': False, 'gap_count': 0}
            if data is not None:
                missing_data = self.missing_detector.detect_data_gaps(
                    data, expected_frequency
                )

            # 计算新鲜度分数
            freshness_score = self._calculate_freshness_score(
                latency_result, frequency_analysis, missing_data
            )

            # 提取缺失期间
            missing_periods = []
            if 'gap_periods' in missing_data:
                missing_periods = missing_data['gap_periods']

            # 生成建议
            recommendations = self._generate_recommendations(
                latency_result, frequency_analysis, missing_data
            )

            # 创建结果
            result = FreshnessResult(
                symbol=symbol,
                timestamp=datetime.utcnow(),
                last_update=last_update,
                status=latency_result['status'],
                age_hours=latency_result.get('latency_hours', 0.0),
                expected_frequency=expected_frequency,
                freshness_score=freshness_score,
                missing_periods=missing_periods,
                anomalies=self._collect_anomalies(latency_result, frequency_analysis, missing_data),
                recommendations=recommendations,
                metadata={
                    'latency': latency_result,
                    'frequency': frequency_analysis,
                    'missing': missing_data
                }
            )

            # 更新统计
            self.stats['status_distribution'][result.status.value] += 1

            if result.status in [UpdateStatus.STALE, UpdateStatus.VERY_STALE]:
                self.stats['stale_detected'] += 1

            if missing_data.get('has_gaps', False):
                self.stats['gaps_detected'] += 1

            # 检查告警
            alerts = await self.alert_manager.check_and_alert(result)
            if alerts:
                self.stats['alerts_sent'] += len(alerts)

            return result

        except Exception as e:
            logger.error(f"新鲜度检查失败: {str(e)}", exc_info=True)
            self.stats['status_distribution']['unknown'] += 1
            return FreshnessResult(
                symbol=symbol,
                timestamp=datetime.utcnow(),
                last_update=last_update,
                status=UpdateStatus.ERROR,
                age_hours=0.0,
                expected_frequency='unknown',
                freshness_score=0.0,
                anomalies=[{'type': 'error', 'description': str(e)}],
                recommendations=['检查系统状态']
            )

    def _get_expected_frequency(self, symbol: str) -> str:
        """获取预期频率"""
        return self.default_frequencies.get(
            symbol,
            self.default_frequencies.get('default', 'daily')
        )

    def _extract_last_update(self, data: pd.DataFrame) -> Optional[datetime]:
        """从数据中提取最后更新时间"""
        try:
            if 'date' in data.columns:
                last_date = pd.to_datetime(data['date']).max()
                return last_date
            elif hasattr(data.index, 'max'):
                last_date = data.index.max()
                if isinstance(last_date, (pd.Timestamp, datetime)):
                    return last_date
        except:
            pass
        return None

    def _extract_timestamps(self, data: pd.DataFrame) -> List[datetime]:
        """从数据中提取时间戳"""
        timestamps = []

        try:
            if 'date' in data.columns:
                timestamps = pd.to_datetime(data['date']).tolist()
            elif hasattr(data.index, 'tolist'):
                timestamps = data.index.tolist()
                timestamps = [t for t in timestamps if isinstance(t, (pd.Timestamp, datetime))]
        except:
            pass

        return sorted(timestamps)

    def _calculate_freshness_score(self, latency_result: Dict[str, Any],
                                  frequency_analysis: Dict[str, Any],
                                  missing_data: Dict[str, Any]) -> float:
        """计算新鲜度分数"""
        # 基于延迟的分数 (0-1)
        latency_score = 0.0
        if latency_result.get('is_within_threshold', False):
            latency_score = 1.0
        else:
            # 距离阈值的远近程度
            latency = latency_result.get('latency_hours', 0)
            threshold = latency_result.get('threshold_hours', 1)
            latency_score = max(0.0, 1.0 - (latency / threshold))

        # 基于频率一致性的分数
        frequency_score = frequency_analysis.get('consistency_score', 0.0)

        # 基于完整性的分数
        completeness = missing_data.get('completeness', 1.0)
        gap_penalty = min(0.3, missing_data.get('gap_count', 0) * 0.1)
        completeness_score = max(0.0, completeness - gap_penalty)

        # 加权平均
        weights = {'latency': 0.5, 'frequency': 0.3, 'completeness': 0.2}
        freshness_score = (
            latency_score * weights['latency'] +
            frequency_score * weights['frequency'] +
            completeness_score * weights['completeness']
        )

        return min(1.0, max(0.0, freshness_score))

    def _generate_recommendations(self, latency_result: Dict[str, Any],
                                 frequency_analysis: Dict[str, Any],
                                 missing_data: Dict[str, Any]) -> List[str]:
        """生成建议"""
        recommendations = []

        # 基于延迟的建议
        if not latency_result.get('is_within_threshold', True):
            recommendations.append("数据更新延迟，建议检查数据源连接")

        # 基于频率的建议
        if frequency_analysis.get('consistency_score', 1.0) < 0.5:
            recommendations.append("数据更新模式不规律，建议优化数据采集频率")

        # 基于缺失数据的建议
        if missing_data.get('has_gaps', False):
            gap_count = missing_data.get('gap_count', 0)
            recommendations.append(f"检测到 {gap_count} 个数据缺口，建议增加数据采集频率")

        # 基于完整性的建议
        completeness = missing_data.get('completeness', 1.0)
        if completeness < 0.8:
            recommendations.append(f"数据完整性较低 ({completeness:.1%})，建议检查数据源质量")

        if not recommendations:
            recommendations.append("数据新鲜度良好")

        return recommendations

    def _collect_anomalies(self, latency_result: Dict[str, Any],
                          frequency_analysis: Dict[str, Any],
                          missing_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """收集异常"""
        anomalies = []

        # 延迟异常
        if not latency_result.get('is_within_threshold', True):
            anomalies.append({
                'type': 'update_latency',
                'description': f"更新延迟: {latency_result.get('latency_hours', 0):.1f}小时",
                'severity': latency_result.get('severity', 'medium')
            })

        # 频率异常
        for anomaly in frequency_analysis.get('anomalies', []):
            anomalies.append(anomaly)

        # 缺失数据异常
        if missing_data.get('has_gaps', False):
            anomalies.append({
                'type': 'missing_data',
                'description': f"存在 {missing_data.get('gap_count', 0)} 个数据缺口",
                'severity': 'medium'
            })

        return anomalies

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()

    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total_checks': 0,
            'alerts_sent': 0,
            'stale_detected': 0,
            'gaps_detected': 0,
            'status_distribution': {
                'up_to_date': 0,
                'slightly_stale': 0,
                'stale': 0,
                'very_stale': 0,
                'unknown': 0
            }
        }


# 便捷函数
async def check_data_freshness(symbol: str, data: Optional[pd.DataFrame] = None,
                              last_update: Optional[datetime] = None,
                              config: Optional[Dict[str, Any]] = None) -> FreshnessResult:
    """
    便捷的新鲜度检查函数

    Args:
        symbol: 股票代码
        data: 数据
        last_update: 最后更新时间
        config: 配置

    Returns:
        新鲜度检查结果
    """
    checker = FreshnessChecker(config)
    return await checker.check(symbol, data, last_update)


def create_freshness_checker(config: Optional[Dict[str, Any]] = None) -> FreshnessChecker:
    """
    创建新鲜度检查器实例

    Args:
        config: 配置字典

    Returns:
        新鲜度检查器实例
    """
    return FreshnessChecker(config)


# 使用示例
if __name__ == "__main__":
    import asyncio

    async def test_freshness_checker():
        # 创建测试数据
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=50, freq='D')

        # 正常数据
        normal_data = pd.DataFrame({
            'date': dates,
            'open': 100 + np.random.normal(0, 2, 50),
            'high': 102 + np.random.normal(0, 2, 50),
            'low': 98 + np.random.normal(0, 2, 50),
            'close': 101 + np.random.normal(0, 2, 50),
            'volume': 1000 + np.random.randint(0, 500, 50)
        })

        # 缺失一些数据
        missing_dates = dates[5:8]
        normal_data = normal_data[~normal_data['date'].isin(missing_dates)]

        # 设置最后更新时间
        last_update = datetime.utcnow() - timedelta(hours=1)

        # 创建新鲜度检查器
        config = {
            'latency': {
                'thresholds': {
                    'daily': 4.0
                }
            },
            'alert': {
                'alert_rules': {
                    'stale': {'enabled': True, 'channels': ['log']},
                    'very_stale': {'enabled': True, 'channels': ['log', 'email']}
                }
            }
        }

        checker = FreshnessChecker(config)

        # 执行检查
        print("执行数据新鲜度检查...")
        result = await checker.check('0700.HK', normal_data, last_update)

        # 打印结果
        print(f"\n=== 数据新鲜度检查结果 ===")
        print(f"股票代码: {result.symbol}")
        print(f"状态: {result.status.value}")
        print(f"新鲜度分数: {result.freshness_score:.2f}")
        print(f"数据年龄: {result.age_hours:.1f}小时")
        print(f"预期频率: {result.expected_frequency}")

        print(f"\n检测到的异常: {len(result.anomalies)}")
        for i, anomaly in enumerate(result.anomalies, 1):
            print(f"  {i}. {anomaly['description']} (严重程度: {anomaly['severity']})")

        print(f"\n建议:")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"  {i}. {rec}")

        # 获取统计信息
        stats = checker.get_stats()
        print(f"\n检查统计: {stats}")

        # 测试多源监控
        print(f"\n=== 多源延迟监控 ===")
        sources = {
            'yahoo': datetime.utcnow() - timedelta(hours=1),
            'alpha_vantage': datetime.utcnow() - timedelta(hours=2),
            'bloomberg': datetime.utcnow() - timedelta(minutes=30)
        }
        monitor_result = checker.latency_monitor.monitor_multiple_sources(sources, 'daily')
        print(f"整体状态: {monitor_result['overall_status'].value}")
        print(f"陈旧源: {', '.join(monitor_result['stale_sources'])}")

    # 运行测试
    asyncio.run(test_freshness_checker())
