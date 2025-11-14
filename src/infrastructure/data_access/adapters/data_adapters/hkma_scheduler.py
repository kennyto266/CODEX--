"""
HKMA数据更新调度器
管理HIBOR数据的自动更新任务

功能:
- 定时任务调度
- 每日更新机制
- 优先级管理
- 任务状态跟踪
- 失败重试
- 节假日跳过
"""

import asyncio
import logging
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
import aiofiles
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class ScheduledTask:
    """计划任务数据类"""
    id: str
    name: str
    type: str
    priority: TaskPriority
    status: TaskStatus
    scheduled_time: datetime
    started_time: Optional[datetime]
    completed_time: Optional[datetime]
    last_error: Optional[str]
    retry_count: int
    max_retries: int
    data: Dict[str, Any]
    result: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            **asdict(self),
            'priority': self.priority.value,
            'status': self.status.value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduledTask':
        """从字典创建实例"""
        return cls(
            id=data['id'],
            name=data['name'],
            type=data['type'],
            priority=TaskPriority(data['priority']),
            status=TaskStatus(data['status']),
            scheduled_time=datetime.fromisoformat(data['scheduled_time']),
            started_time=datetime.fromisoformat(data['started_time']) if data.get('started_time') else None,
            completed_time=datetime.fromisoformat(data['completed_time']) if data.get('completed_time') else None,
            last_error=data.get('last_error'),
            retry_count=data.get('retry_count', 0),
            max_retries=data.get('max_retries', 3),
            data=data.get('data', {}),
            result=data.get('result'),
            metadata=data.get('metadata', {})
        )


class TaskScheduler:
    """任务调度器"""

    # 任务存储文件
    TASK_STORE_FILE = "data/hkma_task_store.json"

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化任务调度器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # 任务存储
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}

        # 调度器设置
        self.scheduler_interval = self.config.get('scheduler_interval', 60)  # 秒
        self.cleanup_interval = self.config.get('cleanup_interval', 3600)  # 1小时
        self.max_concurrent_tasks = self.config.get('max_concurrent_tasks', 5)
        self.auto_start = self.config.get('auto_start', True)

        # 执行器
        self.executor = None
        self.scheduler_task = None
        self.cleanup_task = None

        # 任务执行器映射
        self.task_handlers: Dict[str, Callable] = {}

        # 加载任务存储
        # self._load_task_store()

    def register_handler(self, task_type: str, handler: Callable):
        """
        注册任务处理器

        Args:
            task_type: 任务类型
            handler: 异步处理函数
        """
        self.task_handlers[task_type] = handler
        self.logger.info(f"注册任务处理器: {task_type}")

    async def start(self):
        """启动调度器"""
        if self.scheduler_task and not self.scheduler_task.done():
            self.logger.warning("调度器已在运行")
            return

        self.logger.info("启动HKMA数据调度器...")

        # 启动调度器任务
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())

        # 启动清理任务
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())

        # 启动失败任务重试
        asyncio.create_task(self._retry_failed_tasks())

        self.logger.info("调度器已启动")

    async def stop(self):
        """停止调度器"""
        self.logger.info("停止调度器...")

        # 取消调度器任务
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass

        # 取消清理任务
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

        # 等待运行中的任务完成
        if self.running_tasks:
            self.logger.info(f"等待 {len(self.running_tasks)} 个任务完成...")
            await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)

        self.logger.info("调度器已停止")

    async def schedule_daily_update(
        self,
        task_name: str,
        run_time: str = "08:00",
        task_data: Optional[Dict] = None,
        priority: TaskPriority = TaskPriority.HIGH,
        max_retries: int = 3
    ) -> str:
        """
        计划每日更新任务

        Args:
            task_name: 任务名称
            run_time: 运行时间 (HH:MM)
            task_data: 任务数据
            priority: 优先级
            max_retries: 最大重试次数

        Returns:
            任务ID
        """
        task_id = f"daily_{task_name}_{datetime.now().strftime('%Y%m%d')}"

        # 解析运行时间
        hour, minute = map(int, run_time.split(':'))

        # 计算下次运行时间
        next_run = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)

        # 如果今天已经过了运行时间，改为明天
        if next_run <= datetime.now():
            next_run += timedelta(days=1)

        task = ScheduledTask(
            id=task_id,
            name=task_name,
            type="daily_update",
            priority=priority,
            status=TaskStatus.PENDING,
            scheduled_time=next_run,
            started_time=None,
            completed_time=None,
            last_error=None,
            retry_count=0,
            max_retries=max_retries,
            data=task_data or {},
            result=None,
            metadata={'run_time': run_time, 'frequency': 'daily'}
        )

        self.tasks[task_id] = task
        await self._save_task_store()

        self.logger.info(f"计划每日任务: {task_name} 于 {next_run.isoformat()}")
        return task_id

    async def schedule_historical_data_update(
        self,
        start_date: date,
        end_date: Optional[date] = None,
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> str:
        """
        计划历史数据更新任务

        Args:
            start_date: 开始日期
            end_date: 结束日期（默认今天）
            priority: 优先级

        Returns:
            任务ID
        """
        if end_date is None:
            end_date = date.today()

        task_id = f"historical_update_{start_date}_{end_date}"

        task = ScheduledTask(
            id=task_id,
            name=f"历史数据更新: {start_date} - {end_date}",
            type="historical_update",
            priority=priority,
            status=TaskStatus.PENDING,
            scheduled_time=datetime.now(),
            started_time=None,
            completed_time=None,
            last_error=None,
            retry_count=0,
            max_retries=3,
            data={
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            result=None,
            metadata={'date_range': f"{start_date} 到 {end_date}"}
        )

        self.tasks[task_id] = task
        await self._save_task_store()

        self.logger.info(f"计划历史数据更新任务: {start_date} - {end_date}")
        return task_id

    async def schedule_custom_task(
        self,
        task_name: str,
        task_type: str,
        run_time: datetime,
        task_data: Optional[Dict] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3
    ) -> str:
        """
        计划自定义任务

        Args:
            task_name: 任务名称
            task_type: 任务类型
            run_time: 运行时间
            task_data: 任务数据
            priority: 优先级
            max_retries: 最大重试次数

        Returns:
            任务ID
        """
        task_id = f"custom_{task_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        task = ScheduledTask(
            id=task_id,
            name=task_name,
            type=task_type,
            priority=priority,
            status=TaskStatus.PENDING,
            scheduled_time=run_time,
            started_time=None,
            completed_time=None,
            last_error=None,
            retry_count=0,
            max_retries=max_retries,
            data=task_data or {},
            result=None,
            metadata={}
        )

        self.tasks[task_id] = task
        await self._save_task_store()

        self.logger.info(f"计划自定义任务: {task_name} 于 {run_time.isoformat()}")
        return task_id

    async def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功取消
        """
        if task_id not in self.tasks:
            self.logger.warning(f"任务不存在: {task_id}")
            return False

        task = self.tasks[task_id]

        if task.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
            self.logger.warning(f"任务已结束: {task_id}")
            return False

        # 如果任务正在运行，先取消
        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            del self.running_tasks[task_id]

        # 更新任务状态
        task.status = TaskStatus.CANCELLED
        task.completed_time = datetime.now()

        await self._save_task_store()
        self.logger.info(f"任务已取消: {task_id}")
        return True

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态字典
        """
        if task_id not in self.tasks:
            return None

        return self.tasks[task_id].to_dict()

    async def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        task_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        列出任务

        Args:
            status: 状态过滤
            task_type: 类型过滤
            limit: 限制数量

        Returns:
            任务列表
        """
        tasks = list(self.tasks.values())

        if status:
            tasks = [t for t in tasks if t.status == status]

        if task_type:
            tasks = [t for t in tasks if t.type == task_type]

        # 按优先级和时间排序
        tasks.sort(key=lambda t: (t.priority.value, t.scheduled_time), reverse=True)

        if limit:
            tasks = tasks[:limit]

        return [task.to_dict() for task in tasks]

    async def _scheduler_loop(self):
        """调度器主循环"""
        self.logger.info("调度器循环已启动")

        while True:
            try:
                await self._process_pending_tasks()
                await asyncio.sleep(self.scheduler_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"调度器循环错误: {e}")
                await asyncio.sleep(5)

    async def _process_pending_tasks(self):
        """处理待执行任务"""
        now = datetime.now()
        pending_tasks = [
            task for task in self.tasks.values()
            if task.status == TaskStatus.PENDING
            and task.scheduled_time <= now
        ]

        # 按优先级排序
        pending_tasks.sort(key=lambda t: t.priority.value, reverse=True)

        # 检查并发限制
        available_slots = self.max_concurrent_tasks - len(self.running_tasks)

        for task in pending_tasks[:available_slots]:
            await self._execute_task(task)

    async def _execute_task(self, task: ScheduledTask):
        """执行任务"""
        task_id = task.id
        self.logger.info(f"开始执行任务: {task.name} ({task_id})")

        # 更新任务状态
        task.status = TaskStatus.RUNNING
        task.started_time = datetime.now()
        task.retry_count += 1

        await self._save_task_store()

        # 创建执行任务
        exec_task = asyncio.create_task(self._run_task_handler(task))
        self.running_tasks[task_id] = exec_task

        try:
            # 等待任务完成
            result = await exec_task

            # 更新任务状态
            task.status = TaskStatus.COMPLETED
            task.completed_time = datetime.now()
            task.result = result
            task.last_error = None

            self.logger.info(f"任务完成: {task.name} ({task_id})")

        except asyncio.CancelledError:
            task.status = TaskStatus.CANCELLED
            task.completed_time = datetime.now()
            self.logger.warning(f"任务取消: {task.name} ({task_id})")

        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"任务失败: {task.name} ({task_id}): {error_msg}")

            # 检查是否需要重试
            if task.retry_count < task.max_retries:
                task.status = TaskStatus.PENDING
                task.scheduled_time = datetime.now() + timedelta(
                    minutes=2 ** task.retry_count  # 指数退避
                )
                task.last_error = error_msg

                self.logger.info(
                    f"任务将在 {task.scheduled_time} 重新执行 "
                    f"(第 {task.retry_count + 1} 次尝试)"
                )
            else:
                task.status = TaskStatus.FAILED
                task.completed_time = datetime.now()
                task.last_error = error_msg

                self.logger.error(f"任务达到最大重试次数: {task.name}")

        finally:
            # 清理运行任务
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]

            await self._save_task_store()

    async def _run_task_handler(self, task: ScheduledTask) -> Dict[str, Any]:
        """运行任务处理器"""
        handler = self.task_handlers.get(task.type)

        if not handler:
            raise ValueError(f"未找到任务处理器: {task.type}")

        # 调用处理器
        if asyncio.iscoroutinefunction(handler):
            return await handler(task)
        else:
            # 同步函数在线程池中运行
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, handler, task)

    async def _retry_failed_tasks(self):
        """重试失败任务"""
        while True:
            try:
                # 查找可以重试的失败任务
                for task in self.tasks.values():
                    if (task.status == TaskStatus.FAILED
                        and task.retry_count < task.max_retries
                        and task.scheduled_time <= datetime.now()):

                        self.logger.info(f"重试失败任务: {task.name}")
                        task.status = TaskStatus.PENDING
                        task.scheduled_time = datetime.now()
                        task.last_error = None

                await self._save_task_store()
                await asyncio.sleep(300)  # 每5分钟检查一次

            except Exception as e:
                self.logger.error(f"重试任务错误: {e}")
                await asyncio.sleep(60)

    async def _cleanup_loop(self):
        """清理过期任务"""
        self.logger.info("清理循环已启动")

        while True:
            try:
                await self._cleanup_old_tasks()
                await asyncio.sleep(self.cleanup_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"清理循环错误: {e}")
                await asyncio.sleep(300)

    async def _cleanup_old_tasks(self):
        """清理过期任务"""
        now = datetime.now()
        retention_days = self.config.get('task_retention_days', 30)

        # 找出需要清理的任务
        tasks_to_remove = []
        for task_id, task in self.tasks.items():
            if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
                and task.completed_time
                and (now - task.completed_time).days > retention_days):
                tasks_to_remove.append(task_id)

        # 删除过期任务
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
            self.logger.info(f"清理过期任务: {task_id}")

        if tasks_to_remove:
            await self._save_task_store()

    async def _load_task_store(self):
        """加载任务存储"""
        try:
            if os.path.exists(self.TASK_STORE_FILE):
                async with aiofiles.open(self.TASK_STORE_FILE, 'r') as f:
                    content = await f.read()
                    data = json.loads(content)

                    for task_id, task_data in data.get('tasks', {}).items():
                        self.tasks[task_id] = ScheduledTask.from_dict(task_data)

                self.logger.info(f"加载了 {len(self.tasks)} 个任务")
        except Exception as e:
            self.logger.error(f"加载任务存储失败: {e}")

    async def _save_task_store(self):
        """保存任务存储"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.TASK_STORE_FILE), exist_ok=True)

            # 准备数据
            data = {
                'tasks': {task_id: task.to_dict() for task_id, task in self.tasks.items()},
                'updated_at': datetime.now().isoformat()
            }

            async with aiofiles.open(self.TASK_STORE_FILE, 'w') as f:
                await f.write(json.dumps(data, indent=2, default=str))
        except Exception as e:
            self.logger.error(f"保存任务存储失败: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取调度器统计信息

        Returns:
            统计信息字典
        """
        stats = {
            'total_tasks': len(self.tasks),
            'pending_tasks': sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING),
            'running_tasks': len(self.running_tasks),
            'completed_tasks': sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED),
            'failed_tasks': sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED),
            'cancelled_tasks': sum(1 for t in self.tasks.values() if t.status == TaskStatus.CANCELLED),
        }

        return stats


# 全局调度器实例
scheduler: Optional[TaskScheduler] = None


async def get_scheduler() -> TaskScheduler:
    """获取全局调度器实例"""
    global scheduler
    if scheduler is None:
        scheduler = TaskScheduler()
    return scheduler


# 示例：HIBOR更新处理器
async def hibor_update_handler(task: ScheduledTask) -> Dict[str, Any]:
    """
    HIBOR更新任务处理器示例

    Args:
        task: 任务对象

    Returns:
        执行结果
    """
    from .hkma_hibor import HKMAHibiorAdapter

    result = {'success': False, 'message': ''}

    try:
        async with HKMAHibiorAdapter() as adapter:
            if task.type == "daily_update":
                # 获取最新HIBOR
                latest = await adapter.fetch_latest_hibor()

                if latest:
                    result.update({
                        'success': True,
                        'message': '成功获取HIBOR数据',
                        'data': latest
                    })
                else:
                    result['message'] = '未能获取HIBOR数据'

            elif task.type == "historical_update":
                # 获取历史数据
                start_date = date.fromisoformat(task.data['start_date'])
                end_date = date.fromisoformat(task.data['end_date'])

                historical = await adapter.fetch_historical_hibor(start_date, end_date)

                if historical is not None and not historical.empty:
                    result.update({
                        'success': True,
                        'message': f'成功获取 {len(historical)} 条历史记录',
                        'data': {
                            'start_date': start_date.isoformat(),
                            'end_date': end_date.isoformat(),
                            'count': len(historical)
                        }
                    })
                else:
                    result['message'] = '未能获取历史数据'

    except Exception as e:
        result['message'] = f'处理错误: {e}'
        raise

    return result


if __name__ == "__main__":
    # 测试代码
    async def test():
        scheduler = TaskScheduler()
        scheduler.register_handler("daily_update", hibor_update_handler)
        scheduler.register_handler("historical_update", hibor_update_handler)

        # 启动调度器
        await scheduler.start()

        # 计划每日更新
        task_id = await scheduler.schedule_daily_update("hibor_daily", "09:00")
        print(f"计划任务: {task_id}")

        # 等待一段时间
        await asyncio.sleep(10)

        # 查看统计
        stats = scheduler.get_statistics()
        print(f"调度器统计: {json.dumps(stats, indent=2, default=str)}")

        # 停止调度器
        await scheduler.stop()

    asyncio.run(test())
