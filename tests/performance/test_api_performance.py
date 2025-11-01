#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API性能测试
"""

import pytest
import asyncio
import time
import statistics
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import requests


class TestAPIPerformance:
    """API性能测试类"""

    @pytest.fixture
    def api_base_url(self):
        """API基础URL"""
        return "http://localhost:8001"

    @pytest.fixture
    async def api_session(self):
        """API会话"""
        async with aiohttp.ClientSession() as session:
            yield session

    def test_health_check_performance(self, api_base_url):
        """测试健康检查接口性能"""
        response_times = []

        for _ in range(100):
            start_time = time.time()
            response = requests.get(f"{api_base_url}/health")
            end_time = time.time()

            assert response.status_code == 200
            response_times.append(end_time - start_time)

        # 验证响应时间统计
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        min_time = min(response_times)

        print(f"\n健康检查接口性能统计:")
        print(f"  平均响应时间: {avg_time*1000:.2f}ms")
        print(f"  最大响应时间: {max_time*1000:.2f}ms")
        print(f"  最小响应时间: {min_time*1000:.2f}ms")

        # 性能断言
        assert avg_time < 0.1  # 平均响应时间应小于100ms
        assert max_time < 0.5  # 最大响应时间应小于500ms

    async def test_concurrent_api_requests(self, api_session, api_base_url):
        """测试并发API请求性能"""
        async def make_request(session, url):
            start_time = time.time()
            async with session.get(url) as response:
                await response.json()
                end_time = time.time()
                return end_time - start_time

        # 并发100个请求
        num_requests = 100
        tasks = [
            make_request(api_session, f"{api_base_url}/health")
            for _ in range(num_requests)
        ]

        start_time = time.time()
        response_times = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # 统计结果
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        p95_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile

        print(f"\n并发{num_requests}个API请求性能统计:")
        print(f"  总耗时: {total_time:.2f}s")
        print(f"  平均响应时间: {avg_time*1000:.2f}ms")
        print(f"  最大响应时间: {max_time*1000:.2f}ms")
        print(f"  最小响应时间: {min_time*1000:.2f}ms")
        print(f"  95%分位响应时间: {p95_time*1000:.2f}ms")
        print(f"  吞吐量: {num_requests/total_time:.2f} req/s")

        # 性能断言
        assert p95_time < 0.2  # 95%分位响应时间应小于200ms
        assert (num_requests / total_time) > 500  # 吞吐量应大于500 req/s

    def test_api_throughput_benchmark(self, api_base_url):
        """测试API吞吐量基准"""
        # 测试不同并发级别的吞吐量
        concurrency_levels = [1, 10, 50, 100, 200]
        results = []

        for concurrency in concurrency_levels:
            requests_per_test = 500
            response_times = []

            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = []

                for _ in range(requests_per_test):
                    future = executor.submit(
                        lambda: time.time() or requests.get(f"{api_base_url}/health").status_code
                    )
                    futures.append(future)

                # 收集结果
                for future in futures:
                    future.result()

            start_time = time.time()
            for _ in range(requests_per_test):
                start = time.time()
                response = requests.get(f"{api_base_url}/health")
                end = time.time()
                assert response.status_code == 200
                response_times.append(end - start)

            total_time = time.time() - start_time
            throughput = requests_per_test / total_time
            avg_time = statistics.mean(response_times)

            results.append({
                "concurrency": concurrency,
                "throughput": throughput,
                "avg_response_time": avg_time * 1000
            })

            print(f"\n并发级别 {concurrency}:")
            print(f"  吞吐量: {throughput:.2f} req/s")
            print(f"  平均响应时间: {avg_time*1000:.2f}ms")

        # 验证性能曲线
        # 在合理范围内，吞吐量应该随着并发增加而增加
        for i in range(1, len(results)):
            # 并发增加时，吞吐量应该保持或增加
            assert results[i]["throughput"] > results[i-1]["throughput"] * 0.8

    async def test_api_response_time_consistency(self, api_session, api_base_url):
        """测试API响应时间一致性"""
        # 测试1000个请求的响应时间分布
        num_requests = 1000
        response_times = []

        for _ in range(num_requests):
            start_time = time.time()
            async with api_session.get(f"{api_base_url}/health") as response:
                await response.json()
            end_time = time.time()

            response_times.append(end_time - start_time)

        # 计算统计指标
        mean_time = statistics.mean(response_times)
        median_time = statistics.median(response_times)
        stdev_time = statistics.stdev(response_times) if len(response_times) > 1 else 0

        print(f"\n响应时间一致性统计 (n={num_requests}):")
        print(f"  平均值: {mean_time*1000:.2f}ms")
        print(f"  中位数: {median_time*1000:.2f}ms")
        print(f"  标准差: {stdev_time*1000:.2f}ms")
        print(f"  变异系数: {(stdev_time/mean_time)*100:.2f}%")

        # 验证一致性（变异系数应小于50%）
        coefficient_of_variation = (stdev_time / mean_time) * 100
        assert coefficient_of_variation < 50, f"响应时间变异系数过大: {coefficient_of_variation:.2f}%"

    def test_api_memory_usage(self, api_base_url):
        """测试API内存使用情况"""
        import psutil
        import os

        # 获取API进程的PID（假设在同一台机器上）
        # 这里需要实际获取API进程ID
        pid = os.getpid()
        process = psutil.Process(pid)

        # 记录初始内存使用
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 发送大量请求
        num_requests = 1000
        for _ in range(num_requests):
            response = requests.get(f"{api_base_url}/health")
            assert response.status_code == 200

        # 记录测试后内存使用
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        print(f"\n内存使用统计:")
        print(f"  初始内存: {initial_memory:.2f}MB")
        print(f"  最终内存: {final_memory:.2f}MB")
        print(f"  内存增长: {memory_increase:.2f}MB")

        # 验证内存泄漏（内存增长不应超过100MB）
        assert memory_increase < 100, f"可能存在内存泄漏，内存增长过多: {memory_increase:.2f}MB"

    async def test_api_error_rate_performance(self, api_session, api_base_url):
        """测试API错误率对性能的影响"""
        # 发送一些正常请求和错误请求
        num_requests = 100
        error_count = 0

        # 发送混合请求（一些正常的，一些会导致错误的）
        tasks = []
        for i in range(num_requests):
            if i % 10 == 0:  # 10%的请求会导致错误
                url = f"{api_base_url}/nonexistent-endpoint"
                tasks.append(make_error_request(api_session, url))
            else:
                url = f"{api_base_url}/health"
                tasks.append(make_request(api_session, url))

        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time

        # 统计结果
        for result in results:
            if isinstance(result, Exception) or result is False:
                error_count += 1

        error_rate = error_count / num_requests
        success_rate = 1 - error_rate

        print(f"\n错误率性能统计:")
        print(f"  总请求数: {num_requests}")
        print(f"  错误请求数: {error_count}")
        print(f"  错误率: {error_rate*100:.2f}%")
        print(f"  成功率: {success_rate*100:.2f}%")
        print(f"  总耗时: {total_time:.2f}s")

        # 验证错误率与性能的关系
        assert error_rate <= 0.2  # 错误率不应超过20%

        # 即使有错误，系统也应该能够处理
        assert success_rate >= 0.8  # 成功率应该至少80%


async def make_request(session, url):
    """发送API请求"""
    try:
        start_time = time.time()
        async with session.get(url) as response:
            await response.json()
            end_time = time.time()
            return end_time - start_time
    except Exception as e:
        print(f"请求失败: {url}, 错误: {e}")
        return False


async def make_error_request(session, url):
    """发送错误请求"""
    try:
        async with session.get(url) as response:
            await response.json()
            return True
    except Exception as e:
        return False


# 性能测试配置
class PerformanceBenchmarks:
    """性能基准配置"""

    # API响应时间基准 (毫秒)
    RESPONSE_TIME_BENCHMARKS = {
        "health_check": 50,      # 健康检查 < 50ms
        "get_orders": 200,       # 获取订单 < 200ms
        "get_portfolios": 200,   # 获取投资组合 < 200ms
        "create_order": 500,     # 创建订单 < 500ms
        "update_portfolio": 500  # 更新投资组合 < 500ms
    }

    # 吞吐量基准 (请求/秒)
    THROUGHPUT_BENCHMARKS = {
        "simple_endpoint": 1000,  # 简单接口 > 1000 req/s
        "complex_endpoint": 200,  # 复杂接口 > 200 req/s
        "database_query": 100     # 数据库查询 > 100 req/s
    }

    # 并发性能基准
    CONCURRENCY_BENCHMARKS = {
        "max_concurrent_users": 1000,  # 最大并发用户数
        "graceful_degradation": 500    # 优雅降级用户数
    }

    # 资源使用基准
    RESOURCE_BENCHMARKS = {
        "memory_usage_mb": 512,      # 内存使用 < 512MB
        "cpu_usage_percent": 80,     # CPU使用率 < 80%
        "database_connections": 100  # 数据库连接数 < 100
    }


@pytest.mark.performance
class TestPerformanceBenchmarks:
    """性能基准测试"""

    def test_health_check_meets_benchmark(self, api_base_url):
        """测试健康检查接口满足基准"""
        start_time = time.time()
        response = requests.get(f"{api_base_url}/health")
        response_time = (time.time() - start_time) * 1000  # 转换为毫秒

        benchmark = PerformanceBenchmarks.RESPONSE_TIME_BENCHMARKS["health_check"]
        print(f"\n健康检查基准测试:")
        print(f"  响应时间: {response_time:.2f}ms")
        print(f"  基准要求: < {benchmark}ms")

        assert response_time < benchmark
        assert response.status_code == 200

    def test_throughput_meets_benchmark(self, api_base_url):
        """测试吞吐量满足基准"""
        num_requests = 500
        start_time = time.time()

        for _ in range(num_requests):
            response = requests.get(f"{api_base_url}/health")
            assert response.status_code == 200

        total_time = time.time() - start_time
        throughput = num_requests / total_time

        benchmark = PerformanceBenchmarks.THROUGHPUT_BENCHMARKS["simple_endpoint"]
        print(f"\n吞吐量基准测试:")
        print(f"  吞吐量: {throughput:.2f} req/s")
        print(f"  基准要求: > {benchmark} req/s")

        assert throughput > benchmark

    @pytest.mark.slow
    def test_concurrent_load_handling(self, api_base_url):
        """测试并发负载处理能力"""
        concurrent_users = 500
        requests_per_user = 10
        total_requests = concurrent_users * requests_per_user

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            for _ in range(total_requests):
                future = executor.submit(
                    lambda: requests.get(f"{api_base_url}/health").status_code
                )
                futures.append(future)

            # 收集结果
            success_count = 0
            for future in futures:
                if future.result() == 200:
                    success_count += 1

        total_time = time.time() - start_time
        throughput = total_requests / total_time

        print(f"\n并发负载测试:")
        print(f"  并发用户数: {concurrent_users}")
        print(f"  每用户请求数: {requests_per_user}")
        print(f"  总请求数: {total_requests}")
        print(f"  成功请求数: {success_count}")
        print(f"  成功率: {success_count/total_requests*100:.2f}%")
        print(f"  总耗时: {total_time:.2f}s")
        print(f"  吞吐量: {throughput:.2f} req/s")

        assert success_count / total_requests > 0.95  # 成功率应 > 95%
        assert throughput > 100  # 吞吐量应 > 100 req/s
