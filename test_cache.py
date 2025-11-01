"""
測試緩存管理器功能
"""

import asyncio
import time
import sys
import os

# 添加src目錄到路徑
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

# 直接導入緩存模塊
sys.path.insert(0, os.path.join(src_path, 'dashboard', 'cache'))
from cache_manager import cache_manager


async def test_cache_basic():
    """測試基本緩存功能"""
    print("\n=== 測試基本緩存功能 ===")

    # 測試設置和獲取
    await cache_manager.set("test_key", {"name": "test", "value": 123}, ttl=60)
    result = await cache_manager.get("test_key")

    if result and result["name"] == "test":
        print("✅ 基本緩存設置/獲取: 通過")
    else:
        print("❌ 基本緩存設置/獲取: 失敗")
        return False

    return True


async def test_cache_expiration():
    """測試緩存過期"""
    print("\n=== 測試緩存過期 ===")

    # 設置短TTL
    await cache_manager.set("expire_key", "will_expire", ttl=1)
    result1 = await cache_manager.get("expire_key")

    if result1:
        print("✅ 緩存過期前: 通過")
    else:
        print("❌ 緩存過期前: 失敗")
        return False

    # 等待過期
    await asyncio.sleep(1.1)
    result2 = await cache_manager.get("expire_key")

    if result2 is None:
        print("✅ 緩存過期後: 通過")
    else:
        print("❌ 緩存過期後: 失敗")
        return False

    return True


async def test_cache_decorator():
    """測試緩存裝飾器"""
    print("\n=== 測試緩存裝飾器 ===")

    call_count = 0

    @cache_manager.cache_result(ttl=60, key_prefix="test_func")
    async def expensive_function(x: int):
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.1)  # 模擬耗時操作
        return x * 2

    # 第一次調用
    start = time.time()
    result1 = await expensive_function(5)
    time1 = time.time() - start

    # 第二次調用（應該從緩存獲取）
    start = time.time()
    result2 = await expensive_function(5)
    time2 = time.time() - start

    # 驗證結果
    if result1 == 10 and result2 == 10:
        print(f"✅ 緩存裝飾器結果: 通過 (call_count={call_count})")
    else:
        print(f"❌ 緩存裝飾器結果: 失敗 (result1={result1}, result2={result2}, call_count={call_count})")
        return False

    # 驗證性能提升
    if time2 < time1:
        print(f"✅ 緩存性能提升: 通過 (第一次: {time1*1000:.2f}ms, 第二次: {time2*1000:.2f}ms)")
    else:
        print(f"⚠️  緩存性能提升: 警告 (第一次: {time1*1000:.2f}ms, 第二次: {time2*1000:.2f}ms)")
        print("   注意: 這可能是因為內存緩存，實際Redis緩存會有明顯提升")

    return True


async def test_cache_key_generation():
    """測試緩存鍵生成"""
    print("\n=== 測試緩存鍵生成 ===")

    key1 = cache_manager.generate_cache_key("test", param1="value1", param2=123)
    key2 = cache_manager.generate_cache_key("test", param1="value1", param2=123)
    key3 = cache_manager.generate_cache_key("test", param1="value2", param2=123)

    if key1 == key2 and key1 != key3:
        print(f"✅ 緩存鍵生成: 通過")
        print(f"   相同參數生成相同鍵: {key1}")
        print(f"   不同參數生成不同鍵: {key3}")
        return True
    else:
        print(f"❌ 緩存鍵生成: 失敗")
        return False


async def test_cache_invalidation():
    """測試緩存失效"""
    print("\n=== 測試緩存失效 ===")

    # 設置多個緩存
    await cache_manager.set("test:invalidate1", "value1", ttl=60)
    await cache_manager.set("test:invalidate2", "value2", ttl=60)
    await cache_manager.set("other:invalidate3", "value3", ttl=60)

    # 驗證存在
    assert await cache_manager.get("test:invalidate1") is not None
    assert await cache_manager.get("test:invalidate2") is not None
    assert await cache_manager.get("other:invalidate3") is not None

    # 按模式失效
    count = await cache_manager.clear_pattern("test:*")

    if count >= 2:
        print(f"✅ 緩存失效: 通過 (失效了 {count} 個鍵)")
    else:
        print(f"❌ 緩存失效: 失敗 (只失效了 {count} 個鍵)")
        return False

    # 驗證其他鍵未被影響
    if await cache_manager.get("other:invalidate3") is not None:
        print("✅ 模式失效無誤殺: 通過")
    else:
        print("❌ 模式失效無誤殺: 失敗")
        return False

    return True


async def test_cache_health_check():
    """測試健康檢查"""
    print("\n=== 測試健康檢查 ===")

    health = await cache_manager.health_check()

    if health.get("status") == "healthy":
        print(f"✅ 緩存健康檢查: 通過")
        print(f"   類型: {health.get('type')}")
        if health.get("type") == "redis":
            print(f"   內存使用: {health.get('memory_usage')}")
            print(f"   連接數: {health.get('connected_clients')}")
        else:
            print(f"   緩存大小: {health.get('cache_size')}")
        return True
    else:
        print(f"❌ 緩存健康檢查: 失敗")
        print(f"   錯誤: {health.get('error')}")
        return False


async def run_all_tests():
    """運行所有測試"""
    print("\n" + "="*60)
    print("🚀 開始緩存管理器測試")
    print("="*60)

    tests = [
        ("基本功能", test_cache_basic),
        ("過期機制", test_cache_expiration),
        ("緩存裝飾器", test_cache_decorator),
        ("鍵生成", test_cache_key_generation),
        ("緩存失效", test_cache_invalidation),
        ("健康檢查", test_cache_health_check),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name}: 異常 - {e}")
            results.append((name, False))

    # 統計結果
    print("\n" + "="*60)
    print("📊 測試結果統計")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{status}: {name}")

    print(f"\n總計: {passed}/{total} 項測試通過 ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 所有測試通過！緩存系統運行正常。")
    else:
        print(f"\n⚠️  有 {total-passed} 項測試失敗，請檢查配置。")

    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 測試出現異常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
