"""
Real-time HKEX Data Adapter
連接真實數據源 http://18.180.162.113:9191/inst/getInst
"""

import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger("hk_quant_system.realtime_hkex_adapter")


class RealtimeHKEXAdapter:
    """連接真實 HKEX 數據源的適配器"""

    API_BASE_URL = "http://18.180.162.113:9191"
    API_ENDPOINT = "/inst/getInst"
    DEFAULT_DURATION = 365  # 1 year
    TIMEOUT = 30

    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.realtime_hkex_adapter")
        self.cache = {}
        self.cache_ttl = 300  # 5 分鐘快取
        self.last_cache_time = {}

    def _normalize_symbol(self, symbol: str) -> str:
        """標準化股票代碼為小寫格式"""
        return symbol.lower()

    def _is_cache_valid(self, symbol: str) -> bool:
        """檢查快取是否有效"""
        if symbol not in self.last_cache_time:
            return False

        elapsed = (datetime.now() - self.last_cache_time[symbol]).total_seconds()
        return elapsed < self.cache_ttl

    def fetch_stock_data(
        self,
        symbol: str,
        duration: int = DEFAULT_DURATION
    ) -> Optional[Dict[str, Any]]:
        """
        獲取真實股票數據

        Args:
            symbol: 股票代碼 (e.g., "0700.hk")
            duration: 時間範圍（天數）

        Returns:
            包含股票信息的字典，或 None（如果失敗）
        """
        symbol = self._normalize_symbol(symbol)

        # 檢查快取
        if self._is_cache_valid(symbol) and symbol in self.cache:
            self.logger.debug(f"Using cached data for {symbol}")
            return self.cache[symbol]

        try:
            self.logger.info(f"Fetching real-time data for {symbol} (duration: {duration} days)")

            # 調用真實 API
            url = f"{self.API_BASE_URL}{self.API_ENDPOINT}"
            params = {
                "symbol": symbol,
                "duration": duration
            }

            response = requests.get(
                url,
                params=params,
                timeout=self.TIMEOUT
            )
            response.raise_for_status()

            api_data = response.json()

            # 解析 API 響應
            processed_data = self._process_api_response(symbol, api_data)

            # 快取結果
            self.cache[symbol] = processed_data
            self.last_cache_time[symbol] = datetime.now()

            self.logger.info(f"Successfully fetched data for {symbol}")
            return processed_data

        except requests.RequestException as e:
            self.logger.error(f"API request failed for {symbol}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error processing data for {symbol}: {e}")
            return None

    def _process_api_response(self, symbol: str, api_data: Dict) -> Dict[str, Any]:
        """
        處理 API 響應並提取最新價格數據

        Args:
            symbol: 股票代碼
            api_data: API 響應數據

        Returns:
            處理後的股票數據
        """
        try:
            data = api_data.get("data", {})

            # 提取最新的價格數據
            close_data = data.get("close", {})
            high_data = data.get("high", {})
            low_data = data.get("low", {})
            volume_data = data.get("volume", {})

            # 獲取最新日期的數據
            if not close_data:
                self.logger.warning(f"No close data available for {symbol}")
                return self._create_empty_response(symbol)

            # 取得最後一個交易日的數據
            dates = sorted(close_data.keys(), reverse=True)
            if not dates:
                return self._create_empty_response(symbol)

            latest_date = dates[0]

            last_price = float(close_data.get(latest_date, 0))
            high_price = float(high_data.get(latest_date, last_price))
            low_price = float(low_data.get(latest_date, last_price))
            volume = float(volume_data.get(latest_date, 0))

            # 計算變化
            if len(dates) > 1:
                prev_date = dates[1]
                prev_close = float(close_data.get(prev_date, last_price))
                change = last_price - prev_close
                change_percent = (change / prev_close * 100) if prev_close != 0 else 0
            else:
                change = 0
                change_percent = 0

            return {
                "symbol": symbol.upper(),
                "name": self._get_stock_name(symbol),
                "last_price": round(last_price, 2),
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "volume": int(volume),
                "market_cap": self._estimate_market_cap(symbol, last_price),
                "timestamp": self._parse_timestamp(latest_date),
                "data_source": "Real-time HKEX API",
                "last_update_date": latest_date
            }

        except Exception as e:
            self.logger.error(f"Error processing API response for {symbol}: {e}")
            return self._create_empty_response(symbol)

    def _create_empty_response(self, symbol: str) -> Dict[str, Any]:
        """創建空響應"""
        return {
            "symbol": symbol.upper(),
            "name": "Unknown Stock",
            "last_price": 0.0,
            "change": 0.0,
            "change_percent": 0.0,
            "high": 0.0,
            "low": 0.0,
            "volume": 0,
            "market_cap": "N/A",
            "timestamp": datetime.now().isoformat(),
            "data_source": "Real-time HKEX API",
            "note": "No data available for this symbol"
        }

    def _get_stock_name(self, symbol: str) -> str:
        """獲取股票名稱"""
        stock_names = {
            "0700.hk": "Tencent (騰訊)",
            "0939.hk": "China Construction Bank (中國建設銀行)",
            "0388.hk": "Hong Kong Exchanges (香港交易所)",
            "1398.hk": "ICBC (工商銀行)",
            "3988.hk": "Bank of China (中國銀行)",
        }
        return stock_names.get(symbol.lower(), f"Stock {symbol.upper()}")

    def _estimate_market_cap(self, symbol: str, price: float) -> str:
        """估計市值（基於行業平均）"""
        # 這些是估計值，實際應從另一個 API 獲取
        estimated_shares = {
            "0700.hk": 2_467_000_000,  # 騰訊
            "0939.hk": 173_000_000_000,  # 建設銀行
            "0388.hk": 790_000_000,  # HKEX
            "1398.hk": 318_000_000_000,  # ICBC
        }

        shares = estimated_shares.get(symbol.lower(), 1_000_000_000)
        market_cap = price * shares

        if market_cap >= 1_000_000_000_000:
            return f"{market_cap/1_000_000_000_000:.1f}T"
        elif market_cap >= 1_000_000_000:
            return f"{market_cap/1_000_000_000:.1f}B"
        else:
            return f"{market_cap/1_000_000:.1f}M"

    def _parse_timestamp(self, date_string: str) -> str:
        """解析日期字符串"""
        try:
            # 嘗試解析 ISO 格式的日期
            if "T" in date_string:
                dt = datetime.fromisoformat(date_string.replace("+00:00", ""))
            else:
                dt = datetime.strptime(date_string, "%Y-%m-%d")
            return dt.isoformat()
        except:
            return datetime.now().isoformat()

    def clear_cache(self):
        """清除快取"""
        self.cache.clear()
        self.last_cache_time.clear()
        self.logger.info("Cache cleared")


# 全局適配器實例
_adapter_instance = None


def get_adapter() -> RealtimeHKEXAdapter:
    """獲取適配器單例"""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = RealtimeHKEXAdapter()
    return _adapter_instance
