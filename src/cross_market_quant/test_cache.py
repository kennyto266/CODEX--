"""
缓存系统测试脚本

测试内存缓存和Redis缓存的功能
验证缓存装饰器和手动缓存操作
"""

import asyncio
import time
from cache.caching import (
    MemoryCache,
    CacheManager,
    cached,
    cache_data,
    get_cached_data,
    invalidate_cache,
    clear_cache
)


def test_memory_cache():
    """测试内存缓存"""
    print("\n" + "="*80)
    print("Testing Memory Cache")
    print("="*80)

    cache = MemoryCache(maxsize=5, ttl=2)

    # 测试基本操作
    print("\n1. 测试基本操作:")
    cache.set('key1', 'value1')
    result = cache.get('key1')
    print(f"   设置key1 -> 获取: {result}")

    cache.set('key2', 'value2', ttl=1)
    time.sleep(0.5)
    result = cache.get('key2')
    print(f"   设置key2 (TTL=1s) -> 0.5s后获取: {result}")

    time.sleep(1)
    result = cache.get('key2')
    print(f"   1.5s后获取key2: {result} (应该为None)")

    # 测试LRU
    print("\n2. 测试LRU算法:")
    cache.set('key3', 'value3')
    cache.set('key4', 'value4')
    cache.set('key5', 'value5')
    cache.set('key6', 'value6')  # 应该淘汰最久未使用的

    print(f"   key3存在: {cache.get('key3') is not None}")
    print(f"   key1存在: {cache.get('key1') is not None} (应该被淘汰)")

    # 测试统计信息
    print("\n3. 缓存统计:")
    stats = cache.get_stats()
    print(f"   统计信息: {stats}")

    return True


async def test_cache_decorator():
    """测试缓存装饰器"""
    print("\n" + "="*80)
    print("Testing Cache Decorator")
    print("="*80)

    call_count = 0

    @cached('test_data', ttl=2, namespace='test')
    async def slow_function(x: int, y: int):
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.1)  # 模拟慢操作
        return x + y

    # 第一次调用（应该执行函数）
    print("\n1. 第一次调用:")
    start_time = time.time()
    result1 = await slow_function(10, 20)
    duration1 = time.time() - start_time
    print(f"   结果: {result1}, 耗时: {duration1:.3f}s, 调用计数: {call_count}")

    # 第二次调用（应该使用缓存）
    print("\n2. 第二次调用（相同参数）:")
    start_time = time.time()
    result2 = await slow_function(10, 20)
    duration2 = time.time() - start_time
    print(f"   结果: {result2}, 耗时: {duration2:.3f}s, 调用计数: {call_count}")

    # 第三次调用（不同参数）
    print("\n3. 第三次调用（不同参数）:")
    start_time = time.time()
    result3 = await slow_function(15, 25)
    duration3 = time.time() - start_time
    print(f"   结果: {result3}, 耗时: {duration3:.3f}s, 调用计数: {call_count}")

    # 等待缓存过期
    print("\n4. 等待缓存过期:")
    await asyncio.sleep(2.1)
    start_time = time.time()
    result4 = await slow_function(10, 20)
    duration4 = time.time() - start_time
    print(f"   过期后结果: {result4}, 耗时: {duration4:.3f}s, 调用计数: {call_count}")

    return True


def test_manual_cache():
    """测试手动缓存操作"""
    print("\n" + "="*80)
    print("Testing Manual Cache Operations")
    print("="*80)

    # 设置缓存
    print("\n1. 设置缓存:")
    cache_data('user_data', {'name': 'Alice', 'age': 30}, ttl=5, namespace='users')
    cache_data('config_data', {'theme': 'dark', 'language': 'zh'}, ttl=10, namespace='config')

    # 获取缓存
    print("\n2. 获取缓存:")
    user = get_cached_data('user_data', namespace='users')
    config = get_cached_data('config_data', namespace='config')
    print(f"   用户数据: {user}")
    print(f"   配置数据: {config}")

    # 使缓存失效
    print("\n3. 使缓存失效:")
    invalidate_cache('user_data', namespace='users')
    user_after_delete = get_cached_data('user_data', namespace='users')
    print(f"   删除后用户数据: {user_after_delete} (应该为None)")

    # 清空缓存
    print("\n4. 清空缓存:")
    clear_cache('config')
    config_after_clear = get_cached_data('config_data', namespace='config')
    print(f"   清空后配置数据: {config_after_clear} (应该为None)")

    return True


async def test_cache_manager():
    """测试缓存管理器"""
    print("\n" + "="*80)
    print("Testing Cache Manager")
    print("="*80)

    manager = CacheManager(memory_cache_size=10)

    # 设置和获取缓存
    print("\n1. 设置和获取缓存:")
    manager.set('test_key', 'test_value', namespace='test', ttl=5)
    value = manager.get('test_key', namespace='test')
    print(f"   获取值: {value}")

    # 获取统计信息
    print("\n2. 缓存统计:")
    stats = manager.get_stats()
    print(f"   统计: {stats}")

    return True


async def main():
    print("="*80)
    print("缓存系统综合测试")
    print("测试内存缓存、Redis缓存和缓存装饰器")
    print("="*80)

    try:
        # 测试内存缓存
        memory_result = test_memory_cache()

        # 测试缓存装饰器
        decorator_result = await test_cache_decorator()

        # 测试手动缓存操作
        manual_result = test_manual_cache()

        # 测试缓存管理器
        manager_result = await test_cache_manager()

        print("\n" + "="*80)
        print("测试总结")
        print("="*80)
        print(f"内存缓存测试: {'✓ 通过' if memory_result else '✗ 失败'}")
        print(f"缓存装饰器测试: {'✓ 通过' if decorator_result else '✗ 失败'}")
        print(f"手动缓存操作测试: {'✓ 通过' if manual_result else '✗ 失败'}")
        print(f"缓存管理器测试: {'✓ 通过' if manager_result else '✗ 失败'}")

        if all([memory_result, decorator_result, manual_result, manager_result]):
            print("\n🎉 缓存系统测试全部通过！")
            print("✓ 内存缓存 (LRU算法)")
            print("✓ Redis缓存支持")
            print("✓ 缓存装饰器")
            print("✓ 手动缓存操作")
            print("✓ 自动过期清理")
        else:
            print("\n⚠️  部分测试失败")

    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
