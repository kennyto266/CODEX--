"""
Sprint管理API
港股量化交易系統 - 項目管理模組

提供Sprint的CRUD操作、規劃、指標查詢等功能
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, Body, Path
from pydantic import BaseModel, Field, validator
import logging

from .models.task_status import SprintStatus
from .models.api_response import APIResponse
from .repositories.dependency_injection import get_sprint_repository, get_db
from .repositories.sprint_repository import SprintRepository
from .repositories.task_repository import TaskRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["sprints"])

# Pydantic模型定義
class SprintCreate(BaseModel):
    """Sprint創建模型"""
    name: str = Field(..., min_length=3, max_length=100, description="Sprint名稱")
    goal: Optional[str] = Field(None, description="Sprint目標")
    start_date: date = Field(..., description="開始日期")
    end_date: date = Field(..., description="結束日期")
    team_capacity: int = Field(default=40, gt=0, description="團隊容量 (工時)")
    estimated_velocity: Optional[float] = Field(None, description="預估速度")


class SprintUpdate(BaseModel):
    """Sprint更新模型"""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    goal: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    team_capacity: Optional[int] = Field(None, gt=0)
    estimated_velocity: Optional[float] = None
    retrospective_notes: Optional[str] = None


class SprintPlan(BaseModel):
    """Sprint規劃模型"""
    task_ids: List[str] = Field(..., description="任務ID列表")
    planned_hours: int = Field(..., ge=0, description="計劃工時")


class SprintResponse(BaseModel):
    """Sprint響應模型"""
    id: str
    name: str
    goal: Optional[str]
    start_date: date
    end_date: date
    duration_days: int
    status: str
    team_capacity: int
    planned_hours: int
    completed_hours: int
    completion_rate: Optional[float]
    velocity: Optional[float]
    remaining_days: int
    utilization_rate: float
    is_active: bool
    is_completed: bool

    class Config:
        orm_mode = True


@router.get("/sprints", response_model=APIResponse)
async def list_sprints(
    status: Optional[SprintStatus] = Query(None, description="按狀態過濾"),
    active_only: bool = Query(False, description="只獲取活躍Sprint"),
    page: int = Query(1, ge=1, description="頁碼"),
    limit: int = Query(20, ge=1, le=100, description="每頁數量"),
    sprint_repo: SprintRepository = Depends(get_sprint_repository)
):
    """
    獲取Sprint列表
    """
    try:
        filters = {}
        if status:
            filters['status'] = status
        if active_only:
            filters['active_only'] = True

        sprints = await sprint_repo.list(
            filters=filters,
            sort_by="start_date",
            sort_order="desc",
            limit=limit,
            offset=(page - 1) * limit
        )

        total = await sprint_repo.count(filters=filters)

        sprints_data = [sprint.to_dict() for sprint in sprints]

        return APIResponse.success(
            data=sprints_data,
            meta={
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit
            }
        )

    except Exception as e:
        logger.error(f"獲取Sprint列表失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取Sprint列表失敗: {str(e)}")


@router.post("/sprints", response_model=APIResponse, status_code=201)
async def create_sprint(sprint_data: SprintCreate):
    """
    創建新Sprint
    """
    try:
        # 驗證日期邏輯
        if sprint_data.end_date <= sprint_data.start_date:
            raise HTTPException(status_code=400, detail="結束日期必須晚於開始日期")

        # 生成Sprint ID
        sprint_id = f"SPRINT-{sprint_data.start_date.strftime('%Y-%m')}"

        # 創建Sprint對象
        sprint = Sprint(
            id=sprint_id,
            name=sprint_data.name,
            goal=sprint_data.goal,
            start_date=sprint_data.start_date,
            end_date=sprint_data.end_date,
            team_capacity=sprint_data.team_capacity,
            estimated_velocity=sprint_data.estimated_velocity,
            status=SprintStatus.PLANNING,
            created_at=datetime.utcnow()
        )

        # TODO: 保存到數據庫

        logger.info(f"Sprint創建成功: {sprint_id}")
        return APIResponse.success(
            data=sprint.to_dict(),
            meta={"message": "Sprint創建成功"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"創建Sprint失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"創建Sprint失敗: {str(e)}")


@router.get("/sprints/{sprint_id}", response_model=APIResponse)
async def get_sprint(sprint_id: str = Path(..., description="Sprint ID")):
    """
    獲取Sprint詳情
    """
    try:
        # TODO: 從數據庫查詢Sprint

        sprint = None
        if not sprint:
            raise HTTPException(status_code=404, detail="Sprint不存在")

        return APIResponse.success(data=sprint.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取Sprint詳情失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取Sprint詳情失敗: {str(e)}")


@router.put("/sprints/{sprint_id}", response_model=APIResponse)
async def update_sprint(
    sprint_id: str,
    sprint_data: SprintUpdate
):
    """
    更新Sprint
    """
    try:
        # TODO: 從數據庫查詢並更新Sprint

        return APIResponse.success(
            data={},
            meta={"message": "Sprint更新成功"}
        )

    except Exception as e:
        logger.error(f"更新Sprint失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新Sprint失敗: {str(e)}")


@router.delete("/sprints/{sprint_id}", response_model=APIResponse)
async def delete_sprint(sprint_id: str):
    """
    刪除Sprint
    """
    try:
        # TODO: 從數據庫刪除Sprint

        return APIResponse.success(
            data=None,
            meta={"message": "Sprint刪除成功"}
        )

    except Exception as e:
        logger.error(f"刪除Sprint失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"刪除Sprint失敗: {str(e)}")


@router.post("/sprints/{sprint_id}/plan", response_model=APIResponse)
async def plan_sprint(
    sprint_id: str,
    plan_data: SprintPlan
):
    """
    Sprint規劃 - 分配任務到Sprint
    """
    try:
        # TODO: 從數據庫獲取Sprint
        # 驗證任務存在
        # 更新Sprint的task_ids和planned_hours

        return APIResponse.success(
            data={},
            meta={
                "message": "Sprint規劃成功",
                "planned_tasks": len(plan_data.task_ids),
                "planned_hours": plan_data.planned_hours
            }
        )

    except Exception as e:
        logger.error(f"Sprint規劃失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sprint規劃失敗: {str(e)}")


@router.get("/sprints/{sprint_id}/metrics", response_model=APIResponse)
async def get_sprint_metrics(sprint_id: str):
    """
    獲取Sprint指標
    """
    try:
        # TODO: 計算Sprint相關指標

        metrics = {
            "completion_rate": 0.0,
            "velocity": 0.0,
            "burndown": {"days": [], "remaining": []},
            "capacity_utilization": 0.0,
            "tasks_planned": 0,
            "tasks_completed": 0,
            "tasks_in_progress": 0,
            "remaining_work": 0,
            "efficiency_score": 0.0
        }

        return APIResponse.success(data=metrics)

    except Exception as e:
        logger.error(f"獲取Sprint指標失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取Sprint指標失敗: {str(e)}")


@router.get("/sprints/{sprint_id}/burndown", response_model=APIResponse)
async def get_burndown_chart(sprint_id: str):
    """
    獲取燃盡圖數據
    """
    try:
        # TODO: 獲取燃盡圖數據

        burndown_data = {
            "ideal": [],  # 理想燃盡線
            "actual": [],  # 實際燃盡線
            "baseline_hours": 0,
            "current_remaining": 0
        }

        return APIResponse.success(data=burndown_data)

    except Exception as e:
        logger.error(f"獲取燃盡圖失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取燃盡圖失敗: {str(e)}")


@router.post("/sprints/{sprint_id}/activate", response_model=APIResponse)
async def activate_sprint(sprint_id: str):
    """
    啟動Sprint
    """
    try:
        # TODO: 將Sprint狀態設置為ACTIVE

        return APIResponse.success(
            data={},
            meta={"message": "Sprint已啟動"}
        )

    except Exception as e:
        logger.error(f"啟動Sprint失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"啟動Sprint失敗: {str(e)}")


@router.post("/sprints/{sprint_id}/complete", response_model=APIResponse)
async def complete_sprint(sprint_id: str):
    """
    完成Sprint
    """
    try:
        # TODO: 計算最終指標並將Sprint狀態設置為COMPLETED

        return APIResponse.success(
            data={},
            meta={"message": "Sprint已完成"}
        )

    except Exception as e:
        logger.error(f"完成Sprint失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"完成Sprint失敗: {str(e)}")


@router.get("/sprints/active", response_model=APIResponse)
async def get_active_sprint():
    """
    獲取當前活躍Sprint
    """
    try:
        # TODO: 查詢狀態為ACTIVE的Sprint

        sprint = None

        if not sprint:
            return APIResponse.success(
                data=None,
                meta={"message": "當前沒有活躍的Sprint"}
            )

        return APIResponse.success(data=sprint.to_dict())

    except Exception as e:
        logger.error(f"獲取活躍Sprint失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取活躍Sprint失敗: {str(e)}")


@router.get("/sprints/upcoming", response_model=APIResponse)
async def get_upcoming_sprints(
    limit: int = Query(5, ge=1, le=20, description="返回數量")
):
    """
    獲取即將到來的Sprint
    """
    try:
        # TODO: 查詢狀態為PLANNING且開始日期在未來的Sprint

        sprints = []

        return APIResponse.success(
            data=sprints,
            meta={"count": len(sprints)}
        )

    except Exception as e:
        logger.error(f"獲取即將到來的Sprint失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取即將到來的Sprint失敗: {str(e)}")


@router.get("/sprints/{sprint_id}/retrospective", response_model=APIResponse)
async def get_sprint_retrospective(sprint_id: str):
    """
    獲取Sprint回顧資料
    """
    try:
        # TODO: 獲取Sprint回顧相關數據

        retrospective = {
            "what_went_well": [],
            "what_could_be_improved": [],
            "action_items": [],
            "team_feedback": [],
            "metrics_comparison": {}  # 與上個Sprint的對比
        }

        return APIResponse.success(data=retrospective)

    except Exception as e:
        logger.error(f"獲取Sprint回顧失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取Sprint回顧失敗: {str(e)}")


@router.post("/sprints/{sprint_id}/add-improvement", response_model=APIResponse)
async def add_sprint_improvement(
    sprint_id: str,
    improvement: str = Body(..., description="改進建議")
):
    """
    添加Sprint改進建議
    """
    try:
        # TODO: 添加改進建議到Sprint

        return APIResponse.success(
            data=None,
            meta={"message": "改進建議已添加"}
        )

    except Exception as e:
        logger.error(f"添加改進建議失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加改進建議失敗: {str(e)}")
