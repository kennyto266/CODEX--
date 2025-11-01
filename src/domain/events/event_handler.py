#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件处理器
"""

from abc import ABC, abstractmethod
from typing import Type, Any
from .domain_event import DomainEvent


class EventHandler(ABC):
    """事件处理器抽象基类"""

    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        """处理事件"""
        pass

    @classmethod
    @property
    def subscribed_to(self) -> Type[DomainEvent]:
        """获取订阅的事件类型"""
        raise NotImplementedError("子类必须实现 subscribed_to 属性")