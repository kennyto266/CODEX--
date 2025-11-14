"""
股票数据 API路由
使用Yahoo Finance提供真实股票行情数据
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import logging

# 導入Yahoo Finance適配器
import yfinance as yf

router = APIRouter(prefix="/stock", tags=["股票数据"])
logger = logging.getLogger("hk_quant_system.stock_api")


class StockQuote(BaseModel):
    """股票行情数据"""
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    volume: int
    currency: str
    market: str
    timestamp: str
    source: str = "Yahoo Finance"


class StockHistoryItem(BaseModel):
    """历史数据项"""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class StockHistoryResponse(BaseModel):
    """历史数据响应"""
    success: bool
    symbol: str
    data: List[StockHistoryItem]
    total: int
    period: str
    timestamp: str


@router.get("/{symbol}")
async def get_stock_quote(symbol: str) -> StockQuote:
    """
    获取股票实时行情

    - **symbol**: 股票代码，如 0700.HK, AAPL

    Returns:
        股票实时行情数据
    """
    try:
        logger.info(f"获取股票行情: {symbol}")

        # 使用yfinance获取股票数据
        ticker = yf.Ticker(symbol)
        info = ticker.info

        # 获取最新报价
        if 'currentPrice' in info:
            current_price = float(info['currentPrice'])
        elif 'regularMarketPrice' in info:
            current_price = float(info['regularMarketPrice'])
        else:
            # Fallback：获取最近的收盘价
            hist = ticker.history(period='1d')
            if not hist.empty:
                current_price = float(hist['Close'].iloc[-1])
            else:
                raise ValueError("无法获取股票价格")

        # 计算涨跌
        if 'regularMarketPreviousClose' in info and info['regularMarketPreviousClose']:
            prev_close = float(info['regularMarketPreviousClose'])
            change = current_price - prev_close
            change_percent = (change / prev_close) * 100
        else:
            change = 0.0
            change_percent = 0.0

        # 获取成交量
        if 'volume' in info and info['volume']:
            volume = int(info['volume'])
        elif 'regularMarketVolume' in info and info['regularMarketVolume']:
            volume = int(info['regularMarketVolume'])
        else:
            volume = 0

        # 获取公司名称
        if 'longName' in info:
            name = info['longName']
        elif 'shortName' in info:
            name = info['shortName']
        else:
            name = symbol

        # 获取货币
        currency = info.get('currency', 'HKD')

        # 确定市场
        if '.HK' in symbol.upper():
            market = '港股'
        elif '.SS' in symbol.upper() or '.SZ' in symbol.upper():
            market = 'A股'
        else:
            market = '美股'

        logger.info(f"成功获取股票数据: {symbol} = {current_price}")

        return StockQuote(
            symbol=symbol,
            name=name,
            price=round(current_price, 2),
            change=round(change, 2),
            change_percent=round(change_percent, 2),
            volume=volume,
            currency=currency,
            market=market,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"获取股票数据失败 {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取股票数据失败: {str(e)}"
        )


@router.get("/{symbol}/history")
async def get_stock_history(
    symbol: str,
    period: str = Query("1mo", regex="^(1d|5d|1mo|3mo|6mo|1y|2y|5y|10y|ytd|max)$")
) -> StockHistoryResponse:
    """
    获取股票历史数据

    - **symbol**: 股票代码
    - **period**: 时间周期 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)

    Returns:
        股票历史K线数据
    """
    try:
        logger.info(f"获取历史数据: {symbol}, 周期: {period}")

        # 使用yfinance获取历史数据
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)

        if hist.empty:
            raise ValueError("无法获取历史数据")

        # 转换数据格式
        history_items = []
        for date_index, row in hist.iterrows():
            history_items.append(StockHistoryItem(
                date=date_index.strftime('%Y-%m-%d'),
                open=round(float(row['Open']), 2),
                high=round(float(row['High']), 2),
                low=round(float(row['Low']), 2),
                close=round(float(row['Close']), 2),
                volume=int(row['Volume'])
            ))

        logger.info(f"成功获取历史数据: {symbol}, {len(history_items)}条记录")

        return StockHistoryResponse(
            success=True,
            symbol=symbol,
            data=history_items,
            total=len(history_items),
            period=period,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"获取历史数据失败 {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取历史数据失败: {str(e)}"
        )


@router.get("/{symbol}/info")
async def get_stock_info(symbol: str):
    """
    获取股票详细信息

    - **symbol**: 股票代码

    Returns:
        股票详细信息（市值、PE ratio等）
    """
    try:
        logger.info(f"获取股票信息: {symbol}")

        ticker = yf.Ticker(symbol)
        info = ticker.info

        # 提取关键信息
        stock_info = {
            "symbol": symbol,
            "name": info.get('longName', info.get('shortName', symbol)),
            "sector": info.get('sector', 'N/A'),
            "industry": info.get('industry', 'N/A'),
            "marketCap": info.get('marketCap', 0),
            "peRatio": info.get('forwardPE', info.get('trailingPE', None)),
            "dividendYield": info.get('dividendYield', 0),
            "52WeekHigh": info.get('fiftyTwoWeekHigh', None),
            "52WeekLow": info.get('fiftyTwoWeekLow', None),
            "averageVolume": info.get('averageVolume', 0),
            "currency": info.get('currency', 'HKD'),
            "exchange": info.get('exchange', 'HKEX'),
            "timestamp": datetime.now().isoformat(),
            "source": "Yahoo Finance"
        }

        logger.info(f"成功获取股票信息: {symbol}")

        return {
            "success": True,
            "data": stock_info
        }

    except Exception as e:
        logger.error(f"获取股票信息失败 {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取股票信息失败: {str(e)}"
        )
