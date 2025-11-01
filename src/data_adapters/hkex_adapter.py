"""
HKEX 數據適配器 - 香港交易所實時市場數據

提供香港交易所(HKEX)上市股票的真實歷史數據和實時市場數據
支持恒生指數成分股和其他HKEX上市公司
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Tuple
import yfinance as yf
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


class HKEXAdapter(BaseDataAdapter):
    """香港交易所 HKEX 數據適配器"""

    # 恒生指數 40 個主要成分股
    MAJOR_STOCKS = {
        '0700.HK': {'name': '騰訊控股', 'sector': '科技'},
        '0388.HK': {'name': '香港交易所', 'sector': '金融'},
        '1398.HK': {'name': '中國工商銀行', 'sector': '金融'},
        '0939.HK': {'name': '中國建設銀行', 'sector': '金融'},
        '3988.HK': {'name': '中國銀行', 'sector': '金融'},
        '2318.HK': {'name': '中國平安', 'sector': '保險'},
        '0883.HK': {'name': '中國石油', 'sector': '能源'},
        '0386.HK': {'name': '中國石化', 'sector': '能源'},
        '0941.HK': {'name': '中國移動', 'sector': '電信'},
        '0011.HK': {'name': '恒生銀行', 'sector': '金融'},
        '1299.HK': {'name': '友邦保險', 'sector': '保險'},
        '0005.HK': {'name': '匯豐控股', 'sector': '金融'},
        '0001.HK': {'name': '長和', 'sector': '綜合企業'},
        '0002.HK': {'name': '中電控股', 'sector': '公用事業'},
        '0016.HK': {'name': '新鴻基地產', 'sector': '房地產'},
        '0017.HK': {'name': '新世界發展', 'sector': '房地產'},
        '0019.HK': {'name': '太古股份公司甲', 'sector': '運輸'},
        '0023.HK': {'name': '東亞銀行', 'sector': '金融'},
        '0066.HK': {'name': '港鐵公司', 'sector': '運輸'},
        '0083.HK': {'name': '信和置業', 'sector': '房地產'},
    }

    # 其他常見HKEX股票
    OTHER_COMMON_STOCKS = {
        '0175.HK': {'name': '吉利汽車', 'sector': '汽車'},
        '0288.HK': {'name': '恒安國際', 'sector': '消費品'},
        '0293.HK': {'name': '國泰航空', 'sector': '運輸'},
        '0322.HK': {'name': '中航科技', 'sector': '航空'},
        '0425.HK': {'name': '嘉里建設', 'sector': '房地產'},
        '0688.HK': {'name': '中國海外發展', 'sector': '房地產'},
        '0857.HK': {'name': '中國石油股份', 'sector': '能源'},
        '0902.HK': {'name': '華能國際', 'sector': '能源'},
        '0992.HK': {'name': '聯想集團', 'sector': '科技'},
        '1088.HK': {'name': '中國神華', 'sector': '能源'},
    }

    def __init__(self, config: Optional[DataAdapterConfig] = None):
        """
        初始化HKEX適配器

        Args:
            config: 適配器配置，如果為None則使用默認配置
        """
        if config is None:
            config = DataAdapterConfig(
                source_type=DataSourceType.YAHOO_FINANCE,
                source_path="https://finance.yahoo.com",
                update_frequency=300,  # 5分鐘更新一次
                max_retries=3,
                timeout=30,
                cache_enabled=True,
                cache_ttl=600,  # 10分鐘緩存
                quality_threshold=0.8
            )
        else:
            config.source_type = DataSourceType.YAHOO_FINANCE

        super().__init__(config)
        self.logger = logging.getLogger("hk_quant_system.hkex_adapter")

    async def connect(self) -> bool:
        """連接到HKEX數據源"""
        try:
            self.logger.info("Connecting to HKEX data source...")
            # 使用測試股票連接
            test_symbol = "0700.HK"  # 騰訊
            ticker = yf.Ticker(test_symbol)
            info = ticker.info
            if info:
                self.logger.info("✓ Successfully connected to HKEX")
                return True
            else:
                self.logger.error("✗ Failed to connect to HKEX")
                return False
        except Exception as e:
            self.logger.error(f"✗ Connection error: {e}")
            return False

    async def disconnect(self) -> bool:
        """斷開HKEX連接"""
        try:
            self.logger.info("Disconnecting from HKEX...")
            return True
        except Exception as e:
            self.logger.error(f"Disconnection error: {e}")
            return False

    async def get_hkex_stock_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        獲取HKEX股票真實歷史數據

        Args:
            symbol: 股票代碼 (例: "0700.HK")
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            OHLCV 數據 DataFrame
        """
        try:
            self.logger.info(f"Fetching HKEX data for {symbol} from {start_date} to {end_date}")

            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)

            if hist.empty:
                self.logger.warning(f"No data found for {symbol}")
                return pd.DataFrame()

            # 重置索引以便操作
            df = hist.reset_index()
            df.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'dividends', 'splits']

            # 只保留需要的列
            df = df[['date', 'open', 'high', 'low', 'close', 'volume']]

            self.logger.info(f"✓ Successfully fetched {len(df)} trading days for {symbol}")
            return df

        except Exception as e:
            self.logger.error(f"✗ Error fetching HKEX data for {symbol}: {e}")
            return pd.DataFrame()

    async def get_market_data(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[RealMarketData]:
        """
        獲取市場數據（基類方法）

        Args:
            symbol: 股票代碼
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            RealMarketData 列表
        """
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
                self.logger.warning(f"Poor data quality for {symbol}: {validation_result.errors}")

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
                # 獲取股票基本信息
                ticker = yf.Ticker(symbol)
                info = ticker.info

                data_point = RealMarketData(
                    symbol=symbol,
                    timestamp=pd.Timestamp(row['date']).to_pydatetime(),
                    open_price=Decimal(str(row['open'])),
                    high_price=Decimal(str(row['high'])),
                    low_price=Decimal(str(row['low'])),
                    close_price=Decimal(str(row['close'])),
                    volume=int(row['volume']),
                    market_cap=Decimal(str(info.get('marketCap', 0))) if info.get('marketCap') else None,
                    pe_ratio=Decimal(str(info.get('trailingPE', 0))) if info.get('trailingPE') else None,
                    data_source="hkex_yahoo_finance",
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
                # 檢查價格
                if item.open_price <= 0 or item.high_price <= 0 or item.low_price <= 0 or item.close_price <= 0:
                    errors.append(f"Invalid price at index {i}")

                # 檢查價格邏輯
                if item.high_price < item.low_price:
                    errors.append(f"High < Low at index {i}")

                if item.high_price < item.open_price or item.high_price < item.close_price:
                    errors.append(f"High price not highest at index {i}")

                if item.low_price > item.open_price or item.low_price > item.close_price:
                    errors.append(f"Low price not lowest at index {i}")

                # 檢查成交量
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

    def get_common_stocks(self) -> Dict[str, Dict[str, str]]:
        """獲取其他常見HKEX股票"""
        return self.OTHER_COMMON_STOCKS

    def get_all_stocks(self) -> Dict[str, Dict[str, str]]:
        """獲取所有股票列表"""
        return {**self.MAJOR_STOCKS, **self.OTHER_COMMON_STOCKS}

    async def get_sector_stocks(self, sector: str) -> Dict[str, Dict[str, str]]:
        """按行業獲取HKEX股票"""
        all_stocks = self.get_all_stocks()
        sector_stocks = {
            symbol: info
            for symbol, info in all_stocks.items()
            if info.get('sector') == sector
        }
        return sector_stocks

    async def get_all_sectors(self) -> List[str]:
        """獲取所有行業分類"""
        all_stocks = self.get_all_stocks()
        sectors = set()
        for info in all_stocks.values():
            if 'sector' in info:
                sectors.add(info['sector'])
        return sorted(list(sectors))

    async def backtest_stock(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        strategy_func=None
    ) -> Dict[str, Any]:
        """
        對HKEX股票進行簡單回測

        Args:
            symbol: 股票代碼
            start_date: 開始日期
            end_date: 結束日期
            strategy_func: 策略函數

        Returns:
            回測結果
        """
        try:
            # 獲取歷史數據
            df = await self.get_hkex_stock_data(symbol, start_date, end_date)

            if df.empty:
                self.logger.error(f"No data for backtest: {symbol}")
                return {
                    "symbol": symbol,
                    "status": "failed",
                    "error": "No data available"
                }

            # 計算基本指標
            initial_price = df['close'].iloc[0]
            final_price = df['close'].iloc[-1]
            total_return = (final_price - initial_price) / initial_price

            # 計算Sharpe比例
            returns = df['close'].pct_change()
            sharpe_ratio = returns.mean() / returns.std() * (252 ** 0.5) if returns.std() > 0 else 0

            # 計算最大回撤
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min()

            result = {
                "symbol": symbol,
                "start_date": str(start_date),
                "end_date": str(end_date),
                "trading_days": len(df),
                "initial_price": float(initial_price),
                "final_price": float(final_price),
                "total_return": float(total_return),
                "sharpe_ratio": float(sharpe_ratio),
                "max_drawdown": float(max_drawdown),
                "status": "success"
            }

            self.logger.info(f"Backtest completed for {symbol}")
            return result

        except Exception as e:
            self.logger.error(f"Error during backtest: {e}")
            return {
                "symbol": symbol,
                "status": "failed",
                "error": str(e)
            }

    async def get_sector_performance(
        self,
        sector: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        獲取行業性能統計

        Args:
            sector: 行業名稱
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            行業性能數據
        """
        try:
            sector_stocks = await self.get_sector_stocks(sector)

            if not sector_stocks:
                return {
                    "sector": sector,
                    "status": "failed",
                    "error": f"No stocks found for sector: {sector}"
                }

            results = []

            for symbol in sector_stocks.keys():
                df = await self.get_hkex_stock_data(symbol, start_date, end_date)

                if df.empty:
                    continue

                initial_price = df['close'].iloc[0]
                final_price = df['close'].iloc[-1]
                total_return = (final_price - initial_price) / initial_price

                results.append({
                    "symbol": symbol,
                    "name": sector_stocks[symbol].get('name'),
                    "return": float(total_return)
                })

            if results:
                avg_return = sum(r['return'] for r in results) / len(results)
                best_stock = max(results, key=lambda x: x['return'])
                worst_stock = min(results, key=lambda x: x['return'])

                return {
                    "sector": sector,
                    "stocks_count": len(results),
                    "average_return": float(avg_return),
                    "best_stock": best_stock,
                    "worst_stock": worst_stock,
                    "stocks": results,
                    "status": "success"
                }
            else:
                return {
                    "sector": sector,
                    "status": "failed",
                    "error": "Unable to fetch data for any stocks in sector"
                }

        except Exception as e:
            self.logger.error(f"Error getting sector performance: {e}")
            return {
                "sector": sector,
                "status": "failed",
                "error": str(e)
            }
