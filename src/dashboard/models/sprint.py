"""
Sprint數據模型
港股量化交易系統 - 項目管理模組
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, String, Integer, Text, DateTime, Date, Enum, Float, Index, JSON
from sqlalchemy.dialects.postgresql import ARRAY
from .task_status import SprintStatus


class Sprint:
    """
    Sprint數據模型

    用於敏捷開發管理，支持：
    - Sprint生命周期管理
    - 容量計算和規劃
    - 速度和效率追蹤
    - 燃盡圖數據
    """

    # 表名
    __tablename__ = "sprints"

    # 基本信息
    id = Column(String(50), primary_key=True, comment="Sprint唯一ID (格式: SPRINT-YYYY-MM)")
    name = Column(String(100), nullable=False, comment="Sprint名稱")
    goal = Column(Text, comment="Sprint目標")

    # 時間管理
    start_date = Column(Date, nullable=False, comment="開始日期")
    end_date = Column(Date, nullable=False, comment="結束日期")
    status = Column(Enum(SprintStatus), default=SprintStatus.PLANNING, comment="Sprint狀態")

    # 任務關聯
    task_ids = Column(ARRAY(String), default=list, comment="任務ID列表")
    planned_hours = Column(Integer, default=0, comment="計劃工時")
    completed_hours = Column(Integer, default=0, comment="已完成工時")

    # 容量和速度
    team_capacity = Column(Integer, default=0, comment="團隊總容量 (工時)")
    velocity = Column(Float, comment="Sprint速度 (完成的故事點數)")
    estimated_velocity = Column(Float, comment="預估速度")

    # 指標
    completion_rate = Column(Float, comment="完成率 (百分比)")
    burndown_data = Column(JSON, comment="燃盡圖數據")

    # 審查和回顧
    retrospective_notes = Column(Text, comment="回顧會議記錄")
    improvements = Column(ARRAY(Text), default=list, comment="改進建議")

    # 時間戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="創建時間")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="最後更新時間")

    # 索引
    __table_args__ = (
        Index('idx_sprints_status', 'status'),
        Index('idx_sprints_dates', 'start_date', 'end_date'),
        Index('idx_sprints_created', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<Sprint(id={self.id}, name={self.name}, status={self.status})>"

    @property
    def duration_days(self) -> int:
        """計算Sprint持續天數"""
        return (self.end_date - self.start_date).days

    @property
    def is_active(self) -> bool:
        """檢查Sprint是否正在進行"""
        today = date.today()
        return self.status == SprintStatus.ACTIVE and self.start_date <= today <= self.end_date

    @property
    def is_completed(self) -> bool:
        """檢查Sprint是否已完成"""
        return self.status == SprintStatus.COMPLETED

    @property
    def remaining_days(self) -> int:
        """計算剩餘天數"""
        if not self.is_active:
            return 0
        today = date.today()
        return (self.end_date - today).days

    @property
    def utilization_rate(self) -> float:
        """計算團隊容量利用率"""
        if self.team_capacity == 0:
            return 0.0
        return (self.planned_hours / self.team_capacity) * 100

    @property
    def efficiency_score(self) -> float:
        """計算效率分數 (完成率 / 利用率)"""
        if self.utilization_rate == 0:
            return 0.0
        return self.completion_rate / self.utilization_rate if self.completion_rate else 0.0

    def calculate_velocity(self, completed_tasks: List[Dict]) -> float:
        """
        計算Sprint速度

        Args:
            completed_tasks: 已完成的任務列表

        Returns:
            float: 速度 (故事點數總和)
        """
        velocity = sum(task.get('story_points', 0) for task in completed_tasks)
        self.velocity = velocity
        return velocity

    def update_burndown(self, remaining_hours: float, day_offset: int):
        """
        更新燃盡圖數據

        Args:
            remaining_hours: 剩餘工時
            day_offset: 第幾天 (相對開始日期)
        """
        if self.burndown_data is None:
            self.burndown_data = {"days": [], "remaining": []}

        self.burndown_data["days"].append(day_offset)
        self.burndown_data["remaining"].append(remaining_hours)

    def add_improvement(self, improvement: str):
        """添加改進建議"""
        if improvement not in self.improvements:
            self.improvements.append(improvement)

    def to_dict(self) -> Dict[str, Any]:
        """
        轉換為字典格式

        Returns:
            Dict: Sprint數據字典
        """
        return {
            "id": self.id,
            "name": self.name,
            "goal": self.goal,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "duration_days": self.duration_days,
            "status": self.status.value if self.status else None,
            "task_ids": self.task_ids or [],
            "planned_hours": self.planned_hours,
            "completed_hours": self.completed_hours,
            "team_capacity": self.team_capacity,
            "velocity": self.velocity,
            "estimated_velocity": self.estimated_velocity,
            "completion_rate": self.completion_rate,
            "burndown_data": self.burndown_data or {},
            "retrospective_notes": self.retrospective_notes,
            "improvements": self.improvements or [],
            "remaining_days": self.remaining_days,
            "is_active": self.is_active,
            "is_completed": self.is_completed,
            "utilization_rate": round(self.utilization_rate, 2),
            "efficiency_score": round(self.efficiency_score, 2),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
