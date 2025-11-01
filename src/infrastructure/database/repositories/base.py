#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库仓储基类
"""

from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger("codex.database.repository")

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseRepository(Generic[ModelType], ABC):
    """
    数据库仓储基类
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    @abstractmethod
    def to_domain(self, model_instance: ModelType) -> Any:
        """
        将数据库模型转换为领域模型
        """
        pass

    @abstractmethod
    def to_model(self, domain_instance: Any) -> ModelType:
        """
        将领域模型转换为数据库模型
        """
        pass

    async def get_by_id(self, id: int) -> Optional[Any]:
        """
        通过ID获取领域实体
        """
        try:
            result = await self.session.get(self.model, id)
            if result:
                return self.to_domain(result)
            return None
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model.__name__} by id {id}: {e}")
            return None

    async def get_by_uuid(self, uuid: str) -> Optional[Any]:
        """
        通过UUID获取领域实体
        """
        try:
            query = select(self.model).where(self.model.uuid == uuid)
            result = await self.session.execute(query)
            instance = result.scalar_one_or_none()
            if instance:
                return self.to_domain(instance)
            return None
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model.__name__} by uuid {uuid}: {e}")
            return None

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[Any]:
        """
        获取所有领域实体
        """
        try:
            query = select(self.model).limit(limit).offset(offset)
            result = await self.session.execute(query)
            instances = result.scalars().all()
            return [self.to_domain(instance) for instance in instances]
        except SQLAlchemyError as e:
            logger.error(f"Error getting all {self.model.__name__}: {e}")
            return []

    async def create(self, domain_instance: Any) -> Optional[Any]:
        """
        创建领域实体
        """
        try:
            model_instance = self.to_model(domain_instance)
            self.session.add(model_instance)
            await self.session.flush()
            await self.session.refresh(model_instance)
            return self.to_domain(model_instance)
        except SQLAlchemyError as e:
            logger.error(f"Error creating {self.model.__name__}: {e}")
            await self.session.rollback()
            return None

    async def update(self, id: int, update_data: Dict[str, Any]) -> Optional[Any]:
        """
        更新领域实体
        """
        try:
            query = update(self.model).where(self.model.id == id).values(**update_data)
            await self.session.execute(query)
            await self.session.flush()

            # 获取更新后的实例
            result = await self.session.get(self.model, id)
            if result:
                return self.to_domain(result)
            return None
        except SQLAlchemyError as e:
            logger.error(f"Error updating {self.model.__name__} with id {id}: {e}")
            await self.session.rollback()
            return None

    async def delete(self, id: int) -> bool:
        """
        删除领域实体
        """
        try:
            query = delete(self.model).where(self.model.id == id)
            result = await self.session.execute(query)
            await self.session.flush()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            logger.error(f"Error deleting {self.model.__name__} with id {id}: {e}")
            await self.session.rollback()
            return False

    async def exists_by_id(self, id: int) -> bool:
        """
        检查领域实体是否存在
        """
        try:
            query = select(func.count()).select_from(self.model).where(self.model.id == id)
            result = await self.session.execute(query)
            return result.scalar() > 0
        except SQLAlchemyError as e:
            logger.error(f"Error checking existence of {self.model.__name__} with id {id}: {e}")
            return False

    async def exists_by_uuid(self, uuid: str) -> bool:
        """
        检查领域实体是否存在（通过UUID）
        """
        try:
            query = select(func.count()).select_from(self.model).where(self.model.uuid == uuid)
            result = await self.session.execute(query)
            return result.scalar() > 0
        except SQLAlchemyError as e:
            logger.error(f"Error checking existence of {self.model.__name__} with uuid {uuid}: {e}")
            return False

    async def count(self) -> int:
        """
        统计实体总数
        """
        try:
            query = select(func.count()).select_from(self.model)
            result = await self.session.execute(query)
            return result.scalar()
        except SQLAlchemyError as e:
            logger.error(f"Error counting {self.model.__name__}: {e}")
            return 0

    async def find_by_criteria(
        self,
        criteria: Dict[str, Any],
        limit: int = 100,
        offset: int = 0
    ) -> List[Any]:
        """
        根据条件查找实体
        """
        try:
            query = select(self.model)
            for field, value in criteria.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)

            query = query.limit(limit).offset(offset)
            result = await self.session.execute(query)
            instances = result.scalars().all()
            return [self.to_domain(instance) for instance in instances]
        except SQLAlchemyError as e:
            logger.error(f"Error finding {self.model.__name__} by criteria: {e}")
            return []
