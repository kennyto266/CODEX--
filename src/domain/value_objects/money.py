#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
金额值对象
"""

from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class Money:
    """金额值对象"""
    value: Decimal
    currency: str

    def __post_init__(self):
        """验证金额有效性"""
        if not isinstance(self.currency, str) or not self.currency:
            raise ValueError("货币代码不能为空")
        if self.value < 0:
            raise ValueError("金额不能为负数")

    @classmethod
    def from_float(cls, amount: float, currency: str = 'HKD', precision: int = 2) -> 'Money':
        """从浮点数创建金额"""
        decimal_value = Decimal(str(amount)).quantize(
            Decimal('0.' + '0' * (precision - 1) + '1') if precision > 0 else Decimal('1'),
            rounding=ROUND_HALF_UP
        )
        return cls(decimal_value, currency)

    @classmethod
    def from_string(cls, amount: str, currency: str = 'HKD') -> 'Money':
        """从字符串创建金额"""
        try:
            decimal_value = Decimal(amount).quantize(
                Decimal('0.01'),
                rounding=ROUND_HALF_UP
            )
            return cls(decimal_value, currency)
        except (ValueError, TypeError) as e:
            raise ValueError(f"无效的金额格式: {amount}") from e

    def convert_to(self, exchange_rate: Union[float, Decimal], target_currency: str) -> 'Money':
        """货币转换"""
        if not isinstance(exchange_rate, Decimal):
            exchange_rate = Decimal(str(exchange_rate))

        if exchange_rate <= 0:
            raise ValueError("汇率必须大于零")

        converted_value = self.value * exchange_rate
        return Money(converted_value, target_currency)

    def add(self, other: 'Money') -> 'Money':
        """金额相加"""
        if self.currency != other.currency:
            raise ValueError(f"货币不匹配: {self.currency} vs {other.currency}")
        return Money(self.value + other.value, self.currency)

    def subtract(self, other: 'Money') -> 'Money':
        """金额相减"""
        if self.currency != other.currency:
            raise ValueError(f"货币不匹配: {self.currency} vs {other.currency}")
        result = self.value - other.value
        if result < 0:
            raise ValueError("结果不能为负数")
        return Money(result, self.currency)

    def multiply(self, factor: Union[int, float]) -> 'Money':
        """金额乘以因子"""
        if not isinstance(factor, Decimal):
            factor = Decimal(str(factor))
        return Money(self.value * factor, self.currency)

    def divide(self, divisor: Union[int, float]) -> 'Money':
        """金额除以因子"""
        if divisor == 0:
            raise ValueError("除数不能为零")
        if not isinstance(divisor, Decimal):
            divisor = Decimal(str(divisor))
        return Money(self.value / divisor, self.currency)

    def __lt__(self, other: 'Money') -> bool:
        if self.currency != other.currency:
            raise ValueError(f"货币不匹配: {self.currency} vs {other.currency}")
        return self.value < other.value

    def __le__(self, other: 'Money') -> bool:
        if self.currency != other.currency:
            raise ValueError(f"货币不匹配: {self.currency} vs {other.currency}")
        return self.value <= other.value

    def __gt__(self, other: 'Money') -> bool:
        if self.currency != other.currency:
            raise ValueError(f"货币不匹配: {self.currency} vs {other.currency}")
        return self.value > other.value

    def __ge__(self, other: 'Money') -> bool:
        if self.currency != other.currency:
            raise ValueError(f"货币不匹配: {self.currency} vs {other.currency}")
        return self.value >= other.value

    def __eq__(self, other: 'Money') -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.value == other.value and self.currency == other.currency

    def __repr__(self) -> str:
        return f"Money({self.value} {self.currency})"