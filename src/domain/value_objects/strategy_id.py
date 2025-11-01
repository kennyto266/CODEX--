#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略ID值对象
"""

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class StrategyId:
    """策略ID值对象"""
    value: str

    def __post_init__(self):
        """验证策略ID格式"""
        if not self.value:
            raise ValueError("策略ID不能为空")
        if len(self.value) > 50:
            raise ValueError("策略ID长度不能超过50个字符")

    @classmethod
    def generate(cls) -> 'StrategyId':
        """生成新的策略ID"""
        return cls(str(uuid.uuid4()))

    @classmethod
    def from_string(cls, strategy_id: str) -> 'StrategyId':
        """从字符串创建策略ID"""
        return cls(strategy_id)

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"StrategyId('{self.value}')"