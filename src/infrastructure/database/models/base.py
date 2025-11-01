#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库基础模型
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, Integer
from datetime import datetime
import uuid

Base = declarative_base()


class BaseModel(Base):
    """
    所有数据库模型的抽象基类
    """

    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class UUIDMixin:
    """
    提供UUID支持混入类
    """

    uuid = Column(
        # 使用CHAR存储UUID以便跨数据库兼容
        # 在PostgreSQL中可以使用UUID类型
        # 在SQLite中需要使用CHAR(36)
        # 这里使用CHAR(36)以确保兼容性
    )
