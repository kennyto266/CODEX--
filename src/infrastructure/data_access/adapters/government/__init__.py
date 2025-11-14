"""
政府数据适配器

包含香港政府统计数据适配器：
- HIBOR利率数据 (HKMA)
- GDP数据 (C&SD)
- 房价指数 (RVD)
- 访客数据 (Tourism Board)
- 零售数据 (Statistics)
- 贸易数据 (Trade statistics)
- 失业率 (Labor statistics)
- CPI指数 (Inflation)
"""

from .hkma_adapter import HKMARateAdapter
from .gdp_adapter import GDPAdapter
from .property_adapter import PropertyPriceAdapter
from .visitor_adapter import VisitorAdapter
from .retail_adapter import RetailAdapter
from .trade_adapter import TradeAdapter
from .unemployment_adapter import UnemploymentAdapter
from .cpi_adapter import CPIAdapter

# 导入模块以触发自动注册
from . import hkma_adapter as _hkma
from . import gdp_adapter as _gdp
from . import property_adapter as _prop
from . import visitor_adapter as _visitor
from . import retail_adapter as _retail
from . import trade_adapter as _trade
from . import unemployment_adapter as _unemp
from . import cpi_adapter as _cpi

__all__ = [
    'HKMARateAdapter',
    'GDPAdapter',
    'PropertyPriceAdapter',
    'VisitorAdapter',
    'RetailAdapter',
    'TradeAdapter',
    'UnemploymentAdapter',
    'CPIAdapter',
]
