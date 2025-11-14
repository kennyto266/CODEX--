"""
Database Base
数据库基类
提供SQLAlchemy基类和元数据
"""

from sqlalchemy.ext.declarative import declarative_base

# 创建基类
Base = declarative_base()

# 导出
__all__ = ['Base']
