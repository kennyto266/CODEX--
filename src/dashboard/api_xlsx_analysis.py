"""
xlsx 股票分析系统 API 集成

将 xlsx 股票分析功能集成到现有 Dashboard API 中
提供 Excel 报告生成和分析结果的 REST 端点
"""

import asyncio
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
import json
import sys

# 添加 xlsx 分析模块路径
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(current_dir))
xlsx_module_path = os.path.join(root_dir)
if xlsx_module_path not in sys.path:
    sys.path.insert(0, xlsx_module_path)

try:
    from xlsx_stock_analyzer import XlsxStockAnalyzer
    from create_xlsx_report import create_excel_report
    from simple_enhance_xlsx import enhance_excel
except ImportError as e:
    logging.warning(f"无法导入 xlsx 分析模块: {e}")


# ==================== Data Models ====================

class XlsxAnalysisRequest(BaseModel):
    """xlsx 分析请求"""
    symbol: str = Field(..., description="股票代码，如 0001.HK")
    start_date: str = Field(..., description="开始日期 YYYY-MM-DD")
    end_date: str = Field(..., description="结束日期 YYYY-MM-DD")
    strategy_types: List[str] = Field(
        default=["BOLL", "RSI"],
        description="策略类型列表"
    )
    generate_enhanced: bool = Field(
        default=True,
        description="是否生成增强版 Excel 报告"
    )


class XlsxAnalysisStatus(BaseModel):
    """分析状态"""
    task_id: str
    status: str  # pending, running, completed, failed
    progress: int = Field(default=0, ge=0, le=100)
    message: str = Field(default="")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class XlsxAnalysisResult(BaseModel):
    """分析结果"""
    task_id: str
    symbol: str
    period: Dict[str, str]
    metrics: Dict[str, Any]
    strategies: Dict[str, Any]
    excel_files: Dict[str, str]  # {type: file_path}
    generated_at: datetime


class XlsxAnalysisService:
    """xlsx 分析服务"""

    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.xlsx_analysis")
        self.results_dir = Path("data/xlsx_reports")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self._tasks = {}  # 存储任务状态

    async def start_analysis(
        self,
        request: XlsxAnalysisRequest,
        task_id: str
    ) -> XlsxAnalysisStatus:
        """启动分析任务"""
        try:
            self.logger.info(f"启动 xlsx 分析任务: {task_id}, 股票: {request.symbol}")

            # 更新任务状态
            self._tasks[task_id] = {
                "status": "running",
                "progress": 0,
                "message": "正在初始化分析...",
                "started_at": datetime.now()
            }

            # 在后台运行分析
            asyncio.create_task(
                self._run_analysis(request, task_id)
            )

            return XlsxAnalysisStatus(
                task_id=task_id,
                status="running",
                progress=0,
                message="分析已启动",
                started_at=datetime.now()
            )

        except Exception as e:
            self.logger.error(f"启动分析任务失败: {e}")
            self._tasks[task_id] = {
                "status": "failed",
                "progress": 0,
                "message": str(e),
                "started_at": datetime.now(),
                "completed_at": datetime.now()
            }
            raise HTTPException(status_code=500, detail=str(e))

    async def _run_analysis(
        self,
        request: XlsxAnalysisRequest,
        task_id: str
    ):
        """运行分析任务"""
        try:
            self._update_progress(task_id, 10, "加载数据...")

            # 1. 运行分析引擎
            analyzer = XlsxStockAnalyzer()
            await analyzer.load_data(
                symbol=request.symbol,
                start_date=request.start_date,
                end_date=request.end_date
            )

            self._update_progress(task_id, 30, "计算性能指标...")
            await analyzer.calculate_performance_metrics()
            await analyzer.analyze_strategies(request.strategy_types)

            self._update_progress(task_id, 50, "生成分析结果...")
            results = await analyzer.generate_results()

            # 保存分析结果
            results_file = self.results_dir / f"{task_id}_analysis.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)

            excel_files = {}

            # 2. 生成基础 Excel 报告
            self._update_progress(task_id, 60, "生成 Excel 报告...")
            basic_excel = self.results_dir / f"{task_id}_basic.xlsx"
            await create_excel_report(
                results,
                str(basic_excel)
            )
            excel_files["basic"] = str(basic_excel)

            # 3. 生成增强版 Excel 报告
            if request.generate_enhanced:
                self._update_progress(task_id, 80, "增强格式...")
                enhanced_excel = self.results_dir / f"{task_id}_enhanced.xlsx"
                # 复制基础文件然后增强
                shutil.copy2(basic_excel, enhanced_excel)
                await self._enhance_excel(enhanced_excel)
                excel_files["enhanced"] = str(enhanced_excel)

            # 4. 完成
            self._update_progress(task_id, 100, "分析完成")
            self._tasks[task_id]["status"] = "completed"
            self._tasks[task_id]["progress"] = 100
            self._tasks[task_id]["message"] = "分析完成"
            self._tasks[task_id]["completed_at"] = datetime.now()
            self._tasks[task_id]["results"] = {
                "symbol": request.symbol,
                "period": {"start": request.start_date, "end": request.end_date},
                "metrics": results.get("performance_metrics", {}),
                "strategies": results.get("strategy_summary", {}),
                "excel_files": excel_files,
                "generated_at": datetime.now()
            }

            self.logger.info(f"xlsx 分析任务完成: {task_id}")

        except Exception as e:
            self.logger.error(f"分析任务失败: {task_id}, 错误: {e}")
            self._tasks[task_id]["status"] = "failed"
            self._tasks[task_id]["message"] = str(e)
            self._tasks[task_id]["completed_at"] = datetime.now()

    async def _enhance_excel(self, excel_path: Path):
        """增强 Excel 格式"""
        try:
            # 使用现有脚本增强格式
            os.chdir(excel_path.parent)
            enhance_excel()
        except Exception as e:
            self.logger.warning(f"增强 Excel 格式失败: {e}")

    def _update_progress(
        self,
        task_id: str,
        progress: int,
        message: str
    ):
        """更新任务进度"""
        if task_id in self._tasks:
            self._tasks[task_id]["progress"] = progress
            self._tasks[task_id]["message"] = message

    def get_status(self, task_id: str) -> Optional[XlsxAnalysisStatus]:
        """获取任务状态"""
        task = self._tasks.get(task_id)
        if not task:
            return None

        return XlsxAnalysisStatus(
            task_id=task_id,
            status=task["status"],
            progress=task["progress"],
            message=task["message"],
            started_at=task.get("started_at"),
            completed_at=task.get("completed_at")
        )

    def get_results(self, task_id: str) -> Optional[XlsxAnalysisResult]:
        """获取分析结果"""
        task = self._tasks.get(task_id)
        if not task or task["status"] != "completed":
            return None

        return XlsxAnalysisResult(
            task_id=task_id,
            **task["results"]
        )


# ==================== API Router Setup ====================

def create_xlsx_analysis_router() -> APIRouter:
    """创建 xlsx 分析 API 路由器"""
    router = APIRouter(prefix="/api/xlsx", tags=["xlsx-analysis"])
    service = XlsxAnalysisService()

    @router.post("/analyze", response_model=XlsxAnalysisStatus)
    async def start_analysis(request: XlsxAnalysisRequest):
        """启动 xlsx 股票分析"""
        import uuid
        task_id = str(uuid.uuid4())
        return await service.start_analysis(request, task_id)

    @router.get("/status/{task_id}", response_model=XlsxAnalysisStatus)
    async def get_analysis_status(task_id: str):
        """获取分析状态"""
        status = service.get_status(task_id)
        if not status:
            raise HTTPException(status_code=404, detail="任务不存在")
        return status

    @router.get("/results/{task_id}", response_model=XlsxAnalysisResult)
    async def get_analysis_results(task_id: str):
        """获取分析结果"""
        results = service.get_results(task_id)
        if not results:
            raise HTTPException(
                status_code=404,
                detail="结果不存在或任务未完成"
            )
        return results

    @router.get("/download/{task_id}")
    async def download_excel(
        task_id: str,
        type: str = Query("enhanced", description="文件类型: basic 或 enhanced")
    ):
        """下载 Excel 报告"""
        status = service.get_status(task_id)
        if not status or status.status != "completed":
            raise HTTPException(status_code=404, detail="文件不存在")

        results = service.get_results(task_id)
        file_path = results.excel_files.get(type)

        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")

        filename = f"{results.symbol}_{type}_report.xlsx"
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    @router.get("/reports")
    async def list_reports():
        """列出所有生成的报告"""
        reports = []
        for task_id, task in service._tasks.items():
            if task["status"] == "completed":
                reports.append({
                    "task_id": task_id,
                    "symbol": task["results"]["symbol"],
                    "period": task["results"]["period"],
                    "generated_at": task["completed_at"],
                    "files": list(task["results"]["excel_files"].keys())
                })
        return {"reports": reports}

    return router
