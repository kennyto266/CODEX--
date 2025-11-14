"""
牛熊證 (CBBC) API路由
提供HKEX牛熊證成交數據
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import sys
import os

# 添加src目錄到路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../..'))

from src.scraping.hkex_cbbc_scraper import HKEXCBBCScraper


router = APIRouter(prefix="/api/v1/cbbc", tags=["牛熊證數據"])


class CBBCItem(BaseModel):
    """牛熊證數據模型"""
    rank: int
    code: str
    name: str
    type: str  # 牛證/熊證
    last_price: float
    change: float
    volume: int
    turnover: float
    strike: Optional[float] = None
    callable_price: Optional[float] = None
    expiry_date: Optional[str] = None
    underlying: Optional[str] = None
    issuer: Optional[str] = None
    outstanding: Optional[int] = None
    timestamp: str


class CBBCResponse(BaseModel):
    """牛熊證響應模型"""
    success: bool
    data: List[CBBCItem]
    total: int
    timestamp: str
    source: str = "HKEX"


class CBBCDetailResponse(BaseModel):
    """牛熊證詳情響應模型"""
    success: bool
    code: str
    name: str
    type: str
    details: dict
    timestamp: str


# 全局爬蟲實例
_scraper = None


def get_scraper() -> HKEXCBBCScraper:
    """獲取爬蟲實例（單例模式）"""
    global _scraper
    if _scraper is None:
        _scraper = HKEXCBBCScraper()
    return _scraper


@router.get("/top10", response_model=CBBCResponse)
async def get_top_10_cbbc(
    refresh: bool = Query(False, description="是否刷新數據")
):
    """
    獲取10大牛熊證成交數據

    - **refresh**: 是否強制刷新數據（默認False，使用緩存）

    Returns:
        10大牛熊證成交數據
    """
    try:
        scraper = get_scraper()

        # 獲取數據
        data = await scraper.get_top_10_cbbc()

        if not data:
            raise HTTPException(status_code=500, detail="無法獲取牛熊證數據")

        return CBBCResponse(
            success=True,
            data=[CBBCItem(**item) for item in data],
            total=len(data),
            timestamp=datetime.now().isoformat(),
            source="HKEX"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取牛熊證數據失敗: {str(e)}")


@router.get("/details/{code}", response_model=CBBCDetailResponse)
async def get_cbbc_details(code: str):
    """
    獲取單個牛熊證詳細信息

    - **code**: 牛熊證代碼

    Returns:
        牛熊證詳細信息
    """
    try:
        scraper = get_scraper()

        # 獲取詳情
        details = await scraper.get_cbbc_details(code)

        if not details:
            raise HTTPException(status_code=404, detail=f"找不到牛熊證: {code}")

        return CBBCDetailResponse(
            success=True,
            code=details['code'],
            name=details['name'],
            type=details['type'],
            details=details['details'],
            timestamp=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取牛熊證詳情失敗: {str(e)}")


@router.get("/types")
async def get_cbbc_types():
    """
    獲取牛熊證類型統計

    Returns:
        牛熊證類型分佈
    """
    try:
        scraper = get_scraper()
        data = await scraper.get_top_10_cbbc()

        # 統計牛證和熊證數量
        bull_count = sum(1 for item in data if item['type'] == '牛證')
        bear_count = sum(1 for item in data if item['type'] == '熊證')

        return {
            'success': True,
            'data': {
                'bull': {
                    'count': bull_count,
                    'percentage': round(bull_count / len(data) * 100, 2) if data else 0
                },
                'bear': {
                    'count': bear_count,
                    'percentage': round(bear_count / len(data) * 100, 2) if data else 0
                }
            },
            'total': len(data),
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取牛熊證類型統計失敗: {str(e)}")


@router.get("/market-sentiment")
async def get_market_sentiment():
    """
    根據牛熊證數據分析市場情緒

    Returns:
        市場情緒指標
    """
    try:
        scraper = get_scraper()
        data = await scraper.get_top_10_cbbc()

        if not data:
            raise HTTPException(status_code=500, detail="無法獲取數據")

        # 計算市場情緒指標
        bull_turnover = sum(item['turnover'] for item in data if item['type'] == '牛證')
        bear_turnover = sum(item['turnover'] for item in data if item['type'] == '熊證')
        total_turnover = bull_turnover + bear_turnover

        # 牛熊比率
        bull_bear_ratio = bull_turnover / bear_turnover if bear_turnover > 0 else 0

        # 市場情緒 (1-10)
        sentiment_score = min(10, max(1, 5 + (bull_bear_ratio - 1) * 2))

        # 情緒描述
        if sentiment_score >= 7:
            sentiment_label = "看多"
            sentiment_color = "green"
        elif sentiment_score <= 3:
            sentiment_label = "看空"
            sentiment_color = "red"
        else:
            sentiment_label = "中性"
            sentiment_color = "yellow"

        return {
            'success': True,
            'sentiment': {
                'score': round(sentiment_score, 2),
                'label': sentiment_label,
                'color': sentiment_color
            },
            'details': {
                'bull_turnover': round(bull_turnover, 2),
                'bear_turnover': round(bear_turnover, 2),
                'total_turnover': round(total_turnover, 2),
                'bull_bear_ratio': round(bull_bear_ratio, 2)
            },
            'timestamp': datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析市場情緒失敗: {str(e)}")


# 清理資源
@router.on_event("shutdown")
async def shutdown_event():
    """關閉時清理資源"""
    global _scraper
    if _scraper:
        await _scraper.close()
