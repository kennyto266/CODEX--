#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票数据库模型
"""

from sqlalchemy import (
    Column, String, Numeric, Integer, DateTime, Text,
    Index, Boolean, Float
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from ..models.base import BaseModel


class StockModel(BaseModel):
    """
    股票数据库模型
    """

    __tablename__ = "stocks"

    # 基本信息
    symbol = Column(String(20), unique=True, nullable=False, index=True, comment="股票代码")
    name = Column(String(100), nullable=False, comment="股票名称")
    short_name = Column(String(50), comment="股票简称")

    # 市场信息
    market = Column(String(10), nullable=False, default="HKEX", index=True, comment="交易市场")
    exchange_code = Column(String(10), comment="交易所代码")
    sector = Column(String(50), comment="行业分类")
    industry = Column(String(100), comment="细分行业")

    # 价格信息
    last_price = Column(Numeric(18, 6), comment="最新价格")
    previous_close = Column(Numeric(18, 6), comment="前收盘价")
    open_price = Column(Numeric(18, 6), comment="开盘价")
    high_price = Column(Numeric(18, 6), comment="最高价")
    low_price = Column(Numeric(18, 6), comment="最低价")
    bid_price = Column(Numeric(18, 6), comment="买价")
    ask_price = Column(Numeric(18, 6), comment="卖价")
    bid_size = Column(Integer, comment="买盘数量")
    ask_size = Column(Integer, comment="卖盘数量")

    # 成交量和成交额
    volume = Column(Integer, comment="成交量")
    turnover = Column(Numeric(18, 6), comment="成交额")

    # 价格变化
    change = Column(Numeric(18, 6), default=0, comment="价格变化")
    change_percentage = Column(Numeric(10, 4), default=0, comment="价格变化百分比")

    # 技术指标
    moving_avg_5 = Column(Numeric(18, 6), comment="5日均价")
    moving_avg_20 = Column(Numeric(18, 6), comment="20日均价")
    moving_avg_50 = Column(Numeric(18, 6), comment="50日均价")
    rsi = Column(Numeric(8, 4), comment="RSI指标")
    macd = Column(Numeric(18, 6), comment="MACD指标")

    # 基本面信息
    market_cap = Column(Numeric(18, 2), comment="市值")
    pe_ratio = Column(Numeric(10, 4), comment="市盈率")
    pb_ratio = Column(Numeric(10, 4), comment="市净率")
    dividend_yield = Column(Numeric(8, 4), comment="股息率")
    shares_outstanding = Column(Integer, comment="发行股数")

    # 时间信息
    last_trade_time = Column(DateTime, comment="最后交易时间")
    last_price_update = Column(DateTime, comment="最后价格更新时间")

    # 状态
    is_active = Column(Boolean, default=True, index=True, comment="是否活跃")
    is_trading = Column(Boolean, default=True, comment="是否可交易")
    trading_status = Column(String(20), default="active", comment="交易状态")

    # 扩展信息
    description = Column(Text, comment="股票描述")
    website = Column(String(200), comment="公司网站")
    currency = Column(String(3), default="HKD", comment="交易货币")

    # 统计数据
    avg_volume_30d = Column(Integer, comment="30日平均成交量")
    high_52w = Column(Numeric(18, 6), comment="52周最高价")
    low_52w = Column(Numeric(18, 6), comment="52周最低价")

    def __repr__(self) -> str:
        return (
            f"<StockModel(id={self.id}, symbol={self.symbol}, name={self.name}, "
            f"price={self.last_price}, change={self.change_percentage}%)>"
        )

    @property
    def is_up(self) -> bool:
        """检查是否上涨"""
        return self.change > 0

    @property
    def is_down(self) -> bool:
        """检查是否下跌"""
        return self.change < 0

    @property
    def price_change_magnitude(self) -> float:
        """获取价格变化幅度"""
        return float(abs(self.change_percentage))


# 创建索引优化查询性能
Index("idx_stocks_market_active", StockModel.market, StockModel.is_active)
Index("idx_stocks_sector", StockModel.sector)
Index("idx_stocks_price_desc", StockModel.last_price.desc())
Index("idx_stocks_change_desc", StockModel.change_percentage.desc())
Index("idx_stocks_volume_desc", StockModel.volume.desc())
