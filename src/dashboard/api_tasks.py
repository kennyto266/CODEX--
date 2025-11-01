"""
任務管理API
港股量化交易系統 - 項目管理模組

提供任務的CRUD操作、狀態流轉、分配、查詢等功能
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, Body, Path
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
import logging

from .models.task_status import TaskStatus, Priority
from .models.api_response import APIResponse
from .repositories.dependency_injection import get_task_repository, get_db
from .repositories.task_repository import TaskRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["tasks"])

# Pydantic模型定義
class TaskCreate(BaseModel):
    """任務創建模型"""
    title: str = Field(..., min_length=3, max_length=200, description="任務標題")
    description: Optional[str] = Field(None, max_length=2000, description="任務描述")
    priority: Priority = Field(default=Priority.P2, description="優先級")
    estimated_hours: int = Field(..., gt=0, le=100, description="預估工時")
    assignee: Optional[str] = Field(None, max_length=100, description="被分配者")
    sprint: Optional[str] = Field(None, max_length=50, description="所屬Sprint")
    acceptance_criteria: List[str] = Field(default_factory=list, description="驗收標準")
    deliverables: List[str] = Field(default_factory=list, description="交付物")
    dependencies: List[str] = Field(default_factory=list, description="前置依賴")

    @validator('title')
    def title_must_start_with_verb(cls, v):
        """驗證任務標題必須以動詞開頭"""
        verbs = ['創建', '重構', '實現', '優化', '修復', '添加', '更新', '刪除', '測試', '部署', '配置', '設計']
        if not any(v.startswith(verb) for verb in verbs):
            raise ValueError('任務標題必須以動詞開頭 (如：創建、重構、實現等)')
        return v


class TaskUpdate(BaseModel):
    """任務更新模型"""
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    priority: Optional[Priority] = None
    estimated_hours: Optional[int] = Field(None, gt=0, le=100)
    actual_hours: Optional[int] = Field(None, ge=0)
    assignee: Optional[str] = Field(None, max_length=100)
    sprint: Optional[str] = Field(None, max_length=50)
    acceptance_criteria: Optional[List[str]] = None
    deliverables: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class TaskStatusTransition(BaseModel):
    """任務狀態流轉模型"""
    new_status: TaskStatus = Field(..., description="目標狀態")
    comment: Optional[str] = Field(None, max_length=500, description="變更說明")


class TaskAssign(BaseModel):
    """任務分配模型"""
    assignee: str = Field(..., max_length=100, description="被分配者")


class TaskResponse(BaseModel):
    """任務響應模型"""
    id: str
    title: str
    description: Optional[str]
    status: str
    priority: str
    estimated_hours: int
    actual_hours: Optional[int]
    assignee: Optional[str]
    reporter: str
    sprint: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]
    progress_percentage: float
    is_blocked: bool
    is_completed: bool

    class Config:
        orm_mode = True


@router.get("/tasks", response_model=APIResponse)
async def list_tasks(
    status: Optional[TaskStatus] = Query(None, description="按狀態過濾"),
    priority: Optional[Priority] = Query(None, description="按優先級過濾"),
    assignee: Optional[str] = Query(None, description="按被分配者過濾"),
    sprint: Optional[str] = Query(None, description="按Sprint過濾"),
    reporter: Optional[str] = Query(None, description="按創建者過濾"),
    search: Optional[str] = Query(None, description="搜索關鍵詞"),
    page: int = Query(1, ge=1, description="頁碼"),
    limit: int = Query(20, ge=1, le=100, description="每頁數量"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序方向"),
    task_repo: TaskRepository = Depends(get_task_repository)
):
    """
    獲取任務列表，支持多維度過濾和分頁
    """
    try:
        # 構建過濾條件
        filters = {}

        if status:
            filters['status'] = status
        if priority:
            filters['priority'] = priority
        if assignee:
            filters['assignee'] = assignee
        if sprint:
            filters['sprint'] = sprint
        if reporter:
            filters['reporter'] = reporter
        if search:
            filters['search'] = search

        # 查詢任務
        tasks = await task_repo.list(
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=(page - 1) * limit
        )

        # 獲取總數
        total = await task_repo.count(filters=filters)

        # 轉換為字典格式
        tasks_data = [task.to_dict() for task in tasks]

        return APIResponse.success(
            data=tasks_data,
            meta={
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit,
                "filters": {
                    "status": status.value if status else None,
                    "priority": priority.value if priority else None,
                    "assignee": assignee,
                    "sprint": sprint,
                    "search": search
                }
            }
        )

    except Exception as e:
        logger.error(f"獲取任務列表失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取任務列表失敗: {str(e)}")


@router.post("/tasks", response_model=APIResponse, status_code=201)
async def create_task(
    task_data: TaskCreate,
    task_repo: TaskRepository = Depends(get_task_repository)
):
    """
    創建新任務
    """
    try:
        # 準備任務數據
        task_dict = task_data.dict()
        task_dict['reporter'] = "當前用戶"  # TODO: 從認證上下文獲取
        task_dict['story_points'] = task_repo._calculate_story_points(task_data.estimated_hours)

        # 創建任務
        task = await task_repo.create(task_dict)

        if not task:
            raise HTTPException(status_code=500, detail="創建任務失敗")

        return APIResponse.success(
            data=task.to_dict(),
            message="任務創建成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"創建任務失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"創建任務失敗: {str(e)}")


@router.get("/tasks/{task_id}", response_model=APIResponse)
async def get_task(
    task_id: str = Path(..., description="任務ID"),
    task_repo: TaskRepository = Depends(get_task_repository)
):
    """
    獲取任務詳情
    """
    try:
        task = await task_repo.get_by_id(task_id)

        if not task:
            raise HTTPException(status_code=404, detail="任務不存在")

        return APIResponse.success(data=task.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取任務詳情失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取任務詳情失敗: {str(e)}")


@router.put("/tasks/{task_id}", response_model=APIResponse)
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    task_repo: TaskRepository = Depends(get_task_repository)
):
    """
    更新任務
    """
    try:
        update_dict = task_data.dict(exclude_unset=True)

        task = await task_repo.update(task_id, update_dict)

        if not task:
            raise HTTPException(status_code=404, detail="任務不存在或更新失敗")

        return APIResponse.success(
            data=task.to_dict(),
            message="任務更新成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新任務失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新任務失敗: {str(e)}")


@router.delete("/tasks/{task_id}", response_model=APIResponse)
async def delete_task(
    task_id: str,
    task_repo: TaskRepository = Depends(get_task_repository)
):
    """
    刪除任務
    """
    try:
        success = await task_repo.delete(task_id)

        if not success:
            raise HTTPException(status_code=404, detail="任務不存在或刪除失敗")

        return APIResponse.success(
            data=None,
            message="任務刪除成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刪除任務失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"刪除任務失敗: {str(e)}")


@router.post("/tasks/{task_id}/transition", response_model=APIResponse)
async def transition_task(
    task_id: str,
    transition: TaskStatusTransition,
    task_repo: TaskRepository = Depends(get_task_repository)
):
    """
    任務狀態流轉
    """
    try:
        task = await task_repo.transition_status(
            task_id,
            transition.new_status,
            transition.comment
        )

        if not task:
            raise HTTPException(status_code=404, detail="任務不存在或狀態轉換失敗")

        return APIResponse.success(
            data=task.to_dict(),
            message="狀態轉換成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"狀態轉換失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"狀態轉換失敗: {str(e)}")


@router.post("/tasks/{task_id}/assign", response_model=APIResponse)
async def assign_task(
    task_id: str,
    assign_data: TaskAssign,
    task_repo: TaskRepository = Depends(get_task_repository)
):
    """
    分配任務
    """
    try:
        task = await task_repo.assign_task(task_id, assign_data.assignee)

        if not task:
            raise HTTPException(status_code=404, detail="任務不存在或分配失敗")

        return APIResponse.success(
            data=task.to_dict(),
            message="任務分配成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分配任務失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分配任務失敗: {str(e)}")


@router.post("/tasks/bulk", response_model=APIResponse)
async def bulk_update_tasks(
    task_ids: List[str],
    updates: TaskUpdate,
    task_repo: TaskRepository = Depends(get_task_repository)
):
    """
    批量更新任務
    """
    try:
        update_dict = updates.dict(exclude_unset=True)
        updated_tasks = await task_repo.update_many(task_ids, update_dict)

        return APIResponse.success(
            data={"updated_count": len(updated_tasks)},
            message=f"成功更新 {len(updated_tasks)} 個任務"
        )

    except Exception as e:
        logger.error(f"批量更新任務失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量更新任務失敗: {str(e)}")


@router.get("/tasks/search", response_model=APIResponse)
async def search_tasks(
    q: str = Query(..., description="搜索關鍵詞"),
    fields: Optional[List[str]] = Query(None, description="搜索字段"),
    task_repo: TaskRepository = Depends(get_task_repository)
):
    """
    搜索任務
    """
    try:
        # 使用 Repository 的 list 方法進行搜索
        tasks = await task_repo.list(
            filters={'search': q},
            limit=100
        )

        tasks_data = [task.to_dict() for task in tasks]

        return APIResponse.success(
            data=tasks_data,
            meta={"query": q, "fields": fields, "total": len(tasks_data)}
        )

    except Exception as e:
        logger.error(f"搜索任務失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索任務失敗: {str(e)}")


@router.get("/tasks/metrics", response_model=APIResponse)
async def get_task_metrics(
    sprint: Optional[str] = Query(None, description="按Sprint過濾"),
    task_repo: TaskRepository = Depends(get_task_repository)
):
    """
    獲取任務統計指標
    """
    try:
        filters = {}
        if sprint:
            filters['sprint'] = sprint

        metrics = await task_repo.get_task_statistics(sprint)

        return APIResponse.success(data=metrics)

    except Exception as e:
        logger.error(f"獲取任務指標失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取任務指標失敗: {str(e)}")


@router.get("/tasks/blocked", response_model=APIResponse)
async def get_blocked_tasks(
    task_repo: TaskRepository = Depends(get_task_repository)
):
    """
    獲取所有被阻塞的任務
    """
    try:
        blocked_tasks = await task_repo.get_blocked_tasks()
        tasks_data = [task.to_dict() for task in blocked_tasks]

        return APIResponse.success(
            data=tasks_data,
            message=f"找到 {len(tasks_data)} 個被阻塞的任務"
        )

    except Exception as e:
        logger.error(f"獲取阻塞任務失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取阻塞任務失敗: {str(e)}")


@router.post("/tasks/{task_id}/dependencies", response_model=APIResponse)
async def add_dependency(
    task_id: str,
    dependency_id: str = Body(..., description="依賴的任務ID"),
    task_repo: TaskRepository = Depends(get_task_repository)
):
    """
    添加前置依賴
    """
    try:
        task = await task_repo.add_dependency(task_id, dependency_id)

        if not task:
            raise HTTPException(status_code=400, detail="添加依賴失敗")

        return APIResponse.success(
            data=task.to_dict(),
            message="依賴添加成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加依賴失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加依賴失敗: {str(e)}")

