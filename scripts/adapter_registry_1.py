"""
數據適配器註冊模塊
Sprint 1 - US-003

自動註冊所有可用的數據適配器。
"""

import logging

logger = logging.getLogger(__name__)

# 導入適配器工廠
from .adapter_factory import AdapterFactory, AdapterRegistry

# 導入所有適配器
try:
    from .hkma_adapter import HKMAdapter
    # 註冊 HKMA 適配器
    AdapterFactory.register("hkma", HKMAdapter)
    logger.info("註冊 HKMA 適配器成功")
except ImportError as e:
    logger.warning(f"無法導入 HKMA 適配器: {e}")

# 註冊 GDP 適配器
try:
    from .gdp_adapter import GDPAdapter
    # 註冊 GDP 適配器
    AdapterFactory.register("gdp", GDPAdapter)
    logger.info("註冊 GDP 適配器成功")
except ImportError as e:
    logger.warning(f"無法導入 GDP 適配器: {e}")

# 註冊零售銷售適配器
try:
    from .retail_adapter import RetailAdapter
    # 註冊零售銷售適配器
    AdapterFactory.register("retail", RetailAdapter)
    logger.info("註冊零售銷售適配器成功")
except ImportError as e:
    logger.warning(f"無法導入零售銷售適配器: {e}")

# 註冊房地產適配器
try:
    from .property_adapter import PropertyAdapter
    # 註冊房地產適配器
    AdapterFactory.register("property", PropertyAdapter)
    logger.info("註冊房地產適配器成功")
except ImportError as e:
    logger.warning(f"無法導入房地產適配器: {e}")

# 註冊訪客適配器
try:
    from .visitor_adapter import VisitorAdapter
    # 註冊訪客適配器
    AdapterFactory.register("visitor", VisitorAdapter)
    logger.info("註冊訪客適配器成功")
except ImportError as e:
    logger.warning(f"無法導入訪客適配器: {e}")

# 註冊貿易適配器
try:
    from .trade_adapter import TradeAdapter
    # 註冊貿易適配器
    AdapterFactory.register("trade", TradeAdapter)
    logger.info("註冊貿易適配器成功")
except ImportError as e:
    logger.warning(f"無法導入貿易適配器: {e}")

# 註冊失業率適配器
try:
    from .unemployment_adapter import UnemploymentAdapter
    # 註冊失業率適配器
    AdapterFactory.register("unemployment", UnemploymentAdapter)
    logger.info("註冊失業率適配器成功")
except ImportError as e:
    logger.warning(f"無法導入失業率適配器: {e}")

# 註冊交通適配器
try:
    from .traffic_adapter import TrafficAdapter
    # 註冊交通適配器
    AdapterFactory.register("traffic", TrafficAdapter)
    logger.info("註冊交通適配器成功")
except ImportError as e:
    logger.warning(f"無法導入交通適配器: {e}")

# 其他適配器可以在这里添加註冊
# 例如：
# try:
#     from .yahoo_finance_adapter import YahooFinanceAdapter
#     AdapterFactory.register("yahoo", YahooFinanceAdapter)
# except ImportError:
#     pass

# 獲取所有已註冊的適配器類型
def get_available_adapters():
    """獲取所有可用的適配器"""
    return AdapterFactory.get_adapter_types()


# 導出便捷函數
__all__ = [
    'get_available_adapters',
    'AdapterRegistry',
    'AdapterFactory'
]
