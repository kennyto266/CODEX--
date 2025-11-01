#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略数据库模型
"""

from sqlalchemy import (
    Column, String, Numeric, Integer, Enum, DateTime, Text,
    Index, Boolean, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from decimal import Decimal
from datetime import datetime
from ..models.base import BaseModel


class StrategyModel(BaseModel):
    """
    策略数据库模型
    """

    __tablename__ = "strategies"

    # 策略UUID（业务唯一标识）
    strategy_uuid = Column(
        String(36),
        unique=True,
        index=True,
        nullable=False,
        default=lambda: str(uuid.uuid4())
    )

    # 基本信息
    name = Column(String(100), nullable=False, index=True, comment="策略名称")
    description = Column(Text, comment="策略描述")
    strategy_type = Column(String(50), nullable=False, index=True, comment="策略类型")

    # 策略参数（JSON格式存储）
    parameters = Column(JSON, comment="策略参数")
    parameter_schema = Column(JSON, comment="参数模式定义")

    # 状态
    is_active = Column(Boolean, default=True, index=True, comment="是否启用")
    is_paper_trading = Column(Boolean, default=True, comment="是否纸面交易")
    is_live_trading = Column(Boolean, default=False, comment="是否实盘交易")

    # 绩效指标
    total_return = Column(Numeric(18, 6), default=0, comment="总收益率")
    total_return_percentage = Column(Numeric(10, 4), default=0, comment="总收益率(%)")
    annualized_return = Column(Numeric(10, 4), default=0, comment="年化收益率(%)")
    volatility = Column(Numeric(10, 4), default=0, comment="波动率(%)")
    sharpe_ratio = Column(Numeric(10, 4), default=0, comment="夏普比率")
    max_drawdown = Column(Numeric(10, 4), default=0, comment="最大回撤(%)")
    win_rate = Column(Numeric(10, 4), default=0, comment="胜率(%)")

    # 交易统计
    total_trades = Column(Integer, default=0, comment="总交易次数")
    winning_trades = Column(Integer, default=0, comment="盈利交易次数")
    losing_trades = Column(Integer, default=0, comment="亏损交易次数")
    average_win = Column(Numeric(18, 6), default=0, comment="平均盈利")
    average_loss = Column(Numeric(18, 6), default=0, comment="平均亏损")

    # 时间信息
    backtest_start_date = Column(DateTime, comment="回测开始日期")
    backtest_end_date = Column(DateTime, comment="回测结束日期")
    last_trade_at = Column(DateTime, comment="最后交易时间")
    last_calculated_at = Column(DateTime, comment="最后计算时间")

    # 策略配置
    risk_level = Column(
        Enum("low", "medium", "high", name="risk_level"),
        default="medium",
        comment="风险等级"
    )
    target_markets = Column(String(200), comment="目标市场")
    target_symbols = Column(String(500), comment="目标股票")

    # 备注
    notes = Column(Text, comment="备注")
    tags = Column(String(500), comment="标签")

    def __repr__(self) -> str:
        return (
            f"<StrategyModel(id={self.id}, uuid={self.strategy_uuid[:8]}..., "
            f"name={self.name}, type={self.strategy_type}, "
            f"return={self.total_return_percentage}%)>"
        )

    @property
    def profit_factor(self) -> float:
        """计算盈利因子"""
        if self.average_loss <= 0:
            return 0.0
        return float(self.average_win / abs(self.average_loss))

    @property
    def expected_value(self) -> float:
        """计算期望值"""
        if self.total_trades <= 0:
            return 0.0
        return (self.win_rate / 100 * float(self.average_win) +
                (1 - self.win_rate / 100) * float(self.average_loss))


# 创建索引优化查询性能
Index("idx_strategies_type_active", StrategyModel.strategy_type, StrategyModel.is_active)
Index("idx_strategies_return_desc", StrategyModel.total_return_percentage.desc())
Index("idx_strategies_sharpe_desc", StrategyModel.sharpe_ratio.desc())
Index("idx_strategies_trades_desc", StrategyModel.total_trades.desc())
