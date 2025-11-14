"""
多数据源融合系统 (T197)
========================

提供完整的多数据源融合能力，包括：
- 多源数据对齐
- 数据去重
- 数据补全
- 质量评估
- 冲突解决

Author: Claude Code
Date: 2025-11-09
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple, Set, Callable
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor

from .cache import LRUCache
from .validator import DataValidator, DataValidationResult


class DataSourcePriority(str, Enum):
    """数据源优先级"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    BACKUP = "BACKUP"


class ConflictResolution(str, Enum):
    """冲突解决策略"""
    PRIORITY = "PRIORITY"  # 优先级优先
    LATEST = "LATEST"      # 最新数据优先
    AVERAGE = "AVERAGE"    # 平均值
    MEDIAN = "MEDIAN"      # 中位数
    MANUAL = "MANUAL"      # 手动解决
    REJECT = "REJECT"      # 拒绝数据


class DataType(str, Enum):
    """数据类型"""
    OHLCV = "ohlcv"
    FUNDAMENTAL = "fundamental"
    OPTIONS = "options"
    FUTURES = "futures"
    NEWS = "news"
    ALTERNATIVE = "alternative"


@dataclass
class DataSource:
    """数据源配置"""
    name: str  # 数据源名称
    source_type: str  # 数据源类型
    priority: DataSourcePriority  # 优先级
    reliability_score: float = 1.0  # 可靠性评分 (0-1)
    latency_ms: float = 0.0  # 延迟 (毫秒)
    last_update: Optional[datetime] = None  # 最后更新时间
    is_active: bool = True  # 是否活跃
    supported_types: Set[DataType] = field(default_factory=set)  # 支持的数据类型
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据


@dataclass
class DataRecord:
    """数据记录"""
    symbol: str  # 股票代码
    timestamp: datetime  # 时间戳
    data_type: DataType  # 数据类型
    source: str  # 数据源
    data: Dict[str, Any]  # 原始数据
    quality_score: float = 1.0  # 质量评分
    validation_result: Optional[DataValidationResult] = None  # 验证结果
    merged: bool = False  # 是否已合并
    conflict_resolved: bool = False  # 是否已解决冲突


@dataclass
class FusionResult:
    """融合结果"""
    symbol: str  # 股票代码
    timestamp: datetime  # 时间戳
    data_type: DataType  # 数据类型
    merged_data: Dict[str, Any]  # 融合后的数据
    quality_score: float  # 质量评分
    sources_used: List[str]  # 使用的数据源
    conflicts: List[Dict[str, Any]] = field(default_factory=list)  # 冲突列表
    gaps_filled: List[str] = field(default_factory=list)  # 填补的空缺
    resolution_method: Optional[str] = None  # 解决策略
    last_updated: datetime = field(default_factory=datetime.now)


class DataFusionEngine:
    """
    多数据源融合引擎

    功能：
    1. 注册和管理多个数据源
    2. 实时数据获取和缓存
    3. 数据对齐和去重
    4. 质量评估和验证
    5. 冲突自动解决
    6. 数据补全和插值
    """

    def __init__(
        self,
        cache_size: int = 2000,
        cache_ttl: float = 300.0,
        max_workers: int = 4,
        conflict_threshold: float = 0.05  # 5%的差异认为是冲突
    ):
        self.logger = logging.getLogger("hk_quant_system.fusion")
        self.cache = LRUCache(max_size=cache_size, ttl=cache_ttl)
        self.validator = DataValidator()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.conflict_threshold = conflict_threshold

        # 数据源管理
        self._data_sources: Dict[str, DataSource] = {}
        self._data_fetcher: Dict[str, Any] = {}

        # 冲突解决策略
        self._conflict_resolvers: Dict[str, Callable] = {
            'PRIORITY': self._resolve_by_priority,
            'LATEST': self._resolve_by_latest,
            'AVERAGE': self._resolve_by_average,
            'MEDIAN': self._resolve_by_median,
            'MANUAL': self._resolve_manually,
            'REJECT': self._resolve_by_reject
        }

    def register_data_source(
        self,
        name: str,
        source_type: str,
        fetcher: Any,
        priority: DataSourcePriority = DataSourcePriority.MEDIUM,
        supported_types: Optional[List[DataType]] = None,
        reliability_score: float = 1.0
    ) -> None:
        """
        注册数据源

        Args:
            name: 数据源名称
            source_type: 数据源类型
            fetcher: 数据获取器
            priority: 优先级
            supported_types: 支持的数据类型
            reliability_score: 可靠性评分
        """
        if supported_types is None:
            supported_types = [DataType.OHLCV]

        data_source = DataSource(
            name=name,
            source_type=source_type,
            priority=priority,
            reliability_score=reliability_score,
            supported_types=set(supported_types)
        )

        self._data_sources[name] = data_source
        self._data_fetcher[name] = fetcher

        self.logger.info(
            f"Registered data source: {name} "
            f"(priority={priority.value}, types={supported_types})"
        )

    async def fuse_data(
        self,
        symbol: str,
        data_type: DataType,
        start_time: datetime,
        end_time: datetime,
        resolution: ConflictResolution = ConflictResolution.PRIORITY,
        min_sources: int = 2
    ) -> List[FusionResult]:
        """
        融合多源数据

        Args:
            symbol: 股票代码
            data_type: 数据类型
            start_time: 开始时间
            end_time: 结束时间
            resolution: 冲突解决策略
            min_sources: 最少数据源数

        Returns:
            融合结果列表
        """
        cache_key = f"fusion:{symbol}:{data_type.value}:{start_time.isoformat()}:{end_time.isoformat()}:{resolution.value}"

        # 检查缓存
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        # 获取兼容的数据源
        sources = self._get_compatible_sources(data_type)
        if len(sources) < min_sources:
            self.logger.warning(
                f"Insufficient data sources for {symbol}: "
                f"need {min_sources}, have {len(sources)}"
            )
            return []

        # 并行获取数据
        raw_data = await self._fetch_from_sources(
            sources, symbol, data_type, start_time, end_time
        )

        if not raw_data:
            return []

        # 数据对齐
        aligned_data = self._align_data(raw_data, start_time, end_time)

        # 解决冲突并融合
        fused_results = []
        for timestamp, records in aligned_data.items():
            result = self._merge_records(
                symbol, timestamp, data_type, records, resolution
            )
            if result:
                fused_results.append(result)

        # 填充缺失数据
        filled_results = self._fill_data_gaps(fused_results, start_time, end_time)

        # 缓存结果
        self.cache.set(cache_key, filled_results)

        return filled_results

    async def get_fused_point(
        self,
        symbol: str,
        data_type: DataType,
        timestamp: datetime,
        resolution: ConflictResolution = ConflictResolution.PRIORITY
    ) -> Optional[FusionResult]:
        """
        获取融合数据点

        Args:
            symbol: 股票代码
            data_type: 数据类型
            timestamp: 时间戳
            resolution: 冲突解决策略

        Returns:
            融合结果
        """
        # 获取兼容的数据源
        sources = self._get_compatible_sources(data_type)

        # 获取时间点数据
        records = await self._fetch_point_from_sources(
            sources, symbol, data_type, timestamp
        )

        if not records:
            return None

        # 合并记录
        return self._merge_records(symbol, timestamp, data_type, records, resolution)

    async def compare_sources(
        self,
        symbol: str,
        data_type: DataType,
        start_time: datetime,
        end_time: datetime
    ) -> pd.DataFrame:
        """
        比较不同数据源的数据质量

        Args:
            symbol: 股票代码
            data_type: 数据类型
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            质量比较DataFrame
        """
        sources = self._get_compatible_sources(data_type)
        comparison_data = []

        for source in sources:
            try:
                # 获取数据
                data = await self._fetch_single_source(
                    source, symbol, data_type, start_time, end_time
                )

                if data:
                    # 计算质量指标
                    quality = self._assess_source_quality(data, source)
                    comparison_data.append(quality)
            except Exception as e:
                self.logger.error(f"Error comparing source {source}: {e}")

        return pd.DataFrame(comparison_data)

    async def validate_fusion_quality(
        self,
        fusion_result: FusionResult,
        expected_ranges: Optional[Dict[str, Tuple[float, float]]] = None
    ) -> DataValidationResult:
        """
        验证融合结果质量

        Args:
            fusion_result: 融合结果
            expected_ranges: 期望值范围

        Returns:
            验证结果
        """
        return self.validator.validate_fusion_result(
            fusion_result, expected_ranges
        )

    def _get_compatible_sources(self, data_type: DataType) -> List[str]:
        """获取兼容的数据源"""
        return [
            name for name, source in self._data_sources.items()
            if data_type in source.supported_types and source.is_active
        ]

    async def _fetch_from_sources(
        self,
        sources: List[str],
        symbol: str,
        data_type: DataType,
        start_time: datetime,
        end_time: datetime
    ) -> List[DataRecord]:
        """从多个数据源获取数据"""
        tasks = []
        for source_name in sources:
            task = self._fetch_single_source(
                source_name, symbol, data_type, start_time, end_time
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_records = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Error fetching from {sources[i]}: {result}")
            elif result:
                all_records.extend(result)

        return all_records

    async def _fetch_single_source(
        self,
        source_name: str,
        symbol: str,
        data_type: DataType,
        start_time: datetime,
        end_time: datetime
    ) -> Optional[List[DataRecord]]:
        """从单个数据源获取数据"""
        fetcher = self._data_fetcher.get(source_name)
        if not fetcher:
            return None

        try:
            # 调用数据获取器
            if hasattr(fetcher, 'get_data'):
                raw_data = await fetcher.get_data(symbol, data_type, start_time, end_time)

                # 转换为DataRecord
                records = []
                for item in raw_data:
                    record = DataRecord(
                        symbol=symbol,
                        timestamp=item.get('timestamp', datetime.now()),
                        data_type=data_type,
                        source=source_name,
                        data=item
                    )
                    records.append(record)

                return records
        except Exception as e:
            self.logger.error(f"Error fetching from {source_name}: {e}")

        return None

    async def _fetch_point_from_sources(
        self,
        sources: List[str],
        symbol: str,
        data_type: DataType,
        timestamp: datetime
    ) -> List[DataRecord]:
        """从多个数据源获取单个时间点数据"""
        all_records = []

        for source_name in sources:
            try:
                fetcher = self._data_fetcher.get(source_name)
                if hasattr(fetcher, 'get_point'):
                    item = await fetcher.get_point(symbol, data_type, timestamp)
                    if item:
                        record = DataRecord(
                            symbol=symbol,
                            timestamp=timestamp,
                            data_type=data_type,
                            source=source_name,
                            data=item
                        )
                        all_records.append(record)
            except Exception as e:
                self.logger.error(f"Error fetching point from {source_name}: {e}")

        return all_records

    def _align_data(
        self,
        records: List[DataRecord],
        start_time: datetime,
        end_time: datetime
    ) -> Dict[datetime, List[DataRecord]]:
        """对齐数据"""
        # 按时间戳分组
        aligned = defaultdict(list)
        for record in records:
            # 时间戳四舍五入到分钟
            aligned_ts = record.timestamp.replace(second=0, microsecond=0)
            aligned[aligned_ts].append(record)

        return aligned

    def _merge_records(
        self,
        symbol: str,
        timestamp: datetime,
        data_type: DataType,
        records: List[DataRecord],
        resolution: ConflictResolution
    ) -> Optional[FusionResult]:
        """
        合并数据记录

        Args:
            symbol: 股票代码
            timestamp: 时间戳
            data_type: 数据类型
            records: 数据记录列表
            resolution: 冲突解决策略

        Returns:
            融合结果
        """
        if not records:
            return None

        # 识别冲突
        conflicts = self._identify_conflicts(records)

        # 选择解决策略
        resolver = self._conflict_resolvers.get(resolution.value)

        merged_data = {}
        sources_used = [r.source for r in records]

        try:
            if resolver:
                merged_data = resolver(records, conflicts)
            else:
                # 默认使用优先级策略
                merged_data = self._resolve_by_priority(records, conflicts)

            # 计算质量评分
            quality_score = self._calculate_quality_score(records, conflicts)

            return FusionResult(
                symbol=symbol,
                timestamp=timestamp,
                data_type=data_type,
                merged_data=merged_data,
                quality_score=quality_score,
                sources_used=sources_used,
                conflicts=conflicts,
                resolution_method=resolution.value
            )
        except Exception as e:
            self.logger.error(f"Error merging records: {e}")
            return None

    def _identify_conflicts(self, records: List[DataRecord]) -> List[Dict[str, Any]]:
        """识别数据冲突"""
        if len(records) < 2:
            return []

        conflicts = []

        # 比较数值字段
        numeric_fields = set()
        for record in records:
            numeric_fields.update(
                k for k, v in record.data.items()
                if isinstance(v, (int, float, np.number))
            )

        for field in numeric_fields:
            values = []
            for record in records:
                if field in record.data and record.data[field] is not None:
                    values.append(float(record.data[field]))

            if len(values) >= 2:
                # 检查冲突
                mean_val = np.mean(values)
                max_val = max(values)
                min_val = min(values)

                if mean_val > 0:
                    diff_percent = (max_val - min_val) / mean_val
                    if diff_percent > self.conflict_threshold:
                        conflicts.append({
                            'field': field,
                            'values': values,
                            'mean': mean_val,
                            'min': min_val,
                            'max': max_val,
                            'diff_percent': diff_percent
                        })

        return conflicts

    def _resolve_by_priority(
        self,
        records: List[DataRecord],
        conflicts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """按优先级解决冲突"""
        # 按优先级排序
        sorted_records = sorted(
            records,
            key=lambda r: self._data_sources[r.source].priority.value,
            reverse=True
        )

        # 使用最高优先级的数据
        merged = sorted_records[0].data.copy()

        # 对于有冲突的字段，使用加权平均
        for conflict in conflicts:
            field = conflict['field']
            values = conflict['values']
            sources = [r.source for r in records if field in r.data]

            if len(sources) >= 2:
                # 计算权重
                weights = [
                    self._data_sources[s].reliability_score
                    for s in sources
                ]

                # 加权平均
                weighted_values = [v * w for v, w in zip(values, weights)]
                merged_value = sum(weighted_values) / sum(weights)
                merged[field] = merged_value

        return merged

    def _resolve_by_latest(
        self,
        records: List[DataRecord],
        conflicts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """按最新数据解决冲突"""
        # 按最后更新时间排序
        sorted_records = sorted(
            records,
            key=lambda r: self._data_sources[r.source].last_update or datetime.min,
            reverse=True
        )

        merged = sorted_records[0].data.copy()

        for conflict in conflicts:
            field = conflict['field']
            # 使用最新数据
            for record in sorted_records:
                if field in record.data:
                    merged[field] = record.data[field]
                    break

        return merged

    def _resolve_by_average(
        self,
        records: List[DataRecord],
        conflicts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """按平均值解决冲突"""
        merged = {}

        # 合并所有数据
        for record in records:
            merged.update(record.data)

        # 对冲突字段使用平均值
        for conflict in conflicts:
            field = conflict['field']
            values = conflict['values']
            merged[field] = np.mean(values)

        return merged

    def _resolve_by_median(
        self,
        records: List[DataRecord],
        conflicts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """按中位数解决冲突"""
        merged = {}

        # 合并所有数据
        for record in records:
            merged.update(record.data)

        # 对冲突字段使用中位数
        for conflict in conflicts:
            field = conflict['field']
            values = conflict['values']
            merged[field] = np.median(values)

        return merged

    def _resolve_manually(
        self,
        records: List[DataRecord],
        conflicts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """手动解决冲突 (需要用户输入)"""
        self.logger.warning("Manual conflict resolution requested")
        # 暂时使用优先级策略
        return self._resolve_by_priority(records, conflicts)

    def _resolve_by_reject(
        self,
        records: List[DataRecord],
        conflicts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """拒绝冲突数据"""
        if conflicts:
            self.logger.warning("Rejecting conflicting data")
            return {}
        # 如果没有冲突，返回第一个记录
        return records[0].data if records else {}

    def _fill_data_gaps(
        self,
        results: List[FusionResult],
        start_time: datetime,
        end_time: datetime
    ) -> List[FusionResult]:
        """填充数据空缺"""
        if not results:
            return results

        # 按时间排序
        results.sort(key=lambda r: r.timestamp)

        # 使用前向填充和线性插值
        for i in range(1, len(results)):
            prev_result = results[i - 1]
            curr_result = results[i]
            time_diff = (curr_result.timestamp - prev_result.timestamp).total_seconds()

            # 如果时间差超过5分钟，尝试插值
            if time_diff > 300:  # 5分钟
                interpolated = self._interpolate_data(
                    prev_result, curr_result, time_diff
                )
                if interpolated:
                    results.insert(i, interpolated)
                    i += 1  # 跳过刚插入的数据

        return results

    def _interpolate_data(
        self,
        prev: FusionResult,
        curr: FusionResult,
        time_diff: float
    ) -> Optional[FusionResult]:
        """线性插值"""
        # 这里实现插值逻辑
        # 简化实现
        try:
            interpolated_data = {}
            for key in prev.merged_data:
                if key in curr.merged_data:
                    prev_val = prev.merged_data[key]
                    curr_val = curr.merged_data[key]

                    if isinstance(prev_val, (int, float)) and isinstance(curr_val, (int, float)):
                        # 线性插值
                        alpha = 0.5
                        interpolated_data[key] = alpha * prev_val + (1 - alpha) * curr_val

            if interpolated_data:
                return FusionResult(
                    symbol=prev.symbol,
                    timestamp=prev.timestamp + timedelta(seconds=time_diff / 2),
                    data_type=prev.data_type,
                    merged_data=interpolated_data,
                    quality_score=(prev.quality_score + curr.quality_score) / 2,
                    sources_used=list(set(prev.sources_used + curr.sources_used)),
                    gaps_filled=["interpolation"]
                )
        except Exception as e:
            self.logger.error(f"Error interpolating data: {e}")

        return None

    def _calculate_quality_score(
        self,
        records: List[DataRecord],
        conflicts: List[Dict[str, Any]]
    ) -> float:
        """计算质量评分"""
        if not records:
            return 0.0

        # 基础评分
        base_score = 1.0

        # 数据源可靠性
        reliability_scores = [
            self._data_sources[r.source].reliability_score
            for r in records
        ]
        avg_reliability = np.mean(reliability_scores)

        # 冲突惩罚
        conflict_penalty = len(conflicts) * 0.1

        # 计算最终评分
        quality = base_score * avg_reliability - conflict_penalty

        return max(0.0, min(1.0, quality))

    def _assess_source_quality(
        self,
        data: List[DataRecord],
        source_name: str
    ) -> Dict[str, Any]:
        """评估数据源质量"""
        source = self._data_sources[source_name]

        # 计算数据完整性
        total_records = len(data)
        complete_records = sum(
            1 for r in data
            if all(v is not None for v in r.data.values())
        )
        completeness = complete_records / total_records if total_records > 0 else 0

        # 计算数据新鲜度
        now = datetime.now()
        freshness_scores = []
        for r in data:
            age = (now - r.timestamp).total_seconds()
            freshness = max(0, 1 - age / 86400)  # 1天为满分
            freshness_scores.append(freshness)
        avg_freshness = np.mean(freshness_scores)

        return {
            'source': source_name,
            'type': source.source_type,
            'priority': source.priority.value,
            'reliability': source.reliability_score,
            'total_records': total_records,
            'completeness': completeness,
            'freshness': avg_freshness,
            'overall_score': (source.reliability_score + completeness + avg_freshness) / 3
        }

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        active_sources = sum(1 for s in self._data_sources.values() if s.is_active)

        return {
            "status": "healthy" if active_sources > 0 else "degraded",
            "total_sources": len(self._data_sources),
            "active_sources": active_sources,
            "cache_size": len(self.cache._cache),
            "sources": [
                {
                    "name": s.name,
                    "type": s.source_type,
                    "priority": s.priority.value,
                    "active": s.is_active
                }
                for s in self._data_sources.values()
            ],
            "last_check": datetime.now().isoformat()
        }


# 辅助函数
async def fuse_multi_source_data(
    symbol: str,
    data_type: DataType,
    start_time: datetime,
    end_time: datetime
) -> List[FusionResult]:
    """
    多源数据融合的便捷函数

    Args:
        symbol: 股票代码
        data_type: 数据类型
        start_time: 开始时间
        end_time: 结束时间

    Returns:
        融合结果列表
    """
    engine = DataFusionEngine()
    return await engine.fuse_data(symbol, data_type, start_time, end_time)


if __name__ == "__main__":
    # 测试代码
    async def test():
        engine = DataFusionEngine()

        # 测试健康检查
        health = await engine.health_check()
        print("Health check:", health)

    asyncio.run(test())
