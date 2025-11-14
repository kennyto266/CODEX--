"""
10大牛熊證成交 API路由
從HKEX爬蟲CSV數據提供10大牛熊證成交數據
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, date
import pandas as pd
import os

router = APIRouter(prefix="/top-cbbc", tags=["10大牛熊證成交"])

# CSV文件路徑
CSV_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../../../../hkex爬蟲/data/top_stocks/top_stocks_by_shares_all.csv"
)


class CBBCItem(BaseModel):
    """牛熊證數據項"""
    date: str
    rank: int
    code: str
    ticker: str
    product: str  # RP=熊證, RC=牛證
    name_chi: str
    currency: str
    shares_traded: int
    turnover_hkd: float
    high: float
    low: float
    cbbc_type: str  # 牛證/熊證
    issuer: str  # 發行商


class TopCBBCResponse(BaseModel):
    """10大牛熊證響應"""
    success: bool
    data: List[CBBCItem]
    total: int
    date: str
    timestamp: str
    source: str = "HKEX"


class CBBCStatsResponse(BaseModel):
    """牛熊證統計響應"""
    success: bool
    stats: dict
    timestamp: str


def _parse_cbbc_type(product: str) -> str:
    """解析牛熊證類型"""
    if product.startswith('RC'):
        return '牛證'
    elif product.startswith('RP'):
        return '熊證'
    return '未知'


def _parse_issuer(ticker: str) -> str:
    """解析發行商"""
    issuer_map = {
        'JP': '摩通',
        'UB': '瑞銀',
        'SG': '法興',
        'HS': '匯豐',
        'CI': '信證',
        'MS': '摩利',
        'BP': '法巴',
        'MB': '麥銀'
    }

    if '#' in ticker:
        issuer_code = ticker.split('#')[0]
        return issuer_map.get(issuer_code, issuer_code)
    return '未知'


@router.get("/latest", response_model=TopCBBCResponse)
async def get_latest_top_cbbc(limit: int = Query(10, ge=1, le=20)):
    """
    獲取最新的10大牛熊證成交數據

    - **limit**: 返回數量 (默認10，最多20)

    Returns:
        最新10大牛熊證成交數據
    """
    try:
        # 讀取CSV
        df = pd.read_csv(CSV_PATH)

        if df.empty:
            raise HTTPException(status_code=404, detail="沒有找到數據")

        # 獲取最新日期的數據
        latest_date = df['Date'].max()
        latest_df = df[df['Date'] == latest_date].head(limit)

        # 轉換為響應格式
        items = []
        for _, row in latest_df.iterrows():
            items.append(CBBCItem(
                date=str(row['Date']),
                rank=int(row['Rank']),
                code=str(row['Code']),
                ticker=str(row['Ticker']),
                product=str(row['Product']),
                name_chi=str(row['Name_CHI']),
                currency=str(row['Currency']),
                shares_traded=int(row['Shares_Traded']),
                turnover_hkd=float(row['Turnover_HKD']),
                high=float(row['High']),
                low=float(row['Low']),
                cbbc_type=_parse_cbbc_type(str(row['Product'])),
                issuer=_parse_issuer(str(row['Ticker']))
            ))

        return TopCBBCResponse(
            success=True,
            data=items,
            total=len(items),
            date=str(latest_date),
            timestamp=datetime.now().isoformat()
        )

    except FileNotFoundError:
        raise HTTPException(status_code=500, detail=f"找不到CSV文件: {CSV_PATH}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"讀取數據失敗: {str(e)}")


@router.get("/by-date/{target_date}", response_model=TopCBBCResponse)
async def get_top_cbbc_by_date(
    target_date: str,
    limit: int = Query(10, ge=1, le=20)
):
    """
    獲取指定日期的10大牛熊證成交數據

    - **target_date**: 日期 (格式: YYYY-MM-DD)
    - **limit**: 返回數量 (默認10，最多20)

    Returns:
        指定日期的10大牛熊證成交數據
    """
    try:
        # 讀取CSV
        df = pd.read_csv(CSV_PATH)

        # 篩選指定日期
        date_df = df[df['Date'] == target_date].head(limit)

        if date_df.empty:
            raise HTTPException(status_code=404, detail=f"沒有找到日期 {target_date} 的數據")

        # 轉換為響應格式
        items = []
        for _, row in date_df.iterrows():
            items.append(CBBCItem(
                date=str(row['Date']),
                rank=int(row['Rank']),
                code=str(row['Code']),
                ticker=str(row['Ticker']),
                product=str(row['Product']),
                name_chi=str(row['Name_CHI']),
                currency=str(row['Currency']),
                shares_traded=int(row['Shares_Traded']),
                turnover_hkd=float(row['Turnover_HKD']),
                high=float(row['High']),
                low=float(row['Low']),
                cbbc_type=_parse_cbbc_type(str(row['Product'])),
                issuer=_parse_issuer(str(row['Ticker']))
            ))

        return TopCBBCResponse(
            success=True,
            data=items,
            total=len(items),
            date=target_date,
            timestamp=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"讀取數據失敗: {str(e)}")


@router.get("/stats", response_model=CBBCStatsResponse)
async def get_cbbc_stats():
    """
    獲取牛熊證統計信息

    Returns:
        牛熊證統計數據 (牛證/熊證比例、發行商分佈等)
    """
    try:
        # 讀取CSV
        df = pd.read_csv(CSV_PATH)

        # 獲取最新日期的數據
        latest_date = str(df['Date'].max())
        latest_df = df[df['Date'] == latest_date].copy()  # Use .copy() to avoid SettingWithCopyWarning

        # 統計牛熊證類型
        latest_df['cbbc_type'] = latest_df['Product'].apply(_parse_cbbc_type)
        type_counts = {k: int(v) for k, v in latest_df['cbbc_type'].value_counts().to_dict().items()}

        # 統計發行商
        latest_df['issuer'] = latest_df['Ticker'].apply(_parse_issuer)
        issuer_counts = {k: int(v) for k, v in latest_df['issuer'].value_counts().to_dict().items()}

        # 計算總成交額 - 轉換為Python原生float
        total_turnover = float(latest_df['Turnover_HKD'].sum())
        bull_turnover = float(latest_df[latest_df['cbbc_type'] == '牛證']['Turnover_HKD'].sum())
        bear_turnover = float(latest_df[latest_df['cbbc_type'] == '熊證']['Turnover_HKD'].sum())

        # 牛熊比率
        bull_bear_ratio = float(bull_turnover / bear_turnover) if bear_turnover > 0 else 0.0

        # 市場情緒
        if bull_bear_ratio > 1.2:
            sentiment = {"label": "看多", "color": "green", "score": 8}
        elif bull_bear_ratio < 0.8:
            sentiment = {"label": "看空", "color": "red", "score": 3}
        else:
            sentiment = {"label": "中性", "color": "yellow", "score": 5}

        return CBBCStatsResponse(
            success=True,
            stats={
                "date": latest_date,
                "total_count": int(len(latest_df)),
                "type_distribution": type_counts,
                "issuer_distribution": issuer_counts,
                "turnover": {
                    "total": float(round(total_turnover, 2)),
                    "bull": float(round(bull_turnover, 2)),
                    "bear": float(round(bear_turnover, 2)),
                    "bull_bear_ratio": float(round(bull_bear_ratio, 2))
                },
                "sentiment": sentiment
            },
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"統計數據失敗: {str(e)}")


@router.get("/available-dates")
async def get_available_dates():
    """
    獲取所有可用的日期列表

    Returns:
        可用日期列表
    """
    try:
        df = pd.read_csv(CSV_PATH)
        dates = sorted(df['Date'].unique().tolist(), reverse=True)

        return {
            "success": True,
            "dates": dates,
            "total": len(dates),
            "latest": dates[0] if dates else None,
            "earliest": dates[-1] if dates else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取日期列表失敗: {str(e)}")


@router.get("/bull-bear-ratio-history")
async def get_bull_bear_ratio_history(days: int = Query(30, ge=7, le=365)):
    """
    獲取牛熊比率歷史數據

    - **days**: 查詢天數 (默認30天，最多365天)

    Returns:
        牛熊比率歷史走勢數據
    """
    try:
        # 讀取CSV
        df = pd.read_csv(CSV_PATH)

        # 獲取所有唯一日期並排序
        all_dates = sorted(df['Date'].unique().tolist(), reverse=True)

        # 限制查詢天數
        dates_to_query = all_dates[:days]

        # 計算每天的牛熊比率
        history = []
        for date_str in reversed(dates_to_query):  # 反轉以獲得時間順序
            date_df = df[df['Date'] == date_str].copy()

            # 統計牛熊證類型
            date_df['cbbc_type'] = date_df['Product'].apply(_parse_cbbc_type)

            # 計算成交額
            bull_turnover = float(date_df[date_df['cbbc_type'] == '牛證']['Turnover_HKD'].sum())
            bear_turnover = float(date_df[date_df['cbbc_type'] == '熊證']['Turnover_HKD'].sum())
            total_turnover = float(date_df['Turnover_HKD'].sum())

            # 計算牛熊比率
            bull_bear_ratio = float(bull_turnover / bear_turnover) if bear_turnover > 0 else 0.0

            # 計算牛證佔比
            bull_percentage = float((bull_turnover / total_turnover * 100)) if total_turnover > 0 else 0.0
            bear_percentage = float((bear_turnover / total_turnover * 100)) if total_turnover > 0 else 0.0

            # 市場情緒
            if bull_bear_ratio > 1.2:
                sentiment = "看多"
            elif bull_bear_ratio < 0.8:
                sentiment = "看空"
            else:
                sentiment = "中性"

            history.append({
                "date": date_str,
                "bull_bear_ratio": round(bull_bear_ratio, 2),
                "bull_turnover": round(bull_turnover / 1000000, 2),  # 轉換為百萬
                "bear_turnover": round(bear_turnover / 1000000, 2),
                "total_turnover": round(total_turnover / 1000000, 2),
                "bull_percentage": round(bull_percentage, 2),
                "bear_percentage": round(bear_percentage, 2),
                "sentiment": sentiment,
                "bull_count": int(len(date_df[date_df['cbbc_type'] == '牛證'])),
                "bear_count": int(len(date_df[date_df['cbbc_type'] == '熊證']))
            })

        # 計算統計數據
        ratios = [h['bull_bear_ratio'] for h in history]
        avg_ratio = sum(ratios) / len(ratios) if ratios else 0.0
        max_ratio = max(ratios) if ratios else 0.0
        min_ratio = min(ratios) if ratios else 0.0

        return {
            "success": True,
            "data": history,
            "total_days": len(history),
            "date_range": {
                "start": history[0]['date'] if history else None,
                "end": history[-1]['date'] if history else None
            },
            "statistics": {
                "avg_ratio": round(avg_ratio, 2),
                "max_ratio": round(max_ratio, 2),
                "min_ratio": round(min_ratio, 2),
                "current_ratio": history[-1]['bull_bear_ratio'] if history else 0.0
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取歷史數據失敗: {str(e)}")
