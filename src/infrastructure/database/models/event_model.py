#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件数据库模型
"""

from sqlalchemy import (
    Column, String, Text, DateTime, Integer, Enum, Boolean, JSON,
    Index, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from ..models.base import BaseModel


class EventModel(BaseModel):
    """
    事件数据库模型（用于事件溯源）
    """

    __tablename__ = "events"

    # 事件UUID（业务唯一标识）
    event_uuid = Column(
        String(36),
        unique=True,
        index=True,
        nullable=False,
        default=lambda: str(uuid.uuid4())
    )

    # 事件基本信息
    event_type = Column(String(100), nullable=False, index=True, comment="事件类型")
    aggregate_type = Column(String(50), nullable=False, index=True, comment="聚合根类型")
    aggregate_id = Column(String(36), nullable=False, index=True, comment="聚合根ID")

    # 事件内容
    event_data = Column(JSON, nullable=False, comment="事件数据")
    metadata = Column(JSON, comment="事件元数据")

    # 版本控制
    version = Column(Integer, nullable=False, comment="事件版本")
    sequence_number = Column(Integer, nullable=False, index=True, comment="序列号")

    # 时间信息
    occurred_at = Column(DateTime, nullable=False, default=func.now(), index=True, comment="发生时间")
    processed_at = Column(DateTime, comment="处理时间")

    # 处理状态
    is_processed = Column(Boolean, default=False, index=True, comment="是否已处理")
    retry_count = Column(Integer, default=0, comment="重试次数")
    max_retries = Column(Integer, default=3, comment="最大重试次数")

    # 错误信息
    error_message = Column(Text, comment="错误信息")
    error_details = Column(JSON, comment="错误详情")

    # 关联信息
    correlation_id = Column(String(36), index=True, comment="关联ID")
    causation_id = Column(String(36), index=True, comment="因果ID")

    # 事件源
    event_source = Column(String(100), comment="事件源")

    # 处理者
    processed_by = Column(String(100), comment="处理者")

    def __repr__(self) -> str:
        return (
            f"<EventModel(id={self.id}, uuid={self.event_uuid[:8]}..., "
            f"type={self.event_type}, aggregate={self.aggregate_type}:{self.aggregate_id[:8]}..., "
            f"version={self.version}, processed={self.is_processed})>"
        )

    @property
    def is_failed(self) -> bool:
        """检查事件是否处理失败"""
        return self.error_message is not None

    @property
    def can_retry(self) -> bool:
        """检查是否可以重试"""
        return not self.is_processed and self.retry_count < self.max_retries

    def mark_as_processed(self, processed_by: str = None):
        """标记事件为已处理"""
        self.is_processed = True
        self.processed_at = func.now()
        self.processed_by = processed_by

    def mark_as_failed(self, error_message: str, error_details: dict = None):
        """标记事件为处理失败"""
        self.error_message = error_message
        if error_details:
            self.error_details = error_details
        self.retry_count += 1


# 创建索引优化查询性能
Index("idx_events_aggregate_type_id", EventModel.aggregate_type, EventModel.aggregate_id)
Index("idx_events_type_occurred", EventModel.event_type, EventModel.occurred_at.desc())
Index("idx_events_processed_false", EventModel.is_processed, EventModel.occurred_at)
Index("idx_events_sequence", EventModel.sequence_number)
Index("idx_events_correlation", EventModel.correlation_id, EventModel.causation_id)
