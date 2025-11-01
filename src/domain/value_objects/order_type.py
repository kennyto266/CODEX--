#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订单类型枚举
"""

from enum import Enum


class OrderType(Enum):
    """订单类型"""
    MARKET = "market"  # 市价单
    LIMIT = "limit"   # 限价单
    STOP = "stop"     # 止损单
    STOP_LIMIT = "stop_limit"  # 止损限价单