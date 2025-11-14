"""
統一真實數據管理系統
整合所有真實數據適配器，提供統一的數據訪問接口

這是一個核心組件，管理所有經過驗證的真實數據源。
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Type
from dataclasses import dataclass
from enum import Enum

from .exchange_rate_adapter import ExchangeRateAdapter
from .alpha_vantage_adapter import AlphaVantageAdapter
from .hkma_csv_adapter import HKMACSVAdapter
from .csd_csv_adapter import CSDCSVAdapter


class DataSourceType(Enum):
    """數據源類型"""
    EXCHANGE_RATE = "exchange_rate"
    ALPHA_VANTAGE = "alpha_vantage"
    HKMA_CSV = "hkma_csv"
    CSD_CSV = "csd_csv"


@dataclass
class DataSourceConfig:
    """數據源配置"""
    name: str
    adapter_class: Type
    enabled: bool = True
    api_key_required: bool = False
    api_key_env_var: Optional[str] = None
    description: str = ""


class UnifiedRealDataManager:
    """
    統一真實數據管理器

    管理所有真實數據適配器，提供：
    1. 統一的數據訪問接口
    2. 數據源健康監控
    3. 自動降級和故障轉移
    4. 批量數據獲取
    """

    # 註冊所有真實數據源
    REGISTERED_SOURCES = {
        DataSourceType.EXCHANGE_RATE: DataSourceConfig(
            name="ExchangeRate-API",
            adapter_class=ExchangeRateAdapter,
            enabled=True,
            api_key_required=False,
            description="實時外匯匯率數據 - 完全免費"
        ),
        DataSourceType.ALPHA_VANTAGE: DataSourceConfig(
            name="Alpha Vantage",
            adapter_class=AlphaVantageAdapter,
            enabled=True,
            api_key_required=True,
            api_key_env_var="ALPHAVANTAGE_API_KEY",
            description="金融市場數據 - 需免費API密鑰"
        ),
        DataSourceType.HKMA_CSV: DataSourceConfig(
            name="HKMA CSV",
            adapter_class=HKMACSVAdapter,
            enabled=True,
            api_key_required=False,
            description="香港金融管理局數據 - 需手動下載CSV"
        ),
        DataSourceType.CSD_CSV: DataSourceConfig(
            name="C&SD CSV",
            adapter_class=CSDCSVAdapter,
            enabled=True,
            api_key_required=False,
            description="政府統計處數據 - 可自動抓取"
        )
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # 適配器實例緩存
        self._adapters: Dict[DataSourceType, Any] = {}

        # 數據源狀態
        self._source_status: Dict[DataSourceType, Dict[str, Any]] = {}

        self.logger.info(f"統一真實數據管理器初始化完成，已註冊 {len(self.REGISTERED_SOURCES)} 個數據源")

    async def _get_adapter(self, source_type: DataSourceType):
        """獲取或創建適配器實例"""
        if source_type not in self._adapters:
            config = self.REGISTERED_SOURCES[source_type]
            if not config.enabled:
                raise ValueError(f"數據源 {source_type.value} 已禁用")

            # 檢查API密鑰
            if config.api_key_required:
                import os
                api_key = os.getenv(config.api_key_env_var) if config.api_key_env_var else None
                if not api_key:
                    self.logger.warning(f"數據源 {source_type.value} 需要API密鑰，但未設置")
                    return None

            # 創建適配器實例
            adapter = config.adapter_class()
            self._adapters[source_type] = adapter

        return self._adapters[source_type]

    async def check_source_health(self, source_type: DataSourceType) -> Dict[str, Any]:
        """
        檢查數據源健康狀態

        Args:
            source_type: 數據源類型

        Returns:
            健康狀態信息
        """
        config = self.REGISTERED_SOURCES[source_type]
        status = {
            'name': config.name,
            'enabled': config.enabled,
            'available': False,
            'api_key_required': config.api_key_required,
            'api_key_configured': False,
            'last_check': datetime.now().isoformat(),
            'error': None
        }

        try:
            # 檢查API密鑰
            if config.api_key_required:
                import os
                api_key = os.getenv(config.api_key_env_var) if config.api_key_env_var else None
                status['api_key_configured'] = bool(api_key)
                if not api_key:
                    status['error'] = f"未配置API密鑰 ({config.api_key_env_var})"
                    self._source_status[source_type] = status
                    return status

            # 測試連接
            adapter = await self._get_adapter(source_type)
            if adapter is None:
                status['error'] = "無法創建適配器實例"
                self._source_status[source_type] = status
                return status

            # 嘗試連接測試
            if hasattr(adapter, 'test_connection'):
                connected = await adapter.test_connection()
                status['available'] = connected

                if not connected:
                    status['error'] = "連接測試失敗"
            else:
                # 如果沒有連接測試方法，標記為可用
                status['available'] = True

        except Exception as e:
            status['error'] = str(e)
            self.logger.error(f"檢查 {source_type.value} 健康狀態失敗: {e}")

        self._source_status[source_type] = status
        return status

    async def check_all_sources_health(self) -> Dict[str, Any]:
        """檢查所有數據源健康狀態"""
        results = {}
        for source_type in DataSourceType:
            results[source_type.value] = await self.check_source_health(source_type)
        return results

    async def get_available_sources(self) -> List[DataSourceType]:
        """獲取所有可用的數據源"""
        available = []
        for source_type in DataSourceType:
            status = await self.check_source_health(source_type)
            if status['available']:
                available.append(source_type)
        return available

    async def fetch_exchange_rates(self) -> Dict[str, float]:
        """
        獲取所有外匯匯率數據

        Returns:
            匯率字典
        """
        try:
            adapter = await self._get_adapter(DataSourceType.EXCHANGE_RATE)
            if adapter is None:
                raise ValueError("ExchangeRate適配器不可用")

            rates = await adapter.fetch_all_rates()
            self.logger.info(f"成功獲取 {len(rates)} 個匯率")
            return rates
        except Exception as e:
            self.logger.error(f"獲取匯率失敗: {e}")
            raise

    async def fetch_alpha_vantage_data(
        self,
        data_type: str = 'fx_rate',
        **kwargs
    ) -> Any:
        """
        從Alpha Vantage獲取數據

        Args:
            data_type: 數據類型 ('fx_rate', 'stock_data', 'technical_indicator')
            **kwargs: 額外參數

        Returns:
            數據
        """
        try:
            adapter = await self._get_adapter(DataSourceType.ALPHA_VANTAGE)
            if adapter is None:
                raise ValueError("Alpha Vantage適配器不可用")

            if data_type == 'fx_rate':
                from_currency = kwargs.get('from_currency', 'USD')
                to_currency = kwargs.get('to_currency', 'HKD')
                return await adapter.fetch_fx_rate(from_currency, to_currency)
            elif data_type == 'stock_data':
                symbol = kwargs.get('symbol', 'AAPL')
                return await adapter.fetch_stock_data(symbol)
            else:
                raise ValueError(f"不支持的數據類型: {data_type}")
        except Exception as e:
            self.logger.error(f"獲取Alpha Vantage數據失敗: {e}")
            raise

    async def fetch_hkma_data(self, indicator: str, **kwargs) -> Any:
        """
        從HKMA CSV獲取數據

        Args:
            indicator: 指標名稱
            **kwargs: 額外參數

        Returns:
            數據
        """
        try:
            adapter = await self._get_adapter(DataSourceType.HKMA_CSV)
            if adapter is None:
                raise ValueError("HKMA CSV適配器不可用")

            return await adapter.fetch_real_data(indicator, **kwargs)
        except Exception as e:
            self.logger.error(f"獲取HKMA數據失敗: {e}")
            raise

    async def fetch_csd_data(self, category: str, **kwargs) -> Any:
        """
        從C&SD CSV獲取數據

        Args:
            category: 數據類別
            **kwargs: 額外參數

        Returns:
            數據
        """
        try:
            adapter = await self._get_adapter(DataSourceType.CSD_CSV)
            if adapter is None:
                raise ValueError("C&SD CSV適配器不可用")

            return await adapter.scrape_web_data(category, **kwargs)
        except Exception as e:
            self.logger.error(f"獲取C&SD數據失敗: {e}")
            raise

    async def get_data_source_report(self) -> Dict[str, Any]:
        """獲取數據源完整報告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_sources': len(self.REGISTERED_SOURCES),
            'sources': {},
            'summary': {
                'enabled': 0,
                'available': 0,
                'requires_api_key': 0,
                'api_keys_configured': 0
            }
        }

        for source_type in DataSourceType:
            config = self.REGISTERED_SOURCES[source_type]
            status = await self.check_source_health(source_type)

            report['sources'][source_type.value] = {
                'name': config.name,
                'description': config.description,
                'enabled': status['enabled'],
                'available': status['available'],
                'api_key_required': status['api_key_required'],
                'api_key_configured': status['api_key_configured'],
                'error': status['error']
            }

            if config.enabled:
                report['summary']['enabled'] += 1
            if status['available']:
                report['summary']['available'] += 1
            if status['api_key_required']:
                report['summary']['requires_api_key'] += 1
            if status['api_key_configured']:
                report['summary']['api_keys_configured'] += 1

        return report

    async def close(self):
        """關閉所有適配器"""
        for adapter in self._adapters.values():
            if adapter and hasattr(adapter, 'close_session'):
                await adapter.close_session()
        self._adapters.clear()
        self.logger.info("已關閉所有數據源適配器")

    def __repr__(self):
        return f"<UnifiedRealDataManager(sources={len(self.REGISTERED_SOURCES)})>"


# 測試代碼
if __name__ == "__main__":
    async def test():
        print("統一真實數據管理器測試")
        print("=" * 70)

        manager = UnifiedRealDataManager()

        # 獲取數據源報告
        print("\n[1] 獲取數據源狀態報告")
        print("-" * 70)
        report = await manager.get_data_source_report()

        print(f"總數據源: {report['total_sources']}")
        print(f"已啟用: {report['summary']['enabled']}")
        print(f"可用的: {report['summary']['available']}")
        print(f"需API密鑰: {report['summary']['requires_api_key']}")
        print(f"已配置API密鑰: {report['summary']['api_keys_configured']}")

        print("\n數據源詳細信息:")
        for source_name, source_info in report['sources'].items():
            status = "[OK]" if source_info['available'] else "[ERROR]"
            api_note = ""
            if source_info['api_key_required']:
                api_note = f" (API密鑰: {'✓' if source_info['api_key_configured'] else '✗'})"
            print(f"  {status} {source_info['name']}: {source_info['description']}{api_note}")
            if source_info['error']:
                print(f"      錯誤: {source_info['error']}")

        # 測試獲取數據
        print("\n[2] 測試獲取匯率數據")
        print("-" * 70)
        try:
            rates = await manager.fetch_exchange_rates()
            print(f"[OK] 成功獲取 {len(rates)} 個匯率:")
            for currency, rate in list(rates.items())[:5]:
                print(f"  {currency}: {rate:.6f}")
        except Exception as e:
            print(f"[ERROR] 獲取匯率失敗: {e}")

        print("\n[3] 檢查所有數據源健康狀態")
        print("-" * 70)
        health = await manager.check_all_sources_health()
        for source_name, status in health.items():
            available = "✓" if status['available'] else "✗"
            print(f"  {available} {status['name']}: {status['error'] or 'OK'}")

        await manager.close()

        print("\n" + "=" * 70)
        print("測試完成")
        print("=" * 70)

    asyncio.run(test())
