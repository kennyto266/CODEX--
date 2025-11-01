"""
爬虫数据 API 路由
整合 gov_crawler 和 HKEX 爬虫的数据
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/crawlers", tags=["crawlers"])


class CrawlerDataResponse(BaseModel):
    """爬虫数据响应模型"""
    success: bool
    source: str  # 'gov_crawler' or 'hkex'
    data_type: str  # 数据类型
    record_count: int
    data: Any
    timestamp: str
    last_updated: str


class CrawlerSummary(BaseModel):
    """爬虫数据摘要"""
    gov_crawler_status: Dict[str, Any]
    hkex_crawler_status: Dict[str, Any]
    total_records: int
    last_sync: str


def load_gov_crawler_data() -> Dict[str, Any]:
    """加载政府爬虫数据"""
    try:
        gov_dir = "gov_crawler/data"

        # 加载最新的综合数据
        all_data_files = sorted(
            [f for f in os.listdir(gov_dir) if f.startswith("all_alternative_data") and f.endswith(".json")],
            reverse=True
        )

        if all_data_files:
            with open(os.path.join(gov_dir, all_data_files[0]), 'r', encoding='utf-8') as f:
                return json.load(f)

        return {"status": "no_data", "message": "暂无政府数据"}
    except Exception as e:
        logger.error(f"加载政府爬虫数据失败: {e}")
        return {"status": "error", "message": str(e)}


def load_hkex_crawler_data() -> Dict[str, Any]:
    """加载HKEX爬虫数据"""
    try:
        hkex_dir = "hkex爬蟲/data"

        # 尝试加载HKEX综合数据
        if os.path.exists(os.path.join(hkex_dir, "hkex_all_market_data.csv")):
            import pandas as pd
            df = pd.read_csv(os.path.join(hkex_dir, "hkex_all_market_data.csv"))
            return {
                "status": "success",
                "records": len(df),
                "columns": list(df.columns),
                "sample_data": df.head(10).to_dict(orient='records')
            }

        # 加载最新的JSON数据
        json_files = sorted(
            [f for f in os.listdir(hkex_dir) if f.startswith("hkex_all_dates") and f.endswith(".json")],
            reverse=True
        )

        if json_files:
            with open(os.path.join(hkex_dir, json_files[0]), 'r', encoding='utf-8') as f:
                return json.load(f)

        return {"status": "no_data", "message": "暂无HKEX数据"}
    except Exception as e:
        logger.error(f"加载HKEX爬虫数据失败: {e}")
        return {"status": "error", "message": str(e)}


def classify_gov_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """分类政府爬虫数据"""
    classified = {
        "hibor_rates": [],
        "property_market": [],
        "retail_sales": [],
        "gdp_indicators": [],
        "visitor_arrivals": [],
        "trade_data": [],
        "traffic_flow": [],
        "mtr_passengers": [],
        "border_crossings": [],
        "metadata": {}
    }

    try:
        if isinstance(data, dict):
            # 按照数据源进行分类
            for key, value in data.items():
                if "hibor" in key.lower():
                    classified["hibor_rates"].append({key: value})
                elif "property" in key.lower():
                    classified["property_market"].append({key: value})
                elif "retail" in key.lower():
                    classified["retail_sales"].append({key: value})
                elif "gdp" in key.lower():
                    classified["gdp_indicators"].append({key: value})
                elif "visitor" in key.lower():
                    classified["visitor_arrivals"].append({key: value})
                elif "trade" in key.lower():
                    classified["trade_data"].append({key: value})
                elif "traffic" in key.lower():
                    classified["traffic_flow"].append({key: value})
                elif "mtr" in key.lower():
                    classified["mtr_passengers"].append({key: value})
                elif "border" in key.lower():
                    classified["border_crossings"].append({key: value})
                elif "meta" in key.lower():
                    classified["metadata"] = value

        return classified
    except Exception as e:
        logger.error(f"分类政府数据失败: {e}")
        return classified


@router.get("/gov-crawler/data", response_model=CrawlerDataResponse)
async def get_gov_crawler_data(data_type: Optional[str] = None):
    """
    获取政府爬虫数据
    data_type: hibor_rates, property_market, retail_sales, gdp_indicators, visitor_arrivals, trade_data, traffic_flow, mtr_passengers, border_crossings
    """
    try:
        raw_data = load_gov_crawler_data()
        classified_data = classify_gov_data(raw_data)

        # 如果指定了数据类型，返回该类型的数据
        if data_type and data_type in classified_data:
            filtered_data = classified_data[data_type]
        else:
            filtered_data = classified_data

        return CrawlerDataResponse(
            success=True,
            source="gov_crawler",
            data_type=data_type or "all",
            record_count=len(str(filtered_data)),
            data=filtered_data,
            timestamp=datetime.now().isoformat(),
            last_updated="2025-10-23"
        )
    except Exception as e:
        logger.error(f"获取政府爬虫数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hkex-crawler/data", response_model=CrawlerDataResponse)
async def get_hkex_crawler_data(limit: Optional[int] = 100):
    """
    获取HKEX爬虫数据
    limit: 返回的记录数限制
    """
    try:
        raw_data = load_hkex_crawler_data()

        # 如果有样本数据，限制返回数量
        if "sample_data" in raw_data and limit:
            raw_data["sample_data"] = raw_data["sample_data"][:limit]

        return CrawlerDataResponse(
            success=True,
            source="hkex",
            data_type="market_data",
            record_count=raw_data.get("records", len(str(raw_data))),
            data=raw_data,
            timestamp=datetime.now().isoformat(),
            last_updated="2025-10-20"
        )
    except Exception as e:
        logger.error(f"获取HKEX爬虫数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=CrawlerSummary)
async def get_crawler_summary():
    """获取爬虫数据摘要"""
    try:
        gov_data = load_gov_crawler_data()
        hkex_data = load_hkex_crawler_data()

        return CrawlerSummary(
            gov_crawler_status={
                "status": "active",
                "data_sources": len(gov_data) if isinstance(gov_data, dict) else 0,
                "last_updated": "2025-10-23"
            },
            hkex_crawler_status={
                "status": "active",
                "records": hkex_data.get("records", 0),
                "last_updated": "2025-10-20"
            },
            total_records=sum([
                len(gov_data) if isinstance(gov_data, dict) else 0,
                hkex_data.get("records", 0)
            ]),
            last_sync=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"获取爬虫摘要失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def crawler_health():
    """爬虫模块健康检查"""
    gov_ok = os.path.exists("gov_crawler/data")
    hkex_ok = os.path.exists("hkex爬蟲/data")

    return {
        "status": "healthy" if (gov_ok or hkex_ok) else "degraded",
        "gov_crawler_available": gov_ok,
        "hkex_crawler_available": hkex_ok,
        "timestamp": datetime.now().isoformat()
    }
