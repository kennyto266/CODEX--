"""
FRED债券数据适配器 - 使用FRED API获取真实债券数据

FRED (Federal Reserve Economic Data) 提供免费的美国债券收益率数据
支持美国国债、公司债等债券收益率数据
无需API密钥，完全免费
"""

from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime, timedelta
import aiohttp
import asyncio
import logging

from .base_adapter import BaseAdapter


class FREDBondAdapter(BaseAdapter):
    """FRED债券数据适配器 - 真实数据源"""

    # 支持的债券代码 (FRED Series IDs)
    SUPPORTED_SYMBOLS = {
        'US_10Y': 'DGS10 - 美国10年期国债收益率',
        'US_30Y': 'DGS30 - 美国30年期国债收益率',
        'US_2Y': 'DGS2 - 美国2年期国债收益率',
        'US_5Y': 'DGS5 - 美国5年期国债收益率',
        'US_7Y': 'DGS7 - 美国7年期国债收益率',
        'US_1M': 'DGS1MO - 美国1个月期国债收益率',
        'US_3M': 'DGS3MO - 美国3个月期国债收益率',
        'US_6M': 'DGS6MO - 美国6个月期国债收益率',
        'MORTGAGE_30YR': 'MORTGAGE30US - 30年期抵押贷款利率',
        'MORTGAGE_15YR': 'MORTGAGE15US - 15年期抵押贷款利率',
        'FED_FUNDS': 'FEDFUNDS - 联邦基金利率',
        'TREASURY_1Y': 'DGS1 - 美国1年期国债收益率',
        'TREASURY_20Y': 'DGS20 - 美国20年期国债收益率',
    }

    # 内部代码到FRED Series ID的映射
    FRED_SERIES_IDS = {
        'US_10Y': 'DGS10',
        'US_30Y': 'DGS30',
        'US_2Y': 'DGS2',
        'US_5Y': 'DGS5',
        'US_7Y': 'DGS7',
        'US_1M': 'DGS1MO',
        'US_3M': 'DGS3MO',
        'US_6M': 'DGS6MO',
        'MORTGAGE_30YR': 'MORTGAGE30US',
        'MORTGAGE_15YR': 'MORTGAGE15US',
        'FED_FUNDS': 'FEDFUNDS',
        'TREASURY_1Y': 'DGS1',
        'TREASURY_20Y': 'DGS20',
    }

    def __init__(self):
        super().__init__("FREDBondAdapter")
        # FRED API无需密钥
        self.base_url = 'https://api.stlouisfed.org/fred/series/observations'

    async def fetch_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        **kwargs
    ) -> pd.DataFrame:
        """
        获取债券真实历史收益率数据

        Args:
            symbol: 债券代码 (US_10Y, US_30Y等)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            DataFrame with OHLCV data
            Note: 债券数据通常只有收益率(OHLC中的Close表示收益率)

        Raises:
            Exception: 当无法获取真实数据时
        """
        try:
            self.logger.info(f"获取{symbol}真实数据，从{start_date}到{end_date}")

            # 获取FRED Series ID
            series_id = self._get_series_id(symbol)

            # 构建请求参数
            params = {
                'series_id': series_id,
                'api_key': 'demo',  # FRED允许demo模式
                'file_type': 'json',
                'observation_start': start_date,
                'observation_end': end_date,
                'frequency': 'd'  # 日频数据
            }

            self.logger.info(f"FRED API请求: {series_id}")

            # 发送请求
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()

                        # 检查是否有错误信息
                        if 'error_message' in data:
                            raise Exception(f"FRED API错误: {data['error_message']}")

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
            raise Exception(f"无法获取{symbol}的真实债券数据: {e}")

    async def get_realtime_data(self, symbol: str, **kwargs) -> Dict:
        """
        获取实时债券收益率数据

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
            yesterday = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

            # 尝试获取最近7天的数据
            data = await self.fetch_data(symbol, yesterday, today)

            if not data.empty:
                # 过滤掉空值
                valid_data = data[data['Close'].notna()]

                if not valid_data.empty:
                    latest = valid_data.iloc[-1]
                    return {
                        'symbol': symbol,
                        'rate': float(latest['Close']),
                        'open': float(latest['Open']) if pd.notna(latest['Open']) else float(latest['Close']),
                        'high': float(latest['High']) if pd.notna(latest['High']) else float(latest['Close']),
                        'low': float(latest['Low']) if pd.notna(latest['Low']) else float(latest['Close']),
                        'volume': 0,  # 债券通常没有成交量
                        'timestamp': latest['Date'].isoformat(),
                        'source': 'fred'
                    }
                else:
                    raise Exception("没有有效的收益率数据")

            else:
                raise Exception("未能获取到实时数据")

        except Exception as e:
            error_msg = f"获取{symbol}实时数据失败: {e}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    def _get_series_id(self, symbol: str) -> str:
        """
        获取FRED Series ID

        Args:
            symbol: 内部symbol

        Returns:
            FRED Series ID

        Raises:
            ValueError: 当symbol不支持时
        """
        if symbol in self.FRED_SERIES_IDS:
            return self.FRED_SERIES_IDS[symbol]
        else:
            # 尝试自动生成symbol（US_XX -> DGSXX）
            if symbol.startswith('US_') and symbol[3:].isdigit():
                years = symbol[3:]
                return f"DGS{years}"
            else:
                raise ValueError(f"不支持的债券symbol: {symbol}")

    def _parse_response(self, data: Dict, symbol: str) -> pd.DataFrame:
        """
        解析FRED API响应

        Args:
            data: API响应数据
            symbol: 数据符号

        Returns:
            解析后的DataFrame

        Raises:
            Exception: 当解析失败时
        """
        try:
            # 检查响应结构
            if 'observations' not in data:
                raise Exception(f"响应中没有找到observations数据")

            observations = data['observations']

            if not observations:
                raise Exception("observations数据为空")

            all_data = []
            for obs in observations:
                try:
                    # FRED返回的数据格式：date, value, realtime_start, realtime_end
                    date_str = obs.get('date')
                    value_str = obs.get('value')

                    # 跳过空值
                    if value_str == '.' or value_str == 'NaN' or not value_str:
                        continue

                    rate = float(value_str)

                    all_data.append({
                        'Date': pd.to_datetime(date_str),
                        'Open': rate,  # 债券数据通常只有收益率，使用Close值填充
                        'High': rate,
                        'Low': rate,
                        'Close': rate,
                        'Volume': 0  # 债券收益率没有成交量
                    })
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"跳过无效记录: {obs}, 错误: {e}")
                    continue

            if not all_data:
                raise Exception("没有有效的记录")

            df = pd.DataFrame(all_data)
            df = self.normalize_data(df)

            if self.validate_data(df):
                self.logger.info(f"成功解析{len(df)}条{symbol}真实数据（FRED）")
                return df
            else:
                raise Exception("数据验证失败")

        except Exception as e:
            self.logger.error(f"解析响应失败: {e}")
            raise Exception(f"解析{symbol}数据失败: {e}")

    async def calculate_bond_correlation(
        self,
        bond_symbol: str,
        stock_symbol: str,
        start_date: str,
        end_date: str,
        window: int = 20
    ) -> pd.DataFrame:
        """
        计算债券与股票的真实相关性

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
            bond_returns = bond_data['Close'].pct_change()

            # TODO: 需要接入真实的股票数据（使用HKEX适配器）
            raise NotImplementedError(
                "股票数据获取功能尚未完全实现，请使用HKEXAdapter获取港股数据"
            )

        except NotImplementedError as e:
            self.logger.warning(str(e))
            raise
        except Exception as e:
            self.logger.error(f"计算相关性失败: {e}")
            raise Exception(f"计算{bond_symbol}与{stock_symbol}相关性失败: {e}")

    def get_supported_symbols(self) -> Dict:
        """
        获取支持的symbol列表

        Returns:
            支持的symbol字典
        """
        return self.SUPPORTED_SYMBOLS

    async def get_bond_info(self, symbol: str) -> Dict:
        """
        获取债券信息

        Args:
            symbol: 债券代码

        Returns:
            债券信息
        """
        try:
            series_id = self._get_series_id(symbol)

            # 构建获取series信息的请求
            series_url = 'https://api.stlouisfed.org/fred/series'
            params = {
                'series_id': series_id,
                'api_key': 'demo',
                'file_type': 'json'
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(series_url, params=params, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()

                        if 'seriess' in data and data['seriess']:
                            series = data['seriess'][0]
                            return {
                                'symbol': symbol,
                                'series_id': series_id,
                                'title': series.get('title', 'N/A'),
                                'frequency': series.get('frequency', 'N/A'),
                                'units': series.get('units', 'N/A'),
                                'seasonal_adjustment': series.get('seasonal_adjustment', 'N/A'),
                                'last_updated': series.get('last_updated', 'N/A'),
                                'source': 'FRED'
                            }

            return {
                'symbol': symbol,
                'series_id': series_id,
                'title': 'N/A',
                'frequency': 'N/A',
                'units': 'N/A',
                'seasonal_adjustment': 'N/A',
                'last_updated': 'N/A',
                'source': 'FRED'
            }

        except Exception as e:
            self.logger.warning(f"获取{symbol}信息失败: {e}")
            return {
                'symbol': symbol,
                'series_id': 'N/A',
                'title': 'Unknown',
                'frequency': 'N/A',
                'units': 'N/A',
                'seasonal_adjustment': 'N/A',
                'last_updated': 'N/A',
                'source': 'FRED'
            }

    def get_yield_curve_data(self, date: str) -> Dict:
        """
        获取特定日期的收益率曲线数据

        Args:
            date: 日期 (YYYY-MM-DD)

        Returns:
            收益率曲线数据，包含不同期限的收益率

        Raises:
            Exception: 当获取失败时
        """
        # 这是一个简化版本，实际应用中可以异步获取所有期限的数据
        yield_curve_symbols = ['US_1M', 'US_3M', 'US_6M', 'US_1Y', 'US_2Y', 'US_5Y', 'US_7Y', 'US_10Y', 'US_20Y', 'US_30Y']
        yield_curve = {}

        for symbol in yield_curve_symbols:
            try:
                # 这里应该是异步获取，但为了简化，先同步处理
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                data = loop.run_until_complete(self.fetch_data(symbol, date, date))
                loop.close()

                if not data.empty and pd.notna(data.iloc[-1]['Close']):
                    yield_curve[symbol] = {
                        'maturity': self._get_maturity_years(symbol),
                        'yield': float(data.iloc[-1]['Close'])
                    }
            except Exception as e:
                self.logger.warning(f"获取{symbol}收益率失败: {e}")
                continue

        return {
            'date': date,
            'yield_curve': yield_curve,
            'source': 'FRED'
        }

    def _get_maturity_years(self, symbol: str) -> int:
        """获取债券期限（年）"""
        if symbol == 'US_1M':
            return 0.083
        elif symbol == 'US_3M':
            return 0.25
        elif symbol == 'US_6M':
            return 0.5
        elif symbol.startswith('US_') and symbol[3:].isdigit():
            return int(symbol[3:])
        else:
            return 0
