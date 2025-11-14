"""
Phase 8b - T352: 跨源数据验证系统
实现多数据源对比、数据一致性检查和差异分析
"""

__all__ = [
    "CrossSourceVerification",
    "VerificationResult",
    "SourceComparison",
    "DataSource",
    "ConsistencyChecker",
    "DifferenceAnalyzer",
    "PriorityResolver"
]

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import hashlib
from difflib import SequenceMatcher

logger = logging.getLogger('quant_system.data.cross_source_verification')


class VerificationStatus(Enum):
    """验证状态"""
    CONSISTENT = "consistent"
    INCONSISTENT = "inconsistent"
    PARTIAL_MATCH = "partial_match"
    UNKNOWN = "unknown"
    ERROR = "error"


class DataSource(Enum):
    """数据源枚举"""
    YAHOO_FINANCE = "yahoo_finance"
    ALPHA_VANTAGE = "alpha_vantage"
    FINNHUB = "finnhub"
    HKEX = "hkex"
    FUTU = "futu"
    BLOOMBERG = "bloomberg"
    REFINITIV = "refinitiv"
    MANUAL = "manual"
    DATABASE = "database"
    CACHE = "cache"


@dataclass
class VerificationResult:
    """跨源验证结果"""
    symbol: str
    timestamp: datetime
    status: VerificationStatus
    consistency_score: float
    sources_compared: List[str]
    differences: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status.value,
            'consistency_score': self.consistency_score,
            'sources_compared': self.sources_compared,
            'differences': self.differences,
            'recommendations': self.recommendations,
            'metadata': self.metadata
        }


@dataclass
class SourceComparison:
    """数据源对比结果"""
    source1: str
    source2: str
    fields_compared: List[str]
    match_percentage: float
    exact_matches: int
    partial_matches: int
    total_mismatches: int
    field_differences: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'source1': self.source1,
            'source2': self.source2,
            'fields_compared': self.fields_compared,
            'match_percentage': self.match_percentage,
            'exact_matches': self.exact_matches,
            'partial_matches': self.partial_matches,
            'total_mismatches': self.total_mismatches,
            'field_differences': self.field_differences
        }


class ConsistencyChecker:
    """一致性检查器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化一致性检查器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.tolerance = self.config.get('tolerance', {
            'price': 0.01,  # 1%
            'volume': 0.05,  # 5%
            'percentage': 0.001  # 0.1%
        })
        self.minimum_matches = self.config.get('minimum_matches', 0.7)

    def check_ohlcv_consistency(self, data1: pd.DataFrame, data2: pd.DataFrame) -> Dict[str, Any]:
        """
        检查OHLCV数据一致性

        Args:
            data1: 数据源1
            data2: 数据源2

        Returns:
            一致性检查结果
        """
        result = {
            'is_consistent': False,
            'overall_score': 0.0,
            'field_scores': {},
            'differences': [],
            'matching_periods': 0
        }

        try:
            # 找到共同的时间段
            common_dates = data1.index.intersection(data2.index)

            if len(common_dates) < 10:
                result['differences'].append({
                    'type': 'insufficient_data',
                    'description': f"共同数据点不足: {len(common_dates)}",
                    'severity': 'high'
                })
                return result

            result['matching_periods'] = len(common_dates)

            # 检查OHLCV字段
            ohlcv_fields = ['open', 'high', 'low', 'close', 'volume']
            total_score = 0.0
            valid_fields = 0

            for field in ohlcv_fields:
                if field in data1.columns and field in data2.columns:
                    field_data1 = data1.loc[common_dates, field].dropna()
                    field_data2 = data2.loc[common_dates, field].dropna()

                    if len(field_data1) > 0 and len(field_data2) > 0:
                        field_score = self._calculate_field_consistency(
                            field_data1, field_data2, field
                        )
                        result['field_scores'][field] = field_score
                        total_score += field_score
                        valid_fields += 1

            if valid_fields > 0:
                result['overall_score'] = total_score / valid_fields

            result['is_consistent'] = result['overall_score'] >= self.minimum_matches

            # 记录差异
            if not result['is_consistent']:
                result['differences'].append({
                    'type': 'low_consistency',
                    'description': f"一致性分数过低: {result['overall_score']:.2f}",
                    'severity': 'high'
                })

        except Exception as e:
            logger.error(f"OHLCV一致性检查失败: {str(e)}")
            result['differences'].append({
                'type': 'error',
                'description': str(e),
                'severity': 'critical'
            })

        return result

    def _calculate_field_consistency(self, data1: pd.Series, data2: pd.Series,
                                    field_type: str) -> float:
        """计算字段一致性"""
        if field_type in self.tolerance:
            tolerance = self.tolerance[field_type]
        else:
            tolerance = 0.01

        try:
            # 计算相对差异
            relative_diff = np.abs((data1 - data2) / data2).replace([np.inf, -np.inf], np.nan)

            # 去除缺失值
            relative_diff = relative_diff.dropna()

            if len(relative_diff) == 0:
                return 0.0

            # 计算在容忍范围内的比例
            within_tolerance = (relative_diff <= tolerance).sum()
            match_percentage = within_tolerance / len(relative_diff)

            # 返回0-1的分数
            return match_percentage

        except Exception as e:
            logger.error(f"字段 {field_type} 一致性计算失败: {str(e)}")
            return 0.0

    def check_metadata_consistency(self, data1: Dict, data2: Dict) -> Dict[str, Any]:
        """
        检查元数据一致性

        Args:
            data1: 元数据1
            data2: 元数据2

        Returns:
            元数据一致性结果
        """
        result = {
            'is_consistent': True,
            'match_percentage': 0.0,
            'differences': []
        }

        try:
            keys1 = set(data1.keys())
            keys2 = set(data2.keys())

            common_keys = keys1.intersection(keys2)
            all_keys = keys1.union(keys2)

            if len(all_keys) == 0:
                result['match_percentage'] = 1.0
                return result

            matches = 0
            total = len(all_keys)

            # 检查共同键
            for key in common_keys:
                value1 = data1.get(key)
                value2 = data2.get(key)

                if value1 == value2:
                    matches += 1
                else:
                    # 检查是否数值接近
                    if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
                        relative_diff = abs(value1 - value2) / max(abs(value2), 1)
                        if relative_diff < 0.01:  # 1%容忍度
                            matches += 0.5
                            result['differences'].append({
                                'key': key,
                                'type': 'numeric_slight_difference',
                                'value1': value1,
                                'value2': value2,
                                'severity': 'low'
                            })
                    else:
                        result['differences'].append({
                            'key': key,
                            'type': 'value_mismatch',
                            'value1': str(value1),
                            'value2': str(value2),
                            'severity': 'medium'
                        })

            # 检查缺失键
            missing_in_2 = keys1 - keys2
            missing_in_1 = keys2 - keys1

            for key in missing_in_2:
                result['differences'].append({
                    'key': key,
                    'type': 'missing_in_source2',
                    'severity': 'high'
                })

            for key in missing_in_1:
                result['differences'].append({
                    'key': key,
                    'type': 'missing_in_source1',
                    'severity': 'high'
                })

            result['match_percentage'] = matches / total
            result['is_consistent'] = result['match_percentage'] >= 0.9

        except Exception as e:
            logger.error(f"元数据一致性检查失败: {str(e)}")
            result['is_consistent'] = False
            result['differences'].append({
                'type': 'error',
                'description': str(e),
                'severity': 'critical'
            })

        return result


class DifferenceAnalyzer:
    """差异分析器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化差异分析器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.significance_threshold = self.config.get('significance_threshold', 0.05)

    def analyze_differences(self, diff1: pd.DataFrame, diff2: pd.DataFrame,
                           source1: str, source2: str) -> List[Dict[str, Any]]:
        """
        分析两个数据源的差异

        Args:
            diff1: 数据源1
            diff2: 数据源2
            source1: 数据源1名称
            source2: 数据源2名称

        Returns:
            差异分析结果列表
        """
        differences = []

        try:
            # 找到共同时间点
            common_dates = diff1.index.intersection(diff2.index)

            if len(common_dates) == 0:
                differences.append({
                    'type': 'no_common_data',
                    'description': f"数据源 {source1} 和 {source2} 无共同时间段",
                    'severity': 'critical'
                })
                return differences

            # 分析每个字段的差异
            common_columns = diff1.columns.intersection(diff2.columns)

            for column in common_columns:
                col_diff = self._analyze_column_differences(
                    diff1.loc[common_dates, column],
                    diff2.loc[common_dates, column],
                    source1,
                    source2,
                    column
                )
                differences.extend(col_diff)

            # 分析结构性差异
            self._analyze_structural_differences(diff1, diff2, source1, source2, differences)

        except Exception as e:
            logger.error(f"差异分析失败: {str(e)}")
            differences.append({
                'type': 'error',
                'description': str(e),
                'severity': 'critical'
            })

        return differences

    def _analyze_column_differences(self, col1: pd.Series, col2: pd.Series,
                                   source1: str, source2: str,
                                   column: str) -> List[Dict[str, Any]]:
        """分析列差异"""
        differences = []

        try:
            # 找到共同时间点
            common_index = col1.index.intersection(col2.index)

            if len(common_index) == 0:
                return differences

            col1_common = col1.loc[common_index].dropna()
            col2_common = col2.loc[common_index].dropna()

            if len(col1_common) == 0 or len(col2_common) == 0:
                return differences

            # 计算统计差异
            diff = col1_common - col2_common

            # 识别显著差异
            mean_diff = diff.mean()
            std_diff = diff.std()
            max_diff = diff.abs().max()
            median_diff = diff.median()

            # 显著差异判断
            if abs(median_diff) > self.significance_threshold:
                differences.append({
                    'type': 'value_bias',
                    'column': column,
                    'source1': source1,
                    'source2': source2,
                    'description': f"数据存在系统性偏差，中位数差异: {median_diff:.4f}",
                    'statistics': {
                        'mean_difference': mean_diff,
                        'median_difference': median_diff,
                        'std_difference': std_diff,
                        'max_abs_difference': max_diff
                    },
                    'severity': 'high' if abs(median_diff) > 0.1 else 'medium'
                })

            # 检查异常值
            z_scores = np.abs(stats.zscore(diff.dropna()))
            outlier_threshold = 3.0
            outliers = z_scores > outlier_threshold

            if outliers.sum() > 0:
                differences.append({
                    'type': 'anomalous_differences',
                    'column': column,
                    'source1': source1,
                    'source2': source2,
                    'description': f"发现 {outliers.sum()} 个异常差异点",
                    'outlier_count': outliers.sum(),
                    'severity': 'medium'
                })

            # 时间延迟分析
            correlation = col1_common.corr(col2_common)
            if correlation < 0.5:
                differences.append({
                    'type': 'low_correlation',
                    'column': column,
                    'source1': source1,
                    'source2': source2,
                    'description': f"相关性过低: {correlation:.2f}",
                    'correlation': correlation,
                    'severity': 'high' if correlation < 0.3 else 'medium'
                })

        except Exception as e:
            logger.error(f"列 {column} 差异分析失败: {str(e)}")

        return differences

    def _analyze_structural_differences(self, diff1: pd.DataFrame, diff2: pd.DataFrame,
                                       source1: str, source2: str,
                                       differences: List[Dict[str, Any]]):
        """分析结构性差异"""
        try:
            # 数据完整性差异
            completeness1 = 1 - diff1.isnull().sum().sum() / (len(diff1) * len(diff1.columns))
            completeness2 = 1 - diff2.isnull().sum().sum() / (len(diff2) * len(diff2.columns))

            if abs(completeness1 - completeness2) > 0.1:
                differences.append({
                    'type': 'completeness_difference',
                    'source1': source1,
                    'source2': source2,
                    'description': f"数据完整性差异: {completeness1:.2%} vs {completeness2:.2%}",
                    'completeness1': completeness1,
                    'completeness2': completeness2,
                    'severity': 'medium'
                })

            # 时间范围差异
            date_range1 = (diff1.index.max() - diff1.index.min()).days
            date_range2 = (diff2.index.max() - diff2.index.min()).days

            if abs(date_range1 - date_range2) > 30:
                differences.append({
                    'type': 'date_range_difference',
                    'source1': source1,
                    'source2': source2,
                    'description': f"时间范围差异: {date_range1}天 vs {date_range2}天",
                    'date_range1': date_range1,
                    'date_range2': date_range2,
                    'severity': 'low'
                })

            # 频率差异
            freq1 = self._detect_frequency(diff1.index)
            freq2 = self._detect_frequency(diff2.index)

            if freq1 != freq2:
                differences.append({
                    'type': 'frequency_difference',
                    'source1': source1,
                    'source2': source2,
                    'description': f"数据频率差异: {freq1} vs {freq2}",
                    'frequency1': freq1,
                    'frequency2': freq2,
                    'severity': 'medium'
                })

        except Exception as e:
            logger.error(f"结构性差异分析失败: {str(e)}")

    def _detect_frequency(self, index: pd.DatetimeIndex) -> str:
        """检测时间频率"""
        if len(index) < 2:
            return 'unknown'

        diffs = index.to_series().diff().dropna()
        median_diff = diffs.median()

        if median_diff <= timedelta(days=1):
            return 'daily'
        elif median_diff <= timedelta(days=7):
            return 'weekly'
        elif median_diff <= timedelta(days=30):
            return 'monthly'
        elif median_diff <= timedelta(days=90):
            return 'quarterly'
        else:
            return 'yearly'


class PriorityResolver:
    """优先级解析器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化优先级解析器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.source_priorities = self.config.get('source_priorities', {
            DataSource.BLOOMBERG: 10,
            DataSource.REFINITIV: 9,
            DataSource.HKEX: 8,
            DataSource.YAHOO_FINANCE: 7,
            DataSource.ALPHA_VANTAGE: 6,
            DataSource.FINNHUB: 5,
            DataSource.FUTU: 5,
            DataSource.DATABASE: 4,
            DataSource.CACHE: 3,
            DataSource.MANUAL: 1
        })

    def resolve_conflict(self, symbol: str, data_sources: Dict[str, pd.DataFrame],
                        conflict_type: str = 'value') -> Dict[str, Any]:
        """
        解决数据冲突

        Args:
            symbol: 股票代码
            data_sources: 数据源字典 {source_name: data}
            conflict_type: 冲突类型

        Returns:
            冲突解决结果
        """
        result = {
            'symbol': symbol,
            'conflict_type': conflict_type,
            'resolution_strategy': 'priority_vote',
            'resolved_data': None,
            'confidence': 0.0,
            'source_votes': {},
            'explanation': ''
        }

        try:
            if len(data_sources) < 2:
                result['explanation'] = "数据源不足，无法解决冲突"
                return result

            if conflict_type == 'value':
                result = self._resolve_value_conflict(symbol, data_sources, result)

        except Exception as e:
            logger.error(f"冲突解决失败: {str(e)}")
            result['explanation'] = f"解决过程出错: {str(e)}"

        return result

    def _resolve_value_conflict(self, symbol: str, data_sources: Dict[str, pd.DataFrame],
                               result: Dict[str, Any]) -> Dict[str, Any]:
        """解决数值冲突"""
        # 找到共同的字段和时间
        common_columns = None
        common_index = None

        for source, data in data_sources.items():
            if common_columns is None:
                common_columns = set(data.columns)
            else:
                common_columns = common_columns.intersection(set(data.columns))

            if common_index is None:
                common_index = set(data.index)
            else:
                common_index = common_index.intersection(set(data.index))

        if not common_columns or not common_index:
            result['explanation'] = "无共同字段或时间点"
            return result

        common_columns = list(common_columns)
        common_index = list(common_index)

        if len(common_index) < 10:
            result['explanation'] = "共同数据点不足"
            return result

        # 按优先级投票
        for column in common_columns:
            column_data = {}
            for source, data in data_sources.items():
                source_priority = self._get_source_priority(source)
                if source in data_sources:
                    values = data.loc[common_index, column].dropna()
                    if len(values) > 0:
                        # 计算加权平均
                        column_data[source] = {
                            'values': values,
                            'weight': source_priority,
                            'count': len(values)
                        }

            if len(column_data) > 0:
                # 使用加权中位数（更稳健）
                resolved_values = self._calculate_weighted_median(column_data)
                result['resolved_data'][column] = resolved_values

        result['resolution_strategy'] = 'weighted_median'
        result['confidence'] = self._calculate_resolution_confidence(data_sources)
        result['explanation'] = f"基于 {len(data_sources)} 个数据源的加权中位数"

        return result

    def _get_source_priority(self, source: str) -> int:
        """获取数据源优先级"""
        try:
            source_enum = DataSource(source.lower())
            return self.source_priorities.get(source_enum, 5)
        except:
            return 5

    def _calculate_weighted_median(self, column_data: Dict[str, Dict]) -> pd.Series:
        """计算加权中位数"""
        all_values = []
        all_weights = []

        for source, info in column_data.items():
            values = info['values']
            weight = info['weight']
            for value in values:
                all_values.append(value)
                all_weights.append(weight)

        if not all_values:
            return pd.Series([])

        # 转换为DataFrame进行加权排序
        df = pd.DataFrame({'value': all_values, 'weight': all_weights})
        df = df.sort_values('value')
        df['cumulative_weight'] = df['weight'].cumsum()
        total_weight = df['weight'].sum()

        # 找到中位数位置
        median_position = total_weight / 2
        median_idx = (df['cumulative_weight'] >= median_position).idxmax()

        return df.loc[median_idx, 'value']

    def _calculate_resolution_confidence(self, data_sources: Dict[str, pd.DataFrame]) -> float:
        """计算解决方案置信度"""
        if len(data_sources) < 2:
            return 0.0

        # 简化的置信度计算
        # 基于数据源数量和数据一致性
        source_count_score = min(1.0, len(data_sources) / 3)
        return source_count_score


class CrossSourceVerification:
    """跨源数据验证系统"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化跨源验证系统

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 初始化组件
        self.consistency_checker = ConsistencyChecker(
            self.config.get('consistency', {})
        )
        self.difference_analyzer = DifferenceAnalyzer(
            self.config.get('difference', {})
        )
        self.priority_resolver = PriorityResolver(
            self.config.get('priority', {})
        )

        # 配置
        self.min_sources = self.config.get('min_sources', 2)
        self.parallel_comparison = self.config.get('parallel_comparison', True)

        # 统计信息
        self.stats = {
            'total_verifications': 0,
            'consistent_sources': 0,
            'inconsistent_sources': 0,
            'resolutions_made': 0,
            'comparison_stats': {}
        }

        logger.info("跨源验证系统初始化完成")

    async def verify(self, symbol: str, data_sources: Dict[str, pd.DataFrame]) -> VerificationResult:
        """
        执行跨源验证

        Args:
            symbol: 股票代码
            data_sources: 数据源字典 {source_name: data}

        Returns:
            验证结果
        """
        self.stats['total_verifications'] += 1

        if len(data_sources) < self.min_sources:
            return VerificationResult(
                symbol=symbol,
                timestamp=datetime.utcnow(),
                status=VerificationStatus.UNKNOWN,
                consistency_score=0.0,
                sources_compared=list(data_sources.keys()),
                differences=[{
                    'type': 'insufficient_sources',
                    'description': f"数据源不足: {len(data_sources)} < {self.min_sources}",
                    'severity': 'critical'
                }],
                recommendations=['增加数据源数量']
            )

        try:
            # 并行或串行比较
            if self.parallel_comparison and len(data_sources) > 2:
                comparisons = await self._parallel_compare_sources(symbol, data_sources)
            else:
                comparisons = await self._sequential_compare_sources(symbol, data_sources)

            # 汇总结果
            overall_consistency, all_differences = self._aggregate_results(comparisons)

            # 生成建议
            recommendations = self._generate_recommendations(all_differences)

            # 自动解决冲突
            resolved_data = None
            if len(all_differences) > 0:
                resolution = self.priority_resolver.resolve_conflict(
                    symbol, data_sources
                )
                if resolution['resolved_data'] is not None:
                    self.stats['resolutions_made'] += 1
                    resolved_data = resolution

            # 更新统计
            if overall_consistency >= 0.8:
                self.stats['consistent_sources'] += 1
            else:
                self.stats['inconsistent_sources'] += 1

            return VerificationResult(
                symbol=symbol,
                timestamp=datetime.utcnow(),
                status=VerificationStatus.CONSISTENT if overall_consistency >= 0.8
                      else VerificationStatus.INCONSISTENT,
                consistency_score=overall_consistency,
                sources_compared=list(data_sources.keys()),
                differences=all_differences,
                recommendations=recommendations,
                metadata={
                    'comparisons': [c.to_dict() for c in comparisons],
                    'resolution': resolved_data
                }
            )

        except Exception as e:
            logger.error(f"跨源验证失败: {str(e)}")
            self.stats['inconsistent_sources'] += 1
            return VerificationResult(
                symbol=symbol,
                timestamp=datetime.utcnow(),
                status=VerificationStatus.ERROR,
                consistency_score=0.0,
                sources_compared=list(data_sources.keys()),
                differences=[{
                    'type': 'error',
                    'description': str(e),
                    'severity': 'critical'
                }]
            )

    async def _parallel_compare_sources(self, symbol: str,
                                       data_sources: Dict[str, pd.DataFrame]) -> List[SourceComparison]:
        """并行比较数据源"""
        source_names = list(data_sources.keys())
        tasks = []

        # 创建所有对比任务
        for i in range(len(source_names)):
            for j in range(i + 1, len(source_names)):
                source1 = source_names[i]
                source2 = source_names[j]
                task = asyncio.create_task(
                    self._compare_two_sources(
                        symbol, source1, data_sources[source1], source2, data_sources[source2]
                    )
                )
                tasks.append(task)

        # 等待所有任务完成
        comparisons = await asyncio.gather(*tasks)
        return [c for c in comparisons if c is not None]

    async def _sequential_compare_sources(self, symbol: str,
                                         data_sources: Dict[str, pd.DataFrame]) -> List[SourceComparison]:
        """串行比较数据源"""
        comparisons = []
        source_names = list(data_sources.keys())

        for i in range(len(source_names)):
            for j in range(i + 1, len(source_names)):
                comparison = await self._compare_two_sources(
                    symbol, source_names[i], data_sources[source_names[i]],
                    source_names[j], data_sources[source_names[j]]
                )
                if comparison:
                    comparisons.append(comparison)

        return comparisons

    async def _compare_two_sources(self, symbol: str, source1: str, data1: pd.DataFrame,
                                  source2: str, data2: pd.DataFrame) -> Optional[SourceComparison]:
        """比较两个数据源"""
        try:
            # 一致性检查
            consistency = self.consistency_checker.check_ohlcv_consistency(data1, data2)

            # 差异分析
            differences = self.difference_analyzer.analyze_differences(
                data1, data2, source1, source2
            )

            # 统计匹配
            total_checks = len(consistency.get('field_scores', {}))
            exact_matches = sum(1 for score in consistency.get('field_scores', {}).values()
                              if score >= 0.99)
            partial_matches = sum(1 for score in consistency.get('field_scores', {}).values()
                                if 0.5 <= score < 0.99)
            total_mismatches = total_checks - exact_matches - partial_matches

            match_percentage = consistency.get('overall_score', 0.0)

            return SourceComparison(
                source1=source1,
                source2=source2,
                fields_compared=list(consistency.get('field_scores', {}).keys()),
                match_percentage=match_percentage,
                exact_matches=exact_matches,
                partial_matches=partial_matches,
                total_mismatches=total_mismatches,
                field_differences=consistency
            )

        except Exception as e:
            logger.error(f"数据源 {source1} vs {source2} 比较失败: {str(e)}")
            return None

    def _aggregate_results(self, comparisons: List[SourceComparison]) -> Tuple[float, List[Dict[str, Any]]]:
        """汇总验证结果"""
        if not comparisons:
            return 0.0, []

        # 计算整体一致性分数
        total_score = sum(c.match_percentage for c in comparisons)
        overall_consistency = total_score / len(comparisons)

        # 汇总所有差异
        all_differences = []
        for comparison in comparisons:
            for field, score in comparison.field_differences.get('field_scores', {}).items():
                if score < 0.7:
                    all_differences.append({
                        'type': 'field_inconsistency',
                        'source1': comparison.source1,
                        'source2': comparison.source2,
                        'field': field,
                        'score': score,
                        'description': f"字段 {field} 一致性不足: {score:.2f}",
                        'severity': 'high' if score < 0.5 else 'medium'
                    })

            # 添加字段差异详情
            for diff in comparison.field_differences.get('differences', []):
                all_differences.append(diff)

        return overall_consistency, all_differences

    def _generate_recommendations(self, differences: List[Dict[str, Any]]) -> List[str]:
        """生成建议"""
        recommendations = []

        if not differences:
            return ["数据源间一致性良好，无需特殊处理"]

        # 基于差异类型生成建议
        diff_types = {}
        for diff in differences:
            diff_type = diff.get('type', 'unknown')
            diff_types[diff_type] = diff_types.get(diff_type, 0) + 1

        if 'field_inconsistency' in diff_types:
            recommendations.append("检查数据源质量，考虑使用数据清洗或过滤")

        if 'value_bias' in diff_types:
            recommendations.append("发现系统性偏差，建议使用数据标准化")

        if 'anomalous_differences' in diff_types:
            recommendations.append("检测到异常值，建议进行异常值处理")

        if 'completeness_difference' in diff_types:
            recommendations.append("数据完整性差异，建议选择更可靠的数据源")

        if 'no_common_data' in diff_types:
            recommendations.append("数据源间无重叠时间，建议扩展时间范围")

        if not recommendations:
            recommendations.append("建议进行人工审查以确定最佳数据源")

        return recommendations

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()

    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total_verifications': 0,
            'consistent_sources': 0,
            'inconsistent_sources': 0,
            'resolutions_made': 0,
            'comparison_stats': {}
        }


# 便捷函数
async def verify_cross_sources(symbol: str, data_sources: Dict[str, pd.DataFrame],
                              config: Optional[Dict[str, Any]] = None) -> VerificationResult:
    """
    便捷的跨源验证函数

    Args:
        symbol: 股票代码
        data_sources: 数据源字典
        config: 配置

    Returns:
        验证结果
    """
    verifier = CrossSourceVerification(config)
    return await verifier.verify(symbol, data_sources)


def create_cross_source_verifier(config: Optional[Dict[str, Any]] = None) -> CrossSourceVerification:
    """
    创建跨源验证器实例

    Args:
        config: 配置字典

    Returns:
        跨源验证器实例
    """
    return CrossSourceVerification(config)


# 使用示例
if __name__ == "__main__":
    import asyncio

    async def test_cross_source_verification():
        # 创建模拟数据源
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=100, freq='D')

        # 数据源1 - Yahoo Finance
        source1_data = pd.DataFrame({
            'open': 100 + np.random.normal(0, 2, 100),
            'high': 102 + np.random.normal(0, 2, 100),
            'low': 98 + np.random.normal(0, 2, 100),
            'close': 101 + np.random.normal(0, 2, 100),
            'volume': 1000 + np.random.randint(0, 500, 100)
        }, index=dates)

        # 数据源2 - Alpha Vantage (有细微差异)
        source2_data = source1_data.copy()
        source2_data['close'] = source1_data['close'] * 1.002  # 0.2%偏差
        source2_data.loc[50:52, 'volume'] = np.nan  # 缺失数据

        # 数据源3 - Bloomberg (更高质量)
        source3_data = source1_data.copy() * 0.999  # 0.1%偏差

        data_sources = {
            'yahoo_finance': source1_data,
            'alpha_vantage': source2_data,
            'bloomberg': source3_data
        }

        # 创建跨源验证器
        config = {
            'min_sources': 2,
            'parallel_comparison': True,
            'consistency': {
                'tolerance': {
                    'price': 0.005,  # 0.5%
                    'volume': 0.05
                },
                'minimum_matches': 0.7
            },
            'priority': {
                'source_priorities': {
                    'bloomberg': 10,
                    'yahoo_finance': 7,
                    'alpha_vantage': 6
                }
            }
        }

        verifier = CrossSourceVerification(config)

        # 执行验证
        print("执行跨源验证...")
        result = await verifier.verify('0700.HK', data_sources)

        # 打印结果
        print(f"\n=== 跨源验证结果 ===")
        print(f"股票代码: {result.symbol}")
        print(f"验证状态: {result.status.value}")
        print(f"一致性分数: {result.consistency_score:.2f}")
        print(f"数据源: {', '.join(result.sources_compared)}")

        print(f"\n差异数量: {len(result.differences)}")
        for i, diff in enumerate(result.differences[:5], 1):
            print(f"  {i}. {diff['description']} (严重程度: {diff['severity']})")

        print(f"\n建议:")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"  {i}. {rec}")

        # 获取统计信息
        stats = verifier.get_stats()
        print(f"\n验证统计: {stats}")

        # 测试冲突解决
        print(f"\n=== 冲突解决测试 ===")
        resolution = verifier.priority_resolver.resolve_conflict(
            '0700.HK', data_sources
        )
        print(f"解决策略: {resolution['resolution_strategy']}")
        print(f"置信度: {resolution['confidence']:.2f}")
        print(f"解释: {resolution['explanation']}")

    # 运行测试
    asyncio.run(test_cross_source_verification())
