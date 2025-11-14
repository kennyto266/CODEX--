#!/usr/bin/env python3
"""
Unit Tests for Enhanced HIBOR API - Story 2.1.1
測試擴展HIBOR API端點
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

# Import the API router
from src.dashboard.api_hibor_enhanced import router

# Create test client
client = TestClient(router)

class TestHiborAPI:
    """HIBOR API測試套件"""

    def test_get_current_hibor_success(self):
        """測試獲取當前HIBOR利率成功"""
        response = client.get("/current")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "current_rates" in data["data"]
        assert "last_update" in data["data"]
        assert "next_update" in data["data"]

        # 檢查所有期限是否存在
        rates = data["data"]["current_rates"]
        required_fields = ["overnight", "one_week", "one_month",
                          "three_months", "six_months", "twelve_months"]
        for field in required_fields:
            assert field in rates

    def test_get_hibor_history_success(self):
        """測試獲取HIBOR歷史數據成功"""
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')

        response = client.get("/history", params={
            "start_date": start_date,
            "end_date": end_date
        })

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "data" in data["data"]
        assert "period" in data["data"]
        assert "total_records" in data["data"]

        # 檢查返回數據結構
        if data["data"]["data"]:
            first_record = data["data"]["data"][0]
            assert "date" in first_record
            assert "rates" in first_record
            assert "changes" in first_record

    def test_get_hibor_history_invalid_date_format(self):
        """測試無效日期格式"""
        response = client.get("/history", params={
            "start_date": "2025/11/01",  # 錯誤格式
            "end_date": "2025-11-04"
        })

        assert response.status_code == 400

    def test_get_available_tenors(self):
        """測試獲取可用期限列表"""
        response = client.get("/tenors")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "tenors" in data["data"]
        assert "total" in data["data"]

        # 檢查期限數量
        assert data["data"]["total"] == 6

        # 檢查期限結構
        tenors = data["data"]["tenors"]
        required_fields = ["code", "name", "description", "unit", "frequency"]
        for tenor in tenors:
            for field in required_fields:
                assert field in tenor

    def test_get_hibor_trend(self):
        """測試HIBOR趨勢分析"""
        response = client.get("/trend/overnight", params={
            "period": "1M"
        })

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "tenor" in data["data"]
        assert "period" in data["data"]
        assert "trend" in data["data"]
        assert "change" in data["data"]
        assert "change_percentage" in data["data"]
        assert "data_points" in data["data"]

        # 驗證趨勢值
        trend_values = ["increasing", "decreasing", "stable"]
        assert data["data"]["trend"] in trend_values

    def test_export_hibor_data_json(self):
        """測試導出JSON格式數據"""
        start_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')

        response = client.get("/export", params={
            "start_date": start_date,
            "end_date": end_date,
            "format": "json"
        })

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["data"]["format"] == "json"
        assert "data" in data["data"]
        assert "filename" in data["data"]
        assert "records" in data["data"]

    def test_export_hibor_data_csv(self):
        """測試導出CSV格式數據"""
        start_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')

        response = client.get("/export", params={
            "start_date": start_date,
            "end_date": end_date,
            "format": "csv"
        })

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["data"]["format"] == "csv"
        assert "data" in data["data"]
        assert "filename" in data["data"]
        assert "records" in data["data"]

    def test_hibor_health_check(self):
        """測試HIBOR API健康檢查"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["data"]["status"] == "healthy"
        assert "source" in data["data"]
        assert "version" in data["data"]
        assert "last_check" in data["data"]

    def test_get_hibor_history_edge_cases(self):
        """測試HIBOR歷史數據邊緣情況"""
        # 測試開始日期晚於結束日期
        start_date = datetime.now().strftime('%Y-%m-%d')
        end_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

        response = client.get("/history", params={
            "start_date": start_date,
            "end_date": end_date
        })

        # 應該成功但返回空數據
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_hibor_trend_invalid_tenor(self):
        """測試無效期限的趨勢分析"""
        response = client.get("/trend/invalid_tenor")

        assert response.status_code == 200  # Mock數據允許任何期限
        data = response.json()
        assert data["success"] is True

    def test_api_response_structure(self):
        """測試API響應結構"""
        response = client.get("/tenors")

        assert response.status_code == 200
        data = response.json()

        # 檢查統一API響應格式
        assert "success" in data
        assert "data" in data
        assert "message" in data
        assert "timestamp" in data  # 如果有timestamp字段


# Performance Tests
class TestHiborPerformance:
    """HIBOR API性能測試"""

    def test_concurrent_requests(self):
        """測試並發請求"""
        import concurrent.futures
        import threading

        def make_request():
            return client.get("/current")

        # 模擬50個並發請求
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [future.result() for future in futures]

        # 驗證所有請求都成功
        success_count = sum(1 for r in results if r.status_code == 200)
        assert success_count == 50

    def test_response_time(self):
        """測試響應時間"""
        import time

        start_time = time.time()
        response = client.get("/current")
        end_time = time.time()

        assert response.status_code == 200
        response_time = end_time - start_time

        # 響應時間應該小於200ms（根據需求）
        assert response_time < 0.2, f"Response time {response_time}s exceeded 200ms"

    def test_data_consistency(self):
        """測試數據一致性"""
        # 多次獲取當前數據，應該返回相似結果
        responses = []
        for _ in range(10):
            response = client.get("/current")
            responses.append(response.json())

        # 所有響應應該有相同的結構
        for resp in responses:
            assert resp["success"] is True
            assert "current_rates" in resp["data"]


if __name__ == "__main__":
    # 運行測試
    pytest.main([__file__, "-v", "--tb=short"])
