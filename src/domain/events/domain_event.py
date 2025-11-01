#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
领域事件基类
"""

import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class DomainEvent(ABC):
    """领域事件基类"""
    event_id: str = ""
    timestamp: datetime = None
    version: int = 1

    def __post_init__(self):
        """初始化后处理"""
        if not self.event_id:
            object.__setattr__(self, 'event_id', str(uuid.uuid4()))
        if not self.timestamp:
            object.__setattr__(self, 'timestamp', datetime.now())

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        pass

    @property
    def event_name(self) -> str:
        """获取事件名称"""
        return self.__class__.__name__