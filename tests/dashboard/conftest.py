"""
Dashboard模块测试配置和fixtures
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from pathlib import Path

from tests.dashboard.fixtures.task_test_data import (
    TaskTestDataGenerator,
    MockTaskRepository,
    MockSprintRepository,
    MockCacheManager,
    SAMPLE_TASKS_MARKDOWN
)


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_task_repo():
    """模拟任务Repository"""
    return MockTaskRepository()


@pytest.fixture
def mock_sprint_repo():
    """模拟Sprint Repository"""
    return MockSprintRepository()


@pytest.fixture
def mock_cache_manager():
    """模拟缓存管理器"""
    return MockCacheManager()


@pytest.fixture
def test_markdown_file():
    """创建测试用的Markdown文件"""
    file_path = TaskTestDataGenerator.create_test_markdown_file(SAMPLE_TASKS_MARKDOWN)
    yield file_path
    # 清理临时文件
    import os
    if os.path.exists(file_path):
        os.remove(file_path)


@pytest.fixture
def test_markdown_file_with_issues():
    """创建带质量问题的测试文件"""
    from tests.dashboard.fixtures.task_test_data import SAMPLE_TASKS_WITH_ISSUES
    file_path = TaskTestDataGenerator.create_test_markdown_file(SAMPLE_TASKS_WITH_ISSUES)
    yield file_path
    # 清理临时文件
    import os
    if os.path.exists(file_path):
        os.remove(file_path)


@pytest.fixture
def sample_tasks():
    """获取示例任务数据"""
    return TaskTestDataGenerator.get_sample_tasks()


@pytest.fixture
def sample_sprints():
    """获取示例Sprint数据"""
    return TaskTestDataGenerator.get_sample_sprints()


@pytest.fixture
def mock_import_service(mock_task_repo, mock_sprint_repo, mock_cache_manager):
    """模拟任务导入服务"""
    # 这里需要在实际测试中替换为真实的Service类
    # 由于我们正在测试，这些mock对象将用于验证交互
    return Mock(
        task_repository=mock_task_repo,
        sprint_repository=mock_sprint_repo,
        cache_manager=mock_cache_manager
    )


@pytest.fixture
def mock_http_client():
    """模拟HTTP客户端"""
    client = AsyncMock()
    return client


@pytest.fixture
def test_config():
    """测试配置"""
    return {
        "database_url": "sqlite+aiosqlite:///:memory:",
        "cache_enabled": False,
        "test_mode": True,
        "import_batch_size": 100
    }
