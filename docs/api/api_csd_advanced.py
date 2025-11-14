#!/usr/bin/env python3
"""
C&SD Advanced API - Story 2.1.2b Implementation
C&SD統計數據API - 高級功能
支持失業率、零售銷售數據、數據對比分析、圖表數據導出
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np

from .models.api_response import APIResponse

logger = logging.getLogger(__name__)

# Pydantic Models

class UnemploymentData(BaseModel):
    """失業率數據"""
    date: str
    unemployment_rate: float
    labor_force: int
    unemployed: int
    employment_rate: float


class RetailSalesData(BaseModel):
    """零售銷售數據"""
    date: str
    total_sales: float
    clothing_sales: float
    supermarket_sales: float
    restaurant_sales: float
    electronics_sales: float
    yoy_growth: float


class DataComparison(BaseModel):
    """數據對比分析"""
    indicator1: str
    indicator2: str
    correlation: float
    significance: float
    analysis_period: str


class ChartDataPoint(BaseModel):
    """圖表數據點"""
    x: str
    y: float
    label: Optional[str] = None


class ChartData(BaseModel):
    """圖表數據"""
    chart_type: str
    title: str
    data: List[ChartDataPoint]
    x_axis: str
    y_axis: str


# Mock Data Generator
class MockCSDAdvancedData:
    """C&SD高級數據生成器"""

    def generate_unemployment_data(self, months: int = 36) -> List[UnemploymentData]:
        """生成失業率數據"""
        data = []
        current_date = datetime.now()
        base_rate = 3.2  # 基準失業率

        for month_offset in range(months):
            date = current_date - timedelta(days=30 * month_offset)

            # 模擬失業率變化
            import random
            random.seed(hash(date.strftime('%Y-%m')) % 1000)
            variation = random.uniform(-0.3, 0.3)
            rate = base_rate + variation

            # 計算勞動力數據
            labor_force = 3800000  # 香港勞動力
            unemployed_count = int(labor_force * rate / 100)
            employed_count = labor_force - unemployed_count
            employment_rate = (employed_count / labor_force) * 100

            data.append(UnemploymentData(
                date=date.strftime('%Y-%m'),
                unemployment_rate=round(rate, 2),
                labor_force=labor_force,
                unemployed=unemployed_count,
                employment_rate=round(employment_rate, 2)
            ))

        return sorted(data, key=lambda x: x.date, reverse=True)

    def generate_retail_sales_data(self, months: int = 36) -> List[RetailSalesData]:
        """生成零售銷售數據"""
        data = []
        current_date = datetime.now()
        base_sales = 45000  # 基準銷售額 (百萬港幣)

        for month_offset in range(months):
            date = current_date - timedelta(days=30 * month_offset)

            # 模擬銷售額變化
            import random
            random.seed(hash(date.strftime('%Y-%m')) % 1000)
            variation = random.uniform(-0.15, 0.15)
            total = base_sales * (1 + variation)

            # 各分類銷售額
            clothing = total * 0.25
            supermarket = total * 0.20
            restaurant = total * 0.30
            electronics = total * 0.15
            others = total * 0.10

            # 計算同比增長
            yoy_growth = random.uniform(-5, 8)

            data.append(RetailSalesData(
                date=date.strftime('%Y-%m'),
                total_sales=round(total, 2),
                clothing_sales=round(clothing, 2),
                supermarket_sales=round(supermarket, 2),
                restaurant_sales=round(restaurant, 2),
                electronics_sales=round(electronics, 2),
                yoy_growth=round(yoy_growth, 2)
            ))

        return sorted(data, key=lambda x: x.date, reverse=True)

    def generate_data_comparison(self, indicator1: str, indicator2: str, months: int = 24) -> DataComparison:
        """生成數據對比分析"""
        import random
        random.seed(hash(f"{indicator1}-{indicator2}") % 1000)

        # 計算模擬相關係數
        if "GDP" in indicator1 and "unemployment" in indicator2:
            correlation = -0.65  # GDP與失業率負相關
        elif "CPI" in indicator1 and "retail" in indicator2:
            correlation = 0.42  # CPI與零售正相關
        else:
            correlation = random.uniform(-0.8, 0.8)

        significance = 0.95 if abs(correlation) > 0.5 else 0.75

        return DataComparison(
            indicator1=indicator1,
            indicator2=indicator2,
            correlation=round(correlation, 3),
            significance=round(significance, 3),
            analysis_period=f"{months} months"
        )

    def generate_chart_data(self, indicator: str, months: int = 12) -> ChartData:
        """生成圖表數據"""
        data_points = []
        current_date = datetime.now()

        for month_offset in range(months):
            date = current_date - timedelta(days=30 * month_offset)

            import random
            random.seed(hash(f"{indicator}-{date.strftime('%Y-%m')}") % 1000)

            if "unemployment" in indicator.lower():
                value = 3.2 + random.uniform(-0.5, 0.5)
            elif "retail" in indicator.lower():
                value = 45000 + random.uniform(-5000, 8000)
            else:
                value = 100 + random.uniform(-10, 15)

            data_points.append(ChartDataPoint(
                x=date.strftime('%Y-%m'),
                y=round(value, 2),
                label=indicator
            ))

        data_points.sort(key=lambda x: x.x)

        chart_types = {
            "unemployment": "line",
            "retail": "bar",
            "gdp": "line",
            "cpi": "area"
        }

        chart_type = chart_types.get(indicator.lower().replace(" ", "_"), "line")

        return ChartData(
            chart_type=chart_type,
            title=f"{indicator} Trend Chart",
            data=data_points,
            x_axis="Time Period",
            y_axis="Value"
        )


# Initialize generator
generator = MockCSDAdvancedData()

# FastAPI Router
router = APIRouter(prefix="/api/v2/economic/advanced", tags=["economic_advanced"])

# Dependency
async def get_csd_advanced_adapter():
    return {
        "source": "Census and Statistics Department (Advanced)",
        "available": True
    }

@router.get("/unemployment", response_model=APIResponse)
async def get_unemployment_data(
    months: int = Query(default=36, ge=1, le=60, description="月數"),
    adapter: dict = Depends(get_csd_advanced_adapter)
):
    """獲取失業率數據"""
    try:
        unemployment_data = generator.generate_unemployment_data(months)

        return APIResponse(
            success=True,
            data={
                "indicator": "Unemployment Rate",
                "period": f"{months} months",
                "frequency": "Monthly",
                "data": [item.dict() for item in unemployment_data],
                "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            message=f"失業率數據查詢成功 (近{months}個月，共{len(unemployment_data)}條記錄)"
        )

    except Exception as e:
        logger.error(f"獲取失業率數據失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/retail-sales", response_model=APIResponse)
async def get_retail_sales_data(
    months: int = Query(default=36, ge=1, le=60, description="月數"),
    category: Optional[str] = Query(None, description="零售類別"),
    adapter: dict = Depends(get_csd_advanced_adapter)
):
    """獲取零售銷售數據"""
    try:
        retail_data = generator.generate_retail_sales_data(months)

        # 如果指定類別，過濾數據
        if category and category.lower() != "total":
            filtered_data = []
            for item in retail_data:
                if category.lower() == "clothing":
                    filtered_data.append({
                        "date": item.date,
                        "value": item.clothing_sales,
                        "category": "Clothing"
                    })
                elif category.lower() == "supermarket":
                    filtered_data.append({
                        "date": item.date,
                        "value": item.supermarket_sales,
                        "category": "Supermarket"
                    })

            return APIResponse(
                success=True,
                data={
                    "indicator": f"Retail Sales - {category}",
                    "period": f"{months} months",
                    "frequency": "Monthly",
                    "data": filtered_data,
                    "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                message=f"{category}零售數據查詢成功"
            )

        return APIResponse(
            success=True,
            data={
                "indicator": "Retail Sales",
                "period": f"{months} months",
                "frequency": "Monthly",
                "data": [item.dict() for item in retail_data],
                "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            message=f"零售銷售數據查詢成功 (近{months}個月，共{len(retail_data)}條記錄)"
        )

    except Exception as e:
        logger.error(f"獲取零售銷售數據失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comparison", response_model=APIResponse)
async def compare_indicators(
    indicator1: str = Query(..., description="指標1"),
    indicator2: str = Query(..., description="指標2"),
    months: int = Query(default=24, ge=6, le=60, description="分析月數"),
    adapter: dict = Depends(get_csd_advanced_adapter)
):
    """比較兩個指標的相關性"""
    try:
        comparison = generator.generate_data_comparison(indicator1, indicator2, months)

        return APIResponse(
            success=True,
            data=comparison.dict(),
            message=f"{indicator1} vs {indicator2} 相關性分析完成"
        )

    except Exception as e:
        logger.error(f"指標對比失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chart-data", response_model=APIResponse)
async def get_chart_data(
    indicator: str = Query(..., description="指標名稱"),
    chart_type: str = Query(default="line", description="圖表類型"),
    months: int = Query(default=12, ge=3, le=36, description="月數"),
    adapter: dict = Depends(get_csd_advanced_adapter)
):
    """獲取圖表數據"""
    try:
        chart_data = generator.generate_chart_data(indicator, months)

        return APIResponse(
            success=True,
            data=chart_data.dict(),
            message=f"{indicator} 圖表數據生成成功"
        )

    except Exception as e:
        logger.error(f"獲取圖表數據失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=APIResponse)
async def get_advanced_summary(
    adapter: dict = Depends(get_csd_advanced_adapter)
):
    """獲取高級分析概覽"""
    try:
        # 生成最新數據
        latest_unemployment = generator.generate_unemployment_data(1)[0]
        latest_retail = generator.generate_retail_sales_data(1)[0]

        summary = {
            "last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "key_indicators": {
                "unemployment_rate": {
                    "latest": latest_unemployment.unemployment_rate,
                    "trend": "stable",
                    "change_1m": -0.1
                },
                "retail_sales": {
                    "latest": latest_retail.total_sales,
                    "trend": "increasing",
                    "change_1m": 2.3,
                    "yoy_growth": latest_retail.yoy_growth
                }
            },
            "correlations": [
                {"indicators": "GDP vs Unemployment", "correlation": -0.65, "significance": "High"},
                {"indicators": "CPI vs Retail Sales", "correlation": 0.42, "significance": "Medium"}
            ],
            "alerts": [
                {"type": "info", "message": "失業率保持在低位", "severity": "low"},
                {"type": "warning", "message": "零售銷售增長放緩", "severity": "medium"}
            ]
        }

        return APIResponse(
            success=True,
            data=summary,
            message="C&SD高級分析概覽查詢成功"
        )

    except Exception as e:
        logger.error(f"獲取高級概覽失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=APIResponse)
async def advanced_economic_health(adapter: dict = Depends(get_csd_advanced_adapter)):
    """C&SD高級API健康檢查"""
    try:
        return APIResponse(
            success=True,
            data={
                "status": "healthy",
                "source": adapter["source"],
                "available": adapter["available"],
                "version": "2.1.2b",
                "features": [
                    "unemployment_data",
                    "retail_sales",
                    "indicator_comparison",
                    "chart_data",
                    "advanced_summary"
                ],
                "last_check": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            message="C&SD高級API健康狀態正常"
        )

    except Exception as e:
        logger.error(f"C&SD高級API健康檢查失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ['router']
