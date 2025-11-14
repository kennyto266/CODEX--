"""
图表数据管理器 - Phase 4: User Experience & Visualization
T085 - 创建实时图表更新机制

功能：
- 数据推送
- 图表实时更新
- 高效传输
- 批量更新
- 性能优化
"""

import asyncio
import time
import json
from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timedelta
from collections import deque
import structlog
from dataclasses import dataclass, field

from . import connection_manager

logger = structlog.get_logger("api.websocket.chart")


@dataclass
class ChartDataPoint:
    """图表数据点"""
    timestamp: float
    symbol: str
    data_type: str  # ohlcv, indicator, volume, etc.
    value: float
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChartUpdate:
    """图表更新包"""
    symbol: str
    update_type: str  # add, update, batch
    data_points: List[ChartDataPoint]
    metadata: Dict[str, Any] = field(default_factory=dict)
    update_time: float = field(default_factory=time.time)


class ChartDataManager:
    """图表数据管理器"""

    def __init__(
        self,
        max_symbols: int = 100,
        max_data_points: int = 10000,
        batch_size: int = 100,
        update_interval: float = 1.0  # 秒
    ):
        self.logger = logger
        self.max_symbols = max_symbols
        self.max_data_points = max_data_points
        self.batch_size = batch_size
        self.update_interval = update_interval

        # 数据存储
        self.symbols: Dict[str, Dict[str, deque]] = {}  # symbol -> {data_type -> deque}
        self.subscribers: Dict[str, Set[str]] = {}  # symbol -> set(connection_ids)
        self.update_queues: Dict[str, deque] = {}  # symbol -> update_queue
        self.last_update_time: Dict[str, float] = {}  # symbol -> timestamp

        # 性能指标
        self.metrics = {
            "total_updates": 0,
            "total_data_points": 0,
            "avg_update_latency": 0.0,
            "symbols_tracked": 0
        }

        self._lock = asyncio.Lock()
        self._background_tasks: List[asyncio.Task] = []

    async def add_symbol(
        self,
        symbol: str,
        data_types: List[str] = None
    ) -> bool:
        """添加跟踪的股票代码"""
        if data_types is None:
            data_types = ["ohlcv", "indicators", "volume", "trades"]

        async with self._lock:
            if symbol not in self.symbols:
                self.symbols[symbol] = {}
                self.update_queues[symbol] = deque(maxlen=1000)
                self.last_update_time[symbol] = time.time()
                self.metrics["symbols_tracked"] = len(self.symbols)

            for data_type in data_types:
                if data_type not in self.symbols[symbol]:
                    self.symbols[symbol][data_type] = deque(maxlen=self.max_data_points)

        self.logger.info(
            "添加股票代码到图表跟踪",
            symbol=symbol,
            data_types=data_types,
            total_symbols=len(self.symbols)
        )

        return True

    async def remove_symbol(self, symbol: str) -> bool:
        """移除跟踪的股票代码"""
        async with self._lock:
            if symbol in self.symbols:
                del self.symbols[symbol]
                if symbol in self.update_queues:
                    del self.update_queues[symbol]
                if symbol in self.last_update_time:
                    del self.last_update_time[symbol]
                if symbol in self.subscribers:
                    del self.subscribers[symbol]
                self.metrics["symbols_tracked"] = len(self.symbols)

                self.logger.info(
                    "移除股票代码",
                    symbol=symbol,
                    remaining_symbols=len(self.symbols)
                )
                return True

        return False

    async def add_data_point(
        self,
        symbol: str,
        data_type: str,
        value: float,
        timestamp: Optional[float] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """添加单个数据点"""
        if timestamp is None:
            timestamp = time.time()

        async with self._lock:
            if symbol not in self.symbols or data_type not in self.symbols[symbol]:
                return False

            data_point = ChartDataPoint(
                timestamp=timestamp,
                symbol=symbol,
                data_type=data_type,
                value=value,
                additional_data=additional_data or {}
            )

            self.symbols[symbol][data_type].append(data_point)
            self.last_update_time[symbol] = timestamp
            self.metrics["total_data_points"] += 1

            # 添加到更新队列
            if symbol in self.update_queues:
                self.update_queues[symbol].append(data_point)

        return True

    async def add_data_batch(
        self,
        symbol: str,
        data_points: List[ChartDataPoint]
    ) -> bool:
        """批量添加数据点"""
        async with self._lock:
            if symbol not in self.symbols:
                return False

            for data_point in data_points:
                if data_point.data_type in self.symbols[symbol]:
                    self.symbols[symbol][data_point.data_type].append(data_point)

            if data_points:
                self.last_update_time[symbol] = time.time()
                self.metrics["total_data_points"] += len(data_points)

                # 添加到更新队列
                if symbol in self.update_queues and data_points:
                    self.update_queues[symbol].extend(data_points)

        return True

    async def get_data_points(
        self,
        symbol: str,
        data_type: str,
        limit: int = 1000,
        since: Optional[float] = None
    ) -> List[ChartDataPoint]:
        """获取数据点"""
        async with self._lock:
            if symbol not in self.symbols or data_type not in self.symbols[symbol]:
                return []

            data_deque = self.symbols[symbol][data_type]
            points = list(data_deque)

            # 时间过滤
            if since is not None:
                points = [p for p in points if p.timestamp >= since]

            # 限制数量
            if limit > 0:
                points = points[-limit:]

        return points

    async def add_subscriber(self, symbol: str, connection_id: str):
        """添加订阅者"""
        async with self._lock:
            if symbol not in self.subscribers:
                self.subscribers[symbol] = set()
            self.subscribers[symbol].add(connection_id)

            # 确保股票代码已添加
            if symbol not in self.symbols:
                await self.add_symbol(symbol)

        self.logger.info(
            "客户端订阅图表更新",
            symbol=symbol,
            connection_id=connection_id
        )

    async def remove_subscriber(self, symbol: str, connection_id: str):
        """移除订阅者"""
        async with self._lock:
            if symbol in self.subscribers:
                self.subscribers[symbol].discard(connection_id)

        self.logger.info(
            "客户端取消订阅图表更新",
            symbol=symbol,
            connection_id=connection_id
        )

    async def get_subscriber_count(self, symbol: str) -> int:
        """获取订阅者数量"""
        async with self._lock:
            return len(self.subscribers.get(symbol, set()))

    async def broadcast_update(
        self,
        symbol: str,
        update_type: str = "add",
        data_types: Optional[List[str]] = None,
        batch_size: Optional[int] = None
    ) -> int:
        """广播图表更新"""
        if batch_size is None:
            batch_size = self.batch_size

        if symbol not in self.update_queues:
            return 0

        # 获取数据点
        data_points = []
        for _ in range(min(batch_size, len(self.update_queues[symbol]))):
            if self.update_queues[symbol]:
                data_points.append(self.update_queues[symbol].popleft())

        if not data_points:
            return 0

        # 准备广播数据
        update = ChartUpdate(
            symbol=symbol,
            update_type=update_type,
            data_points=data_points,
            metadata={
                "data_types": data_types or [dp.data_type for dp in data_points],
                "batch_size": len(data_points)
            }
        )

        # 广播到订阅者
        subscribers = self.subscribers.get(symbol, set())
        success_count = 0

        for connection_id in subscribers:
            try:
                await connection_manager.send_personal_message(
                    connection_id,
                    {
                        "type": "chart_update",
                        "symbol": symbol,
                        "update_type": update_type,
                        "data_points": [
                            {
                                "timestamp": dp.timestamp,
                                "data_type": dp.data_type,
                                "value": dp.value,
                                "additional_data": dp.additional_data
                            }
                            for dp in data_points
                        ],
                        "metadata": update.metadata,
                        "timestamp": datetime.now().isoformat()
                    }
                )
                success_count += 1

            except Exception as e:
                self.logger.error(
                    "发送图表更新失败",
                    symbol=symbol,
                    connection_id=connection_id,
                    error=str(e)
                )

        self.metrics["total_updates"] += 1
        return success_count

    async def broadcast_all_pending_updates(self) -> Dict[str, int]:
        """广播所有待处理的更新"""
        results = {}

        async with self._lock:
            symbols_to_update = list(self.update_queues.keys())

        for symbol in symbols_to_update:
            try:
                count = await self.broadcast_update(symbol)
                results[symbol] = count
            except Exception as e:
                self.logger.error(
                    "广播更新异常",
                    symbol=symbol,
                    error=str(e)
                )
                results[symbol] = 0

        return results

    async def get_symbol_status(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取股票代码状态"""
        async with self._lock:
            if symbol not in self.symbols:
                return None

            status = {
                "symbol": symbol,
                "is_tracked": True,
                "data_types": list(self.symbols[symbol].keys()),
                "data_counts": {
                    data_type: len(deque_)
                    for data_type, deque_ in self.symbols[symbol].items()
                },
                "subscriber_count": len(self.subscribers.get(symbol, set())),
                "last_update_time": self.last_update_time.get(symbol),
                "pending_updates": len(self.update_queues.get(symbol, []))
            }

        return status

    async def get_all_symbols(self) -> List[str]:
        """获取所有跟踪的股票代码"""
        async with self._lock:
            return list(self.symbols.keys())

    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return self.metrics.copy()

    async def start_background_task(self):
        """启动后台任务"""
        self.logger.info("启动图表数据管理器后台任务")

        async def update_task():
            """定期广播更新任务"""
            while True:
                try:
                    start_time = time.time()
                    results = await self.broadcast_all_pending_updates()

                    # 更新延迟指标
                    latency = time.time() - start_time
                    self.metrics["avg_update_latency"] = (
                        (self.metrics["avg_update_latency"] * 0.9) + (latency * 0.1)
                    )

                    # 等待下次更新
                    await asyncio.sleep(self.update_interval)

                except Exception as e:
                    self.logger.error("更新任务异常", error=str(e))
                    await asyncio.sleep(self.update_interval)

        update_task_handle = asyncio.create_task(update_task())
        self._background_tasks.append(update_task_handle)

        return self._background_tasks

    async def stop_background_tasks(self):
        """停止后台任务"""
        for task in self._background_tasks:
            if not task.done():
                task.cancel()

        self._background_tasks.clear()
        self.logger.info("图表数据管理器后台任务已停止")


# 便捷函数
async def push_ohlcv_data(
    manager: ChartDataManager,
    symbol: str,
    ohlcv: Dict[str, float],
    timestamp: Optional[float] = None
) -> bool:
    """推送OHLCV数据（便捷函数）"""
    if timestamp is None:
        timestamp = time.time()

    success = True

    # 推送每个OHLCV值
    for key, value in ohlcv.items():
        if not await manager.add_data_point(
            symbol=symbol,
            data_type="ohlcv",
            value=value,
            timestamp=timestamp,
            additional_data={"field": key}
        ):
            success = False

    return success


async def push_indicator_data(
    manager: ChartDataManager,
    symbol: str,
    indicator_name: str,
    value: float,
    timestamp: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """推送技术指标数据（便捷函数）"""
    return await manager.add_data_point(
        symbol=symbol,
        data_type=f"indicator_{indicator_name}",
        value=value,
        timestamp=timestamp,
        additional_data=metadata or {}
    )


async def push_trade_data(
    manager: ChartDataManager,
    symbol: str,
    price: float,
    volume: float,
    timestamp: Optional[float] = None,
    side: Optional[str] = None
) -> bool:
    """推送交易数据（便捷函数）"""
    return await manager.add_data_point(
        symbol=symbol,
        data_type="trade",
        value=price,
        timestamp=timestamp,
        additional_data={
            "volume": volume,
            "side": side or "unknown"
        }
    )


# 示例：实时数据推送流程
"""
# 1. 添加股票代码
await chart_manager.add_symbol("0700.HK", ["ohlcv", "indicators", "volume"])

# 2. 客户端订阅
await chart_manager.add_subscriber("0700.HK", connection_id)

# 3. 推送实时数据
await push_ohlcv_data(
    chart_manager,
    "0700.HK",
    {"open": 350.0, "high": 360.0, "low": 345.0, "close": 355.0, "volume": 1000000}
)

await push_indicator_data(
    chart_manager,
    "0700.HK",
    "KDJ_K",
    65.5,
    additional_data={"D": 60.0, "J": 75.0}
)

# 4. 系统自动广播到所有订阅者
"""


# 导出
__all__ = [
    "ChartDataManager",
    "ChartDataPoint",
    "ChartUpdate",
    "push_ohlcv_data",
    "push_indicator_data",
    "push_trade_data"
]
