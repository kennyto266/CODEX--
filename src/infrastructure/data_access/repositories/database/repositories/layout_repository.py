"""
Layout Repository
布局配置数据访问层
提供CRUD操作和业务逻辑
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from sqlalchemy.exc import SQLAlchemyError

from src.database.models.layout import LayoutConfigModel, LayoutComponentModel
from src.database.repository import IDataRepository

import structlog

logger = structlog.get_logger("database.layout_repository")


class LayoutRepository:
    """布局配置数据仓库"""

    def __init__(self, db_session: Session):
        """
        初始化数据仓库

        Args:
            db_session: 数据库会话
        """
        self.db = db_session

    def get_all(
        self,
        user_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_default: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> List[LayoutConfigModel]:
        """
        获取所有布局配置

        Args:
            user_id: 用户ID过滤
            is_active: 是否激活
            is_default: 是否默认
            skip: 跳过数量
            limit: 限制数量
            sort_by: 排序字段
            sort_order: 排序方向 (asc/desc)

        Returns:
            布局配置列表
        """
        try:
            query = self.db.query(LayoutConfigModel)

            # 应用过滤条件
            if user_id:
                query = query.filter(LayoutConfigModel.user_id == user_id)
            if is_active is not None:
                query = query.filter(LayoutConfigModel.is_active == is_active)
            if is_default is not None:
                query = query.filter(LayoutConfigModel.is_default == is_default)

            # 应用排序
            if sort_order.lower() == "desc":
                query = query.order_by(desc(getattr(LayoutConfigModel, sort_by)))
            else:
                query = query.order_by(asc(getattr(LayoutConfigModel, sort_by)))

            # 应用分页
            results = query.offset(skip).limit(limit).all()

            logger.info(
                "获取布局列表成功",
                count=len(results),
                filters={"user_id": user_id, "is_active": is_active, "is_default": is_default},
            )

            return results

        except SQLAlchemyError as e:
            logger.error("获取布局列表失败", error=str(e))
            raise

    def get_by_id(self, layout_id: str) -> Optional[LayoutConfigModel]:
        """
        根据ID获取布局配置

        Args:
            layout_id: 布局ID

        Returns:
            布局配置或None
        """
        try:
            # 尝试将字符串转换为UUID
            try:
                id_uuid = uuid.UUID(layout_id)
            except ValueError:
                logger.warning("无效的布局ID格式", layout_id=layout_id)
                return None

            layout = self.db.query(LayoutConfigModel).filter(
                LayoutConfigModel.id == id_uuid
            ).first()

            if layout:
                logger.info("获取布局成功", layout_id=layout_id)
            else:
                logger.info("布局不存在", layout_id=layout_id)

            return layout

        except SQLAlchemyError as e:
            logger.error("获取布局失败", error=str(e), layout_id=layout_id)
            raise

    def create(
        self,
        name: str,
        description: Optional[str] = None,
        components: Optional[List[Dict[str, Any]]] = None,
        theme: Optional[Dict[str, Any]] = None,
        version: str = "1.0.0",
        user_id: Optional[str] = None,
        is_default: bool = False,
    ) -> LayoutConfigModel:
        """
        创建新布局配置

        Args:
            name: 布局名称
            description: 布局描述
            components: 组件列表
            theme: 主题配置
            version: 版本号
            user_id: 用户ID
            is_default: 是否默认

        Returns:
            创建的布局配置
        """
        try:
            # 如果是默认布局，先取消其他默认布局
            if is_default:
                self.db.query(LayoutConfigModel).filter(
                    and_(
                        LayoutConfigModel.user_id == user_id,
                        LayoutConfigModel.is_default == True,
                    )
                ).update({"is_default": False})

            layout = LayoutConfigModel(
                name=name,
                description=description,
                components=components or [],
                theme=theme or {},
                version=version,
                user_id=user_id,
                is_default=is_default,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            self.db.add(layout)
            self.db.commit()
            self.db.refresh(layout)

            logger.info(
                "创建布局成功",
                layout_id=str(layout.id),
                name=name,
                user_id=user_id,
            )

            return layout

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("创建布局失败", error=str(e))
            raise

    def update(
        self,
        layout_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        components: Optional[List[Dict[str, Any]]] = None,
        theme: Optional[Dict[str, Any]] = None,
        version: Optional[str] = None,
        is_default: Optional[bool] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[LayoutConfigModel]:
        """
        更新布局配置

        Args:
            layout_id: 布局ID
            name: 布局名称
            description: 布局描述
            components: 组件列表
            theme: 主题配置
            version: 版本号
            is_default: 是否默认
            is_active: 是否激活

        Returns:
            更新后的布局配置或None
        """
        try:
            # 尝试将字符串转换为UUID
            try:
                id_uuid = uuid.UUID(layout_id)
            except ValueError:
                logger.warning("无效的布局ID格式", layout_id=layout_id)
                return None

            layout = self.db.query(LayoutConfigModel).filter(
                LayoutConfigModel.id == id_uuid
            ).first()

            if not layout:
                logger.info("布局不存在，无法更新", layout_id=layout_id)
                return None

            # 如果设置为默认，先取消其他默认布局
            if is_default and not layout.is_default:
                self.db.query(LayoutConfigModel).filter(
                    and_(
                        LayoutConfigModel.user_id == layout.user_id,
                        LayoutConfigModel.is_default == True,
                        LayoutConfigModel.id != id_uuid,
                    )
                ).update({"is_default": False})

            # 更新字段
            if name is not None:
                layout.name = name
            if description is not None:
                layout.description = description
            if components is not None:
                layout.components = components
            if theme is not None:
                layout.theme = theme
            if version is not None:
                layout.version = version
            if is_default is not None:
                layout.is_default = is_default
            if is_active is not None:
                layout.is_active = is_active

            layout.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(layout)

            logger.info("更新布局成功", layout_id=layout_id)

            return layout

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("更新布局失败", error=str(e), layout_id=layout_id)
            raise

    def delete(self, layout_id: str) -> bool:
        """
        删除布局配置（软删除）

        Args:
            layout_id: 布局ID

        Returns:
            是否删除成功
        """
        try:
            # 尝试将字符串转换为UUID
            try:
                id_uuid = uuid.UUID(layout_id)
            except ValueError:
                logger.warning("无效的布局ID格式", layout_id=layout_id)
                return False

            layout = self.db.query(LayoutConfigModel).filter(
                LayoutConfigModel.id == id_uuid
            ).first()

            if not layout:
                logger.info("布局不存在，无法删除", layout_id=layout_id)
                return False

            # 不能删除默认布局
            if layout.is_default:
                raise ValueError("不能删除默认布局")

            # 软删除 - 设置为非激活状态
            layout.is_active = False
            layout.updated_at = datetime.utcnow()

            self.db.commit()

            logger.info("删除布局成功", layout_id=layout_id)

            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("删除布局失败", error=str(e), layout_id=layout_id)
            raise

    def hard_delete(self, layout_id: str) -> bool:
        """
        硬删除布局配置（物理删除）

        Args:
            layout_id: 布局ID

        Returns:
            是否删除成功
        """
        try:
            # 尝试将字符串转换为UUID
            try:
                id_uuid = uuid.UUID(layout_id)
            except ValueError:
                logger.warning("无效的布局ID格式", layout_id=layout_id)
                return False

            layout = self.db.query(LayoutConfigModel).filter(
                LayoutConfigModel.id == id_uuid
            ).first()

            if not layout:
                logger.info("布局不存在，无法删除", layout_id=layout_id)
                return False

            # 不能删除默认布局
            if layout.is_default:
                raise ValueError("不能删除默认布局")

            # 硬删除
            self.db.delete(layout)
            self.db.commit()

            logger.info("硬删除布局成功", layout_id=layout_id)

            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("硬删除布局失败", error=str(e), layout_id=layout_id)
            raise

    def apply_layout(self, layout_id: str) -> bool:
        """
        应用布局配置（增加使用次数）

        Args:
            layout_id: 布局ID

        Returns:
            是否应用成功
        """
        try:
            # 尝试将字符串转换为UUID
            try:
                id_uuid = uuid.UUID(layout_id)
            except ValueError:
                logger.warning("无效的布局ID格式", layout_id=layout_id)
                return False

            layout = self.db.query(LayoutConfigModel).filter(
                LayoutConfigModel.id == id_uuid
            ).first()

            if not layout:
                logger.info("布局不存在，无法应用", layout_id=layout_id)
                return False

            # 增加使用次数
            layout.usage_count += 1
            layout.updated_at = datetime.utcnow()

            self.db.commit()

            logger.info("应用布局成功", layout_id=layout_id, usage_count=layout.usage_count)

            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("应用布局失败", error=str(e), layout_id=layout_id)
            raise

    def get_components(self, layout_id: str) -> List[LayoutComponentModel]:
        """
        获取布局的组件列表

        Args:
            layout_id: 布局ID

        Returns:
            组件列表
        """
        try:
            # 尝试将字符串转换为UUID
            try:
                id_uuid = uuid.UUID(layout_id)
            except ValueError:
                logger.warning("无效的布局ID格式", layout_id=layout_id)
                return []

            components = self.db.query(LayoutComponentModel).filter(
                LayoutComponentModel.layout_id == id_uuid
            ).all()

            logger.info("获取组件列表成功", layout_id=layout_id, count=len(components))

            return components

        except SQLAlchemyError as e:
            logger.error("获取组件列表失败", error=str(e), layout_id=layout_id)
            raise

    def create_default_layouts(self, user_id: Optional[str] = None) -> List[LayoutConfigModel]:
        """
        创建默认布局

        Args:
            user_id: 用户ID

        Returns:
            创建的默认布局列表
        """
        default_layouts = [
            {
                "name": "默认仪表板",
                "description": "标准仪表板布局，包含价格图表、技术指标、投资组合等",
                "is_default": True,
            },
            {
                "name": "交易布局",
                "description": "专注于交易操作的布局，包含订单面板和实时行情",
                "is_default": False,
            },
            {
                "name": "分析布局",
                "description": "专注于数据分析的布局，包含多图表和分析工具",
                "is_default": False,
            },
        ]

        created_layouts = []
        for layout_data in default_layouts:
            layout = self.create(
                name=layout_data["name"],
                description=layout_data["description"],
                user_id=user_id,
                is_default=layout_data["is_default"],
            )
            created_layouts.append(layout)

        logger.info(
            "创建默认布局成功",
            count=len(created_layouts),
            user_id=user_id,
        )

        return created_layouts
