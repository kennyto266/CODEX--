"""
PBOC数据适配器
从中国人民银行(PBOC)获取利率和货币政策数据

支持的指标:
- 基准贷款利率 (LPR - Loan Prime Rate)
- 7天逆回购利率 (7-Day Reverse Repo)
- 中期借贷便利利率 (MLF - Medium-term Lending Facility)
- 常备借贷便利利率 (SLF - Standing Lending Facility)
- 存款准备金率 (RRR - Reserve Requirement Ratio)

数据来源:
- 中国人民银行官网: http://www.pbc.gov.cn/
- 中国利率网: http://www.chinamoney.com.cn/

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


class PBOCAdapter(BaseRateAdapter):
    """中国人民银行数据适配器"""

    ADAPTER_NAME = "People's Bank of China (PBOC)"
    DATA_SOURCE_URL = "http://www.pbc.gov.cn"
    DEFAULT_CURRENCY = Currency.CNY

    # PBOC支持的利率指标
    SUPPORTED_INDICATORS = {
        'lpr_1y': {
            'name': 'LPR 1年',
            'description': '贷款市场报价利率（1年期）'
        },
        'lpr_5y': {
            'name': 'LPR 5年',
            'description': '贷款市场报价利率（5年期以上）'
        },
        'repo_7d': {
            'name': '7天逆回购利率',
            'description': '7天期逆回购操作利率'
        },
        'mlf': {
            'name': '中期借贷便利利率',
            'description': 'MLF中期借贷便利利率'
        },
        'slf': {
            'name': '常备借贷便利利率',
            'description': 'SLF常备借贷便利利率'
        },
        'rrr': {
            'name': '存款准备金率',
            'description': '金融机构存款准备金率'
        },
        'overnight': {
            'name': '隔夜利率',
            'description': '银行间同业拆借利率（隔夜）'
        },
        '1w': {
            'name': '1周利率',
            'description': '银行间同业拆借利率（1周）'
        },
        '1m': {
            'name': '1月利率',
            'description': '银行间同业拆借利率（1月）'
        },
        '3m': {
            'name': '3月利率',
            'description': '银行间同业拆借利率（3月）'
        },
        '6m': {
            'name': '6月利率',
            'description': '银行间同业拆借利率（6月）'
        },
        '1y': {
            'name': '1年利率',
            'description': '银行间同业拆借利率（1年）'
        }
    }

    # 数据抓取URL
    LPR_URL = "http://www.pbc.gov.cn/goutongjiaoliu/135786/147995/index.html"
    SHIBOR_URL = "http://www.shibor.org/shibor/web/DataService.jsp"
    POLICY_RATE_URL = "http://www.pbc.gov.cn/goutongjiaoliu/135786/135871/index.html"

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化PBOC适配器

        Args:
            config: 配置字典
                - use_mock_data: 是否使用模拟数据（默认: True）
                - data_source: 数据源选择 ('lpr', 'shibor', 'policy')
        """
        super().__init__(config)

        self.data_source = self.config.get('data_source', 'mock')
        if self.use_mock_data:
            logger.info("使用模拟数据进行测试")

    async def _fetch_lpr_data(self) -> Optional[List[Dict]]:
        """获取LPR数据"""
        logger.info("正在获取LPR数据...")

        try:
            response = await self._make_request(self.LPR_URL)

            if not response:
                logger.error("获取LPR页面失败")
                return None

            html_content = await response.text()
            return self._parse_lpr_html(html_content)

        except Exception as e:
            logger.error(f"获取LPR数据失败: {e}")
            return None

    def _parse_lpr_html(self, html_content: str) -> Optional[List[Dict]]:
        """解析LPR HTML页面"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # 查找包含LPR数据的表格
            tables = soup.find_all('table')
            data = []

            for table in tables:
                rows = table.find_all('tr')

                for row in rows[1:]:  # 跳过标题行
                    cells = row.find_all(['td', 'th'])

                    if len(cells) >= 3:
                        try:
                            # 解析日期
                            date_str = cells[0].get_text(strip=True)
                            if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

                                # 解析1年期LPR
                                lpr_1y_text = cells[1].get_text(strip=True)
                                lpr_1y_match = re.search(r'(\d+\.?\d*)%', lpr_1y_text)

                                # 解析5年期LPR
                                lpr_5y_text = cells[2].get_text(strip=True)
                                lpr_5y_match = re.search(r'(\d+\.?\d*)%', lpr_5y_text)

                                if lpr_1y_match:
                                    data.append({
                                        'date': date_obj,
                                        'indicator': 'lpr_1y',
                                        'value': float(lpr_1y_match.group(1))
                                    })

                                if lpr_5y_match:
                                    data.append({
                                        'date': date_obj,
                                        'indicator': 'lpr_5y',
                                        'value': float(lpr_5y_match.group(1))
                                    })

                        except (ValueError, IndexError) as e:
                            logger.debug(f"跳过无效LPR行: {e}")
                            continue

            if data:
                logger.info(f"成功解析{len(data)}条LPR记录")
                return data

            return None

        except Exception as e:
            logger.error(f"解析LPR HTML失败: {e}")
            return None

    async def _fetch_shibor_data(self) -> Optional[List[Dict]]:
        """获取SHIBOR数据"""
        logger.info("正在获取SHIBOR数据...")

        try:
            # SHIBOR可能需要POST请求
            response = await self._make_request(
                self.SHIBOR_URL,
                method='POST',
                params={'type': 'Shibor'}
            )

            if not response:
                logger.error("获取SHIBOR数据失败")
                return None

            content = await response.text()

            # 尝试解析JSON格式
            if content.strip().startswith('{'):
                json_data = json.loads(content)
                return self._parse_shibor_json(json_data)
            else:
                # 可能是HTML格式
                return self._parse_shibor_html(content)

        except Exception as e:
            logger.error(f"获取SHIBOR数据失败: {e}")
            return None

    def _parse_shibor_json(self, json_data: Dict) -> Optional[List[Dict]]:
        """解析SHIBOR JSON数据"""
        try:
            data = []

            if 'data' in json_data:
                for item in json_data['data']:
                    if 'date' in item:
                        date_str = item['date']
                        if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

                            # 解析各期限SHIBOR
                            for term in ['1w', '1m', '3m', '6m', '1y']:
                                if term in item:
                                    try:
                                        value = float(item[term])
                                        data.append({
                                            'date': date_obj,
                                            'indicator': term,
                                            'value': value
                                        })
                                    except (ValueError, TypeError):
                                        continue

            if data:
                logger.info(f"成功解析{len(data)}条SHIBOR记录")
                return data

            return None

        except Exception as e:
            logger.error(f"解析SHIBOR JSON失败: {e}")
            return None

    def _parse_shibor_html(self, html_content: str) -> Optional[List[Dict]]:
        """解析SHIBOR HTML数据"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            data = []

            # 查找表格数据
            tables = soup.find_all('table')

            for table in tables:
                rows = table.find_all('tr')

                for row in rows[1:]:  # 跳过标题行
                    cells = row.find_all(['td', 'th'])

                    if len(cells) >= 6:
                        try:
                            # 日期通常在第一列
                            date_str = cells[0].get_text(strip=True)
                            if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

                                # 各期限利率
                                terms = ['1w', '1m', '3m', '6m', '1y']
                                for i, term in enumerate(terms):
                                    if i + 1 < len(cells):
                                        value_text = cells[i + 1].get_text(strip=True)
                                        if value_text and value_text != '-':
                                            try:
                                                value = float(value_text)
                                                data.append({
                                                    'date': date_obj,
                                                    'indicator': term,
                                                    'value': value
                                                })
                                            except (ValueError, TypeError):
                                                continue

                        except (ValueError, IndexError) as e:
                            logger.debug(f"跳过无效SHIBOR行: {e}")
                            continue

            if data:
                logger.info(f"成功解析{len(data)}条SHIBOR记录")
                return data

            return None

        except Exception as e:
            logger.error(f"解析SHIBOR HTML失败: {e}")
            return None

    async def _fetch_policy_rate_data(self) -> Optional[List[Dict]]:
        """获取货币政策利率数据"""
        logger.info("正在获取货币政策利率数据...")

        try:
            response = await self._make_request(self.POLICY_RATE_URL)

            if not response:
                logger.error("获取政策利率页面失败")
                return None

            html_content = await response.text()
            return self._parse_policy_rate_html(html_content)

        except Exception as e:
            logger.error(f"获取政策利率数据失败: {e}")
            return None

    def _parse_policy_rate_html(self, html_content: str) -> Optional[List[Dict]]:
        """解析政策利率HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            data = []

            # 查找包含政策利率的表格或列表
            tables = soup.find_all('table')

            for table in tables:
                rows = table.find_all('tr')

                for row in rows[1:]:  # 跳过标题行
                    cells = row.find_all(['td', 'th'])

                    if len(cells) >= 3:
                        try:
                            # 解析日期
                            date_str = cells[0].get_text(strip=True)
                            if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

                                # 解析利率名称和数值
                                for i in range(1, len(cells) - 1, 2):
                                    rate_name = cells[i].get_text(strip=True).lower()
                                    rate_value_text = cells[i + 1].get_text(strip=True)

                                    # 匹配不同类型的利率
                                    if 'mlf' in rate_name:
                                        value_match = re.search(r'(\d+\.?\d*)%', rate_value_text)
                                        if value_match:
                                            data.append({
                                                'date': date_obj,
                                                'indicator': 'mlf',
                                                'value': float(value_match.group(1))
                                            })
                                    elif 'slf' in rate_name:
                                        value_match = re.search(r'(\d+\.?\d*)%', rate_value_text)
                                        if value_match:
                                            data.append({
                                                'date': date_obj,
                                                'indicator': 'slf',
                                                'value': float(value_match.group(1))
                                            })

                        except (ValueError, IndexError) as e:
                            logger.debug(f"跳过无效政策利率行: {e}")
                            continue

            if data:
                logger.info(f"成功解析{len(data)}条政策利率记录")
                return data

            return None

        except Exception as e:
            logger.error(f"解析政策利率HTML失败: {e}")
            return None

    async def _fetch_generic_rate(
        self,
        indicator: RateIndicator
    ) -> Optional[RateDataPoint]:
        """获取通用利率"""
        try:
            # 根据指标类型选择数据源
            if indicator.value in ['lpr_1y', 'lpr_5y']:
                data_list = await self._fetch_lpr_data()
                indicator_key = indicator.value
            elif indicator.value in ['1w', '1m', '3m', '6m', '1y']:
                data_list = await self._fetch_shibor_data()
                indicator_key = indicator.value
            elif indicator.value in ['mlf', 'slf']:
                data_list = await self._fetch_policy_rate_data()
                indicator_key = indicator.value
            else:
                logger.warning(f"不支持的指标: {indicator}")
                return self._generate_mock_data(indicator, date.today())

            if not data_list:
                logger.warning(f"未获取到{indicator}数据，使用模拟数据")
                return self._generate_mock_data(indicator, date.today())

            # 查找最新数据
            filtered_data = [
                item for item in data_list
                if item['indicator'] == indicator_key
            ]

            if not filtered_data:
                logger.warning(f"未找到{indicator}指标数据，使用模拟数据")
                return self._generate_mock_data(indicator, date.today())

            # 按日期排序，获取最新数据
            filtered_data.sort(key=lambda x: x['date'])
            latest_data = filtered_data[-1]

            return RateDataPoint(
                indicator=indicator,
                currency=Currency.CNY,
                date=latest_data['date'],
                value=latest_data['value'],
                unit='%',
                source=self.ADAPTER_NAME,
                is_mock=self.use_mock_data
            )

        except Exception as e:
            logger.error(f"获取{indicator}失败: {e}")
            return self._generate_mock_data(indicator, date.today())

    async def _fetch_fed_funds_rate(self) -> Optional[RateDataPoint]:
        """PBOC不支持联邦基金利率，返回None"""
        logger.warning("PBOC不支持联邦基金利率")
        return None

    async def _fetch_discount_rate(self) -> Optional[RateDataPoint]:
        """获取贴现率（映射到SLF）"""
        indicator = RateIndicator.DISCOUNT_RATE

        try:
            data_list = await self._fetch_policy_rate_data()

            if not data_list:
                return self._generate_mock_data(indicator, date.today())

            # 查找SLF数据作为贴现率
            slf_data = [
                item for item in data_list
                if item['indicator'] == 'slf'
            ]

            if slf_data:
                slf_data.sort(key=lambda x: x['date'])
                latest_data = slf_data[-1]

                return RateDataPoint(
                    indicator=indicator,
                    currency=Currency.CNY,
                    date=latest_data['date'],
                    value=latest_data['value'],
                    unit='%',
                    source=self.ADAPTER_NAME,
                    is_mock=self.use_mock_data
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
        # 当前实现返回空，实际需要实现分页抓取
        logger.warning("PBOC历史数据抓取需要完整实现，当前使用模拟数据")

        # 生成模拟历史数据用于测试
        return self._generate_mock_historical(indicator, start_date, end_date)


# 便捷函数
async def get_latest_pboc_rate(
    indicator: RateIndicator,
    use_mock: bool = True
) -> Optional[RateDataPoint]:
    """
    获取最新PBOC利率

    Args:
        indicator: 利率指标
        use_mock: 是否使用模拟数据

    Returns:
        RateDataPoint或None
    """
    config = {
        'use_mock_data': use_mock
    }

    adapter = PBOCAdapter(config)
    async with adapter:
        return await adapter.fetch_latest_rate(indicator)


async def get_lpr_data(
    use_mock: bool = True
) -> Optional[List[RateDataPoint]]:
    """
    获取LPR数据

    Args:
        use_mock: 是否使用模拟数据

    Returns:
        LPR数据列表
    """
    config = {
        'use_mock_data': use_mock,
        'data_source': 'lpr'
    }

    adapter = PBOCAdapter(config)
    async with adapter:
        # 获取1年期和5年期LPR
        lpr_1y = await adapter.fetch_latest_rate(RateIndicator('lpr_1y'))
        lpr_5y = await adapter.fetch_latest_rate(RateIndicator('lpr_5y'))

        results = []
        if lpr_1y:
            results.append(lpr_1y)
        if lpr_5y:
            results.append(lpr_5y)

        return results


# 测试代码
if __name__ == "__main__":
    async def test():
        # 测试获取LPR利率
        adapter = PBOCAdapter(config={'use_mock_data': True})

        async with adapter:
            # 获取LPR利率
            lpr = await adapter.fetch_latest_rate(RateIndicator('lpr_1y'))
            print(f"LPR 1年期: {lpr.value if lpr else 'N/A'}%")

            # 获取SHIBOR
            shibor = await adapter.fetch_latest_rate(RateIndicator('1m'))
            print(f"SHIBOR 1月: {shibor.value if shibor else 'N/A'}%")

    asyncio.run(test())
