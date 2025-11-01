#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
价格值对象
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Union
from dataclasses import dataclass


@dataclass(frozen=True)
class Price:
    """价格值对象"""
    value: Decimal

    def __post_init__(self):
        """验证价格有效性"""
        if self.value < 0:
            raise ValueError("价格不能为负数")

    @classmethod
    def from_float(cls, price: float, precision: int = 2) -> 'Price':
        """从浮点数创建价格"""
        decimal_value = Decimal(str(price)).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )
        return cls(decimal_value)

    @classmethod
    def from_string(cls, price: str) -> 'Price':
        """从字符串创建价格"""
        try:
            decimal_value = Decimal(price).quantize(
                Decimal('0.01'),
                rounding=ROUND_HALF_UP
            )
            return cls(decimal_value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"无效的价格格式: {price}") from e

    def round(self, precision: int = 2) -> Decimal:
        """四舍五入到指定精度"""
        quantizer = Decimal('0.' + '0' * (precision - 1) + '1') if precision > 0 else Decimal('1')
        return self.value.quantize(quantizer, rounding=ROUND_HALF_UP)

    def to_float(self) -> float:
        """转换为浮点数"""
        return float(self.value)

    def to_string(self, precision: int = 2) -> str:
        """转换为字符串"""
        return str(self.round(precision))

    def __lt__(self, other: 'Price') -> bool:
        if not isinstance(other, Price):
            return NotImplemented
        return self.value < other.value

    def __le__(self, other: 'Price') -> bool:
        if not isinstance(other, Price):
            return NotImplemented
        return self.value <= other.value

    def __gt__(self, other: 'Price') -> bool:
        if not isinstance(other, Price):
            return NotImplemented
        return self.value > other.value

    def __ge__(self, other: 'Price') -> bool:
        if not isinstance(other, Price):
            return NotImplemented
        return self.value >= other.value

    def __eq__(self, other: 'Price') -> bool:
        if not isinstance(other, Price):
            return NotImplemented
        return self.value == other.value

    def __add__(self, other: 'Price') -> 'Price':
        if not isinstance(other, Price):
            return NotImplemented
        return Price(self.value + other.value)

    def __sub__(self, other: 'Price') -> 'Price':
        if not isinstance(other, Price):
            return NotImplemented
        return Price(self.value - other.value)

    def __mul__(self, other: Union[int, float, 'Price']) -> 'Price':
        if isinstance(other, Price):
            return Price(self.value * other.value)
        return Price(self.value * Decimal(str(other)))

    def __truediv__(self, other: Union[int, float, 'Price']) -> 'Price':
        if isinstance(other, Price):
            if other.value == 0:
                raise ValueError("除数不能为零")
            return Price(self.value / other.value)
        if other == 0:
            raise ValueError("除数不能为零")
        return Price(self.value / Decimal(str(other)))

    def __repr__(self) -> str:
        return f"Price({self.value})"