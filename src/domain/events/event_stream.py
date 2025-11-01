#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件流 (Event Stream)
表示一个聚合的事件序列
"""

from typing import List, Optional
from dataclasses import dataclass

from .domain_event import DomainEvent
from .event_snapshot import EventSnapshot


@dataclass
class EventStream:
    """事件流"""
    aggregate_id: str
    events: List[DomainEvent]
    snapshot: Optional[EventSnapshot] = None

    @property
    def version(self) -> int:
        """获取事件流版本"""
        return len(self.events)

    @property
    def is_empty(self) -> bool:
        """检查是否为空"""
        return len(self.events) == 0

    def get_events_after(self, version: int) -> List[DomainEvent]:
        """获取指定版本之后的事件"""
        return self.events[version:]

    def append_event(self, event: DomainEvent):
        """添加事件"""
        self.events.append(event)