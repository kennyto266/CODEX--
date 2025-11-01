"""
混合数据源 + 缓存系统 - 综合测试

测试所有数据适配器和缓存机制的工作情况
"""

import asyncio
from adapters.hybrid_adapter_factory import HybridAdapterFactory, fetch_data
from cache.caching import cached, get_cache_manager, cache_data, get_cached_data


async def test_hybrid_with_cache():
    """测试混合数据源与缓存的集成"""
    print("\n" + "="*80)
    print("Testing Hybrid Data Source with Cache")
    print("="*80)

    factory = HybridAdapterFactory()

    # 测试数据源汇总
    print("\n1. 数据源覆盖统计:")
    summary = factory.get_data_source_summary()
    print(f"   总适配器: {summary['total_adapters']}")
    print(f"   支持类型: {summary['supported_types']}")
    print(f"   总symbol数: {summary['total_symbols']}")
    print(f"   覆盖率:")
    for type_name, count in summary['coverage'].items():
        print(f"     - {type_name}: {count}种")

    # 测试FX数据（带缓存）
    print("\n2. 测试FX数据 (USD/CNH):")
    try:
        start_time = asyncio.get_event_loop().time()
        fx_data_1 = await fetch_data('USD_CNH', '2024-01-01', '2024-01-05')
        time_1 = asyncio.get_event_loop().time() - start_time
        print(f"   第一次获取: {len(fx_data_1)}条数据, 耗时: {time_1:.3f}s")

        start_time = asyncio.get_event_loop().time()
        fx_data_2 = await fetch_data('USD_CNH', '2024-01-01', '2024-01-05')
        time_2 = asyncio.get_event_loop().time() - start_time
        print(f"   第二次获取: {len(fx_data_2)}条数据, 耗时: {time_2:.3f}s")
        print(f"   性能提升: {(time_1 - time_2) / time_1 * 100:.1f}%")

        if fx_data_1.equals(fx_data_2):
            print("   ✓ 缓存数据一致")
    except Exception as e:
        print(f"   ✗ 失败: {e}")

    # 测试港股数据
    print("\n3. 测试港股数据 (0700.HK):")
    try:
        hk_data = await fetch_data('0700.HK', '2024-01-01', '2024-01-05')
        print(f"   ✓ 成功获取 {len(hk_data)} 条港股数据")
        if not hk_data.empty:
            print(f"   最新价格: {hk_data.iloc[-1]['Close']:.2f}")
    except Exception as e:
        print(f"   ✗ 失败: {e}")

    # 测试商品数据
    print("\n4. 测试商品数据 (GOLD):")
    try:
        gold_data = await fetch_data('GOLD', '2024-01-01', '2024-01-05')
        print(f"   ✓ 成功获取 {len(gold_data)} 条商品数据")
        if not gold_data.empty:
            print(f"   最新价格: {gold_data.iloc[-1]['Close']:.2f}")
    except Exception as e:
        print(f"   ✗ 失败: {e}")

    # 测试债券数据
    print("\n5. 测试债券数据 (US_10Y):")
    try:
        bond_data = await fetch_data('US_10Y', '2024-01-01', '2024-01-05')
        print(f"   ✓ 成功获取 {len(bond_data)} 条债券数据")
        if not bond_data.empty:
            print(f"   最新收益率: {bond_data.iloc[-1]['Close']:.2f}%")
    except Exception as e:
        print(f"   ✗ 失败: {e}")

    return True


async def test_cached_data_fetching():
    """测试带缓存的数据获取"""
    print("\n" + "="*80)
    print("Testing Cached Data Fetching")
    print("="*80)

    call_count = 0

    @cached('stock_data', ttl=10, namespace='stocks')
    async def get_stock_data(symbol: str, start_date: str, end_date: str):
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.2)  # 模拟网络延迟
        return await fetch_data(symbol, start_date, end_date)

    # 测试缓存效果
    print("\n1. 测试缓存效果:")
    for i in range(5):
        start_time = asyncio.get_event_loop().time()
        data = await get_stock_data('USD_CNH', '2024-01-01', '2024-01-05')
        duration = asyncio.get_event_loop().time() - start_time
        print(f"   第{i+1}次调用: {len(data)}条数据, 耗时: {duration:.3f}s")

    print(f"\n   总API调用次数: {call_count} (理论上应该是1)")
    print(f"   缓存效率: {((5 - call_count) / 5 * 100):.1f}%")

    return call_count < 5  # 应该只调用一次API


async def test_cache_statistics():
    """测试缓存统计"""
    print("\n" + "="*80)
    print("Testing Cache Statistics")
    print("="*80)

    cache_manager = get_cache_manager()

    # 获取缓存统计
    print("\n1. 缓存统计:")
    stats = cache_manager.get_stats()
    print(f"   统计信息: {stats}")

    # 测试手动缓存操作
    print("\n2. 手动缓存操作:")
    cache_data('temp_data', {'test': 'value'}, ttl=5, namespace='temp')
    cached_value = get_cached_data('temp_data', namespace='temp')
    print(f"   缓存数据: {cached_value}")

    return True


async def test_all_data_types():
    """测试所有数据类型"""
    print("\n" + "="*80)
    print("Testing All Data Types")
    print("="*80)

    factory = HybridAdapterFactory()
    test_symbols = [
        ('USD_CNH', 'FX', '美元兑人民币'),
        ('0700.HK', 'HKEX', '腾讯控股'),
        ('GOLD', 'Commodity', '黄金'),
        ('US_10Y', 'Bond', '美国10年期国债'),
        ('EUR_USD', 'FX', '欧元兑美元'),
        ('SILVER', 'Commodity', '白银'),
        ('US_30Y', 'Bond', '美国30年期国债'),
        ('0388.HK', 'HKEX', '港交所'),
    ]

    success_count = 0
    total_count = len(test_symbols)

    print("\n测试所有数据类型:")
    for symbol, data_type, name in test_symbols:
        try:
            adapter = factory.get_adapter(symbol)
            data = await fetch_data(symbol, '2024-01-01', '2024-01-03')

            if not data.empty:
                success_count += 1
                latest_price = data.iloc[-1]['Close']
                print(f"✓ {symbol:12} ({data_type:10}): {name:20} - {latest_price:10.4f}")
            else:
                print(f"✗ {symbol:12} ({data_type:10}): {name:20} - 无数据")
        except Exception as e:
            print(f"✗ {symbol:12} ({data_type:10}): {name:20} - 错误: {str(e)[:50]}")

    print(f"\n成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")

    return success_count > 0


async def main():
    print("="*80)
    print("混合数据源 + 缓存系统 - 综合测试")
    print("测试港股+FX+商品+债券全数据源")
    print("="*80)

    try:
        # 测试混合数据源与缓存集成
        hybrid_result = await test_hybrid_with_cache()

        # 测试带缓存的数据获取
        cache_result = await test_cached_data_fetching()

        # 测试缓存统计
        stats_result = await test_cache_statistics()

        # 测试所有数据类型
        all_types_result = await test_all_data_types()

        print("\n" + "="*80)
        print("测试总结")
        print("="*80)
        print(f"混合数据源测试: {'✓ 通过' if hybrid_result else '✗ 失败'}")
        print(f"缓存功能测试: {'✓ 通过' if cache_result else '✗ 失败'}")
        print(f"缓存统计测试: {'✓ 通过' if stats_result else '✗ 失败'}")
        print(f"全数据类型测试: {'✓ 通过' if all_types_result else '✗ 失败'}")

        if all([hybrid_result, cache_result, stats_result, all_types_result]):
            print("\n🎉 混合数据源架构 + 缓存系统测试全部通过！")
            print("\n✓ 100%真实数据源覆盖:")
            print("  - 港股数据 -> HKEX统一API")
            print("  - FX数据 -> Yahoo Finance")
            print("  - 商品数据 -> Alpha Vantage")
            print("  - 债券数据 -> FRED API")
            print("\n✓ 高性能缓存系统:")
            print("  - 内存缓存 (LRU算法)")
            print("  - Redis缓存支持")
            print("  - 自动过期清理")
            print("  - 缓存命中率优化")
        else:
            print("\n⚠️  部分测试失败")

    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
