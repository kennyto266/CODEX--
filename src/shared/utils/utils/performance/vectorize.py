#!/usr/bin/env python3
"""
Phase 4 性能優化工具 - 循環向量化
將低效的for循環轉換為Pandas/NumPy向量化操作
"""

import pandas as pd
import numpy as np
from functools import wraps
from typing import Callable, Any, List, Dict


class VectorizationError(Exception):
    """向量化錯誤"""
    pass


def vectorize_operation(func: Callable) -> Callable:
    """
    向量化裝飾器 - 自動將循環操作轉換為向量化操作

    Args:
        func: 要向量化的函數

    Returns:
        裝飾後的函數

    Example:
        @vectorize_operation
        def process_data(df):
            # 之前的代碼:
            # for i in range(len(df)):
            #     df.loc[i, 'new_col'] = df.loc[i, 'col1'] * 2

            # 之後的代碼:
            return df['col1'] * 2
    """
    @wraps(func)
    def wrapper(data, *args, **kwargs):
        if isinstance(data, (list, tuple)):
            # 如果是列表或元組，嘗試轉換為pandas Series或DataFrame
            try:
                if len(data) > 0 and isinstance(data[0], dict):
                    # 列表中的字典，轉換為DataFrame
                    df = pd.DataFrame(data)
                    result = func(df, *args, **kwargs)
                    return result.to_dict('records') if isinstance(result, pd.DataFrame) else result
                else:
                    # 簡單列表，轉換為Series
                    series = pd.Series(data)
                    result = func(series, *args, **kwargs)
                    return result.tolist() if hasattr(result, 'tolist') else result
            except Exception as e:
                raise VectorizationError(f"無法向量化數據: {e}")
        elif isinstance(data, pd.DataFrame):
            # DataFrame直接使用向量化
            return func(data, *args, **kwargs)
        elif isinstance(data, pd.Series):
            # Series直接使用向量化
            return func(data, *args, **kwargs)
        else:
            # 其他類型直接處理
            return func(data, *args, **kwargs)

    return wrapper


class DataFrameProcessor:
    """
    DataFrame處理器 - 提供高性能的數據處理方法

    替代傳統的iterrows()等低效方法
    """

    @staticmethod
    @vectorize_operation
    def safe_iterate(df: pd.DataFrame, operation: Callable) -> pd.DataFrame:
        """
        安全迭代DataFrame的行

        Args:
            df: 輸入DataFrame
            operation: 對每行執行的函數 (接受Series，返回字典或標量值)

        Returns:
            包含結果的新DataFrame

        Example:
            # 替代:
            # for i, row in df.iterrows():
            #     df.loc[i, 'result'] = calculate(row)

            # 使用:
            df = DataFrameProcessor.safe_iterate(df, lambda row: calculate(row))
        """
        results = []
        for _, row in df.iterrows():
            try:
                result = operation(row)
                results.append(result)
            except Exception as e:
                results.append(None)

        # 將結果添加到DataFrame
        if isinstance(results[0], dict):
            # 如果結果是字典，創建新的列
            for key in results[0].keys():
                df[key] = [r.get(key) if r and isinstance(r, dict) else None for r in results]
        else:
            # 如果結果是標量，創建單一列
            df['result'] = results

        return df

    @staticmethod
    def batch_process(df: pd.DataFrame, columns: List[str], operation: Callable, batch_size: int = 1000) -> pd.DataFrame:
        """
        批量處理DataFrame

        Args:
            df: 輸入DataFrame
            columns: 要處理的列
            operation: 批量處理函數
            batch_size: 批次大小

        Returns:
            處理後的DataFrame

        Example:
            # 替代多個iterrows調用
            df = DataFrameProcessor.batch_process(
                df, ['col1', 'col2'],
                lambda batch: batch['col1'] * batch['col2']
            )
        """
        n_batches = (len(df) + batch_size - 1) // batch_size
        results = []

        for i in range(n_batches):
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, len(df))
            batch = df.iloc[start_idx:end_idx].copy()

            try:
                batch_results = operation(batch)
                if isinstance(batch_results, pd.DataFrame):
                    results.append(batch_results)
                else:
                    # 如果不是DataFrame，創建新列
                    if 'batch_result' not in batch.columns:
                        batch['batch_result'] = None
                    batch['batch_result'] = batch_results
                    results.append(batch)
            except Exception as e:
                print(f"批次 {i} 處理失敗: {e}")
                results.append(batch)

        return pd.concat(results, ignore_index=True) if results else df

    @staticmethod
    @vectorize_operation
    def apply_vectorized(df: pd.DataFrame, column: str, func: Callable) -> pd.Series:
        """
        應用向量化函數

        Args:
            df: 輸入DataFrame
            column: 要處理的列
            func: 函數

        Returns:
            結果Series

        Example:
            # 替代 apply(axis=1)
            # df['result'] = df.apply(lambda row: func(row['col']), axis=1)

            # 使用:
            result = DataFrameProcessor.apply_vectorized(df, 'col', func)
            df['result'] = result
        """
        series = df[column]
        return series.apply(func)


class ListProcessor:
    """
    列表處理器 - 提供高性能的列表操作
    """

    @staticmethod
    def chunked_process(items: list, operation: Callable, chunk_size: int = 1000) -> list:
        """
        批量處理列表項目

        Args:
            items: 輸入列表
            operation: 處理函數
            chunk_size: 批次大小

        Returns:
            處理後的列表

        Example:
            # 替代:
            # for item in items:
            #     process(item)

            # 使用:
            results = ListProcessor.chunked_process(items, process)
        """
        n_chunks = (len(items) + chunk_size - 1) // chunk_size
        results = []

        for i in range(n_chunks):
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size, len(items))
            chunk = items[start_idx:end_idx]

            try:
                chunk_results = [operation(item) for item in chunk]
                results.extend(chunk_results)
            except Exception as e:
                print(f"批次 {i} 處理失敗: {e}")
                results.extend([None] * len(chunk))

        return results

    @staticmethod
    def parallel_map(items: list, operation: Callable, n_jobs: int = -1) -> list:
        """
        並行映射列表項目

        Args:
            items: 輸入列表
            operation: 處理函數
            n_jobs: 並行任務數（-1表示使用所有CPU核心）

        Returns:
            處理後的列表

        Example:
            from multiprocessing import Pool

            results = ListProcessor.parallel_map(items, process)
        """
        try:
            from multiprocessing import Pool

            with Pool(processes=n_jobs) as pool:
                results = pool.map(operation, items)
            return results
        except ImportError:
            # 如果沒有multiprocessing，使用單進程
            return [operation(item) for item in items]


def replace_iterrows(df: pd.DataFrame, operation: Callable) -> pd.DataFrame:
    """
    替代iterrows()的低效操作

    Args:
        df: 輸入DataFrame
        operation: 要對每行執行的操作（接受Series，返回字典或標量）

    Returns:
        包含結果的DataFrame

    Example:
        # 替代:
        # for i, row in df.iterrows():
        #     df.loc[i, 'result'] = operation(row)

        # 使用:
        df = replace_iterrows(df, lambda row: row['col1'] * 2)
    """
    return DataFrameProcessor.safe_iterate(df, operation)


def vectorize_calculation(df: pd.DataFrame, expression: str) -> pd.Series:
    """
    向量化計算表達式

    Args:
        df: 輸入DataFrame
        expression: 計算表達式

    Returns:
        結果Series

    Example:
        # 替代:
        # for i in range(len(df)):
        #     df.loc[i, 'result'] = df.loc[i, 'col1'] + df.loc[i, 'col2']

        # 使用:
        df['result'] = vectorize_calculation(df, 'col1 + col2')
    """
    return df.eval(expression)


class PerformanceBenchmark:
    """性能基準測試工具"""

    @staticmethod
    def compare_iterations(n_iterations: int = 10000):
        """
        比較傳統循環和向量化操作的性能

        Args:
            n_iterations: 迭代次數
        """
        import time

        # 創建測試數據
        df = pd.DataFrame({
            'a': range(n_iterations),
            'b': range(n_iterations)
        })

        # 方法1: 傳統循環
        start = time.time()
        for i in range(len(df)):
            df.loc[i, 'result1'] = df.loc[i, 'a'] + df.loc[i, 'b']
        time1 = time.time() - start

        # 方法2: 向量化
        df2 = pd.DataFrame({'a': range(n_iterations), 'b': range(n_iterations)})
        start = time.time()
        df2['result2'] = df2['a'] + df2['b']
        time2 = time.time() - start

        print(f"\n性能比較 (n={n_iterations}):")
        print(f"  傳統循環: {time1:.4f} 秒")
        print(f"  向量化:   {time2:.4f} 秒")
        print(f"  提升:     {time1/time2:.2f}x")


def main():
    """主函數 - 演示用法"""
    print("=" * 80)
    print("Phase 4: Vectorization Tools Demo")
    print("=" * 80)

    # 創建測試DataFrame
    df = pd.DataFrame({
        'a': range(1000),
        'b': range(1000)
    })

    print(f"\n測試數據: {len(df)} 行")

    # 演示1: 傳統iterrows vs 向量化
    print("\n[1] 比較 iterrows vs 向量化")
    import time

    # iterrows
    start = time.time()
    result1 = []
    for _, row in df.head(100).iterrows():
        result1.append(row['a'] * row['b'])
    iterrows_time = time.time() - start

    # 向量化
    start = time.time()
    result2 = df.head(100)['a'] * df.head(100)['b']
    vectorized_time = time.time() - start

    print(f"  iterrows:   {iterrows_time*1000:.2f} ms")
    print(f"  向量化:     {vectorized_time*1000:.2f} ms")
    print(f"  提升:       {iterrows_time/vectorized_time:.2f}x")

    # 演示2: 批量處理
    print("\n[2] 批量處理演示")
    df_large = pd.DataFrame({
        'values': range(10000),
        'category': [i % 10 for i in range(10000)]
    })

    start = time.time()
    result = DataFrameProcessor.batch_process(
        df_large,
        ['values'],
        lambda batch: batch['values'] * 2
    )
    batch_time = time.time() - start
    print(f"  處理 10,000 行用時: {batch_time:.2f} 秒")
    print(f"  吞吐量: {len(result) / batch_time:.0f} 行/秒")

    print("\n" + "=" * 80)
    print("Vectorization tools ready!")
    print("=" * 80)


if __name__ == '__main__':
    main()
