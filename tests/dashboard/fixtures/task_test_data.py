"""
测试任务数据导入功能的fixtures和模拟数据
"""

import os
import tempfile
from typing import Dict, List
from pathlib import Path

# 模拟任务清单Markdown内容
SAMPLE_TASKS_MARKDOWN = """# 项目任务清单

## 阶段1: 任务管理系统建设

### 1.1 数据模型设计 (4小时)
- [ ] 创建 `src/dashboard/models/task.py` 任务数据模型 [P0]
- [ ] 创建 `src/dashboard/models/sprint.py` Sprint数据模型 [P0]
- [ ] 创建 `src/dashboard/models/task_status.py` 状态枚举 [P0]
- [ ] 定义数据库迁移脚本 [P1]

### 1.2 任务管理API开发 (8小时)
- [ ] 实现 `/api/tasks` GET端点 (获取任务列表) [P0]
- [ ] 实现 `/api/tasks` POST端点 (创建任务) [P0]
- [ ] 实现 `/api/tasks/{id}` GET端点 (获取任务详情) [P0]
- [ ] 实现 `/api/tasks/{id}` PUT端点 (更新任务) [P0]
- [ ] 实现 `/api/tasks/{id}` DELETE端点 (删除任务) [P1]

## 阶段2: 工作流标准化

### 2.1 任务状态管理 (6小时)
- [ ] 实现任务状态流转逻辑 [P0]
- [ ] 创建状态变更历史记录 [P1]
- [ ] 实现批量状态更新 [P2]

### 2.2 自动化工作流 (8小时)
- [ ] Git集成 - 自动检测PR和提交 [P0]
- [ ] 实现任务状态自动更新 [P0]
- [ ] 创建Webhook处理程序 [P1]
- [ ] 实现任务依赖关系检查 [P2]
"""

# 带质量问题的任务清单
SAMPLE_TASKS_WITH_ISSUES = """# 项目任务清单（有问题版本）

## 阶段1: 任务管理系统建设

### 1.1 数据模型设计 (4小时)
- [ ] 创建任务模型 [P0]
- [ ] 创建Sprint模型 [P0]
- [ ] 无优先级任务
- [ ] 长时间任务超过20小时的超长任务描述 [P1]
- [ ] 创建状态枚举

### 1.2 任务管理API开发 (8小时)
- [ ] 实现获取任务列表 [P0]
- [ ] 实现创建任务 [P0]
- [ ] 无时间估算任务 [P2]
- [ ] 重复任务标题
- [ ] 重复任务标题

## 阶段2: 工作流标准化

### 2.1 任务状态管理 (6小时)
- [ ] 实现任务状态流转逻辑 [P0]
- [ ] 无优先级无时间估算
"""

# 期望解析的任务列表
EXPECTED_TASKS = [
    {
        "title": "创建 `src/dashboard/models/task.py` 任务数据模型",
        "priority": "P0",
        "estimated_hours": None,
        "stage": "阶段1: 任务管理系统建设",
        "section": "1.1 数据模型设计"
    },
    {
        "title": "实现 `/api/tasks` GET端点 (获取任务列表)",
        "priority": "P0",
        "estimated_hours": None,
        "stage": "阶段1: 任务管理系统建设",
        "section": "1.2 任务管理API开发"
    },
]

# 期望的分析结果
EXPECTED_ANALYSIS = {
    "file_path": "test_tasks.md",
    "total_lines": 10,
    "task_count": 5,
    "priority_distribution": {"P0": 2, "P1": 1, "P2": 2},
    "hours_stats": {
        "min": 2,
        "max": 12,
        "avg": 5.5,
        "total": 22
    },
    "quality_score": 85.0,
    "issues": ["无优先级任务", "长时间任务"]
}

# 期望的导入结果
EXPECTED_IMPORT_RESULT = {
    "import_id": "import_20250101_120000",
    "total_tasks": 10,
    "created_tasks": 10,
    "created_sprints": 2,
    "failed_tasks": 0,
    "duplicated_tasks": 0,
    "statistics": {
        "by_priority": {"P0": 5, "P1": 3, "P2": 2},
        "by_stage": {"阶段1": 5, "阶段2": 5}
    }
}


class TaskTestDataGenerator:
    """任务测试数据生成器"""

    @staticmethod
    def create_test_markdown_file(content: str = None) -> str:
        """创建测试用的Markdown文件

        Args:
            content: 文件内容，默认为SAMPLE_TASKS_MARKDOWN

        Returns:
            文件路径
        """
        if content is None:
            content = SAMPLE_TASKS_MARKDOWN

        # 创建临时文件
        fd, path = tempfile.mkstemp(suffix='.md', text=True)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(content)
        except:
            os.close(fd)
            raise

        return path

    @staticmethod
    def get_sample_tasks() -> List[Dict]:
        """获取示例任务列表"""
        return [
            {
                "id": "TASK-100",
                "title": "创建任务数据模型",
                "description": "创建 `src/dashboard/models/task.py` 任务数据模型",
                "priority": "P0",
                "status": "待开始",
                "estimated_hours": 4,
                "sprint_id": "SPRINT-1",
                "stage": "阶段1: 任务管理系统建设",
                "section": "1.1 数据模型设计"
            },
            {
                "id": "TASK-101",
                "title": "实现任务API GET端点",
                "description": "实现 `/api/tasks` GET端点 (获取任务列表)",
                "priority": "P0",
                "status": "待开始",
                "estimated_hours": 4,
                "sprint_id": "SPRINT-1",
                "stage": "阶段1: 任务管理系统建设",
                "section": "1.2 任务管理API开发"
            },
        ]

    @staticmethod
    def get_sample_sprints() -> List[Dict]:
        """获取示例Sprint列表"""
        return [
            {
                "id": "SPRINT-1",
                "name": "阶段1: 任务管理系统建设",
                "goal": "构建完整的任务管理系统核心功能",
                "start_date": "2025-01-01",
                "end_date": "2025-01-10",
                "status": "ACTIVE",
                "task_ids": ["TASK-100", "TASK-101"],
                "planned_hours": 8
            },
            {
                "id": "SPRINT-2",
                "name": "阶段2: 工作流标准化",
                "goal": "实现标准化的任务工作流",
                "start_date": "2025-01-11",
                "end_date": "2025-01-20",
                "status": "PLANNING",
                "task_ids": ["TASK-200", "TASK-201"],
                "planned_hours": 14
            }
        ]


class MockTaskRepository:
    """模拟任务Repository"""

    def __init__(self):
        self.tasks = {}
        self._sequence = 100

    async def create_task(self, task_data: Dict) -> Dict:
        """创建任务"""
        task_id = f"TASK-{self._sequence}"
        self._sequence += 1
        task = {
            "id": task_id,
            **task_data,
            "created_at": "2025-01-01T12:00:00"
        }
        self.tasks[task_id] = task
        return task

    async def get_task(self, task_id: str) -> Dict:
        """获取任务"""
        return self.tasks.get(task_id)

    async def list_tasks(self, filters: Dict = None) -> List[Dict]:
        """列出任务"""
        if not filters:
            return list(self.tasks.values())

        # 简单过滤
        results = []
        for task in self.tasks.values():
            match = True
            for key, value in filters.items():
                if task.get(key) != value:
                    match = False
                    break
            if match:
                results.append(task)
        return results

    async def count_tasks(self, filters: Dict = None) -> int:
        """统计任务数量"""
        return len(await self.list_tasks(filters))

    async def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False


class MockSprintRepository:
    """模拟Sprint Repository"""

    def __init__(self):
        self.sprints = {}
        self._sequence = 1

    async def create_sprint(self, sprint_data: Dict) -> Dict:
        """创建Sprint"""
        sprint_id = f"SPRINT-{self._sequence}"
        self._sequence += 1
        sprint = {
            "id": sprint_id,
            **sprint_data,
            "created_at": "2025-01-01T12:00:00"
        }
        self.sprints[sprint_id] = sprint
        return sprint

    async def get_sprint(self, sprint_id: str) -> Dict:
        """获取Sprint"""
        return self.sprints.get(sprint_id)

    async def list_sprints(self) -> List[Dict]:
        """列出所有Sprint"""
        return list(self.sprints.values())

    async def update_sprint(self, sprint_id: str, data: Dict) -> Dict:
        """更新Sprint"""
        if sprint_id not in self.sprints:
            raise ValueError(f"Sprint不存在: {sprint_id}")

        self.sprints[sprint_id] = {
            **self.sprints[sprint_id],
            **data,
            "updated_at": "2025-01-01T12:00:00"
        }
        return self.sprints[sprint_id]


class MockCacheManager:
    """模拟缓存管理器"""

    def __init__(self):
        self.cache = {}

    async def get(self, key: str):
        """获取缓存"""
        return self.cache.get(key)

    async def set(self, key: str, value, ttl: int = 300):
        """设置缓存"""
        self.cache[key] = value

    async def delete(self, key: str):
        """删除缓存"""
        if key in self.cache:
            del self.cache[key]

    async def clear_pattern(self, pattern: str):
        """清空匹配模式的缓存"""
        keys_to_delete = [k for k in self.cache.keys() if pattern.replace('*', '') in k]
        for key in keys_to_delete:
            del self.cache[key]
        return len(keys_to_delete)
