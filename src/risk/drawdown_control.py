"""
回撤控制系统

实现动态止损、跟踪止损、回撤预警、仓位削减、风险恢复等回撤控制机制
支持多层回撤保护和动态调整策略
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, validator
import warnings


class DrawdownSeverity(str, Enum):
    """回撤严重程度"""
    NORMAL = "normal"  # 正常
    MILD = "mild"  # 轻度
    MODERATE = "moderate"  # 中度
    SEVERE = "severe"  # 严重
    CRITICAL = "critical"  # 危险


class DrawdownThreshold(BaseModel):
    """回撤阈值"""
    severity: DrawdownSeverity = Field(..., description="严重程度")
    threshold: float = Field(..., description="回撤阈值")
    position_reduction: float = Field(..., description="仓位削减比例")
    action_required: str = Field(..., description="所需操作")
    cooldown_days: int = Field(7, description="冷静期天数")


class StopLossConfig(BaseModel):
    """止损配置"""
    dynamic_stop_loss: bool = Field(True, description="动态止损")
    initial_stop_loss: float = Field(0.05, description="初始止损线")
    trailing_distance: float = Field(0.03, description="跟踪距离")
    volatility_adjusted: bool = Field(True, description="波动率调整")
    min_stop_loss: float = Field(0.02, description="最小止损")
    max_stop_loss: float = Field(0.15, description="最大止损")


class PositionReductionRule(BaseModel):
    """仓位削减规则"""
    drawdown_level: float = Field(..., description="回撤水平")
    position_limit: float = Field(..., description="仓位限制")
    risk_reduction: float = Field(..., description="风险削减")
    recovery_multiplier: float = Field(1.0, description="恢复乘数")


class DrawdownWarning(BaseModel):
    """回撤预警"""
    symbol: str = Field(..., description="资产代码")
    current_drawdown: float = Field(..., description="当前回撤")
    max_drawdown: float = Field(..., description="最大回撤")
    severity: DrawdownSeverity = Field(..., description="严重程度")
    warning_level: str = Field(..., description="预警等级")
    recommended_action: str = Field(..., description="建议操作")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    portfolio_impact: float = Field(..., description="组合影响")


class DrawdownControlResult(BaseModel):
    """回撤控制结果"""
    symbol: str = Field(..., description="资产代码")
    current_price: float = Field(..., description="当前价格")
    stop_loss_level: float = Field(..., description="止损线")
    trailing_stop_level: Optional[float] = Field(None, description="跟踪止损线")
    current_drawdown: float = Field(..., description="当前回撤")
    max_drawdown: float = Field(..., description="最大回撤")
    position_limit: float = Field(..., description="仓位限制")
    risk_score: float = Field(..., description="风险评分")
    action_required: Optional[str] = Field(None, description="所需操作")
    control_measures: List[str] = Field(default_factory=list, description="控制措施")
    recovery_outlook: str = Field(..., description="恢复展望")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class RiskRecoveryPlan(BaseModel):
    """风险恢复计划"""
    target_drawdown: float = Field(..., description="目标回撤水平")
    position_increase_schedule: List[float] = Field(..., description="仓位增加计划")
    risk_budget_utilization: float = Field(..., description="风险预算使用率")
    recovery_timeline: int = Field(..., description="恢复时间线")
    milestones: List[Tuple[float, str]] = Field(..., description="里程碑")
    review_frequency: int = Field(..., description="审查频率")


class DrawdownControlEngine:
    """回撤控制引擎"""

    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.drawdown_control")
        self.risk_free_rate = 0.02

        # 默认回撤阈值配置
        self.drawdown_thresholds = [
            DrawdownThreshold(
                severity=DrawdownSeverity.NORMAL,
                threshold=0.02,
                position_reduction=0.0,
                action_required="监控",
                cooldown_days=0
            ),
            DrawdownThreshold(
                severity=DrawdownSeverity.MILD,
                threshold=0.05,
                position_reduction=0.1,
                action_required="减少仓位10%",
                cooldown_days=3
            ),
            DrawdownThreshold(
                severity=DrawdownSeverity.MODERATE,
                threshold=0.10,
                position_reduction=0.25,
                action_required="减少仓位25%",
                cooldown_days=5
            ),
            DrawdownThreshold(
                severity=DrawdownSeverity.SEVERE,
                threshold=0.15,
                position_reduction=0.5,
                action_required="减少仓位50%",
                cooldown_days=10
            ),
            DrawdownThreshold(
                severity=DrawdownSeverity.CRITICAL,
                threshold=0.20,
                position_reduction=0.8,
                action_required="减少仓位80%，考虑平仓",
                cooldown_days=15
            )
        ]

    async def calculate_drawdown(
        self,
        price_series: pd.Series,
        current_price: Optional[float] = None
    ) -> Dict[str, float]:
        """计算回撤指标"""
        try:
            self.logger.info("Calculating drawdown metrics")

            if current_price is not None:
                # 使用当前价格扩展序列
                extended_series = price_series.copy()
                extended_series.loc[datetime.now()] = current_price
                price_series = extended_series

            # 计算累计峰值
            cumulative_peak = price_series.expanding().max()

            # 计算回撤
            drawdown = (price_series - cumulative_peak) / cumulative_peak

            # 指标
            current_drawdown = drawdown.iloc[-1]
            max_drawdown = drawdown.min()

            # 回撤持续时间
            in_drawdown = drawdown < 0
            if in_drawdown.any():
                # 从最近的高点开始计算
                last_peak_idx = cumulative_peak.idxmax()
                drawdown_duration = (drawdown.index[-1] - last_peak_idx).days
            else:
                drawdown_duration = 0

            # 回撤恢复时间 (简化)
            recovery_rate = abs(current_drawdown) / max(0.01, abs(max_drawdown))

            result = {
                "current_drawdown": current_drawdown,
                "max_drawdown": max_drawdown,
                "drawdown_duration_days": drawdown_duration,
                "recovery_rate": recovery_rate,
                "days_since_peak": (drawdown.index[-1] - cumulative_peak.idxmax()).days
            }

            self.logger.info(f"Drawdown calculated: current={current_drawdown:.2%}, max={max_drawdown:.2%}")
            return result

        except Exception as e:
            self.logger.error(f"Error calculating drawdown: {e}")
            raise

    async def calculate_dynamic_stop_loss(
        self,
        price_series: pd.Series,
        current_price: float,
        config: StopLossConfig
    ) -> Dict[str, float]:
        """计算动态止损线"""
        try:
            self.logger.info("Calculating dynamic stop loss levels")

            # 计算价格变动
            price_changes = price_series.pct_change().dropna()

            # 波动率
            volatility = price_changes.std()

            # ATR (简化版)
            high_low = price_series.rolling(window=14).max() - price_series.rolling(window=14).min()
            atr = high_low.mean()

            # 初始止损线 (基于ATR)
            if config.volatility_adjusted:
                # 波动率调整
                vol_multiplier = max(1.0, min(3.0, volatility / 0.02))  # 基准波动率2%
                initial_stop = config.initial_stop_loss * vol_multiplier
                initial_stop = np.clip(initial_stop, config.min_stop_loss, config.max_stop_loss)
            else:
                initial_stop = config.initial_stop_loss

            # 最高价 (用于跟踪止损)
            peak_price = price_series.expanding().max().iloc[-1]

            # 跟踪止损线
            if config.trailing_distance > 0:
                trailing_stop = peak_price * (1 - config.trailing_distance)
            else:
                trailing_stop = current_price * (1 - initial_stop)

            # 动态止损线 (取较严格者)
            dynamic_stop = max(
                current_price * (1 - initial_stop),
                trailing_stop
            )

            # 止损距离
            stop_distance = (current_price - dynamic_stop) / current_price

            return {
                "stop_loss_level": dynamic_stop,
                "trailing_stop_level": trailing_stop,
                "initial_stop_loss": current_price * (1 - initial_stop),
                "stop_distance": stop_distance,
                "peak_price": peak_price,
                "volatility_adjusted": config.volatility_adjusted
            }

        except Exception as e:
            self.logger.error(f"Error calculating dynamic stop loss: {e}")
            raise

    async def assess_drawdown_severity(
        self,
        current_drawdown: float,
        max_drawdown: float,
        portfolio_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[DrawdownSeverity, str]:
        """评估回撤严重程度"""
        try:
            # 确定当前严重程度
            severity = DrawdownSeverity.NORMAL
            action = "维持当前配置"

            for threshold in self.drawdown_thresholds:
                if abs(current_drawdown) >= threshold.threshold:
                    severity = threshold.severity
                    action = threshold.action_required

            # 考虑历史最大回撤
            if max_drawdown < -0.20 and current_drawdown > max_drawdown * 0.8:
                # 当前回撤接近历史最大，考虑升级
                if severity == DrawdownSeverity.SEVERE:
                    severity = DrawdownSeverity.CRITICAL
                    action = "立即减仓，考虑平仓"
                elif severity == DrawdownSeverity.MODERATE:
                    severity = DrawdownSeverity.SEVERE

            # 组合上下文调整
            if portfolio_context:
                # 如果组合整体回撤较小，可以适当放宽
                portfolio_dd = portfolio_context.get("portfolio_drawdown", 0)
                if portfolio_dd > current_drawdown:
                    # 个股回撤小于组合，略微放宽
                    if severity in [DrawdownSeverity.SEVERE, DrawdownSeverity.CRITICAL]:
                        severity = DrawdownSeverity.MODERATE
                        action = "减少仓位，考虑对冲"

            return severity, action

        except Exception as e:
            self.logger.error(f"Error assessing drawdown severity: {e}")
            raise

    async def calculate_position_limits(
        self,
        current_drawdown: float,
        severity: DrawdownSeverity,
        initial_position_limit: float = 0.2
    ) -> float:
        """计算仓位限制"""
        try:
            # 基础仓位限制
            position_limit = initial_position_limit

            # 根据回撤水平调整
            for threshold in self.drawdown_thresholds:
                if severity == threshold.severity:
                    # 应用削减
                    position_limit = position_limit * (1 - threshold.position_reduction)
                    break

            # 动态调整因子
            if current_drawdown < -0.15:
                # 严重回撤，进一步削减
                position_limit = position_limit * 0.5
            elif current_drawdown < -0.10:
                position_limit = position_limit * 0.7
            elif current_drawdown < -0.05:
                position_limit = position_limit * 0.85

            # 限制在合理范围内
            position_limit = np.clip(position_limit, 0.01, 0.3)

            self.logger.info(f"Position limit calculated: {position_limit:.2%}")
            return position_limit

        except Exception as e:
            self.logger.error(f"Error calculating position limits: {e}")
            raise

    async def monitor_drawdown(
        self,
        symbol: str,
        price_series: pd.Series,
        current_price: float,
        position_value: float,
        portfolio_value: float,
        config: Optional[StopLossConfig] = None
    ) -> DrawdownControlResult:
        """监控回撤并生成控制措施"""
        try:
            self.logger.info(f"Monitoring drawdown for {symbol}")

            # 计算回撤
            drawdown_metrics = await self.calculate_drawdown(price_series, current_price)
            current_drawdown = drawdown_metrics["current_drawdown"]
            max_drawdown = drawdown_metrics["max_drawdown"]

            # 评估严重程度
            severity, action = await self.assess_drawdown_severity(
                current_drawdown,
                max_drawdown
            )

            # 止损线
            if config is None:
                config = StopLossConfig()

            stop_loss_data = await self.calculate_dynamic_stop_loss(price_series, current_price, config)
            stop_loss_level = stop_loss_data["stop_loss_level"]
            trailing_stop = stop_loss_data["trailing_stop_level"]

            # 仓位限制
            position_limit = await self.calculate_position_limits(current_drawdown, severity)

            # 风险评分 (0-100)
            risk_score = min(100, abs(current_drawdown) * 500 + severity.value * 20)

            # 控制措施
            control_measures = []
            if abs(current_drawdown) > 0.05:
                control_measures.append("减少仓位")
            if current_price <= stop_loss_level:
                control_measures.append("触发止损")
            if severity in [DrawdownSeverity.SEVERE, DrawdownSeverity.CRITICAL]:
                control_measures.append("考虑对冲")
            if drawdown_metrics["drawdown_duration_days"] > 30:
                control_measures.append("长期回撤关注")

            # 恢复展望
            if abs(current_drawdown) < 0.03:
                recovery_outlook = "轻微回撤，快速恢复"
            elif abs(current_drawdown) < 0.10:
                recovery_outlook = "中等回撤，需要时间恢复"
            elif abs(current_drawdown) < 0.20:
                recovery_outlook = "深度回撤，长期恢复"
            else:
                recovery_outlook = "严重回撤，谨慎操作"

            # 组合影响
            portfolio_impact = (position_value / portfolio_value) * abs(current_drawdown)

            result = DrawdownControlResult(
                symbol=symbol,
                current_price=current_price,
                stop_loss_level=stop_loss_level,
                trailing_stop_level=trailing_stop,
                current_drawdown=current_drawdown,
                max_drawdown=max_drawdown,
                position_limit=position_limit,
                risk_score=risk_score,
                action_required=action if risk_score > 60 else None,
                control_measures=control_measures,
                recovery_outlook=recovery_outlook
            )

            return result

        except Exception as e:
            self.logger.error(f"Error monitoring drawdown: {e}")
            raise

    async def generate_drawdown_warning(
        self,
        results: List[DrawdownControlResult],
        portfolio_value: float
    ) -> List[DrawdownWarning]:
        """生成回撤预警"""
        try:
            self.logger.info("Generating drawdown warnings")

            warnings = []

            for result in results:
                # 风险评分阈值
                if result.risk_score >= 70:
                    severity = DrawdownSeverity.CRITICAL
                    warning_level = "极高风险"
                elif result.risk_score >= 50:
                    severity = DrawdownSeverity.SEVERE
                    warning_level = "高风险"
                elif result.risk_score >= 30:
                    severity = DrawdownSeverity.MODERATE
                    warning_level = "中等风险"
                else:
                    severity = DrawdownSeverity.MILD
                    warning_level = "低风险"

                # 组合影响
                portfolio_impact = (result.current_drawdown * result.position_limit) * portfolio_value / portfolio_value

                warning = DrawdownWarning(
                    symbol=result.symbol,
                    current_drawdown=result.current_drawdown,
                    max_drawdown=result.max_drawdown,
                    severity=severity,
                    warning_level=warning_level,
                    recommended_action=result.action_required or "持续监控",
                    portfolio_impact=portfolio_impact
                )

                warnings.append(warning)

            return warnings

        except Exception as e:
            self.logger.error(f"Error generating drawdown warnings: {e}")
            raise

    async def create_risk_recovery_plan(
        self,
        current_drawdown: float,
        position_limit: float,
        config: Optional[Dict[str, Any]] = None
    ) -> RiskRecoveryPlan:
        """创建风险恢复计划"""
        try:
            self.logger.info("Creating risk recovery plan")

            # 目标回撤水平 (恢复到轻微回撤)
            target_drawdown = -0.03

            # 仓位增加计划 (分阶段恢复)
            if abs(current_drawdown) > 0.15:
                # 严重回撤，分5阶段恢复
                position_schedule = [
                    position_limit * 0.5,  # 5%
                    position_limit * 0.7,  # 7%
                    position_limit * 0.85,  # 8.5%
                    position_limit * 0.95,  # 9.5%
                    position_limit  # 最终
                ]
                recovery_timeline = 60  # 60天
            elif abs(current_drawdown) > 0.10:
                # 中度回撤，分3阶段恢复
                position_schedule = [
                    position_limit * 0.7,
                    position_limit * 0.85,
                    position_limit
                ]
                recovery_timeline = 30  # 30天
            else:
                # 轻度回撤，快速恢复
                position_schedule = [
                    position_limit * 0.85,
                    position_limit
                ]
                recovery_timeline = 14  # 14天

            # 里程碑
            milestones = [
                (0.0, "回撤控制启动"),
                (0.3, "30%恢复完成"),
                (0.6, "60%恢复完成"),
                (0.9, "90%恢复完成"),
                (1.0, "完全恢复")
            ]

            # 风险预算使用率
            risk_budget_utilization = min(1.0, abs(current_drawdown) / 0.2)  # 最大回撤20%

            # 审查频率
            review_frequency = max(3, recovery_timeline // 5)  # 每几天审查一次

            plan = RiskRecoveryPlan(
                target_drawdown=target_drawdown,
                position_increase_schedule=position_schedule,
                risk_budget_utilization=risk_budget_utilization,
                recovery_timeline=recovery_timeline,
                milestones=milestones,
                review_frequency=review_frequency
            )

            return plan

        except Exception as e:
            self.logger.error(f"Error creating risk recovery plan: {e}")
            raise

    async def validate_drawdown_control(
        self,
        price_series: pd.Series,
        current_price: float,
        stop_loss_level: float
    ) -> Dict[str, Any]:
        """验证回撤控制措施"""
        try:
            # 检查是否触发止损
            stop_loss_triggered = current_price <= stop_loss_level

            # 计算回撤历史
            drawdown_series = await self.calculate_drawdown(price_series, current_price)

            # 模拟不同价格水平下的回撤
            price_levels = [current_price * (1 - 0.05 * i) for i in range(1, 6)]
            scenario_drawdowns = []

            for price in price_levels:
                scenario_dd = await self.calculate_drawdown(price_series, price)
                scenario_drawdowns.append({
                    "price": price,
                    "drawdown": scenario_dd["current_drawdown"],
                    "below_stop_loss": price <= stop_loss_level
                })

            # 有效性评估
            if stop_loss_triggered:
                effectiveness = "止损成功触发，风险得到控制"
            elif drawdown_series["current_drawdown"] > -0.05:
                effectiveness = "控制有效，回撤在可接受范围"
            else:
                effectiveness = "需要加强控制措施"

            validation_result = {
                "stop_loss_triggered": stop_loss_triggered,
                "current_drawdown": drawdown_series,
                "scenario_analysis": scenario_drawdowns,
                "control_effectiveness": effectiveness,
                "recommendation": "维持当前配置" if not stop_loss_triggered else "执行止损"
            }

            return validation_result

        except Exception as e:
            self.logger.error(f"Error validating drawdown control: {e}")
            raise

    async def generate_drawdown_report(
        self,
        results: List[DrawdownControlResult],
        portfolio_value: float
    ) -> Dict[str, Any]:
        """生成回撤控制报告"""
        try:
            # 汇总指标
            total_risk_score = sum(r.risk_score for r in results)
            avg_risk_score = total_risk_score / len(results) if results else 0

            max_drawdown = min(r.max_drawdown for r in results) if results else 0
            current_drawdown = max(r.current_drawdown for r in results) if results else 0

            # 风险集中度
            high_risk_positions = [r for r in results if r.risk_score > 60]
            risk_concentration = len(high_risk_positions) / len(results) if results else 0

            # 止损触发情况
            stop_loss_triggered = [r for r in results if r.current_price <= r.stop_loss_level]

            # 恢复展望
            recovery_outlooks = [r.recovery_outlook for r in results]
            severe_recovery = sum(1 for outlook in recovery_outlooks if "严重" in outlook or "深度" in outlook)

            # 建议
            recommendations = []
            if risk_concentration > 0.3:
                recommendations.append("高风险仓位集中，建议分散投资")
            if len(stop_loss_triggered) > 0:
                recommendations.append("多个止损被触发，建议减少仓位")
            if severe_recovery > len(results) * 0.5:
                recommendations.append("多数资产恢复前景不佳，建议重新评估策略")
            if avg_risk_score > 50:
                recommendations.append("整体风险水平较高，建议降低杠杆")
            if not recommendations:
                recommendations.append("回撤控制有效，维持当前配置")

            report = {
                "report_date": datetime.now().isoformat(),
                "portfolio_summary": {
                    "total_value": portfolio_value,
                    "positions_monitored": len(results),
                    "high_risk_positions": len(high_risk_positions),
                    "stop_loss_triggered": len(stop_loss_triggered)
                },
                "risk_metrics": {
                    "average_risk_score": avg_risk_score,
                    "max_drawdown": max_drawdown,
                    "current_drawdown": current_drawdown,
                    "risk_concentration": risk_concentration
                },
                "warnings": await self.generate_drawdown_warning(results, portfolio_value),
                "recommendations": recommendations,
                "next_review_date": (datetime.now() + timedelta(days=7)).isoformat()
            }

            return report

        except Exception as e:
            self.logger.error(f"Error generating drawdown report: {e}")
            raise
