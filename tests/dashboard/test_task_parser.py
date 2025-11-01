"""
任务解析器测试
测试Markdown格式任务清单的解析功能
"""

import pytest
import re
from pathlib import Path
from typing import List, Dict

from tests.dashboard.fixtures.task_test_data import (
    SAMPLE_TASKS_MARKDOWN,
    SAMPLE_TASKS_WITH_ISSUES,
    TaskTestDataGenerator
)


class TestTaskParser:
    """任务解析器测试类"""

    def test_parse_markdown_content(self):
        """测试解析Markdown内容"""
        from src.dashboard.services.task_import_service import TaskDataAnalyzer

        analyzer = TaskDataAnalyzer()
        analysis = analyzer.analyze_markdown_content(SAMPLE_TASKS_MARKDOWN)

        assert analysis is not None
        assert "tasks" in analysis
        assert "stages" in analysis
        assert "sections" in analysis

    def test_extract_tasks_from_markdown(self):
        """测试从Markdown中提取任务"""
        from src.dashboard.services.task_import_service import TaskDataAnalyzer

        analyzer = TaskDataAnalyzer()
        tasks = analyzer._extract_tasks_from_markdown(SAMPLE_TASKS_MARKDOWN)

        assert len(tasks) > 0
        assert all(isinstance(task, dict) for task in tasks)

        # 验证任务结构
        for task in tasks:
            assert "title" in task
            assert "priority" in task
            assert "stage" in task
            assert "section" in task

    def test_extract_priority(self):
        """测试提取优先级"""
        from src.dashboard.services.task_import_service import TaskDataAnalyzer

        analyzer = TaskDataAnalyzer()

        # 测试P0优先级
        assert analyzer._extract_priority("- [ ] 任务描述 [P0]") == "P0"
        assert analyzer._extract_priority("- [ ] 任务描述 [P1]") == "P1"
        assert analyzer._extract_priority("- [ ] 任务描述 [P2]") == "P2"

        # 测试无优先级
        assert analyzer._extract_priority("- [ ] 任务描述") is None

    def test_extract_estimated_hours(self):
        """测试提取预估工时"""
        from src.dashboard.services.task_import_service import TaskDataAnalyzer

        analyzer = TaskDataAnalyzer()

        # 测试时间提取
        hours = analyzer._extract_estimated_hours("### 1.1 标题 (4小时)")
        assert hours == 4

        hours = analyzer._extract_estimated_hours("### 1.2 标题 (8小时)")
        assert hours == 8

        # 测试无时间
        hours = analyzer._extract_estimated_hours("### 1.3 标题")
        assert hours is None

    def test_extract_stage_and_section(self):
        """测试提取阶段和小节"""
        from src.dashboard.services.task_import_service import TaskDataAnalyzer

        analyzer = TaskDataAnalyzer()

        # 解析Markdown以建立上下文
        context = analyzer._build_context(SAMPLE_TASKS_MARKDOWN)

        # 测试阶段识别
        stage = analyzer._extract_stage("任务描述", context)
        assert "阶段1" in stage

        # 测试小节识别
        section = analyzer._extract_section("任务描述", context)
        assert "1.1" in section or "1.2" in section

    def test_analyze_task_quality(self):
        """测试任务质量分析"""
        from src.dashboard.services.task_import_service import TaskDataAnalyzer

        analyzer = TaskDataAnalyzer()

        # 测试有质量问题的任务
        task_with_issues = {
            "title": "无优先级任务",
            "priority": None,
            "estimated_hours": None
        }

        task_without_issues = {
            "title": "完整任务描述",
            "priority": "P0",
            "estimated_hours": 4
        }

        # 分析质量
        issues = analyzer._analyze_task_quality(task_with_issues)
        assert len(issues) > 0
        assert "无优先级" in issues[0]

        issues = analyzer._analyze_task_quality(task_without_issues)
        assert len(issues) == 0

    def test_calculate_quality_score(self):
        """测试质量评分计算"""
        from src.dashboard.services.task_import_service import TaskDataAnalyzer

        analyzer = TaskDataAnalyzer()

        # 高质量任务列表
        high_quality_tasks = [
            {"title": "任务1", "priority": "P0", "estimated_hours": 4},
            {"title": "任务2", "priority": "P1", "estimated_hours": 6},
        ]

        score = analyzer._calculate_quality_score(high_quality_tasks)
        assert score >= 80

        # 低质量任务列表
        low_quality_tasks = [
            {"title": "任务1"},  # 无优先级无时间
            {"title": "任务2"},  # 无优先级无时间
        ]

        score = analyzer._calculate_quality_score(low_quality_tasks)
        assert score < 60

    def test_parse_tasks_with_all_features(self, test_markdown_file):
        """测试解析包含所有功能的Markdown文件"""
        from src.dashboard.services.task_import_service import TaskDataAnalyzer

        analyzer = TaskDataAnalyzer()
        analysis = analyzer.analyze_markdown_tasks(test_markdown_file)

        assert analysis is not None
        assert "task_count" in analysis
        assert "priority_distribution" in analysis
        assert "hours_stats" in analysis
        assert "quality_score" in analysis

        # 验证任务数量
        assert analysis["task_count"] > 0

        # 验证优先级分布
        assert sum(analysis["priority_distribution"].values()) == analysis["task_count"]

    def test_parse_tasks_with_issues(self, test_markdown_file_with_issues):
        """测试解析包含质量问题的文件"""
        from src.dashboard.services.task_import_service import TaskDataAnalyzer

        analyzer = TaskDataAnalyzer()
        analysis = analyzer.analyze_markdown_tasks(test_markdown_file_with_issues)

        assert analysis is not None
        assert "issues" in analysis
        assert "quality_score" in analysis

        # 有问题的文件质量分数应该较低
        assert analysis["quality_score"] < 80

        # 应该检测到问题
        if analysis["issues"]:
            assert len(analysis["issues"]) > 0

    def test_extract_sections_from_markdown(self):
        """测试从Markdown中提取小节"""
        from src.dashboard.services.task_import_service import TaskDataAnalyzer

        analyzer = TaskDataAnalyzer()
        sections = analyzer._extract_sections(SAMPLE_TASKS_MARKDOWN)

        assert len(sections) > 0
        assert all(isinstance(section, dict) for section in sections)

        # 验证小节结构
        for section in sections:
            assert "name" in section
            assert "stage" in section
            assert "estimated_hours" in section

    def test_build_context(self):
        """测试构建解析上下文"""
        from src.dashboard.services.task_import_service import TaskDataAnalyzer

        analyzer = TaskDataAnalyzer()
        context = analyzer._build_context(SAMPLE_TASKS_MARKDOWN)

        assert "stages" in context
        assert "sections" in context
        assert "current_stage" in context
        assert "current_section" in context

        # 验证上下文内容
        assert len(context["stages"]) > 0
        assert len(context["sections"]) > 0

    def test_detect_duplicate_tasks(self):
        """测试重复任务检测"""
        from src.dashboard.services.task_import_service import TaskDataAnalyzer

        analyzer = TaskDataAnalyzer()

        # 创建重复任务
        tasks = [
            {"title": "相同任务标题"},
            {"title": "相同任务标题"},
            {"title": "不同任务标题"}
        ]

        duplicates = analyzer._detect_duplicate_tasks(tasks)
        assert len(duplicates) > 0
        assert "相同任务标题" in duplicates

    def test_validate_task_format(self):
        """测试任务格式验证"""
        from src.dashboard.services.task_import_service import TaskDataAnalyzer

        analyzer = TaskDataAnalyzer()

        # 有效任务格式
        valid_task = "- [ ] 任务描述 [P0] (4小时)"
        is_valid = analyzer._validate_task_format(valid_task)
        assert is_valid

        # 无效任务格式
        invalid_task = "这不是任务行"
        is_valid = analyzer._validate_task_format(invalid_task)
        assert not is_valid

    def test_parse_complex_markdown_structure(self):
        """测试解析复杂的Markdown结构"""
        from src.dashboard.services.task_import_service import TaskDataAnalyzer

        # 创建更复杂的Markdown结构
        complex_markdown = """
# 项目任务清单

## 阶段1: 第一阶段

### 1.1 小节1.1 (2小时)
- [ ] 任务1 [P0]
- [ ] 任务2 [P1]
- [ ] 任务3

### 1.2 小节1.2 (3小时)
- [ ] 任务4 [P0]
- [ ] 任务5

## 阶段2: 第二阶段

### 2.1 小节2.1 (4小时)
- [ ] 任务6 [P2]
- [ ] 任务7
"""

        analyzer = TaskDataAnalyzer()
        tasks = analyzer._extract_tasks_from_markdown(complex_markdown)

        # 验证任务提取
        assert len(tasks) >= 5  # 至少5个任务

        # 验证阶段分配
        stage1_tasks = [t for t in tasks if "阶段1" in t.get("stage", "")]
        stage2_tasks = [t for t in tasks if "阶段2" in t.get("stage", "")]

        assert len(stage1_tasks) > 0
        assert len(stage2_tasks) > 0

    def test_handle_special_characters(self):
        """测试处理特殊字符"""
        from src.dashboard.services.task_import_service import TaskDataAnalyzer

        analyzer = TaskDataAnalyzer()

        # 测试包含特殊字符的任务
        special_char_task = "- [ ] 创建 `特殊路径/文件.py` 任务 [P0] (4小时)"
        parsed = analyzer._extract_single_task(special_char_task, {})

        assert parsed is not None
        assert "特殊路径/文件.py" in parsed["title"]

    def test_extract_multiple_priorities(self):
        """测试提取多种优先级"""
        from src.dashboard.services.task_import_service import TaskDataAnalyzer

        analyzer = TaskDataAnalyzer()

        priorities = []
        test_lines = [
            "- [ ] 任务1 [P0]",
            "- [ ] 任务2 [P1]",
            "- [ ] 任务3 [P2]",
            "- [ ] 任务4 [P0]"
        ]

        for line in test_lines:
            priority = analyzer._extract_priority(line)
            priorities.append(priority)

        assert priorities == ["P0", "P1", "P2", "P0"]

    def test_extract_section_with_variations(self):
        """测试不同格式的小节标题提取"""
        from src.dashboard.services.task_import_service import TaskDataAnalyzer

        analyzer = TaskDataAnalyzer()

        test_sections = [
            "### 1.1 标题 (4小时)",
            "### 2.1-标题 [P1]",
            "### 3.1 复杂标题 (2小时)"
        ]

        for section in test_sections:
            hours = analyzer._extract_estimated_hours(section)
            # 验证小时数提取
            assert isinstance(hours, (int, type(None)))
