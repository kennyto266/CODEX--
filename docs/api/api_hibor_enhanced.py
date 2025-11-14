#!/usr/bin/env python3
"""
Enhanced HIBOR API - Story 2.1.1 Implementation
擴展HIBOR API端點支持所有期限
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
import pandas as pd
import json

from .models.api_response import APIResponse

logger = logging.getLogger(__name__)

# Pydantic Models for Enhanced HIBOR API

class HiborRate(BaseModel):
    """HIBOR利率數據"""
    date: str
    overnight: Optional[float] = None
    one_week: Optional[float] = None
    one_month: Optional[float] = None
    three_months: Optional[float] = None
    six_months: Optional[float] = None
    twelve_months: Optional[float] = None


class HiborChange(BaseModel):
    """HIBOR變化數據"""
    overnight: Optional[float] = None
    one_week: Optional[float] = None
    one_month: Optional[float] = None
    three_months: Optional[float] = None
    six_months: Optional[float] = None
    twelve_months: Optional[float] = None


class HiborResponse(BaseModel):
    """HIBOR響應數據"""
    date: str
    rates: HiborRate
    changes: HiborChange


class HiborHistoryResponse(BaseModel):
    """HIBOR歷史數據響應"""
    data: List[HiborResponse]
    period: str
    total_records: int
    last_updated: str


class HiborCurrentResponse(BaseModel):
    """HIBOR當前數據響應"""
    current_rates: HiborRate
    last_update: str
    next_update: str


# Mock Data Generator for Demonstration
class MockHiborDataGenerator:
    """模擬HIBOR數據生成器（僅用於演示）"""

    def __init__(self):
        # 基準利率
        self.base_rates = {
            'overnight': 4.25,
            'one_week': 4.30,
            'one_month': 4.35,
            'three_months': 4.40,
            'six_months': 4.45,
            'twelve_months': 4.50
        }

    def generate_current_rates(self) -> HiborRate:
        """生成當前利率數據"""
        # 添加小隨機波動
        rates = {}
        for tenor, base_rate in self.base_rates.items():
            # 模擬日常波動（±0.1%）
            import random
            random.seed(hash(datetime.now().strftime('%Y-%m-%d')) % 1000)
            change = random.uniform(-0.1, 0.1)
            rates[tenor] = round(base_rate + change, 3)

        return HiborRate(
            date=datetime.now().strftime('%Y-%m-%d'),
            **rates
        )

    def generate_historical_data(self, days: int = 30) -> List[HiborResponse]:
        """生成歷史利率數據"""
        data = []
        base_date = datetime.now()

        for i in range(days):
            date = base_date - timedelta(days=i)
            if date.weekday() >= 5:  # 跳過週末
                continue

            rates = {}
            changes = {}

            for tenor, base_rate in self.base_rates.items():
                # 模擬歷史波動
                import random
                random.seed(hash(f"{date.strftime('%Y-%m-%d')}_{tenor}") % 1000)
                variation = random.uniform(-0.15, 0.15)
                rate = base_rate + variation
                rates[tenor] = round(rate, 3)

                # 計算日變化
                prev_rate = base_rate + random.uniform(-0.2, 0.2)
                change = round(rate - prev_rate, 3)
                changes[tenor] = change

            hibor_data = HiborResponse(
                date=date.strftime('%Y-%m-%d'),
                rates=HiborRate(date=date.strftime('%Y-%m-%d'), **rates),
                changes=HiborChange(**changes)
            )
            data.append(hibor_data)

        return data

# Initialize Mock Data Generator
mock_generator = MockHiborDataGenerator()

# FastAPI Router
router = APIRouter(prefix="/api/v2/hibor", tags=["hibor"])

# Dependency: Get HIBOR Adapter (placeholder)
async def get_hibor_adapter():
    """獲取HIBOR適配器（實際實現時連接真實數據源）"""
    # TODO: Replace with actual HKMA HIBOR adapter
    return {
        "source": "HKMA",
        "available": True
    }

@router.get("/current", response_model=APIResponse)
async def get_current_hibor(adapter: dict = Depends(get_hibor_adapter)):
    """獲取當前HIBOR利率（所有期限）"""
    try:
        current_rates = mock_generator.generate_current_rates()
        last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        next_update = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d 09:00:00')

        return APIResponse(
            success=True,
            data=HiborCurrentResponse(
                current_rates=current_rates,
                last_update=last_update,
                next_update=next_update
            ).dict(),
            message="當前HIBOR利率查詢成功"
        )

    except Exception as e:
        logger.error(f"獲取當前HIBOR利率失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=APIResponse)
async def get_hibor_history(
    start_date: str = Query(..., description="開始日期 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="結束日期 (YYYY-MM-DD)"),
    tenor: Optional[str] = Query(None, description="期限 (overnight, 1w, 1m, 3m, 6m, 12m)"),
    adapter: dict = Depends(get_hibor_adapter)
):
    """獲取HIBOR歷史數據"""
    try:
        # 計算天數
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        days = (end_dt - start_dt).days

        # 生成歷史數據
        historical_data = mock_generator.generate_historical_data(days)

        # 如果指定了期限，可以過濾數據
        if tenor:
            # TODO: 實現期限過濾邏輯
            pass

        return APIResponse(
            success=True,
            data=HiborHistoryResponse(
                data=[item.dict() for item in historical_data],
                period=f"{start_date} to {end_date}",
                total_records=len(historical_data),
                last_updated=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ).dict(),
            message=f"HIBOR歷史數據查詢成功 ({len(historical_data)} 條記錄)"
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式錯誤，請使用 YYYY-MM-DD 格式")
    except Exception as e:
        logger.error(f"獲取HIBOR歷史數據失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenors", response_model=APIResponse)
async def get_available_tenors():
    """獲取支持的HIBOR期限列表"""
    try:
        tenors = [
            {
                "code": "overnight",
                "name": "隔夜",
                "description": "香港銀行同業隔夜拆息",
                "unit": "%",
                "frequency": "每日"
            },
            {
                "code": "1w",
                "name": "1周",
                "description": "香港銀行同業1周拆息",
                "unit": "%",
                "frequency": "每日"
            },
            {
                "code": "1m",
                "name": "1個月",
                "description": "香港銀行同業1個月拆息",
                "unit": "%",
                "frequency": "每日"
            },
            {
                "code": "3m",
                "name": "3個月",
                "description": "香港銀行同業3個月拆息",
                "unit": "%",
                "frequency": "每日"
            },
            {
                "code": "6m",
                "name": "6個月",
                "description": "香港銀行同業6個月拆息",
                "unit": "%",
                "frequency": "每日"
            },
            {
                "code": "12m",
                "name": "12個月",
                "description": "香港銀行同業12個月拆息",
                "unit": "%",
                "frequency": "每日"
            }
        ]

        return APIResponse(
            success=True,
            data={
                "tenors": tenors,
                "total": len(tenors)
            },
            message="HIBOR期限列表查詢成功"
        )

    except Exception as e:
        logger.error(f"獲取HIBOR期限列表失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trend/{tenor}", response_model=APIResponse)
async def get_hibor_trend(
    tenor: str,
    period: str = Query(default="1M", description="期間 (1D, 1W, 1M, 3M, 6M, 1Y)"),
    adapter: dict = Depends(get_hibor_adapter)
):
    """獲取HIBOR利率趨勢分析"""
    try:
        # 根據期間計算天數
        period_days = {
            "1D": 1, "1W": 7, "1M": 30,
            "3M": 90, "6M": 180, "1Y": 365
        }

        days = period_days.get(period.upper(), 30)
        historical_data = mock_generator.generate_historical_data(days)

        # 計算趨勢
        if len(historical_data) >= 2:
            first_rate = getattr(historical_data[-1].rates, tenor, None)
            last_rate = getattr(historical_data[0].rates, tenor, None)

            if first_rate and last_rate:
                change = last_rate - first_rate
                change_pct = (change / first_rate) * 100
            else:
                change = 0
                change_pct = 0
        else:
            change = 0
            change_pct = 0

        # 判斷趨勢方向
        if change > 0.05:
            trend = "increasing"
        elif change < -0.05:
            trend = "decreasing"
        else:
            trend = "stable"

        return APIResponse(
            success=True,
            data={
                "tenor": tenor,
                "period": period,
                "trend": trend,
                "change": round(change, 4),
                "change_percentage": round(change_pct, 2),
                "data_points": len(historical_data),
                "analysis_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            message=f"{tenor} 期限HIBOR趨勢分析完成"
        )

    except Exception as e:
        logger.error(f"獲取HIBOR趨勢失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export", response_model=APIResponse)
async def export_hibor_data(
    start_date: str = Query(...),
    end_date: str = Query(...),
    format: str = Query(default="json", description="導出格式 (json/csv)"),
    adapter: dict = Depends(get_hibor_adapter)
):
    """導出HIBOR數據"""
    try:
        # 生成數據
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        days = (end_dt - start_dt).days
        historical_data = mock_generator.generate_historical_data(days)

        # 轉換為DataFrame
        export_data = []
        for item in historical_data:
            row = {
                "date": item.date,
                "overnight": item.rates.overnight,
                "one_week": item.rates.one_week,
                "one_month": item.rates.one_month,
                "three_months": item.rates.three_months,
                "six_months": item.rates.six_months,
                "twelve_months": item.rates.twelve_months
            }
            export_data.append(row)

        df = pd.DataFrame(export_data)

        if format.lower() == "csv":
            # 返回CSV格式
            csv_data = df.to_csv(index=False)
            return APIResponse(
                success=True,
                data={
                    "format": "csv",
                    "data": csv_data,
                    "filename": f"hibor_data_{start_date}_{end_date}.csv",
                    "records": len(df)
                },
                message=f"HIBOR數據CSV導出成功 ({len(df)} 條記錄)"
            )
        else:
            # 返回JSON格式
            return APIResponse(
                success=True,
                data={
                    "format": "json",
                    "data": export_data,
                    "filename": f"hibor_data_{start_date}_{end_date}.json",
                    "records": len(df)
                },
                message=f"HIBOR數據JSON導出成功 ({len(df)} 條記錄)"
            )

    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式錯誤")
    except Exception as e:
        logger.error(f"導出HIBOR數據失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Health Check Endpoint
@router.get("/health", response_model=APIResponse)
async def hibor_health_check(adapter: dict = Depends(get_hibor_adapter)):
    """HIBOR API健康檢查"""
    try:
        return APIResponse(
            success=True,
            data={
                "status": "healthy",
                "source": adapter.get("source", "HKMA"),
                "available": adapter.get("available", True),
                "version": "2.1.1",
                "last_check": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            message="HIBOR API健康狀態正常"
        )

    except Exception as e:
        logger.error(f"HIBOR健康檢查失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Export router
__all__ = ['router']
