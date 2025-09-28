"""
股票数据获取模块
基于hk_complete_system.py的数据获取逻辑重构
"""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class StockDataProvider:
    """股票数据提供者"""
    
    def __init__(self, api_base_url: str = "http://18.180.162.113:9191"):
        self.api_base_url = api_base_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def get_stock_data(self, symbol: str, duration: int = 1825) -> List[Dict[str, Any]]:
        """
        获取股票数据
        
        Args:
            symbol: 股票代码，如 "0700.HK"
            duration: 数据天数，默认1825天
            
        Returns:
            格式化的股票数据列表
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            url = f"{self.api_base_url}/inst/getInst"
            params = {
                "symbol": symbol,
                "duration": duration
            }
            
            logger.info(f"正在获取股票数据: {symbol}")
            
            async with self.session.get(url, params=params, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    formatted_data = self._format_market_data(data, symbol)
                    if formatted_data:
                        logger.info(f"成功获取 {len(formatted_data)} 条数据")
                        return formatted_data[-30:]  # 返回最近30天数据
                    else:
                        logger.error("数据格式化失败")
                        return []
                else:
                    logger.error(f"数据获取失败: HTTP {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"获取股票数据出错: {e}")
            return []
    
    def _format_market_data(self, raw_data: Dict[str, Any], symbol: str) -> List[Dict[str, Any]]:
        """
        格式化市场数据
        
        Args:
            raw_data: 原始API响应数据
            symbol: 股票代码
            
        Returns:
            格式化的数据列表
        """
        try:
            if not raw_data or 'data' not in raw_data:
                logger.error("原始数据格式不正确")
                return []
            
            data_dict = raw_data['data']
            required_fields = ['open', 'high', 'low', 'close', 'volume']
            missing_fields = [field for field in required_fields if field not in data_dict]
            
            if missing_fields:
                logger.error(f"缺少必要字段: {missing_fields}")
                return []
            
            # 获取所有日期
            dates = set()
            for field in required_fields:
                if isinstance(data_dict[field], dict):
                    dates.update(data_dict[field].keys())
            
            dates = sorted(list(dates))
            if len(dates) == 0:
                logger.error("没有找到交易日期")
                return []
            
            formatted_data = []
            for date in dates:
                try:
                    open_price = data_dict['open'].get(date, 0)
                    high_price = data_dict['high'].get(date, 0)
                    low_price = data_dict['low'].get(date, 0)
                    close_price = data_dict['close'].get(date, 0)
                    volume = data_dict['volume'].get(date, 0)
                    
                    # 跳过无效数据
                    if open_price == 0 and high_price == 0 and low_price == 0 and close_price == 0:
                        continue
                    
                    formatted_item = {
                        "symbol": symbol.upper(),
                        "timestamp": date,
                        "open": float(open_price),
                        "high": float(high_price),
                        "low": float(low_price),
                        "close": float(close_price),
                        "volume": int(volume)
                    }
                    formatted_data.append(formatted_item)
                    
                except Exception as e:
                    logger.warning(f"处理日期 {date} 时出错: {e}")
                    continue
            
            logger.info(f"成功格式化 {len(formatted_data)} 条数据")
            return formatted_data
            
        except Exception as e:
            logger.error(f"格式化数据出错: {e}")
            return []
    
    async def close(self):
        """关闭HTTP会话"""
        if self.session:
            await self.session.close()
            self.session = None
