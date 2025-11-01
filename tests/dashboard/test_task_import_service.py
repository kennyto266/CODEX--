"""
任务导入服务测试
测试任务导入的核心业务逻辑
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict

from tests.dashboard.fixtures.task_test_data import (
    SAMPLE_TASKS_MARKDOWN,
    TaskTestDataGenerator,
    MockTaskRepository,
    MockSprintRepository
)


class TestTaskImportService:
    """任务导入服务测试类"""

    @pytest.mark.asyncio
    async def test_service_initialization(self, mock_task_repo, mock_sprint_repo):
        """测试服务初始化"""
        from src.dashboard.services.task_import_service import TaskImportService

        service = TaskImportService(mock_task_repo, mock_sprint_repo)

        assert service.task_repository == mock_task_repo
        assert service.sprint_repository == mock_sprint_repo

    @pytest.mark.asyncio
    async def test_parse_tasks_from_markdown(self, test_markdown_file):
        """测试从Markdown解析任务"""
        from src.dashboard.services.task_import_service import TaskImportService

        service = TaskImportService(MockTaskRepository(), MockSprintRepository())
        tasks = await service.parse_tasks_from_markdown(test_markdown_file)

        assert len(tasks) > 0
        assert all(hasattr(task, "title") for task in tasks)
        assert all(hasattr(task, "priority") for task in tasks)

    @pytest.mark.asyncio
    async def test_create_sprint_for_stage(self, mock_sprint_repo):
        """测试为阶段创建Sprint"""
        from src.dashboard.services.task_import_service import TaskImportService

        service = TaskImportService(MockTaskRepository(), mock_sprint_repo)

        stage_data = {
            "name": "阶段1: 任务管理系统建设",
            "task_count": 5,
            "total_hours": 20
        }

        sprint = await service._create_sprint_for_stage(stage_data, 1)

        assert sprint is not None
        assert sprint["name"] == stage_data["name"]
        assert "SPRINT-1" in sprint["id"]

    @pytest.mark.asyncio
    async def test_create_tasks_bulk(self, mock_task_repo, sample_tasks):
        """测试批量创建任务"""
        from src.dashboard.services.task_import_service import TaskImportService

        service = TaskImportService(mock_task_repo, MockSprintRepository())

        created_tasks = await service._create_tasks_bulk(sample_tasks)

        assert len(created_tasks) == len(sample_tasks)
        assert all("id" in task for task in created_tasks)
        assert all(task["created_at"] for task in created_tasks)

    @pytest.mark.asyncio
    async def test_import_tasks_full_flow(self, test_markdown_file, mock_task_repo, mock_sprint_repo):
        """测试完整导入流程"""
        from src.dashboard.services.task_import_service import TaskImportService

        service = TaskImportService(mock_task_repo, mock_sprint_repo)

        # 执行导入
        result = await service.import_tasks_from_markdown(test_markdown_file)

        assert result is not None
        assert "import_id" in result
        assert "total_tasks" in result
        assert "created_tasks" in result

        # 验证任务被创建
        tasks_in_repo = await mock_task_repo.list_tasks()
        assert len(tasks_in_repo) == result["created_tasks"]

        # 验证Sprint被创建
        sprints_in_repo = await mock_sprint_repo.list_sprints()
        assert len(sprints_in_repo) > 0

    @pytest.mark.asyncio
    async def test_rollback_import(self, mock_task_repo, mock_sprint_repo, sample_tasks):
        """测试导入回滚"""
        from src.dashboard.services.task_import_service import TaskImportService

        service = TaskImportService(mock_task_repo, mock_sprint_repo)

        # 先创建一些任务
        created_tasks = await service._create_tasks_bulk(sample_tasks)
        created_task_ids = [task["id"] for task in created_tasks]

        # 执行回滚
        rollback_result = await service.rollback_import(created_task_ids)

        assert rollback_result is not None
        assert "deleted_count" in rollback_result

        # 验证任务被删除
        remaining_tasks = await mock_task_repo.list_tasks()
        assert len(remaining_tasks) == 0

    @pytest.mark.asyncio
    async def test_check_duplicate_tasks(self, mock_task_repo, sample_tasks):
        """测试重复任务检查"""
        from src.dashboard.services.task_import_service import TaskImportService

        service = TaskImportService(mock_task_repo, MockSprintRepository())

        # 创建第一批任务
        await service._create_tasks_bulk(sample_tasks)

        # 检查重复
        duplicates = await service.check_duplicate_tasks(sample_tasks)
        assert len(duplicates) == 0  # 第一次不应该有重复

        # 添加相同任务再次检查
        duplicates = await service.check_duplicate_tasks(sample_tasks)
        assert len(duplicates) > 0  # 现在应该有重复

    @pytest.mark.asyncio
    async def test_update_sprint_progress(self, mock_task_repo, mock_sprint_repo, sample_tasks):
        """测试更新Sprint进度"""
        from src.dashboard.services.task_import_service import TaskImportService

        service = TaskImportService(mock_task_repo, mock_sprint_repo)

        # 创建任务和Sprint
        tasks = await service._create_tasks_bulk(sample_tasks)
        sprint = await mock_sprint_repo.create_sprint({
            "name": "测试Sprint",
            "start_date": "2025-01-01",
            "end_date": "2025-01-10",
            "task_ids": [t["id"] for t in tasks]
        })

        # 更新进度
        updated_sprint = await service._update_sprint_progress(sprint["id"])

        assert updated_sprint is not None
        assert "completed_hours" in updated_sprint

    @pytest.mark.asyncio
    async def test_validate_import_data(self, mock_task_repo):
        """测试导入数据验证"""
        from src.dashboard.services.task_import_service import TaskImportService

        service = TaskImportService(mock_task_repo, MockSprintRepository())

        # 有效数据
        valid_tasks = [
            {"title": "任务1", "priority": "P0", "estimated_hours": 4},
            {"title": "任务2", "priority": "P1", "estimated_hours": 6}
        ]

        validation_result = await service.validate_import_data(valid_tasks)
        assert validation_result["is_valid"]
        assert len(validation_result["errors"]) == 0

        # 无效数据
        invalid_tasks = [
            {"title": "无优先级任务"},  # 缺少优先级
            {"priority": "P0", "estimated_hours": 4}  # 缺少标题
        ]

        validation_result = await service.validate_import_data(invalid_tasks)
        assert not validation_result["is_valid"]
        assert len(validation_result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_handle_import_errors(self, test_markdown_file, mock_task_repo, mock_sprint_repo):
        """测试处理导入错误"""
        from src.dashboard.services.task_import_service import TaskImportService

        service = TaskImportService(mock_task_repo, mock_sprint_repo)

        # 模拟task_repository失败
        mock_task_repo.create_task = AsyncMock(side_effect=Exception("数据库错误"))

        # 执行导入应该处理错误
        result = await service.import_tasks_from_markdown(test_markdown_file)

        assert result is not None
        assert "failed_tasks" in result
        assert result["failed_tasks"] > 0

    @pytest.mark.asyncio
    async def test_concurrent_import(self, test_markdown_file, mock_task_repo, mock_sprint_repo):
        """测试并发导入"""
        from src.dashboard.services.task_import_service import TaskImportService

        service = TaskImportService(mock_task_repo, mock_sprint_repo)

        # 并发执行多次导入
        tasks = []
        for i in range(3):
            task = asyncio.create_task(
                service.import_tasks_from_markdown(test_markdown_file)
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        assert all(result is not None for result in results)

        # 验证没有重复任务
        all_tasks = await mock_task_repo.list_tasks()
        task_titles = [t["title"] for t in all_tasks]
        assert len(task_titles) == len(set(task_titles))

    @pytest.mark.asyncio
    async def test_import_large_dataset(self):
        """测试导入大型数据集"""
        from src.dashboard.services.task_import_service import TaskImportService

        # 创建大型任务清单
        large_markdown = """
# 大型项目任务清单

## 阶段1: 基础建设

"""
        for i in range(100):
            large_markdown += f"""
### 1.{i+1} 任务组{i+1} (4小时)
- [ ] 任务{i*4+1} [P0]
- [ ] 任务{i*4+2} [P1]
- [ ] 任务{i*4+3} [P2]
- [ ] 任务{i*4+4} [P1]
"""

        # 创建临时文件
        file_path = TaskTestDataGenerator.create_test_markdown_file(large_markdown)

        try:
            service = TaskImportService(MockTaskRepository(), MockSprintRepository())
            result = await service.import_tasks_from_markdown(file_path)

            assert result is not None
            assert result["total_tasks"] >= 400  # 100组 × 4任务
        finally:
            import os
            if os.path.exists(file_path):
                os.remove(file_path)

    @pytest.mark.asyncio
    async def test_import_with_special_characters(self, mock_task_repo, mock_sprint_repo):
        """测试导入包含特殊字符的任务"""
        from src.dashboard.services.task_import_service import TaskImportService

        special_markdown = """
# 项目任务清单

## 阶段1: 任务管理系统建设

### 1.1 数据模型设计 (4小时)
- [ ] 创建 `src/dashboard/models/task.py` 任务数据模型 [P0]
- [ ] 创建 `src/dashboard/models/sprint.py` Sprint数据模型 [P0]
- [ ] 实现 \"特殊字符任务\" 功能 [P1]
- [ ] 处理中文路径 `/用户/桌面/项目` [P2]
"""

        file_path = TaskTestDataGenerator.create_test_markdown_file(special_markdown)

        try:
            service = TaskImportService(mock_task_repo, mock_sprint_repo)
            result = await service.import_tasks_from_markdown(file_path)

            assert result is not None
            assert result["created_tasks"] > 0

            # 验证特殊字符正确处理
            tasks = await mock_task_repo.list_tasks()
            assert any("`" in task["title"] for task in tasks)
            assert any("" in task["title"] for task in tasks)
        finally:
            import os
            if os.path.exists(file_path):
                os.remove(file_path)

    @pytest.mark.asyncio
    async def test_count_by_stage(self, sample_tasks):
        """测试按阶段统计"""
        from src.dashboard.services.task_import_service import TaskImportService

        service = TaskImportService(MockTaskRepository(), MockSprintRepository())

        # 添加阶段信息
        for i, task in enumerate(sample_tasks):
            if i < 2:
                task["stage"] = "阶段1"
            else:
                task["stage"] = "阶段2"

        counts = service._count_by_stage(sample_tasks)

        assert "阶段1" in counts
        assert "阶段2" in counts
        assert counts["阶段1"] == 2
        assert counts["阶段2"] == 0  # 剩余的没有明确阶段

    @pytest.mark.asyncio
    async def test_count_by_priority(self, sample_tasks):
        """测试按优先级统计"""
        from src.dashboard.services.task_import_service import TaskImportService

        service = TaskImportService(MockTaskRepository(), MockSprintRepository())

        counts = service._count_by_priority(sample_tasks)

        assert "P0" in counts
        assert "P1" in counts
        assert "P2" in counts
        assert all(count >= 0 for count in counts.values())

    @pytest.mark.asyncio
    async def test_generate_import_report(self, mock_task_repo, mock_sprint_repo):
        """测试生成导入报告"""
        from src.dashboard.services.task_import_service import TaskImportService

        service = TaskImportService(mock_task_repo, mock_sprint_repo)

        # 创建测试数据
        tasks = TaskTestDataGenerator.get_sample_tasks()
        sprints = TaskTestDataGenerator.get_sample_sprints()

        # 创建任务和Sprint
        created_tasks = await service._create_tasks_bulk(tasks)
        for sprint_data in sprints:
            await mock_sprint_repo.create_sprint(sprint_data)

        # 生成报告
        report = await service.generate_import_report(
            "import_20250101_120000",
            created_tasks,
            sprints
        )

        assert report is not None
        assert "import_id" in report
        assert "total_tasks" in report
        assert "statistics" in report
        assert "task_list" in report
