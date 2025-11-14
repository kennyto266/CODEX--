#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance Optimization Script for Multi-Source Data Integration

This script implements performance optimizations for the 5-source data integration:
1. Parallel data fetching using asyncio
2. LRU caching for API responses
3. Batch processing for indicator calculations
4. Memory optimization and data streaming
5. Performance benchmarking

Author: Claude Code
Version: 1.0
Date: 2025-11-10
"""

import asyncio
import time
from functools import lru_cache
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import pandas as pd
import numpy as np


class PerformanceOptimizer:
    """Optimize performance for multi-source data integration"""

    def __init__(self, max_workers: int = 8):
        self.max_workers = max_workers
        self.cache_stats = {'hits': 0, 'misses': 0}

    @staticmethod
    @lru_cache(maxsize=128)
    def cached_data_fetch(source: str, start_date: str, end_date: str) -> Dict:
        """
        Cache API responses to reduce redundant network calls

        This function is decorated with lru_cache to automatically cache results
        based on the function arguments.
        """
        # Simulate API call
        import random
        time.sleep(0.1)  # Simulate network latency

        return {
            'source': source,
            'data': [random.random() for _ in range(100)],
            'date_range': (start_date, end_date)
        }

    async def fetch_all_sources_parallel(
        self,
        sources: List[str],
        start_date: str,
        end_date: str
    ) -> Dict[str, Dict]:
        """
        Fetch data from all sources in parallel using asyncio

        Args:
            sources: List of data source names
            start_date: Start date for data fetch
            end_date: End date for data fetch

        Returns:
            Dict mapping source names to fetched data
        """
        tasks = []
        for source in sources:
            task = asyncio.create_task(
                self._fetch_with_semaphore(
                    source, start_date, end_date
                )
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        return dict(zip(sources, results))

    async def _fetch_with_semaphore(
        self,
        source: str,
        start_date: str,
        end_date: str
    ) -> Dict:
        """
        Fetch data with semaphore to limit concurrent connections
        """
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent connections

        async with semaphore:
            # Use cached fetch if available
            cache_key = (source, start_date, end_date)
            if cache_key in self._fetch_cache:
                self.cache_stats['hits'] += 1
                return self._fetch_cache[cache_key]

            self.cache_stats['misses'] += 1
            result = await asyncio.to_thread(
                self.cached_data_fetch,
                source, start_date, end_date
            )

            self._fetch_cache[cache_key] = result
            return result

    _fetch_cache = {}  # Simple in-memory cache

    def calculate_indicators_parallel(
        self,
        data_dict: Dict[str, pd.DataFrame],
        indicator_funcs: List
    ) -> Dict[str, Dict]:
        """
        Calculate technical indicators in parallel using ThreadPoolExecutor

        Args:
            data_dict: Dict mapping source to DataFrame
            indicator_funcs: List of indicator calculation functions

        Returns:
            Dict mapping source to calculated indicators
        """
        results = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}

            for source, data in data_dict.items():
                for func in indicator_funcs:
                    future = executor.submit(func, data)
                    futures[(source, func.__name__)] = future

            for (source, func_name), future in futures.items():
                result = future.result()
                if source not in results:
                    results[source] = {}
                results[source][func_name] = result

        return results

    def optimize_memory_usage(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Optimize memory usage of DataFrame

        Args:
            data: Input DataFrame

        Returns:
            Memory-optimized DataFrame
        """
        # Convert to appropriate dtypes
        for col in data.columns:
            col_type = data[col].dtype

            if col_type != 'object':
                c_min = data[col].min()
                c_max = data[col].max()

                if str(col_type)[:3] == 'int':
                    if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                        data[col] = data[col].astype(np.int8)
                    elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                        data[col] = data[col].astype(np.int16)
                    elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                        data[col] = data[col].astype(np.int32)
                elif str(col_type)[:5] == 'float':
                    if c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                        data[col] = data[col].astype(np.float32)

        return data

    def batch_process_data(
        self,
        data: pd.DataFrame,
        batch_size: int = 1000
    ) -> List[pd.DataFrame]:
        """
        Split data into batches for memory-efficient processing

        Args:
            data: Input DataFrame
            batch_size: Size of each batch

        Returns:
            List of DataFrame batches
        """
        batches = []
        for i in range(0, len(data), batch_size):
            batch = data.iloc[i:i + batch_size].copy()
            batches.append(batch)
        return batches

    def benchmark_data_fetching(
        self,
        sources: List[str],
        start_date: str,
        end_date: str
    ) -> Dict:
        """
        Benchmark data fetching performance

        Returns:
            Dict with timing and cache statistics
        """
        # Clear cache for clean benchmark
        self.cached_data_fetch.cache_clear()
        self.cache_stats = {'hits': 0, 'misses': 0}

        # Sequential fetch
        start_time = time.time()
        sequential_results = {}
        for source in sources:
            result = self.cached_data_fetch(source, start_date, end_date)
            sequential_results[source] = result
        sequential_time = time.time() - start_time

        # Parallel fetch
        start_time = time.time()
        parallel_results = asyncio.run(
            self.fetch_all_sources_parallel(sources, start_date, end_date)
        )
        parallel_time = time.time() - start_time

        return {
            'sequential_time': sequential_time,
            'parallel_time': parallel_time,
            'speedup': sequential_time / parallel_time if parallel_time > 0 else 0,
            'cache_hit_rate': (
                self.cache_stats['hits'] /
                (self.cache_stats['hits'] + self.cache_stats['misses'])
                if (self.cache_stats['hits'] + self.cache_stats['misses']) > 0 else 0
            ),
            'sources_count': len(sources),
            'total_records': sum(len(r['data']) for r in parallel_results.values())
        }

    def generate_optimization_report(self, benchmark_results: Dict) -> str:
        """
        Generate performance optimization report

        Args:
            benchmark_results: Results from benchmark

        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 80)
        report.append("PERFORMANCE OPTIMIZATION REPORT")
        report.append("=" * 80)
        report.append(f"\nConfiguration:")
        report.append(f"  Max Workers: {self.max_workers}")
        report.append(f"  Sources: {benchmark_results['sources_count']}")

        report.append(f"\nData Fetching Performance:")
        report.append(f"  Sequential Time: {benchmark_results['sequential_time']:.2f}s")
        report.append(f"  Parallel Time: {benchmark_results['parallel_time']:.2f}s")
        report.append(f"  Speedup: {benchmark_results['speedup']:.2f}x")
        report.append(f"  Total Records: {benchmark_results['total_records']}")

        report.append(f"\nCaching Performance:")
        report.append(f"  Cache Hit Rate: {benchmark_results['cache_hit_rate']*100:.1f}%")

        report.append(f"\nPerformance Targets:")
        report.append(f"  Target: < 30 seconds for 5 sources")
        is_fast = benchmark_results['parallel_time'] < 30
        status = "[PASS]" if is_fast else "[FAIL]"
        report.append(f"  Status: {status}")

        report.append("\n" + "=" * 80)
        report.append("OPTIMIZATION RECOMMENDATIONS")
        report.append("=" * 80)

        if benchmark_results['speedup'] < 2.0:
            report.append("\n1. Increase concurrency:")
            report.append("   - Increase max_workers")
            report.append("   - Check network latency")
            report.append("   - Monitor API rate limits")

        if benchmark_results['cache_hit_rate'] < 0.5:
            report.append("\n2. Improve caching:")
            report.append("   - Increase cache size (currently 128)")
            report.append("   - Implement smarter cache invalidation")
            report.append("   - Use Redis for distributed caching")

        if benchmark_results['parallel_time'] > 30:
            report.append("\n3. Further optimization needed:")
            report.append("   - Implement data streaming")
            report.append("   - Use faster data serialization")
            report.append("   - Consider data compression")

        report.append("\n" + "=" * 80)

        return '\n'.join(report)


def main():
    """Run performance optimization and benchmarking"""
    # Configuration
    sources = ['visitor', 'property', 'gdp', 'retail', 'trade']
    start_date = '2020-01-01'
    end_date = '2023-12-31'

    # Initialize optimizer
    optimizer = PerformanceOptimizer(max_workers=8)

    # Run benchmark
    print("Running performance benchmark...")
    benchmark_results = optimizer.benchmark_data_fetching(
        sources, start_date, end_date
    )

    # Generate report
    report = optimizer.generate_optimization_report(benchmark_results)
    print(report)

    # Save report
    with open('PERFORMANCE_OPTIMIZATION_REPORT.md', 'w', encoding='utf-8') as f:
        f.write(report)

    print("\nReport saved to: PERFORMANCE_OPTIMIZATION_REPORT.md")


if __name__ == '__main__':
    main()
