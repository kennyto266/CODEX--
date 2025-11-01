"""
任務檢查器服務
實現任務依賴檢查、阻塞檢測、僵屍任務檢測等功能
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum

from ..repositories.task_repository import TaskRepository
from ..repositories.sprint_repository import SprintRepository

logger = logging.getLogger(__name__)


class IssueType(Enum):
    """問題類型"""
    BLOCKED = "blocked"  # 被阻塞
    STALE = "stale"      # 長時間未更新
    OVERDUE = "overdue"  # 逾期
    CIRCULAR_DEP = "circular_dep"  # 循環依賴
    WIP_LIMIT = "wip_limit"  # 超過WIP限制


@dataclass
class TaskIssue:
    """任務問題"""
    task_id: str
    issue_type: IssueType
    severity: str  # info, warning, error
    description: str
    suggestions: List[str]
    metadata: Dict[str, Any]


@dataclass
class SprintMetrics:
    """Sprint指標"""
    sprint_id: str
    total_tasks: int
    completed_tasks: int
    blocked_tasks: int
    blocked_percentage: float
    velocity: float
    burndown_data: List[Dict[str, Any]]
    risks: List[TaskIssue]


class TaskCheckerService:
    """
    任務檢查器服務

    功能：
    - 檢查任務依賴
    - 檢測被阻塞的任務
    - 識別僵屍任務
    - 檢測循環依賴
    - 檢查Sprint健康度
    - 生成檢查報告
    """

    def __init__(self, task_repo: TaskRepository, sprint_repo: SprintRepository):
        """初始化服務

        Args:
            task_repo: 任務Repository實例
            sprint_repo: Sprint Repository實例
        """
        self.task_repo = task_repo
        self.sprint_repo = sprint_repo

    async def check_all_tasks(self) -> List[TaskIssue]:
        """檢查所有任務

        Returns:
            問題列表
        """
        issues = []

        try:
            # 獲取所有任務
            all_tasks = await self.task_repo.list(limit=10000)

            # 檢查依賴
            dep_issues = await self._check_dependencies(all_tasks)
            issues.extend(dep_issues)

            # 檢查僵屍任務
            stale_issues = await self._check_stale_tasks(all_tasks)
            issues.extend(stale_issues)

            # 檢查逾期任務
            overdue_issues = await self._check_overdue_tasks(all_tasks)
            issues.extend(overdue_issues)

            # 檢查循環依賴
            circular_issues = await self._check_circular_dependencies(all_tasks)
            issues.extend(circular_issues)

            # 檢查WIP限制
            wip_issues = await self._check_wip_limits(all_tasks)
            issues.extend(wip_issues)

            logger.info(f"完成任務檢查，共發現 {len(issues)} 個問題")

            return issues

        except Exception as e:
            logger.error(f"檢查任務失敗: {e}")
            return []

    async def check_sprint_health(self, sprint_id: str) -> SprintMetrics:
        """檢查Sprint健康度

        Args:
            sprint_id: Sprint ID

        Returns:
            Sprint指標
        """
        try:
            sprint = await self.sprint_repo.get_by_id(sprint_id)
            if not sprint:
                raise ValueError(f"Sprint不存在: {sprint_id}")

            # 獲取Sprint任務
            sprint_tasks = await self.sprint_repo.get_sprint_tasks(sprint_id)

            # 統計數據
            total_tasks = len(sprint_tasks)
            completed_tasks = sum(1 for t in sprint_tasks if t.status.value == "已完成")
            blocked_tasks = sum(1 for t in sprint_tasks if t.status.value == "已阻塞")

            blocked_percentage = (
                (blocked_tasks / total_tasks * 100)
                if total_tasks > 0 else 0
            )

            # 計算速度
            velocity = sprint.velocity or 0

            # 生成燃盡圖數據
            burndown_data = await self._generate_burndown_data(sprint, sprint_tasks)

            # 檢查風險
            risks = await self._check_sprint_risks(sprint, sprint_tasks)

            return SprintMetrics(
                sprint_id=sprint_id,
                total_tasks=total_tasks,
                completed_tasks=completed_tasks,
                blocked_tasks=blocked_tasks,
                blocked_percentage=blocked_percentage,
                velocity=velocity,
                burndown_data=burndown_data,
                risks=risks
            )

        except Exception as e:
            logger.error(f"檢查Sprint健康度失敗 ({sprint_id}): {e}")
            raise

    async def _check_dependencies(self, tasks: List) -> List[TaskIssue]:
        """檢查任務依賴

        Args:
            tasks: 任務列表

        Returns:
            問題列表
        """
        issues = []
        task_map = {task.id: task for task in tasks}

        for task in tasks:
            if not task.dependencies:
                continue

            unsatisfied_deps = []
            for dep_id in task.dependencies:
                dep_task = task_map.get(dep_id)
                if not dep_task:
                    unsatisfied_deps.append(f"{dep_id} (不存在)")
                elif dep_task.status.value != "已完成":
                    unsatisfied_deps.append(f"{dep_id} (狀態: {dep_task.status.value})")

            if unsatisfied_deps and task.status.value != "已阻塞":
                issues.append(TaskIssue(
                    task_id=task.id,
                    issue_type=IssueType.BLOCKED,
                    severity="warning",
                    description=f"任務被阻塞，等待依賴: {', '.join(unsatisfied_deps)}",
                    suggestions=[
                        "檢查依賴任務狀態",
                        "聯繫依賴任務負責人",
                        "考慮調整任務優先級"
                    ],
                    metadata={
                        "dependencies": task.dependencies,
                        "unsatisfied": unsatisfied_deps
                    }
                ))

        return issues

    async def _check_stale_tasks(self, tasks: List) -> List[TaskIssue]:
        """檢查僵屍任務

        Args:
            tasks: 任務列表

        Returns:
            問題列表
        """
        issues = []
        stale_threshold = datetime.utcnow() - timedelta(days=3)

        for task in tasks:
            # 檢查長時間未更新的進行中任務
            if (task.status.value == "進行中" and
                task.updated_at and
                task.updated_at < stale_threshold):

                issues.append(TaskIssue(
                    task_id=task.id,
                    issue_type=IssueType.STALE,
                    severity="warning",
                    description=f"任務已超過3天未更新",
                    suggestions=[
                        "更新任務進度",
                        "聯繫任務負責人",
                        "考慮重新分配或拆分任務"
                    ],
                    metadata={
                        "last_update": task.updated_at.isoformat(),
                        "days_since_update": (datetime.utcnow() - task.updated_at).days
                    }
                ))

        return issues

    async def _check_overdue_tasks(self, tasks: List) -> List[TaskIssue]:
        """檢查逾期任務

        Args:
            tasks: 任務列表

        Returns:
            問題列表
        """
        issues = []
        # 假設Sprint有結束日期
        # 實際實現中需要從Sprint獲取

        return issues

    async def _check_circular_dependencies(self, tasks: List) -> List[TaskIssue]:
        """檢查循環依賴

        Args:
            tasks: 任務列表

        Returns:
            問題列表
        """
        issues = []
        task_map = {task.id: task for task in tasks}

        # 使用DFS檢測循環
        visited = set()
        rec_stack = set()

        def has_cycle(task_id: str, path: List[str]) -> bool:
            if task_id in rec_stack:
                # 發現循環
                cycle_start = path.index(task_id)
                cycle = " -> ".join(path[cycle_start:] + [task_id])

                issues.append(TaskIssue(
                    task_id=task_id,
                    issue_type=IssueType.CIRCULAR_DEP,
                    severity="error",
                    description=f"發現循環依賴: {cycle}",
                    suggestions=[
                        "重新設計任務依賴關係",
                        "拆分任務或調整順序",
                        "檢查任務業務邏輯"
                    ],
                    metadata={
                        "cycle": cycle,
                        "path": path
                    }
                ))
                return True

            if task_id in visited:
                return False

            visited.add(task_id)
            rec_stack.add(task_id)
            path.append(task_id)

            task = task_map.get(task_id)
            if task and task.dependencies:
                for dep_id in task.dependencies:
                    if has_cycle(dep_id, path):
                        return True

            rec_stack.remove(task_id)
            path.pop()
            return False

        # 檢查所有任務
        for task in tasks:
            if task.id not in visited:
                has_cycle(task.id, [])

        return issues

    async def _check_wip_limits(self, tasks: List) -> List[TaskIssue]:
        """檢查WIP限制

        Args:
            tasks: 任務列表

        Returns:
            問題列表
        """
        issues = []
        # 統計每個被分配者的進行中任務數
        assignee_wip = {}

        for task in tasks:
            if task.status.value == "進行中" and task.assignee:
                assignee_wip.setdefault(task.assignee, 0)
                assignee_wip[task.assignee] += 1

        # WIP限制（例如：每人最多3個同時進行的任務）
        WIP_LIMIT = 3

        for assignee, wip_count in assignee_wip.items():
            if wip_count > WIP_LIMIT:
                issues.append(TaskIssue(
                    task_id=f"ASSIGNEE_{assignee}",
                    issue_type=IssueType.WIP_LIMIT,
                    severity="info",
                    description=f"{assignee} 有 {wip_count} 個同時進行的任務，超過限制 {WIP_LIMIT}",
                    suggestions=[
                        "重新分配任務",
                        "優先完成部分任務",
                        "考慮延遲非緊急任務"
                    ],
                    metadata={
                        "assignee": assignee,
                        "wip_count": wip_count,
                        "limit": WIP_LIMIT
                    }
                ))

        return issues

    async def _generate_burndown_data(
        self,
        sprint,
        tasks: List
    ) -> List[Dict[str, Any]]:
        """生成燃盡圖數據

        Args:
            sprint: Sprint對象
            tasks: 任務列表

        Returns:
            燃盡圖數據
        """
        # 簡化實現：返回Sprint現有的燃盡數據
        return sprint.burndown_data.get("remaining", [])

    async def _check_sprint_risks(
        self,
        sprint,
        tasks: List
    ) -> List[TaskIssue]:
        """檢查Sprint風險

        Args:
            sprint: Sprint對象
            tasks: 任務列表

        Returns:
            風險列表
        """
        risks = []

        # 檢查阻塞任務比例
        blocked_count = sum(1 for t in tasks if t.status.value == "已阻塞")
        total_count = len(tasks)

        if total_count > 0 and (blocked_count / total_count) > 0.3:
            risks.append(TaskIssue(
                task_id=sprint.id,
                issue_type=IssueType.BLOCKED,
                severity="warning",
                description=f"Sprint中 {blocked_count}/{total_count} ({blocked_count/total_count*100:.1f}%) 的任務被阻塞",
                suggestions=[
                    "優先處理阻塞問題",
                    "重新評估任務優先級",
                    "考慮調整Sprint範圍"
                ],
                metadata={
                    "blocked_count": blocked_count,
                    "total_count": total_count
                }
            ))

        # 檢查進度落後
        # TODO: 根據燃盡圖數據檢查進度

        return risks

    async def generate_check_report(
        self,
        sprint_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """生成檢查報告

        Args:
            sprint_id: 可選的Sprint ID

        Returns:
            檢查報告
        """
        try:
            report = {
                "timestamp": datetime.utcnow().isoformat(),
                "sprint_id": sprint_id,
                "summary": {
                    "total_issues": 0,
                    "by_severity": {
                        "info": 0,
                        "warning": 0,
                        "error": 0
                    },
                    "by_type": {}
                },
                "issues": [],
                "sprint_metrics": None
            }

            # 獲取問題
            issues = await self.check_all_tasks()
            report["issues"] = [
                {
                    "task_id": issue.task_id,
                    "type": issue.issue_type.value,
                    "severity": issue.severity,
                    "description": issue.description,
                    "suggestions": issue.suggestions
                }
                for issue in issues
            ]

            # 統計摘要
            report["summary"]["total_issues"] = len(issues)

            for issue in issues:
                report["summary"]["by_severity"][issue.severity] += 1
                report["summary"]["by_type"][issue.issue_type.value] = \
                    report["summary"]["by_type"].get(issue.issue_type.value, 0) + 1

            # Sprint指標
            if sprint_id:
                metrics = await self.check_sprint_health(sprint_id)
                report["sprint_metrics"] = {
                    "total_tasks": metrics.total_tasks,
                    "completed_tasks": metrics.completed_tasks,
                    "blocked_tasks": metrics.blocked_tasks,
                    "blocked_percentage": metrics.blocked_percentage,
                    "velocity": metrics.velocity
                }

            return report

        except Exception as e:
            logger.error(f"生成檢查報告失敗: {e}")
            return {}


# 任務健康檢查器
class TaskHealthChecker:
    """
    任務健康檢查器
    定期檢查任務狀態並發送告警
    """

    def __init__(
        self,
        task_checker: TaskCheckerService,
        notification_service=None
    ):
        self.task_checker = task_checker
        self.notification_service = notification_service

    async def run_health_check(self) -> Dict[str, Any]:
        """運行健康檢查

        Returns:
            檢查結果
        """
        try:
            # 檢查所有任務
            issues = await self.task_checker.check_all_tasks()

            # 按嚴重性分類
            critical_issues = [i for i in issues if i.severity == "error"]
            warning_issues = [i for i in issues if i.severity == "warning"]

            # 發送通知（如果配置了通知服務）
            if critical_issues and self.notification_service:
                await self.notification_service.send_alert(
                    f"發現 {len(critical_issues)} 個嚴重問題",
                    [i.description for i in critical_issues]
                )

            # 自動修復部分問題
            auto_fixed = await self._auto_fix_issues(issues)

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "total_issues": len(issues),
                "critical_issues": len(critical_issues),
                "warning_issues": len(warning_issues),
                "auto_fixed": auto_fixed,
                "issues_summary": {
                    issue.issue_type.value: len([i for i in issues if i.issue_type == issue.issue_type])
                    for issue in issues
                }
            }

        except Exception as e:
            logger.error(f"運行健康檢查失敗: {e}")
            raise

    async def _auto_fix_issues(self, issues: List[TaskIssue]) -> int:
        """自動修復問題

        Args:
            issues: 問題列表

        Returns:
            修復數量
        """
        fixed_count = 0

        try:
            # 自動更新被阻塞的任務
            unblocked = await self.task_checker.task_repo.db  # 獲取數據庫實例
            # 注意：這裡需要調用實際的自動更新方法
            # unblocked_tasks = await self.task_checker.task_repo.auto_update_blocked_tasks()
            # fixed_count += len(unblocked_tasks)

            logger.info(f"自動修復 {fixed_count} 個問題")

        except Exception as e:
            logger.error(f"自動修復問題失敗: {e}")

        return fixed_count
