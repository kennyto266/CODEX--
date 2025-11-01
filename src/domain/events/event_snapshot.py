#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件快照 (Event Snapshot)
存储聚合状态的快照，用于优化事件重放
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict


@dataclass
class EventSnapshot:
    """事件快照"""
    aggregate_id: str
    version: int
    timestamp: datetime
    data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'aggregate_id': self.aggregate_id,
            'version': self.version,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EventSnapshot':
        """从字典创建快照"""
        return cls(
            aggregate_id=data['aggregate_id'],
            version=data['version'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            data=data['data']
        )