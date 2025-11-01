"""
混合数据源适配器工厂 - 统一管理多个数据适配器

根据数据类型自动选择最合适的数据源：
- 港股 -> HKEX统一API
- FX -> Yahoo Finance (免费)
- 商品 -> Alpha Vantage (免费层500次/天)
- 债券 -> FRED API (待实现)

确保100%真实数据源覆盖
"""

from typing import Dict, Type, Optional
import logging

from .base_adapter import BaseAdapter
from .hkex_adapter_fixed import HKEXAdapterFixed as HKEXAdapter
from .fx_yahoo_adapter import FXYahooAdapter
from .alphavantage_commodity_adapter import AlphaVantageCommodityAdapter
from .fred_bond_adapter import FREDBondAdapter


class HybridAdapterFactory:
    """混合数据源适配器工厂"""

    def __init__(self):
        self.logger = logging.getLogger("cross_market_quant.HybridAdapterFactory")

        # 注册所有适配器
        self.adapters = {
            'hkex': HKEXAdapter(),
            'fx': FXYahooAdapter(),
            'commodity': AlphaVantageCommodityAdapter(),
            'bond': FREDBondAdapter(),
        }

        # 数据类型映射
        self.type_mapping = {
            # 港股
            '0700.hk': 'hkex',
            '0388.hk': 'hkex',
            '1398.hk': 'hkex',
            '0939.hk': 'hkex',
            '3988.hk': 'hkex',
            # FX
            'USD_CNH': 'fx',
            'USD_CNY': 'fx',
            'EUR_USD': 'fx',
            'GBP_USD': 'fx',
            'USD_JPY': 'fx',
            'AUD_USD': 'fx',
            'USD_CHF': 'fx',
            'USD_CAD': 'fx',
            'NZD_USD': 'fx',
            # 商品
            'GOLD': 'commodity',
            'SILVER': 'commodity',
            'OIL_WTI': 'commodity',
            'OIL_BRENT': 'commodity',
            'COPPER': 'commodity',
            'PLATINUM': 'commodity',
            'PALLADIUM': 'commodity',
            'NATURAL_GAS': 'commodity',
            'WHEAT': 'commodity',
            'CORN': 'commodity',
            # 债券
            'US_10Y': 'bond',
            'US_30Y': 'bond',
            'US_2Y': 'bond',
            'US_5Y': 'bond',
            'US_7Y': 'bond',
            'FED_FUNDS': 'bond',
            'MORTGAGE_30YR': 'bond',
        }

        self.logger.info(f"混合数据源工厂初始化完成，支持{len(self.adapters)}种数据类型")

    def get_adapter(self, symbol: str) -> BaseAdapter:
        """
        根据symbol获取对应的适配器

        Args:
            symbol: 数据符号

        Returns:
            对应的适配器实例

        Raises:
            ValueError: 当symbol不支持时
        """
        # 标准化symbol
        symbol_upper = symbol.upper()

        # 尝试精确匹配
        if symbol_upper in self.type_mapping:
            adapter_type = self.type_mapping[symbol_upper]
            adapter = self.adapters.get(adapter_type)
            if adapter:
                self.logger.info(f"使用{adapter_type}适配器获取{symbol}数据")
                return adapter

        # 尝试前缀匹配（用于港股）
        for pattern in self.type_mapping.keys():
            if symbol_upper.startswith(pattern.split('.')[0]):
                adapter_type = self.type_mapping[pattern]
                adapter = self.adapters.get(adapter_type)
                if adapter:
                    self.logger.info(f"使用{adapter_type}适配器获取{symbol}数据")
                    return adapter

        # 如果都匹配不到，尝试根据symbol特征推断
        if '_' in symbol:
            # 例如 USD_CNH, EUR_USD
            adapter = self.adapters.get('fx')
            if adapter:
                self.logger.info(f"推断{symbol}为FX数据，使用FX适配器")
                return adapter

        raise ValueError(f"不支持的数据类型: {symbol}")

    def get_adapter_by_type(self, data_type: str) -> Optional[BaseAdapter]:
        """
        根据数据类型直接获取适配器

        Args:
            data_type: 数据类型 (hkex, fx, commodity, bond)

        Returns:
            适配器实例，如果不支持则返回None
        """
        return self.adapters.get(data_type.lower())

    def get_supported_symbols(self) -> Dict[str, Dict]:
        """
        获取所有支持的symbol及其适配器类型

        Returns:
            字典: {symbol: {'type': adapter_type, 'name': symbol_name}}
        """
        result = {}

        # 港股
        hkex_adapter = self.adapters.get('hkex')
        if hkex_adapter:
            symbols = hkex_adapter.get_supported_symbols() if hasattr(hkex_adapter, 'get_supported_symbols') else {}
            for symbol in symbols:
                result[symbol] = {'type': 'hkex', 'name': symbols[symbol]}

        # FX
        fx_adapter = self.adapters.get('fx')
        if fx_adapter:
            symbols = fx_adapter.get_supported_symbols() if hasattr(fx_adapter, 'get_supported_symbols') else {}
            for symbol in symbols:
                result[symbol] = {'type': 'fx', 'name': symbols[symbol]}

        # 商品
        commodity_adapter = self.adapters.get('commodity')
        if commodity_adapter:
            symbols = commodity_adapter.get_supported_symbols() if hasattr(commodity_adapter, 'get_supported_symbols') else {}
            for symbol in symbols:
                result[symbol] = {'type': 'commodity', 'name': symbols[symbol]}

        # 债券
        bond_adapter = self.adapters.get('bond')
        if bond_adapter:
            symbols = bond_adapter.get_supported_symbols() if hasattr(bond_adapter, 'get_supported_symbols') else {}
            for symbol in symbols:
                result[symbol] = {'type': 'bond', 'name': symbols[symbol]}

        return result

    def get_data_source_summary(self) -> Dict:
        """
        获取数据源汇总信息

        Returns:
            数据源汇总字典
        """
        summary = {
            'total_adapters': len(self.adapters),
            'supported_types': list(self.adapters.keys()),
            'coverage': {},
            'total_symbols': 0
        }

        symbols = self.get_supported_symbols()
        summary['total_symbols'] = len(symbols)

        for adapter_type, adapter in self.adapters.items():
            count = len([s for s in symbols.values() if s['type'] == adapter_type])
            summary['coverage'][adapter_type] = count

        return summary

    async def fetch_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        **kwargs
    ):
        """
        统一的数据获取接口

        Args:
            symbol: 数据符号
            start_date: 开始日期
            end_date: 结束日期
            **kwargs: 额外参数

        Returns:
            获取的数据DataFrame

        Raises:
            Exception: 当获取失败时
        """
        try:
            adapter = self.get_adapter(symbol)
            return await adapter.fetch_data(symbol, start_date, end_date, **kwargs)
        except Exception as e:
            self.logger.error(f"获取{symbol}数据失败: {e}")
            raise

    async def get_realtime_data(self, symbol: str, **kwargs):
        """
        统一的实时数据获取接口

        Args:
            symbol: 数据符号
            **kwargs: 额外参数

        Returns:
            实时数据字典

        Raises:
            Exception: 当获取失败时
        """
        try:
            adapter = self.get_adapter(symbol)
            return await adapter.get_realtime_data(symbol, **kwargs)
        except Exception as e:
            self.logger.error(f"获取{symbol}实时数据失败: {e}")
            raise


# 全局工厂实例
factory = HybridAdapterFactory()


def get_adapter(symbol: str) -> BaseAdapter:
    """便捷函数：获取适配器"""
    return factory.get_adapter(symbol)


async def fetch_data(symbol: str, start_date: str, end_date: str, **kwargs):
    """便捷函数：获取数据"""
    return await factory.fetch_data(symbol, start_date, end_date, **kwargs)


async def get_realtime_data(symbol: str, **kwargs):
    """便捷函数：获取实时数据"""
    return await factory.get_realtime_data(symbol, **kwargs)
