"""
HKEX数据适配器 (修复版) - 港交所股票数据获取

修复API响应解析逻辑
支持获取HSI成分股、恒生指数等港股数据
"""

from typing import Dict, List, Optional
import pandas as pd
import requests
from datetime import datetime, timedelta
import aiohttp
import asyncio
import logging

from .base_adapter import BaseAdapter


class HKEXAdapterFixed(BaseAdapter):
    """港交所数据适配器 (修复版)"""

    SUPPORTED_SYMBOLS = {
        '0700.HK': '腾讯控股',
        '0388.HK': '香港交易所',
        '1398.HK': '中国工商银行',
        '0939.HK': '中国建设银行',
        '3988.HK': '中国银行',
        '1299.HK': '友邦保险',
        '2318.HK': '中国平安',
        '3690.HK': '美团',
        '0941.HK': '中国移动',
        '0883.HK': '中国海洋石油',
    }

    def __init__(self):
        super().__init__("HKEXAdapterFixed")
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
        获取港股历史数据

        Args:
            symbol: 股票代码 (0700.HK, 0388.HK等)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            DataFrame with OHLCV data

        Raises:
            Exception: 当无法获取真实数据时
        """
        try:
            self.logger.info(f"获取{symbol}真实数据，从{start_date}到{end_date}")

            # 计算天数
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            duration_days = (end_dt - start_dt).days

            # 使用统一数据API
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}{self.endpoint}"
                params = {
                    "symbol": symbol.lower(),
                    "duration": max(duration_days, 1)  # 至少1天
                }

                self.logger.info(f"API请求: {url}?symbol={symbol.lower()}&duration={params['duration']}")

                async with session.get(url, params=params, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.logger.info(f"API响应: {list(data.keys())}")
                        return self._parse_hkex_response(data, symbol)
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

    def _parse_hkex_response(self, data: Dict, symbol: str) -> pd.DataFrame:
        """
        解析HKEX API响应 (修复版)

        API返回格式:
        {
          "ts": 1761835888317,
          "data": {
            "open": {"2025-10-21T00:00:00+00:00": 643.0, ...},
            "high": {"2025-10-21T00:00:00+00:00": 644.0, ...},
            "low": {...},
            "close": {...},
            "volume": {...}
          }
        }

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
            if not isinstance(data, dict):
                raise Exception(f"响应数据不是字典格式: {type(data)}")

            if 'data' not in data:
                raise Exception(f"响应中没有找到'data'字段，可用字段: {list(data.keys())}")

            data_section = data['data']

            if not isinstance(data_section, dict):
                raise Exception(f"'data'字段不是字典格式: {type(data_section)}")

            # 检查必要的字段
            required_fields = ['open', 'high', 'low', 'close']
            missing_fields = [field for field in required_fields if field not in data_section]

            if missing_fields:
                raise Exception(f"缺少必要字段: {missing_fields}，可用字段: {list(data_section.keys())}")

            # 提取各个字段的数据
            open_prices = data_section['open']
            high_prices = data_section['high']
            low_prices = data_section['low']
            close_prices = data_section['close']
            volume_data = data_section.get('volume', {})

            if not isinstance(open_prices, dict):
                raise Exception(f"'open'字段不是字典格式: {type(open_prices)}")

            # 获取所有日期并排序
            all_dates = set(open_prices.keys()) | set(high_prices.keys()) | \
                       set(low_prices.keys()) | set(close_prices.keys())

            if not all_dates:
                raise Exception("没有找到任何价格数据")

            # 转换为日期格式并排序
            dates = sorted(all_dates)

            # 构建DataFrame
            all_data = []
            for date_str in dates:
                try:
                    # 解析日期
                    date_obj = pd.to_datetime(date_str)

                    # 获取价格数据
                    open_price = float(open_prices.get(date_str, 0))
                    high_price = float(high_prices.get(date_str, 0))
                    low_price = float(low_prices.get(date_str, 0))
                    close_price = float(close_prices.get(date_str, 0))
                    volume = int(volume_data.get(date_str, 0)) if volume_data else 0

                    # 跳过无效数据
                    if open_price <= 0 and high_price <= 0 and low_price <= 0 and close_price <= 0:
                        self.logger.warning(f"跳过无效数据: {date_str}")
                        continue

                    all_data.append({
                        'Date': date_obj,
                        'Open': open_price,
                        'High': high_price,
                        'Low': low_price,
                        'Close': close_price,
                        'Volume': volume
                    })

                except (ValueError, TypeError) as e:
                    self.logger.warning(f"跳过无效记录: {date_str}, 错误: {e}")
                    continue

            if not all_data:
                raise Exception("没有有效的记录")

            # 创建DataFrame并排序
            df = pd.DataFrame(all_data)
            df = df.sort_values('Date')
            df = df.reset_index(drop=True)

            # 标准化数据
            df = self.normalize_data(df)

            # 验证数据
            if self.validate_data(df):
                self.logger.info(f"成功解析{len(df)}条{symbol}真实数据")
                return df
            else:
                raise Exception("数据验证失败")

        except Exception as e:
            self.logger.error(f"解析HKEX响应失败: {e}")
            raise Exception(f"解析{symbol}数据失败: {e}")

    async def get_realtime_data(self, symbol: str, **kwargs) -> Dict:
        """
        获取港股实时价格

        Args:
            symbol: 股票代码

        Returns:
            实时价格数据
        """
        try:
            # 获取最新一天的数据作为实时数据
            today = datetime.now().strftime('%Y-%m-%d')
            yesterday = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')

            # 尝试获取最近5天的数据
            data = await self.fetch_data(symbol, yesterday, today)

            if not data.empty:
                latest = data.iloc[-1]
                return {
                    'symbol': symbol,
                    'price': float(latest['Close']),
                    'open': float(latest['Open']),
                    'high': float(latest['High']),
                    'low': float(latest['Low']),
                    'volume': int(latest['Volume']) if latest['Volume'] else 0,
                    'timestamp': latest['Date'].isoformat(),
                    'source': 'hkex-api'
                }
            else:
                raise Exception("未能获取到实时数据")

        except Exception as e:
            error_msg = f"获取{symbol}实时数据失败: {e}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    def get_supported_symbols(self) -> Dict:
        """获取支持的symbol列表"""
        return self.SUPPORTED_SYMBOLS

    async def get_stock_info(self, symbol: str) -> Dict:
        """
        获取股票信息

        Args:
            symbol: 股票代码

        Returns:
            股票信息
        """
        try:
            return {
                'symbol': symbol,
                'name': self.SUPPORTED_SYMBOLS.get(symbol, 'Unknown'),
                'exchange': 'HKEX',
                'market': 'Hong Kong',
                'currency': 'HKD',
                'api_source': 'hkex-unified-api'
            }
        except Exception as e:
            self.logger.warning(f"获取{symbol}信息失败: {e}")
            return {
                'symbol': symbol,
                'name': 'Unknown',
                'exchange': 'HKEX',
                'market': 'Hong Kong',
                'currency': 'HKD',
                'api_source': 'hkex-unified-api'
            }

    async def health_check(self) -> Dict:
        """
        健康检查

        Returns:
            健康状态字典
        """
        try:
            # 尝试获取一个常用股票的数据
            test_data = await self.fetch_data('0700.HK', '2024-01-01', '2024-01-05')

            return {
                'status': 'healthy',
                'adapter': self.name,
                'test_symbol': '0700.HK',
                'test_result': 'success',
                'data_points': len(test_data),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'status': 'unhealthy',
                'adapter': self.name,
                'test_symbol': '0700.HK',
                'test_result': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
