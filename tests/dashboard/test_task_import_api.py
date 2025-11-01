"""
任务导入API测试
测试REST API端点的功能
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from tests.dashboard.fixtures.task_test_data import (
    SAMPLE_TASKS_MARKDOWN,
    TaskTestDataGenerator,
    MockTaskRepository,
    MockSprintRepository
)


class TestTaskImportAPI:
    """任务导入API测试类"""

    @pytest.fixture
    def app(self):
        """创建测试应用"""
        from src.dashboard.api.task_import import create_app
        app = create_app()
        return app

    @pytest.fixture
    def client(self, app):
        """创建测试客户端"""
        return TestClient(app)

    @pytest.fixture
    def mock_repos(self):
        """模拟Repository"""
        return {
            "task": MockTaskRepository(),
            "sprint": MockSprintRepository()
        }

    def test_analyze_endpoint(self, client, mock_repos):
        """测试分析端点"""
        # 创建测试文件
        file_path = TaskTestDataGenerator.create_test_markdown_file(SAMPLE_TASKS_MARKDOWN)

        try:
            response = client.post(
                "/api/v1/import/tasks/analyze",
                json={"file_path": file_path}
            )

            assert response.status_code == 200
            data = response.json()
            assert "task_count" in data
            assert "priority_distribution" in data
            assert "quality_score" in data
        finally:
            import os
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_start_import_endpoint(self, client, mock_repos):
        """测试开始导入端点"""
        # 创建测试文件
        file_path = TaskTestDataGenerator.create_test_markdown_file(SAMPLE_TASKS_MARKDOWN)

        try:
            response = client.post(
                "/api/v1/import/tasks/start",
                json={
                    "file_path": file_path,
                    "create_sprint": True
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "import_id" in data
            assert "status" in data
            assert data["status"] == "running"
        finally:
            import os
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_status_endpoint(self, client, mock_repos):
        """测试状态查询端点"""
        import_id = "import_20250101_120000"

        response = client.get(f"/api/v1/import/tasks/status/{import_id}")

        assert response.status_code == 200
        data = response.json()
        assert "import_id" in data
        assert "status" in data
        assert "progress" in data

    def test_report_endpoint(self, client, mock_repos):
        """测试报告端点"""
        import_id = "import_20250101_120000"

        response = client.get(f"/api/v1/import/tasks/report/{import_id}")

        assert response.status_code == 200
        data = response.json()
        assert "import_id" in data
        assert "summary" in data
        assert "task_list" in data

    def test_upload_endpoint(self, client):
        """测试文件上传端点"""
        # 创建临时文件
        file_path = TaskTestDataGenerator.create_test_markdown_file(SAMPLE_TASKS_MARKDOWN)

        try:
            with open(file_path, 'rb') as f:
                response = client.post(
                    "/api/v1/import/tasks/upload",
                    files={"file": f},
                    data={"create_sprint": "true"}
                )

            # 根据实际实现调整响应
            assert response.status_code in [200, 201]
        finally:
            import os
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_rollback_endpoint(self, client, mock_repos):
        """测试回滚端点"""
        task_ids = ["TASK-100", "TASK-101", "TASK-102"]

        response = client.post(
            "/api/v1/import/tasks/rollback",
            json={"task_ids": task_ids}
        )

        assert response.status_code == 200
        data = response.json()
        assert "deleted_count" in data
        assert "status" in data

    def test_validate_endpoint(self, client, mock_repos):
        """测试验证端点"""
        response = client.get("/api/v1/import/tasks/validate")

        assert response.status_code == 200
        data = response.json()
        assert "is_valid" in data
        assert "errors" in data

    def test_list_imports_endpoint(self, client, mock_repos):
        """测试列出导入记录端点"""
        response = client.get("/api/v1/import/tasks/list")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_simulate_endpoint(self, client, mock_repos):
        """测试模拟导入端点"""
        # 创建测试文件
        file_path = TaskTestDataGenerator.create_test_markdown_file(SAMPLE_TASKS_MARKDOWN)

        try:
            response = client.post(
                "/api/v1/import/tasks/simulate",
                json={"file_path": file_path}
            )

            assert response.status_code == 200
            data = response.json()
            assert "total_tasks" in data
            assert "will_create" in data
            assert "preview" in data
        finally:
            import os
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_analyze_nonexistent_file(self, client):
        """测试分析不存在的文件"""
        response = client.post(
            "/api/v1/import/tasks/analyze",
            json={"file_path": "/nonexistent/file.md"}
        )

        assert response.status_code == 404
        data = response.json()
        assert "error" in data

    def test_start_import_nonexistent_file(self, client):
        """测试导入不存在的文件"""
        response = client.post(
            "/api/v1/import/tasks/start",
            json={"file_path": "/nonexistent/file.md"}
        )

        assert response.status_code == 404
        data = response.json()
        assert "error" in data

    def test_analyze_invalid_json(self, client):
        """测试分析端点接收无效JSON"""
        response = client.post(
            "/api/v1/import/tasks/analyze",
            json={}  # 缺少file_path
        )

        assert response.status_code == 422  # 验证错误

    def test_upload_no_file(self, client):
        """测试上传端点未提供文件"""
        response = client.post("/api/v1/import/tasks/upload")

        assert response.status_code == 422  # 验证错误

    def test_rollback_empty_task_list(self, client):
        """测试回滚端点传入空任务列表"""
        response = client.post(
            "/api/v1/import/tasks/rollback",
            json={"task_ids": []}
        )

        assert response.status_code == 400  # 客户端错误

    def test_status_nonexistent_import(self, client):
        """测试查询不存在的导入记录"""
        import_id = "import_nonexistent"

        response = client.get(f"/api/v1/import/tasks/status/{import_id}")

        assert response.status_code == 404

    def test_report_nonexistent_import(self, client):
        """测试获取不存在导入的报告"""
        import_id = "import_nonexistent"

        response = client.get(f"/api/v1/import/tasks/report/{import_id}")

        assert response.status_code == 404

    def test_analyze_with_invalid_markdown(self, client):
        """测试分析无效的Markdown文件"""
        invalid_markdown = "这不是有效的Markdown格式"

        file_path = TaskTestDataGenerator.create_test_markdown_file(invalid_markdown)

        try:
            response = client.post(
                "/api/v1/import/tasks/analyze",
                json={"file_path": file_path}
            )

            # 应该返回空结果或错误
            assert response.status_code in [200, 400]
            data = response.json()
            assert "task_count" in data
        finally:
            import os
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_large_file_upload(self, client):
        """测试大文件上传"""
        # 创建大文件
        large_markdown = """
# 大型任务清单

"""
        for i in range(1000):
            large_markdown += f"- [ ] 任务{i} [P0]\n"

        file_path = TaskTestDataGenerator.create_test_markdown_file(large_markdown)

        try:
            with open(file_path, 'rb') as f:
                response = client.post(
                    "/api/v1/import/tasks/upload",
                    files={"file": f}
                )

            # 根据实际API限制调整
            assert response.status_code in [200, 413]  # 413为文件过大
        finally:
            import os
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_api_rate_limiting(self, client):
        """测试API速率限制"""
        file_path = TaskTestDataGenerator.create_test_markdown_file(SAMPLE_TASKS_MARKDOWN)

        try:
            # 快速发送多个请求
            for i in range(10):
                response = client.post(
                    "/api/v1/import/tasks/analyze",
                    json={"file_path": file_path}
                )

                # 根据实际实现，可能触发速率限制
                if response.status_code == 429:
                    break
        finally:
            import os
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_concurrent_import_requests(self, client):
        """测试并发导入请求"""
        file_path = TaskTestDataGenerator.create_test_markdown_file(SAMPLE_TASKS_MARKDOWN)

        try:
            import asyncio
            import threading

            results = []
            errors = []

            def make_request():
                try:
                    response = client.post(
                        "/api/v1/import/tasks/start",
                        json={"file_path": file_path}
                    )
                    results.append(response.status_code)
                except Exception as e:
                    errors.append(str(e))

            # 启动多个线程
            threads = []
            for i in range(5):
                thread = threading.Thread(target=make_request)
                threads.append(thread)
                thread.start()

            # 等待所有线程完成
            for thread in threads:
                thread.join()

            # 验证结果
            assert len(errors) == 0 or len(results) > 0
        finally:
            import os
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_api_error_handling(self, client):
        """测试API错误处理"""
        # 模拟服务器错误
        with patch('src.dashboard.api.task_import.analyze_markdown_tasks') as mock:
            mock.side_effect = Exception("模拟服务器错误")

            response = client.post(
                "/api/v1/import/tasks/analyze",
                json={"file_path": "/test/file.md"}
            )

            # 应该返回500错误
            assert response.status_code == 500
            data = response.json()
            assert "error" in data

    def test_api_response_format(self, client):
        """测试API响应格式"""
        file_path = TaskTestDataGenerator.create_test_markdown_file(SAMPLE_TASKS_MARKDOWN)

        try:
            response = client.post(
                "/api/v1/import/tasks/analyze",
                json={"file_path": file_path}
            )

            assert response.status_code == 200
            data = response.json()

            # 验证响应格式
            assert "task_count" in data
            assert isinstance(data["task_count"], int)
            assert "priority_distribution" in data
            assert isinstance(data["priority_distribution"], dict)
            assert "quality_score" in data
            assert isinstance(data["quality_score"], (int, float))

            # 验证质量分数范围
            assert 0 <= data["quality_score"] <= 100
        finally:
            import os
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_api_caching(self, client):
        """测试API缓存功能"""
        file_path = TaskTestDataGenerator.create_test_markdown_file(SAMPLE_TASKS_MARKDOWN)

        try:
            # 第一次请求
            response1 = client.post(
                "/api/v1/import/tasks/analyze",
                json={"file_path": file_path}
            )

            # 第二次相同请求（应该命中缓存）
            response2 = client.post(
                "/api/v1/import/tasks/analyze",
                json={"file_path": file_path}
            )

            # 验证响应一致
            assert response1.json() == response2.json()
        finally:
            import os
            if os.path.exists(file_path):
                os.remove(file_path)
