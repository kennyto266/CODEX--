#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订单数据库模型
"""

from sqlalchemy import (
    Column, String, Numeric, Integer, Enum, DateTime, Text,
    Index, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from decimal import Decimal
from datetime import datetime
from ..models.base import BaseModel


class OrderModel(BaseModel):
    """
    订单数据库模型
    """

    __tablename__ = "orders"

    # 订单UUID（业务唯一标识）
    order_uuid = Column(
        String(36),
        unique=True,
        index=True,
        nullable=False,
        default=lambda: str(uuid.uuid4())
    )

    # 基本订单信息
    symbol = Column(String(20), nullable=False, index=True, comment="股票代码")
    side = Column(Enum("buy", "sell", name="order_side"), nullable=False, comment="买卖方向")
    order_type = Column(
        Enum("market", "limit", "stop", "stop_limit", name="order_type"),
        nullable=False,
        comment="订单类型"
    )

    # 数量和价格
    quantity = Column(Integer, nullable=False, comment="数量")
    price = Column(Numeric(18, 6), comment="价格")
    stop_price = Column(Numeric(18, 6), comment="止损价格")

    # 状态管理
    status = Column(
        Enum(
            "created", "submitted", "pending", "filled", "partial",
            "cancelled", "rejected", "expired", name="order_status"
        ),
        nullable=False,
        default="created",
        index=True,
        comment="订单状态"
    )

    # 执行信息
    filled_quantity = Column(Integer, default=0, comment="已成交数量")
    filled_price = Column(Numeric(18, 6), comment="成交均价")
    average_price = Column(Numeric(18, 6), comment="平均成交价")

    # 时间信息
    submitted_at = Column(DateTime, comment="提交时间")
    filled_at = Column(DateTime, comment="成交时间")
    cancelled_at = Column(DateTime, comment="取消时间")
    expires_at = Column(DateTime, comment="过期时间")

    # 费用
    commission = Column(Numeric(18, 6), default=0, comment="手续费")
    tax = Column(Numeric(18, 6), default=0, comment="税费")

    # 附加信息
    client_order_id = Column(String(50), unique=True, index=True, comment="客户端订单ID")
    exchange_order_id = Column(String(50), index=True, comment="交易所订单ID")
    parent_order_id = Column(String(36), comment="父订单ID（用于拆单）")
    portfolio_name = Column(String(100), index=True, comment="投资组合名称")

    # 备注
    notes = Column(Text, comment="订单备注")

    # 关联关系
    trades = relationship("TradeModel", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return (
            f"<OrderModel(id={self.id}, uuid={self.order_uuid[:8]}..., "
            f"symbol={self.symbol}, side={self.side}, status={self.status})>"
        )

    @property
    def remaining_quantity(self) -> int:
        """获取剩余数量"""
        return self.quantity - self.filled_quantity

    @property
    def is_filled(self) -> bool:
        """检查是否完全成交"""
        return self.filled_quantity >= self.quantity

    @property
    def is_active(self) -> bool:
        """检查订单是否活跃"""
        return self.status in ["created", "submitted", "pending", "partial"]


# 创建索引优化查询性能
Index("idx_orders_symbol_status", OrderModel.symbol, OrderModel.status)
Index("idx_orders_portfolio_status", OrderModel.portfolio_name, OrderModel.status)
Index("idx_orders_submitted_at", OrderModel.submitted_at)
Index("idx_orders_filled_at", OrderModel.filled_at)
