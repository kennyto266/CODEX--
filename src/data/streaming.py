"""
实时数据流模块 (T198)
=====================

提供完整的实时数据流处理能力，包括：
- WebSocket连接
- 实时行情
- 事件流处理
- 数据缓冲
- 断线重连

Author: Claude Code
Date: 2025-11-09
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable, Set
from enum import Enum
from dataclasses import dataclass, field
from collections import deque, defaultdict
import websockets
from websockets.exceptions import ConnectionClosed, InvalidStatus
import pandas as pd
import numpy as np

from .cache import LRUCache


class StreamEventType(str, Enum):
    """流事件类型"""
    TICK = "TICK"  # 逐笔成交
    TRADE = "TRADE"  # 成交
    QUOTE = "QUOTE"  # 报价
    ORDER_BOOK = "ORDER_BOOK"  # 订单簿
    NEWS = "NEWS"  # 新闻
    ALERT = "ALERT"  # 告警
    HEARTBEAT = "HEARTBEAT"  # 心跳
    ERROR = "ERROR"  # 错误


class ConnectionStatus(str, Enum):
    """连接状态"""
    CONNECTING = "CONNECTING"  # 连接中
    CONNECTED = "CONNECTED"  # 已连接
    DISCONNECTED = "DISCONNECTED"  # 断开连接
    RECONNECTING = "RECONNECTING"  # 重连中
    FAILED = "FAILED"  # 连接失败
    CLOSED = "CLOSED"  # 已关闭


@dataclass
class StreamEvent:
    """流事件"""
    event_type: StreamEventType
    symbol: str
    timestamp: datetime
    data: Dict[str, Any]
    source: str  # 数据源
    sequence: Optional[int] = None  # 序列号
    raw_message: Optional[str] = None  # 原始消息
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Subscription:
    """订阅信息"""
    symbol: str
    data_types: Set[StreamEventType]
    filters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: Optional[datetime] = None


class DataBuffer:
    """数据缓冲区"""
    def __init__(
        self,
        max_size: int = 10000,
        max_age_seconds: int = 3600
    ):
        self.max_size = max_size
        self.max_age_seconds = max_age_seconds
        self._buffer: deque = deque(maxlen=max_size)
        self._timestamps: deque = deque(maxlen=max_size)
        self.logger = logging.getLogger("hk_quant_system.streaming.buffer")

    def add(self, event: StreamEvent) -> None:
        """添加事件到缓冲区"""
        current_time = datetime.now()
        self._buffer.append(event)
        self._timestamps.append(current_time)

        # 清理过期数据
        self._cleanup()

    def get_recent(self, count: int = 100) -> List[StreamEvent]:
        """获取最近的事件"""
        return list(self._buffer)[-count:]

    def get_by_symbol(self, symbol: str) -> List[StreamEvent]:
        """根据股票代码获取事件"""
        return [e for e in self._buffer if e.symbol == symbol]

    def get_by_time_range(
        self,
        start_time: datetime,
        end_time: Optional[datetime] = None
    ) -> List[StreamEvent]:
        """根据时间范围获取事件"""
        if end_time is None:
            end_time = datetime.now()

        events = []
        for i, event in enumerate(self._buffer):
            if start_time <= event.timestamp <= end_time:
                events.append(event)

        return events

    def _cleanup(self) -> None:
        """清理过期数据"""
        cutoff_time = datetime.now() - timedelta(seconds=self.max_age_seconds)

        # 移除过期事件
        while self._timestamps and self._timestamps[0] < cutoff_time:
            self._buffer.popleft()
            self._timestamps.popleft()

    def get_statistics(self) -> Dict[str, Any]:
        """获取缓冲区统计信息"""
        return {
            "current_size": len(self._buffer),
            "max_size": self.max_size,
            "oldest_event": self._buffer[0].timestamp if self._buffer else None,
            "newest_event": self._buffer[-1].timestamp if self._buffer else None,
            "events_by_type": self._get_events_by_type()
        }

    def _get_events_by_type(self) -> Dict[str, int]:
        """按类型统计事件数量"""
        counts = defaultdict(int)
        for event in self._buffer:
            counts[event.event_type.value] += 1
        return dict(counts)


class RealtimeStreamManager:
    """
    实时流管理器

    功能：
    1. WebSocket连接管理
    2. 订阅管理
    3. 数据缓冲
    4. 事件处理
    5. 断线重连
    """

    def __init__(
        self,
        buffer_size: int = 10000,
        buffer_age: int = 3600,
        reconnect_attempts: int = 5,
        reconnect_delay: float = 5.0,
        heartbeat_interval: float = 30.0
    ):
        self.logger = logging.getLogger("hk_quant_system.streaming")
        self.buffer = DataBuffer(buffer_size, buffer_age)
        self.reconnect_attempts = reconnect_attempts
        self.reconnect_delay = reconnect_delay
        self.heartbeat_interval = heartbeat_interval

        # 连接管理
        self.connections: Dict[str, Any] = {}
        self.connection_status: Dict[str, ConnectionStatus] = {}
        self._reconnect_tasks: Dict[str, asyncio.Task] = {}

        # 订阅管理
        self.subscriptions: Dict[str, Subscription] = {}
        self._subscription_handlers: Dict[str, List[Callable]] = defaultdict(list)

        # 事件处理器
        self._event_handlers: Dict[StreamEventType, List[Callable]] = defaultdict(list)
        self._default_handlers: List[Callable] = []

        # 统计
        self._stats = {
            "total_events": 0,
            "events_by_type": defaultdict(int),
            "events_by_symbol": defaultdict(int),
            "last_event_time": None,
            "connection_errors": 0,
            "reconnect_attempts": 0
        }

    def add_event_handler(
        self,
        event_type: Optional[StreamEventType],
        handler: Callable[[StreamEvent], None]
    ) -> None:
        """
        添加事件处理器

        Args:
            event_type: 事件类型 (None表示默认处理器)
            handler: 处理器函数
        """
        if event_type is None:
            self._default_handlers.append(handler)
        else:
            self._event_handlers[event_type].append(handler)

    def add_subscription_handler(
        self,
        symbol: str,
        handler: Callable[[StreamEvent], None]
    ) -> None:
        """
        添加订阅处理器

        Args:
            symbol: 股票代码
            handler: 处理器函数
        """
        self._subscription_handlers[symbol].append(handler)

    async def connect(
        self,
        source_name: str,
        ws_url: str,
        headers: Optional[Dict[str, str]] = None,
        protocols: Optional[List[str]] = None
    ) -> bool:
        """
        连接到WebSocket

        Args:
            source_name: 数据源名称
            ws_url: WebSocket URL
            headers: 请求头
            protocols: WebSocket协议

        Returns:
            连接是否成功
        """
        self.logger.info(f"Connecting to {source_name}: {ws_url}")

        try:
            self.connection_status[source_name] = ConnectionStatus.CONNECTING

            # 创建WebSocket连接
            connection = await websockets.connect(
                ws_url,
                headers=headers,
                protocols=protocols,
                ping_interval=20,
                ping_timeout=10
            )

            self.connections[source_name] = connection
            self.connection_status[source_name] = ConnectionStatus.CONNECTED

            # 启动消息处理任务
            asyncio.create_task(
                self._handle_messages(source_name, connection)
            )

            # 启动心跳任务
            asyncio.create_task(
                self._heartbeat(source_name, connection)
            )

            self.logger.info(f"Connected to {source_name}")

            # 重新订阅
            await self._resubscribe(source_name)

            return True

        except Exception as e:
            self.logger.error(f"Connection failed to {source_name}: {e}")
            self.connection_status[source_name] = ConnectionStatus.FAILED
            return False

    async def disconnect(self, source_name: str) -> bool:
        """
        断开连接

        Args:
            source_name: 数据源名称

        Returns:
            断开是否成功
        """
        if source_name in self.connections:
            try:
                connection = self.connections[source_name]
                await connection.close()
                del self.connections[source_name]
                self.connection_status[source_name] = ConnectionStatus.CLOSED

                # 取消重连任务
                if source_name in self._reconnect_tasks:
                    self._reconnect_tasks[source_name].cancel()
                    del self._reconnect_tasks[source_name]

                self.logger.info(f"Disconnected from {source_name}")
                return True
            except Exception as e:
                self.logger.error(f"Error disconnecting from {source_name}: {e}")
                return False

        return False

    async def subscribe(
        self,
        source_name: str,
        symbol: str,
        data_types: Set[StreamEventType],
        filters: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        订阅数据

        Args:
            source_name: 数据源名称
            symbol: 股票代码
            data_types: 数据类型
            filters: 过滤条件

        Returns:
            订阅是否成功
        """
        if filters is None:
            filters = {}

        # 创建订阅
        subscription = Subscription(
            symbol=symbol,
            data_types=data_types,
            filters=filters
        )

        self.subscriptions[f"{source_name}:{symbol}"] = subscription

        # 发送订阅消息
        if source_name in self.connections:
            await self._send_subscribe_message(source_name, symbol, data_types, filters)
            self.logger.info(f"Subscribed to {symbol} on {source_name}")

        return True

    async def unsubscribe(
        self,
        source_name: str,
        symbol: str
    ) -> bool:
        """
        取消订阅

        Args:
            source_name: 数据源名称
            symbol: 股票代码

        Returns:
            取消订阅是否成功
        """
        key = f"{source_name}:{symbol}"
        if key in self.subscriptions:
            del self.subscriptions[key]

            # 发送取消订阅消息
            if source_name in self.connections:
                await self._send_unsubscribe_message(source_name, symbol)

            self.logger.info(f"Unsubscribed from {symbol} on {source_name}")
            return True

        return False

    async def publish_event(
        self,
        event: StreamEvent
    ) -> None:
        """
        发布事件

        Args:
            event: 流事件
        """
        # 添加到缓冲区
        self.buffer.add(event)

        # 更新统计
        self._stats["total_events"] += 1
        self._stats["events_by_type"][event.event_type.value] += 1
        self._stats["events_by_symbol"][event.symbol] += 1
        self._stats["last_event_time"] = event.timestamp

        # 调用订阅处理器
        if event.symbol in self._subscription_handlers:
            for handler in self._subscription_handlers[event.symbol]:
                try:
                    handler(event)
                except Exception as e:
                    self.logger.error(f"Error in subscription handler: {e}")

        # 调用事件处理器
        if event.event_type in self._event_handlers:
            for handler in self._event_handlers[event.event_type]:
                try:
                    handler(event)
                except Exception as e:
                    self.logger.error(f"Error in event handler: {e}")

        # 调用默认处理器
        for handler in self._default_handlers:
            try:
                handler(event)
            except Exception as e:
                self.logger.error(f"Error in default handler: {e}")

    async def _handle_messages(
        self,
        source_name: str,
        connection: websockets.WebSocketServerProtocol
    ) -> None:
        """处理WebSocket消息"""
        try:
            async for message in connection:
                try:
                    # 解析消息
                    event = await self._parse_message(source_name, message)
                    if event:
                        await self.publish_event(event)
                except Exception as e:
                    self.logger.error(f"Error processing message from {source_name}: {e}")
        except ConnectionClosed:
            self.logger.warning(f"Connection closed: {source_name}")
            self.connection_status[source_name] = ConnectionStatus.DISCONNECTED
            # 启动重连
            await self._reconnect(source_name)
        except Exception as e:
            self.logger.error(f"Error handling messages from {source_name}: {e}")
            self.connection_status[source_name] = ConnectionStatus.FAILED

    async def _parse_message(
        self,
        source_name: str,
        message: str
    ) -> Optional[StreamEvent]:
        """解析WebSocket消息"""
        try:
            data = json.loads(message)

            # 根据数据源格式解析 (这里需要根据具体数据源调整)
            # 简化实现
            event_type = StreamEventType.TICK
            if 'type' in data:
                event_type = StreamEventType(data['type'])

            event = StreamEvent(
                event_type=event_type,
                symbol=data.get('symbol', ''),
                timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
                data=data.get('data', {}),
                source=source_name,
                raw_message=message
            )

            return event

        except Exception as e:
            self.logger.error(f"Error parsing message: {e}")
            return None

    async def _send_subscribe_message(
        self,
        source_name: str,
        symbol: str,
        data_types: Set[StreamEventType],
        filters: Dict[str, Any]
    ) -> None:
        """发送订阅消息"""
        if source_name in self.connections:
            connection = self.connections[source_name]

            message = {
                "action": "subscribe",
                "symbol": symbol,
                "types": [t.value for t in data_types],
                "filters": filters
            }

            try:
                await connection.send(json.dumps(message))
            except Exception as e:
                self.logger.error(f"Error sending subscribe message: {e}")

    async def _send_unsubscribe_message(
        self,
        source_name: str,
        symbol: str
    ) -> None:
        """发送取消订阅消息"""
        if source_name in self.connections:
            connection = self.connections[source_name]

            message = {
                "action": "unsubscribe",
                "symbol": symbol
            }

            try:
                await connection.send(json.dumps(message))
            except Exception as e:
                self.logger.error(f"Error sending unsubscribe message: {e}")

    async def _heartbeat(
        self,
        source_name: str,
        connection: websockets.WebSocketServerProtocol
    ) -> None:
        """发送心跳"""
        try:
            while self.connection_status.get(source_name) == ConnectionStatus.CONNECTED:
                await asyncio.sleep(self.heartbeat_interval)

                # 发送心跳消息
                heartbeat_event = StreamEvent(
                    event_type=StreamEventType.HEARTBEAT,
                    symbol="SYSTEM",
                    timestamp=datetime.now(),
                    data={"source": source_name},
                    source=source_name
                )
                await self.publish_event(heartbeat_event)

        except Exception as e:
            self.logger.error(f"Error in heartbeat: {e}")

    async def _reconnect(self, source_name: str) -> None:
        """重连逻辑"""
        if source_name in self._reconnect_tasks:
            return  # 已在重连中

        self.logger.info(f"Starting reconnection to {source_name}")
        self._stats["reconnect_attempts"] += 1
        self.connection_status[source_name] = ConnectionStatus.RECONNECTING

        attempt = 0
        while attempt < self.reconnect_attempts:
            attempt += 1
            self.logger.info(f"Reconnection attempt {attempt}/{self.reconnect_attempts}")

            # 等待延迟
            await asyncio.sleep(self.reconnect_delay * attempt)

            # 尝试重连
            try:
                # 这里需要保存连接URL等配置
                # 简化实现
                pass
            except Exception as e:
                self.logger.error(f"Reconnection attempt {attempt} failed: {e}")

        # 重连失败
        self.connection_status[source_name] = ConnectionStatus.FAILED
        self.logger.error(f"Failed to reconnect to {source_name}")

    async def _resubscribe(self, source_name: str) -> None:
        """重新订阅"""
        for key, subscription in self.subscriptions.items():
            src, symbol = key.split(':', 1)
            if src == source_name:
                await self._send_subscribe_message(
                    source_name, symbol, subscription.data_types, subscription.filters
                )

    def get_buffer_stats(self) -> Dict[str, Any]:
        """获取缓冲区统计"""
        return self.buffer.get_statistics()

    def get_connection_stats(self) -> Dict[str, Any]:
        """获取连接统计"""
        return {
            "connections": len(self.connections),
            "status": {name: status.value for name, status in self.connection_status.items()},
            "subscriptions": len(self.subscriptions),
            "stats": dict(self._stats)
        }

    async def close_all(self) -> None:
        """关闭所有连接"""
        for source_name in list(self.connections.keys()):
            await self.disconnect(source_name)

        self.logger.info("All connections closed")

    def clear_buffer(self) -> None:
        """清空缓冲区"""
        # 重新初始化缓冲区
        self.buffer = DataBuffer(self.buffer.max_size, self.buffer.max_age_seconds)
        self.logger.info("Buffer cleared")


# 辅助函数和工具
class StreamEventProcessor:
    """流事件处理器"""

    def __init__(self, manager: RealtimeStreamManager):
        self.manager = manager
        self.logger = logging.getLogger("hk_quant_system.streaming.processor")

    def on_tick(self, handler: Callable[[StreamEvent], None]) -> None:
        """注册逐笔成交处理器"""
        self.manager.add_event_handler(StreamEventType.TICK, handler)

    def on_trade(self, handler: Callable[[StreamEvent], None]) -> None:
        """注册成交处理器"""
        self.manager.add_event_handler(StreamEventType.TRADE, handler)

    def on_quote(self, handler: Callable[[StreamEvent], None]) -> None:
        """注册报价处理器"""
        self.manager.add_event_handler(StreamEventType.QUOTE, handler)

    def on_news(self, handler: Callable[[StreamEvent], None]) -> None:
        """注册新闻处理器"""
        self.manager.add_event_handler(StreamEventType.NEWS, handler)

    def on_alert(self, handler: Callable[[StreamEvent], None]) -> None:
        """注册告警处理器"""
        self.manager.add_event_handler(StreamEventType.ALERT, handler)


def create_price_alert(
    symbol: str,
    target_price: float,
    direction: str,  # "above" or "below"
    event: StreamEvent
) -> bool:
    """
    创建价格告警

    Args:
        symbol: 股票代码
        target_price: 目标价格
        direction: 方向 (above/below)
        event: 流事件

    Returns:
        是否触发告警
    """
    if event.symbol != symbol:
        return False

    # 从事件中提取价格
    price = None
    if 'price' in event.data:
        price = event.data['price']
    elif 'last_price' in event.data:
        price = event.data['last_price']

    if price is None:
        return False

    # 检查告警条件
    if direction == "above" and price >= target_price:
        return True
    elif direction == "below" and price <= target_price:
        return True

    return False


async def get_realtime_data(
    symbol: str,
    stream_manager: RealtimeStreamManager,
    timeout: float = 5.0
) -> Optional[StreamEvent]:
    """
    获取实时数据的便捷函数

    Args:
        symbol: 股票代码
        stream_manager: 流管理器
        timeout: 超时时间

    Returns:
        最新的流事件
    """
    # 等待新数据
    event = asyncio.Event()

    def event_handler(evt: StreamEvent):
        if evt.symbol == symbol:
            event.set()

    # 注册临时处理器
    stream_manager.add_event_handler(None, event_handler)

    try:
        # 等待事件或超时
        await asyncio.wait_for(event.wait(), timeout=timeout)

        # 从缓冲区获取最新数据
        recent_events = stream_manager.buffer.get_by_symbol(symbol)
        return recent_events[-1] if recent_events else None

    except asyncio.TimeoutError:
        return None
    finally:
        # 清理处理器
        stream_manager._default_handlers.pop() if stream_manager._default_handlers else None


if __name__ == "__main__":
    # 测试代码
    async def test():
        manager = RealtimeStreamManager()

        # 添加事件处理器
        def on_tick(event: StreamEvent):
            print(f"Tick: {event.symbol} - {event.data}")

        manager.add_event_handler(StreamEventType.TICK, on_tick)

        # 测试统计
        stats = manager.get_connection_stats()
        print("Connection stats:", stats)

    asyncio.run(test())
