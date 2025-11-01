#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件存储 (Event Store)
事件溯源系统的核心组件，存储和检索事件流
"""

import json
import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Type, TypeVar
from dataclasses import asdict
from abc import ABC, abstractmethod

from .domain_event import DomainEvent
from .event_stream import EventStream
from .event_snapshot import EventSnapshot

T = TypeVar('T')


class EventStore(ABC):
    """事件存储抽象基类"""

    @abstractmethod
    async def save_events(self, aggregate_id: str, events: List[DomainEvent],
                         expected_version: int) -> int:
        """保存事件流"""
        pass

    @abstractmethod
    async def get_events(self, aggregate_id: str, from_version: int = 0,
                        to_version: Optional[int] = None) -> List[DomainEvent]:
        """获取事件流"""
        pass

    @abstractmethod
    async def get_all_events(self, from_date: Optional[datetime] = None) -> List[DomainEvent]:
        """获取所有事件"""
        pass

    @abstractmethod
    async def save_snapshot(self, snapshot: EventSnapshot) -> None:
        """保存快照"""
        pass

    @abstractmethod
    async def get_snapshot(self, aggregate_id: str,
                          max_version: Optional[int] = None) -> Optional[EventSnapshot]:
        """获取快照"""
        pass


class InMemoryEventStore(EventStore):
    """内存事件存储实现（用于测试和演示）"""

    def __init__(self):
        """初始化事件存储"""
        self._events: Dict[str, List[DomainEvent]] = {}  # aggregate_id -> events
        self._snapshots: Dict[str, EventSnapshot] = {}  # aggregate_id -> snapshot
        self._global_events: List[DomainEvent] = []
        self._event_registry: Dict[str, Type[DomainEvent]] = {}

    def register_event_type(self, event_type: Type[DomainEvent]):
        """注册事件类型"""
        self._event_registry[event_type.__name__] = event_type

    async def save_events(self, aggregate_id: str, events: List[DomainEvent],
                         expected_version: int) -> int:
        """保存事件流"""
        # 获取现有事件
        existing_events = self._events.get(aggregate_id, [])

        # 检查版本
        if len(existing_events) != expected_version:
            raise ConcurrencyException(
                f"版本冲突: 期望版本 {expected_version}, 实际版本 {len(existing_events)}"
            )

        # 保存事件
        for event in events:
            event.global_sequence = len(self._global_events)
            existing_events.append(event)
            self._global_events.append(event)

        self._events[aggregate_id] = existing_events

        return len(existing_events)

    async def get_events(self, aggregate_id: str, from_version: int = 0,
                        to_version: Optional[int] = None) -> List[DomainEvent]:
        """获取事件流"""
        events = self._events.get(aggregate_id, [])

        # 应用版本过滤
        if from_version > 0:
            events = events[from_version:]

        if to_version:
            events = events[:to_version - from_version]

        return events.copy()

    async def get_all_events(self, from_date: Optional[datetime] = None) -> List[DomainEvent]:
        """获取所有事件"""
        if from_date:
            return [event for event in self._global_events
                   if event.timestamp >= from_date]
        return self._global_events.copy()

    async def save_snapshot(self, snapshot: EventSnapshot) -> None:
        """保存快照"""
        self._snapshots[snapshot.aggregate_id] = snapshot

    async def get_snapshot(self, aggregate_id: str,
                          max_version: Optional[int] = None) -> Optional[EventSnapshot]:
        """获取快照"""
        snapshot = self._snapshots.get(aggregate_id)

        if snapshot and (max_version is None or snapshot.version <= max_version):
            return snapshot

        return None

    async def get_aggregate_events(self, aggregate_id: str) -> EventStream:
        """获取聚合的事件流"""
        events = await self.get_events(aggregate_id)
        snapshot = await self.get_snapshot(aggregate_id)

        return EventStream(
            aggregate_id=aggregate_id,
            events=events,
            snapshot=snapshot
        )

    def get_statistics(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        return {
            'total_aggregates': len(self._events),
            'total_events': len(self._global_events),
            'total_snapshots': len(self._snapshots),
            'event_types': list(self._event_registry.keys())
        }


class FileEventStore(EventStore):
    """文件事件存储实现"""

    def __init__(self, storage_dir: str = "data/events"):
        """初始化事件存储"""
        self.storage_dir = storage_dir
        self.events_file = os.path.join(storage_dir, "events.jsonl")
        self.snapshots_dir = os.path.join(storage_dir, "snapshots")

        # 确保目录存在
        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs(self.snapshots_dir, exist_ok=True)

        self._event_registry: Dict[str, Type[DomainEvent]] = {}

    def register_event_type(self, event_type: Type[DomainEvent]):
        """注册事件类型"""
        self._event_registry[event_type.__name__] = event_type

    async def save_events(self, aggregate_id: str, events: List[DomainEvent],
                         expected_version: int) -> int:
        """保存事件流"""
        # 读取现有事件以检查版本
        existing_events = await self._read_aggregate_events(aggregate_id)

        if len(existing_events) != expected_version:
            raise ConcurrencyException(
                f"版本冲突: 期望版本 {expected_version}, 实际版本 {len(existing_events)}"
            )

        # 追加事件到文件
        async with open(self.events_file, 'a', encoding='utf-8') as f:
            for event in events:
                event_data = {
                    'aggregate_id': aggregate_id,
                    'event_id': event.event_id,
                    'event_type': event.__class__.__name__,
                    'timestamp': event.timestamp.isoformat(),
                    'version': len(existing_events) + 1,
                    'data': event.to_dict()
                }

                f.write(json.dumps(event_data, ensure_ascii=False) + '\n')
                existing_events.append(event)

        return len(existing_events)

    async def get_events(self, aggregate_id: str, from_version: int = 0,
                        to_version: Optional[int] = None) -> List[DomainEvent]:
        """获取事件流"""
        return await self._read_aggregate_events(aggregate_id, from_version, to_version)

    async def get_all_events(self, from_date: Optional[datetime] = None) -> List[DomainEvent]:
        """获取所有事件"""
        events = []

        if not os.path.exists(self.events_file):
            return events

        async with open(self.events_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    event_data = json.loads(line)

                    # 应用日期过滤
                    if from_date:
                        event_time = datetime.fromisoformat(event_data['timestamp'])
                        if event_time < from_date:
                            continue

                    # 创建事件实例
                    event_type = self._event_registry.get(event_data['event_type'])
                    if event_type:
                        # 这里需要根据事件类型创建实例
                        # 简化处理，假设所有事件都有相同的构造函数
                        pass

                except Exception as e:
                    print(f"读取事件失败: {e}")

        return events

    async def save_snapshot(self, snapshot: EventSnapshot) -> None:
        """保存快照"""
        snapshot_file = os.path.join(self.snapshots_dir, f"{snapshot.aggregate_id}.json")

        snapshot_data = {
            'aggregate_id': snapshot.aggregate_id,
            'version': snapshot.version,
            'timestamp': snapshot.timestamp.isoformat(),
            'data': snapshot.data
        }

        async with open(snapshot_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot_data, f, ensure_ascii=False, indent=2)

    async def get_snapshot(self, aggregate_id: str,
                          max_version: Optional[int] = None) -> Optional[EventSnapshot]:
        """获取快照"""
        snapshot_file = os.path.join(self.snapshots_dir, f"{aggregate_id}.json")

        if not os.path.exists(snapshot_file):
            return None

        try:
            with open(snapshot_file, 'r', encoding='utf-8') as f:
                snapshot_data = json.load(f)

            if max_version and snapshot_data['version'] > max_version:
                return None

            return EventSnapshot(
                aggregate_id=snapshot_data['aggregate_id'],
                version=snapshot_data['version'],
                timestamp=datetime.fromisoformat(snapshot_data['timestamp']),
                data=snapshot_data['data']
            )
        except Exception as e:
            print(f"读取快照失败: {e}")
            return None

    async def _read_aggregate_events(self, aggregate_id: str, from_version: int = 0,
                                   to_version: Optional[int] = None) -> List[DomainEvent]:
        """读取聚合事件"""
        events = []

        if not os.path.exists(self.events_file):
            return events

        async with open(self.events_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    event_data = json.loads(line)

                    if event_data['aggregate_id'] != aggregate_id:
                        continue

                    version = event_data['version']
                    if version < from_version:
                        continue

                    if to_version and version >= to_version:
                        break

                    # 创建事件实例
                    event_type = self._event_registry.get(event_data['event_type'])
                    if event_type:
                        # 这里需要根据事件类型创建实例
                        # 简化处理
                        pass

                except Exception as e:
                    print(f"读取事件失败: {e}")

        return events


class ConcurrencyException(Exception):
    """并发异常"""
    pass