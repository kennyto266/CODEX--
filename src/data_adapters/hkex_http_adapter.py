"""
HKEX HTTP API 數據適配器 - 使用統一的 Curl/HTTP API

通過統一的 HTTP 端點獲取香港交易所(HKEX)實時市場數據
API: http://18.180.162.113:9191/inst/getInst
"""

import logging
import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
import requests
import pandas as pd
from decimal import Decimal

from .base_adapter import (
    BaseDataAdapter,
    DataAdapterConfig,
    RealMarketData,
    DataValidationResult,
    DataQuality,
    DataSourceType
)


class HKEXHttpAdapter(BaseDataAdapter):
    """香港交易所 HKEX HTTP API 數據適配器"""

    # API 配置
    API_BASE_URL = "http://18.180.162.113:9191"
    API_ENDPOINT = "/inst/getInst"

    # 恒生指數 40 個主要成分股
    MAJOR_STOCKS = {
        '0700': {'name': '騰訊控股', 'sector': '科技'},
        '0388': {'name': '香港交易所', 'sector': '金融'},
        '1398': {'name': '中國工商銀行', 'sector': '金融'},
        '0939': {'name': '中國建設銀行', 'sector': '金融'},
        '3988': {'name': '中國銀行', 'sector': '金融'},
        '2318': {'name': '中國平安', 'sector': '保險'},
        '0883': {'name': '中國石油', 'sector': '能源'},
        '0386': {'name': '中國石化', 'sector': '能源'},
        '0941': {'name': '中國移動', 'sector': '電信'},
        '0011': {'name': '恒生銀行', 'sector': '金融'},
        '1299': {'name': '友邦保險', 'sector': '保險'},
        '0005': {'name': '匯豐控股', 'sector': '金融'},
        '0001': {'name': '長和', 'sector': '綜合企業'},
        '0002': {'name': '中電控股', 'sector': '公用事業'},
        '0016': {'name': '新鴻基地產', 'sector': '房地產'},
        '0017': {'name': '新世界發展', 'sector': '房地產'},
        '0019': {'name': '太古股份公司甲', 'sector': '運輸'},
        '0023': {'name': '東亞銀行', 'sector': '金融'},
        '0066': {'name': '港鐵公司', 'sector': '運輸'},
        '0083': {'name': '信和置業', 'sector': '房地產'},
    }

    # 其他常見HKEX股票
    OTHER_COMMON_STOCKS = {
        '0175': {'name': '吉利汽車', 'sector': '汽車'},
        '0288': {'name': '恒安國際', 'sector': '消費品'},
        '0293': {'name': '國泰航空', 'sector': '運輸'},
        '0322': {'name': '中航科技', 'sector': '航空'},
        '0425': {'name': '嘉里建設', 'sector': '房地產'},
        '0688': {'name': '中國海外發展', 'sector': '房地產'},
        '0857': {'name': '中國石油股份', 'sector': '能源'},
        '0902': {'name': '華能國際', 'sector': '能源'},
        '0992': {'name': '聯想集團', 'sector': '科技'},
        '1088': {'name': '中國神華', 'sector': '能源'},
    }

    def __init__(self, config: Optional[DataAdapterConfig] = None):
        """
        初始化 HKEX HTTP API 適配器

        Args:
            config: 適配器配置，如果為 None 則使用默認配置
        """
        if config is None:
            config = DataAdapterConfig(
                source_type=DataSourceType.HTTP_API,
                source_path=self.API_BASE_URL,
                update_frequency=300,  # 5 分鐘更新一次
                max_retries=3,
                timeout=30,
                cache_enabled=True,
                cache_ttl=600,  # 10 分鐘緩存
                quality_threshold=0.8
            )
        else:
            config.source_type = DataSourceType.HTTP_API

        super().__init__(config)
        self.logger = logging.getLogger("hk_quant_system.hkex_http_adapter")

    async def connect(self) -> bool:
        """連接到 HKEX HTTP API"""
        try:
            self.logger.info("Connecting to HKEX HTTP API...")
            # 測試連接
            test_symbol = "0700"  # 騰訊
            test_response = await self._call_api(test_symbol, 365)

            if test_response:
                self.logger.info("✓ Successfully connected to HKEX HTTP API")
                return True
            else:
                self.logger.error("✗ Failed to connect to HKEX HTTP API")
                return False
        except Exception as e:
            self.logger.error(f"✗ Connection error: {e}")
            return False

    async def disconnect(self) -> bool:
        """斷開連接"""
        try:
            self.logger.info("Disconnecting from HKEX HTTP API...")
            return True
        except Exception as e:
            self.logger.error(f"Disconnection error: {e}")
            return False

    async def _call_api(self, symbol: str, duration: int) -> Optional[Dict]:
        """
        調用 HTTP API 獲取數據

        Args:
            symbol: 股票代碼 (不含 .hk, 例: "0700")
            duration: 時間跨度（天數）

        Returns:
            API 返回的 JSON 數據
        """
        try:
            # 確保符號是小寫
            symbol = symbol.lower()
            if not symbol.endswith('.hk'):
                symbol = f"{symbol}.hk"

            url = f"{self.API_BASE_URL}{self.API_ENDPOINT}"
            params = {
                "symbol": symbol,
                "duration": duration
            }

            self.logger.debug(f"Calling API: {url} with params: {params}")

            # 進行重試
            for attempt in range(self.config.max_retries):
                try:
                    response = requests.get(
                        url,
                        params=params,
                        timeout=self.config.timeout
                    )

                    if response.status_code == 200:
                        data = response.json()
                        self.logger.debug(f"Successfully fetched data for {symbol}")
                        return data
                    else:
                        self.logger.warning(
                            f"API returned status {response.status_code} for {symbol}"
                        )

                except requests.Timeout:
                    self.logger.warning(f"Timeout on attempt {attempt + 1}/{self.config.max_retries}")
                    if attempt < self.config.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        raise

                except Exception as e:
                    self.logger.warning(f"Error on attempt {attempt + 1}/{self.config.max_retries}: {e}")
                    if attempt < self.config.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                    else:
                        raise

            return None

        except Exception as e:
            self.logger.error(f"Error calling API for {symbol}: {e}")
            return None

    async def get_hkex_stock_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        獲取 HKEX 股票真實歷史數據

        Args:
            symbol: 股票代碼 (例: "0700" 或 "0700.hk")
            start_date: 開始日期 (注: API 使用 duration 參數)
            end_date: 結束日期

        Returns:
            OHLCV 數據 DataFrame
        """
        try:
            # 計算時間跨度
            duration = (end_date - start_date).days

            self.logger.info(
                f"Fetching HKEX data for {symbol} ({duration} days)"
            )

            # 清理符號
            symbol_clean = symbol.replace('.hk', '').lower()

            # 調用 API
            api_response = await self._call_api(symbol_clean, duration)

            if not api_response:
                self.logger.warning(f"No data found for {symbol}")
                return pd.DataFrame()

            # 解析 API 響應並轉換為 DataFrame
            df = self._parse_api_response(api_response)

            if df.empty:
                self.logger.warning(f"API response is empty for {symbol}")
                return df

            self.logger.info(f"✓ Successfully fetched {len(df)} data points for {symbol}")
            return df

        except Exception as e:
            self.logger.error(f"✗ Error fetching HKEX data for {symbol}: {e}")
            return pd.DataFrame()

    def _parse_api_response(self, response: Dict) -> pd.DataFrame:
        """
        解析 API 響應為 DataFrame

        Args:
            response: API 返回的 JSON 數據

        Returns:
            包含 OHLCV 數據的 DataFrame
        """
        try:
            # 假設 API 返回的格式包含時間序列數據
            # 需要根據實際 API 返回格式調整
            records = []

            # 提取數據點
            if isinstance(response, dict) and 'data' in response:
                data = response['data']
                if isinstance(data, list):
                    for item in data:
                        record = {
                            'date': pd.to_datetime(item.get('date', item.get('time'))),
                            'open': float(item.get('open', 0)),
                            'high': float(item.get('high', 0)),
                            'low': float(item.get('low', 0)),
                            'close': float(item.get('close', 0)),
                            'volume': int(item.get('volume', 0))
                        }
                        records.append(record)

            if records:
                df = pd.DataFrame(records)
                df = df.sort_values('date').reset_index(drop=True)
                return df
            else:
                return pd.DataFrame()

        except Exception as e:
            self.logger.error(f"Error parsing API response: {e}")
            return pd.DataFrame()

    async def get_market_data(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[RealMarketData]:
        """獲取市場數據（基類方法）"""
        try:
            # 檢查緩存
            cache_key = self.get_cache_key(symbol, start_date, end_date)
            cached_data = self.get_cache(cache_key)
            if cached_data:
                self.logger.debug(f"Using cached data for {symbol}")
                return cached_data

            # 設置默認日期範圍
            if not end_date:
                end_date = date.today()
            if not start_date:
                start_date = end_date - timedelta(days=365)

            # 獲取數據
            hist = await self.get_hkex_stock_data(symbol, start_date, end_date)

            if hist.empty:
                return []

            # 轉換為標準格式
            market_data = await self.transform_data(hist, symbol)

            # 驗證數據
            validation_result = await self.validate_data(market_data)
            if validation_result.quality_level in [DataQuality.POOR, DataQuality.UNKNOWN]:
                self.logger.warning(
                    f"Poor data quality for {symbol}: {validation_result.errors}"
                )

            # 緩存數據
            self.set_cache(cache_key, market_data)

            return market_data

        except Exception as e:
            self.logger.error(f"Error getting market data for {symbol}: {e}")
            return []

    async def transform_data(
        self,
        raw_data: pd.DataFrame,
        symbol: str
    ) -> List[RealMarketData]:
        """轉換原始數據為標準格式"""
        try:
            market_data = []

            for _, row in raw_data.iterrows():
                data_point = RealMarketData(
                    symbol=symbol,
                    timestamp=pd.Timestamp(row['date']).to_pydatetime(),
                    open_price=Decimal(str(row['open'])),
                    high_price=Decimal(str(row['high'])),
                    low_price=Decimal(str(row['low'])),
                    close_price=Decimal(str(row['close'])),
                    volume=int(row['volume']),
                    market_cap=None,
                    pe_ratio=None,
                    data_source="hkex_http_api",
                    quality_score=1.0,
                    last_updated=datetime.now()
                )
                market_data.append(data_point)

            return market_data

        except Exception as e:
            self.logger.error(f"Error transforming data: {e}")
            return []

    async def validate_data(
        self,
        data: List[RealMarketData]
    ) -> DataValidationResult:
        """驗證數據質量"""
        try:
            if not data:
                return DataValidationResult(
                    is_valid=False,
                    quality_score=0.0,
                    quality_level=DataQuality.POOR,
                    errors=["No data provided"],
                    warnings=[]
                )

            errors = []
            warnings = []

            # 檢查數據完整性和合理性
            for i, item in enumerate(data):
                if item.open_price <= 0 or item.high_price <= 0 or item.low_price <= 0 or item.close_price <= 0:
                    errors.append(f"Invalid price at index {i}")

                if item.high_price < item.low_price:
                    errors.append(f"High < Low at index {i}")

                if item.high_price < item.open_price or item.high_price < item.close_price:
                    errors.append(f"High price not highest at index {i}")

                if item.low_price > item.open_price or item.low_price > item.close_price:
                    errors.append(f"Low price not lowest at index {i}")

                if item.volume < 0:
                    errors.append(f"Negative volume at index {i}")

            # 計算質量評分
            quality_score = self.calculate_quality_score(data)
            quality_level = self.get_quality_level(quality_score)

            is_valid = len(errors) == 0 and quality_score >= self.config.quality_threshold

            return DataValidationResult(
                is_valid=is_valid,
                quality_score=quality_score,
                quality_level=quality_level,
                errors=errors,
                warnings=warnings,
                metadata={
                    "data_points": len(data),
                    "symbol": data[0].symbol if data else None,
                    "date_range": {
                        "start": str(data[0].timestamp) if data else None,
                        "end": str(data[-1].timestamp) if data else None
                    }
                }
            )

        except Exception as e:
            self.logger.error(f"Error validating data: {e}")
            return DataValidationResult(
                is_valid=False,
                quality_score=0.0,
                quality_level=DataQuality.UNKNOWN,
                errors=[f"Validation error: {str(e)}"],
                warnings=[]
            )

    def get_major_stocks(self) -> Dict[str, Dict[str, str]]:
        """獲取恒生指數主要成分股"""
        return self.MAJOR_STOCKS

    def get_all_stocks(self) -> Dict[str, Dict[str, str]]:
        """獲取所有股票列表"""
        return {**self.MAJOR_STOCKS, **self.OTHER_COMMON_STOCKS}
