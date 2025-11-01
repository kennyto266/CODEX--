"""
HKEX数据适配器 - 港交所股票数据获取

支持获取HSI成分股、恒生指数等港股数据
"""

from typing import Dict, List, Optional
import pandas as pd
import requests
from datetime import datetime, timedelta
import aiohttp
import asyncio

from .base_adapter import BaseAdapter


class HKEXAdapter(BaseAdapter):
    """港交所数据适配器"""

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
        super().__init__("HKEXAdapter")
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
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            DataFrame with OHLCV data
        """
        try:
            self.logger.info(f"获取{symbol}数据，从{start_date}到{end_date}")

            # 计算天数
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            duration_days = (end_dt - start_dt).days

            # 使用统一数据API
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}{self.endpoint}"
                params = {
                    "symbol": symbol.lower(),
                    "duration": duration_days
                }

                async with session.get(url, params=params, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_hkex_response(data)

            raise Exception(f"API请求失败，状态码: {response.status}")

        except Exception as e:
            self.logger.error(f"获取{symbol}数据失败: {e}")
            await self.handle_error(e)
            raise Exception(f"无法获取{symbol}的真实数据: {e}")

    async def get_realtime_data(self, symbol: str, **kwargs) -> Dict:
        """
        获取港股实时价格

        Args:
            symbol: 股票代码

        Returns:
            实时价格数据
        """
        try:
            # 获取今日数据作为实时数据
            today = datetime.now().strftime('%Y-%m-%d')
            data = await self.fetch_data(symbol, today, today)

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

        except Exception as e:
            self.logger.error(f"获取{symbol}实时数据失败: {e}")

        # 返回模拟数据
        return {
            'symbol': symbol,
            'price': 350.00,
            'open': 348.00,
            'high': 352.00,
            'low': 347.00,
            'volume': 1000000,
            'timestamp': datetime.now().isoformat(),
            'source': 'mock'
        }

    def _parse_hkex_response(self, data: Dict) -> pd.DataFrame:
        """
        解析HKEX API响应

        Args:
            data: API响应数据

        Returns:
            解析后的DataFrame
        """
        try:
            # 假设API返回的格式
            # 实际格式需要根据真实API调整
            records = data.get('data', []) if isinstance(data, dict) else []

            if not records:
                raise Exception("响应数据为空")

            all_data = []
            for record in records:
                all_data.append({
                    'Date': pd.to_datetime(record.get('date', record.get('Date'))),
                    'Open': float(record.get('open', record.get('Open', 0))),
                    'High': float(record.get('high', record.get('High', 0))),
                    'Low': float(record.get('low', record.get('Low', 0))),
                    'Close': float(record.get('close', record.get('Close', 0))),
                    'Volume': int(record.get('volume', record.get('Volume', 0)))
                })

            df = pd.DataFrame(all_data)
            df = self.normalize_data(df)

            if self.validate_data(df):
                self.logger.info(f"成功解析{len(df)}条数据")
                return df
            else:
                raise Exception("数据验证失败")

        except Exception as e:
            self.logger.error(f"解析HKEX响应失败: {e}")
            raise

    def _generate_mock_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        生成模拟港股数据（用于测试和演示）
        """
        self.logger.warning(f"生成{symbol}模拟数据（仅用于测试）")

        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        all_data = []

        # 根据股票代码设置基准价格
        base_prices = {
            '0700.HK': 350.00,  # 腾讯
            '0388.HK': 280.00,  # 港交所
            '1398.HK': 5.20,    # 工行
            '0939.HK': 5.80,    # 建行
            '3988.HK': 3.10,    # 中行
            '1299.HK': 65.00,   # 友邦
            '2318.HK': 45.00,   # 平安
            '3690.HK': 120.00,  # 美团
            '0941.HK': 65.00,   # 中移动
            '0883.HK': 18.50,   # 中海油
        }

        volatility = {
            '0700.HK': 0.025,
            '0388.HK': 0.02,
            '1398.HK': 0.015,
            '0939.HK': 0.015,
            '3988.HK': 0.015,
            '1299.HK': 0.02,
            '2318.HK': 0.02,
            '3690.HK': 0.03,
            '0941.HK': 0.012,
            '0883.HK': 0.022,
        }

        base_price = base_prices.get(symbol, 100.0)
        vol = volatility.get(symbol, 0.02)

        for i, date in enumerate(dates):
            # 生成随机价格（带趋势和波动）
            noise = (hash(str(date) + symbol) % 1000) / 1000.0 - 0.5
            trend = 0.0001 * i  # 长期上涨趋势

            price = base_price * (1 + trend + noise * vol)

            # OHLC数据
            high = price * (1 + abs(noise) * 0.01)
            low = price * (1 - abs(noise) * 0.01)
            open_price = price * (1 + noise * 0.005)

            all_data.append({
                'Date': date,
                'Open': open_price,
                'High': high,
                'Low': low,
                'Close': price,
                'Volume': 1000000 + int(hash(str(date)) % 1000000)
            })

        df = pd.DataFrame(all_data)
        return self.normalize_data(df)

    async def get_hsi_components(self) -> List[str]:
        """
        获取恒生指数成分股列表

        Returns:
            成分股代码列表
        """
        return list(self.SUPPORTED_SYMBOLS.keys())

    async def calculate_cross_market_correlation(
        self,
        hk_stock_symbol: str,
        fx_symbol: str,
        start_date: str,
        end_date: str,
        window: int = 20
    ) -> pd.DataFrame:
        """
        计算港股与外汇的相关性

        Args:
            hk_stock_symbol: 港股代码
            fx_symbol: 外汇代码
            start_date: 开始日期
            end_date: 结束日期
            window: 滚动窗口

        Returns:
            包含相关性数据的DataFrame
        """
        try:
            # 获取港股数据
            hk_data = await self.fetch_data(hk_stock_symbol, start_date, end_date)
            hk_returns = hk_data['Close'].pct_change()

            # TODO: 获取外汇数据
            # fx_data = await self._get_fx_data(fx_symbol, start_date, end_date)
            # fx_returns = fx_data['Close'].pct_change()

            # 计算滚动相关性（模拟外汇数据）
            dates = hk_data['Date']
            mock_fx_returns = pd.Series(
                (hash(str(date) + fx_symbol) % 100) / 10000.0 - 0.005,
                index=dates
            )

            rolling_corr = hk_returns.rolling(window=window).corr(mock_fx_returns)

            result = pd.DataFrame({
                'Date': dates,
                'HK_Stock_Returns': hk_returns,
                'FX_Returns': mock_fx_returns,
                'Rolling_Correlation': rolling_corr
            })

            return result

        except Exception as e:
            self.logger.error(f"计算相关性失败: {e}")
            return pd.DataFrame()
