"""
任務Repository實現
實現任務數據的CRUD操作、查詢、過濾、分頁等功能
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, or_, desc, asc, func, text
from sqlalchemy.exc import SQLAlchemyError
import json
import logging

from .base_repository import BaseRepository
from ..models.task import Task
from ..models.task_status import TaskStatus, Priority

logger = logging.getLogger(__name__)


class TaskRepository(BaseRepository[Task]):
    """
    任務Repository實現

    專門負責任務數據的持久化操作，提供：
    - 基本CRUD操作
    - 複雜查詢和過濾
    - 狀態管理和流轉
    - 依賴關係查詢
    - 統計和分析
    """

    def __init__(self, db: Session, cache_manager=None):
        """初始化TaskRepository

        Args:
            db: SQLAlchemy數據庫會話
            cache_manager: 緩存管理器（可選）
        """
        super().__init__(cache_manager)
        self.db = db
        self.model = Task

    async def get_by_id(self, task_id: str) -> Optional[Task]:
        """
        根據ID獲取任務

        Args:
            task_id: 任務ID

        Returns:
            任務對象，如果不存在返回None
        """
        try:
            cache_key = f"task:{task_id}"
            # 嘗試從緩存獲取
            if self.cache_manager:
                cached_task = await self.cache_manager.get(cache_key)
                if cached_task:
                    return Task(**cached_task)

            # 從數據庫查詢
            task = self.db.query(Task).options(
                selectinload(Task.dependencies),
                selectinload(Task.dependents)
            ).filter(Task.id == task_id).first()

            if task and self.cache_manager:
                await self.cache_manager.set(
                    cache_key,
                    self._task_to_dict(task),
                    ttl=300
                )

            return task

        except SQLAlchemyError as e:
            logger.error(f"獲取任務失敗 (ID: {task_id}): {e}")
            return None

    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0
    ) -> List[Task]:
        """
        獲取任務列表

        Args:
            filters: 過濾條件字典
                - status: 狀態過濾
                - priority: 優先級過濾
                - assignee: 被分配者過濾
                - sprint: Sprint過濾
                - reporter: 報告者過濾
                - date_range: 日期範圍 (start_date, end_date)
                - search: 搜索關鍵詞 (搜索標題和描述)
            sort_by: 排序字段
            sort_order: 排序方向 (asc/desc)
            limit: 限制數量
            offset: 偏移量

        Returns:
            任務列表
        """
        try:
            query = self.db.query(Task)

            # 應用過濾條件
            if filters:
                query = self._apply_filters(query, filters)

            # 排序
            if sort_order.lower() == "asc":
                query = query.order_by(asc(sort_by))
            else:
                query = query.order_by(desc(sort_by))

            # 分頁
            tasks = query.offset(offset).limit(limit).all()

            return tasks

        except SQLAlchemyError as e:
            logger.error(f"獲取任務列表失敗: {e}")
            return []

    async def create(self, data: Dict[str, Any]) -> Optional[Task]:
        """
        創建新任務

        Args:
            data: 任務數據字典

        Returns:
            創建的任務對象
        """
        try:
            # 生成任務ID
            data['id'] = await self._generate_task_id()

            # 設置默認值
            data.setdefault('status', TaskStatus.TODO)
            data.setdefault('priority', Priority.P2)
            data.setdefault('story_points', 1)
            data.setdefault('created_at', datetime.utcnow())
            data.setdefault('updated_at', datetime.utcnow())

            # 處理數組字段
            array_fields = ['watchers', 'dependencies', 'dependents',
                          'acceptance_criteria', 'deliverables']
            for field in array_fields:
                if field not in data:
                    data[field] = []

            # 創建任務對象
            task = Task(**data)

            # 保存到數據庫
            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)

            # 清除相關緩存
            if self.cache_manager:
                await self.cache_manager.delete_pattern("tasks:*")
                await self.cache_manager.delete_pattern(f"task:{task.id}")

            logger.info(f"任務創建成功: {task.id}")

            return task

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"創建任務失敗: {e}")
            return None

    async def update(self, task_id: str, data: Dict[str, Any]) -> Optional[Task]:
        """
        更新任務

        Args:
            task_id: 任務ID
            data: 更新數據

        Returns:
            更新後的任務對象
        """
        try:
            # 獲取現有任務
            task = await self.get_by_id(task_id)
            if not task:
                logger.warning(f"任務不存在: {task_id}")
                return None

            # 更新字段
            for key, value in data.items():
                if hasattr(task, key):
                    setattr(task, key, value)

            # 更新時間戳
            task.updated_at = datetime.utcnow()

            # 保存到數據庫
            self.db.commit()
            self.db.refresh(task)

            # 清除緩存
            if self.cache_manager:
                await self.cache_manager.delete(f"task:{task_id}")
                await self.cache_manager.delete_pattern("tasks:*")

            logger.info(f"任務更新成功: {task_id}")

            return task

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"更新任務失敗 (ID: {task_id}): {e}")
            return None

    async def delete(self, task_id: str) -> bool:
        """
        刪除任務

        Args:
            task_id: 任務ID

        Returns:
            是否刪除成功
        """
        try:
            task = await self.get_by_id(task_id)
            if not task:
                logger.warning(f"任務不存在: {task_id}")
                return False

            # 檢查是否有依賴
            if task.dependents:
                logger.warning(f"任務 {task_id} 有依賴任務，無法刪除")
                return False

            # 刪除任務
            self.db.delete(task)
            self.db.commit()

            # 清除緩存
            if self.cache_manager:
                await self.cache_manager.delete(f"task:{task_id}")
                await self.cache_manager.delete_pattern("tasks:*")

            logger.info(f"任務刪除成功: {task_id}")

            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"刪除任務失敗 (ID: {task_id}): {e}")
            return False

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        統計任務數量

        Args:
            filters: 過濾條件

        Returns:
            任務數量
        """
        try:
            query = self.db.query(func.count(Task.id))

            if filters:
                query = self._apply_filters(query, filters)

            return query.scalar()

        except SQLAlchemyError as e:
            logger.error(f"統計任務數量失敗: {e}")
            return 0

    async def transition_status(
        self,
        task_id: str,
        new_status: TaskStatus,
        comment: Optional[str] = None
    ) -> Optional[Task]:
        """
        轉換任務狀態

        Args:
            task_id: 任務ID
            new_status: 新狀態
            comment: 變更說明

        Returns:
            更新後的任務對象
        """
        try:
            task = await self.get_by_id(task_id)
            if not task:
                return None

            old_status = task.status

            # 檢查狀態轉換是否合法
            if not task.status.can_transition_to(new_status):
                logger.error(
                    f"非法狀態轉換: {old_status} -> {new_status} (任務: {task_id})"
                )
                return None

            # 執行狀態轉換
            task.status = new_status
            task.updated_at = datetime.utcnow()

            # 設置完成時間
            if new_status == TaskStatus.DONE:
                task.completed_at = datetime.utcnow()

            # 記錄變更元數據
            if task.metadata is None:
                task.metadata = {}

            if 'status_changes' not in task.metadata:
                task.metadata['status_changes'] = []

            task.metadata['status_changes'].append({
                'from': old_status.value,
                'to': new_status.value,
                'comment': comment,
                'timestamp': datetime.utcnow().isoformat()
            })

            self.db.commit()
            self.db.refresh(task)

            # 清除緩存
            if self.cache_manager:
                await self.cache_manager.delete(f"task:{task_id}")
                await self.cache_manager.delete_pattern("tasks:*")

            logger.info(
                f"任務狀態轉換成功: {task_id} {old_status} -> {new_status}"
            )

            return task

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"狀態轉換失敗 (ID: {task_id}): {e}")
            return None

    async def assign_task(self, task_id: str, assignee: str) -> Optional[Task]:
        """
        分配任務

        Args:
            task_id: 任務ID
            assignee: 被分配者

        Returns:
            更新後的任務對象
        """
        return await self.update(task_id, {'assignee': assignee})

    async def add_dependency(self, task_id: str, dependency_id: str) -> Optional[Task]:
        """
        添加前置依賴

        Args:
            task_id: 任務ID
            dependency_id: 依賴的任務ID

        Returns:
            更新後的任務對象
        """
        try:
            task = await self.get_by_id(task_id)
            if not task:
                return None

            # 檢查依賴任務是否存在
            dep_task = await self.get_by_id(dependency_id)
            if not dep_task:
                logger.warning(f"依賴任務不存在: {dependency_id}")
                return None

            # 防止循環依賴
            if await self._would_create_circular_dependency(task_id, dependency_id):
                logger.error(f"會造成循環依賴: {task_id} -> {dependency_id}")
                return None

            # 添加依賴
            if dependency_id not in task.dependencies:
                task.dependencies.append(dependency_id)
                task.updated_at = datetime.utcnow()

                self.db.commit()

            # 清除緩存
            if self.cache_manager:
                await self.cache_manager.delete(f"task:{task_id}")
                await self.cache_manager.delete_pattern("tasks:*")

            return task

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"添加依賴失敗 (ID: {task_id}): {e}")
            return None

    async def get_blocked_tasks(self) -> List[Task]:
        """
        獲取所有被阻塞的任務

        Returns:
            被阻塞的任務列表
        """
        try:
            blocked_tasks = self.db.query(Task).filter(
                Task.status == TaskStatus.BLOCKED
            ).all()

            return blocked_tasks

        except SQLAlchemyError as e:
            logger.error(f"獲取阻塞任務失敗: {e}")
            return []

    async def get_tasks_by_sprint(self, sprint_id: str) -> List[Task]:
        """
        獲取指定Sprint的所有任務

        Args:
            sprint_id: Sprint ID

        Returns:
            任務列表
        """
        try:
            tasks = self.db.query(Task).filter(
                Task.sprint == sprint_id
            ).order_by(desc(Task.priority)).all()

            return tasks

        except SQLAlchemyError as e:
            logger.error(f"獲取Sprint任務失敗 (Sprint: {sprint_id}): {e}")
            return []

    async def get_task_statistics(self, sprint_id: Optional[str] = None) -> Dict[str, Any]:
        """
        獲取任務統計信息

        Args:
            sprint_id: 可選的Sprint ID

        Returns:
            統計信息字典
        """
        try:
            query = self.db.query(Task)

            if sprint_id:
                query = query.filter(Task.sprint == sprint_id)

            total_tasks = query.count()

            # 按狀態統計
            status_stats = {}
            for status in TaskStatus:
                count = query.filter(Task.status == status).count()
                status_stats[status.value] = count

            # 按優先級統計
            priority_stats = {}
            for priority in Priority:
                count = query.filter(Task.priority == priority).count()
                priority_stats[priority.value] = count

            # 計算完成率
            completed = status_stats.get(TaskStatus.DONE.value, 0)
            completion_rate = (completed / total_tasks * 100) if total_tasks > 0 else 0

            # 計算預估總工時
            total_estimated = query.with_entities(
                func.sum(Task.estimated_hours)
            ).scalar() or 0

            # 計算實際工時
            total_actual = query.with_entities(
                func.sum(Task.actual_hours)
            ).scalar() or 0

            return {
                'total_tasks': total_tasks,
                'status_distribution': status_stats,
                'priority_distribution': priority_stats,
                'completion_rate': round(completion_rate, 2),
                'total_estimated_hours': total_estimated,
                'total_actual_hours': total_actual,
                'sprint_id': sprint_id
            }

        except SQLAlchemyError as e:
            logger.error(f"獲取任務統計失敗: {e}")
            return {}

    # ==================== 私有方法 ====================

    def _apply_filters(self, query, filters: Dict[str, Any]):
        """應用過濾條件"""
        # 狀態過濾
        if 'status' in filters and filters['status']:
            query = query.filter(Task.status == filters['status'])

        # 優先級過濾
        if 'priority' in filters and filters['priority']:
            query = query.filter(Task.priority == filters['priority'])

        # 被分配者過濾
        if 'assignee' in filters and filters['assignee']:
            query = query.filter(Task.assignee == filters['assignee'])

        # Sprint過濾
        if 'sprint' in filters and filters['sprint']:
            query = query.filter(Task.sprint == filters['sprint'])

        # 報告者過濾
        if 'reporter' in filters and filters['reporter']:
            query = query.filter(Task.reporter == filters['reporter'])

        # 日期範圍過濾
        if 'date_range' in filters:
            date_range = filters['date_range']
            if isinstance(date_range, dict):
                if 'start_date' in date_range:
                    query = query.filter(Task.created_at >= date_range['start_date'])
                if 'end_date' in date_range:
                    query = query.filter(Task.created_at <= date_range['end_date'])

        # 搜索過濾
        if 'search' in filters and filters['search']:
            search_term = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    Task.title.like(search_term),
                    Task.description.like(search_term)
                )
            )

        return query

    async def _generate_task_id(self) -> str:
        """生成新的任務ID"""
        try:
            # 獲取最大ID數字
            result = self.db.query(Task.id).all()
            max_num = 0
            for row in result:
                id_str = row[0]
                if id_str.startswith('TASK-'):
                    try:
                        num = int(id_str.split('-')[1])
                        max_num = max(max_num, num)
                    except (ValueError, IndexError):
                        pass

            new_num = max_num + 1
            return f"TASK-{new_num:03d}"

        except SQLAlchemyError as e:
            logger.error(f"生成任務ID失敗: {e}")
            # 返回時間戳作為備用
            return f"TASK-{int(datetime.utcnow().timestamp())}"

    async def _would_create_circular_dependency(
        self,
        task_id: str,
        dependency_id: str
    ) -> bool:
        """檢查是否會造成循環依賴"""
        try:
            # 檢查dependency_id是否依賴task_id
            dependent = self.db.query(Task).filter(
                Task.dependencies.contains([task_id])
            ).all()

            return dependency_id in [d.id for d in dependent]

        except SQLAlchemyError as e:
            logger.error(f"檢查循環依賴失敗: {e}")
            return True  # 保守處理，認為有循環依賴

    def _task_to_dict(self, task: Task) -> Dict[str, Any]:
        """轉換任務為字典"""
        result = {}
        for column in task.__table__.columns:
            value = getattr(task, column.name)
            if isinstance(value, (datetime, date)):
                value = value.isoformat() if value else None
            elif isinstance(value, list):
                value = value or []
            result[column.name] = value
        return result

    def _calculate_story_points(self, estimated_hours: int) -> int:
        """
        根據預估工時計算故事點數

        Args:
            estimated_hours: 預估工時

        Returns:
            故事點數
        """
        if estimated_hours <= 2:
            return 1
        elif estimated_hours <= 4:
            return 2
        elif estimated_hours <= 8:
            return 3
        else:
            return 5
