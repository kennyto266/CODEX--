#!/usr/bin/env python3
"""
異步請求管理器
優化並發處理，提升系統性能
"""

import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AsyncRequestManager:
    """異步請求管理器"""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.connector = None
        self.default_timeout = 10.0
        self.max_concurrent = 100

    async def __aenter__(self):
        """異步上下文管理器進入"""
        await self.init_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器退出"""
        await self.close()

    async def init_session(self):
        """初始化HTTP會話和連接池"""
        if self.session is None or self.session.closed:
            self.connector = aiohttp.TCPConnector(
                limit=100,              # 連接池大小
                limit_per_host=30,       # 每主機連接數
                keepalive_timeout=60,     # keep-alive超時
                enable_cleanup_closed=True  # 啟用清理
            )

            timeout = aiohttp.ClientTimeout(
                connect=5.0,
                sock_read=10.0,
                total=30.0
            )

            self.session = aiohttp.ClientSession(
                connector=self.connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )

    async def close(self):
        """關閉會話"""
        if self.session and not self.session.closed:
            await self.session.close()
        if self.connector:
            await self.connector.close()

    async def fetch_multiple(self, requests: List[Dict]) -> List[Dict]:
        """並行獲取多個數據源"""
        if not requests:
            return []

        semaphore = asyncio.Semaphore(self.max_concurrent)
        tasks = [
            self._fetch_single(request, semaphore)
            for request in requests
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 處理結果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"請求 {i} 失敗: {result}")
                processed_results.append({
                    "request": requests[i],
                    "success": False,
                    "error": str(result),
                    "data": None,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                processed_results.append(result)

        return processed_results

    async def _fetch_single(self, request: Dict, semaphore: asyncio.Semaphore) -> Dict:
        """獲取單個數據源"""
        async with semaphore:
            start_time = datetime.now()

            try:
                url = request.get("url")
                method = request.get("method", "GET").upper()
                params = request.get("params", {})
                headers = request.get("headers", {})
                json_data = request.get("json")
                timeout = request.get("timeout", self.default_timeout)

                async with self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=headers,
                    json=json_data,
                    timeout=timeout
                ) as response:

                    response_time = (datetime.now() - start_time).total_seconds()

                    # 檢查狀態碼
                    if response.status == 200:
                        try:
                            data = await response.json()
                            return {
                                "request": request,
                                "success": True,
                                "data": data,
                                "status_code": response.status,
                                "response_time": response_time,
                                "timestamp": datetime.now().isoformat()
                            }
                        except Exception as e:
                            # JSON解析失敗，返回文本
                            text = await response.text()
                            return {
                                "request": request,
                                "success": True,
                                "data": {"text": text},
                                "status_code": response.status,
                                "response_time": response_time,
                                "timestamp": datetime.now().isoformat()
                            }
                    else:
                        return {
                            "request": request,
                            "success": False,
                            "error": f"HTTP {response.status}",
                            "status_code": response.status,
                            "response_time": response_time,
                            "timestamp": datetime.now().isoformat()
                        }

            except asyncio.TimeoutError:
                return {
                    "request": request,
                    "success": False,
                    "error": "TimeoutError",
                    "response_time": (datetime.now() - start_time).total_seconds(),
                    "timestamp": datetime.now().isoformat()
                }

            except Exception as e:
                logger.error(f"請求 {url} 失敗: {e}")
                return {
                    "request": request,
                    "success": False,
                    "error": str(e),
                    "response_time": (datetime.now() - start_time).total_seconds(),
                    "timestamp": datetime.now().isoformat()
                }

    async def fetch_with_retry(self, request: Dict, max_retries: int = 3) -> Dict:
        """帶重試的請求"""
        for attempt in range(max_retries):
            result = await self._fetch_single(request, asyncio.Semaphore(1))

            if result["success"]:
                return result

            # 等待後重試
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 指數退避
                logger.warning(f"請求失敗，{wait_time}秒後重試 (第{attempt+1}/{max_retries}次)")
                await asyncio.sleep(wait_time)

        return result


# 創建全局實例
async_request_manager = AsyncRequestManager()


class ConcurrentDataFetcher:
    """並發數據獲取器"""

    def __init__(self):
        self.request_manager = AsyncRequestManager()

    async def get_stock_and_weather(self, stock_symbol: str) -> Dict:
        """並行獲取股票和天氣數據"""
        requests = [
            {
                "url": "http://18.180.162.113:9191/inst/getInst",
                "params": {
                    "symbol": stock_symbol.lower(),
                    "duration": 30
                },
                "timeout": 10,
                "source": "stock"
            },
            {
                "url": "http://weather.gov.hk/wxinfo/currwx/fnday3e.xml",
                "timeout": 5,
                "source": "weather"
            }
        ]

        async with self.request_manager:
            results = await self.request_manager.fetch_multiple(requests)

        # 處理結果
        response = {
            "stock_data": None,
            "weather_data": None,
            "timestamp": datetime.now().isoformat(),
            "success_count": 0,
            "total_count": len(results)
        }

        for result in results:
            if result["success"]:
                response["success_count"] += 1
                source = result["request"]["source"]
                if source == "stock":
                    response["stock_data"] = result["data"]
                elif source == "weather":
                    response["weather_data"] = result["data"]

        return response

    async def get_sports_scores(self) -> List[Dict]:
        """並行獲取多種體育比分"""
        requests = [
            {
                "url": "https://bet.hkjc.com/ch/football/index.jsp",
                "timeout": 5,
                "source": "joker_soccer"
            },
            {
                "url": "https://www.espn.com/soccer/scoreboard",
                "timeout": 5,
                "source": "espn_soccer"
            },
            {
                "url": "https://www.basketball-reference.com/",
                "timeout": 5,
                "source": "basketball"
            }
        ]

        async with self.request_manager:
            results = await self.request_manager.fetch_multiple(requests)

        # 處理結果
        scores = []
        for result in results:
            if result["success"]:
                source = result["request"]["source"]
                scores.append({
                    "source": source,
                    "data": result["data"],
                    "response_time": result["response_time"],
                    "timestamp": result["timestamp"]
                })

        return scores

    async def get_multiple_markets(self, symbols: List[str]) -> Dict:
        """並行獲取多個市場數據"""
        requests = []
        for symbol in symbols:
            requests.append({
                "url": "http://18.180.162.113:9191/inst/getInst",
                "params": {
                    "symbol": symbol.lower(),
                    "duration": 30
                },
                "timeout": 8,
                "source": "stock",
                "symbol": symbol
            })

        async with self.request_manager:
            results = await self.request_manager.fetch_multiple(requests)

        # 處理結果
        market_data = {
            "markets": [],
            "success_count": 0,
            "timestamp": datetime.now().isoformat()
        }

        for result in results:
            symbol = result["request"]["symbol"]
            if result["success"]:
                market_data["success_count"] += 1
                market_data["markets"].append({
                    "symbol": symbol,
                    "data": result["data"],
                    "response_time": result["response_time"]
                })
            else:
                market_data["markets"].append({
                    "symbol": symbol,
                    "error": result["error"],
                    "response_time": result["response_time"]
                })

        return market_data
