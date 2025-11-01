"""
LIHKG API 路由
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
import logging

from ..core.storage import LIHKGDataStore

logger = logging.getLogger('lihkg_scraper.api')
router = APIRouter()
data_store = LIHKGDataStore()

@router.get("/posts")
async def get_posts(
    category: Optional[int] = Query(None, description="板塊 ID (2=股票, 15=期貨)"),
    limit: int = Query(100, ge=1, le=1000, description="返回數量限制"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """
    獲取 LIHKG 帖子列表
    """
    try:
        posts = await data_store.get_recent_posts(category=category, limit=limit)
        
        # 應用偏移量 (簡化實現)
        if offset > 0 and offset < len(posts):
            posts = posts[offset:]
        
        return {
            "posts": posts,
            "total": len(posts),
            "category": category,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"獲取帖子列表失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sentiment")
async def get_sentiment(
    category: Optional[int] = Query(None, description="板塊 ID"),
    days: int = Query(7, ge=1, le=30, description="天數範圍")
):
    """
    獲取散戶情緒分析統計
    """
    try:
        posts = await data_store.get_recent_posts(category=category, limit=1000)
        
        # 計算情緒統計
        total = len(posts)
        positive = sum(1 for p in posts if p.get('sentiment_label') == 'positive')
        negative = sum(1 for p in posts if p.get('sentiment_label') == 'negative')
        neutral = sum(1 for p in posts if p.get('sentiment_label') == 'neutral')
        
        avg_sentiment = sum(p.get('sentiment_score', 0) for p in posts) / max(total, 1)
        
        return {
            "total_posts": total,
            "sentiment_distribution": {
                "positive": positive,
                "negative": negative,
                "neutral": neutral
            },
            "average_sentiment": round(avg_sentiment, 3),
            "period_days": days,
            "category": category
        }
    except Exception as e:
        logger.error(f"獲取情緒分析失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stocks")
async def get_trending_stocks(
    category: Optional[int] = Query(None, description="板塊 ID"),
    days: int = Query(7, ge=1, le=30, description="天數範圍"),
    limit: int = Query(20, ge=1, le=50, description="返回數量限制")
):
    """
    獲取熱門討論股票
    """
    try:
        trending = await data_store.get_trending_stocks(
            category=category,
            days=days,
            limit=limit
        )
        
        return {
            "trending_stocks": trending,
            "period_days": days,
            "category": category,
            "total_stocks": len(trending)
        }
    except Exception as e:
        logger.error(f"獲取熱門股票失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics")
async def get_statistics():
    """
    獲取系統統計數據
    """
    try:
        stats = await data_store.get_statistics()
        return stats
    except Exception as e:
        logger.error(f"獲取統計數據失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stock/{stock_code}")
async def get_stock_posts(
    stock_code: str,
    days: int = Query(7, ge=1, le=30, description="天數範圍")
):
    """
    獲取特定股票的討論和情緒
    """
    try:
        posts = await data_store.get_stock_sentiment(stock_code, days)
        
        return {
            "stock_code": stock_code,
            "posts": posts,
            "total_posts": len(posts),
            "period_days": days
        }
    except Exception as e:
        logger.error(f"獲取股票討論失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))
