#!/usr/bin/env python3
"""
內存優化工具 - T089
提供數據流式處理、內存監控和優化功能
"""

import pandas as pd
import numpy as np
import psutil
import gc
from typing import Iterator, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MemoryOptimizer:
    """內存優化器 - 減少內存使用並支持數據流"""

    def __init__(self, max_memory_mb: float = 2048):
        """
        初始化內存優化器

        Args:
            max_memory_mb: 最大內存使用量 (MB)
        """
        self.max_memory_mb = max_memory_mb
        self.initial_memory = self.get_memory_usage()
        self.peak_memory = self.initial_memory

    def get_memory_usage(self) -> Dict[str, float]:
        """獲取當前內存使用情況"""
        process = psutil.Process()
        memory_info = process.memory_info()
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,
            'vms_mb': memory_info.vms / 1024 / 1024,
            'percent': process.memory_percent()
        }

    def check_memory_threshold(self) -> bool:
        """檢查是否超過內存閾值"""
        current = self.get_memory_usage()
        return current['rss_mb'] < self.max_memory_mb

    def update_peak_memory(self):
        """更新峰值內存使用"""
        current = self.get_memory_usage()
        self.peak_memory = max(self.peak_memory['rss_mb'], current['rss_mb'])

    def force_garbage_collection(self):
        """強制垃圾回收"""
        collected = gc.collect()
        logger.debug(f"垃圾回收完成，回收 {collected} 個對象")
        return collected

    def optimize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        優化DataFrame以減少內存使用

        技術:
        1. 轉換數據類型
        2. 釋放未使用的內存
        3. 設置分類變量
        """
        if df.empty:
            return df

        # 記錄原始大小
        original_memory = df.memory_usage(deep=True).sum() / 1024 / 1024

        # 優化數字類型
        for col in df.select_dtypes(include=['int64']).columns:
            col_min = df[col].min()
            col_max = df[col].max()

            if col_min >= 0:
                if col_max < 255:
                    df[col] = df[col].astype('uint8')
                elif col_max < 65535:
                    df[col] = df[col].astype('uint16')
                elif col_max < 4294967295:
                    df[col] = df[col].astype('uint32')
            else:
                if col_min > -128 and col_max < 127:
                    df[col] = df[col].astype('int8')
                elif col_min > -32768 and col_max < 32767:
                    df[col] = df[col].astype('int16')
                elif col_min > -2147483648 and col_max < 2147483647:
                    df[col] = df[col].astype('int32')

        # 優化浮點類型
        for col in df.select_dtypes(include=['float64']).columns:
            df[col] = pd.to_numeric(df[col], downcast='float')

        # 優化對象類型
        for col in df.select_dtypes(include=['object']).columns:
            if df[col].nunique() / len(df) < 0.5:  # 如果唯一值較少，轉換為分類
                df[col] = df[col].astype('category')

        # 計算優化後大小
        optimized_memory = df.memory_usage(deep=True).sum() / 1024 / 1024
        reduction = (1 - optimized_memory / original_memory) * 100

        logger.debug(f"DataFrame優化: {original_memory:.2f} MB -> {optimized_memory:.2f} MB (減少 {reduction:.1f}%)")

        return df

    def stream_dataframe(self, df: pd.DataFrame, chunk_size: int = 10000) -> Iterator[pd.DataFrame]:
        """
        流式處理大型DataFrame

        Args:
            df: 原始DataFrame
            chunk_size: 塊大小

        Yields:
            DataFrame分塊
        """
        if df.empty:
            return

        for i in range(0, len(df), chunk_size):
            yield df.iloc[i:i + chunk_size]
            self.update_peak_memory()

    def memory_efficient_merge(self, dataframes: Dict[str, pd.DataFrame], on: str, how: str = 'inner') -> pd.DataFrame:
        """
        內存高效的DataFrame合併

        策略:
        1. 先排序減少內存使用
        2. 逐個合併釋放不需要的DataFrame
        """
        if not dataframes:
            return pd.DataFrame()

        # 轉換為列表
        dfs = list(dataframes.values())
        result = dfs[0]

        # 優化第一個DataFrame
        result = self.optimize_dataframe(result)

        # 逐個合併其餘DataFrame
        for df in dfs[1:]:
            # 優化要合併的DataFrame
            df = self.optimize_dataframe(df)

            # 合併
            result = pd.merge(result, df, on=on, how=how, suffixes=('', '_temp'))

            # 立即優化結果
            result = self.optimize_dataframe(result)

            # 釋放不需要的列
            temp_cols = [c for c in result.columns if c.endswith('_temp')]
            if temp_cols:
                result = result.drop(columns=temp_cols)

            # 強制垃圾回收
            self.force_garbage_collection()

        return result

    def cleanup_large_objects(self, *objects):
        """
        清理大型對象

        Args:
            *objects: 要清理的對象
        """
        for obj in objects:
            del obj
        self.force_garbage_collection()

    def get_optimization_report(self) -> Dict[str, Any]:
        """獲取優化報告"""
        current = self.get_memory_usage()
        self.update_peak_memory()

        return {
            'timestamp': datetime.now().isoformat(),
            'initial_memory_mb': self.initial_memory['rss_mb'],
            'current_memory_mb': current['rss_mb'],
            'peak_memory_mb': self.peak_memory,
            'memory_increase_mb': current['rss_mb'] - self.initial_memory['rss_mb'],
            'memory_percent': current['percent'],
            'under_threshold': self.check_memory_threshold(),
            'garbage_collection_runs': gc.get_count()
        }


class DataStreamProcessor:
    """數據流處理器 - 用於處理大型數據集"""

    def __init__(self, memory_optimizer: MemoryOptimizer):
        self.optimizer = memory_optimizer

    def process_in_batches(self, data: Dict[str, pd.DataFrame], batch_size: int = 5000) -> Iterator[Dict[str, pd.DataFrame]]:
        """
        批量處理多個DataFrame

        Args:
            data: 數據字典
            batch_size: 批次大小

        Yields:
            批量數據字典
        """
        if not data:
            return

        # 獲取所有DataFrame的長度
        lengths = {k: len(v) for k, v in data.items()}
        max_length = max(lengths.values())

        for start in range(0, max_length, batch_size):
            batch = {}
            for key, df in data.items():
                end = min(start + batch_size, len(df))
                batch[key] = df.iloc[start:end].copy()

            # 優化批次數據
            for key in batch:
                batch[key] = self.optimizer.optimize_dataframe(batch[key])

            yield batch

            # 清理內存
            self.optimizer.force_garbage_collection()

    def aggregate_results(self, batch_results: list) -> Dict[str, Any]:
        """
        聚合批次結果

        Args:
            batch_results: 批次結果列表

        Returns:
            聚合後的結果
        """
        if not batch_results:
            return {}

        # 合併所有批次結果
        aggregated = {}
        for result in batch_results:
            for key, value in result.items():
                if key not in aggregated:
                    aggregated[key] = []
                aggregated[key].append(value)

        # 處理不同類型的數據
        for key, values in aggregated.items():
            if isinstance(values[0], pd.DataFrame):
                # DataFrame需要concat
                aggregated[key] = pd.concat(values, ignore_index=True)
                aggregated[key] = self.optimizer.optimize_dataframe(aggregated[key])
            elif isinstance(values[0], (int, float)):
                # 數值需要統計
                aggregated[key] = {
                    'sum': sum(values),
                    'mean': np.mean(values),
                    'count': len(values)
                }

        return aggregated


class StreamingDataCollector:
    """流式數據收集器 - 減少內存峰值"""

    def __init__(self, memory_limit_mb: float = 1024):
        self.memory_optimizer = MemoryOptimizer(memory_limit_mb)
        self.collected_data = {}
        self.data_sources = []

    def add_data_source(self, name: str, data: pd.DataFrame):
        """
        添加數據源

        Args:
            name: 數據源名稱
            data: 數據DataFrame
        """
        # 立即優化
        optimized_data = self.memory_optimizer.optimize_dataframe(data)

        # 檢查內存
        if not self.memory_optimizer.check_memory_threshold():
            logger.warning(f"內存使用超過閾值: {self.memory_optimizer.max_memory_mb} MB")
            # 強制垃圾回收
            self.memory_optimizer.force_garbage_collection()

        self.collected_data[name] = optimized_data
        self.data_sources.append(name)

        logger.info(f"已添加數據源 '{name}': {len(optimized_data)} 行")

    def get_data_summary(self) -> Dict[str, Any]:
        """獲取數據摘要"""
        summary = {
            'sources': len(self.data_sources),
            'total_rows': 0,
            'total_columns': 0,
            'memory_usage': self.memory_optimizer.get_optimization_report()
        }

        for name, data in self.collected_data.items():
            summary['total_rows'] += len(data)
            summary['total_columns'] += len(data.columns)

        return summary

    def cleanup_all(self):
        """清理所有數據"""
        logger.info("清理所有數據...")
        self.collected_data.clear()
        self.data_sources.clear()
        self.memory_optimizer.force_garbage_collection()


# 導出
__all__ = ['MemoryOptimizer', 'DataStreamProcessor', 'StreamingDataCollector']
