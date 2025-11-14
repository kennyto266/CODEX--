"""
数据质量报告生成器 (T354) - FastAPI 集成示例
演示如何将 QualityReporter 集成到 FastAPI 应用中

Author: Claude Code
Date: 2025-11-09
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import asyncio
import json
import os
from datetime import datetime
import sys

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data import QualityReporter, generate_quality_report


# ==================== Pydantic 模型 ====================

class ValidationStageResult(BaseModel):
    is_passed: bool
    score: float
    errors: List[str] = []


class ValidationResult(BaseModel):
    is_valid: bool
    overall_score: float
    stages: Dict[str, ValidationStageResult]
    source: Optional[str] = None


class AnomalyItem(BaseModel):
    type: str
    severity: str
    description: str
    count: int = 1


class AnomalySummary(BaseModel):
    total_anomalies: int
    high_severity: int = 0
    medium_severity: int = 0
    low_severity: int = 0


class AnomalyResult(BaseModel):
    summary: AnomalySummary
    anomalies: List[AnomalyItem]
    source: Optional[str] = None


class Difference(BaseModel):
    type: str
    description: str
    impact: str


class VerificationResult(BaseModel):
    status: str
    consistency_score: float
    differences: List[Difference] = []


class FreshnessResult(BaseModel):
    status: str
    freshness_score: float
    age_hours: float
    last_update: Optional[str] = None


class QualityReportRequest(BaseModel):
    symbol: str = Field(..., description="股票代码")
    validation_results: Optional[List[ValidationResult]] = None
    anomaly_results: Optional[List[AnomalyResult]] = None
    verification_results: Optional[List[VerificationResult]] = None
    freshness_results: Optional[List[FreshnessResult]] = None
    output_format: str = Field(default="html", description="输出格式: html, json")


class QualityReportResponse(BaseModel):
    success: bool
    message: str
    report_id: str
    data: Optional[Dict[str, Any]] = None
    file_url: Optional[str] = None
    download_url: Optional[str] = None


class HistoryTrendResponse(BaseModel):
    success: bool
    symbol: str
    trends: Dict[str, Any]
    generated_at: str


# ==================== FastAPI 应用 ====================

app = FastAPI(
    title="数据质量报告API",
    description="提供数据质量评估、报告生成和趋势分析服务",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局报告生成器实例
reporter = QualityReporter()

# 报告存储
report_storage = {}


# ==================== API 端点 ====================

@app.get("/")
async def root():
    """根路径 - API信息"""
    return {
        "service": "数据质量报告生成器",
        "version": "1.0.0",
        "status": "运行中",
        "endpoints": {
            "生成报告": "/api/quality/report",
            "获取报告": "/api/quality/report/{report_id}",
            "趋势分析": "/api/quality/trends/{symbol}",
            "健康检查": "/api/health"
        }
    }


@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "data-quality-reporter"
    }


@app.post("/api/quality/report", response_model=QualityReportResponse)
async def generate_report(request: QualityReportRequest, background_tasks: BackgroundTasks):
    """
    生成数据质量报告

    - **symbol**: 股票代码 (例如: 0700.HK)
    - **validation_results**: 数据验证结果
    - **anomaly_results**: 异常检测结果
    - **verification_results**: 跨源验证结果
    - **freshness_results**: 新鲜度检查结果
    - **output_format**: 输出格式 (html 或 json)
    """
    try:
        # 转换为内部格式
        validation_data = [r.dict() for r in (request.validation_results or [])]
        anomaly_data = [r.dict() for r in (request.anomaly_results or [])]
        verification_data = [r.dict() for r in (request.verification_results or [])]
        freshness_data = [r.dict() for r in (request.freshness_results or [])]

        # 生成报告
        report = await reporter.generate_report(
            symbol=request.symbol,
            validation_results=validation_data if validation_data else None,
            anomaly_results=anomaly_data if anomaly_data else None,
            verification_results=verification_data if verification_data else None,
            freshness_results=freshness_data if freshness_data else None
        )

        # 生成报告ID
        report_id = f"{request.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 保存报告
        report_data = report.to_dict()
        report_storage[report_id] = {
            'report': report_data,
            'symbol': request.symbol,
            'timestamp': datetime.now().isoformat()
        }

        # 根据输出格式处理
        if request.output_format.lower() == "html":
            # 保存HTML文件
            filepath = reporter.save_html_report(report, f"{report_id}.html")
            file_url = f"/api/quality/report/{report_id}/file"

            background_tasks.add_task(
                lambda: print(f"报告已生成: {filepath}")
            )

            return QualityReportResponse(
                success=True,
                message="报告生成成功",
                report_id=report_id,
                data=report_data,
                file_url=file_url,
                download_url=f"/api/quality/report/{report_id}/download"
            )
        else:
            # JSON格式
            return QualityReportResponse(
                success=True,
                message="报告生成成功",
                report_id=report_id,
                data=report_data
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"报告生成失败: {str(e)}")


@app.get("/api/quality/report/{report_id}")
async def get_report(report_id: str):
    """
    根据报告ID获取报告
    """
    if report_id not in report_storage:
        raise HTTPException(status_code=404, detail="报告不存在")

    report_info = report_storage[report_id]
    return {
        "success": True,
        "report_id": report_id,
        "data": report_info['report'],
        "metadata": {
            "symbol": report_info['symbol'],
            "timestamp": report_info['timestamp']
        }
    }


@app.get("/api/quality/report/{report_id}/file")
async def get_report_file(report_id: str):
    """
    获取HTML报告文件
    """
    if report_id not in report_storage:
        raise HTTPException(status_code=404, detail="报告不存在")

    # 这里应该返回实际保存的HTML文件
    # 示例中仅返回提示信息
    return HTMLResponse(content=f"""
    <h1>报告文件: {report_id}</h1>
    <p>在实际应用中，这里会返回完整的HTML报告内容</p>
    <p>报告ID: {report_id}</p>
    """)


@app.get("/api/quality/report/{report_id}/download")
async def download_report(report_id: str):
    """
    下载报告文件
    """
    if report_id not in report_storage:
        raise HTTPException(status_code=404, detail="报告不存在")

    # 示例返回JSON数据
    report_info = report_storage[report_id]
    return {
        "download_url": f"/api/quality/report/{report_id}/file",
        "format": "html",
        "size": "N/A"
    }


@app.get("/api/quality/trends/{symbol}", response_model=HistoryTrendResponse)
async def get_trends(symbol: str):
    """
    获取指定股票的质量趋势分析
    """
    try:
        # 模拟历史报告数据
        historical_reports = []
        base_score = 0.75
        for i in range(10):
            report = {
                'timestamp': (datetime.now() - timedelta(days=i*7)).isoformat(),
                'overall_score': base_score + (i * 0.02),
                'dimensions': {
                    'completeness': 0.80 + (i * 0.015),
                    'accuracy': 0.78 + (i * 0.018),
                    'consistency': 0.75 + (i * 0.012),
                    'timeliness': 0.70 + (i * 0.020),
                    'validity': 0.82 + (i * 0.010),
                    'uniqueness': 0.85 + (i * 0.005)
                }
            }
            historical_reports.append(report)

        # 使用趋势分析器
        from data import TrendAnalyzer
        trend_analyzer = TrendAnalyzer()
        trends = trend_analyzer.analyze_trends(historical_reports)

        return HistoryTrendResponse(
            success=True,
            symbol=symbol,
            trends=trends,
            generated_at=datetime.now().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"趋势分析失败: {str(e)}")


@app.post("/api/quality/batch-report")
async def generate_batch_report(
    symbols: List[str],
    background_tasks: BackgroundTasks
):
    """
    批量生成多个股票的质量报告
    """
    async def generate_reports():
        results = []
        for symbol in symbols:
            try:
                # 模拟生成报告
                report = await generate_quality_report(
                    symbol=symbol,
                    validation_results=[{
                        'is_valid': True,
                        'overall_score': 0.90
                    }]
                )
                results.append({
                    'symbol': symbol,
                    'success': True,
                    'score': report.overall_score
                })
            except Exception as e:
                results.append({
                    'symbol': symbol,
                    'success': False,
                    'error': str(e)
                })
        print(f"批量报告生成完成: {results}")

    background_tasks.add_task(generate_reports)

    return {
        "success": True,
        "message": f"已开始为 {len(symbols)} 个股票生成报告",
        "symbols": symbols
    }


# ==================== 使用示例 ====================

def demo_api_usage():
    """演示如何使用API"""
    print("\n" + "="*80)
    print("数据质量报告API - 使用示例")
    print("="*80)

    import requests
    import json

    # API基础URL
    base_url = "http://localhost:8000"

    # 1. 健康检查
    print("\n1. 健康检查:")
    response = requests.get(f"{base_url}/api/health")
    print(f"  状态: {response.json()}")

    # 2. 生成单个报告
    print("\n2. 生成质量报告:")
    report_data = {
        "symbol": "0700.HK",
        "output_format": "json",
        "validation_results": [{
            "is_valid": True,
            "overall_score": 0.92,
            "stages": {
                "structure": {"is_passed": True, "score": 0.95, "errors": []},
                "data_type": {"is_passed": True, "score": 0.93, "errors": []}
            }
        }],
        "anomaly_results": [{
            "summary": {
                "total_anomalies": 3,
                "high_severity": 1,
                "medium_severity": 1,
                "low_severity": 1
            },
            "anomalies": [
                {"type": "statistical", "severity": "high", "description": "异常", "count": 1}
            ]
        }]
    }

    response = requests.post(
        f"{base_url}/api/quality/report",
        json=report_data
    )
    result = response.json()
    print(f"  报告ID: {result['report_id']}")
    print(f"  总体分数: {result['data']['overall_score']}")
    print(f"  质量等级: {result['data']['grade']}")

    # 3. 获取趋势分析
    print("\n3. 趋势分析:")
    response = requests.get(f"{base_url}/api/quality/trends/0700.HK")
    trends = response.json()
    print(f"  总体趋势: {trends['trends']['overall']['direction']}")
    print(f"  R²: {trends['trends']['overall']['r_squared']:.3f}")

    print("\n✅ API使用示例完成")


if __name__ == "__main__":
    # 导入必要的模块
    from timedelta import timedelta

    print("\n" + "="*80)
    print("数据质量报告生成器 (T354) - FastAPI 集成")
    print("="*80)
    print("\n🚀 启动方式:")
    print("  uvicorn quality_reporter_api_example:app --reload --port 8000")
    print("\n📖 API文档:")
    print("  http://localhost:8000/docs")
    print("\n🧪 测试API:")
    print("  python quality_reporter_api_example.py")

    # 如果直接运行，运行演示
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_api_usage()
