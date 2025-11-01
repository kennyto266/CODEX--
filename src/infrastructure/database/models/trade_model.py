#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易数据库模型
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


class TradeModel(BaseModel):
    """
    交易数据库模型
    """

    __tablename__ = "trades"

    # 交易UUID（业务唯一标识）
    trade_uuid = Column(
        String(36),
        unique=True,
        index=True,
        nullable=False,
        default=lambda: str(uuid.uuid4())
    )

    # 基本交易信息
    symbol = Column(String(20), nullable=False, index=True, comment="股票代码")
    side = Column(Enum("buy", "sell", name="trade_side"), nullable=False, comment="买卖方向")

    # 交易数量和价格
    quantity = Column(Integer, nullable=False, comment="交易数量")
    price = Column(Numeric(18, 6), nullable=False, comment="成交价格")
    total_amount = Column(Numeric(18, 6), nullable=False, comment="总金额")

    # 费用
    commission = Column(Numeric(18, 6), default=0, comment="手续费")
    stamp_duty = Column(Numeric(18, 6), default=0, comment="印花税")
    total_fees = Column(Numeric(18, 6), default=0, comment="总费用")

    # 时间信息
    trade_time = Column(DateTime, nullable=False, default=func.now(), index=True, comment="成交时间")
    settlement_date = Column(DateTime, comment="结算日期")

    # 状态
    status = Column(
        Enum("pending", "confirmed", "cancelled", name="trade_status"),
        nullable=False,
        default="confirmed",
        index=True,
        comment="交易状态"
    )

    # 关联信息
    portfolio_name = Column(String(100), index=True, comment="投资组合名称")
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), comment="投资组合ID")

    # 订单关联
    order_id = Column(Integer, ForeignKey("orders.id"), comment="订单ID")
    exchange_trade_id = Column(String(50), index=True, comment="交易所成交ID")
    client_trade_id = Column(String(50), index=True, comment="客户端成交ID")

    # 市场信息
    market = Column(String(10), default="HKEX", comment="交易市场")
    currency = Column(String(3), default="HKD", comment="交易货币")

    # 备注
    notes = Column(Text, comment="交易备注")

    # 关联关系
    order = relationship("OrderModel", back_populates="trades")
    portfolio = relationship("PortfolioModel", back_populates="trades")

    def __repr__(self) -> str:
        return (
            f"<TradeModel(id={self.id}, uuid={self.trade_uuid[:8]}..., "
            f"symbol={self.symbol}, side={self.side}, "
            f"quantity={self.quantity}, price={self.price})>"
        )

    @property
    def net_amount(self) -> Decimal:
        """获取净成交金额（扣除费用）"""
        return self.total_amount - self.total_fees


# 创建索引优化查询性能
Index("idx_trades_symbol_time", TradeModel.symbol, TradeModel.trade_time.desc())
Index("idx_trades_portfolio_time", TradeModel.portfolio_name, TradeModel.trade_time.desc())
Index("idx_trades_order_id", TradeModel.order_id)
Index("idx_trades_exchange_id", TradeModel.exchange_trade_id)
