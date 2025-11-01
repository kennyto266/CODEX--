"""
真實數據 pytest fixtures

提供使用真實 HKEX 歷史數據的 pytest fixtures，用於真實數據回測測試
"""

import pytest
import asyncio
from datetime import date, timedelta
import pandas as pd
import logging

# 導入真實數據適配器
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data_adapters.hkex_adapter import HKEXAdapter


logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def event_loop():
    """為異步測試提供事件循環"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def hkex_adapter():
    """HKEX 數據適配器 fixture"""
    adapter = HKEXAdapter()
    connected = await adapter.connect()
    if not connected:
        logger.warning("無法連接到 HKEX 數據源")
    yield adapter
    await adapter.disconnect()


@pytest.fixture
async def real_hkex_tencent_data():
    """
    騰訊 (0700.HK) 真實歷史數據

    返回: 過去 1 年的真實 OHLCV 數據
    """
    adapter = HKEXAdapter()
    await adapter.connect()

    end_date = date.today()
    start_date = end_date - timedelta(days=365)

    df = await adapter.get_hkex_stock_data("0700.HK", start_date, end_date)

    await adapter.disconnect()

    return df if not df.empty else pd.DataFrame()


@pytest.fixture
async def real_hkex_aex_data():
    """
    香港交易所 (0388.HK) 真實歷史數據

    返回: 過去 1 年的真實 OHLCV 數據
    """
    adapter = HKEXAdapter()
    await adapter.connect()

    end_date = date.today()
    start_date = end_date - timedelta(days=365)

    df = await adapter.get_hkex_stock_data("0388.HK", start_date, end_date)

    await adapter.disconnect()

    return df if not df.empty else pd.DataFrame()


@pytest.fixture
async def real_hkex_multiple_stocks_data():
    """
    多個 HKEX 股票的真實歷史數據

    返回: 字典 {symbol -> DataFrame}
    """
    adapter = HKEXAdapter()
    await adapter.connect()

    symbols = ["0700.HK", "0388.HK", "1398.HK"]  # 騰訊、香港交易所、工商銀行
    end_date = date.today()
    start_date = end_date - timedelta(days=365)

    data_dict = {}

    for symbol in symbols:
        df = await adapter.get_hkex_stock_data(symbol, start_date, end_date)
        data_dict[symbol] = df if not df.empty else pd.DataFrame()

    await adapter.disconnect()

    return data_dict


@pytest.fixture
async def real_market_data_tencent():
    """
    騰訊的 RealMarketData 對象列表

    返回: List[RealMarketData]
    """
    adapter = HKEXAdapter()
    await adapter.connect()

    end_date = date.today()
    start_date = end_date - timedelta(days=365)

    market_data = await adapter.get_market_data("0700.HK", start_date, end_date)

    await adapter.disconnect()

    return market_data


@pytest.fixture
async def real_backtest_data_1year():
    """
    適用於 1 年回測的真實數據

    返回: DataFrame with OHLCV data
    """
    adapter = HKEXAdapter()
    await adapter.connect()

    end_date = date.today()
    start_date = end_date - timedelta(days=365)

    # 使用騰訊作為回測數據
    df = await adapter.get_hkex_stock_data("0700.HK", start_date, end_date)

    await adapter.disconnect()

    if df.empty:
        # 如果無法獲取真實數據，返回空 DataFrame
        return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])

    return df


@pytest.fixture
async def real_backtest_data_90days():
    """
    適用於 90 天回測的真實數據

    返回: DataFrame with OHLCV data
    """
    adapter = HKEXAdapter()
    await adapter.connect()

    end_date = date.today()
    start_date = end_date - timedelta(days=90)

    df = await adapter.get_hkex_stock_data("0700.HK", start_date, end_date)

    await adapter.disconnect()

    if df.empty:
        return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])

    return df


@pytest.fixture
async def hkex_sector_stocks():
    """
    HKEX 按行業分類的股票

    返回: Dict[sector -> Dict[symbol -> info]]
    """
    adapter = HKEXAdapter()
    await adapter.connect()

    sectors = await adapter.get_all_sectors()
    sector_stocks = {}

    for sector in sectors:
        stocks = await adapter.get_sector_stocks(sector)
        sector_stocks[sector] = stocks

    await adapter.disconnect()

    return sector_stocks


@pytest.fixture
async def hkex_major_stocks_performance():
    """
    HKEX 主要成分股的性能數據

    返回: Dict with performance metrics for each stock
    """
    adapter = HKEXAdapter()
    await adapter.connect()

    major_stocks = adapter.get_major_stocks()
    end_date = date.today()
    start_date = end_date - timedelta(days=90)

    performance = {}

    for symbol in list(major_stocks.keys())[:5]:  # 只分析前 5 支股票以節省時間
        df = await adapter.get_hkex_stock_data(symbol, start_date, end_date)

        if not df.empty:
            performance[symbol] = {
                'name': major_stocks[symbol]['name'],
                'initial_price': float(df['close'].iloc[0]),
                'final_price': float(df['close'].iloc[-1]),
                'return': float((df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]),
                'high': float(df['high'].max()),
                'low': float(df['low'].min()),
                'avg_volume': float(df['volume'].mean())
            }

    await adapter.disconnect()

    return performance


@pytest.fixture
def real_data_start_date():
    """真實數據回測的開始日期"""
    return date.today() - timedelta(days=365)


@pytest.fixture
def real_data_end_date():
    """真實數據回測的結束日期"""
    return date.today()


@pytest.fixture
def hkex_symbols():
    """HKEX 主要股票符號列表"""
    return [
        '0700.HK',  # 騰訊
        '0388.HK',  # 香港交易所
        '1398.HK',  # 工商銀行
        '0939.HK',  # 建設銀行
        '3988.HK',  # 中國銀行
    ]


# 輔助函數


@pytest.fixture
async def backtest_with_real_data():
    """
    運行真實數據回測的輔助函數

    返回: async function for backtesting
    """
    async def run_backtest(symbol, strategy_func, start_date, end_date, **params):
        from src.backtest.real_data_backtest import RealDataBacktester

        backtester = RealDataBacktester(initial_capital=100000)
        results = await backtester.backtest_single_stock(
            symbol, strategy_func, start_date, end_date,
            strategy_name="test_strategy",
            **params
        )
        return results

    return run_backtest


@pytest.fixture
async def get_real_hkex_data():
    """
    獲取真實 HKEX 數據的輔助函數

    返回: async function for data fetching
    """
    async def fetch_data(symbol, start_date, end_date):
        adapter = HKEXAdapter()
        await adapter.connect()
        df = await adapter.get_hkex_stock_data(symbol, start_date, end_date)
        await adapter.disconnect()
        return df

    return fetch_data


# Session-wide 初始化和清理


@pytest.fixture(scope="session", autouse=True)
async def setup_real_data_tests():
    """
    為真實數據測試進行 session-wide 設置
    """
    logger.info("🔧 初始化真實數據測試...")

    adapter = HKEXAdapter()
    connected = await adapter.connect()

    if connected:
        logger.info("✓ 成功連接到 HKEX 數據源")
    else:
        logger.warning("⚠️ 無法連接到 HKEX 數據源，某些測試可能被跳過")

    await adapter.disconnect()

    yield

    logger.info("🔧 清理真實數據測試...")
