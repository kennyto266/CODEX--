"""
真实数据分析API
基于FastAPI框架实现

基于OpenSpec规范设计：
- 完整的REST API
- 支持复杂查询
- 实时数据返回
- 性能优化
- 完整的API文档

性能要求：
- 响应时间 < 500ms
- 支持并发请求 (最多100个)
- 数据缓存时间 1小时
"""

from fastapi import FastAPI, HTTPException, Query, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import logging
import asyncio
import json

from ..data_adapters.real.hibor_adapter import HKMHiborAdapter
from ..data_adapters.real.property_adapter import PropertyDataAdapter
from ..data_adapters.real.tourism_adapter import TourismDataAdapter
from ..storage.data_storage import RealDataStorage, StorageConfig
from ..data_processing.real_data_cleaner import RealDataCleaner

logger = logging.getLogger(__name__)

# FastAPI应用初始化
app = FastAPI(
    title="真实数据API",
    description="基于OpenSpec规范的非价格真实数据API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
storage = None
cleaner = RealDataCleaner()
adapters = {}


class HIBORQuery(BaseModel):
    """HIBOR查询模型"""
    period: str = Field(..., description="HIBOR期限", example="1m")
    start_date: str = Field(..., description="开始日期 (YYYY-MM-DD)", example="2024-10-01")
    end_date: str = Field(..., description="结束日期 (YYYY-MM-DD)", example="2024-11-01")

    @validator('period')
    def validate_period(cls, v):
        valid_periods = ['overnight', '1m', '3m', '6m', '12m']
        if v not in valid_periods:
            raise ValueError(f'无效HIBOR期限: {v}，有效值: {valid_periods}')
        return v

    @validator('start_date', 'end_date')
    def validate_date(cls, v):
        try:
            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError('日期格式必须为 YYYY-MM-DD')


class PropertyQuery(BaseModel):
    """物业查询模型"""
    district: Optional[str] = Field(None, description="地区", example="中區")
    start_date: Optional[str] = Field(None, description="开始日期 (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="结束日期 (YYYY-MM-DD)")
    min_price: Optional[float] = Field(None, description="最低价格")
    max_price: Optional[float] = Field(None, description="最高价格")
    data_type: str = Field('transaction', description="数据类型", example="transaction")

    @validator('data_type')
    def validate_data_type(cls, v):
        valid_types = ['transaction', 'rental']
        if v not in valid_types:
            raise ValueError(f'无效数据类型: {v}，有效值: {valid_types}')
        return v

    @validator('start_date', 'end_date')
    def validate_date(cls, v):
        if v:
            try:
                datetime.fromisoformat(v)
                return v
            except ValueError:
                raise ValueError('日期格式必须为 YYYY-MM-DD')
        return v


class TourismQuery(BaseModel):
    """旅客查询模型"""
    month: Optional[int] = Field(None, description="月份 (1-12)")
    year: Optional[int] = Field(None, description="年份")
    country: Optional[str] = Field(None, description="国家代码", example="CN")
    visitor_type: str = Field('arrival', description="旅客类型", example="arrival")

    @validator('month')
    def validate_month(cls, v):
        if v and (v < 1 or v > 12):
            raise ValueError('月份必须在1-12之间')
        return v

    @validator('visitor_type')
    def validate_visitor_type(cls, v):
        valid_types = ['arrival', 'departure', 'both']
        if v not in valid_types:
            raise ValueError(f'无效旅客类型: {v}，有效值: {valid_types}')
        return v


class DataSourceHealth(BaseModel):
    """数据源健康状态"""
    source_name: str
    status: str  # 'healthy', 'degraded', 'failed'
    last_updated: Optional[str]
    response_time: float
    error_message: Optional[str] = None


class ApiResponse(BaseModel):
    """API响应模型"""
    status: str = "success"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    data: Optional[Any] = None
    count: Optional[int] = None
    source: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    """启动事件"""
    global storage, adapters

    try:
        # 初始化存储系统
        storage_config = StorageConfig(
            postgres_host="localhost",
            postgres_port=5432,
            postgres_database="hk_quant",
            postgres_user="postgres",
            postgres_password="password",
            redis_host="localhost",
            redis_port=6379
        )

        storage = RealDataStorage(storage_config)
        await storage.initialize()

        # 初始化数据适配器
        hibor_config = type('Config', (), {
            'api_key': 'your_hkma_api_key',
            'base_url': 'https://api.hkma.gov.hk',
            'timeout': 30
        })()

        adapters['hibor'] = HKMHiborAdapter(hibor_config)
        adapters['property'] = PropertyDataAdapter(type('Config', (), {
            'api_key': 'your_rvd_api_key',
            'base_url': 'https://www.rvd.gov.hk',
            'timeout': 60
        })())
        adapters['tourism'] = TourismDataAdapter(type('Config', (), {
            'api_key': 'your_tourism_api_key',
            'base_url': 'https://www.discoverhongkong.com',
            'timeout': 60
        })())

        logger.info("真实数据API启动完成")

    except Exception as e:
        logger.error(f"API启动失败: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    global storage
    if storage:
        await storage.close()
    logger.info("真实数据API已关闭")


@app.get("/api/v1/real_data/health")
async def check_system_health():
    """检查系统健康状态"""
    try:
        # 检查存储系统
        storage_health = await storage.health_check()

        # 检查数据适配器
        adapter_status = []
        for name, adapter in adapters.items():
            try:
                health = await adapter.health_check()
                adapter_status.append(DataSourceHealth(
                    source_name=name,
                    status=health['status'],
                    last_updated=health['last_updated'],
                    response_time=0.1  # 模拟响应时间
                ))
            except Exception as e:
                adapter_status.append(DataSourceHealth(
                    source_name=name,
                    status='failed',
                    last_updated=None,
                    response_time=0.0,
                    error_message=str(e)
                ))

        return ApiResponse(
            status="success",
            data={
                'storage': storage_health,
                'adapters': [s.dict() for s in adapter_status],
                'overall_status': 'healthy' if storage_health.get('storage_system') else 'degraded'
            }
        )

    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/real_data/hibor", response_model=ApiResponse)
async def get_real_hibor_data(
    period: str = Query(..., description="HIBOR期限 (overnight, 1m, 3m, 6m, 12m)"),
    start_date: str = Query(..., description="开始日期 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="结束日期 (YYYY-MM-DD)"),
    use_cache: bool = Query(True, description="是否使用缓存")
):
    """
    获取真实HIBOR数据
    从HKMA官方API获取真实的HIBOR利率数据
    """
    try:
        # 验证参数
        valid_periods = ['overnight', '1m', '3m', '6m', '12m']
        if period not in valid_periods:
            raise ValueError(f"无效HIBOR期限: {period}")

        # 记录请求
        start_time = datetime.now()

        # 尝试从存储系统获取
        if use_cache and storage:
            cached_data = await storage.query_real_data(
                source='HKMA',
                start_date=start_date,
                end_date=end_date,
                filters={'period': period}
            )

            if cached_data:
                response_time = (datetime.now() - start_time).total_seconds()
                return ApiResponse(
                    status="success",
                    count=len(cached_data),
                    data=cached_data,
                    source="HKMA",
                    timestamp=datetime.now().isoformat()
                )

        # 从API获取实时数据
        async with adapters['hibor'] as adapter:
            raw_data = await adapter.fetch_real_data(period, start_date, end_date)

        # 数据清洗
        cleaned_data, quality_report = await cleaner.clean_real_data('hibor', raw_data)

        # 存储清洗后的数据
        if storage:
            await storage.store_real_data('HKMA', cleaned_data)

        response_time = (datetime.now() - start_time).total_seconds()

        # 检查性能要求
        if response_time > 0.5:
            logger.warning(f"HIBOR API响应时间超限: {response_time:.2f}s")

        return ApiResponse(
            status="success",
            count=len(cleaned_data),
            data=[item.data for item in cleaned_data],
            source="HKMA",
            timestamp=datetime.now().isoformat()
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"HIBOR数据获取失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/real_data/property", response_model=ApiResponse)
async def get_real_property_data(
    district: Optional[str] = Query(None, description="地区"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    min_price: Optional[float] = Query(None, description="最低价格"),
    max_price: Optional[float] = Query(None, description="最高价格"),
    data_type: str = Query("transaction", description="数据类型 (transaction, rental)"),
    use_cache: bool = Query(True, description="是否使用缓存")
):
    """
    获取真实物业数据
    从土地注册处获取真实的物业交易和租金数据
    """
    try:
        # 验证参数
        if min_price and max_price and min_price > max_price:
            raise ValueError("最低价格不能大于最高价格")

        # 准备查询条件
        filters = {}
        if district:
            filters['district'] = district
        if min_price:
            filters['min_price'] = min_price
        if max_price:
            filters['max_price'] = max_price

        # 从存储系统获取缓存数据
        if use_cache and storage:
            cached_data = await storage.query_real_data(
                source='RVD',
                start_date=start_date,
                end_date=end_date,
                filters=filters
            )

            if cached_data:
                return ApiResponse(
                    status="success",
                    count=len(cached_data),
                    data=cached_data,
                    source="RVD"
                )

        # 从API获取实时数据
        async with adapters['property'] as adapter:
            raw_data = await adapter.fetch_real_data(
                district=district,
                start_date=start_date,
                end_date=end_date,
                data_type=data_type
            )

        # 数据清洗
        cleaned_data, quality_report = await cleaner.clean_real_data('property', raw_data)

        # 应用价格过滤
        if min_price or max_price:
            filtered_data = []
            for item in cleaned_data:
                price = item.data.get('price') or item.data.get('monthly_rent')
                if price:
                    if (min_price is None or price >= min_price) and (max_price is None or price <= max_price):
                        filtered_data.append(item)
            cleaned_data = filtered_data

        # 存储清洗后的数据
        if storage:
            await storage.store_real_data('RVD', cleaned_data)

        return ApiResponse(
            status="success",
            count=len(cleaned_data),
            data=[item.data for item in cleaned_data],
            source="RVD"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"物业数据获取失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/real_data/tourism", response_model=ApiResponse)
async def get_real_tourism_data(
    month: Optional[int] = Query(None, description="月份 (1-12)"),
    year: Optional[int] = Query(None, description="年份"),
    country: Optional[str] = Query(None, description="国家代码"),
    visitor_type: str = Query("arrival", description="旅客类型 (arrival, departure, both)"),
    use_cache: bool = Query(True, description="是否使用缓存")
):
    """
    获取真实旅客流量数据
    从旅游发展局和入境事务处获取真实的旅客统计数据
    """
    try:
        # 设置默认日期
        if not month:
            month = datetime.now().month
        if not year:
            year = datetime.now().year

        # 从存储系统获取缓存数据
        if use_cache and storage:
            cached_data = await storage.query_real_data(
                source='HKBTO',
                filters={'month': month, 'year': year, 'country': country}
            )

            if cached_data:
                return ApiResponse(
                    status="success",
                    count=len(cached_data),
                    data=cached_data,
                    source="HKBTO"
                )

        # 从API获取实时数据
        async with adapters['tourism'] as adapter:
            raw_data = await adapter.fetch_real_data(
                month=month,
                year=year,
                country=country,
                visitor_type=visitor_type
            )

        # 数据清洗
        cleaned_data, quality_report = await cleaner.clean_real_data('tourism', raw_data)

        # 存储清洗后的数据
        if storage:
            await storage.store_real_data('HKBTO', cleaned_data)

        return ApiResponse(
            status="success",
            count=len(cleaned_data),
            data=[item.data for item in cleaned_data],
            source="HKBTO"
        )

    except Exception as e:
        logger.error(f"旅客数据获取失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/real_data/hibor/trend")
async def get_hibor_trend(
    period: str = Query(..., description="HIBOR期限"),
    days: int = Query(30, description="天数", ge=1, le=365)
):
    """
    获取HIBOR趋势数据
    分析HIBOR利率的历史趋势和变化
    """
    try:
        async with adapters['hibor'] as adapter:
            trend_data = await adapter.get_hibor_trend(period, days)

        return ApiResponse(
            status="success",
            data=trend_data,
            source="HKMA"
        )

    except Exception as e:
        logger.error(f"HIBOR趋势分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/real_data/property/market-stats")
async def get_property_market_stats(
    district: Optional[str] = Query(None, description="地区"),
    days: int = Query(30, description="天数", ge=1, le=365)
):
    """
    获取物业市场统计
    分析物业市场的价格、交易量等统计信息
    """
    try:
        async with adapters['property'] as adapter:
            stats = await adapter.get_market_statistics(district, days)

        return ApiResponse(
            status="success",
            data=stats,
            source="RVD"
        )

    except Exception as e:
        logger.error(f"物业市场统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/real_data/tourism/monthly-stats")
async def get_tourism_monthly_stats(
    month: int = Query(..., description="月份", ge=1, le=12),
    year: int = Query(..., description="年份")
):
    """
    获取月度旅游统计
    分析月度旅客流量数据和趋势
    """
    try:
        async with adapters['tourism'] as adapter:
            stats = await adapter.get_monthly_statistics(month, year)

        return ApiResponse(
            status="success",
            data=stats,
            source="HKBTO"
        )

    except Exception as e:
        logger.error(f"月度旅游统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/real_data/refresh")
async def refresh_real_data(
    source: str = Query(..., description="数据源 (hibor, property, tourism, all)"),
    background_tasks: BackgroundTasks
):
    """
    手动刷新真实数据
    强制从API获取最新数据并更新缓存
    """
    try:
        valid_sources = ['hibor', 'property', 'tourism', 'all']
        if source not in valid_sources:
            raise ValueError(f"无效数据源: {source}，有效值: {valid_sources}")

        # 记录刷新任务
        background_tasks.add_task(_background_refresh, source)

        return ApiResponse(
            status="success",
            message=f"开始刷新 {source} 数据",
            timestamp=datetime.now().isoformat()
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"数据刷新失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _background_refresh(source: str):
    """后台刷新任务"""
    try:
        logger.info(f"开始后台刷新 {source} 数据")

        if source in ['hibor', 'all']:
            async with adapters['hibor'] as adapter:
                await adapter.fetch_latest_hibor()

        if source in ['property', 'all']:
            async with adapters['property'] as adapter:
                await adapter.fetch_real_data()

        if source in ['tourism', 'all']:
            async with adapters['tourism'] as adapter:
                await adapter.fetch_real_data()

        logger.info(f"{source} 数据刷新完成")

    except Exception as e:
        logger.error(f"{source} 数据刷新失败: {e}")


@app.get("/api/v1/real_data/quality-report")
async def get_data_quality_report(source: Optional[str] = Query(None, description="数据源")):
    """
    获取数据质量报告
    查看数据清洗和验证的详细报告
    """
    try:
        if not storage:
            raise HTTPException(status_code=503, detail="存储系统不可用")

        quality_report = await storage.get_data_quality_report(source)

        return ApiResponse(
            status="success",
            data=quality_report
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取质量报告失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/real_data/anomalies")
async def get_anomaly_summary(source: Optional[str] = Query(None, description="数据源")):
    """
    获取异常摘要
    查看数据异常检测的统计和详情
    """
    try:
        summary = cleaner.get_anomaly_summary(source)

        return ApiResponse(
            status="success",
            data=summary
        )

    except Exception as e:
        logger.error(f"获取异常摘要失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/real_data/summary")
async def get_data_summary():
    """
    获取数据摘要
    快速查看各数据源的基本信息
    """
    try:
        if not storage:
            raise HTTPException(status_code=503, detail="存储系统不可用")

        quality_report = await storage.get_data_quality_report()

        # 获取异常摘要
        anomaly_summary = cleaner.get_anomaly_summary()

        summary = {
            'data_sources': len(quality_report['source_status']),
            'total_data_points': sum(quality_report['data_statistics'].values()),
            'quality_scores': quality_report['quality_metrics'],
            'anomalies': anomaly_summary,
            'last_updated': datetime.now().isoformat()
        }

        return ApiResponse(
            status="success",
            data=summary
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取数据摘要失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "真实数据API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/real_data/health"
    }


@app.get("/api/v1/real_data/documentation")
async def get_api_documentation():
    """获取API文档信息"""
    return {
        "title": "真实数据API",
        "description": "基于OpenSpec规范的非价格真实数据API",
        "version": "1.0.0",
        "endpoints": {
            "健康检查": "/api/v1/real_data/health",
            "HIBOR数据": "/api/v1/real_data/hibor",
            "物业数据": "/api/v1/real_data/property",
            "旅客数据": "/api/v1/real_data/tourism",
            "HIBOR趋势": "/api/v1/real_data/hibor/trend",
            "物业统计": "/api/v1/real_data/property/market-stats",
            "旅客统计": "/api/v1/real_data/tourism/monthly-stats",
            "数据刷新": "/api/v1/real_data/refresh",
            "质量报告": "/api/v1/real_data/quality-report",
            "异常摘要": "/api/v1/real_data/anomalies"
        },
        "performance_targets": {
            "response_time": "< 500ms",
            "concurrent_requests": "100",
            "cache_ttl": "1小时",
            "uptime": "> 99%"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
