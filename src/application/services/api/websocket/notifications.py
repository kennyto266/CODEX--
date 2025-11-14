"""
通知中心 - Phase 4: User Experience & Visualization
T086 - 添加操作完成通知系统

功能：
- 操作完成通知
- 消息推送
- 通知中心
- 历史记录
- 用户偏好
"""

import asyncio
import time
import json
from typing import Dict, Any, Optional, List, Set, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field, asdict
from collections import deque, defaultdict
import structlog

from . import connection_manager

logger = structlog.get_logger("api.websocket.notifications")


class NotificationType(Enum):
    """通知类型"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    BACKTEST_COMPLETED = "backtest_completed"
    OPTIMIZATION_COMPLETED = "optimization_completed"
    DATA_UPDATE = "data_update"
    SYSTEM_STATUS = "system_status"
    USER_ACTION = "user_action"


class NotificationPriority(Enum):
    """通知优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Notification:
    """通知对象"""
    notification_id: str
    type: NotificationType
    title: str
    message: str
    priority: NotificationPriority
    timestamp: float
    user_id: Optional[str] = None
    target_channel: Optional[str] = "notifications"
    metadata: Dict[str, Any] = field(default_factory=dict)
    auto_dismiss: bool = False
    dismiss_after: Optional[int] = None  # 秒
    action_url: Optional[str] = None
    action_text: Optional[str] = None
    read: bool = False
    read_at: Optional[float] = None


@dataclass
class NotificationPreferences:
    """用户通知偏好"""
    user_id: str
    email_enabled: bool = False
    sms_enabled: bool = False
    push_enabled: bool = True
    desktop_enabled: bool = True
    mute_all: bool = False
    quiet_hours_start: Optional[int] = None  # 0-23
    quiet_hours_end: Optional[int] = None   # 0-23
    type_preferences: Dict[NotificationType, bool] = field(
        default_factory=lambda: {
            NotificationType.INFO: True,
            NotificationType.SUCCESS: True,
            NotificationType.WARNING: True,
            NotificationType.ERROR: True,
            NotificationType.BACKTEST_COMPLETED: True,
            NotificationType.OPTIMIZATION_COMPLETED: True,
            NotificationType.DATA_UPDATE: False,
            NotificationType.SYSTEM_STATUS: False,
            NotificationType.USER_ACTION: True
        }
    )


class NotificationCenter:
    """通知中心"""

    def __init__(
        self,
        max_notifications: int = 10000,
        max_history: int = 5000,
        cleanup_interval: int = 3600  # 1小时清理一次
    ):
        self.logger = logger
        self.max_notifications = max_notifications
        self.max_history = max_history
        self.cleanup_interval = cleanup_interval

        # 存储
        self.notifications: Dict[str, Notification] = {}
        self.user_notifications: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=max_notifications)
        )
        self.channel_notifications: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=max_notifications)
        )
        self.user_preferences: Dict[str, NotificationPreferences] = {}
        self.subscribers: Dict[str, Set[str]] = {}  # channel -> {connection_ids}
        self.read_receipts: Dict[str, float] = {}  # notification_id -> read_timestamp

        # 统计
        self.stats = {
            "total_sent": 0,
            "total_read": 0,
            "total_dismissed": 0,
            "by_type": defaultdict(int),
            "by_priority": defaultdict(int)
        }

        self._lock = asyncio.Lock()
        self._background_tasks: List[asyncio.Task] = []

    async def create_notification(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        user_id: Optional[str] = None,
        target_channel: str = "notifications",
        metadata: Optional[Dict[str, Any]] = None,
        auto_dismiss: bool = False,
        dismiss_after: Optional[int] = None,
        action_url: Optional[str] = None,
        action_text: Optional[str] = None
    ) -> str:
        """创建通知"""
        notification_id = f"notif_{int(time.time() * 1000)}_{len(self.notifications)}"

        notification = Notification(
            notification_id=notification_id,
            type=notification_type,
            title=title,
            message=message,
            priority=priority,
            timestamp=time.time(),
            user_id=user_id,
            target_channel=target_channel,
            metadata=metadata or {},
            auto_dismiss=auto_dismiss,
            dismiss_after=dismiss_after,
            action_url=action_url,
            action_text=action_text
        )

        async with self._lock:
            # 存储通知
            self.notifications[notification_id] = notification

            # 添加到用户队列
            if user_id:
                self.user_notifications[user_id].append(notification)

            # 添加到频道队列
            self.channel_notifications[target_channel].append(notification)

            # 更新统计
            self.stats["total_sent"] += 1
            self.stats["by_type"][notification_type.value] += 1
            self.stats["by_priority"][priority.name] += 1

        self.logger.info(
            "创建通知",
            notification_id=notification_id,
            type=notification_type.value,
            priority=priority.name,
            user_id=user_id,
            channel=target_channel
        )

        return notification_id

    async def send_notification(
        self,
        notification_id: str,
        connection_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> bool:
        """发送通知"""
        notification = self.notifications.get(notification_id)
        if not notification:
            return False

        # 检查用户偏好
        if user_id:
            preferences = self.user_preferences.get(user_id)
            if preferences and not self._should_send_notification(preferences, notification):
                self.logger.debug(
                    "通知被用户偏好阻止",
                    notification_id=notification_id,
                    user_id=user_id
                )
                return False

        # 准备发送数据
        send_data = {
            "type": "notification",
            "notification": {
                "id": notification.notification_id,
                "type": notification.type.value,
                "title": notification.title,
                "message": notification.message,
                "priority": notification.priority.name,
                "timestamp": datetime.fromtimestamp(notification.timestamp).isoformat(),
                "metadata": notification.metadata,
                "action_url": notification.action_url,
                "action_text": notification.action_text
            },
            "timestamp": datetime.now().isoformat()
        }

        # 发送
        if connection_id:
            # 发送到指定连接
            success = await connection_manager.send_personal_message(
                connection_id,
                send_data
            )
        else:
            # 广播到频道
            success_count = await connection_manager.broadcast(
                notification.target_channel,
                send_data
            )
            success = success_count > 0

        return success

    async def send_to_channel(
        self,
        channel: str,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """发送通知到频道"""
        notification_id = await self.create_notification(
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            target_channel=channel,
            metadata=metadata,
            **kwargs
        )

        await self.send_notification(notification_id)
        return notification_id

    async def send_to_user(
        self,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """发送通知到用户"""
        notification_id = await self.create_notification(
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            user_id=user_id,
            target_channel=f"user_{user_id}",
            metadata=metadata,
            **kwargs
        )

        await self.send_notification(notification_id)
        return notification_id

    async def subscribe(self, channel: str, connection_id: str):
        """订阅通知频道"""
        async with self._lock:
            if channel not in self.subscribers:
                self.subscribers[channel] = set()
            self.subscribers[channel].add(connection_id)

        self.logger.info(
            "客户端订阅通知频道",
            channel=channel,
            connection_id=connection_id
        )

    async def unsubscribe(self, channel: str, connection_id: str):
        """取消订阅通知频道"""
        async with self._lock:
            if channel in self.subscribers:
                self.subscribers[channel].discard(connection_id)

        self.logger.info(
            "客户端取消订阅通知频道",
            channel=channel,
            connection_id=connection_id
        )

    async def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """标记通知为已读"""
        async with self._lock:
            if notification_id not in self.notifications:
                return False

            notification = self.notifications[notification_id]
            if not notification.read:
                notification.read = True
                notification.read_at = time.time()
                self.stats["total_read"] += 1

            # 记录阅读回执
            self.read_receipts[notification_id] = time.time()

        return True

    async def mark_all_as_read(self, user_id: str) -> int:
        """标记用户所有通知为已读"""
        count = 0
        async with self._lock:
            user_queue = self.user_notifications.get(user_id, deque())
            for notification in user_queue:
                if not notification.read:
                    notification.read = True
                    notification.read_at = time.time()
                    count += 1
                    self.stats["total_read"] += 1

        self.logger.info(
            "标记所有通知为已读",
            user_id=user_id,
            count=count
        )

        return count

    async def dismiss_notification(self, notification_id: str) -> bool:
        """解散通知"""
        async with self._lock:
            if notification_id in self.notifications:
                del self.notifications[notification_id]
                self.stats["total_dismissed"] += 1
                return True

        return False

    async def get_notification(self, notification_id: str) -> Optional[Notification]:
        """获取通知"""
        return self.notifications.get(notification_id)

    async def get_user_notifications(
        self,
        user_id: str,
        limit: int = 50,
        unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """获取用户通知"""
        async with self._lock:
            notifications = list(self.user_notifications.get(user_id, deque()))

        # 过滤未读
        if unread_only:
            notifications = [n for n in notifications if not n.read]

        # 排序（最新的在前）
        notifications.sort(key=lambda x: x.timestamp, reverse=True)

        # 限制数量
        notifications = notifications[:limit]

        # 转换为字典
        return [
            {
                "id": n.notification_id,
                "type": n.type.value,
                "title": n.title,
                "message": n.message,
                "priority": n.priority.name,
                "timestamp": datetime.fromtimestamp(n.timestamp).isoformat(),
                "read": n.read,
                "read_at": datetime.fromtimestamp(n.read_at).isoformat() if n.read_at else None,
                "metadata": n.metadata,
                "action_url": n.action_url,
                "action_text": n.action_text
            }
            for n in notifications
        ]

    async def get_channel_notifications(
        self,
        channel: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取频道通知"""
        async with self._lock:
            notifications = list(self.channel_notifications.get(channel, deque()))

        # 排序
        notifications.sort(key=lambda x: x.timestamp, reverse=True)
        notifications = notifications[:limit]

        # 转换为字典
        return [
            {
                "id": n.notification_id,
                "type": n.type.value,
                "title": n.title,
                "message": n.message,
                "priority": n.priority.name,
                "timestamp": datetime.fromtimestamp(n.timestamp).isoformat(),
                "metadata": n.metadata
            }
            for n in notifications
        ]

    async def get_recent_notifications(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取最近通知（向后兼容）"""
        return await self.get_user_notifications(user_id, limit)

    async def get_unread_count(self, user_id: str) -> int:
        """获取未读通知数量"""
        async with self._lock:
            user_queue = self.user_notifications.get(user_id, deque())
            return sum(1 for n in user_queue if not n.read)

    def _should_send_notification(
        self,
        preferences: NotificationPreferences,
        notification: Notification
    ) -> bool:
        """检查是否应该发送通知（根据用户偏好）"""
        if preferences.mute_all:
            return False

        # 检查类型偏好
        if not preferences.type_preferences.get(notification.type, True):
            return False

        # 检查静音时间
        if preferences.quiet_hours_start is not None and preferences.quiet_hours_end is not None:
            current_hour = datetime.now().hour
            if preferences.quiet_hours_start <= preferences.quiet_hours_end:
                # 例如 22:00 - 07:00
                if preferences.quiet_hours_start <= current_hour or current_hour < preferences.quiet_hours_end:
                    if notification.priority in [NotificationPriority.LOW, NotificationPriority.NORMAL]:
                        return False
            else:
                # 例如 23:00 - 06:00
                if current_hour >= preferences.quiet_hours_start or current_hour < preferences.quiet_hours_end:
                    if notification.priority in [NotificationPriority.LOW, NotificationPriority.NORMAL]:
                        return False

        return True

    async def set_user_preferences(
        self,
        user_id: str,
        preferences: NotificationPreferences
    ):
        """设置用户偏好"""
        async with self._lock:
            self.user_preferences[user_id] = preferences

        self.logger.info(
            "设置用户通知偏好",
            user_id=user_id,
            push_enabled=preferences.push_enabled,
            desktop_enabled=preferences.desktop_enabled
        )

    async def get_user_preferences(self, user_id: str) -> Optional[NotificationPreferences]:
        """获取用户偏好"""
        return self.user_preferences.get(user_id)

    async def cleanup_old_notifications(self):
        """清理旧通知"""
        current_time = time.time()
        cutoff_time = current_time - (24 * 3600)  # 24小时前

        async with self._lock:
            old_ids = [
                notification_id
                for notification_id, notification in self.notifications.items()
                if notification.timestamp < cutoff_time
            ]

            for notification_id in old_ids:
                del self.notifications[notification_id]
                # 从用户队列中移除
                for user_queue in self.user_notifications.values():
                    # 查找并移除
                    for n in list(user_queue):
                        if n.notification_id == notification_id:
                            user_queue.remove(n)
                            break

            if old_ids:
                self.logger.info(
                    "清理旧通知",
                    removed_count=len(old_ids),
                    remaining_count=len(self.notifications)
                )

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_notifications": len(self.notifications),
            "total_sent": self.stats["total_sent"],
            "total_read": self.stats["total_read"],
            "total_dismissed": self.stats["total_dismissed"],
            "by_type": dict(self.stats["by_type"]),
            "by_priority": dict(self.stats["by_priority"]),
            "active_channels": len(self.subscribers),
            "users_with_preferences": len(self.user_preferences)
        }

    async def start_background_task(self):
        """启动后台任务"""
        self.logger.info("启动通知中心后台任务")

        async def cleanup_task():
            """定期清理任务"""
            while True:
                try:
                    await self.cleanup_old_notifications()
                    await asyncio.sleep(self.cleanup_interval)
                except Exception as e:
                    self.logger.error("清理任务异常", error=str(e))
                    await asyncio.sleep(self.cleanup_interval)

        cleanup_task_handle = asyncio.create_task(cleanup_task())
        self._background_tasks.append(cleanup_task_handle)

        return self._background_tasks

    async def stop_background_tasks(self):
        """停止后台任务"""
        for task in self._background_tasks:
            if not task.done():
                task.cancel()

        self._background_tasks.clear()
        self.logger.info("通知中心后台任务已停止")


# 便捷函数
async def notify_backtest_completed(
    center: NotificationCenter,
    user_id: str,
    task_id: str,
    result_summary: Dict[str, Any]
):
    """通知回测完成（便捷函数）"""
    await center.send_to_user(
        user_id=user_id,
        notification_type=NotificationType.BACKTEST_COMPLETED,
        title="回测完成",
        message=f"回测任务 {task_id} 已完成",
        priority=NotificationPriority.HIGH,
        metadata={
            "task_id": task_id,
            "result_summary": result_summary
        }
    )


async def notify_optimization_completed(
    center: NotificationCenter,
    user_id: str,
    task_id: str,
    best_result: Dict[str, Any]
):
    """通知优化完成（便捷函数）"""
    await center.send_to_user(
        user_id=user_id,
        notification_type=NotificationType.OPTIMIZATION_COMPLETED,
        title="参数优化完成",
        message=f"优化任务 {task_id} 已完成，找到最佳参数",
        priority=NotificationPriority.HIGH,
        metadata={
            "task_id": task_id,
            "best_result": best_result
        }
    )


async def notify_system_status(
    center: NotificationCenter,
    status: str,
    message: str,
    priority: NotificationPriority = NotificationPriority.NORMAL
):
    """通知系统状态（便捷函数）"""
    await center.send_to_channel(
        channel="system_status",
        notification_type=NotificationType.SYSTEM_STATUS,
        title=f"系统状态: {status}",
        message=message,
        priority=priority
    )


# 示例：通知使用流程
"""
# 1. 创建通知
await notification_center.create_notification(
    type=NotificationType.BACKTEST_COMPLETED,
    title="回测完成",
    message="KDJ策略回测已完成，总收益15.67%",
    user_id="user123"
)

# 2. 发送到用户
await notification_center.send_to_user(
    user_id="user123",
    type=NotificationType.SUCCESS,
    title="成功",
    message="操作成功完成"
)

# 3. 广播到频道
await notification_center.send_to_channel(
    channel="notifications",
    type=NotificationType.INFO,
    title="信息",
    message="系统将在5分钟后进行维护"
)
"""


# 导出
__all__ = [
    "NotificationCenter",
    "Notification",
    "NotificationType",
    "NotificationPriority",
    "NotificationPreferences",
    "notify_backtest_completed",
    "notify_optimization_completed",
    "notify_system_status"
]
