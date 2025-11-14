"""
回测进度跟踪器 - Phase 4: User Experience & Visualization
T084 - 实现回测进度实时更新

功能：
- 回测进度跟踪
- 进度推送
- 状态管理
- 客户端订阅
- 自动重连支持
"""

import asyncio
import time
import json
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from enum import Enum
import structlog
from dataclasses import dataclass, field, asdict

from . import connection_manager

logger = structlog.get_logger("api.websocket.progress")


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class ProgressUpdate:
    """进度更新数据"""
    task_id: str
    status: TaskStatus
    progress: float  # 0.0 - 100.0
    current_step: str
    total_steps: int
    current_step_index: int
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    estimated_time_remaining: Optional[float] = None
    start_time: float = field(default_factory=time.time)
    update_time: float = field(default_factory=time.time)
    error: Optional[str] = None


class BacktestProgressTracker:
    """回测进度跟踪器"""

    def __init__(self):
        self.logger = logger
        self.active_tasks: Dict[str, ProgressUpdate] = {}
        self.task_history: Dict[str, ProgressUpdate] = {}
        self.subscribers: Dict[str, List[str]] = {}  # task_id -> [connection_ids]
        self._lock = asyncio.Lock()
        self._update_callbacks: List[Callable] = []
        self._max_history = 1000  # 最大历史记录数
        self._history_cleanup_interval = 3600  # 1小时清理一次

    async def create_task(
        self,
        task_id: str,
        total_steps: int,
        initial_message: str = "任务初始化中...",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProgressUpdate:
        """创建新任务"""
        progress = ProgressUpdate(
            task_id=task_id,
            status=TaskStatus.PENDING,
            progress=0.0,
            current_step="初始化",
            total_steps=total_steps,
            current_step_index=0,
            message=initial_message,
            data=metadata or {}
        )

        async with self._lock:
            self.active_tasks[task_id] = progress
            self.subscribers[task_id] = []

        self.logger.info(
            "创建回测任务",
            task_id=task_id,
            total_steps=total_steps
        )

        return progress

    async def update_progress(
        self,
        task_id: str,
        progress: float,
        current_step: Optional[str] = None,
        message: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        estimated_time_remaining: Optional[float] = None
    ) -> bool:
        """更新任务进度"""
        async with self._lock:
            if task_id not in self.active_tasks:
                self.logger.warning("尝试更新不存在的任务", task_id=task_id)
                return False

            task = self.active_tasks[task_id]
            task.progress = max(0.0, min(100.0, progress))
            task.update_time = time.time()

            if current_step is not None:
                task.current_step = current_step

            if message is not None:
                task.message = message

            if data is not None:
                task.data.update(data)

            if estimated_time_remaining is not None:
                task.estimated_time_remaining = estimated_time_remaining

            # 更新当前步骤索引（基于进度估算）
            if task.total_steps > 0:
                task.current_step_index = int((task.progress / 100.0) * task.total_steps)

        # 广播进度更新
        await self.broadcast_progress_update(task_id, task)

        return True

    async def set_status(
        self,
        task_id: str,
        status: TaskStatus,
        message: Optional[str] = None,
        error: Optional[str] = None
    ) -> bool:
        """设置任务状态"""
        async with self._lock:
            if task_id not in self.active_tasks:
                return False

            task = self.active_tasks[task_id]
            old_status = task.status
            task.status = status
            task.update_time = time.time()

            if message is not None:
                task.message = message

            if error is not None:
                task.error = error

        self.logger.info(
            "任务状态变更",
            task_id=task_id,
            old_status=old_status.value,
            new_status=status.value
        )

        # 广播状态更新
        await self.broadcast_progress_update(task_id, task)

        # 如果任务完成或失败，移动到历史记录
        if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            await self._move_to_history(task_id)

        return True

    async def start_task(self, task_id: str) -> bool:
        """启动任务"""
        return await self.set_status(task_id, TaskStatus.RUNNING, "任务执行中...")

    async def complete_task(
        self,
        task_id: str,
        final_message: str = "任务完成",
        result_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """完成任务"""
        if result_data:
            async with self._lock:
                if task_id in self.active_tasks:
                    self.active_tasks[task_id].data.update(result_data)

        await self.update_progress(task_id, 100.0, message=final_message)
        return await self.set_status(task_id, TaskStatus.COMPLETED, final_message)

    async def fail_task(self, task_id: str, error_message: str) -> bool:
        """标记任务失败"""
        return await self.set_status(
            task_id,
            TaskStatus.FAILED,
            f"任务失败: {error_message}",
            error_message
        )

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        return await self.set_status(task_id, TaskStatus.CANCELLED, "任务已取消")

    async def pause_task(self, task_id: str) -> bool:
        """暂停任务"""
        return await self.set_status(task_id, TaskStatus.PAUSED, "任务已暂停")

    async def resume_task(self, task_id: str) -> bool:
        """恢复任务"""
        return await self.set_status(task_id, TaskStatus.RUNNING, "任务已恢复")

    async def broadcast_progress_update(self, task_id: str, task: ProgressUpdate):
        """广播进度更新到订阅的客户端"""
        try:
            # 准备广播数据
            broadcast_data = {
                "task_id": task_id,
                "status": task.status.value,
                "progress": task.progress,
                "current_step": task.current_step,
                "current_step_index": task.current_step_index,
                "total_steps": task.total_steps,
                "message": task.message,
                "estimated_time_remaining": task.estimated_time_remaining,
                "elapsed_time": time.time() - task.start_time,
                "data": task.data,
                "error": task.error
            }

            # 广播到订阅的客户端
            subscribers = self.subscribers.get(task_id, [])
            for connection_id in subscribers:
                await connection_manager.send_personal_message(
                    connection_id,
                    {
                        "type": "backtest_progress_update",
                        "task_id": task_id,
                        "data": broadcast_data,
                        "timestamp": datetime.now().isoformat()
                    }
                )

            # 调用回调函数
            for callback in self._update_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(task_id, task)
                    else:
                        callback(task_id, task)
                except Exception as e:
                    self.logger.error("进度更新回调错误", task_id=task_id, error=str(e))

        except Exception as e:
            self.logger.error("广播进度更新失败", task_id=task_id, error=str(e))

    async def subscribe(self, task_id: str, connection_id: str):
        """订阅任务进度更新"""
        async with self._lock:
            if task_id not in self.subscribers:
                self.subscribers[task_id] = []
            if connection_id not in self.subscribers[task_id]:
                self.subscribers[task_id].append(connection_id)

        self.logger.info(
            "客户端订阅任务进度",
            task_id=task_id,
            connection_id=connection_id
        )

        # 立即发送当前进度
        if task_id in self.active_tasks:
            await self.broadcast_progress_update(task_id, self.active_tasks[task_id])

    async def unsubscribe(self, task_id: str, connection_id: str):
        """取消订阅任务进度更新"""
        async with self._lock:
            if task_id in self.subscribers:
                if connection_id in self.subscribers[task_id]:
                    self.subscribers[task_id].remove(connection_id)

        self.logger.info(
            "客户端取消订阅任务进度",
            task_id=task_id,
            connection_id=connection_id
        )

    async def get_progress(self, task_id: str) -> Optional[ProgressUpdate]:
        """获取任务进度"""
        async with self._lock:
            return self.active_tasks.get(task_id)

    async def get_all_active_tasks(self) -> Dict[str, ProgressUpdate]:
        """获取所有活跃任务"""
        async with self._lock:
            return self.active_tasks.copy()

    async def get_task_history(self, limit: int = 50) -> List[ProgressUpdate]:
        """获取任务历史"""
        async with self._lock:
            history_list = list(self.task_history.values())
            # 按更新时间倒序
            history_list.sort(key=lambda x: x.update_time, reverse=True)
            return history_list[:limit]

    async def _move_to_history(self, task_id: str):
        """将完成的任务移动到历史记录"""
        async with self._lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                self.task_history[task_id] = task
                del self.active_tasks[task_id]

                # 清理旧的订阅者
                if task_id in self.subscribers:
                    del self.subscribers[task_id]

                # 限制历史记录数量
                if len(self.task_history) > self._max_history:
                    # 删除最旧的记录
                    oldest_id = min(
                        self.task_history.keys(),
                        key=lambda tid: self.task_history[tid].update_time
                    )
                    del self.task_history[oldest_id]

    async def _cleanup_old_history(self):
        """清理旧历史记录"""
        current_time = time.time()
        cutoff_time = current_time - self._history_cleanup_interval

        async with self._lock:
            old_task_ids = [
                task_id
                for task_id, task in self.task_history.items()
                if task.update_time < cutoff_time
            ]

            for task_id in old_task_ids:
                del self.task_history[task_id]

            if old_task_ids:
                self.logger.info(
                    "清理旧历史记录",
                    removed_count=len(old_task_ids),
                    remaining_count=len(self.task_history)
                )

    def add_update_callback(self, callback: Callable):
        """添加进度更新回调函数"""
        self._update_callbacks.append(callback)

    def remove_update_callback(self, callback: Callable):
        """移除进度更新回调函数"""
        if callback in self._update_callbacks:
            self._update_callbacks.remove(callback)

    async def start_background_task(self):
        """启动后台任务"""
        self.logger.info("启动进度跟踪器后台任务")

        async def cleanup_task():
            while True:
                try:
                    await self._cleanup_old_history()
                    await asyncio.sleep(1800)  # 每30分钟清理一次
                except Exception as e:
                    self.logger.error("清理任务异常", error=str(e))
                    await asyncio.sleep(1800)

        return asyncio.create_task(cleanup_task())


# 便捷函数
async def create_backtest_task(
    tracker: BacktestProgressTracker,
    task_id: str,
    total_steps: int,
    metadata: Optional[Dict[str, Any]] = None
) -> ProgressUpdate:
    """创建回测任务（便捷函数）"""
    return await tracker.create_task(
        task_id=task_id,
        total_steps=total_steps,
        initial_message="回测任务已创建",
        metadata=metadata
    )


async def update_backtest_step(
    tracker: BacktestProgressTracker,
    task_id: str,
    step_index: int,
    step_name: str,
    message: Optional[str] = None
) -> bool:
    """更新回测步骤（便捷函数）"""
    progress = (step_index + 1) / 100.0 * 100.0 if step_index < 100 else 100.0
    return await tracker.update_progress(
        task_id=task_id,
        progress=progress,
        current_step=step_name,
        message=message or f"正在执行: {step_name}"
    )


# 示例：回测进度更新流程
"""
# 1. 创建任务
task = await tracker.create_task("backtest_001", total_steps=10)

# 2. 启动任务
await tracker.start_task("backtest_001")

# 3. 逐步更新进度
await tracker.update_progress(
    "backtest_001",
    progress=10.0,
    current_step="数据加载",
    message="正在加载历史数据..."
)

await tracker.update_progress(
    "backtest_001",
    progress=50.0,
    current_step="策略执行",
    message="正在执行KDJ策略..."
)

# 4. 完成任务
await tracker.complete_task(
    "backtest_001",
    final_message="回测完成",
    result_data={
        "total_return": 15.67,
        "sharpe_ratio": 1.23,
        "trades_count": 48
    }
)
"""


# 导出
__all__ = [
    "BacktestProgressTracker",
    "ProgressUpdate",
    "TaskStatus",
    "create_backtest_task",
    "update_backtest_step"
]
