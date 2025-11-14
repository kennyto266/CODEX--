"""
SIBOR数据适配器
从新加坡银行公会(Singapore Association of Banks)获取SIBOR利率数据

支持的指标:
- SIBOR隔夜 (SIBOR Overnight)
- SIBOR 1周 (SIBOR 1 Week)
- SIBOR 1月 (SIBOR 1 Month)
- SIBOR 3月 (SIBOR 3 Months)
- SIBOR 6月 (SIBOR 6 Months)
- SIBOR 12月 (SIBOR 12 Months)

数据来源:
- 新加坡银行公会: http://www.sabs.org.sg/
- 新加坡金融管理局: http://www.mas.gov.sg/
- 国际货币市场: https://www.sgx.com/

Author: Phase 2 Development
Date: 2025-11-12
"""

import asyncio
import json
import logging
import re
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
from bs4 import BeautifulSoup

from .unified_rate_adapter import (
    BaseRateAdapter,
    RateIndicator,
    Currency,
    RateDataPoint
)

logger = logging.getLogger(__name__)


class SIBORAdapter(BaseRateAdapter):
    """SIBOR数据适配器"""

    ADAPTER_NAME = "Singapore Interbank Offered Rate (SIBOR)"
    DATA_SOURCE_URL = "http://www.sabs.org.sg"
    DEFAULT_CURRENCY = Currency.SGD

    # SIBOR支持的利率指标
    SUPPORTED_INDICATORS = {
        'overnight': {
            'name': 'SIBOR隔夜',
            'description': '新加坡银行同业拆借隔夜利率'
        },
        '1w': {
            'name': 'SIBOR 1周',
            'description': '新加坡银行同业拆借1周利率'
        },
        '1m': {
            'name': 'SIBOR 1月',
            'description': '新加坡银行同业拆借1月利率'
        },
        '3m': {
            'name': 'SIBOR 3月',
            'description': '新加坡银行同业拆借3月利率'
        },
        '6m': {
            'name': 'SIBOR 6月',
            'description': '新加坡银行同业拆借6月利率'
        },
        '12m': {
            'name': 'SIBOR 12月',
            'description': '新加坡银行同业拆借12月利率'
        }
    }

    # 数据抓取URL
    SIBOR_DATA_URL = "https://eservices.mas.gov.sg/api/data/X"
    SIBOR_HISTORICAL_URL = "https://eservices.mas.gov.sg/api/data/X"

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化SIBOR适配器

        Args:
            config: 配置字典
                - use_mock_data: 是否使用模拟数据（默认: True）
                - data_source_url: 自定义数据源URL
        """
        super().__init__(config)

        if self.use_mock_data:
            logger.info("使用模拟数据进行测试")

    async def _fetch_mas_sibor_data(
        self,
        indicator: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Optional[List[Dict]]:
        """
        从新加坡金管局获取SIBOR数据

        Args:
            indicator: 指标代码 (如'1M', '3M', '6M', '12M')
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            数据点列表或None
        """
        logger.info(f"正在从MAS获取SIBOR {indicator}数据...")

        try:
            # 构建MAS API请求
            # 注意：MAS的实际API可能需要调整，这里提供示例结构
            params = {
                '_limit': 100,
                'sort': 'date:desc'
            }

            if start_date:
                params['date'] = f"gte:{start_date.strftime('%Y-%m-%d')}"
            if end_date:
                params['date'] = f"lte:{end_date.strftime('%Y-%m-%d')}"

            response = await self._make_request(self.SIBOR_DATA_URL, params=params)

            if not response:
                logger.error("获取MAS SIBOR数据失败")
                return None

            content = await response.text()

            # 尝试解析JSON
            if content.strip().startswith('{'):
                json_data = json.loads(content)
                return self._parse_sibor_json_data(json_data, indicator)
            else:
                # 尝试解析HTML
                return self._parse_sibor_html_data(content, indicator)

        except Exception as e:
            logger.error(f"获取MAS SIBOR数据失败: {e}")
            return None

    def _parse_sibor_json_data(
        self,
        json_data: Dict,
        indicator: str
    ) -> Optional[List[Dict]]:
        """解析SIBOR JSON数据"""
        try:
            data = []

            # 假设JSON结构包含数据数组
            if 'data' in json_data:
                for item in json_data['data']:
                    try:
                        # 解析日期
                        date_str = item.get('date', '')
                        if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

                            # 解析利率值
                            value_key = f'sibor_{indicator.lower()}'
                            if value_key in item:
                                value = float(item[value_key])
                                data.append({
                                    'date': date_obj,
                                    'value': value
                                })
                    except (ValueError, KeyError, TypeError) as e:
                        logger.debug(f"跳过无效数据项: {e}")
                        continue

            if data:
                logger.info(f"成功解析{len(data)}条SIBOR {indicator}记录")
                return data

            return None

        except Exception as e:
            logger.error(f"解析SIBOR JSON数据失败: {e}")
            return None

    def _parse_sibor_html_data(
        self,
        html_content: str,
        indicator: str
    ) -> Optional[List[Dict]]:
        """解析SIBOR HTML数据"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            data = []

            # 查找表格数据
            tables = soup.find_all('table')

            for table in tables:
                rows = table.find_all('tr')

                for row in rows[1:]:  # 跳过标题行
                    cells = row.find_all(['td', 'th'])

                    if len(cells) >= 2:
                        try:
                            # 解析日期
                            date_str = cells[0].get_text(strip=True)
                            if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

                                # 解析利率值
                                value_text = cells[1].get_text(strip=True)
                                if value_text and value_text != '-':
                                    # 移除非数字字符，保留数字和小数点
                                    cleaned_value = re.sub(r'[^\d.]', '', value_text)
                                    if cleaned_value:
                                        value = float(cleaned_value)
                                        data.append({
                                            'date': date_obj,
                                            'value': value
                                        })

                        except (ValueError, IndexError) as e:
                            logger.debug(f"跳过无效SIBOR行: {e}")
                            continue

            if data:
                logger.info(f"成功解析{len(data)}条SIBOR {indicator}记录")
                return data

            return None

        except Exception as e:
            logger.error(f"解析SIBOR HTML数据失败: {e}")
            return None

    async def _fetch_sibor_from_alternative_source(
        self,
        indicator: str
    ) -> Optional[List[Dict]]:
        """从备选数据源获取SIBOR数据"""
        logger.info(f"尝试从备选数据源获取SIBOR {indicator}数据...")

        try:
            # 备选URL - 新加坡交易所或金融数据提供商
            alt_url = "https://www.sgx.com/api/data"

            params = {
                'type': 'sibor',
                'tenor': indicator
            }

            response = await self._make_request(alt_url, params=params)

            if response:
                content = await response.text()
                if content.strip().startswith('{'):
                    json_data = json.loads(content)
                    return self._parse_sibor_json_data(json_data, indicator)

            return None

        except Exception as e:
            logger.error(f"从备选数据源获取SIBOR失败: {e}")
            return None

    def _generate_mock_sibor_data(
        self,
        indicator: str,
        data_date: date
    ) -> Dict:
        """
        生成模拟SIBOR数据

        Args:
            indicator: 指标（如'1M', '3M'）
            data_date: 数据日期

        Returns:
            模拟数据字典
        """
        # 基准SIBOR利率（根据历史数据合理范围）
        base_rates = {
            'O/N': 1.50,  # 隔夜
            '1W': 1.60,   # 1周
            '1M': 1.80,   # 1月
            '3M': 2.00,   # 3月
            '6M': 2.20,   # 6月
            '12M': 2.40   # 12月
        }

        # 期限越长，利率越高，加入随机波动
        import random
        base_value = base_rates.get(indicator, 2.00)
        value = base_value + random.uniform(-0.3, 0.3)

        return {
            'date': data_date,
            'value': max(0.5, min(5.0, value))  # 限制在合理范围内
        }

    async def _fetch_generic_rate(
        self,
        indicator: RateIndicator
    ) -> Optional[RateDataPoint]:
        """获取通用SIBOR利率"""
        try:
            # 将内部指标映射到SIBOR期限代码
            indicator_map = {
                'overnight': 'O/N',
                '1w': '1W',
                '1m': '1M',
                '3m': '3M',
                '6m': '6M',
                '12m': '12M'
            }

            sibor_code = indicator_map.get(indicator.value)
            if not sibor_code:
                logger.warning(f"不支持的SIBOR指标: {indicator}")
                return self._generate_mock_data(indicator, date.today())

            # 尝试从MAS获取数据
            data_list = await self._fetch_mas_sibor_data(sibor_code)

            if not data_list:
                # 如果没有获取到数据，尝试备选数据源
                data_list = await self._fetch_sibor_from_alternative_source(sibor_code)

            if not data_list:
                # 最终回退到模拟数据
                logger.warning(f"未获取到{indicator}真实数据，使用模拟数据")
                mock_data = self._generate_mock_sibor_data(sibor_code, date.today())

                return RateDataPoint(
                    indicator=indicator,
                    currency=Currency.SGD,
                    date=mock_data['date'],
                    value=mock_data['value'],
                    unit='%',
                    source=self.ADAPTER_NAME,
                    is_mock=True
                )

            # 获取最新数据
            data_list.sort(key=lambda x: x['date'])
            latest_data = data_list[-1]

            return RateDataPoint(
                indicator=indicator,
                currency=Currency.SGD,
                date=latest_data['date'],
                value=latest_data['value'],
                unit='%',
                source=self.ADAPTER_NAME,
                is_mock=False
            )

        except Exception as e:
            logger.error(f"获取{indicator}失败: {e}")
            return self._generate_mock_data(indicator, date.today())

    async def _fetch_fed_funds_rate(self) -> Optional[RateDataPoint]:
        """SIBOR不支持联邦基金利率，返回None"""
        logger.warning("SIBOR不支持联邦基金利率")
        return None

    async def _fetch_discount_rate(self) -> Optional[RateDataPoint]:
        """获取贴现率（映射到SIBOR隔夜）"""
        indicator = RateIndicator.DISCOUNT_RATE

        try:
            # 使用SIBOR隔夜利率作为贴现率参考
            overnight_rate = await self._fetch_generic_rate(RateIndicator.OVERNIGHT)

            if overnight_rate:
                # 略高于隔夜利率
                adjusted_value = overnight_rate.value + 0.25

                return RateDataPoint(
                    indicator=indicator,
                    currency=Currency.SGD,
                    date=overnight_rate.date,
                    value=adjusted_value,
                    unit='%',
                    source=self.ADAPTER_NAME,
                    is_mock=overnight_rate.is_mock
                )
            else:
                return self._generate_mock_data(indicator, date.today())

        except Exception as e:
            logger.error(f"获取贴现率失败: {e}")
            return self._generate_mock_data(indicator, date.today())

    async def _fetch_historical_data(
        self,
        indicator: RateIndicator,
        start_date: date,
        end_date: date
    ) -> Optional[List[RateDataPoint]]:
        """获取历史数据"""
        # 当前实现返回模拟数据，实际需要实现完整的历史数据抓取
        logger.warning("SIBOR历史数据抓取需要完整实现，当前使用模拟数据")

        return self._generate_mock_historical(indicator, start_date, end_date)

    async def fetch_all_sibor_rates(self) -> Dict[str, Optional[RateDataPoint]]:
        """
        获取所有SIBOR期限的最新利率

        Returns:
            包含所有SIBOR期限利率的字典
        """
        logger.info("获取所有SIBOR期限利率...")

        results = {}
        indicators = [
            RateIndicator.OVERNIGHT,
            RateIndicator.ONE_WEEK,
            RateIndicator.ONE_MONTH,
            RateIndicator.THREE_MONTHS,
            RateIndicator.SIX_MONTHS,
            RateIndicator.TWELVE_MONTHS
        ]

        for indicator in indicators:
            try:
                rate_data = await self.fetch_latest_rate(indicator)
                results[indicator.value] = rate_data
                if rate_data:
                    logger.info(f"SIBOR {indicator.value}: {rate_data.value}%")
                else:
                    logger.warning(f"未获取到{indicator.value}数据")
            except Exception as e:
                logger.error(f"获取{indicator.value}失败: {e}")
                results[indicator.value] = None

        return results


# 便捷函数
async def get_latest_sibor_rate(
    indicator: RateIndicator,
    use_mock: bool = True
) -> Optional[RateDataPoint]:
    """
    获取最新SIBOR利率

    Args:
        indicator: 利率指标
        use_mock: 是否使用模拟数据

    Returns:
        RateDataPoint或None
    """
    config = {
        'use_mock_data': use_mock
    }

    adapter = SIBORAdapter(config)
    async with adapter:
        return await adapter.fetch_latest_rate(indicator)


async def get_all_sibor_rates(
    use_mock: bool = True
) -> Dict[str, Optional[RateDataPoint]]:
    """
    获取所有SIBOR期限的最新利率

    Args:
        use_mock: 是否使用模拟数据

    Returns:
        各期限SIBOR利率字典
    """
    config = {
        'use_mock_data': use_mock
    }

    adapter = SIBORAdapter(config)
    async with adapter:
        return await adapter.fetch_all_sibor_rates()


# 测试代码
if __name__ == "__main__":
    async def test():
        # 测试获取SIBOR利率
        adapter = SIBORAdapter(config={'use_mock_data': True})

        async with adapter:
            # 获取所有SIBOR利率
            all_rates = await adapter.fetch_all_sibor_rates()

            print("\n=== SIBOR 利率 ===")
            for term, rate_data in all_rates.items():
                if rate_data:
                    print(f"{term}: {rate_data.value}%")

            # 获取特定期限
            sibor_1m = await adapter.fetch_latest_rate(RateIndicator.ONE_MONTH)
            print(f"\nSIBOR 1月: {sibor_1m.value if sibor_1m else 'N/A'}%")

    asyncio.run(test())
