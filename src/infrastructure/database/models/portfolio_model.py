#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投资组合数据库模型
"""

from sqlalchemy import (
    Column, String, Numeric, Integer, Enum, DateTime, Text,
    Index, Boolean
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from decimal import Decimal
from datetime import datetime
from ..models.base import BaseModel


class PortfolioModel(BaseModel):
    """
    投资组合数据库模型
    """

    __tablename__ = "portfolios"

    # 投资组合UUID（业务唯一标识）
    portfolio_uuid = Column(
        String(36),
        unique=True,
        index=True,
        nullable=False,
        default=lambda: str(uuid.uuid4())
    )

    # 基本信息
    name = Column(String(100), unique=True, nullable=False, index=True, comment="投资组合名称")
    description = Column(Text, comment="投资组合描述")

    # 类型和策略
    portfolio_type = Column(
        Enum("long_only", "long_short", "market_neutral", "pairs", name="portfolio_type"),
        nullable=False,
        default="long_only",
        comment="投资组合类型"
    )

    # 资金信息
    initial_capital = Column(Numeric(18, 6), nullable=False, comment="初始资金")
    current_cash = Column(Numeric(18, 6), default=0, comment="当前现金")
    reserved_cash = Column(Numeric(18, 6), default=0, comment="预留现金")

    # 货币
    base_currency = Column(String(3), default="HKD", nullable=False, comment="基础货币")

    # 状态
    is_active = Column(Boolean, default=True, index=True, comment="是否活跃")
    is_frozen = Column(Boolean, default=False, comment="是否冻结")

    # 绩效指标
    total_value = Column(Numeric(18, 6), default=0, comment="总价值")
    total_return = Column(Numeric(18, 6), default=0, comment="总收益")
    total_return_percentage = Column(Numeric(10, 4), default=0, comment="总收益率(%)")
    day_return = Column(Numeric(18, 6), default=0, comment="日内收益")
    day_return_percentage = Column(Numeric(10, 4), default=0, comment="日内收益率(%)")

    # 风险指标
    leverage_ratio = Column(Numeric(10, 6), default=0, comment="杠杆比率")
    var_95 = Column(Numeric(18, 6), default=0, comment="95% VaR")
    var_99 = Column(Numeric(18, 6), default=0, comment="99% VaR")
    max_drawdown = Column(Numeric(10, 4), default=0, comment="最大回撤(%)")

    # 时间信息
    last_rebalance_at = Column(DateTime, comment="上次再平衡时间")
    last_calculated_at = Column(DateTime, comment="上次计算时间")

    # 附加信息
    notes = Column(Text, comment="备注")
    tags = Column(String(500), comment="标签（逗号分隔）")

    # 关联关系
    positions = relationship("PositionModel", back_populates="portfolio", cascade="all, delete-orphan")
    trades = relationship("TradeModel", back_populates="portfolio")

    def __repr__(self) -> str:
        return (
            f"<PortfolioModel(id={self.id}, uuid={self.portfolio_uuid[:8]}..., "
            f"name={self.name}, type={self.portfolio_type}, "
            f"value={self.total_value}, return={self.total_return_percentage}%)>"
        )

    @property
    def invested_amount(self) -> Decimal:
        """获取投资金额"""
        return self.total_value - self.current_cash

    @property
    def available_cash(self) -> Decimal:
        """获取可用现金"""
        return self.current_cash - self.reserved_cash

    @property
    def cash_percentage(self) -> float:
        """获取现金占比"""
        if self.total_value <= 0:
            return 0.0
        return float((self.current_cash / self.total_value) * 100)


# 创建索引优化查询性能
Index("idx_portfolios_active_type", PortfolioModel.is_active, PortfolioModel.portfolio_type)
Index("idx_portfolios_value_desc", PortfolioModel.total_value.desc())
Index("idx_portfolios_return_desc", PortfolioModel.total_return_percentage.desc())
