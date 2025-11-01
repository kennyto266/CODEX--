#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百分比值对象
"""

from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class Percentage:
    """百分比值对象"""
    value: Decimal

    def __post_init__(self):
        """验证百分比有效性"""
        if self.value < -100 or self.value > 100:
            raise ValueError("百分比值必须在-100到100之间")

    @classmethod
    def from_float(cls, percentage: float) -> 'Percentage':
        """从浮点数创建百分比"""
        return cls(Decimal(str(percentage)))

    @classmethod
    def from_string(cls, percentage: str) -> 'Percentage':
        """从字符串创建百分比"""
        try:
            decimal_value = Decimal(percentage)
            return cls(decimal_value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"无效的百分比格式: {percentage}") from e

    @classmethod
    def from_parts(cls, numerator: Union[int, float], denominator: Union[int, float]) -> 'Percentage':
        """从分子分母创建百分比"""
        if denominator == 0:
            raise ValueError("分母不能为零")
        percentage = (numerator / denominator) * 100
        return cls(Decimal(str(percentage)))

    def to_decimal(self) -> float:
        """转换为小数（0.15表示15%）"""
        return float(self.value) / 100

    def to_fraction(self) -> float:
        """转换为百分比字符串"""
        return float(self.value)

    def multiply(self, amount: Union[int, float]) -> Union[int, float]:
        """百分比乘以数量"""
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        return float(self.to_decimal() * amount)

    def add(self, other: 'Percentage') -> 'Percentage':
        """百分比相加"""
        return Percentage(self.value + other.value)

    def subtract(self, other: 'Percentage') -> 'Percentage':
        """百分比相减"""
        return Percentage(self.value - other.value)

    def is_positive(self) -> bool:
        """是否为正数"""
        return self.value > 0

    def is_negative(self) -> bool:
        """是否为负数"""
        return self.value < 0

    def is_zero(self) -> bool:
        """是否为零"""
        return self.value == 0

    def __lt__(self, other: 'Percentage') -> bool:
        if not isinstance(other, Percentage):
            return NotImplemented
        return self.value < other.value

    def __le__(self, other: 'Percentage') -> bool:
        if not isinstance(other, Percentage):
            return NotImplemented
        return self.value <= other.value

    def __gt__(self, other: 'Percentage') -> bool:
        if not isinstance(other, Percentage):
            return NotImplemented
        return self.value > other.value

    def __ge__(self, other: 'Percentage') -> bool:
        if not isinstance(other, Percentage):
            return NotImplemented
        return self.value >= other.value

    def __eq__(self, other: 'Percentage') -> bool:
        if not isinstance(other, Percentage):
            return NotImplemented
        return self.value == other.value

    def __repr__(self) -> str:
        return f"Percentage({self.value}%)"