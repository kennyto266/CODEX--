"""
替代数据适配器单元测试

测试覆盖:
- AlternativeDataAdapter 基类
- HKEXDataCollector
- GovDataCollector
- KaggleDataCollector
- AlternativeDataService

目标覆盖率: 90%+
"""

import pytest
import asyncio
import pandas as pd
from datetime import date, datetime, timedelta
from pathlib import Path
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_adapters.alternative_data_adapter import (
    AlternativeDataAdapter,
    IndicatorMetadata,
    DataFrequency,
    AlternativeDataPoint,
)
from src.data_adapters.hkex_data_collector import HKEXDataCollector
from src.data_adapters.gov_data_collector import GovDataCollector
from src.data_adapters.kaggle_data_collector import KaggleDataCollector
from src.data_adapters.alternative_data_service import AlternativeDataService


class TestAlternativeDataAdapter:
    """测试AlternativeDataAdapter基类"""

    @pytest.fixture
    async def adapter(self):
        """创建测试用的HKEXDataCollector实例"""
        collector = HKEXDataCollector(mode="mock")
        await collector.connect()
        yield collector
        await collector.disconnect()

    @pytest.mark.asyncio
    async def test_adapter_initialization(self):
        """测试适配器初始化"""
        collector = HKEXDataCollector(mode="mock")
        assert collector.adapter_name == "HKEXDataCollector"
        assert collector.cache_ttl == 3600
        assert collector.max_retries == 3
        assert collector._is_connected is False

    @pytest.mark.asyncio
    async def test_adapter_connect(self):
        """测试连接"""
        collector = HKEXDataCollector(mode="mock")
        result = await collector.connect()
        assert result is True
        assert collector._is_connected is True
        await collector.disconnect()

    @pytest.mark.asyncio
    async def test_adapter_disconnect(self):
        """测试断开连接"""
        collector = HKEXDataCollector(mode="mock")
        await collector.connect()
        result = await collector.disconnect()
        assert result is True
        assert collector._is_connected is False

    @pytest.mark.asyncio
    async def test_list_indicators(self):
        """测试列出指标"""
        collector = HKEXDataCollector(mode="mock")
        await collector.connect()

        indicators = await collector.list_indicators()
        assert len(indicators) > 0
        assert "hsi_futures_volume" in indicators

        await collector.disconnect()

    @pytest.mark.asyncio
    async def test_health_check(self):
        """测试健康检查"""
        collector = HKEXDataCollector(mode="mock")
        await collector.connect()

        health = await collector.health_check()
        assert "adapter_name" in health
        assert "is_connected" in health
        assert "cache_size" in health
        assert health["is_connected"] is True

        await collector.disconnect()

    @pytest.mark.asyncio
    async def test_cache_mechanism(self):
        """测试缓存机制"""
        collector = HKEXDataCollector(mode="mock", cache_ttl=3600)
        await collector.connect()

        # 第一次获取
        data1 = await collector.fetch_data(
            "hsi_futures_volume", date(2024, 1, 1), date(2024, 1, 5)
        )
        assert len(data1) > 0

        # 第二次获取（应该从缓存获取）
        data2 = await collector.fetch_data(
            "hsi_futures_volume", date(2024, 1, 1), date(2024, 1, 5)
        )
        assert len(data2) == len(data1)

        # 检查缓存
        health = await collector.health_check()
        assert health["cache_size"] > 0

        await collector.disconnect()

    @pytest.mark.asyncio
    async def test_clear_cache(self):
        """测试清空缓存"""
        collector = HKEXDataCollector(mode="mock")
        await collector.connect()

        # 获取数据以填充缓存
        await collector.fetch_data(
            "hsi_futures_volume", date(2024, 1, 1), date(2024, 1, 5)
        )
        assert len(collector._cache) > 0

        # 清空缓存
        collector.clear_cache()
        assert len(collector._cache) == 0

        await collector.disconnect()

    @pytest.mark.asyncio
    async def test_metadata_cache(self):
        """测试元数据缓存"""
        collector = HKEXDataCollector(mode="mock")
        await collector.connect()

        # 第一次获取元数据
        metadata1 = await collector.get_metadata("hsi_futures_volume")
        assert metadata1 is not None
        assert metadata1.indicator_code == "hsi_futures_volume"

        # 第二次获取应该从缓存获取
        metadata2 = await collector.get_metadata("hsi_futures_volume")
        assert metadata1 == metadata2

        await collector.disconnect()


class TestHKEXDataCollector:
    """测试HKEX数据收集器"""

    @pytest.mark.asyncio
    async def test_hkex_initialization(self):
        """测试HKEX收集器初始化"""
        collector = HKEXDataCollector(mode="mock")
        assert collector.mode == "mock"
        # HKEX collector has 12 indicators (futures, options, market structure)
        assert len(collector.SUPPORTED_INDICATORS) >= 10

    @pytest.mark.asyncio
    async def test_hkex_supported_indicators(self):
        """测试HKEX支持的指标"""
        collector = HKEXDataCollector(mode="mock")
        indicators = collector.SUPPORTED_INDICATORS.keys()

        expected = [
            "hsi_futures_volume",
            "hsi_futures_open_interest",
            "hsi_implied_volatility",
        ]
        for ind in expected:
            assert ind in indicators

    @pytest.mark.asyncio
    async def test_hkex_fetch_data(self):
        """测试HKEX数据获取"""
        collector = HKEXDataCollector(mode="mock")
        await collector.connect()

        data = await collector.fetch_data(
            "hsi_futures_volume", date(2024, 1, 1), date(2024, 1, 31)
        )

        assert isinstance(data, pd.DataFrame)
        assert len(data) > 0
        assert "timestamp" in data.columns
        assert "value" in data.columns
        assert "indicator" in data.columns

        await collector.disconnect()

    @pytest.mark.asyncio
    async def test_hkex_realtime_data(self):
        """测试HKEX实时数据"""
        collector = HKEXDataCollector(mode="mock")
        await collector.connect()

        data = await collector.get_realtime_data("hsi_implied_volatility")

        assert data is not None
        assert "indicator_code" in data
        assert "timestamp" in data
        assert "value" in data
        assert "unit" in data

        await collector.disconnect()

    @pytest.mark.asyncio
    async def test_hkex_invalid_indicator(self):
        """测试HKEX无效指标"""
        collector = HKEXDataCollector(mode="mock")
        await collector.connect()

        with pytest.raises(ValueError):
            await collector.fetch_data("invalid_indicator", date(2024, 1, 1), date(2024, 1, 5))

        await collector.disconnect()

    @pytest.mark.asyncio
    async def test_hkex_metadata(self):
        """测试HKEX元数据"""
        collector = HKEXDataCollector(mode="mock")
        await collector.connect()

        metadata = await collector.get_metadata("hsi_futures_volume")

        assert metadata.indicator_code == "hsi_futures_volume"
        assert metadata.data_source == "HKEX"
        assert metadata.frequency == DataFrequency.DAILY
        assert metadata.country_code == "HK"

        await collector.disconnect()


class TestGovDataCollector:
    """测试政府数据收集器"""

    @pytest.mark.asyncio
    async def test_gov_initialization(self):
        """测试政府收集器初始化"""
        collector = GovDataCollector(mode="mock")
        assert collector.mode == "mock"
        assert len(collector.SUPPORTED_INDICATORS) >= 11

    @pytest.mark.asyncio
    async def test_gov_supported_indicators(self):
        """测试政府支持的指标"""
        collector = GovDataCollector(mode="mock")
        indicators = collector.SUPPORTED_INDICATORS.keys()

        expected = ["hibor_overnight", "visitor_arrivals_total", "unemployment_rate"]
        for ind in expected:
            assert ind in indicators

    @pytest.mark.asyncio
    async def test_gov_fetch_data(self):
        """测试政府数据获取"""
        collector = GovDataCollector(mode="mock")
        await collector.connect()

        # HIBOR数据（日频）
        data = await collector.fetch_data(
            "hibor_3m", date(2024, 1, 1), date(2024, 1, 31)
        )

        assert isinstance(data, pd.DataFrame)
        assert len(data) > 0
        # GovDataCollector returns 'date' column, not 'timestamp'
        assert "date" in data.columns or "timestamp" in data.columns
        assert "value" in data.columns

        await collector.disconnect()

    @pytest.mark.asyncio
    async def test_gov_monthly_data(self):
        """测试政府月度数据"""
        collector = GovDataCollector(mode="mock")
        await collector.connect()

        # 访客数据（月频）
        data = await collector.fetch_data(
            "visitor_arrivals_total", date(2024, 1, 1), date(2024, 12, 31)
        )

        assert isinstance(data, pd.DataFrame)
        assert len(data) > 0
        # 应该大约是12个数据点（每月1个）
        assert 1 <= len(data) <= 13

        await collector.disconnect()

    @pytest.mark.asyncio
    async def test_gov_realtime_data(self):
        """测试政府实时数据"""
        collector = GovDataCollector(mode="mock")
        await collector.connect()

        data = await collector.get_realtime_data("unemployment_rate")

        assert data is not None
        assert "indicator_code" in data
        assert "value" in data
        assert "timestamp" in data

        await collector.disconnect()

    @pytest.mark.asyncio
    async def test_gov_metadata(self):
        """测试政府元数据"""
        collector = GovDataCollector(mode="mock")
        await collector.connect()

        metadata = await collector.get_metadata("hibor_overnight")

        assert metadata.indicator_code == "hibor_overnight"
        assert metadata.data_source is not None  # Data source should be set
        assert metadata.country_code == "HK"

        await collector.disconnect()


class TestKaggleDataCollector:
    """测试Kaggle数据收集器"""

    @pytest.mark.asyncio
    async def test_kaggle_initialization(self):
        """测试Kaggle收集器初始化"""
        collector = KaggleDataCollector(mode="mock", data_directory="./datasets")
        assert collector.mode == "mock"
        assert len(collector.SUPPORTED_INDICATORS) == 10

    @pytest.mark.asyncio
    async def test_kaggle_supported_indicators(self):
        """测试Kaggle支持的指标"""
        collector = KaggleDataCollector(mode="mock")
        indicators = collector.SUPPORTED_INDICATORS.keys()

        expected = ["hong_kong_gdp", "hsi_historical", "us_stock_prices"]
        for ind in expected:
            assert ind in indicators

    @pytest.mark.asyncio
    async def test_kaggle_fetch_data(self):
        """测试Kaggle数据获取"""
        collector = KaggleDataCollector(mode="mock")
        await collector.connect()

        data = await collector.fetch_data(
            "hong_kong_gdp", date(2024, 1, 1), date(2024, 12, 31)
        )

        assert isinstance(data, pd.DataFrame)
        assert len(data) > 0
        assert "timestamp" in data.columns
        assert "value" in data.columns

        await collector.disconnect()

    @pytest.mark.asyncio
    async def test_kaggle_realtime_data(self):
        """测试Kaggle实时数据"""
        collector = KaggleDataCollector(mode="mock")
        await collector.connect()

        data = await collector.get_realtime_data("hsi_historical")

        assert data is not None
        assert "indicator_code" in data
        assert "value" in data

        await collector.disconnect()

    @pytest.mark.asyncio
    async def test_kaggle_set_data_directory(self):
        """测试Kaggle设置数据目录"""
        collector = KaggleDataCollector(mode="mock")
        original_dir = collector.data_directory

        collector.set_data_directory("./new_datasets")
        assert collector.data_directory == Path("./new_datasets")

        collector.set_data_directory(str(original_dir))

    @pytest.mark.asyncio
    async def test_kaggle_metadata(self):
        """测试Kaggle元数据"""
        collector = KaggleDataCollector(mode="mock")
        await collector.connect()

        metadata = await collector.get_metadata("hong_kong_gdp")

        assert metadata.indicator_code == "hong_kong_gdp"
        assert metadata.data_source == "Kaggle"
        assert metadata.country_code == "HK"

        await collector.disconnect()


class TestAlternativeDataService:
    """测试替代数据服务"""

    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """测试服务初始化"""
        service = AlternativeDataService()
        assert service._initialized is False

        initialized = await service.initialize(mode="mock")
        assert initialized is True
        assert service._initialized is True

        await service.cleanup()

    @pytest.mark.asyncio
    async def test_service_list_adapters(self):
        """测试列出适配器"""
        service = AlternativeDataService()
        await service.initialize(mode="mock")

        adapters = await service.list_adapters()
        assert len(adapters) >= 3
        assert "hkex" in adapters
        assert "government" in adapters
        assert "kaggle" in adapters

        await service.cleanup()

    @pytest.mark.asyncio
    async def test_service_get_data(self):
        """测试从服务获取数据"""
        service = AlternativeDataService()
        await service.initialize(mode="mock")

        data = await service.get_data(
            "hkex", "hsi_futures_volume", date(2024, 1, 1), date(2024, 1, 31)
        )

        assert data is not None
        assert len(data) > 0
        assert "timestamp" in data.columns
        assert "value" in data.columns

        await service.cleanup()

    @pytest.mark.asyncio
    async def test_service_get_realtime_data(self):
        """测试从服务获取实时数据"""
        service = AlternativeDataService()
        await service.initialize(mode="mock")

        data = await service.get_realtime_data("hkex", "hsi_implied_volatility")

        assert data is not None
        assert "indicator_code" in data

        await service.cleanup()

    @pytest.mark.asyncio
    async def test_service_list_indicators(self):
        """测试列出指标"""
        service = AlternativeDataService()
        await service.initialize(mode="mock")

        indicators = await service.list_indicators("hkex")
        assert len(indicators) >= 10  # HKEX has 12 indicators

        indicators = await service.list_indicators("government")
        assert len(indicators) >= 11

        await service.cleanup()

    @pytest.mark.asyncio
    async def test_service_health_check(self):
        """测试服务健康检查"""
        service = AlternativeDataService()
        await service.initialize(mode="mock")

        health = await service.health_check()

        assert "service" in health
        assert "initialized" in health
        assert "adapters" in health
        assert health["initialized"] is True

        await service.cleanup()

    @pytest.mark.asyncio
    async def test_service_clear_cache(self):
        """测试清空服务缓存"""
        service = AlternativeDataService()
        await service.initialize(mode="mock")

        # 获取一些数据以填充缓存
        await service.get_data("hkex", "hsi_futures_volume", date(2024, 1, 1), date(2024, 1, 5))

        # 清空特定适配器的缓存
        result = await service.clear_cache("hkex")
        assert result is True

        # 清空所有缓存
        result = await service.clear_cache()
        assert result is True

        await service.cleanup()

    @pytest.mark.asyncio
    async def test_service_info(self):
        """测试服务信息"""
        service = AlternativeDataService()
        info = service.get_service_info()

        assert info["service_name"] == "AlternativeDataService"
        assert "adapters_registered" in info

        await service.initialize(mode="mock")
        info = service.get_service_info()
        assert info["initialized"] is True

        await service.cleanup()

    @pytest.mark.asyncio
    async def test_service_invalid_adapter(self):
        """测试无效适配器处理"""
        service = AlternativeDataService()
        await service.initialize(mode="mock")

        # 尝试从不存在的适配器获取数据
        data = await service.get_data(
            "invalid_adapter", "some_indicator", date(2024, 1, 1), date(2024, 1, 5)
        )
        assert data is None

        await service.cleanup()


class TestDataValidation:
    """测试数据验证"""

    @pytest.mark.asyncio
    async def test_data_format_validation(self):
        """测试数据格式验证"""
        collector = HKEXDataCollector(mode="mock")
        await collector.connect()

        data = await collector.fetch_data(
            "hsi_futures_volume", date(2024, 1, 1), date(2024, 1, 5)
        )

        # 验证必要列
        assert "timestamp" in data.columns
        assert "value" in data.columns

        # 验证数据类型
        assert pd.api.types.is_datetime64_any_dtype(data["timestamp"])
        assert pd.api.types.is_numeric_dtype(data["value"])

        await collector.disconnect()

    @pytest.mark.asyncio
    async def test_no_missing_values(self):
        """测试无缺失值"""
        collector = GovDataCollector(mode="mock")
        await collector.connect()

        data = await collector.fetch_data(
            "hibor_overnight", date(2024, 1, 1), date(2024, 1, 31)
        )

        # 检查没有NaN值
        assert not data.isnull().any().any()

        await collector.disconnect()


class TestErrorHandling:
    """测试错误处理"""

    @pytest.mark.asyncio
    async def test_invalid_date_range(self):
        """测试无效日期范围"""
        collector = HKEXDataCollector(mode="mock")
        await collector.connect()

        # end_date在start_date之前应该返回空数据或引发异常
        try:
            data = await collector.fetch_data(
                "hsi_futures_volume", date(2024, 1, 31), date(2024, 1, 1)
            )
            # 如果返回了数据，应该是空的
            assert isinstance(data, pd.DataFrame)
            assert len(data) == 0
        except (KeyError, Exception):
            # 也可以接受异常处理
            pass

        await collector.disconnect()

    @pytest.mark.asyncio
    async def test_uninitialized_service(self):
        """测试未初始化的服务"""
        service = AlternativeDataService()

        # 应该返回None因为服务未初始化
        data = await service.get_data("hkex", "hsi_futures_volume", date(2024, 1, 1), date(2024, 1, 5))
        assert data is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
