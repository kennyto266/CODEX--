"""
WebSocket服务器 - Phase 4: User Experience & Visualization
实时更新系统的主WebSocket服务器
提供：
- FastAPI WebSocket端点
- 连接管理
- 消息广播
- 错误处理
- 性能优化
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Set
from uuid import uuid4
from datetime import datetime, timedelta

from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Depends
from fastapi.responses import JSONResponse
import structlog

from src.infrastructure.websocket.websocket_optimized import get_ws_manager
from src.api.websocket.progress_tracker import BacktestProgressTracker
from src.api.websocket.chart_updates import ChartDataManager
from src.api.websocket.notifications import NotificationCenter

logger = structlog.get_logger("api.websocket")

# WebSocket路由器
websocket_router = APIRouter()

# 全局组件实例
_progress_tracker: Optional[BacktestProgressTracker] = None
_chart_manager: Optional[ChartDataManager] = None
_notification_center: Optional[NotificationCenter] = None

# 连接池管理
class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        self.subscriptions: Dict[str, Set[str]] = {
            "backtest_progress": set(),
            "chart_updates": set(),
            "notifications": set(),
            "system_status": set(),
            "market_data": set()
        }
        self.heartbeat_interval = 30  # 秒
        self.connection_timeout = 90  # 秒
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        client_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> str:
        """接受新连接"""
        await websocket.accept()
        connection_id = client_id or str(uuid4())

        async with self._lock:
            self.active_connections[connection_id] = websocket
            self.connection_metadata[connection_id] = {
                "connected_at": datetime.now(),
                "last_ping": time.time(),
                "user_id": user_id,
                "message_count": 0,
                "bytes_sent": 0,
                "subscriptions": set()
            }

        logger.info(
            "WebSocket连接已建立",
            connection_id=connection_id,
            user_id=user_id,
            total_connections=len(self.active_connections)
        )

        # 发送欢迎消息
        await self.send_personal_message(
            connection_id,
            {
                "type": "connection_established",
                "connection_id": connection_id,
                "timestamp": datetime.now().isoformat(),
                "server_time": time.time()
            }
        )

        return connection_id

    async def disconnect(self, connection_id: str):
        """断开连接"""
        async with self._lock:
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]

            if connection_id in self.connection_metadata:
                metadata = self.connection_metadata[connection_id]
                # 从所有订阅中移除
                for channel in metadata.get("subscriptions", set()):
                    self.subscriptions.get(channel, set()).discard(connection_id)
                del self.connection_metadata[connection_id]

        logger.info(
            "WebSocket连接已断开",
            connection_id=connection_id,
            total_connections=len(self.active_connections)
        )

    async def send_personal_message(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """发送个人消息"""
        websocket = self.active_connections.get(connection_id)
        if not websocket:
            return False

        try:
            message_str = json.dumps(message, ensure_ascii=False)
            await websocket.send_text(message_str)

            # 更新元数据
            if connection_id in self.connection_metadata:
                self.connection_metadata[connection_id]["message_count"] += 1
                self.connection_metadata[connection_id]["bytes_sent"] += len(message_str)

            return True

        except WebSocketDisconnect:
            await self.disconnect(connection_id)
            return False
        except Exception as e:
            logger.error("发送个人消息失败", connection_id=connection_id, error=str(e))
            await self.disconnect(connection_id)
            return False

    async def broadcast(
        self,
        channel: str,
        message: Dict[str, Any],
        exclude_connection: Optional[str] = None
    ) -> int:
        """广播消息到指定频道"""
        subscribers = self.subscriptions.get(channel, set())
        if not subscribers:
            return 0

        # 添加时间戳和频道信息
        message["channel"] = channel
        message["timestamp"] = datetime.now().isoformat()
        message["server_time"] = time.time()

        success_count = 0
        disconnected = []

        for connection_id in subscribers:
            if exclude_connection and connection_id == exclude_connection:
                continue

            if await self.send_personal_message(connection_id, message):
                success_count += 1
            else:
                disconnected.append(connection_id)

        # 清理断开的连接
        for connection_id in disconnected:
            await self.disconnect(connection_id)

        return success_count

    async def subscribe(self, connection_id: str, channel: str) -> bool:
        """订阅频道"""
        async with self._lock:
            if connection_id not in self.active_connections:
                return False

            if channel not in self.subscriptions:
                self.subscriptions[channel] = set()

            self.subscriptions[channel].add(connection_id)

            if connection_id in self.connection_metadata:
                self.connection_metadata[connection_id]["subscriptions"].add(channel)

        logger.info(
            "客户端订阅频道",
            connection_id=connection_id,
            channel=channel,
            total_subscribers=len(self.subscriptions.get(channel, set()))
        )

        return True

    async def unsubscribe(self, connection_id: str, channel: str) -> bool:
        """取消订阅频道"""
        async with self._lock:
            if channel in self.subscriptions:
                self.subscriptions[channel].discard(connection_id)

            if connection_id in self.connection_metadata:
                self.connection_metadata[connection_id]["subscriptions"].discard(channel)

        logger.info(
            "客户端取消订阅",
            connection_id=connection_id,
            channel=channel
        )

        return True

    async def handle_ping(self, connection_id: str) -> bool:
        """处理ping消息"""
        if connection_id in self.connection_metadata:
            self.connection_metadata[connection_id]["last_ping"] = time.time()

        return await self.send_personal_message(
            connection_id,
            {
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            }
        )

    async def cleanup_stale_connections(self):
        """清理过期连接"""
        current_time = time.time()
        stale_connections = []

        async with self._lock:
            for connection_id, metadata in self.connection_metadata.items():
                if current_time - metadata.get("last_ping", 0) > self.connection_timeout:
                    stale_connections.append(connection_id)

        for connection_id in stale_connections:
            await self.disconnect(connection_id)

        if stale_connections:
            logger.info(
                "清理过期连接",
                count=len(stale_connections),
                remaining_connections=len(self.active_connections)
            )

    def get_status(self) -> Dict[str, Any]:
        """获取连接状态"""
        return {
            "total_connections": len(self.active_connections),
            "subscriptions": {
                channel: len(subscribers)
                for channel, subscribers in self.subscriptions.items()
            },
            "active_connections": list(self.active_connections.keys())
        }


# 全局连接管理器
connection_manager = ConnectionManager()


async def get_progress_tracker() -> BacktestProgressTracker:
    """获取回测进度跟踪器（依赖注入）"""
    global _progress_tracker
    if _progress_tracker is None:
        _progress_tracker = BacktestProgressTracker()
    return _progress_tracker


async def get_chart_manager() -> ChartDataManager:
    """获取图表数据管理器（依赖注入）"""
    global _chart_manager
    if _chart_manager is None:
        _chart_manager = ChartDataManager()
    return _chart_manager


async def get_notification_center() -> NotificationCenter:
    """获取通知中心（依赖注入）"""
    global _notification_center
    if _notification_center is None:
        _notification_center = NotificationCenter()
    return _notification_center


@websocket_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket主端点"""
    connection_id = None

    try:
        # 获取查询参数
        client_id = websocket.query_params.get("client_id")
        user_id = websocket.query_params.get("user_id")

        # 建立连接
        connection_id = await connection_manager.connect(websocket, client_id, user_id)

        # 启动消息处理循环
        while True:
            try:
                # 接收消息
                data = await websocket.receive_text()

                # 解析消息
                try:
                    message = json.loads(data)
                except json.JSONDecodeError:
                    await connection_manager.send_personal_message(
                        connection_id,
                        {
                            "type": "error",
                            "error": "Invalid JSON",
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                    continue

                # 处理消息
                await handle_client_message(connection_id, message)

            except WebSocketDisconnect:
                logger.info("客户端主动断开连接", connection_id=connection_id)
                break
            except Exception as e:
                logger.error("处理消息错误", connection_id=connection_id, error=str(e))
                await asyncio.sleep(0.1)  # 短暂暂停避免忙等待

    except Exception as e:
        logger.error("WebSocket连接错误", connection_id=connection_id, error=str(e))

    finally:
        if connection_id:
            await connection_manager.disconnect(connection_id)


async def handle_client_message(connection_id: str, message: Dict[str, Any]):
    """处理客户端消息"""
    message_type = message.get("type")

    if message_type == "ping":
        await connection_manager.handle_ping(connection_id)

    elif message_type == "subscribe":
        channel = message.get("channel")
        if channel:
            await connection_manager.subscribe(connection_id, channel)

            # 发送订阅确认
            await connection_manager.send_personal_message(
                connection_id,
                {
                    "type": "subscription_confirmed",
                    "channel": channel,
                    "timestamp": datetime.now().isoformat()
                }
            )

    elif message_type == "unsubscribe":
        channel = message.get("channel")
        if channel:
            await connection_manager.unsubscribe(connection_id, channel)

    elif message_type == "request_backtest_progress":
        task_id = message.get("task_id")
        if task_id and _progress_tracker:
            progress = _progress_tracker.get_progress(task_id)
            if progress:
                await connection_manager.send_personal_message(
                    connection_id,
                    {
                        "type": "backtest_progress_update",
                        "task_id": task_id,
                        "progress": progress,
                        "timestamp": datetime.now().isoformat()
                    }
                )

    elif message_type == "subscribe_chart":
        symbol = message.get("symbol")
        if symbol and _chart_manager:
            await connection_manager.subscribe(connection_id, f"chart_{symbol}")
            _chart_manager.add_subscriber(symbol, connection_id)

    elif message_type == "unsubscribe_chart":
        symbol = message.get("symbol")
        if symbol and _chart_manager:
            await connection_manager.unsubscribe(connection_id, f"chart_{symbol}")
            _chart_manager.remove_subscriber(symbol, connection_id)

    elif message_type == "get_notifications":
        if _notification_center:
            notifications = _notification_center.get_recent_notifications(
                connection_id,
                limit=message.get("limit", 50)
            )
            await connection_manager.send_personal_message(
                connection_id,
                {
                    "type": "notifications_list",
                    "notifications": notifications,
                    "timestamp": datetime.now().isoformat()
                }
            )

    else:
        logger.warning("未知消息类型", message_type=message_type)


@websocket_router.get("/websocket/status")
async def websocket_status():
    """WebSocket连接状态"""
    return {
        "status": "online",
        "connections": connection_manager.get_status(),
        "timestamp": datetime.now().isoformat()
    }


@websocket_router.post("/websocket/broadcast")
async def broadcast_message(
    channel: str,
    message: Dict[str, Any],
    exclude: Optional[str] = None
):
    """广播消息（管理员接口）"""
    try:
        count = await connection_manager.broadcast(channel, message, exclude)
        return {
            "success": True,
            "channel": channel,
            "recipient_count": count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error("广播消息失败", error=str(e))
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


# 后台任务
async def start_background_tasks():
    """启动后台任务"""
    tasks = []

    # 定期清理过期连接
    async def cleanup_task():
        while True:
            try:
                await connection_manager.cleanup_stale_connections()
                await asyncio.sleep(60)  # 每分钟清理一次
            except Exception as e:
                logger.error("清理任务异常", error=str(e))
                await asyncio.sleep(60)

    tasks.append(asyncio.create_task(cleanup_task()))

    # 启动进度跟踪器后台任务
    if _progress_tracker:
        tasks.append(asyncio.create_task(_progress_tracker.start_background_task()))

    # 启动图表数据管理器后台任务
    if _chart_manager:
        tasks.append(asyncio.create_task(_chart_manager.start_background_task()))

    # 启动通知中心后台任务
    if _notification_center:
        tasks.append(asyncio.create_task(_notification_center.start_background_task()))

    logger.info("WebSocket后台任务已启动", task_count=len(tasks))
    return tasks


# 广播辅助函数
async def broadcast_backtest_progress(task_id: str, progress_data: Dict[str, Any]):
    """广播回测进度更新"""
    await connection_manager.broadcast(
        "backtest_progress",
        {
            "type": "backtest_progress_update",
            "task_id": task_id,
            "progress": progress_data,
            "timestamp": datetime.now().isoformat()
        }
    )


async def broadcast_chart_update(symbol: str, chart_data: Dict[str, Any]):
    """广播图表数据更新"""
    await connection_manager.broadcast(
        f"chart_{symbol}",
        {
            "type": "chart_update",
            "symbol": symbol,
            "data": chart_data,
            "timestamp": datetime.now().isoformat()
        }
    )


async def broadcast_notification(notification: Dict[str, Any], target_channel: str = "notifications"):
    """广播通知消息"""
    await connection_manager.broadcast(
        target_channel,
        {
            "type": "notification",
            "notification": notification,
            "timestamp": datetime.now().isoformat()
        }
    )


async def broadcast_system_status(status_data: Dict[str, Any]):
    """广播系统状态"""
    await connection_manager.broadcast(
        "system_status",
        {
            "type": "system_status_update",
            "status": status_data,
            "timestamp": datetime.now().isoformat()
        }
    )


# 导出
__all__ = [
    "websocket_router",
    "connection_manager",
    "get_progress_tracker",
    "get_chart_manager",
    "get_notification_center",
    "broadcast_backtest_progress",
    "broadcast_chart_update",
    "broadcast_notification",
    "broadcast_system_status",
    "start_background_tasks"
]
