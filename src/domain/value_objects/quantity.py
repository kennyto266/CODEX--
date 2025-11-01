#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数量值对象
"""

from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class Quantity:
    """数量值对象"""
    value: int

    def __post_init__(self):
        """验证数量有效性"""
        if self.value <= 0:
            raise ValueError("数量必须大于零")
        if not isinstance(self.value, int):
            raise ValueError("数量必须是整数")

    @classmethod
    def from_int(cls, quantity: int) -> 'Quantity':
        """从整数创建数量"""
        return cls(quantity)

    @classmethod
    def from_float(cls, quantity: float) -> 'Quantity':
        """从浮点数创建数量"""
        if not quantity.is_integer():
            raise ValueError("数量必须是整数")
        return cls(int(quantity))

    def add(self, other: 'Quantity') -> 'Quantity':
        """数量相加"""
        return Quantity(self.value + other.value)

    def subtract(self, other: 'Quantity') -> 'Quantity':
        """数量相减"""
        result = self.value - other.value
        if result < 0:
            raise ValueError("结果不能为负数")
        return Quantity(result)

    def multiply(self, factor: Union[int, float]) -> 'Quantity':
        """数量乘以因子"""
        if isinstance(factor, float) and not factor.is_integer():
            raise ValueError("乘数必须是整数")
        return Quantity(int(self.value * factor))

    def divide(self, divisor: Union[int, float]) -> 'Quantity':
        """数量除以因子"""
        if divisor == 0:
            raise ValueError("除数不能为零")
        if isinstance(divisor, float) and not divisor.is_integer():
            raise ValueError("除数必须是整数")
        result = self.value // int(divisor)
        return Quantity(result)

    def __lt__(self, other: 'Quantity') -> bool:
        if not isinstance(other, Quantity):
            return NotImplemented
        return self.value < other.value

    def __le__(self, other: 'Quantity') -> bool:
        if not isinstance(other, Quantity):
            return NotImplemented
        return self.value <= other.value

    def __gt__(self, other: 'Quantity') -> bool:
        if not isinstance(other, Quantity):
            return NotImplemented
        return self.value > other.value

    def __ge__(self, other: 'Quantity') -> bool:
        if not isinstance(other, Quantity):
            return NotImplemented
        return self.value >= other.value

    def __eq__(self, other: 'Quantity') -> bool:
        if not isinstance(other, Quantity):
            return NotImplemented
        return self.value == other.value

    def __repr__(self) -> str:
        return f"Quantity({self.value})"