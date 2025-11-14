#!/usr/bin/env python3
"""
Phase 4 性能優化工具 - Pandas懶加載優化
優化Pandas操作，減少重複計算和內存使用
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Callable
from functools import wraps
import weakref


class LazyDataFrame:
    """
    懶惰DataFrame - 延遲計算，避免重複操作

    Example:
        # 替代重複的 groupby 操作
        # df.groupby('category')['value'].sum()
        # df.groupby('category')['value'].mean()

        # 使用:
        lazy_df = LazyDataFrame(df)
        sum_result = lazy_df.groupby('category')['value'].sum()
        mean_result = lazy_df.groupby('category')['value'].mean()
    """

    def __init__(self, df: pd.DataFrame):
        self._df = df
        self._cache = weakref.WeakValueDictionary()
        self._operations = []

    def _get_cached(self, key: str, operation: Callable):
        """獲取緩存的結果或執行操作"""
        if key in self._cache:
            return self._cache[key]

        result = operation()
        self._cache[key] = result
        return result

    def groupby(self, by, **kwargs):
        """惰性 groupby"""
        key = f"groupby_{hash(str(by))}_{hash(str(kwargs))}"

        def do_groupby():
            return LazyGroupBy(self._df.groupby(by, **kwargs), self._cache, key)

        return self._get_cached(key, do_groupby)

    def apply(self, func, axis=0, **kwargs):
        """惰性 apply"""
        # apply 不能完全惰性，但可以緩存結果
        @wraps(func)
        def wrapped_func(*args, **kw):
            return func(self._df, *args, **kw)

        return self._df.apply(wrapped_func, axis=axis, **kwargs)

    @property
    def values(self):
        """獲取數組值（惰性）"""
        return self._df.values

    def __getattr__(self, name):
        """代理所有其他屬性"""
        return getattr(self._df, name)


class LazyGroupByColumn:
    """惰性 GroupBy 列操作"""

    def __init__(self, groupby_obj, column, cache, cache_key):
        self._groupby = groupby_obj
        self._column = column
        self._cache = cache
        self._cache_key = cache_key

    def _get_agg_key(self, agg):
        """生成聚合操作的緩存鍵"""
        return f"{self._cache_key}_agg_{self._column}_{agg}"

    def sum(self, **kwargs):
        """惰性求和"""
        key = self._get_agg_key('sum')
        if key in self._cache:
            return self._cache[key]
        result = self._groupby[self._column].sum(**kwargs)
        self._cache[key] = result
        return result

    def mean(self, **kwargs):
        """惰性平均值"""
        key = self._get_agg_key('mean')
        if key in self._cache:
            return self._cache[key]
        result = self._groupby[self._column].mean(**kwargs)
        self._cache[key] = result
        return result

    def count(self, **kwargs):
        """惰性計數"""
        key = self._get_agg_key('count')
        if key in self._cache:
            return self._cache[key]
        result = self._groupby[self._column].count(**kwargs)
        self._cache[key] = result
        return result


class LazyGroupBy:
    """
    惰性 GroupBy 操作
    """

    def __init__(self, groupby_obj, cache, cache_key):
        self._groupby = groupby_obj
        self._cache = cache
        self._cache_key = cache_key

    def _get_agg_key(self, column, agg):
        """生成聚合操作的緩存鍵"""
        return f"{self._cache_key}_agg_{column}_{agg}"

    def __getitem__(self, column):
        """支持使用[]訪問列"""
        return LazyGroupByColumn(self._groupby, column, self._cache, self._cache_key)

    def sum(self, numeric_only=True, **kwargs):
        """惰性求和"""
        column = kwargs.get('column') if kwargs else None
        agg = 'sum'
        if column:
            key = self._get_agg_key(column, agg)
            if key in self._cache:
                return self._cache[key]
            result = self._groupby[column].sum()
            self._cache[key] = result
            return result
        return self._groupby.sum(numeric_only=numeric_only, **kwargs)

    def mean(self, numeric_only=True, **kwargs):
        """惰性平均值"""
        column = kwargs.get('column') if kwargs else None
        agg = 'mean'
        if column:
            key = self._get_agg_key(column, agg)
            if key in self._cache:
                return self._cache[key]
            result = self._groupby[column].mean()
            self._cache[key] = result
            return result
        return self._groupby.mean(numeric_only=numeric_only, **kwargs)

    def count(self, **kwargs):
        """惰性計數"""
        return self._groupby.count(**kwargs)

    def agg(self, agg_dict, **kwargs):
        """惰性聚合"""
        key = f"{self._cache_key}_agg_{hash(str(agg_dict))}"
        if key in self._cache:
            return self._cache[key]
        result = self._groupby.agg(agg_dict, **kwargs)
        self._cache[key] = result
        return result

    def apply(self, func, **kwargs):
        """應用函數"""
        return self._groupby.apply(func, **kwargs)


class DataFrameOptimizer:
    """
    DataFrame 優化器 - 提供高性能的DataFrame操作
    """

    @staticmethod
    def merge_optimized(*dfs, on=None, how='inner', **kwargs):
        """
        優化的合併操作

        Args:
            *dfs: 要合併的DataFrame列表
            on: 合併鍵
            how: 合併方式
            **kwargs: 其他參數

        Returns:
            合併後的DataFrame
        """
        if len(dfs) == 2:
            # 兩個DataFrame的合併
            df1, df2 = dfs
            # 預先排序以提高合併性能
            if on:
                df1 = df1.sort_values(on)
                df2 = df2.sort_values(on)
            return pd.merge(df1, df2, on=on, how=how, **kwargs)
        else:
            # 多個DataFrame的合併
            result = dfs[0]
            for df in dfs[1:]:
                if on:
                    result = result.sort_values(on)
                    df = df.sort_values(on)
                result = pd.merge(result, df, on=on, how=how, **kwargs)
            return result

    @staticmethod
    def concat_optimized(dfs: List[pd.DataFrame], axis=0, **kwargs) -> pd.DataFrame:
        """
        優化的連接操作

        Args:
            dfs: DataFrame列表
            axis: 連接軸
            **kwargs: 其他參數

        Returns:
            連接後的DataFrame
        """
        if not dfs:
            return pd.DataFrame()

        # 預檢查列名一致性
        if axis == 0 and len(dfs) > 1:
            # 垂直連接時確保列名一致
            first_cols = set(dfs[0].columns)
            for df in dfs[1:]:
                if set(df.columns) != first_cols:
                    # 列名不一致時需要重新索引
                    dfs = [df.reindex(columns=first_cols, fill_value=np.nan) for df in dfs]

        return pd.concat(dfs, axis=axis, **kwargs)

    @staticmethod
    def apply_chunked(df: pd.DataFrame, func: Callable, chunk_size: int = 10000, **kwargs):
        """
        分塊應用函數（避免內存溢出）

        Args:
            df: 輸入DataFrame
            func: 要應用的函數
            chunk_size: 塊大小
            **kwargs: 其他參數

        Returns:
            結果DataFrame
        """
        n_chunks = (len(df) + chunk_size - 1) // chunk_size
        results = []

        for i in range(n_chunks):
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size, len(df))
            chunk = df.iloc[start_idx:end_idx]

            try:
                result_chunk = func(chunk, **kwargs)
                results.append(result_chunk)
            except Exception as e:
                print(f"Chunk {i} 處理失敗: {e}")

        if not results:
            return pd.DataFrame()

        # 合併結果
        if isinstance(results[0], pd.DataFrame):
            return pd.concat(results, ignore_index=True)
        elif isinstance(results[0], pd.Series):
            return pd.concat(results, ignore_index=True)
        else:
            # 如果是標量值，返回列表
            return results

    @staticmethod
    def vectorized_conditional(df: pd.DataFrame, condition: pd.Series, if_true: Any, if_false: Any) -> pd.Series:
        """
        向量化條件操作（替代 apply）

        Args:
            df: 輸入DataFrame
            condition: 條件Series
            if_true: 為真時的值
            if_false: 為假時的值

        Returns:
            結果Series

        Example:
            # 替代:
            # df['result'] = df.apply(lambda row: value1 if condition(row) else value2, axis=1)

            # 使用:
            df['result'] = DataFrameOptimizer.vectorized_conditional(
                df, df['col'] > 0, 'positive', 'negative'
            )
        """
        return np.where(condition, if_true, if_false)

    @staticmethod
    def calculate_metrics(df: pd.DataFrame, columns: List[str]) -> Dict[str, float]:
        """
        批量計算統計指標

        Args:
            df: 輸入DataFrame
            columns: 要計算的列

        Returns:
            統計指標字典
        """
        metrics = {}
        for col in columns:
            if col in df.columns:
                series = df[col]
                metrics[col] = {
                    'mean': series.mean(),
                    'std': series.std(),
                    'min': series.min(),
                    'max': series.max(),
                    'median': series.median(),
                    'count': series.count()
                }
        return metrics

    @staticmethod
    def remove_duplicates_optimized(df: pd.DataFrame, subset=None, keep='first', **kwargs) -> pd.DataFrame:
        """
        優化的去重操作

        Args:
            df: 輸入DataFrame
            subset: 指定列
            keep: 保留方式
            **kwargs: 其他參數

        Returns:
            去重後的DataFrame
        """
        return df.drop_duplicates(subset=subset, keep=keep, **kwargs)


class MemoryOptimizer:
    """
    內存優化工具
    """

    @staticmethod
    def optimize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
        """
        優化數據類型以減少內存使用

        Args:
            df: 輸入DataFrame

        Returns:
            優化後的DataFrame
        """
        df_optimized = df.copy()

        for col in df_optimized.columns:
            col_type = df_optimized[col].dtype

            if col_type != 'object':
                # 數值類型
                if col_type in ['int64', 'int32', 'int16', 'int8']:
                    # 檢查是否能降級為更小的整數類型
                    col_min = df_optimized[col].min()
                    col_max = df_optimized[col].max()

                    if col_min >= 0:
                        # 無符號整數
                        if col_max < 2**8:
                            df_optimized[col] = df_optimized[col].astype('uint8')
                        elif col_max < 2**16:
                            df_optimized[col] = df_optimized[col].astype('uint16')
                        elif col_max < 2**32:
                            df_optimized[col] = df_optimized[col].astype('uint32')
                    else:
                        # 有符號整數
                        if col_min > np.iinfo('int8').min and col_max < np.iinfo('int8').max:
                            df_optimized[col] = df_optimized[col].astype('int8')
                        elif col_min > np.iinfo('int16').min and col_max < np.iinfo('int16').max:
                            df_optimized[col] = df_optimized[col].astype('int16')
                        elif col_min > np.iinfo('int32').min and col_max < np.iinfo('int32').max:
                            df_optimized[col] = df_optimized[col].astype('int32')

                elif col_type in ['float64']:
                    # 浮點數
                    if pd.api.types.is_float_dtype(df_optimized[col]):
                        col_min = df_optimized[col].min()
                        col_max = df_optimized[col].max()

                        # 檢查是否能使用 float32
                        if col_min > np.finfo('float32').min and col_max < np.finfo('float32').max:
                            df_optimized[col] = df_optimized[col].astype('float32')
            else:
                # 對象類型，嘗試轉換為分類
                n_unique = df_optimized[col].nunique()
                n_total = len(df_optimized[col])
                if n_unique / n_total < 0.5:  # 唯一值少於50%時轉換為分類
                    df_optimized[col] = df_optimized[col].astype('category')

        return df_optimized

    @staticmethod
    def memory_usage(df: pd.DataFrame) -> Dict[str, Any]:
        """
        分析DataFrame內存使用

        Args:
            df: 輸入DataFrame

        Returns:
            內存使用報告
        """
        usage = df.memory_usage(deep=True)
        total = usage.sum()

        return {
            'total_mb': total / (1024 ** 2),
            'columns': {
                col: {
                    'usage_mb': mem / (1024 ** 2),
                    'dtype': str(df[col].dtype)
                }
                for col, mem in zip(df.columns, usage)
            }
        }

    @staticmethod
    def compress_numeric_columns(df: pd.DataFrame, columns: List[str] = None) -> pd.DataFrame:
        """
        壓縮數值列

        Args:
            df: 輸入DataFrame
            columns: 要壓縮的列（None表示所有數值列）

        Returns:
            壓縮後的DataFrame
        """
        df_compressed = df.copy()

        if columns is None:
            columns = df_compressed.select_dtypes(include=[np.number]).columns.tolist()

        for col in columns:
            if col in df_compressed.columns:
                # 嘗試不同的壓縮方式
                original_size = df_compressed[col].memory_usage(deep=True)

                # 方法1: 降級數值類型
                try:
                    df_compressed[col] = pd.to_numeric(df_compressed[col], downcast='integer')
                except:
                    pass

                try:
                    df_compressed[col] = pd.to_numeric(df_compressed[col], downcast='float')
                except:
                    pass

                # 方法2: 使用category編碼
                if df_compressed[col].dtype == 'object':
                    df_compressed[col] = df_compressed[col].astype('category')

                compressed_size = df_compressed[col].memory_usage(deep=True)
                if compressed_size < original_size * 0.8:  # 節省超過20%
                    print(f"  {col}: {original_size / 1024:.1f}KB -> {compressed_size / 1024:.1f}KB")

        return df_compressed


def main():
    """主函數 - 演示用法"""
    print("=" * 80)
    print("Phase 4: Pandas Optimization Tools Demo")
    print("=" * 80)

    # 創建測試數據
    df = pd.DataFrame({
        'category': ['A', 'B', 'A', 'B', 'A'] * 200,
        'value1': range(1000),
        'value2': range(1000, 2000),
        'value3': np.random.randn(1000)
    })

    print(f"\n測試數據: {len(df)} 行 x {len(df.columns)} 列")

    # 演示1: 懶惰DataFrame
    print("\n[1] 懶惰DataFrame")
    lazy_df = LazyDataFrame(df)

    # 惰性groupby（緩存結果）
    import time

    start = time.time()
    result1 = lazy_df.groupby('category')['value1'].sum()
    time1 = time.time() - start

    start = time.time()
    result2 = lazy_df.groupby('category')['value1'].sum()  # 從緩存獲取
    time2 = time.time() - start

    print(f"  第一次計算: {time1*1000:.2f} ms")
    print(f"  緩存讀取:   {time2*1000:.2f} ms")
    print(f"  提升:       {time1/time2:.2f}x")

    # 演示2: 內存優化
    print("\n[2] 內存優化")
    memory_before = MemoryOptimizer.memory_usage(df)
    df_optimized = MemoryOptimizer.optimize_dtypes(df)
    memory_after = MemoryOptimizer.memory_usage(df_optimized)

    print(f"  優化前: {memory_before['total_mb']:.2f} MB")
    print(f"  優化後: {memory_after['total_mb']:.2f} MB")
    print(f"  節省:   {(1 - memory_after['total_mb']/memory_before['total_mb'])*100:.1f}%")

    # 演示3: 分塊處理
    print("\n[3] 分塊處理")
    large_df = pd.DataFrame({
        'values': range(100000),
        'category': [i % 100 for i in range(100000)]
    })

    def process_chunk(chunk):
        return chunk.groupby('category')['values'].sum()

    import time
    start = time.time()
    result = DataFrameOptimizer.apply_chunked(large_df, process_chunk, chunk_size=10000)
    process_time = time.time() - start

    print(f"  處理 100,000 行用時: {process_time:.2f} 秒")
    print(f"  吞吐量: {len(large_df) / process_time:.0f} 行/秒")

    print("\n" + "=" * 80)
    print("Pandas optimization tools ready!")
    print("=" * 80)


if __name__ == '__main__':
    main()
