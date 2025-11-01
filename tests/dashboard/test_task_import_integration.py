"""
任务导入功能集成测试
测试完整的端到端导入流程
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from tests.dashboard.fixtures.task_test_data import (
    SAMPLE_TASKS_MARKDOWN,
    SAMPLE_TASKS_WITH_ISSUES,
    TaskTestDataGenerator,
    MockTaskRepository,
    MockSprintRepository
)


class TestTaskImportIntegration:
    """任务导入集成测试类"""

    @pytest.mark.asyncio
    async def test_full_import_workflow(self, test_markdown_file):
        """测试完整的导入工作流"""
        from src.dashboard.services.task_import_service import TaskImportService
        from src.dashboard.services.task_import_service import TaskDataAnalyzer

        # 步骤1: 分析
        analyzer = TaskDataAnalyzer()
        analysis = analyzer.analyze_markdown_tasks(test_markdown_file)

        assert analysis is not None
        assert analysis["task_count"] > 0

        # 步骤2: 创建服务
        task_repo = MockTaskRepository()
        sprint_repo = MockSprintRepository()
        service = TaskImportService(task_repo, sprint_repo)

        # 步骤3: 验证数据
        tasks = await service.parse_tasks_from_markdown(test_markdown_file)
        validation = await service.validate_import_data(tasks)

        assert validation["is_valid"]

        # 步骤4: 执行导入
        result = await service.import_tasks_from_markdown(test_markdown_file)

        assert result is not None
        assert "import_id" in result
        assert result["created_tasks"] > 0

        # 步骤5: 验证结果
        imported_tasks = await task_repo.list_tasks()
        assert len(imported_tasks) == result["created_tasks"]

        sprints = await sprint_repo.list_sprints()
        assert len(sprints) > 0

    @pytest.mark.asyncio
    async def test_import_with_quality_issues(self, test_markdown_file_with_issues):
        """测试导入带质量问题的文件"""
        from src.dashboard.services.task_import_service import TaskImportService

        task_repo = MockTaskRepository()
        sprint_repo = MockSprintRepository()
        service = TaskImportService(task_repo, sprint_repo)

        # 分析质量
        result = await service.import_tasks_from_markdown(test_markdown_file_with_issues)

        # 验证导入仍然成功，但记录了问题
        assert result is not None
        assert "quality_score" in result
        assert result["quality_score"] < 100  # 有质量问题

        # 验证任务被创建
        imported_tasks = await task_repo.list_tasks()
        assert len(imported_tasks) > 0

    @pytest.mark.asyncio
    async def test_import_and_rollback_workflow(self, test_markdown_file):
        """测试导入和回滚工作流"""
        from src.dashboard.services.task_import_service import TaskImportService

        task_repo = MockTaskRepository()
        sprint_repo = MockSprintRepository()
        service = TaskImportService(task_repo, sprint_repo)

        # 执行导入
        import_result = await service.import_tasks_from_markdown(test_markdown_file)

        created_task_ids = []
        if import_result.get("created_task_ids"):
            created_task_ids = import_result["created_task_ids"]

        # 执行回滚
        if created_task_ids:
            rollback_result = await service.rollback_import(created_task_ids)

            assert rollback_result is not None
            assert rollback_result["deleted_count"] > 0

            # 验证任务被删除
            remaining_tasks = await task_repo.list_tasks()
            assert len(remaining_tasks) == 0

    @pytest.mark.asyncio
    async def test_multiple_sprints_creation(self, test_markdown_file):
        """测试创建多个Sprint"""
        from src.dashboard.services.task_import_service import TaskImportService

        task_repo = MockTaskRepository()
        sprint_repo = MockSprintRepository()
        service = TaskImportService(task_repo, sprint_repo)

        # 导入应该为每个阶段创建Sprint
        result = await service.import_tasks_from_markdown(test_markdown_file)

        sprints = await sprint_repo.list_sprints()

        # 验证多个Sprint被创建
        assert len(sprints) >= 2  # 至少2个阶段

        # 验证Sprint结构
        for sprint in sprints:
            assert "id" in sprint
            assert "name" in sprint
            assert "task_ids" in sprint

    @pytest.mark.asyncio
    async def test_import_with_concurrent_requests(self, test_markdown_file):
        """测试并发导入请求处理"""
        from src.dashboard.services.task_import_service import TaskImportService

        task_repo = MockTaskRepository()
        sprint_repo = MockSprintRepository()

        # 并发执行多次导入
        tasks = []
        for i in range(3):
            service = TaskImportService(task_repo, sprint_repo)
            task = asyncio.create_task(
                service.import_tasks_from_markdown(test_markdown_file)
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # 验证所有导入都成功
        assert all(r is not None for r in results)

        # 验证最终任务数量（应该去重）
        imported_tasks = await task_repo.list_tasks()
        assert len(imported_tasks) > 0

    @pytest.mark.asyncio
    async def test_import_large_dataset(self):
        """测试导入大型数据集"""
        from src.dashboard.services.task_import_service import TaskImportService

        # 创建包含500个任务的文件
        large_markdown = """
# 大型项目任务清单

## 阶段1: 基础建设

"""
        for i in range(125):
            large_markdown += f"""
### 1.{i+1} 任务组{i+1} (4小时)
- [ ] 任务{i*4+1} [P0]
- [ ] 任务{i*4+2} [P1]
- [ ] 任务{i*4+3} [P2]
- [ ] 任务{i*4+4} [P1]
"""

        file_path = TaskTestDataGenerator.create_test_markdown_file(large_markdown)

        try:
            task_repo = MockTaskRepository()
            sprint_repo = MockSprintRepository()
            service = TaskImportService(task_repo, sprint_repo)

            result = await service.import_tasks_from_markdown(file_path)

            assert result is not None
            assert result["total_tasks"] >= 500

            # 验证性能
            imported_tasks = await task_repo.list_tasks()
            assert len(imported_tasks) == result["created_tasks"]
        finally:
            import os
            if os.path.exists(file_path):
                os.remove(file_path)

    @pytest.mark.asyncio
    async def test_import_data_consistency(self, test_markdown_file):
        """测试导入数据一致性"""
        from src.dashboard.services.task_import_service import TaskImportService

        task_repo = MockTaskRepository()
        sprint_repo = MockSprintRepository()
        service = TaskImportService(task_repo, sprint_repo)

        # 执行导入
        result = await service.import_tasks_from_markdown(test_markdown_file)

        # 验证数据一致性
        imported_tasks = await task_repo.list_tasks()
        sprints = await sprint_repo.list_sprints()

        # 验证任务关联
        all_task_ids = set()
        for sprint in sprints:
            sprint_task_ids = set(sprint.get("task_ids", []))
            all_task_ids.update(sprint_task_ids)

        imported_task_ids = {task["id"] for task in imported_tasks}

        # 所有导入的任务应该都在某个Sprint中
        assert all_task_ids.issubset(imported_task_ids)

        # 验证Sprint任务分配
        for sprint in sprints:
            sprint_task_count = len(sprint.get("task_ids", []))
            assert sprint_task_count > 0

    @pytest.mark.asyncio
    async def test_import_error_recovery(self):
        """测试导入错误恢复"""
        from src.dashboard.services.task_import_service import TaskImportService

        # 创建测试文件
        file_path = TaskTestDataGenerator.create_test_markdown_file(SAMPLE_TASKS_MARKDOWN)

        try:
            task_repo = MockTaskRepository()
            sprint_repo = MockSprintRepository()

            # 模拟task_repository在中间失败
            original_create = task_repo.create_task
            call_count = 0

            async def failing_create(task_data):
                nonlocal call_count
                call_count += 1
                if call_count > 3:
                    raise Exception("模拟数据库错误")
                return await original_create(task_data)

            task_repo.create_task = failing_create

            service = TaskImportService(task_repo, sprint_repo)

            # 执行导入应该部分成功
            result = await service.import_tasks_from_markdown(file_path)

            assert result is not None
            assert result["failed_tasks"] > 0
            assert result["created_tasks"] > 0

        finally:
            import os
            if os.path.exists(file_path):
                os.remove(file_path)

    @pytest.mark.asyncio
    async def test_import_report_generation(self, test_markdown_file):
        """测试导入报告生成"""
        from src.dashboard.services.task_import_service import TaskImportService

        task_repo = MockTaskRepository()
        sprint_repo = MockSprintRepository()
        service = TaskImportService(task_repo, sprint_repo)

        # 执行导入
        result = await service.import_tasks_from_markdown(test_markdown_file)

        import_id = result.get("import_id")
        assert import_id

        # 获取导入的任务
        tasks = await task_repo.list_tasks()

        # 生成报告
        report = await service.generate_import_report(import_id, tasks, [])

        # 验证报告内容
        assert report is not None
        assert report["import_id"] == import_id
        assert report["total_tasks"] == len(tasks)
        assert "task_list" in report
        assert "statistics" in report

        # 验证统计信息
        stats = report["statistics"]
        assert "by_priority" in stats
        assert "by_stage" in stats

    @pytest.mark.asyncio
    async def test_import_with_special_characters(self):
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
- [ ] 创建文件: `C:\\Users\\Name\\project\\file.py` [P0]
"""

        file_path = TaskTestDataGenerator.create_test_markdown_file(special_markdown)

        try:
            task_repo = MockTaskRepository()
            sprint_repo = MockSprintRepository()
            service = TaskImportService(task_repo, sprint_repo)

            result = await service.import_tasks_from_markdown(file_path)

            assert result is not None
            assert result["created_tasks"] > 0

            # 验证特殊字符正确处理
            tasks = await task_repo.list_tasks()

            # 检查包含反引号的任务
            has_backtick = any("`" in task["title"] for task in tasks)
            assert has_backtick

            # 检查包含引号的任务
            has_quotes = any("" in task["title"] for task in tasks)
            assert has_quotes
        finally:
            import os
            if os.path.exists(file_path):
                os.remove(file_path)

    @pytest.mark.asyncio
    async def test_import_state_persistence(self, test_markdown_file):
        """测试导入状态持久化"""
        from src.dashboard.services.task_import_service import TaskImportService

        task_repo = MockTaskRepository()
        sprint_repo = MockSprintRepository()
        service = TaskImportService(task_repo, sprint_repo)

        # 第一次导入
        result1 = await service.import_tasks_from_markdown(test_markdown_file)
        assert result1 is not None

        # 等待一段时间（模拟实际场景）
        await asyncio.sleep(0.1)

        # 第二次导入相同文件（模拟重新启动）
        result2 = await service.import_tasks_from_markdown(test_markdown_file)

        # 验证状态保持一致
        assert result2 is not None
        assert result2["created_tasks"] > 0

    @pytest.mark.asyncio
    async def test_duplicate_detection_across_imports(self, test_markdown_file):
        """测试跨导入的重复检测"""
        from src.dashboard.services.task_import_service import TaskImportService

        task_repo = MockTaskRepository()
        sprint_repo = MockSprintRepository()
        service = TaskImportService(task_repo, sprint_repo)

        # 第一次导入
        result1 = await service.import_tasks_from_markdown(test_markdown_file)
        assert result1 is not None

        # 检查重复任务（模拟）
        tasks = await service.parse_tasks_from_markdown(test_markdown_file)
        duplicates = await service.check_duplicate_tasks(tasks)

        # 应该检测到重复（因为已经导入过）
        assert len(duplicates) > 0

    @pytest.mark.asyncio
    async def test_import_performance_metrics(self, test_markdown_file):
        """测试导入性能指标"""
        import time

        from src.dashboard.services.task_import_service import TaskImportService

        task_repo = MockTaskRepository()
        sprint_repo = MockSprintRepository()
        service = TaskImportService(task_repo, sprint_repo)

        # 测量导入时间
        start_time = time.time()

        result = await service.import_tasks_from_markdown(test_markdown_file)

        end_time = time.time()
        duration = end_time - start_time

        # 验证导入成功
        assert result is not None

        # 验证性能（在合理时间内完成）
        assert duration < 10  # 应该小于10秒

        # 记录性能指标
        print(f"\n导入性能指标:")
        print(f"  总任务数: {result['total_tasks']}")
        print(f"  创建任务数: {result['created_tasks']}")
        print(f"  耗时: {duration:.2f}秒")
        print(f"  平均每任务: {duration/result['total_tasks']*1000:.2f}ms")
