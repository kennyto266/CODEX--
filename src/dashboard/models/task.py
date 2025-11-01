"""
任務數據模型
港股量化交易系統 - 項目管理模組
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, String, Integer, Text, DateTime, Enum, JSON, Index
from sqlalchemy.dialects.postgresql import ARRAY
from .task_status import TaskStatus, Priority


class Task:
    """
    任務數據模型

    用於港股量化交易系統的項目管理，支持：
    - 任務生命周期管理
    - 依賴關係管理
    - 狀態追蹤和流轉
    - 自動化工作流集成
    """

    # 表名
    __tablename__ = "tasks"

    # 基本信息
    id = Column(String(20), primary_key=True, comment="任務唯一ID (格式: TASK-XXX)")
    title = Column(String(200), nullable=False, comment="任務標題")
    description = Column(Text, comment="任務描述")

    # 狀態和優先級
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO, nullable=False, comment="任務狀態")
    priority = Column(Enum(Priority), default=Priority.P2, nullable=False, comment="優先級")

    # 時間管理
    estimated_hours = Column(Integer, nullable=False, comment="預估工時")
    actual_hours = Column(Integer, comment="實際工時")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="創建時間")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="最後更新時間")
    completed_at = Column(DateTime, comment="完成時間")

    # 人員管理
    assignee = Column(String(100), comment="被分配者")
    reporter = Column(String(100), nullable=False, comment="報告者/創建者")
    watchers = Column(ARRAY(String), default=list, comment="觀察者列表")

    # 關係管理
    dependencies = Column(ARRAY(String), default=list, comment="前置依賴任務ID列表")
    dependents = Column(ARRAY(String), default=list, comment="依賴此任務的任務ID列表")

    # 驗收和輸出
    acceptance_criteria = Column(ARRAY(Text), default=list, comment="驗收標準列表")
    deliverables = Column(ARRAY(String), default=list, comment="交付物列表")

    # Sprint管理
    sprint = Column(String(50), comment="所屬Sprint ID")
    story_points = Column(Integer, default=1, comment="故事點數")

    # 元數據和擴展
    metadata = Column(JSON, default=dict, comment="自動化元數據 (Git提交ID等)")

    # 索引
    __table_args__ = (
        Index('idx_tasks_status', 'status'),
        Index('idx_tasks_priority', 'priority'),
        Index('idx_tasks_assignee', 'assignee'),
        Index('idx_tasks_sprint', 'sprint'),
        Index('idx_tasks_created_at', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title={self.title}, status={self.status})>"

    @property
    def progress_percentage(self) -> float:
        """
        計算任務進度百分比

        Returns:
            float: 進度百分比 (0-100)
        """
        progress_map = {
            TaskStatus.TODO: 0,
            TaskStatus.IN_PROGRESS: 50,
            TaskStatus.REVIEW: 80,
            TaskStatus.BLOCKED: 30,
            TaskStatus.DONE: 100
        }
        return progress_map.get(self.status, 0)

    @property
    def is_blocked(self) -> bool:
        """檢查任務是否被阻塞"""
        return self.status == TaskStatus.BLOCKED

    @property
    def is_completed(self) -> bool:
        """檢查任務是否已完成"""
        return self.status == TaskStatus.DONE

    @property
    def can_start(self) -> bool:
        """
        檢查任務是否可以開始

        條件：狀態為TODO且所有依賴已完成
        """
        if self.status != TaskStatus.TODO:
            return False

        # 檢查依賴是否完成（由服務層實現，這裡僅占位）
        return True

    def add_dependency(self, task_id: str):
        """添加前置依賴"""
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)

    def remove_dependency(self, task_id: str):
        """移除前置依賴"""
        if task_id in self.dependencies:
            self.dependencies.remove(task_id)

    def add_deliverable(self, deliverable: str):
        """添加交付物"""
        if deliverable not in self.deliverables:
            self.deliverables.append(deliverable)

    def add_acceptance_criteria(self, criteria: str):
        """添加驗收標準"""
        if criteria not in self.acceptance_criteria:
            self.acceptance_criteria.append(criteria)

    def to_dict(self) -> Dict[str, Any]:
        """
        轉換為字典格式

        Returns:
            Dict: 任務數據字典
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value if self.status else None,
            "priority": self.priority.value if self.priority else None,
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "assignee": self.assignee,
            "reporter": self.reporter,
            "watchers": self.watchers or [],
            "dependencies": self.dependencies or [],
            "dependents": self.dependents or [],
            "acceptance_criteria": self.acceptance_criteria or [],
            "deliverables": self.deliverables or [],
            "sprint": self.sprint,
            "story_points": self.story_points,
            "progress_percentage": self.progress_percentage,
            "is_blocked": self.is_blocked,
            "is_completed": self.is_completed,
            "metadata": self.metadata or {}
        }
