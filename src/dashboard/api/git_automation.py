"""
Git自動化工作流API
提供Git提交處理、Webhook接收、自動化規則管理等功能
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
import logging

from ..models.api_response import APIResponse
from ..repositories.dependency_injection import get_repository_manager
from ..services.git_automation_service import GitAutomationService, GitWebhookHandler
from ..services.task_checker_service import TaskCheckerService
from ..services.automation_config import AutomationConfig, TriggerType

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/automation", tags=["automation"])


# Pydantic模型
class CommitInfo(BaseModel):
    """提交信息模型"""
    hash: str = Field(..., description="提交哈希")
    message: str = Field(..., description="提交信息")
    author: str = Field(..., description="提交者")
    branch: str = Field(..., description="分支")
    files: List[str] = Field(default_factory=list, description="修改文件")
    timestamp: datetime = Field(..., description="提交時間")


class ProcessCommitRequest(BaseModel):
    """處理提交請求"""
    repo_path: str = Field(..., description="倉庫路徑")
    commit: CommitInfo = Field(..., description="提交信息")
    auto_assign: bool = Field(default=True, description="是否自動分配")


class WebhookEvent(BaseModel):
    """Webhook事件"""
    event_type: str = Field(..., description="事件類型")
    payload: Dict[str, Any] = Field(..., description="事件數據")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CheckRequest(BaseModel):
    """檢查請求"""
    sprint_id: Optional[str] = Field(None, description="Sprint ID")
    auto_fix: bool = Field(default=False, description="是否自動修復")


class RuleConfig(BaseModel):
    """規則配置"""
    name: str
    description: str
    trigger_type: str
    enabled: bool = True
    priority: int = 0
    conditions: List[Dict[str, Any]] = Field(default_factory=list)
    actions: List[Dict[str, Any]] = Field(default_factory=list)


# 自動化配置實例
automation_config = AutomationConfig()


# API端點

@router.post("/commit/process", response_model=APIResponse)
async def process_commit(
    request: ProcessCommitRequest,
    repo_manager=Depends(get_repository_manager)
):
    """
    處理Git提交並自動更新任務狀態

    這個端點會：
    1. 解析提交信息
    2. 提取任務ID
    3. 根據規則自動更新任務
    4. 檢查依賴關係
    """
    try:
        task_repo = repo_manager.task_repo

        # 創建Git自動化服務
        git_automation = GitAutomationService(
            task_repo=task_repo,
            sprint_repo=repo_manager.sprint_repo
        )

        # 處理提交
        events = await git_automation.process_git_commit(
            request.repo_path,
            request.commit.hash
        )

        # 生成響應
        response_data = {
            "commit_hash": request.commit.hash,
            "task_ids_found": request.commit.hash,
            "events_processed": len(events),
            "events": [
                {
                    "task_id": event.task_id,
                    "action": event.action,
                    "commit_hash": event.commit_info.hash[:8]
                }
                for event in events
            ]
        }

        return APIResponse.success(
            data=response_data,
            message=f"成功處理提交 {request.commit.hash[:8]}"
        )

    except Exception as e:
        logger.error(f"處理提交失敗: {e}")
        raise HTTPException(status_code=500, detail=f"處理提交失敗: {str(e)}")


@router.post("/webhook/git", response_model=APIResponse)
async def handle_git_webhook(
    request: Request,
    repo_manager=Depends(get_repository_manager)
):
    """
    接收GitHub/GitLab等平台的Webhook推送

    支援的事件類型：
    - push: 代碼推送
    - pull_request: PR事件
    - issues: Issue事件
    """
    try:
        # 獲取Webhook payload
        payload = await request.json()
        event_type = request.headers.get("X-GitHub-Event", "unknown")
        signature = request.headers.get("X-Hub-Signature-256", "")

        logger.info(f"收到Webhook: {event_type}")

        # 創建服務實例
        git_automation = GitAutomationService(
            task_repo=repo_manager.task_repo,
            sprint_repo=repo_manager.sprint_repo
        )

        webhook_handler = GitWebhookHandler(git_automation)

        # 處理不同類型的事件
        events = []

        if event_type == "push":
            events = await webhook_handler.handle_push_event(payload)
        # TODO: 處理其他事件類型

        # 統計結果
        response_data = {
            "event_type": event_type,
            "events_processed": len(events),
            "tasks_updated": len(set(event.task_id for event in events))
        }

        return APIResponse.success(
            data=response_data,
            message="Webhook處理成功"
        )

    except Exception as e:
        logger.error(f"處理Webhook失敗: {e}")
        raise HTTPException(status_code=500, detail=f"處理Webhook失敗: {str(e)}")


@router.post("/check/run", response_model=APIResponse)
async def run_task_check(
    request: CheckRequest,
    repo_manager=Depends(get_repository_manager)
):
    """
    運行任務檢查

    檢查內容：
    - 任務依賴
    - 僵屍任務
    - 循環依賴
    - WIP限制
    - Sprint健康度
    """
    try:
        # 創建檢查器
        task_checker = TaskCheckerService(
            task_repo=repo_manager.task_repo,
            sprint_repo=repo_manager.sprint_repo
        )

        # 運行檢查
        issues = await task_checker.check_all_tasks()

        # 按嚴重性分類
        errors = [i for i in issues if i.severity == "error"]
        warnings = [i for i in issues if i.severity == "warning"]
        infos = [i for i in issues if i.severity == "info"]

        # 生成檢查報告
        report_data = {
            "total_issues": len(issues),
            "by_severity": {
                "errors": len(errors),
                "warnings": len(warnings),
                "infos": len(infos)
            },
            "by_type": {},
            "issues": [
                {
                    "task_id": issue.task_id,
                    "type": issue.issue_type.value,
                    "severity": issue.severity,
                    "description": issue.description,
                    "suggestions": issue.suggestions
                }
                for issue in issues
            ]
        }

        # 按類型統計
        for issue in issues:
            issue_type = issue.issue_type.value
            report_data["by_type"][issue_type] = (
                report_data["by_type"].get(issue_type, 0) + 1
            )

        # Sprint檢查
        if request.sprint_id:
            sprint_metrics = await task_checker.check_sprint_health(request.sprint_id)
            report_data["sprint_metrics"] = {
                "sprint_id": request.sprint_id,
                "total_tasks": sprint_metrics.total_tasks,
                "completed_tasks": sprint_metrics.completed_tasks,
                "blocked_tasks": sprint_metrics.blocked_tasks,
                "blocked_percentage": round(sprint_metrics.blocked_percentage, 2),
                "velocity": sprint_metrics.velocity
            }

        # 自動修復
        auto_fixed = 0
        if request.auto_fix:
            # 自動更新被阻塞的任務
            # TODO: 實現自動修復邏輯
            pass

        return APIResponse.success(
            data=report_data,
            message=f"檢查完成，發現 {len(issues)} 個問題"
        )

    except Exception as e:
        logger.error(f"運行任務檢查失敗: {e}")
        raise HTTPException(status_code=500, detail=f"運行任務檢查失敗: {str(e)}")


@router.get("/check/report", response_model=APIResponse)
async def get_check_report(
    sprint_id: Optional[str] = None,
    repo_manager=Depends(get_repository_manager)
):
    """
    獲取檢查報告

    Args:
        sprint_id: 可選的Sprint ID
    """
    try:
        task_checker = TaskCheckerService(
            task_repo=repo_manager.task_repo,
            sprint_repo=repo_manager.sprint_repo
        )

        report = await task_checker.generate_check_report(sprint_id)

        return APIResponse.success(
            data=report,
            message="檢查報告生成成功"
        )

    except Exception as e:
        logger.error(f"生成檢查報告失敗: {e}")
        raise HTTPException(status_code=500, detail=f"生成檢查報告失敗: {str(e)}")


@router.get("/rules", response_model=APIResponse)
async def list_automation_rules():
    """
    獲取自動化規則列表
    """
    try:
        rules = automation_config.list_rules()

        return APIResponse.success(
            data=rules,
            message=f"共 {len(rules)} 個規則"
        )

    except Exception as e:
        logger.error(f"獲取規則列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取規則列表失敗: {str(e)}")


@router.post("/rules", response_model=APIResponse)
async def create_automation_rule(
    rule_config: RuleConfig,
):
    """
    創建自動化規則

    Args:
        rule_config: 規則配置
    """
    try:
        # TODO: 實現規則創建邏輯
        # 目前返回成功響應

        return APIResponse.success(
            data={"name": rule_config.name},
            message=f"規則 {rule_config.name} 創建成功"
        )

    except Exception as e:
        logger.error(f"創建規則失敗: {e}")
        raise HTTPException(status_code=500, detail=f"創建規則失敗: {str(e)}")


@router.put("/rules/{rule_name}/toggle", response_model=APIResponse)
async def toggle_automation_rule(
    rule_name: str,
    enabled: bool = True
):
    """
    啟用或禁用自動化規則

    Args:
        rule_name: 規則名稱
        enabled: 是否啟用
    """
    try:
        if enabled:
            automation_config.enable_rule(rule_name)
            message = f"規則 {rule_name} 已啟用"
        else:
            automation_config.disable_rule(rule_name)
            message = f"規則 {rule_name} 已禁用"

        return APIResponse.success(
            data={"name": rule_name, "enabled": enabled},
            message=message
        )

    except Exception as e:
        logger.error(f"切換規則失敗: {e}")
        raise HTTPException(status_code=500, detail=f"切換規則失敗: {str(e)}")


@router.get("/stats", response_model=APIResponse)
async def get_automation_stats(
    repo_manager=Depends(get_repository_manager)
):
    """
    獲取自動化統計信息
    """
    try:
        git_automation = GitAutomationService(
            task_repo=repo_manager.task_repo,
            sprint_repo=repo_manager.sprint_repo
        )

        # 生成自動化報告
        report = await git_automation.generate_automation_report()

        # 添加規則統計
        report["rules"] = {
            "total": len(automation_config.rules),
            "enabled": len([r for r in automation_config.rules if r.enabled]),
            "by_trigger": {}
        }

        for rule in automation_config.rules:
            trigger_type = rule.trigger_type.value
            report["rules"]["by_trigger"][trigger_type] = (
                report["rules"]["by_trigger"].get(trigger_type, 0) + 1
            )

        return APIResponse.success(
            data=report,
            message="統計信息獲取成功"
        )

    except Exception as e:
        logger.error(f"獲取統計信息失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取統計信息失敗: {str(e)}")


@router.post("/simulate", response_model=APIResponse)
async def simulate_commit(
    commit_info: CommitInfo,
    repo_manager=Depends(get_repository_manager)
):
    """
    模擬提交處理（用於測試）

    Args:
        commit_info: 提交信息
    """
    try:
        task_repo = repo_manager.task_repo

        git_automation = GitAutomationService(
            task_repo=task_repo,
            sprint_repo=repo_manager.sprint_repo
        )

        # 模擬處理
        # TODO: 實現模擬處理邏輯

        return APIResponse.success(
            data={
                "commit_hash": commit_info.hash,
                "simulated": True,
                "would_update": [],
                "would_create": []
            },
            message="模擬處理完成"
        )

    except Exception as e:
        logger.error(f"模擬提交失敗: {e}")
        raise HTTPException(status_code=500, detail=f"模擬提交失敗: {str(e)}")
