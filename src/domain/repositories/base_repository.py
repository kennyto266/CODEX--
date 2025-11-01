#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仓储基类
定义通用的数据访问接口
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Type, TypeVar, Generic
import asyncio

T = TypeVar('T')
ID = TypeVar('ID')


class BaseRepository(ABC, Generic[T, ID]):
    """仓储基类"""

    def __init__(self, entity_type: Type[T]):
        """初始化仓储"""
        self.entity_type = entity_type

    @abstractmethod
    async def save(self, entity: T) -> T:
        """保存实体"""
        pass

    @abstractmethod
    async def get_by_id(self, entity_id: ID) -> Optional[T]:
        """根据ID获取实体"""
        pass

    @abstractmethod
    async def get_all(self) -> List[T]:
        """获取所有实体"""
        pass

    @abstractmethod
    async def delete(self, entity_id: ID) -> bool:
        """删除实体"""
        pass

    @abstractmethod
    async def exists(self, entity_id: ID) -> bool:
        """检查实体是否存在"""
        pass

    async def save_many(self, entities: List[T]) -> List[T]:
        """批量保存实体"""
        saved_entities = []
        for entity in entities:
            saved_entity = await self.save(entity)
            saved_entities.append(saved_entity)
        return saved_entities

    async def get_many(self, entity_ids: List[ID]) -> List[T]:
        """批量获取实体"""
        entities = []
        for entity_id in entity_ids:
            entity = await self.get_by_id(entity_id)
            if entity:
                entities.append(entity)
        return entities

    async def count(self) -> int:
        """计算实体数量"""
        all_entities = await self.get_all()
        return len(all_entities)

    async def clear(self) -> None:
        """清除所有实体"""
        all_entities = await self.get_all()
        for entity in all_entities:
            # 获取实体的ID
            entity_id = getattr(entity, 'id', None) or getattr(entity, 'order_id', None)
            if entity_id:
                await self.delete(entity_id)