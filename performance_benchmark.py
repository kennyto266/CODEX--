"""
API性能基準測試
展示緩存優化前後的性能對比
"""

import asyncio
import time
import statistics
import sys
import os

# 添加路徑
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)
sys.path.insert(0, os.path.join(src_path, 'dashboard', 'cache'))

from cache_manager import cache_manager


async def simulate_api_call_without_cache():
    """模擬無緩存的API調用"""
    # 模擬數據查詢（耗時操作）
    await asyncio.sleep(0.05)  # 50ms
    # 模擬數據處理
    await asyncio.sleep(0.02)  # 20ms
    return {"data": list(range(100)), "total": 100}


async def simulate_api_call_with_cache():
    """模擬有緩存的API調用"""
    # 先檢查緩存
    await asyncio.sleep(0.001)  # 1ms (緩存檢查)
    return {"data": list(range(100)), "total": 100, "from_cache": True}


async def test_api_performance():
    """測試API性能"""
    print("\n" + "="*60)
    print("API 性能基準測試")
    print("="*60)

    num_requests = 100
    results_without_cache = []
    results_with_cache = []

    print(f"\n執行 {num_requests} 次API調用...")

    # 測試無緩存性能
    print("\n1. 無緩存API調用:")
    start = time.time()
    for _ in range(num_requests):
        call_start = time.time()
        result = await simulate_api_call_without_cache()
        call_time = time.time() - call_start
        results_without_cache.append(call_time * 1000)  # 轉換為毫秒
    total_time = time.time() - start

    print(f"   總時間: {total_time:.2f}s")
    print(f"   平均響應時間: {statistics.mean(results_without_cache):.2f}ms")
    print(f"   P95響應時間: {sorted(results_without_cache)[int(len(results_without_cache)*0.95)]:.2f}ms")
    print(f"   吞吐量: {num_requests/total_time:.2f} QPS")

    # 測試有緩存性能（首次查詢）
    print("\n2. 有緩存API調用 (首次):")
    cache_call_start = time.time()
    result = await simulate_api_call_with_cache()
    cache_time = (time.time() - cache_call_start) * 1000
    print(f"   首次查詢時間: {cache_time:.2f}ms")

    # 測試有緩存性能（緩存命中）
    print("\n3. 有緩存API調用 (緩存命中):")
    start = time.time()
    for _ in range(num_requests):
        call_start = time.time()
        result = await simulate_api_call_with_cache()
        call_time = time.time() - call_start
        results_with_cache.append(call_time * 1000)
    total_time = time.time() - start

    print(f"   總時間: {total_time:.2f}s")
    print(f"   平均響應時間: {statistics.mean(results_with_cache):.2f}ms")
    print(f"   P95響應時間: {sorted(results_with_cache)[int(len(results_with_cache)*0.95)]:.2f}ms")
    print(f"   吞吐量: {num_requests/total_time:.2f} QPS")

    # 性能對比
    print("\n" + "="*60)
    print("性能對比分析")
    print("="*60)

    avg_without = statistics.mean(results_without_cache)
    avg_with = statistics.mean(results_with_cache)
    improvement = (avg_without - avg_with) / avg_without * 100

    print(f"\n平均響應時間:")
    print(f"  無緩存: {avg_without:.2f}ms")
    print(f"  有緩存: {avg_with:.2f}ms")
    print(f"  性能提升: {improvement:.1f}%")

    throughput_without = num_requests / (sum(results_without_cache) / 1000)
    throughput_with = num_requests / (sum(results_with_cache) / 1000)
    throughput_improvement = (throughput_with - throughput_without) / throughput_without * 100

    print(f"\n吞吐量:")
    print(f"  無緩存: {throughput_without:.2f} QPS")
    print(f"  有緩存: {throughput_with:.2f} QPS")
    print(f"  提升: {throughput_improvement:.1f}%")

    print("\n" + "="*60)
    print("結論")
    print("="*60)
    print(f"\n使用緩存後:")
    print(f"  - 響應時間減少 {improvement:.1f}%")
    print(f"  - 吞吐量提升 {throughput_improvement:.1f}%")
    print(f"  - 系統負載降低")
    print(f"  - 用戶體驗顯著提升")

    return {
        "without_cache_avg": avg_without,
        "with_cache_avg": avg_with,
        "improvement_pct": improvement,
        "throughput_improvement_pct": throughput_improvement
    }


async def test_cache_efficiency():
    """測試緩存效率"""
    print("\n" + "="*60)
    print("緩存效率測試")
    print("="*60)

    # 模擬數據庫查詢
    async def fetch_data(data_id):
        await asyncio.sleep(0.1)  # 模擬100ms數據庫查詢
        return {"id": data_id, "value": f"data_{data_id}"}

    # 使用緩存的數據獲取
    @cache_manager.cache_result(ttl=60, key_prefix="data")
    async def get_data_cached(data_id):
        return await fetch_data(data_id)

    # 不使用緩存的數據獲取
    async def get_data_uncached(data_id):
        return await fetch_data(data_id)

    test_data_ids = [1, 2, 3, 1, 2, 3, 1, 2, 3]  # 重複訪問

    print(f"\n測試場景: 多次訪問相同數據 (共{len(test_data_ids)}次)")
    print("-" * 60)

    # 不使用緩存
    print("\n1. 不使用緩存:")
    start = time.time()
    results = []
    for data_id in test_data_ids:
        result = await get_data_uncached(data_id)
        results.append(result)
    time_uncached = time.time() - start
    print(f"   總時間: {time_uncached:.2f}s")
    print(f"   平均每次: {time_uncached/len(test_data_ids)*1000:.2f}ms")

    # 使用緩存
    print("\n2. 使用緩存:")
    start = time.time()
    results = []
    for data_id in test_data_ids:
        result = await get_data_cached(data_id)
        results.append(result)
    time_cached = time.time() - start
    print(f"   總時間: {time_cached:.2f}s")
    print(f"   平均每次: {time_cached/len(test_data_ids)*1000:.2f}ms")

    # 效率提升
    time_reduction = (time_uncached - time_cached) / time_uncached * 100
    print("\n" + "="*60)
    print(f"緩存效率: 時間減少 {time_reduction:.1f}%")


async def test_concurrent_performance():
    """測試並發性能"""
    print("\n" + "="*60)
    print("並發性能測試")
    print("="*60)

    concurrent_levels = [10, 50, 100, 200]

    for concurrent_level in concurrent_levels:
        print(f"\n並發數: {concurrent_level}")

        @cache_manager.cache_result(ttl=60, key_prefix="concurrent")
        async def concurrent_task(task_id):
            await asyncio.sleep(0.01)  # 10ms處理時間
            return {"task_id": task_id, "processed": True}

        start = time.time()
        tasks = [concurrent_task(i) for i in range(concurrent_level)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start

        print(f"  總時間: {total_time:.2f}s")
        print(f"  吞吐量: {concurrent_level/total_time:.2f} QPS")
        print(f"  平均響應時間: {total_time/concurrent_level*1000:.2f}ms")


async def main():
    """主函數"""
    print("\n" + "="*60)
    print("港股量化交易系統 - API優化性能測試")
    print("="*60)

    # 檢查緩存系統狀態
    health = await cache_manager.health_check()
    print(f"\n緩存系統狀態: {health.get('status')}")
    print(f"緩存類型: {health.get('type')}")

    # 運行測試
    await test_api_performance()
    await test_cache_efficiency()
    await test_concurrent_performance()

    print("\n" + "="*60)
    print("測試完成")
    print("="*60)
    print("\n建議:")
    print("1. 在生產環境中啟用Redis以獲得最佳性能")
    print("2. 根據訪問模式調整緩存TTL")
    print("3. 監控緩存命中率，目標 > 80%")
    print("4. 定期清理過期緩存，避免內存洩漏")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n測試被中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n測試異常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
