#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订单ID值对象
"""

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class OrderId:
    """订单ID值对象"""
    value: str

    def __post_init__(self):
        """验证订单ID格式"""
        if not self.value:
            raise ValueError("订单ID不能为空")
        if len(self.value) > 50:
            raise ValueError("订单ID长度不能超过50个字符")

    @classmethod
    def generate(cls) -> 'OrderId':
        """生成新的订单ID"""
        return cls(str(uuid.uuid4()))

    @classmethod
    def from_string(cls, order_id: str) -> 'OrderId':
        """从字符串创建订单ID"""
        return cls(order_id)

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"OrderId('{self.value}')"