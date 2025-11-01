"""
任務數據導入API
提供任務清單解析、導入、驗證和報告生成功能
"""

import os
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks
from pydantic import BaseModel, Field
import logging

from ..models.api_response import APIResponse
from ..repositories.dependency_injection import get_repository_manager
from ..services.task_import_service import TaskImportService, TaskDataAnalyzer
from ..services.task_import_service import ParsedTask, ImportResult

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/import", tags=["import"])


# Pydantic模型
class ImportRequest(BaseModel):
    """導入請求"""
    file_path: str = Field(..., description="任務清單文件路徑")
    create_sprint: bool = Field(default=True, description="是否創建Sprint")
    rollback_previous: bool = Field(default=False, description="是否回滾之前的導入")


class ImportStatus(BaseModel):
    """導入狀態"""
    task_id: str
    status: str  # pending, running, completed, failed
    progress: float
    message: str
    result: Optional[Dict[str, Any]] = None


class AnalysisRequest(BaseModel):
    """分析請求"""
    file_path: str = Field(..., description="要分析的文件路徑")


# 導入狀態存儲（在實際生產中應該使用Redis或數據庫）
IMPORT_STATUS = {}


# API端點

@router.post("/tasks/analyze", response_model=APIResponse)
async def analyze_tasks(
    request: AnalysisRequest
):
    """
    分析任務清單文件質量

    分析內容：
    - 任務數量和分布
    - 優先級分布
    - 工時估算
    - 潛在問題
    - 質量評分
    """
    try:
        # 檢查文件是否存在
        if not os.path.exists(request.file_path):
            raise HTTPException(
                status_code=404,
                detail=f"文件不存在: {request.file_path}"
            )

        # 分析文件
        analyzer = TaskDataAnalyzer()
        analysis = analyzer.analyze_markdown_tasks(request.file_path)

        if not analysis:
            raise HTTPException(
                status_code=500,
                detail="文件分析失敗"
            )

        # 生成建議
        suggestions = []
        if analysis.get('issues'):
            for issue in analysis['issues']:
                suggestions.append(f"⚠️ {issue}")

        if analysis.get('quality_score', 0) < 60:
            suggestions.append("📊 質量分數較低，建議優化任務描述")

        if analysis.get('hours_stats', {}).get('total', 0) > 200:
            suggestions.append("⏰ 總工時較大，建議拆分為多個Sprint")

        return APIResponse.success(
            data={
                'analysis': analysis,
                'suggestions': suggestions,
                'file_path': request.file_path,
                'analyzed_at': datetime.utcnow().isoformat()
            },
            message=f"分析完成，質量評分: {analysis.get('quality_score', 0):.1f}/100"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分析任務文件失敗: {e}")
        raise HTTPException(status_code=500, detail=f"分析失敗: {str(e)}")


@router.post("/tasks/start", response_model=APIResponse)
async def start_import(
    request: ImportRequest,
    background_tasks: BackgroundTasks,
    repo_manager=Depends(get_repository_manager)
):
    """
    開始導入任務

    Args:
        request: 導入請求
        background_tasks: 後台任務
    """
    try:
        # 生成導入任務ID
        import_id = f"import_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # 檢查文件是否存在
        if not os.path.exists(request.file_path):
            raise HTTPException(
                status_code=404,
                detail=f"文件不存在: {request.file_path}"
            )

        # 初始化導入狀態
        IMPORT_STATUS[import_id] = ImportStatus(
            task_id=import_id,
            status="running",
            progress=0.0,
            message="正在初始化..."
        )

        # 後台執行導入
        background_tasks.add_task(
            run_import_task,
            import_id,
            request.file_path,
            request.create_sprint,
            request.rollback_previous,
            repo_manager
        )

        return APIResponse.success(
            data={
                'import_id': import_id,
                'file_path': request.file_path,
                'status': 'running'
            },
            message="導入任務已啟動"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"啟動導入失敗: {e}")
        raise HTTPException(status_code=500, detail=f"啟動導入失敗: {str(e)}")


async def run_import_task(
    import_id: str,
    file_path: str,
    create_sprint: bool,
    rollback_previous: bool,
    repo_manager
):
    """後台執行導入任務

    Args:
        import_id: 導入任務ID
        file_path: 文件路徑
        create_sprint: 是否創建Sprint
        rollback_previous: 是否回滾
        repo_manager: Repository管理器
    """
    try:
        IMPORT_STATUS[import_id].progress = 10.0
        IMPORT_STATUS[import_id].message = "正在解析任務清單..."

        # 創建導入服務
        import_service = TaskImportService(
            task_repo=repo_manager.task_repo,
            sprint_repo=repo_manager.sprint_repo
        )

        # 步驟1: 解析任務
        tasks = await import_service.parse_tasks_from_markdown(file_path)

        IMPORT_STATUS[import_id].progress = 30.0
        IMPORT_STATUS[import_id].message = f"解析完成，發現 {len(tasks)} 個任務"

        # 步驟2: 導入任務
        result = await import_service.import_tasks(tasks, create_sprint)

        IMPORT_STATUS[import_id].progress = 90.0
        IMPORT_STATUS[import_id].message = "正在生成報告..."

        # 步驟3: 生成報告
        report = import_service.generate_import_report(result)

        # 保存報告
        report_path = f"import_report_{import_id}.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)

        # 更新狀態
        IMPORT_STATUS[import_id].status = "completed"
        IMPORT_STATUS[import_id].progress = 100.0
        IMPORT_STATUS[import_id].message = "導入完成"
        IMPORT_STATUS[import_id].result = {
            'imported': result.imported,
            'skipped': result.skipped,
            'errors': result.errors,
            'report_path': report_path,
            'task_ids': result.task_ids
        }

        logger.info(f"導入任務完成: {import_id}")

    except Exception as e:
        IMPORT_STATUS[import_id].status = "failed"
        IMPORT_STATUS[import_id].progress = 0.0
        IMPORT_STATUS[import_id].message = f"導入失敗: {str(e)}"
        logger.error(f"導入任務失敗 ({import_id}): {e}")


@router.get("/tasks/status/{import_id}", response_model=APIResponse)
async def get_import_status(
    import_id: str
):
    """
    獲取導入狀態

    Args:
        import_id: 導入任務ID
    """
    try:
        if import_id not in IMPORT_STATUS:
            raise HTTPException(
                status_code=404,
                detail=f"導入任務不存在: {import_id}"
            )

        status = IMPORT_STATUS[import_id]

        return APIResponse.success(
            data=status.dict(),
            message=f"當前狀態: {status.status}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取導入狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取狀態失敗: {str(e)}")


@router.post("/tasks/rollback", response_model=APIResponse)
async def rollback_import(
    task_ids: List[str],
    repo_manager=Depends(get_repository_manager)
):
    """
    回滾導入（刪除指定任務）

    Args:
        task_ids: 任務ID列表
    """
    try:
        import_service = TaskImportService(
            task_repo=repo_manager.task_repo,
            sprint_repo=repo_manager.sprint_repo
        )

        deleted_count = await import_service.rollback_import(task_ids)

        return APIResponse.success(
            data={'deleted_count': deleted_count},
            message=f"成功刪除 {deleted_count} 個任務"
        )

    except Exception as e:
        logger.error(f"回滾導入失敗: {e}")
        raise HTTPException(status_code=500, detail=f"回滾失敗: {str(e)}")


@router.post("/tasks/upload", response_model=APIResponse)
async def upload_and_import(
    file: UploadFile = File(...),
    create_sprint: bool = True,
    background_tasks: BackgroundTasks = None,
    repo_manager=Depends(get_repository_manager)
):
    """
    上傳文件並導入

    Args:
        file: 上傳的文件
        create_sprint: 是否創建Sprint
        background_tasks: 後台任務
    """
    try:
        # 保存上傳的文件
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        file_path = f"uploads/tasks_{timestamp}.md"

        # 創建上傳目錄
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # 保存文件
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)

        logger.info(f"文件已上傳: {file_path}")

        # 生成導入請求
        request = ImportRequest(
            file_path=file_path,
            create_sprint=create_sprint
        )

        # 啟動導入
        import_id = f"upload_{timestamp}"

        IMPORT_STATUS[import_id] = ImportStatus(
            task_id=import_id,
            status="running",
            progress=0.0,
            message="正在初始化..."
        )

        # 後台執行
        background_tasks.add_task(
            run_import_task,
            import_id,
            file_path,
            create_sprint,
            False,
            repo_manager
        )

        return APIResponse.success(
            data={
                'import_id': import_id,
                'file_path': file_path,
                'file_name': file.filename,
                'file_size': len(content)
            },
            message="文件上傳成功，導入已啟動"
        )

    except Exception as e:
        logger.error(f"上傳並導入失敗: {e}")
        raise HTTPException(status_code=500, detail=f"上傳失敗: {str(e)}")


@router.get("/tasks/report/{import_id}", response_model=APIResponse)
async def get_import_report(
    import_id: str
):
    """
    獲取導入報告

    Args:
        import_id: 導入任務ID
    """
    try:
        if import_id not in IMPORT_STATUS:
            raise HTTPException(
                status_code=404,
                detail=f"導入任務不存在: {import_id}"
            )

        status = IMPORT_STATUS[import_id]

        if status.status != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"導入尚未完成，當前狀態: {status.status}"
            )

        # 讀取報告文件
        report_path = status.result.get('report_path')
        if not report_path or not os.path.exists(report_path):
            raise HTTPException(
                status_code=404,
                detail="報告文件不存在"
            )

        with open(report_path, 'r', encoding='utf-8') as f:
            report_content = f.read()

        return APIResponse.success(
            data={
                'import_id': import_id,
                'status': status.status,
                'report': report_content,
                'summary': status.result
            },
            message="報告獲取成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取報告失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取報告失敗: {str(e)}")


@router.get("/tasks/validate", response_model=APIResponse)
async def validate_imported_tasks(
    repo_manager=Depends(get_repository_manager)
):
    """
    驗證已導入的任務
    """
    try:
        import_service = TaskImportService(
            task_repo=repo_manager.task_repo,
            sprint_repo=repo_manager.sprint_repo
        )

        validation = await import_service.validate_imported_tasks()

        return APIResponse.success(
            data=validation,
            message="驗證完成"
        )

    except Exception as e:
        logger.error(f"驗證任務失敗: {e}")
        raise HTTPException(status_code=500, detail=f"驗證失敗: {str(e)}")


@router.get("/tasks/list", response_model=APIResponse)
async def list_import_status():
    """列出所有導入任務"""
    try:
        imports = list(IMPORT_STATUS.values())
        imports.sort(key=lambda x: x.task_id, reverse=True)

        return APIResponse.success(
            data={
                'imports': [i.dict() for i in imports],
                'total': len(imports)
            },
            message=f"共 {len(imports)} 個導入任務"
        )

    except Exception as e:
        logger.error(f"列出導入任務失敗: {e}")
        raise HTTPException(status_code=500, detail=f"列出任務失敗: {str(e)}")
