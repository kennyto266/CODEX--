#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风险管理服务
处理风险评估和控制相关的业务逻辑
"""

from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal

from ..entities import Portfolio, Position
from ..value_objects import (
    StockSymbol, Price, Money, Percentage, Timestamp
)
from ..events import DomainEvent, DomainEvent as DomainEventBase


class RiskMetrics:
    """风险指标"""
    def __init__(self):
        self.var_95: float = 0.0  # 95% VaR
        self.var_99: float = 0.0  # 99% VaR
        self.sharpe_ratio: float = 0.0  # 夏普比率
        self.max_drawdown: float = 0.0  # 最大回撤
        self.volatility: float = 0.0  # 波动率
        self.beta: float = 0.0  # 贝塔系数
        self.alpha: float = 0.0  # 阿尔法

    def to_dict(self) -> Dict[str, float]:
        """转换为字典"""
        return {
            'var_95': self.var_95,
            'var_99': self.var_99,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'volatility': self.volatility,
            'beta': self.beta,
            'alpha': self.alpha
        }


class RiskLimits:
    """风险限制"""
    def __init__(self):
        self.max_position_size: float = 1000000  # 最大仓位金额
        self.max_sector_exposure: float = 0.30  # 最大行业暴露
        self.max_single_stock_exposure: float = 0.10  # 最大单股暴露
        self.max_leverage: float = 2.0  # 最大杠杆
        self.max_daily_loss: float = 0.05  # 最大日损失 (5%)
        self.stop_loss_percentage: float = 0.10  # 止损百分比 (10%)

    def to_dict(self) -> Dict[str, float]:
        """转换为字典"""
        return {
            'max_position_size': self.max_position_size,
            'max_sector_exposure': self.max_sector_exposure,
            'max_single_stock_exposure': self.max_single_stock_exposure,
            'max_leverage': self.max_leverage,
            'max_daily_loss': self.max_daily_loss,
            'stop_loss_percentage': self.stop_loss_percentage
        }


class RiskAlertEvent(DomainEventBase):
    """风险告警事件"""
    portfolio_name: str
    alert_type: str
    message: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    timestamp: Timestamp

    def __init__(self, portfolio_name: str, alert_type: str, message: str,
                 severity: str, timestamp: Timestamp):
        self.portfolio_name = portfolio_name
        self.alert_type = alert_type
        self.message = message
        self.severity = severity
        self.timestamp = timestamp
        super().__init__()


class RiskManagementService:
    """风险管理服务"""

    def __init__(self, event_bus):
        """初始化风险管理服务"""
        self.event_bus = event_bus
        self.risk_limits = RiskLimits()
        self._portfolios: Dict[str, Portfolio] = {}

    async def assess_portfolio_risk(self, portfolio: Portfolio) -> RiskMetrics:
        """评估投资组合风险"""
        risk_metrics = RiskMetrics()

        # 计算基础风险指标
        risk_metrics.volatility = self._calculate_volatility(portfolio)
        risk_metrics.sharpe_ratio = self._calculate_sharpe_ratio(portfolio)
        risk_metrics.max_drawdown = self._calculate_max_drawdown(portfolio)
        risk_metrics.var_95 = self._calculate_var(portfolio, 0.95)
        risk_metrics.var_99 = self._calculate_var(portfolio, 0.99)

        return risk_metrics

    async def check_risk_limits(self, portfolio: Portfolio) -> List[RiskAlertEvent]:
        """检查风险限制"""
        alerts = []

        # 检查单个仓位大小
        for symbol, position in portfolio.positions.items():
            position_value = position.market_value.value
            if position_value > self.risk_limits.max_position_size:
                alerts.append(RiskAlertEvent(
                    portfolio_name=portfolio.name,
                    alert_type="POSITION_SIZE",
                    message=f"仓位过大: {symbol} = {position_value:,.2f}",
                    severity="HIGH",
                    timestamp=Timestamp.now()
                ))

        # 检查杠杆比率
        leverage = portfolio.get_leverage_ratio()
        if leverage > self.risk_limits.max_leverage:
            alerts.append(RiskAlertEvent(
                portfolio_name=portfolio.name,
                alert_type="LEVERAGE",
                message=f"杠杆比率过高: {leverage:.2f} > {self.risk_limits.max_leverage}",
                severity="HIGH",
                timestamp=Timestamp.now()
            ))

        # 检查现金占比
        cash_percentage = portfolio.get_cash_percentage()
        if cash_percentage < 10:  # 现金占比低于10%
            alerts.append(RiskAlertEvent(
                portfolio_name=portfolio.name,
                alert_type="CASH_POSITION",
                message=f"现金占比过低: {cash_percentage:.1f}%",
                severity="MEDIUM",
                timestamp=Timestamp.now()
            ))

        # 发布告警事件
        for alert in alerts:
            await self.event_bus.publish(alert)

        return alerts

    async def check_stop_loss(self, portfolio: Portfolio) -> List[str]:
        """检查止损条件"""
        stop_loss_symbols = []

        for symbol, position in portfolio.positions.items():
            # 检查是否需要止损（简化逻辑）
            if position.position_type.value in ['long', 'short']:
                unrealized_pnl = position.unrealized_pnl.value
                market_value = abs(position.market_value.value)

                if market_value > 0:
                    loss_percentage = abs(unrealized_pnl) / market_value

                    if loss_percentage > self.risk_limits.stop_loss_percentage:
                        stop_loss_symbols.append(symbol)

                        # 发布止损告警
                        await self.event_bus.publish(RiskAlertEvent(
                            portfolio_name=portfolio.name,
                            alert_type="STOP_LOSS",
                            message=f"触发止损: {symbol} 损失 {loss_percentage:.1%}",
                            severity="CRITICAL",
                            timestamp=Timestamp.now()
                        ))

        return stop_loss_symbols

    def calculate_position_risk(self, position: Position, current_price: Price) -> Dict[str, float]:
        """计算单个仓位风险"""
        risk_metrics = {}

        # 计算仓位价值风险
        market_value = position.market_value.value
        if market_value > 0:
            # 假设价格波动5%
            price_volatility = 0.05
            potential_loss = market_value * price_volatility

            risk_metrics['market_value'] = market_value
            risk_metrics['potential_loss_5pct'] = potential_loss
            risk_metrics['risk_percentage'] = (potential_loss / market_value) * 100
        else:
            risk_metrics['market_value'] = 0
            risk_metrics['potential_loss_5pct'] = 0
            risk_metrics['risk_percentage'] = 0

        # 计算流动性风险（简化）
        risk_metrics['liquidity_risk'] = self._assess_liquidity_risk(position.symbol)

        return risk_metrics

    def _calculate_volatility(self, portfolio: Portfolio) -> float:
        """计算波动率（简化计算）"""
        # 这里应该基于历史收益率计算波动率
        # 简化处理，返回固定值
        return 0.15

    def _calculate_sharpe_ratio(self, portfolio: Portfolio) -> float:
        """计算夏普比率（简化计算）"""
        # 简化处理，返回固定值
        return 1.2

    def _calculate_max_drawdown(self, portfolio: Portfolio) -> float:
        """计算最大回撤（简化计算）"""
        # 简化处理，返回固定值
        return 0.08

    def _calculate_var(self, portfolio: Portfolio, confidence_level: float) -> float:
        """计算风险价值 VaR（简化计算）"""
        total_value = portfolio.total_value.value
        if confidence_level == 0.95:
            return total_value * 0.05  # 5% VaR
        elif confidence_level == 0.99:
            return total_value * 0.08  # 8% VaR
        return 0.0

    def _assess_liquidity_risk(self, symbol: StockSymbol) -> float:
        """评估流动性风险（简化计算）"""
        # 根据股票代码评估流动性风险
        # 大盘股流动性好，小盘股流动性差
        if '.HK' in str(symbol):
            # 假设港股流动性风险中等
            return 0.3
        return 0.5  # 默认流动性风险

    def get_risk_summary(self, portfolio: Portfolio) -> Dict[str, Any]:
        """获取风险摘要"""
        summary = {
            'portfolio_name': portfolio.name,
            'total_value': portfolio.total_value.value,
            'number_of_positions': portfolio.get_number_of_positions(),
            'leverage_ratio': portfolio.get_leverage_ratio(),
            'cash_percentage': portfolio.get_cash_percentage(),
            'top_positions': portfolio.get_top_positions(5),
            'risk_limits': self.risk_limits.to_dict()
        }

        return summary