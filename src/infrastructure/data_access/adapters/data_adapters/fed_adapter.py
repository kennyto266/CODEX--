"""
FED数据适配器
从美联储FRED (Federal Reserve Economic Data) 获取利率数据

支持的指标:
- 联邦基金利率 (Federal Funds Rate)
- 贴现率 (Discount Rate)
- 10年期国债收益率 (10-Year Treasury Constant Maturity Rate)
- 30年期国债收益率 (30-Year Treasury Constant Maturity Rate)

数据源: https://fred.stlouisfed.org/docs/api/

Author: Phase 2 Development
Date: 2025-11-12
"""

import asyncio
import json
import logging
from datetime import date, datetime
from typing import Dict, List, Optional, Any
import pandas as pd

from .unified_rate_adapter import (
    BaseRateAdapter,
    RateIndicator,
    Currency,
    RateDataPoint
)

logger = logging.getLogger(__name__)


class FedAdapter(BaseRateAdapter):
    """美联储数据适配器"""

    ADAPTER_NAME = "Federal Reserve (FRED)"
    DATA_SOURCE_URL = "https://api.stlouisfed.org/fred"
    DEFAULT_CURRENCY = Currency.USD

    # FRED API支持的利率指标
    SUPPORTED_INDICATORS = {
        'fed_funds': {
            'code': 'FEDFUNDS',
            'name': 'Federal Funds Rate',
            'description': 'Effective Federal Funds Rate'
        },
        'discount_rate': {
            'code': 'DFEDTARU',
            'name': 'Discount Rate',
            'description': 'Federal Discount Rate'
        },
        'treasury_10y': {
            'code': 'DGS10',
            'name': '10-Year Treasury Rate',
            'description': '10-Year Treasury Constant Maturity Rate'
        },
        'treasury_30y': {
            'code': 'DGS30',
            'name': '30-Year Treasury Rate',
            'description': '30-Year Treasury Constant Maturity Rate'
        },
        'treasury_1m': {
            'code': 'DGS1MO',
            'name': '1-Month Treasury Rate',
            'description': '1-Month Treasury Constant Maturity Rate'
        },
        'treasury_3m': {
            'code': 'DGS3MO',
            'name': '3-Month Treasury Rate',
            'description': '3-Month Treasury Constant Maturity Rate'
        },
        'treasury_6m': {
            'code': 'DGS6MO',
            'name': '6-Month Treasury Rate',
            'description': '6-Month Treasury Constant Maturity Rate'
        },
        'treasury_1y': {
            'code': 'DGS1',
            'name': '1-Year Treasury Rate',
            'description': '1-Year Treasury Constant Maturity Rate'
        },
        'treasury_2y': {
            'code': 'DGS2',
            'name': '2-Year Treasury Rate',
            'description': '2-Year Treasury Constant Maturity Rate'
        },
        'treasury_5y': {
            'code': 'DGS5',
            'name': '5-Year Treasury Rate',
            'description': '5-Year Treasury Constant Maturity Rate'
        },
        'treasury_7y': {
            'code': 'DGS7',
            'name': '7-Year Treasury Rate',
            'description': '7-Year Treasury Constant Maturity Rate'
        },
        'treasury_20y': {
            'code': 'DGS20',
            'name': '20-Year Treasury Rate',
            'description': '20-Year Treasury Constant Maturity Rate'
        }
    }

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化FED适配器

        Args:
            config: 配置字典
                - api_key: FRED API密钥（可选，无密钥可获取有限数据）
                - use_mock_data: 是否使用模拟数据（默认: False）
        """
        super().__init__(config)

        self.api_key = self.config.get('api_key')
        if not self.api_key:
            logger.warning(
                "No FRED API key provided. Limited data access. "
                "Get free API key at: https://fred.stlouisfed.org/docs/api/api_key.html"
            )

        # FRED API基础URL
        self.base_url = f"{self.DATA_SOURCE_URL}/series"

    def _map_indicator_to_fred_code(self, indicator: RateIndicator) -> Optional[str]:
        """将内部指标映射到FRED系列代码"""
        indicator_map = {
            RateIndicator.FED_FUNDS: 'FEDFUNDS',
            RateIndicator.DISCOUNT_RATE: 'DFEDTARU',
            RateIndicator.TREASURY_10Y: 'DGS10',
        }

        # 从SUPPORTED_INDICATORS中查找
        for key, info in self.SUPPORTED_INDICATORS.items():
            if key == indicator.value or info['name'].lower() == indicator.value.lower():
                return info['code']

        return indicator_map.get(indicator)

    async def _fetch_fred_series(
        self,
        series_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Optional[List[Dict]]:
        """
        从FRED API获取系列数据

        Args:
            series_id: FRED系列ID（如'FEDFUNDS'）
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            数据点列表或None
        """
        # 构建API URL
        url = f"{self.base_url}/observations"

        # 构建参数
        params = {
            'series_id': series_id,
            'api_key': self.api_key or 'demo',
            'file_type': 'json'
        }

        # 添加日期范围
        if start_date:
            params['observation_start'] = start_date.strftime('%Y-%m-%d')
        if end_date:
            params['observation_end'] = end_date.strftime('%Y-%m-%d')

        logger.debug(f"请求FRED数据: {series_id}, 日期范围: {start_date} - {end_date}")

        response = await self._make_request(url, params=params)

        if not response:
            logger.error(f"获取{series_id}数据失败")
            return None

        try:
            data = await response.json()

            if 'observations' not in data:
                logger.error(f"响应中无observations字段: {data}")
                return None

            # 检查是否有错误
            if 'error_code' in data:
                logger.error(f"FRED API错误 {data.get('error_code')}: {data.get('error_message')}")
                return None

            logger.info(f"成功获取{series_id}数据，共{len(data['observations'])}条记录")
            return data['observations']

        except json.JSONDecodeError as e:
            logger.error(f"解析JSON响应失败: {e}")
            return None
        except Exception as e:
            logger.error(f"处理FRED响应失败: {e}")
            return None

    async def _fetch_fed_funds_rate(self) -> Optional[RateDataPoint]:
        """获取联邦基金利率"""
        series_id = 'FEDFUNDS'
        end_date = date.today()
        start_date = end_date  # 只要最新数据

        observations = await self._fetch_fred_series(series_id, start_date, end_date)

        if not observations:
            return None

        # 获取最新有效数据
        for obs in reversed(observations):
            if obs['value'] != '.':
                try:
                    rate_value = float(obs['value'])
                    data_date = datetime.strptime(obs['date'], '%Y-%m-%d').date()

                    return RateDataPoint(
                        indicator=RateIndicator.FED_FUNDS,
                        currency=Currency.USD,
                        date=data_date,
                        value=rate_value,
                        unit='%',
                        source=self.ADAPTER_NAME,
                        is_mock=self.use_mock_data
                    )
                except (ValueError, TypeError) as e:
                    logger.debug(f"跳过无效数据点: {obs['value']}, 错误: {e}")
                    continue

        logger.warning(f"未找到有效的{series_id}数据")
        return None

    async def _fetch_discount_rate(self) -> Optional[RateDataPoint]:
        """获取贴现率"""
        series_id = 'DFEDTARU'
        end_date = date.today()
        start_date = end_date

        observations = await self._fetch_fred_series(series_id, start_date, end_date)

        if not observations:
            return None

        # 获取最新有效数据
        for obs in reversed(observations):
            if obs['value'] != '.':
                try:
                    rate_value = float(obs['value'])
                    data_date = datetime.strptime(obs['date'], '%Y-%m-%d').date()

                    return RateDataPoint(
                        indicator=RateIndicator.DISCOUNT_RATE,
                        currency=Currency.USD,
                        date=data_date,
                        value=rate_value,
                        unit='%',
                        source=self.ADAPTER_NAME,
                        is_mock=self.use_mock_data
                    )
                except (ValueError, TypeError) as e:
                    logger.debug(f"跳过无效数据点: {obs['value']}, 错误: {e}")
                    continue

        logger.warning(f"未找到有效的{series_id}数据")
        return None

    async def _fetch_generic_rate(
        self,
        indicator: RateIndicator
    ) -> Optional[RateDataPoint]:
        """获取通用利率"""
        # 尝试从SUPPORTED_INDICATORS中查找
        fred_code = self._map_indicator_to_fred_code(indicator)

        if not fred_code:
            logger.error(f"不支持的指标: {indicator}")
            return None

        end_date = date.today()
        start_date = end_date

        observations = await self._fetch_fred_series(fred_code, start_date, end_date)

        if not observations:
            return None

        # 获取最新有效数据
        for obs in reversed(observations):
            if obs['value'] != '.':
                try:
                    rate_value = float(obs['value'])
                    data_date = datetime.strptime(obs['date'], '%Y-%m-%d').date()

                    return RateDataPoint(
                        indicator=indicator,
                        currency=Currency.USD,
                        date=data_date,
                        value=rate_value,
                        unit='%',
                        source=self.ADAPTER_NAME,
                        is_mock=self.use_mock_data
                    )
                except (ValueError, TypeError) as e:
                    logger.debug(f"跳过无效数据点: {obs['value']}, 错误: {e}")
                    continue

        logger.warning(f"未找到有效的{fred_code}数据")
        return None

    async def _fetch_historical_data(
        self,
        indicator: RateIndicator,
        start_date: date,
        end_date: date
    ) -> Optional[List[RateDataPoint]]:
        """获取历史数据"""
        fred_code = self._map_indicator_to_fred_code(indicator)

        if not fred_code:
            logger.error(f"不支持的指标: {indicator}")
            return None

        observations = await self._fetch_fred_series(fred_code, start_date, end_date)

        if not observations:
            return None

        # 解析数据
        data_points = []
        for obs in observations:
            if obs['value'] != '.':
                try:
                    rate_value = float(obs['value'])
                    data_date = datetime.strptime(obs['date'], '%Y-%m-%d').date()

                    # 只保留指定日期范围内的数据
                    if start_date <= data_date <= end_date:
                        data_points.append(RateDataPoint(
                            indicator=indicator,
                            currency=Currency.USD,
                            date=data_date,
                            value=rate_value,
                            unit='%',
                            source=self.ADAPTER_NAME,
                            is_mock=self.use_mock_data
                        ))
                except (ValueError, TypeError) as e:
                    logger.debug(f"跳过无效数据点: {obs['value']}, 错误: {e}")
                    continue

        if data_points:
            # 按日期排序
            data_points.sort(key=lambda x: x.date)
            logger.info(f"成功解析{len(data_points)}条{indicator}记录")
        else:
            logger.warning(f"未找到有效数据")

        return data_points

    async def get_multiple_rates(
        self,
        indicators: List[RateIndicator]
    ) -> Dict[RateIndicator, Optional[RateDataPoint]]:
        """
        批量获取多个利率指标

        Args:
            indicators: 利率指标列表

        Returns:
            各指标的利率数据字典
        """
        logger.info(f"批量获取{len(indicators)}个利率指标...")

        results = {}
        for indicator in indicators:
            try:
                rate_data = await self.fetch_latest_rate(indicator)
                results[indicator] = rate_data
                logger.debug(f"获取{indicator}: {rate_data.value if rate_data else 'N/A'}")
            except Exception as e:
                logger.error(f"获取{indicator}失败: {e}")
                results[indicator] = None

        return results


# 便捷函数
async def get_latest_fed_rate(
    indicator: RateIndicator,
    api_key: Optional[str] = None,
    use_mock: bool = False
) -> Optional[RateDataPoint]:
    """
    获取最新FED利率

    Args:
        indicator: 利率指标
        api_key: FRED API密钥
        use_mock: 是否使用模拟数据

    Returns:
        RateDataPoint或None
    """
    config = {
        'api_key': api_key,
        'use_mock_data': use_mock
    }

    adapter = FedAdapter(config)
    async with adapter:
        return await adapter.fetch_latest_rate(indicator)


async def get_fed_historical_rates(
    indicator: RateIndicator,
    start_date: date,
    end_date: Optional[date] = None,
    api_key: Optional[str] = None,
    use_mock: bool = False
) -> Optional[List[RateDataPoint]]:
    """
    获取FED历史利率

    Args:
        indicator: 利率指标
        start_date: 开始日期
        end_date: 结束日期
        api_key: FRED API密钥
        use_mock: 是否使用模拟数据

    Returns:
        RateDataPoint列表或None
    """
    config = {
        'api_key': api_key,
        'use_mock_data': use_mock
    }

    adapter = FedAdapter(config)
    async with adapter:
        return await adapter.fetch_historical_rates(indicator, start_date, end_date)


# 测试代码
if __name__ == "__main__":
    async def test():
        # 测试获取联邦基金利率
        adapter = FedAdapter(config={'use_mock_data': True})

        async with adapter:
            # 获取最新联邦基金利率
            fed_funds = await adapter.fetch_latest_rate(RateIndicator.FED_FUNDS)
            print(f"联邦基金利率: {fed_funds.value if fed_funds else 'N/A'}%")

            # 获取历史数据
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            historical = await adapter.fetch_historical_rates(
                RateIndicator.FED_FUNDS,
                start_date,
                end_date
            )

            if historical:
                print(f"历史数据 ({len(historical)} 条):")
                for dp in historical[:5]:  # 只显示前5条
                    print(f"  {dp.date}: {dp.value}%")

    asyncio.run(test())
