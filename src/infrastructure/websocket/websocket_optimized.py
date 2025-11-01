"""
優化的WebSocket管理器

提供：
- 連接池管理
- 消息隊列緩衝
- 心跳檢測和重連
- 序列化優化 (MessagePack)
- 監控指標
"""

import asyncio
import json
import time
from collections import deque, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Set
from uuid import uuid4

from src.core.logging import get_logger

logger = get_logger("websocket_optimized")


@dataclass
class WebSocketConnection:
    """WebSocket連接"""
    connection_id: str
    ws: Any
    user_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    last_ping: float = field(default_factory=time.time)
    message_count: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    is_alive: bool = True
    ping_interval: float = 30.0  # 秒
    reconnect_count: int = 0


@dataclass
class MessageBuffer:
    """消息緩衝"""
    connection_id: str
    messages: deque = field(default_factory=lambda: deque(maxlen=1000))
    max_size: int = 1000
    flush_interval: float = 1.0  # 秒


class ConnectionPool:
    """連接池"""

    def __init__(self, max_connections: int = 1000):
        self.max_connections = max_connections
        self._connections: Dict[str, WebSocketConnection] = {}
        self._lock = asyncio.Lock()
        self._waiting_clients: asyncio.Queue = asyncio.Queue()

    async def acquire(self) -> Optional[WebSocketConnection]:
        """獲取連接"""
        async with self._lock:
            if len(self._connections) >= self.max_connections:
                return None

            connection_id = str(uuid4())
            # 創建占位連接
            connection = WebSocketConnection(connection_id=connection_id, ws=None)
            self._connections[connection_id] = connection
            return connection

    async def release(self, connection: WebSocketConnection):
        """釋放連接"""
        async with self._lock:
            if connection.connection_id in self._connections:
                del self._connections[connection.connection_id]

    async def get_connection(self, connection_id: str) -> Optional[WebSocketConnection]:
        """獲取指定連接"""
        return self._connections.get(connection_id)

    async def get_all_connections(self) -> List[WebSocketConnection]:
        """獲取所有連接"""
        async with self._lock:
            return list(self._connections.values())

    async def cleanup_stale_connections(self, timeout: float = 300):
        """清理僵屍連接"""
        current_time = time.time()
        async with self._lock:
            stale_ids = []
            for conn_id, conn in self._connections.items():
                if current_time - conn.last_ping > timeout:
                    stale_ids.append(conn_id)

            for conn_id in stale_ids:
                del self._connections[conn_id]

            return len(stale_ids)


class MessageQueue:
    """消息隊列"""

    def __init__(self, max_queue_size: int = 10000):
        self.max_queue_size = max_queue_size
        self._queues: Dict[str, MessageBuffer] = {}
        self._lock = asyncio.Lock()

    async def add_message(self, connection_id: str, message: Any, serialize: bool = True):
        """添加消息到隊列"""
        async with self._lock:
            if connection_id not in self._queues:
                self._queues[connection_id] = MessageBuffer(connection_id)

            buffer = self._queues[connection_id]

            # 序列化管理
            if serialize and not isinstance(message, (str, bytes)):
                message = json.dumps(message)

            if len(buffer.messages) < buffer.max_size:
                buffer.messages.append(message)
            else:
                # 移除最舊消息
                buffer.messages.popleft()
                buffer.messages.append(message)

    async def get_messages(self, connection_id: str, max_messages: int = 100) -> List[Any]:
        """獲取消息"""
        async with self._lock:
            buffer = self._queues.get(connection_id)
            if not buffer:
                return []

            messages = []
            for _ in range(min(max_messages, len(buffer.messages))):
                if buffer.messages:
                    messages.append(buffer.messages.popleft())

            return messages

    async def clear_queue(self, connection_id: str):
        """清空隊列"""
        async with self._lock:
            if connection_id in self._queues:
                self._queues[connection_id].messages.clear()

    async def get_queue_size(self, connection_id: str) -> int:
        """獲取隊列大小"""
        buffer = self._queues.get(connection_id)
        return len(buffer.messages) if buffer else 0


class HeartbeatManager:
    """心跳管理器"""

    def __init__(self, ping_interval: float = 30.0, timeout: float = 90.0):
        self.ping_interval = ping_interval
        self.timeout = timeout
        self._tasks: Dict[str, asyncio.Task] = {}
        self._callbacks: List[Callable] = []

    def add_callback(self, callback: Callable[[str, str], None]):
        """添加心跳回調"""
        self._callbacks.append(callback)

    async def start_heartbeat(self, connection: WebSocketConnection, ws: Any):
        """啟用心跳"""
        if connection.connection_id in self._tasks:
            return

        task = asyncio.create_task(self._heartbeat_loop(connection, ws))
        self._tasks[connection.connection_id] = task

    async def stop_heartbeat(self, connection_id: str):
        """停止心跳"""
        task = self._tasks.pop(connection_id, None)
        if task and not task.done():
            task.cancel()

    async def _heartbeat_loop(self, connection: WebSocketConnection, ws: Any):
        """心跳循環"""
        while connection.is_alive:
            try:
                await asyncio.sleep(self.ping_interval)

                if not connection.is_alive:
                    break

                # 發送ping
                current_time = time.time()
                if current_time - connection.last_ping < self.ping_interval:
                    try:
                        await ws.send(json.dumps({"type": "ping", "timestamp": current_time}))
                        connection.last_ping = current_time
                    except Exception as e:
                        logger.warning(f"Ping failed for {connection.connection_id}: {e}")
                        connection.is_alive = False
                        break

                # 檢查超時
                if current_time - connection.last_ping > self.timeout:
                    logger.warning(f"Connection {connection.connection_id} timeout")
                    connection.is_alive = False
                    await self._notify_timeout(connection.connection_id)
                    break

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                connection.is_alive = False
                break

    async def _notify_timeout(self, connection_id: str):
        """通知超時"""
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(connection_id, "timeout")
                else:
                    callback(connection_id, "timeout")
            except Exception as e:
                logger.error(f"Timeout callback error: {e}")


class WebSocketMonitor:
    """WebSocket監控"""

    def __init__(self):
        self._metrics: Dict[str, Any] = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "bytes_sent": 0,
            "bytes_received": 0,
            "errors": 0,
            "reconnects": 0,
            "avg_message_size": 0,
            "peak_concurrent_connections": 0,
            "connection_duration_avg": 0
        }

        self._connection_stats: Dict[str, Dict] = defaultdict(dict)
        self._metrics_history: deque = deque(maxlen=1000)

    def update_metrics(self, connection: WebSocketConnection, message_size: int = 0):
        """更新指標"""
        current_time = time.time()

        # 更新連接指標
        stats = self._connection_stats[connection.connection_id]
        stats["last_activity"] = current_time
        stats["message_count"] = connection.message_count
        stats["bytes_sent"] = connection.bytes_sent
        stats["bytes_received"] = connection.bytes_received

        # 更新總體指標
        self._metrics["active_connections"] = len([
            conn for conn in stats.values()
            if conn.get("last_activity", 0) > current_time - 60
        ])

        if message_size > 0:
            self._metrics["messages_sent"] += 1
            self._metrics["bytes_sent"] += message_size

    def record_error(self, connection_id: str, error: str):
        """記錄錯誤"""
        self._metrics["errors"] += 1
        stats = self._connection_stats[connection_id]
        stats["last_error"] = {
            "error": error,
            "timestamp": time.time()
        }

    def record_reconnect(self, connection_id: str):
        """記錄重連"""
        self._metrics["reconnects"] += 1
        stats = self._connection_stats[connection_id]
        stats["reconnect_count"] = stats.get("reconnect_count", 0) + 1

    def get_metrics(self) -> Dict[str, Any]:
        """獲取指標"""
        return self._metrics.copy()

    def get_connection_stats(self, connection_id: str) -> Dict:
        """獲取連接統計"""
        return self._connection_stats.get(connection_id, {})

    def get_all_stats(self) -> Dict[str, Any]:
        """獲取所有統計"""
        return {
            "metrics": self._metrics,
            "connection_stats": dict(self._connection_stats)
        }


class OptimizedWebSocketManager:
    """優化的WebSocket管理器"""

    def __init__(
        self,
        max_connections: int = 1000,
        max_message_size: int = 1024 * 1024,  # 1MB
        use_msgpack: bool = True
    ):
        self.max_connections = max_connections
        self.max_message_size = max_message_size
        self.use_msgpack = use_msgpack

        # 初始化組件
        self._connection_pool = ConnectionPool(max_connections)
        self._message_queue = MessageQueue()
        self._heartbeat_manager = HeartbeatManager()
        self._monitor = WebSocketMonitor()

        self.logger = get_logger("optimized_websocket_manager")

    async def connect(
        self,
        ws: Any,
        user_id: Optional[str] = None
    ) -> str:
        """建立連接"""
        connection = await self._connection_pool.acquire()
        if not connection:
            raise RuntimeError("Connection pool exhausted")

        connection.ws = ws
        connection.user_id = user_id
        connection.last_ping = time.time()

        # 啟用心跳
        await self._heartbeat_manager.start_heartbeat(connection, ws)

        # 設置超時回調
        self._heartbeat_manager.add_callback(self._handle_connection_timeout)

        self.logger.info(f"Connection established: {connection.connection_id}")
        return connection.connection_id

    async def disconnect(self, connection_id: str):
        """斷開連接"""
        connection = await self._connection_pool.get_connection(connection_id)
        if connection:
            connection.is_alive = False
            await self._heartbeat_manager.stop_heartbeat(connection_id)
            await self._connection_pool.release(connection)

            # 清理消息隊列
            await self._message_queue.clear_queue(connection_id)

            self.logger.info(f"Connection disconnected: {connection_id}")

    async def send_message(
        self,
        connection_id: str,
        message: Any,
        priority: bool = False
    ) -> bool:
        """發送消息"""
        connection = await self._connection_pool.get_connection(connection_id)
        if not connection or not connection.is_alive:
            # 添加到消息隊列
            await self._message_queue.add_message(connection_id, message)
            return False

        try:
            # 序列化消息
            if self.use_msgpack and hasattr(connection.ws, 'send'):
                import msgpack
                serialized_message = msgpack.packb(message)
                await connection.ws.send(serialized_message)
            else:
                if isinstance(message, (dict, list)):
                    message = json.dumps(message)
                await connection.ws.send(message)

            # 更新指標
            message_size = len(str(message))
            connection.message_count += 1
            connection.bytes_sent += message_size
            self._monitor.update_metrics(connection, message_size)

            return True

        except Exception as e:
            self.logger.error(f"Send message error: {e}")
            self._monitor.record_error(connection_id, str(e))

            # 嘗試重連
            await self._attempt_reconnect(connection_id)
            return False

    async def broadcast(self, message: Any, user_ids: Optional[List[str]] = None) -> int:
        """廣播消息"""
        connections = await self._connection_pool.get_all_connections()
        success_count = 0

        for connection in connections:
            if user_ids and connection.user_id not in user_ids:
                continue

            if await self.send_message(connection.connection_id, message):
                success_count += 1

        return success_count

    async def _attempt_reconnect(self, connection_id: str):
        """嘗試重連"""
        # 將消息移動到重連隊列
        messages = await self._message_queue.get_messages(connection_id, max_messages=100)
        if messages:
            await self._message_queue.clear_queue(connection_id)

        self._monitor.record_reconnect(connection_id)

    async def _handle_connection_timeout(self, connection_id: str, reason: str):
        """處理連接超時"""
        self.logger.warning(f"Connection timeout: {connection_id} - {reason}")

        # 斷開連接
        await self.disconnect(connection_id)

    async def cleanup_stale_connections(self, timeout: float = 300):
        """清理僵屍連接"""
        cleaned_count = await self._connection_pool.cleanup_stale_connections(timeout)
        if cleaned_count > 0:
            self.logger.info(f"Cleaned up {cleaned_count} stale connections")

    async def get_status(self) -> Dict[str, Any]:
        """獲取狀態"""
        connections = await self._connection_pool.get_all_connections()
        active_count = sum(1 for c in connections if c.is_alive)

        return {
            "total_connections": len(connections),
            "active_connections": active_count,
            "max_connections": self.max_connections,
            "pool_usage": len(connections) / self.max_connections,
            "metrics": self._monitor.get_metrics()
        }


# 全局WebSocket管理器實例
_global_ws_manager: Optional[OptimizedWebSocketManager] = None


def get_ws_manager(
    max_connections: int = 1000,
    use_msgpack: bool = True
) -> OptimizedWebSocketManager:
    """獲取全局WebSocket管理器"""
    global _global_ws_manager
    if _global_ws_manager is None:
        _global_ws_manager = OptimizedWebSocketManager(
            max_connections=max_connections,
            use_msgpack=use_msgpack
        )
    return _global_ws_manager


# 便捷函數
async def ws_connect(ws: Any, user_id: Optional[str] = None) -> str:
    """建立WebSocket連接"""
    manager = get_ws_manager()
    return await manager.connect(ws, user_id)


async def ws_disconnect(connection_id: str):
    """斷開WebSocket連接"""
    manager = get_ws_manager()
    await manager.disconnect(connection_id)


async def ws_send(connection_id: str, message: Any) -> bool:
    """發送WebSocket消息"""
    manager = get_ws_manager()
    return await manager.send_message(connection_id, message)


async def ws_broadcast(message: Any, user_ids: Optional[List[str]] = None) -> int:
    """廣播WebSocket消息"""
    manager = get_ws_manager()
    return await manager.broadcast(message, user_ids)


def get_ws_status() -> Dict[str, Any]:
    """獲取WebSocket狀態"""
    manager = get_ws_manager()
    return asyncio.run(manager.get_status())
