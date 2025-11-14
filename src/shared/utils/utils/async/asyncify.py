#!/usr/bin/env python3
"""
Phase 4 性能優化工具 - 異步轉換
將阻塞的同步操作轉換為異步操作
"""

import asyncio
import time
from functools import wraps
from typing import Callable, Any, Coroutine
import inspect


class AsyncifyError(Exception):
    """異步轉換錯誤"""
    pass


def make_async(func: Callable) -> Callable:
    """
    將同步函數轉換為異步函數

    Args:
        func: 要轉換的同步函數

    Returns:
        異步版本的函數

    Example:
        # 替代:
        # def sync_function():
        #     time.sleep(1)
        #     return result

        # 使用:
        @make_async
        def async_function():
            time.sleep(1)
            return result
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    return wrapper


def asyncify_time_sleep():
    """
    將 time.sleep 轉換為 async 版本

    Example:
        # 替代:
        # import time
        # time.sleep(1)

        # 使用:
        import asyncio
        await asyncio.sleep(1)
    """
    pass


class AsyncBatchProcessor:
    """
    異步批量處理器 - 並發處理多個任務
    """

    @staticmethod
    async def process_batch(tasks: list, max_concurrent: int = 100) -> list:
        """
        異步批量處理任務

        Args:
            tasks: 任務列表（每個任務是可調用對象或協程）
            max_concurrent: 最大並發數

        Returns:
            結果列表

        Example:
            async def process_item(item):
                return await fetch_data(item)

            results = await AsyncBatchProcessor.process_batch(items, max_concurrent=50)
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def bounded_process(task):
            async with semaphore:
                if asyncio.iscoroutinefunction(task):
                    return await task()
                else:
                    return task()

        return await asyncio.gather(*[bounded_process(task) for task in tasks], return_exceptions=True)

    @staticmethod
    async def process_with_rate_limit(tasks: list, rate_limit: float) -> list:
        """
        帶速率限制的異步處理

        Args:
            tasks: 任務列表
            rate_limit: 每秒最多任務數

        Returns:
            結果列表

        Example:
            # 限制為每秒最多10個請求
            results = await AsyncBatchProcessor.process_with_rate_limit(tasks, 10.0)
        """
        results = []
        interval = 1.0 / rate_limit

        for task in tasks:
            if asyncio.iscoroutinefunction(task):
                result = await task()
            else:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, task)
            results.append(result)

            await asyncio.sleep(interval)

        return results


class AsyncHTTPClient:
    """
    異步HTTP客戶端 - 替代 requests 庫

    Example:
        # 替代:
        # import requests
        # response = requests.get(url)

        # 使用:
        async_client = AsyncHTTPClient()
        response = await async_client.get(url)
    """

    def __init__(self):
        import aiohttp
        self.session = aiohttp.ClientSession()

    async def get(self, url: str, **kwargs) -> dict:
        """
        異步GET請求

        Args:
            url: 請求URL
            **kwargs: 其他參數

        Returns:
            響應數據
        """
        try:
            async with self.session.get(url, **kwargs) as response:
                data = await response.json()
                return {
                    'status': response.status,
                    'data': data
                }
        except Exception as e:
            return {
                'status': 500,
                'error': str(e)
            }

    async def post(self, url: str, **kwargs) -> dict:
        """
        異步POST請求

        Args:
            url: 請求URL
            **kwargs: 其他參數

        Returns:
            響應數據
        """
        try:
            async with self.session.post(url, **kwargs) as response:
                data = await response.json()
                return {
                    'status': response.status,
                    'data': data
                }
        except Exception as e:
            return {
                'status': 500,
                'error': str(e)
            }

    async def close(self):
        """關閉會話"""
        await self.session.close()


class AsyncFileProcessor:
    """
    異步文件處理器
    """

    @staticmethod
    async def read_file(file_path: str) -> str:
        """
        異步讀取文件

        Args:
            file_path: 文件路徑

        Returns:
            文件內容
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: open(file_path, 'r', encoding='utf-8').read())

    @staticmethod
    async def write_file(file_path: str, content: str) -> None:
        """
        異步寫入文件

        Args:
            file_path: 文件路徑
            content: 內容
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: open(file_path, 'w', encoding='utf-8').write(content))

    @staticmethod
    async def read_multiple_files(file_paths: list) -> list:
        """
        異步讀取多個文件

        Args:
            file_paths: 文件路徑列表

        Returns:
            內容列表
        """
        tasks = [AsyncFileProcessor.read_file(fp) for fp in file_paths]
        return await asyncio.gather(*tasks, return_exceptions=True)


class AsyncDatabase:
    """
    異步數據庫操作
    """

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._pool = None

    async def connect(self):
        """連接數據庫"""
        # 這裡需要根據具體數據庫適配器實現
        pass

    async def execute(self, query: str, params: dict = None) -> list:
        """
        異步執行查詢

        Args:
            query: SQL查詢
            params: 參數

        Returns:
            查詢結果
        """
        # 使用 run_in_executor 執行同步數據庫操作
        loop = asyncio.get_event_loop()
        # 這裡需要根據具體數據庫驅動實現
        return await loop.run_in_executor(None, lambda: self._execute_sync(query, params))

    def _execute_sync(self, query: str, params: dict) -> list:
        """同步執行（由具體數據庫驅動實現）"""
        raise NotImplementedError

    async def close(self):
        """關閉連接"""
        if self._pool:
            await self._pool.close()


class AsyncCache:
    """
    異步緩存系統
    """

    def __init__(self):
        self._cache = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any:
        """
        異步獲取緩存

        Args:
            key: 緩存鍵

        Returns:
            緩存值
        """
        async with self._lock:
            return self._cache.get(key)

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """
        異步設置緩存

        Args:
            key: 緩存鍵
            value: 緩存值
            ttl: 生存時間（秒）
        """
        async with self._lock:
            self._cache[key] = {
                'value': value,
                'expires': time.time() + ttl
            }

    async def delete(self, key: str) -> None:
        """刪除緩存"""
        async with self._lock:
            self._cache.pop(key, None)


class AsyncTimer:
    """
    異步計時器
    """

    @staticmethod
    async def sleep(seconds: float):
        """
        異步睡眠

        Args:
            seconds: 睡眠時間（秒）
        """
        await asyncio.sleep(seconds)

    @staticmethod
    async def sleep_ms(milliseconds: float):
        """
        異步睡眠（毫秒）

        Args:
            milliseconds: 睡眠時間（毫秒）
        """
        await asyncio.sleep(milliseconds / 1000)


def convert_blocking_to_async():
    """
    阻塞操作轉異步指南

    1. time.sleep() -> asyncio.sleep()
    2. requests.get() -> AsyncHTTPClient
    3. file.read() -> AsyncFileProcessor.read_file()
    4. 數據庫操作 -> AsyncDatabase.execute()
    """
    return """
# 阻塞操作轉異步轉換指南

## 1. time.sleep() 轉換
之前:
    import time
    time.sleep(1)

之後:
    import asyncio
    await asyncio.sleep(1)

## 2. requests 轉換
之前:
    import requests
    response = requests.get(url)

之後:
    async_client = AsyncHTTPClient()
    response = await async_client.get(url)

## 3. 文件操作轉換
之前:
    with open('file.txt', 'r') as f:
        content = f.read()

之後:
    content = await AsyncFileProcessor.read_file('file.txt')

## 4. 循環轉異步
之前:
    for item in items:
        result = process(item)

之後:
    tasks = [process(item) for item in items]
    results = await asyncio.gather(*tasks)
"""


def benchmark_async_vs_sync(n_operations: int = 100):
    """
    比較異步 vs 同步性能

    Args:
        n_operations: 操作次數
    """
    import time

    print(f"\n性能比較 (n={n_operations}):")

    # 同步版本
    start = time.time()
    for i in range(n_operations):
        time.sleep(0.001)  # 1ms
    sync_time = time.time() - start

    # 異步版本
    async def async_test():
        tasks = [asyncio.sleep(0.001) for _ in range(n_operations)]
        await asyncio.gather(*tasks)

    start = time.time()
    asyncio.run(async_test())
    async_time = time.time() - start

    print(f"  同步操作: {sync_time:.4f} 秒")
    print(f"  異步操作: {async_time:.4f} 秒")
    print(f"  提升:     {sync_time/async_time:.2f}x")


def main():
    """主函數 - 演示用法"""
    print("=" * 80)
    print("Phase 4: Asyncify Tools Demo")
    print("=" * 80)

    # 演示1: 基本異步轉換
    print("\n[1] 異步函數轉換")
    @make_async
    def blocking_function(x):
        time.sleep(0.1)
        return x * 2

    async def test_async():
        result = await blocking_function(5)
        print(f"  異步結果: {result}")

    asyncio.run(test_async())

    # 演示2: 批量異步處理
    print("\n[2] 批量異步處理")
    async def fetch_data(i):
        await asyncio.sleep(0.01)  # 模擬I/O
        return f"Data {i}"

    async def test_batch():
        tasks = [fetch_data(i) for i in range(10)]
        results = await AsyncBatchProcessor.process_batch(tasks, max_concurrent=5)
        print(f"  處理了 {len(results)} 個任務")
        print(f"  前3個結果: {results[:3]}")

    asyncio.run(test_batch())

    # 演示3: 性能比較
    print("\n[3] 性能比較")
    benchmark_async_vs_sync(20)

    print("\n" + "=" * 80)
    print("Asyncify tools ready!")
    print("=" * 80)
    print("\n轉換指南:")
    print(convert_blocking_to_async())


if __name__ == '__main__':
    main()
