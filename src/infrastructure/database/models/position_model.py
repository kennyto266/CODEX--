#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持仓数据库模型
"""

from sqlalchemy import (
    Column, String, Numeric, Integer, Enum, DateTime, Text,
    Index, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from decimal import Decimal
from datetime import datetime
from ..models.base import BaseModel


class PositionModel(BaseModel):
    """
    持仓数据库模型
    """

    __tablename__ = "positions"

    # 持仓UUID（业务唯一标识）
    position_uuid = Column(
        String(36),
        unique=True,
        index=True,
        nullable=False,
        default=lambda: str(uuid.uuid4())
    )

    # 基本信息
    symbol = Column(String(20), nullable=False, index=True, comment="股票代码")
    portfolio_name = Column(String(100), nullable=False, index=True, comment="投资组合名称")
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, comment="投资组合ID")

    # 持仓数量和方向
    quantity = Column(Integer, nullable=False, comment="持仓数量")
    available_quantity = Column(Integer, nullable=False, comment="可用持仓数量")
    side = Column(Enum("long", "short", name="position_side"), nullable=False, comment="持仓方向")

    # 成本信息
    average_cost = Column(Numeric(18, 6), nullable=False, comment="平均成本")
    total_cost = Column(Numeric(18, 6), nullable=False, comment="总成本")

    # 当前价值
    current_price = Column(Numeric(18, 6), comment="当前价格")
    current_value = Column(Numeric(18, 6), comment="当前价值")
    unrealized_pnl = Column(Numeric(18, 6), default=0, comment="未实现盈亏")
    unrealized_pnl_percentage = Column(Numeric(10, 4), default=0, comment="未实现盈亏比例(%)")

    # 已实现盈亏
    realized_pnl = Column(Numeric(18, 6), default=0, comment="已实现盈亏")

    # 风险指标
    position_value_percentage = Column(Numeric(10, 4), default=0, comment="持仓价值占比(%)")
    var_95 = Column(Numeric(18, 6), default=0, comment="95% VaR")
    beta = Column(Numeric(10, 6), default=0, comment="Beta系数")

    # 时间信息
    opened_at = Column(DateTime, nullable=False, default=func.now(), comment="开仓时间")
    last_updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="最后更新时间")

    # 状态
    is_active = Column(Boolean, default=True, index=True, comment="是否活跃")
    is_frozen = Column(Boolean, default=False, comment="是否冻结")

    # 附加信息
    notes = Column(Text, comment="备注")
    tags = Column(String(500), comment="标签")

    # 关联关系
    portfolio = relationship("PortfolioModel", back_populates="positions")

    def __repr__(self) -> str:
        return (
            f"<PositionModel(id={self.id}, uuid={self.position_uuid[:8]}..., "
            f"symbol={self.symbol}, portfolio={self.portfolio_name}, "
            f"quantity={self.quantity}, side={self.side})>"
        )

    @property
    def net_position(self) -> int:
        """获取净持仓数量（正数为多头，负数为空头）"""
        return self.quantity if self.side == "long" else -self.quantity

    @property
    def is_long_position(self) -> bool:
        """检查是否为多头持仓"""
        return self.side == "long"

    @property
    def is_short_position(self) -> bool:
        """检查是否为空头持仓"""
        return self.side == "short"


# 创建索引优化查询性能
Index("idx_positions_portfolio_symbol", PositionModel.portfolio_id, PositionModel.symbol)
Index("idx_positions_symbol_active", PositionModel.symbol, PositionModel.is_active)
Index("idx_positions_portfolio_active", PositionModel.portfolio_name, PositionModel.is_active)
