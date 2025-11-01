"""
跨市场量化交易系统 - 数据适配器模块

这个模块提供了多市场数据获取的适配器，包括：
- FX数据适配器（汇率）
- 商品数据适配器（黄金、石油等）
- 债券数据适配器（国债收益率等）
"""

from .base_adapter import BaseAdapter
from .fx_adapter import FXAdapter
from .commodity_adapter import CommodityAdapter
from .bond_adapter import BondAdapter
from .hkex_adapter import HKEXAdapter

__all__ = [
    'BaseAdapter',
    'FXAdapter',
    'CommodityAdapter',
    'BondAdapter',
    'HKEXAdapter'
]
