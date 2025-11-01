"""
Sprint Repository實現
實現Sprint數據的CRUD操作、查詢、過濾、分頁、規劃等功能
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, or_, desc, asc, func, text
from sqlalchemy.exc import SQLAlchemyError
import json
import logging

from .base_repository import BaseRepository
from ..models.sprint import Sprint
from ..models.task_status import SprintStatus
from ..models.task import Task

logger = logging.getLogger(__name__)


class SprintRepository(BaseRepository[Sprint]):
    """
    Sprint Repository實現

    專門負責Sprint數據的持久化操作，提供：
    - 基本CRUD操作
    - Sprint規劃和任務分配
    - 容量和速度計算
    - 燃盡圖數據管理
    - Sprint統計和分析
    """

    def __init__(self, db: Session, cache_manager=None):
        """初始化SprintRepository

        Args:
            db: SQLAlchemy數據庫會話
            cache_manager: 緩存管理器（可選）
        """
        super().__init__(cache_manager)
        self.db = db
        self.model = Sprint

    async def get_by_id(self, sprint_id: str) -> Optional[Sprint]:
        """
        根據ID獲取Sprint

        Args:
            sprint_id: Sprint ID

        Returns:
            Sprint對象，如果不存在返回None
        """
        try:
            cache_key = f"sprint:{sprint_id}"
            # 嘗試從緩存獲取
            if self.cache_manager:
                cached_sprint = await self.cache_manager.get(cache_key)
                if cached_sprint:
                    return Sprint(**cached_sprint)

            # 從數據庫查詢
            sprint = self.db.query(Sprint).filter(Sprint.id == sprint_id).first()

            if sprint and self.cache_manager:
                await self.cache_manager.set(
                    cache_key,
                    self._sprint_to_dict(sprint),
                    ttl=300
                )

            return sprint

        except SQLAlchemyError as e:
            logger.error(f"獲取Sprint失敗 (ID: {sprint_id}): {e}")
            return None

    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "start_date",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0
    ) -> List[Sprint]:
        """
        獲取Sprint列表

        Args:
            filters: 過濾條件字典
                - status: 狀態過濾
                - date_range: 日期範圍 (start_date, end_date)
                - active_only: 是否只獲取活躍Sprint
            sort_by: 排序字段
            sort_order: 排序方向 (asc/desc)
            limit: 限制數量
            offset: 偏移量

        Returns:
            Sprint列表
        """
        try:
            query = self.db.query(Sprint)

            # 應用過濾條件
            if filters:
                query = self._apply_filters(query, filters)

            # 排序
            if sort_order.lower() == "asc":
                query = query.order_by(asc(sort_by))
            else:
                query = query.order_by(desc(sort_by))

            # 分頁
            sprints = query.offset(offset).limit(limit).all()

            return sprints

        except SQLAlchemyError as e:
            logger.error(f"獲取Sprint列表失敗: {e}")
            return []

    async def create(self, data: Dict[str, Any]) -> Optional[Sprint]:
        """
        創建新Sprint

        Args:
            data: Sprint數據字典

        Returns:
            創建的Sprint對象
        """
        try:
            # 生成Sprint ID
            data['id'] = await self._generate_sprint_id(data['start_date'])

            # 設置默認值
            data.setdefault('status', SprintStatus.PLANNING)
            data.setdefault('task_ids', [])
            data.setdefault('planned_hours', 0)
            data.setdefault('completed_hours', 0)
            data.setdefault('team_capacity', 0)
            data.setdefault('velocity', 0.0)
            data.setdefault('estimated_velocity', 0.0)
            data.setdefault('completion_rate', 0.0)
            data.setdefault('burndown_data', {})
            data.setdefault('improvements', [])
            data.setdefault('created_at', datetime.utcnow())
            data.setdefault('updated_at', datetime.utcnow())

            # 創建Sprint對象
            sprint = Sprint(**data)

            # 保存到數據庫
            self.db.add(sprint)
            self.db.commit()
            self.db.refresh(sprint)

            # 清除相關緩存
            if self.cache_manager:
                await self.cache_manager.delete_pattern("sprints:*")
                await self.cache_manager.delete_pattern(f"sprint:{sprint.id}")

            logger.info(f"Sprint創建成功: {sprint.id}")

            return sprint

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"創建Sprint失敗: {e}")
            return None

    async def update(self, sprint_id: str, data: Dict[str, Any]) -> Optional[Sprint]:
        """
        更新Sprint

        Args:
            sprint_id: Sprint ID
            data: 更新數據

        Returns:
            更新後的Sprint對象
        """
        try:
            # 獲取現有Sprint
            sprint = await self.get_by_id(sprint_id)
            if not sprint:
                logger.warning(f"Sprint不存在: {sprint_id}")
                return None

            # 更新字段
            for key, value in data.items():
                if hasattr(sprint, key):
                    setattr(sprint, key, value)

            # 更新時間戳
            sprint.updated_at = datetime.utcnow()

            # 保存到數據庫
            self.db.commit()
            self.db.refresh(sprint)

            # 清除緩存
            if self.cache_manager:
                await self.cache_manager.delete(f"sprint:{sprint_id}")
                await self.cache_manager.delete_pattern("sprints:*")

            logger.info(f"Sprint更新成功: {sprint_id}")

            return sprint

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"更新Sprint失敗 (ID: {sprint_id}): {e}")
            return None

    async def delete(self, sprint_id: str) -> bool:
        """
        刪除Sprint

        Args:
            sprint_id: Sprint ID

        Returns:
            是否刪除成功
        """
        try:
            sprint = await self.get_by_id(sprint_id)
            if not sprint:
                logger.warning(f"Sprint不存在: {sprint_id}")
                return False

            # 檢查是否為活躍Sprint
            if sprint.status == SprintStatus.ACTIVE:
                logger.warning(f"無法刪除活躍Sprint: {sprint_id}")
                return False

            # 檢查是否有任務
            if sprint.task_ids:
                logger.warning(f"Sprint {sprint_id} 包含任務，無法刪除")
                return False

            # 刪除Sprint
            self.db.delete(sprint)
            self.db.commit()

            # 清除緩存
            if self.cache_manager:
                await self.cache_manager.delete(f"sprint:{sprint_id}")
                await self.cache_manager.delete_pattern("sprints:*")

            logger.info(f"Sprint刪除成功: {sprint_id}")

            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"刪除Sprint失敗 (ID: {sprint_id}): {e}")
            return False

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        統計Sprint數量

        Args:
            filters: 過濾條件

        Returns:
            Sprint數量
        """
        try:
            query = self.db.query(func.count(Sprint.id))

            if filters:
                query = self._apply_filters(query, filters)

            return query.scalar()

        except SQLAlchemyError as e:
            logger.error(f"統計Sprint數量失敗: {e}")
            return 0

    async def plan_sprint(
        self,
        sprint_id: str,
        task_ids: List[str],
        planned_hours: int
    ) -> Optional[Sprint]:
        """
        規劃Sprint任務

        Args:
            sprint_id: Sprint ID
            task_ids: 任務ID列表
            planned_hours: 計劃工時

        Returns:
            更新後的Sprint對象
        """
        try:
            sprint = await self.get_by_id(sprint_id)
            if not sprint:
                return None

            # 驗證任務是否存在
            valid_task_ids = []
            for task_id in task_ids:
                task = self.db.query(Task).filter(Task.id == task_id).first()
                if task:
                    valid_task_ids.append(task_id)
                    # 將任務分配到Sprint
                    task.sprint = sprint_id

            # 更新Sprint
            sprint.task_ids = valid_task_ids
            sprint.planned_hours = planned_hours
            sprint.team_capacity = planned_hours  # 假設容量等於計劃工時
            sprint.updated_at = datetime.utcnow()

            self.db.commit()

            # 重新計算速度
            await self.calculate_velocity(sprint_id)

            # 清除緩存
            if self.cache_manager:
                await self.cache_manager.delete(f"sprint:{sprint_id}")

            logger.info(f"Sprint規劃完成: {sprint_id}, 任務數量: {len(valid_task_ids)}")

            return sprint

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"規劃Sprint失敗 (ID: {sprint_id}): {e}")
            return None

    async def calculate_velocity(self, sprint_id: str) -> float:
        """
        計算Sprint速度

        Args:
            sprint_id: Sprint ID

        Returns:
            Sprint速度 (已完成故事點數)
        """
        try:
            sprint = await self.get_by_id(sprint_id)
            if not sprint:
                return 0.0

            # 獲取已完成任務
            completed_tasks = self.db.query(Task).filter(
                and_(
                    Task.sprint == sprint_id,
                    Task.status == TaskStatus.DONE
                )
            ).all()

            # 計算速度
            velocity = sum(task.story_points for task in completed_tasks)
            sprint.velocity = velocity
            sprint.completed_hours = sum(task.actual_hours or 0 for task in completed_tasks)

            # 計算完成率
            if sprint.planned_hours > 0:
                sprint.completion_rate = (sprint.completed_hours / sprint.planned_hours) * 100

            self.db.commit()

            # 清除緩存
            if self.cache_manager:
                await self.cache_manager.delete(f"sprint:{sprint_id}")

            logger.info(f"速度計算完成: {sprint_id}, 速度: {velocity}")

            return velocity

        except SQLAlchemyError as e:
            logger.error(f"計算Sprint速度失敗 (ID: {sprint_id}): {e}")
            return 0.0

    async def update_burndown(
        self,
        sprint_id: str,
        day_offset: int,
        remaining_hours: float
    ) -> Optional[Sprint]:
        """
        更新燃盡圖數據

        Args:
            sprint_id: Sprint ID
            day_offset: 第幾天 (相對開始日期)
            remaining_hours: 剩餘工時

        Returns:
            更新後的Sprint對象
        """
        try:
            sprint = await self.get_by_id(sprint_id)
            if not sprint:
                return None

            # 初始化燃盡圖數據
            if sprint.burndown_data is None:
                sprint.burndown_data = {"days": [], "remaining": []}

            # 更新數據
            days = sprint.burndown_data.get("days", [])
            remaining = sprint.burndown_data.get("remaining", [])

            # 如果該天已存在，則更新
            if day_offset in days:
                idx = days.index(day_offset)
                remaining[idx] = remaining_hours
            else:
                days.append(day_offset)
                remaining.append(remaining_hours)

            sprint.burndown_data["days"] = sorted(days)
            sprint.burndown_data["remaining"] = remaining

            self.db.commit()

            # 清除緩存
            if self.cache_manager:
                await self.cache_manager.delete(f"sprint:{sprint_id}")

            return sprint

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"更新燃盡圖失敗 (ID: {sprint_id}): {e}")
            return None

    async def get_active_sprint(self) -> Optional[Sprint]:
        """
        獲取當前活躍Sprint

        Returns:
            活躍Sprint對象
        """
        try:
            today = date.today()

            sprint = self.db.query(Sprint).filter(
                and_(
                    Sprint.status == SprintStatus.ACTIVE,
                    Sprint.start_date <= today,
                    Sprint.end_date >= today
                )
            ).first()

            return sprint

        except SQLAlchemyError as e:
            logger.error(f"獲取活躍Sprint失敗: {e}")
            return None

    async def get_sprint_tasks(self, sprint_id: str) -> List[Task]:
        """
        獲取Sprint的所有任務

        Args:
            sprint_id: Sprint ID

        Returns:
            任務列表
        """
        try:
            tasks = self.db.query(Task).filter(
                Task.sprint == sprint_id
            ).order_by(
                desc(Task.priority),
                asc(Task.created_at)
            ).all()

            return tasks

        except SQLAlchemyError as e:
            logger.error(f"獲取Sprint任務失敗 (Sprint: {sprint_id}): {e}")
            return []

    async def get_sprint_statistics(self, sprint_id: str) -> Dict[str, Any]:
        """
        獲取Sprint統計信息

        Args:
            sprint_id: Sprint ID

        Returns:
            統計信息字典
        """
        try:
            sprint = await self.get_by_id(sprint_id)
            if not sprint:
                return {}

            # 獲取所有任務
            tasks = await self.get_sprint_tasks(sprint_id)

            # 按狀態統計
            status_stats = {}
            for status in TaskStatus:
                count = sum(1 for task in tasks if task.status == status)
                status_stats[status.value] = count

            # 按優先級統計
            priority_stats = {}
            for priority in ['P0', 'P1', 'P2']:
                count = sum(1 for task in tasks if task.priority and task.priority.value == priority)
                priority_stats[priority] = count

            # 計算指標
            total_tasks = len(tasks)
            completed_tasks = status_stats.get(TaskStatus.DONE.value, 0)
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

            # 計算故事點數
            total_points = sum(task.story_points for task in tasks)
            completed_points = sum(task.story_points for task in tasks if task.is_completed)

            # 計算工時
            total_estimated = sum(task.estimated_hours for task in tasks)
            total_actual = sum(task.actual_hours or 0 for task in tasks)

            # 計算剩餘時間
            remaining_hours = max(0, sprint.planned_hours - sprint.completed_hours)

            return {
                'sprint_id': sprint_id,
                'total_tasks': total_tasks,
                'status_distribution': status_stats,
                'priority_distribution': priority_stats,
                'total_story_points': total_points,
                'completed_story_points': completed_points,
                'total_estimated_hours': total_estimated,
                'total_actual_hours': total_actual,
                'planned_hours': sprint.planned_hours,
                'completed_hours': sprint.completed_hours,
                'remaining_hours': remaining_hours,
                'completion_rate': round(completion_rate, 2),
                'velocity': sprint.velocity or 0.0,
                'team_capacity': sprint.team_capacity,
                'burndown_data': sprint.burndown_data or {}
            }

        except SQLAlchemyError as e:
            logger.error(f"獲取Sprint統計失敗: {e}")
            return {}

    async def add_retrospective_note(
        self,
        sprint_id: str,
        note: str,
        improvement: Optional[str] = None
    ) -> Optional[Sprint]:
        """
        添加Sprint回顧記錄

        Args:
            sprint_id: Sprint ID
            note: 回顧記錄
            improvement: 改進建議

        Returns:
            更新後的Sprint對象
        """
        try:
            sprint = await self.get_by_id(sprint_id)
            if not sprint:
                return None

            # 更新回顧記錄
            timestamp = datetime.utcnow().isoformat()
            if sprint.retrospective_notes:
                sprint.retrospective_notes += f"\n\n[{timestamp}] {note}"
            else:
                sprint.retrospective_notes = f"[{timestamp}] {note}"

            # 添加改進建議
            if improvement:
                sprint.improvements.append(improvement)

            sprint.updated_at = datetime.utcnow()

            self.db.commit()

            # 清除緩存
            if self.cache_manager:
                await self.cache_manager.delete(f"sprint:{sprint_id}")

            return sprint

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"添加回顧記錄失敗 (ID: {sprint_id}): {e}")
            return None

    # ==================== 私有方法 ====================

    def _apply_filters(self, query, filters: Dict[str, Any]):
        """應用過濾條件"""
        # 狀態過濾
        if 'status' in filters and filters['status']:
            query = query.filter(Sprint.status == filters['status'])

        # 活躍Sprint過濾
        if filters.get('active_only', False):
            today = date.today()
            query = query.filter(
                and_(
                    Sprint.status == SprintStatus.ACTIVE,
                    Sprint.start_date <= today,
                    Sprint.end_date >= today
                )
            )

        # 日期範圍過濾
        if 'date_range' in filters:
            date_range = filters['date_range']
            if isinstance(date_range, dict):
                if 'start_date' in date_range:
                    query = query.filter(Sprint.start_date >= date_range['start_date'])
                if 'end_date' in date_range:
                    query = query.filter(Sprint.end_date <= date_range['end_date'])

        return query

    async def _generate_sprint_id(self, start_date: date) -> str:
        """生成新的Sprint ID"""
        try:
            # 格式: SPRINT-YYYY-MM
            sprint_id = f"SPRINT-{start_date.strftime('%Y-%m')}"

            # 檢查是否已存在，如果存在則添加序號
            existing = self.db.query(Sprint).filter(Sprint.id == sprint_id).first()

            if existing:
                # 添加序號
                counter = 1
                while True:
                    new_id = f"{sprint_id}-{counter}"
                    if not self.db.query(Sprint).filter(Sprint.id == new_id).first():
                        return new_id
                    counter += 1

            return sprint_id

        except SQLAlchemyError as e:
            logger.error(f"生成Sprint ID失敗: {e}")
            # 返回時間戳作為備用
            return f"SPRINT-{datetime.utcnow().strftime('%Y-%m-%d')}"

    def _sprint_to_dict(self, sprint: Sprint) -> Dict[str, Any]:
        """轉換Sprint為字典"""
        result = {}
        for column in sprint.__table__.columns:
            value = getattr(sprint, column.name)
            if isinstance(value, (datetime, date)):
                value = value.isoformat() if value else None
            elif isinstance(value, list):
                value = value or []
            elif isinstance(value, dict):
                value = value or {}
            result[column.name] = value
        return result
