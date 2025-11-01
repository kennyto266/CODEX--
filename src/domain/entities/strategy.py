#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略实体
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from ..value_objects import StrategyId, StockSymbol, Timestamp, Percentage
from ..events import DomainEvent


class StrategyStatus(Enum):
    """策略状态"""
    DRAFT = "draft"           # 草稿
    ACTIVE = "active"         # 活跃
    PAUSED = "paused"         # 暂停
    STOPPED = "stopped"       # 停止
    COMPLETED = "completed"   # 完成


class SignalType(Enum):
    """信号类型"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class Strategy:
    """策略实体"""
    strategy_id: StrategyId
    name: str
    description: str
    parameters: Dict[str, Any]
    status: StrategyStatus = StrategyStatus.DRAFT
    created_at: Timestamp = field(default_factory=Timestamp.now)
    updated_at: Timestamp = field(default_factory=Timestamp.now)
    last_execution: Optional[Timestamp] = None
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    _events: List[DomainEvent] = field(default_factory=list, init=False, repr=False)

    def activate(self):
        """激活策略"""
        if self.status == StrategyStatus.DRAFT:
            self.status = StrategyStatus.ACTIVE
            self.updated_at = Timestamp.now()

            # 触发策略激活事件
            self._events.append(
                StrategyActivatedEvent(
                    strategy_id=self.strategy_id,
                    name=self.name,
                    timestamp=self.updated_at
                )
            )

    def pause(self):
        """暂停策略"""
        if self.status == StrategyStatus.ACTIVE:
            self.status = StrategyStatus.PAUSED
            self.updated_at = Timestamp.now()

            # 触发策略暂停事件
            self._events.append(
                StrategyPausedEvent(
                    strategy_id=self.strategy_id,
                    name=self.name,
                    timestamp=self.updated_at
                )
            )

    def stop(self):
        """停止策略"""
        if self.status in [StrategyStatus.ACTIVE, StrategyStatus.PAUSED]:
            self.status = StrategyStatus.STOPPED
            self.updated_at = Timestamp.now()

            # 触发策略停止事件
            self._events.append(
                StrategyStoppedEvent(
                    strategy_id=self.strategy_id,
                    name=self.name,
                    timestamp=self.updated_at
                )
            )

    def complete(self):
        """完成策略"""
        if self.status != StrategyStatus.COMPLETED:
            self.status = StrategyStatus.COMPLETED
            self.updated_at = Timestamp.now()

            # 触发策略完成事件
            self._events.append(
                StrategyCompletedEvent(
                    strategy_id=self.strategy_id,
                    name=self.name,
                    timestamp=self.updated_at
                )
            )

    def update_parameters(self, parameters: Dict[str, Any]):
        """更新策略参数"""
        old_params = self.parameters.copy()
        self.parameters = parameters
        self.updated_at = Timestamp.now()

        # 触发参数更新事件
        self._events.append(
            StrategyParametersUpdatedEvent(
                strategy_id=self.strategy_id,
                old_parameters=old_params,
                new_parameters=parameters,
                timestamp=self.updated_at
            )
        )

    def add_signal(self, symbol: StockSymbol, signal_type: SignalType, confidence: float):
        """添加交易信号"""
        self.last_execution = Timestamp.now()

        # 触发信号生成事件
        self._events.append(
            SignalGeneratedEvent(
                strategy_id=self.strategy_id,
                symbol=symbol,
                signal_type=signal_type,
                confidence=confidence,
                timestamp=self.last_execution
            )
        )

    def update_performance(self, metrics: Dict[str, float]):
        """更新性能指标"""
        self.performance_metrics.update(metrics)
        self.updated_at = Timestamp.now()

        # 触发性能更新事件
        self._events.append(
            PerformanceUpdatedEvent(
                strategy_id=self.strategy_id,
                metrics=metrics,
                timestamp=self.updated_at
            )
        )

    def is_active(self) -> bool:
        """是否处于活跃状态"""
        return self.status == StrategyStatus.ACTIVE

    def can_execute(self) -> bool:
        """是否可以执行"""
        return self.status in [StrategyStatus.ACTIVE]

    def get_parameter(self, key: str, default: Any = None) -> Any:
        """获取策略参数"""
        return self.parameters.get(key, default)

    def add_domain_event(self, event: DomainEvent):
        """添加领域事件"""
        self._events.append(event)

    def get_domain_events(self) -> List[DomainEvent]:
        """获取所有领域事件"""
        return self._events.copy()

    def clear_domain_events(self):
        """清除领域事件"""
        self._events.clear()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'strategy_id': str(self.strategy_id),
            'name': self.name,
            'description': self.description,
            'parameters': self.parameters,
            'status': self.status.value,
            'created_at': self.created_at.to_string(),
            'updated_at': self.updated_at.to_string(),
            'last_execution': self.last_execution.to_string() if self.last_execution else None,
            'performance_metrics': self.performance_metrics
        }


# 策略事件类
from ..events import DomainEvent as DomainEventBase


class StrategyActivatedEvent(DomainEventBase):
    """策略激活事件"""
    strategy_id: StrategyId
    name: str
    timestamp: Timestamp

    def __init__(self, strategy_id: StrategyId, name: str, timestamp: Timestamp):
        self.strategy_id = strategy_id
        self.name = name
        self.timestamp = timestamp
        super().__init__()


class StrategyPausedEvent(DomainEventBase):
    """策略暂停事件"""
    strategy_id: StrategyId
    name: str
    timestamp: Timestamp

    def __init__(self, strategy_id: StrategyId, name: str, timestamp: Timestamp):
        self.strategy_id = strategy_id
        self.name = name
        self.timestamp = timestamp
        super().__init__()


class StrategyStoppedEvent(DomainEventBase):
    """策略停止事件"""
    strategy_id: StrategyId
    name: str
    timestamp: Timestamp

    def __init__(self, strategy_id: StrategyId, name: str, timestamp: Timestamp):
        self.strategy_id = strategy_id
        self.name = name
        self.timestamp = timestamp
        super().__init__()


class StrategyCompletedEvent(DomainEventBase):
    """策略完成事件"""
    strategy_id: StrategyId
    name: str
    timestamp: Timestamp

    def __init__(self, strategy_id: StrategyId, name: str, timestamp: Timestamp):
        self.strategy_id = strategy_id
        self.name = name
        self.timestamp = timestamp
        super().__init__()


class StrategyParametersUpdatedEvent(DomainEventBase):
    """策略参数更新事件"""
    strategy_id: StrategyId
    old_parameters: Dict[str, Any]
    new_parameters: Dict[str, Any]
    timestamp: Timestamp

    def __init__(self, strategy_id: StrategyId, old_parameters: Dict[str, Any],
                 new_parameters: Dict[str, Any], timestamp: Timestamp):
        self.strategy_id = strategy_id
        self.old_parameters = old_parameters
        self.new_parameters = new_parameters
        self.timestamp = timestamp
        super().__init__()


class SignalGeneratedEvent(DomainEventBase):
    """信号生成事件"""
    strategy_id: StrategyId
    symbol: StockSymbol
    signal_type: SignalType
    confidence: float
    timestamp: Timestamp

    def __init__(self, strategy_id: StrategyId, symbol: StockSymbol,
                 signal_type: SignalType, confidence: float, timestamp: Timestamp):
        self.strategy_id = strategy_id
        self.symbol = symbol
        self.signal_type = signal_type
        self.confidence = confidence
        self.timestamp = timestamp
        super().__init__()


class PerformanceUpdatedEvent(DomainEventBase):
    """性能更新事件"""
    strategy_id: StrategyId
    metrics: Dict[str, float]
    timestamp: Timestamp

    def __init__(self, strategy_id: StrategyId, metrics: Dict[str, float], timestamp: Timestamp):
        self.strategy_id = strategy_id
        self.metrics = metrics
        self.timestamp = timestamp
        super().__init__()