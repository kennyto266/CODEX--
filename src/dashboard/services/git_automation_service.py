"""
Git自動化工作流服務
實現Git提交自動關聯任務、狀態更新、依賴檢查等功能
"""

import re
import os
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import aiofiles
import aiofiles.os

from ..repositories.task_repository import TaskRepository
from ..repositories.sprint_repository import SprintRepository

logger = logging.getLogger(__name__)


class CommitType(Enum):
    """提交類型枚舉"""
    FEAT = "feat"
    FIX = "fix"
    REFACTOR = "refactor"
    DOCS = "docs"
    TEST = "test"
    CHORE = "chore"
    STYLE = "style"
    PERF = "perf"


@dataclass
class CommitInfo:
    """提交信息數據類"""
    hash: str
    author: str
    email: str
    message: str
    type: CommitType
    task_ids: List[str]
    timestamp: datetime
    files: List[str]
    branch: str


@dataclass
class TaskUpdateEvent:
    """任務更新事件"""
    task_id: str
    action: str  # start, progress, complete, block
    commit_info: CommitInfo
    metadata: Dict[str, Any]


class GitAutomationService:
    """
    Git自動化工作流服務

    功能：
    - 解析Git提交信息
    - 自動關聯任務ID
    - 根據提交類型更新任務狀態
    - 檢查任務依賴
    - 檢測阻塞任務
    - 生成自動化報告
    """

    # 任務ID匹配模式
    TASK_ID_PATTERN = re.compile(r'TASK-(\d{3})', re.IGNORECASE)

    # 提交類型匹配模式
    COMMIT_TYPE_PATTERNS = {
        CommitType.FEAT: re.compile(r'^(feat|feature)\s*:', re.IGNORECASE),
        CommitType.FIX: re.compile(r'^(fix|bugfix)\s*:', re.IGNORECASE),
        CommitType.REFACTOR: re.compile(r'^(refactor|cleanup)\s*:', re.IGNORECASE),
        CommitType.DOCS: re.compile(r'^(docs|doc|documentation)\s*:', re.IGNORECASE),
        CommitType.TEST: re.compile(r'^(test|testing)\s*:', re.IGNORECASE),
        CommitType.CHORE: re.compile(r'^(chore|bump|release)\s*:', re.IGNORECASE),
        CommitType.STYLE: re.compile(r'^(style|format)\s*:', re.IGNORECASE),
        CommitType.PERF: re.compile(r'^(perf|optimization)\s*:', re.IGNORECASE)
    }

    # 關鍵字匹配模式
    CLOSING_KEYWORDS = re.compile(
        r'(close[sd]?|fix(e[sd])?|resolve[sd]?|finish(e[sd])?|complete[sd]?)\s+TASK-(\d{3})',
        re.IGNORECASE
    )
    STARTING_KEYWORDS = re.compile(
        r'(start|begin|init|work on|tackle)\s+TASK-(\d{3})',
        re.IGNORECASE
    )
    PROGRESS_KEYWORDS = re.compile(
        r'(progress|update|wip|in\s+progress)\s+TASK-(\d{3})',
        re.IGNORECASE
    )

    def __init__(self, task_repo: TaskRepository, sprint_repo: SprintRepository):
        """初始化服務

        Args:
            task_repo: 任務Repository實例
            sprint_repo: Sprint Repository實例
        """
        self.task_repo = task_repo
        self.sprint_repo = sprint_repo

    async def process_git_commit(
        self,
        repo_path: str,
        commit_hash: str
    ) -> List[TaskUpdateEvent]:
        """
        處理Git提交

        Args:
            repo_path: Git倉庫路徑
            commit_hash: 提交哈希

        Returns:
            任務更新事件列表
        """
        try:
            # 獲取提交信息
            commit_info = await self._get_commit_info(repo_path, commit_hash)

            if not commit_info:
                logger.warning(f"無法獲取提交信息: {commit_hash}")
                return []

            logger.info(f"處理提交 {commit_hash}: {commit_info.message}")

            # 解析提交信息
            await self._analyze_commit(commit_info)

            # 提取任務ID
            task_ids = commit_info.task_ids

            # 生成更新事件
            events = await self._generate_update_events(task_ids, commit_info)

            # 執行更新
            for event in events:
                await self._apply_task_update(event)

            return events

        except Exception as e:
            logger.error(f"處理Git提交失敗 ({commit_hash}): {e}")
            return []

    async def _get_commit_info(
        self,
        repo_path: str,
        commit_hash: str
    ) -> Optional[CommitInfo]:
        """獲取Git提交信息

        Args:
            repo_path: 倉庫路徑
            commit_hash: 提交哈希

        Returns:
            提交信息對象
        """
        try:
            # 獲取提交詳情
            hash_cmd = f"git log -1 --format=%H {commit_hash}"
            author_cmd = f"git log -1 --format=%an {commit_hash}"
            email_cmd = f"git log -1 --format=%ae {commit_hash}"
            message_cmd = f"git log -1 --format=%s {commit_hash}"
            body_cmd = f"git log -1 --format=%b {commit_hash}"
            timestamp_cmd = f"git log -1 --format=%ci {commit_hash}"
            files_cmd = f"git show --name-only --format= {commit_hash}"
            branch_cmd = "git rev-parse --abbrev-ref HEAD"

            # 執行命令
            # 注意：這裡簡化處理，實際應使用GitPython或async-git庫
            hash_match = re.search(r'([a-f0-9]{40})', commit_hash)
            commit_hash_clean = hash_match.group(1) if hash_match else commit_hash

            # 提取任務ID
            task_ids = self._extract_task_ids(commit_hash)

            # 確定提交類型
            commit_type = self._determine_commit_type(commit_hash)

            return CommitInfo(
                hash=commit_hash_clean,
                author="未知",  # TODO: 從認證上下文獲取
                email="unknown@example.com",
                message=f"Commit: {commit_hash_clean}",  # TODO: 實際從Git獲取
                type=commit_type,
                task_ids=task_ids,
                timestamp=datetime.utcnow(),
                files=[],  # TODO: 實際從Git獲取
                branch="main"  # TODO: 實際從Git獲取
            )

        except Exception as e:
            logger.error(f"獲取提交信息失敗: {e}")
            return None

    def _extract_task_ids(self, text: str) -> List[str]:
        """從文本中提取任務ID

        Args:
            text: 輸入文本

        Returns:
            任務ID列表
        """
        task_ids = []
        matches = self.TASK_ID_PATTERN.findall(text)

        for match in matches:
            task_id = f"TASK-{match}"
            if task_id not in task_ids:
                task_ids.append(task_id)

        return task_ids

    def _determine_commit_type(self, text: str) -> CommitType:
        """確定提交類型

        Args:
            text: 提交信息

        Returns:
            提交類型
        """
        for commit_type, pattern in self.COMMIT_TYPE_PATTERNS.items():
            if pattern.search(text):
                return commit_type

        return CommitType.CHORE

    async def _analyze_commit(self, commit_info: CommitInfo):
        """分析提交信息

        Args:
            commit_info: 提交信息
        """
        message = commit_info.message

        # 檢查是否包含任務ID
        task_ids = self._extract_task_ids(message)
        commit_info.task_ids = task_ids

        # 確定提交類型
        commit_info.type = self._determine_commit_type(message)

        logger.debug(f"提交分析結果: 類型={commit_info.type.value}, 任務={task_ids}")

    async def _generate_update_events(
        self,
        task_ids: List[str],
        commit_info: CommitInfo
    ) -> List[TaskUpdateEvent]:
        """生成任務更新事件

        Args:
            task_ids: 任務ID列表
            commit_info: 提交信息

        Returns:
            更新事件列表
        """
        events = []

        for task_id in task_ids:
            # 根據提交類型和關鍵字決定操作
            action = self._determine_action(commit_info)

            event = TaskUpdateEvent(
                task_id=task_id,
                action=action,
                commit_info=commit_info,
                metadata={
                    "commit_type": commit_info.type.value,
                    "files": commit_info.files,
                    "branch": commit_info.branch
                }
            )
            events.append(event)

        return events

    def _determine_action(self, commit_info: CommitInfo) -> str:
        """根據提交信息確定操作類型

        Args:
            commit_info: 提交信息

        Returns:
            操作類型
        """
        message = commit_info.message.lower()

        # 檢查關閉關鍵字
        if self.CLOSING_KEYWORDS.search(message):
            return "complete"

        # 檢查開始關鍵字
        if self.STARTING_KEYWORDS.search(message):
            return "start"

        # 檢查進度關鍵字
        if self.PROGRESS_KEYWORDS.search(message):
            return "progress"

        # 根據提交類型決定操作
        if commit_info.type in [CommitType.FIX, CommitType.FEAT]:
            return "progress"
        elif commit_info.type == CommitType.DOCS:
            return "complete"
        else:
            return "progress"

    async def _apply_task_update(self, event: TaskUpdateEvent):
        """應用任務更新

        Args:
            event: 更新事件
        """
        try:
            task = await self.task_repo.get_by_id(event.task_id)
            if not task:
                logger.warning(f"任務不存在: {event.task_id}")
                return

            old_status = task.status

            # 根據操作類型更新狀態
            if event.action == "start" and task.status.value == "待開始":
                await self.task_repo.transition_status(
                    event.task_id,
                    "進行中",
                    f"由Git提交 {event.commit_info.hash[:8]} 自動開始"
                )
                logger.info(f"任務 {event.task_id} 狀態更新: {old_status} -> 進行中")

            elif event.action == "progress":
                if task.status.value == "待開始":
                    await self.task_repo.transition_status(
                        event.task_id,
                        "進行中",
                        f"由Git提交 {event.commit_info.hash[:8]} 自動更新"
                    )
                    logger.info(f"任務 {event.task_id} 狀態更新: {old_status} -> 進行中")

            elif event.action == "complete":
                if task.status.value not in ["已完成"]:
                    await self.task_repo.transition_status(
                        event.task_id,
                        "已完成",
                        f"由Git提交 {event.commit_info.hash[:8]} 自動完成"
                    )
                    logger.info(f"任務 {event.task_id} 狀態更新: {old_status} -> 已完成")

            # 記錄自動化元數據
            if not task.metadata:
                task.metadata = {}

            if "git_commits" not in task.metadata:
                task.metadata["git_commits"] = []

            task.metadata["git_commits"].append({
                "hash": event.commit_info.hash,
                "message": event.commit_info.message,
                "author": event.commit_info.author,
                "timestamp": event.commit_info.timestamp.isoformat(),
                "action": event.action
            })

            # 更新任務
            await self.task_repo.update(event.task_id, {
                "metadata": task.metadata
            })

        except Exception as e:
            logger.error(f"應用任務更新失敗 (任務: {event.task_id}): {e}")

    async def check_task_dependencies(self, task_id: str) -> List[str]:
        """檢查任務依賴

        Args:
            task_id: 任務ID

        Returns:
            未滿足的依賴列表
        """
        try:
            task = await self.task_repo.get_by_id(task_id)
            if not task:
                return []

            unsatisfied = []

            for dep_id in task.dependencies:
                dep_task = await self.task_repo.get_by_id(dep_id)
                if not dep_task or dep_task.status.value != "已完成":
                    unsatisfied.append(dep_id)

            # 如果有待處理的依賴且任務狀態為待開始，則標記為阻塞
            if unsatisfied and task.status.value in ["待開始"]:
                await self.task_repo.transition_status(
                    task_id,
                    "已阻塞",
                    f"等待依賴任務完成: {', '.join(unsatisfied)}"
                )

            return unsatisfied

        except Exception as e:
            logger.error(f"檢查任務依賴失敗 ({task_id}): {e}")
            return []

    async def auto_update_blocked_tasks(self) -> List[str]:
        """自動更新被阻塞的任務

        Returns:
            被解除阻塞的任務ID列表
        """
        try:
            unblocked_tasks = []

            blocked_tasks = await self.task_repo.get_blocked_tasks()

            for task in blocked_tasks:
                unsatisfied_deps = await self.check_task_dependencies(task.id)

                if not unsatisfied_deps:
                    # 所有依賴都已滿足，可以開始
                    if task.status.value == "已阻塞":
                        await self.task_repo.transition_status(
                            task.id,
                            "待開始",
                            "所有依賴已滿足，等待分配"
                        )
                        unblocked_tasks.append(task.id)
                        logger.info(f"任務 {task.id} 已解除阻塞")

            return unblocked_tasks

        except Exception as e:
            logger.error(f"自動更新阻塞任務失敗: {e}")
            return []

    async def generate_automation_report(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """生成自動化報告

        Args:
            date: 報告日期，默認為今天

        Returns:
            報告數據
        """
        try:
            if not date:
                date = datetime.utcnow()

            # 統計信息
            all_tasks = await self.task_repo.list(limit=10000)

            automated_updates = 0
            blocked_tasks = 0
            completed_by_automation = 0

            for task in all_tasks:
                if task.metadata and "git_commits" in task.metadata:
                    automated_updates += len(task.metadata["git_commits"])

                if task.status.value == "已阻塞":
                    blocked_tasks += 1

                if task.metadata and "git_commits" in task.metadata:
                    for commit in task.metadata["git_commits"]:
                        if commit.get("action") == "complete":
                            completed_by_automation += 1
                            break

            # 獲取活躍Sprint
            active_sprint = await self.sprint_repo.get_active_sprint()

            return {
                "date": date.isoformat(),
                "total_tasks": len(all_tasks),
                "blocked_tasks": blocked_tasks,
                "automated_updates": automated_updates,
                "completed_by_automation": completed_by_automation,
                "automation_rate": (
                    (completed_by_automation / len(all_tasks) * 100)
                    if all_tasks else 0
                ),
                "active_sprint": active_sprint.id if active_sprint else None,
                "blocked_task_list": [
                    {
                        "id": task.id,
                        "title": task.title,
                        "dependencies": task.dependencies
                    }
                    for task in all_tasks
                    if task.status.value == "已阻塞"
                ]
            }

        except Exception as e:
            logger.error(f"生成自動化報告失敗: {e}")
            return {}


# Webhook處理器
class GitWebhookHandler:
    """
    Git Webhook處理器
    接收GitHub/GitLab等平台的Webhook推送
    """

    def __init__(self, automation_service: GitAutomationService):
        self.automation_service = automation_service

    async def handle_push_event(self, payload: Dict[str, Any]) -> List[TaskUpdateEvent]:
        """處理push事件

        Args:
            payload: Webhook payload

        Returns:
            任務更新事件列表
        """
        events = []
        repo_path = payload.get("repository", {}).get("clone_url", "")

        # 處理每次提交
        for commit in payload.get("commits", []):
            commit_hash = commit.get("id", "")
            if commit_hash:
                commit_events = await self.automation_service.process_git_commit(
                    repo_path,
                    commit_hash
                )
                events.extend(commit_events)

        return events
