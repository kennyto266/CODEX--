"""
任務數據導入服務
解析Markdown文件中的任務清單並導入到數據庫
"""

import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib

from ..repositories.task_repository import TaskRepository
from ..repositories.sprint_repository import SprintRepository

logger = logging.getLogger(__name__)


class TaskPriority(str, Enum):
    """任務優先級"""
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


class TaskStage(str, Enum):
    """任務階段"""
    STAGE_1 = "階段1"
    STAGE_2 = "階段2"
    STAGE_3 = "階段3"
    STAGE_4 = "階段4"
    STAGE_5 = "階段5"


@dataclass
class ParsedTask:
    """解析後的任務"""
    id: Optional[str]
    title: str
    description: str
    priority: str
    estimated_hours: int
    stage: str
    section: str
    original_line: str
    order: int


@dataclass
class ImportResult:
    """導入結果"""
    total_tasks: int
    imported: int
    skipped: int
    errors: int
    error_messages: List[str]
    task_ids: List[str]
    summary: Dict[str, Any]


class TaskImportService:
    """
    任務導入服務

    功能：
    - 解析Markdown格式的任務清單
    - 提取任務信息
    - 數據驗證和清洗
    - 批量導入到數據庫
    - 生成導入報告
    """

    # 任務ID分配起始數字
    TASK_ID_START = 100

    def __init__(self, task_repo: TaskRepository, sprint_repo: SprintRepository):
        """初始化服務

        Args:
            task_repo: 任務Repository實例
            sprint_repo: Sprint Repository實例
        """
        self.task_repo = task_repo
        self.sprint_repo = sprint_repo
        self.imported_task_ids = set()

    async def parse_tasks_from_markdown(self, file_path: str) -> List[ParsedTask]:
        """
        從Markdown文件解析任務

        Args:
            file_path: Markdown文件路徑

        Returns:
            解析後的任務列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            logger.info(f"開始解析文件: {file_path}")

            # 解析任務
            tasks = []
            current_stage = None
            current_section = None
            order_counter = 1

            lines = content.split('\n')

            for line in lines:
                line = line.strip()

                # 檢測階段標題
                if line.startswith('## 階段'):
                    current_stage = self._extract_stage(line)
                    logger.debug(f"檢測到階段: {current_stage}")
                    continue

                # 檢測小節標題
                if line.startswith('### '):
                    current_section = line
                    continue

                # 解析任務行
                if line.startswith('- ['):
                    task = self._parse_task_line(
                        line,
                        current_stage,
                        current_section,
                        order_counter
                    )
                    if task:
                        tasks.append(task)
                        order_counter += 1

            logger.info(f"解析完成，共 {len(tasks)} 個任務")
            return tasks

        except Exception as e:
            logger.error(f"解析任務失敗: {e}")
            raise

    def _extract_stage(self, line: str) -> str:
        """提取階段信息

        Args:
            line: 原始行

        Returns:
            階段名稱
        """
        # 匹配 "階段X: 階段名稱"
        match = re.search(r'階段(\d+):\s*(.+)', line)
        if match:
            stage_num = match.group(1)
            stage_name = match.group(2)
            return f"階段{stage_num}"

        return "階段未知"

    def _parse_task_line(
        self,
        line: str,
        stage: str,
        section: str,
        order: int
    ) -> Optional[ParsedTask]:
        """
        解析任務行

        Args:
            line: 任務行
            stage: 所屬階段
            section: 所屬小節
            order: 順序

        Returns:
            解析後的任務
        """
        try:
            # 移除markdown列表標記
            line = re.sub(r'^- \[ \]\s*', '', line)

            # 提取優先級標籤 [P0], [P1], [P2]
            priority = "P2"  # 默認
            priority_match = re.search(r'\[P([012])\]', line)
            if priority_match:
                priority = f"P{priority_match.group(1)}"

            # 移除優先級標籤
            line = re.sub(r'\s*\[[P012]\]\s*', '', line)

            # 提取時間信息 (X小時)
            estimated_hours = 2  # 默認
            time_match = re.search(r'\((\d+)\s*小時\)', line)
            if time_match:
                estimated_hours = int(time_match.group(1))

            # 移除時間信息
            line = re.sub(r'\s*\(\d+\s*小時\)\s*', '', line)

            # 提取文件路徑 `path/to/file.py`
            file_path = None
            path_match = re.search(r'`([^`]+)`', line)
            if path_match:
                file_path = path_match.group(1)
                # 移除文件路徑
                line = line.replace(f'`{file_path}`', '').strip()

            # 標題就是剩餘的文字
            title = line.strip()

            if not title:
                logger.warning(f"任務標題為空: {line}")
                return None

            # 生成任務ID（稍後分配）
            task_id = None

            return ParsedTask(
                id=task_id,
                title=title,
                description=f"導入自項目計劃優化任務清單",
                priority=priority,
                estimated_hours=estimated_hours,
                stage=stage,
                section=section,
                original_line=line,
                order=order
            )

        except Exception as e:
            logger.error(f"解析任務行失敗 ({line}): {e}")
            return None

    async def import_tasks(
        self,
        tasks: List[ParsedTask],
        create_sprint: bool = True
    ) -> ImportResult:
        """
        批量導入任務

        Args:
            tasks: 任務列表
            create_sprint: 是否為每個階段創建Sprint

        Returns:
            導入結果
        """
        logger.info(f"開始導入 {len(tasks)} 個任務")

        result = ImportResult(
            total_tasks=len(tasks),
            imported=0,
            skipped=0,
            errors=0,
            error_messages=[],
            task_ids=[],
            summary={}
        )

        # 步驟1: 創建Sprint（如果需要）
        if create_sprint:
            await self._create_sprints_from_stages(tasks)

        # 步驟2: 分配任務ID
        tasks = await self._assign_task_ids(tasks)

        # 步驟3: 批量導入
        for task in tasks:
            try:
                # 檢查是否已存在
                # TODO: 根據標題和內容檢查重複

                # 準備任務數據
                task_dict = {
                    'title': task.title,
                    'description': task.description,
                    'priority': task.priority,
                    'estimated_hours': task.estimated_hours,
                    'reporter': '系統導入',
                    'status': '待開始',
                    'stage': task.stage,
                    'section': task.section,
                    'order': task.order
                }

                # 添加Sprint信息
                sprint_id = f"SPRINT-{task.stage.replace('階段', '')}"
                task_dict['sprint'] = sprint_id

                # 創建任務
                created_task = await self.task_repo.create(task_dict)

                if created_task:
                    result.imported += 1
                    result.task_ids.append(created_task.id)
                    logger.debug(f"已導入任務: {created_task.id} - {task.title}")
                else:
                    result.skipped += 1
                    result.error_messages.append(f"創建任務失敗: {task.title}")

            except Exception as e:
                result.errors += 1
                error_msg = f"導入任務失敗 ({task.title}): {str(e)}"
                result.error_messages.append(error_msg)
                logger.error(error_msg)

        # 步驟4: 生成摘要
        result.summary = {
            'by_priority': self._count_by_priority(tasks),
            'by_stage': self._count_by_stage(tasks),
            'total_estimated_hours': sum(t.estimated_hours for t in tasks),
            'import_success_rate': (result.imported / result.total_tasks * 100) if result.total_tasks > 0 else 0
        }

        logger.info(f"導入完成: 成功 {result.imported}, 跳過 {result.skipped}, 錯誤 {result.errors}")

        return result

    async def _create_sprints_from_stages(self, tasks: List[ParsedTask]):
        """為每個階段創建Sprint

        Args:
            tasks: 任務列表
        """
        stages = set(task.stage for task in tasks)

        for stage in stages:
            try:
                sprint_id = f"SPRINT-{stage.replace('階段', '')}"

                # 檢查是否已存在
                existing_sprint = await self.sprint_repo.get_by_id(sprint_id)
                if existing_sprint:
                    logger.debug(f"Sprint已存在: {sprint_id}")
                    continue

                # 創建Sprint
                sprint_data = {
                    'id': sprint_id,
                    'name': f"{stage} Sprint",
                    'goal': f"完成 {stage} 的所有任務",
                    'start_date': datetime.utcnow().date(),
                    'end_date': datetime.utcnow().date(),
                    'status': '計劃中'
                }

                created_sprint = await self.sprint_repo.create(sprint_data)
                if created_sprint:
                    logger.info(f"已創建Sprint: {sprint_id}")

            except Exception as e:
                logger.error(f"創建Sprint失敗 ({stage}): {e}")

    async def _assign_task_ids(self, tasks: List[ParsedTask]) -> List[ParsedTask]:
        """分配任務ID

        Args:
            tasks: 任務列表

        Returns:
            分配ID後的任務列表
        """
        # 按階段和順序排序
        tasks.sort(key=lambda t: (t.stage, t.order))

        # 分配ID
        for i, task in enumerate(tasks, start=self.TASK_ID_START):
            task.id = f"TASK-{i:03d}"
            task.description += f" (階段: {task.stage})"

        return tasks

    def _count_by_priority(self, tasks: List[ParsedTask]) -> Dict[str, int]:
        """按優先級統計

        Args:
            tasks: 任務列表

        Returns:
            統計結果
        """
        counts = {'P0': 0, 'P1': 0, 'P2': 0}
        for task in tasks:
            counts[task.priority] += 1
        return counts

    def _count_by_stage(self, tasks: List[ParsedTask]) -> Dict[str, int]:
        """按階段統計

        Args:
            tasks: 任務列表

        Returns:
            統計結果
        """
        counts = {}
        for task in tasks:
            counts[task.stage] = counts.get(task.stage, 0) + 1
        return counts

    async def validate_imported_tasks(self) -> Dict[str, Any]:
        """驗證已導入的任務

        Returns:
            驗證結果
        """
        try:
            # 獲取所有任務
            all_tasks = await self.task_repo.list(limit=10000)

            # 按優先級統計
            by_priority = {}
            for task in all_tasks:
                priority = task.priority
                by_priority[priority] = by_priority.get(priority, 0) + 1

            # 按階段統計
            by_stage = {}
            for task in all_tasks:
                stage = getattr(task, 'stage', '未知')
                by_stage[stage] = by_stage.get(stage, 0) + 1

            # 檢查空標題
            empty_title = sum(1 for t in all_tasks if not t.title or t.title.strip() == '')

            # 檢查異常工時
            abnormal_hours = sum(
                1 for t in all_tasks
                if t.estimated_hours <= 0 or t.estimated_hours > 100
            )

            # 檢查重複標題
            title_counts = {}
            for task in all_tasks:
                title_counts[task.title] = title_counts.get(task.title, 0) + 1
            duplicate_titles = {
                title: count
                for title, count in title_counts.items()
                if count > 1
            }

            return {
                'total': len(all_tasks),
                'by_priority': by_priority,
                'by_stage': by_stage,
                'validation_errors': {
                    'empty_title': empty_title,
                    'abnormal_hours': abnormal_hours,
                    'duplicate_titles': len(duplicate_titles)
                },
                'duplicate_details': duplicate_titles
            }

        except Exception as e:
            logger.error(f"驗證任務失敗: {e}")
            return {}

    def generate_import_report(self, result: ImportResult) -> str:
        """
        生成導入報告

        Args:
            result: 導入結果

        Returns:
            報告內容
        """
        report = f"""# 任務數據導入報告

## 導入摘要

- **總任務數**: {result.total_tasks}
- **成功導入**: {result.imported}
- **跳過任務**: {result.skipped}
- **錯誤任務**: {result.errors}
- **成功率**: {result.summary.get('import_success_rate', 0):.1f}%

## 按優先級分布

"""

        for priority, count in result.summary.get('by_priority', {}).items():
            report += f"- {priority}: {count} 個任務\n"

        report += "\n## 按階段分布\n\n"

        for stage, count in result.summary.get('by_stage', {}).items():
            report += f"- {stage}: {count} 個任務\n"

        report += f"\n## 統計信息\n\n"
        report += f"- **總預估工時**: {result.summary.get('total_estimated_hours', 0)} 小時\n"

        if result.errors > 0:
            report += "\n## 錯誤詳情\n\n"
            for error in result.error_messages[:10]:  # 只顯示前10個錯誤
                report += f"- {error}\n"

            if len(result.error_messages) > 10:
                report += f"\n... 還有 {len(result.error_messages) - 10} 個錯誤\n"

        report += f"\n## 已導入任務ID列表\n\n"
        for task_id in result.task_ids:
            report += f"- {task_id}\n"

        report += f"\n## 下一步建議\n\n"
        report += f"1. 查看任務看板: /tasks\n"
        report += f"2. 驗證任務數據完整性\n"
        report += f"3. 分配任務給團隊成員\n"
        report += f"4. 啟動首個Sprint\n"

        return report

    async def rollback_import(self, task_ids: List[str]) -> int:
        """
        回滾導入（刪除指定任務）

        Args:
            task_ids: 要刪除的任務ID列表

        Returns:
            刪除的任務數量
        """
        deleted_count = 0

        for task_id in task_ids:
            try:
                success = await self.task_repo.delete(task_id)
                if success:
                    deleted_count += 1
                    logger.info(f"已刪除任務: {task_id}")
            except Exception as e:
                logger.error(f"刪除任務失敗 ({task_id}): {e}")

        logger.info(f"回滾完成，刪除 {deleted_count} 個任務")
        return deleted_count


class TaskDataAnalyzer:
    """
    任務數據分析器
    分析任務清單的質量和結構
    """

    def analyze_markdown_tasks(self, file_path: str) -> Dict[str, Any]:
        """
        分析Markdown文件的任務質量

        Args:
            file_path: 文件路徑

        Returns:
            分析結果
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')

            # 基本統計
            total_lines = len(lines)
            task_lines = [line for line in lines if line.strip().startswith('- [ ]')]
            task_count = len(task_lines)

            # 分析優先級
            priority_counts = {'P0': 0, 'P1': 0, 'P2': 0}
            for line in task_lines:
                for p in priority_counts.keys():
                    if f'[{p}]' in line:
                        priority_counts[p] += 1

            # 分析工時
            hours = []
            for line in task_lines:
                match = re.search(r'\((\d+)\s*小時\)', line)
                if match:
                    hours.append(int(match.group(1)))

            # 分析問題
            issues = []

            # 檢查無優先級
            no_priority = sum(1 for line in task_lines if not re.search(r'\[[P012]\]', line))
            if no_priority > 0:
                issues.append(f"發現 {no_priority} 個任務沒有優先級")

            # 檢查無時間估算
            no_hours = sum(1 for line in task_lines if not re.search(r'\(\d+\s*小時\)', line))
            if no_hours > 0:
                issues.append(f"發現 {no_hours} 個任務沒有時間估算")

            # 檢查長時間任務
            long_tasks = [h for h in hours if h > 20]
            if long_tasks:
                issues.append(f"發現 {len(long_tasks)} 個長時間任務 (>20小時)")

            # 檢查超級短任務
            short_tasks = [h for h in hours if h < 1]
            if short_tasks:
                issues.append(f"發現 {len(short_tasks)} 個超短任務 (<1小時)")

            # 計算工時統計
            hours_stats = {
                'min': min(hours) if hours else 0,
                'max': max(hours) if hours else 0,
                'avg': sum(hours) / len(hours) if hours else 0,
                'total': sum(hours) if hours else 0
            }

            return {
                'file_path': file_path,
                'total_lines': total_lines,
                'task_count': task_count,
                'priority_distribution': priority_counts,
                'hours_stats': hours_stats,
                'issues': issues,
                'quality_score': self._calculate_quality_score(len(issues), task_count)
            }

        except Exception as e:
            logger.error(f"分析任務文件失敗: {e}")
            return {}

    def _calculate_quality_score(self, issues_count: int, task_count: int) -> float:
        """
        計算任務質量分數

        Args:
            issues_count: 問題數量
            task_count: 任務總數

        Returns:
            質量分數 (0-100)
        """
        if task_count == 0:
            return 0

        # 基礎分數
        score = 100

        # 根據問題數量扣分
        score -= issues_count * 5

        # 根據問題密度扣分
        issue_density = (issues_count / task_count) * 100
        score -= issue_density

        return max(0, min(100, score))
