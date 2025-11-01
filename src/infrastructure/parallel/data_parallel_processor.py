"""
數據並行處理器

提供：
- 數據分塊 (chunking)
- 內存使用優化
- 動態負載均衡
- 並行處理監控
"""

import asyncio
import gc
import psutil
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from src.core.logging import get_logger

logger = get_logger("data_parallel_processor")


@dataclass
class ChunkConfig:
    """分塊配置"""
    chunk_size: int = 1000
    max_memory_mb: int = 1024
    memory_threshold: float = 0.8
    auto_adjust: bool = True


class DataParallelProcessor:
    """數據並行處理器"""

    def __init__(self, config: ChunkConfig):
        self.config = config
        self.logger = get_logger("data_parallel_processor")
        self._monitoring_active = False

    async def process_in_chunks(
        self,
        data: List[Any],
        processor_func: Callable,
        max_workers: int = 4
    ) -> List[Any]:
        """分塊處理數據"""
        results = []

        # 動態調整塊大小
        chunk_size = self._calculate_optimal_chunk_size(data)

        # 分塊處理
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            self.logger.debug(f"Processing chunk {i//chunk_size + 1}: {len(chunk)} items")

            # 並行處理當前塊
            chunk_results = await self._process_chunk_parallel(
                chunk, processor_func, max_workers
            )
            results.extend(chunk_results)

            # 清理內存
            gc.collect()

            # 檢查內存使用
            await self._check_memory_usage()

        return results

    def _calculate_optimal_chunk_size(self, data: List[Any]) -> int:
        """計算最優塊大小"""
        if not self.config.auto_adjust:
            return self.config.chunk_size

        # 獲取當前內存使用情況
        memory_percent = psutil.virtual_memory().percent / 100
        available_memory = psutil.virtual_memory().available

        # 根據可用內存動態調整
        if memory_percent > self.config.memory_threshold:
            # 內存使用率高，減小塊大小
            chunk_size = max(self.config.chunk_size // 2, 100)
        elif memory_percent < 0.3:
            # 內存使用率低，可以增大塊大小
            chunk_size = min(self.config.chunk_size * 2, 10000)
        else:
            chunk_size = self.config.chunk_size

        # 限制塊大小不超過數據總長度
        return min(chunk_size, len(data))

    async def _process_chunk_parallel(
        self,
        chunk: List[Any],
        processor_func: Callable,
        max_workers: int
    ) -> List[Any]:
        """並行處理單個塊"""
        loop = asyncio.get_event_loop()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任務
            futures = [
                loop.run_in_executor(executor, processor_func, item)
                for item in chunk
            ]

            # 等待所有任務完成
            results = await asyncio.gather(*futures, return_exceptions=True)

            # 處理異常
            return [
                result for result in results
                if not isinstance(result, Exception)
            ]

    async def _check_memory_usage(self):
        """檢查內存使用情況"""
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        if memory_percent > self.config.memory_threshold * 100:
            self.logger.warning(
                f"High memory usage: {memory_percent:.1f}%. "
                f"Available: {memory.available / 1024 / 1024:.0f} MB"
            )
            # 觸發垃圾回收
            gc.collect()
