#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
时间戳值对象
"""

import time
from datetime import datetime
from dataclasses import dataclass


@dataclass(frozen=True)
class Timestamp:
    """时间戳值对象"""
    value: datetime

    def __post_init__(self):
        """验证时间戳有效性"""
        if not isinstance(self.value, datetime):
            raise ValueError("时间戳必须是datetime对象")

    @classmethod
    def now(cls) -> 'Timestamp':
        """获取当前时间戳"""
        return cls(datetime.now())

    @classmethod
    def from_timestamp(cls, timestamp: float) -> 'Timestamp':
        """从时间戳创建"""
        return cls(datetime.fromtimestamp(timestamp))

    @classmethod
    def from_string(cls, timestamp_str: str, format_str: str = '%Y-%m-%d %H:%M:%S') -> 'Timestamp':
        """从字符串创建时间戳"""
        try:
            dt = datetime.strptime(timestamp_str, format_str)
            return cls(dt)
        except ValueError as e:
            raise ValueError(f"无效的时间戳格式: {timestamp_str}") from e

    def to_timestamp(self) -> float:
        """转换为时间戳"""
        return self.value.timestamp()

    def to_string(self, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
        """转换为字符串"""
        return self.value.strftime(format_str)

    def is_before(self, other: 'Timestamp') -> bool:
        """检查是否在另一个时间戳之前"""
        return self.value < other.value

    def is_after(self, other: 'Timestamp') -> bool:
        """检查是否在另一个时间戳之后"""
        return self.value > other.value

    def is_equal(self, other: 'Timestamp') -> bool:
        """检查是否等于另一个时间戳"""
        return self.value == other.value

    def __repr__(self) -> str:
        return f"Timestamp({self.value})"