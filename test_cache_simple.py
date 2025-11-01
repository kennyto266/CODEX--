"""
測試緩存管理器功能（簡化版）
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


async def test_basic():
    print("\n=== 測試基本緩存功能 ===")

    await cache_manager.set("test_key", {"name": "test", "value": 123}, ttl=60)
    result = await cache_manager.get("test_key")

    if result and result["name"] == "test":
        print("PASS: 基本緩存設置/獲取")
        return True
    else:
        print("FAIL: 基本緩存設置/獲取")
        return False


async def test_decorator():
    print("\n=== 測試緩存裝飾器 ===")

    call_count = 0

    @cache_manager.cache_result(ttl=60, key_prefix="test_func")
    async def expensive_function(x: int):
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.1)
        return x * 2

    start = time.time()
    result1 = await expensive_function(5)
    time1 = time.time() - start

    start = time.time()
    result2 = await expensive_function(5)
    time2 = time.time() - start

    if result1 == 10 and result2 == 10 and call_count == 1:
        print(f"PASS: 緩存裝飾器 (調用次數: {call_count})")
        print(f"  第一次: {time1*1000:.2f}ms, 第二次: {time2*1000:.2f}ms")
        return True
    else:
        print(f"FAIL: 緩存裝飾器 (result1={result1}, result2={result2}, call_count={call_count})")
        return False


async def test_key_generation():
    print("\n=== 測試緩存鍵生成 ===")

    key1 = cache_manager.generate_cache_key("test", param1="value1", param2=123)
    key2 = cache_manager.generate_cache_key("test", param1="value1", param2=123)
    key3 = cache_manager.generate_cache_key("test", param1="value2", param2=123)

    if key1 == key2 and key1 != key3:
        print("PASS: 緩存鍵生成")
        print(f"  鍵1: {key1}")
        print(f"  鍵3: {key3}")
        return True
    else:
        print("FAIL: 緩存鍵生成")
        return False


async def test_health():
    print("\n=== 測試健康檢查 ===")

    health = await cache_manager.health_check()

    if health.get("status") == "healthy":
        print(f"PASS: 緩存健康檢查")
        print(f"  類型: {health.get('type')}")
        return True
    else:
        print(f"FAIL: 緩存健康檢查")
        return False


async def main():
    print("\n" + "="*60)
    print("開始緩存管理器測試")
    print("="*60)

    tests = [
        ("基本功能", test_basic),
        ("緩存裝飾器", test_decorator),
        ("鍵生成", test_key_generation),
        ("健康檢查", test_health),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"ERROR: {name} - {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    print("\n" + "="*60)
    print("測試結果")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {name}")

    print(f"\n總計: {passed}/{total} 項測試通過 ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n所有測試通過！緩存系統運行正常。")
    else:
        print(f"\n有 {total-passed} 項測試失敗，請檢查配置。")

    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n測試出現異常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
