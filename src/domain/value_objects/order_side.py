#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订单方向枚举
"""

from enum import Enum


class OrderSide(Enum):
    """订单方向"""
    BUY = "buy"   # 买入
    SELL = "sell" # 卖出