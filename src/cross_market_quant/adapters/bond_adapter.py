"""
债券数据适配器 - 国债收益率数据获取

使用统一数据API端点获取真实的债券收益率数据
支持US 10Y Treasury、US 2Y Treasury等债券收益率数据
"""

from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime, timedelta
import aiohttp
import asyncio

from .base_adapter import BaseAdapter


class BondAdapter(BaseAdapter):
    """债券数据适配器 - 仅使用真实数据源"""

    SUPPORTED_SYMBOLS = {
        'US_10Y': '美国10年期国债收益率',
        'US_2Y': '美国2年期国债收益率',
        'US_5Y': '美国5年期国债收益率',
        'US_30Y': '美国30年期国债收益率',
        'HK_10Y': '香港10年期政府债券收益率',
        'CN_10Y': '中国10年期国债收益率',
    }

    def __init__(self):
        super().__init__("BondAdapter")
        # 使用统一的数据API端点
        self.base_url = "http://18.180.162.113:9191"
        self.endpoint = "/inst/getInst"

    async def fetch_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        **kwargs
    ) -> pd.DataFrame:
        """
        获取债券收益率真实历史数据

        Args:
            symbol: 债券代码 (US_10Y, US_2Y等)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            DataFrame with Date and Yield columns

        Raises:
            Exception: 当无法获取真实数据时
        """
        try:
            self.logger.info(f"获取{symbol}真实数据，从{start_date}到{end_date}")

            # 计算天数
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            duration_days = (end_dt - start_dt).days

            # 使用统一数据API端点
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}{self.endpoint}"
                params = {
                    "symbol": symbol.lower(),
                    "duration": duration_days
                }

                self.logger.info(f"API请求: {url}?symbol={symbol.lower()}&duration={duration_days}")

                async with session.get(url, params=params, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_response(data, symbol)
                    else:
                        error_msg = f"API请求失败，状态码: {response.status}"
                        self.logger.error(error_msg)
                        raise Exception(error_msg)

        except aiohttp.ClientError as e:
            error_msg = f"网络请求失败: {e}"
            self.logger.error(error_msg)
            await self.handle_error(e)
            raise Exception(error_msg)
        except Exception as e:
            self.logger.error(f"获取{symbol}数据失败: {e}")
            await self.handle_error(e)
            raise Exception(f"无法获取{symbol}的真实数据: {e}")

    async def get_realtime_data(self, symbol: str, **kwargs) -> Dict:
        """
        获取实时债券收益率真实数据

        Args:
            symbol: 债券代码

        Returns:
            实时收益率数据

        Raises:
            Exception: 当无法获取真实数据时
        """
        try:
            # 获取最新一天的数据作为实时数据
            today = datetime.now().strftime('%Y-%m-%d')
            data = await self.fetch_data(symbol, today, today)

            if not data.empty:
                latest = data.iloc[-1]
                return {
                    'symbol': symbol,
                    'yield': float(latest['Close']),
                    'open': float(latest['Open']),
                    'high': float(latest['High']),
                    'low': float(latest['Low']),
                    'timestamp': latest['Date'].isoformat(),
                    'source': 'unified-api'
                }
            else:
                raise Exception("未能获取到实时数据")

        except Exception as e:
            error_msg = f"获取{symbol}实时数据失败: {e}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    def _parse_response(self, data: Dict, symbol: str) -> pd.DataFrame:
        """
        解析统一API响应

        Args:
            data: API响应数据
            symbol: 数据符号

        Returns:
            解析后的DataFrame

        Raises:
            Exception: 当解析失败时
        """
        try:
            if not isinstance(data, dict):
                raise Exception(f"响应数据格式错误，期望字典，得到: {type(data)}")

            # 尝试多种可能的响应格式
            records = None
            if 'data' in data:
                records = data['data']
            elif 'results' in data:
                records = data['results']
            elif isinstance(data, list):
                records = data
            else:
                raise Exception(f"无法找到数据记录，响应键: {list(data.keys())}")

            if not records or len(records) == 0:
                raise Exception("响应数据为空")

            all_data = []
            for record in records:
                try:
                    all_data.append({
                        'Date': pd.to_datetime(record.get('date', record.get('Date'))),
                        'Open': float(record.get('open', record.get('Open', 0))),
                        'High': float(record.get('high', record.get('High', 0))),
                        'Low': float(record.get('low', record.get('Low', 0))),
                        'Close': float(record.get('close', record.get('Close', 0))),
                        'Volume': int(record.get('volume', record.get('Volume', 0)))
                    })
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"跳过无效记录: {record}, 错误: {e}")
                    continue

            if not all_data:
                raise Exception("没有有效的记录")

            df = pd.DataFrame(all_data)
            df = self.normalize_data(df)

            if self.validate_data(df):
                self.logger.info(f"成功解析{len(df)}条{symbol}真实数据")
                return df
            else:
                raise Exception("数据验证失败")

        except Exception as e:
            self.logger.error(f"解析响应失败: {e}")
            raise Exception(f"解析{symbol}数据失败: {e}")

    async def calculate_yield_curve(self, date: str) -> pd.DataFrame:
        """
        计算指定日期的真实收益率曲线

        Args:
            date: 日期 (YYYY-MM-DD)

        Returns:
            收益率曲线数据

        Raises:
            Exception: 当无法获取真实数据时
        """
        try:
            self.logger.info(f"计算{date}的收益率曲线")

            # 获取不同期限的国债真实数据
            bonds = ['US_2Y', 'US_5Y', 'US_10Y', 'US_30Y']
            curve_data = []

            for bond_symbol in bonds:
                try:
                    data = await self.fetch_data(bond_symbol, date, date)
                    if not data.empty:
                        curve_data.append({
                            'Bond': bond_symbol,
                            'Maturity': self._get_maturity_years(bond_symbol),
                            'Yield': data.iloc[0]['Close']
                        })
                except Exception as e:
                    self.logger.warning(f"获取{bond_symbol}数据失败: {e}")
                    continue

            if not curve_data:
                raise Exception(f"未能获取到{date}的任何债券数据")

            return pd.DataFrame(curve_data)

        except Exception as e:
            self.logger.error(f"计算收益率曲线失败: {e}")
            raise Exception(f"计算{date}收益率曲线失败: {e}")

    def _get_maturity_years(self, symbol: str) -> int:
        """
        获取债券期限（年）

        Args:
            symbol: 债券代码

        Returns:
            期限（年）
        """
        maturity_map = {
            'US_2Y': 2,
            'US_5Y': 5,
            'US_10Y': 10,
            'US_30Y': 30,
            'HK_10Y': 10,
            'CN_10Y': 10,
        }
        return maturity_map.get(symbol, 10)

    async def calculate_bond_stock_correlation(
        self,
        bond_symbol: str,
        stock_symbol: str,
        start_date: str,
        end_date: str,
        window: int = 20
    ) -> pd.DataFrame:
        """
        计算债券收益率与股票的真实相关性

        Args:
            bond_symbol: 债券代码
            stock_symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            window: 滚动窗口

        Returns:
            包含相关性数据的DataFrame

        Raises:
            Exception: 当无法获取真实数据时
        """
        try:
            self.logger.info(f"计算{bond_symbol}与{stock_symbol}的相关性")

            # 获取债券真实数据
            bond_data = await self.fetch_data(bond_symbol, start_date, end_date)
            bond_yield_changes = bond_data['Close'].pct_change()

            # TODO: 需要接入真实的股票数据API
            raise NotImplementedError(
                "股票数据获取功能尚未实现，请接入真实的股票数据API"
            )

        except NotImplementedError as e:
            self.logger.warning(str(e))
            raise
        except Exception as e:
            self.logger.error(f"计算相关性失败: {e}")
            raise Exception(f"计算{bond_symbol}与{stock_symbol}相关性失败: {e}")
