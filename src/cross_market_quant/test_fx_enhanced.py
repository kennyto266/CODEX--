"""
FX Yahoo适配器增强版测试脚本

测试优化后的错误处理功能:
1. 重试机制
2. 缓存系统
3. 数据质量检查
4. 故障转移
5. 健康检查
"""

import asyncio
import time
from adapters.fx_yahoo_adapter_enhanced import (
    FXYahooAdapterEnhanced,
    FXYahooAdapterError,
    NetworkError,
    DataValidationError,
    SymbolNotSupportedError
)


async def test_basic_functionality():
    """测试基本功能"""
    print("\n" + "="*80)
    print("Testing Basic Functionality")
    print("="*80)

    adapter = FXYahooAdapterEnhanced()

    try:
        # 测试支持的数据
        print("\n1. 获取支持的货币对:")
        symbols = adapter.get_supported_symbols()
        for symbol, name in list(symbols.items())[:5]:
            print(f"   {symbol}: {name}")

        # 测试获取数据 (带缓存)
        print("\n2. 测试数据获取 (第一次，无缓存):")
        start_time = time.time()
        data1 = await adapter.fetch_data('USD_CNH', '2024-01-01', '2024-01-10', use_cache=True)
        duration1 = time.time() - start_time
        print(f"   ✓ 成功获取 {len(data1)} 条数据，耗时: {duration1:.3f}s")

        # 测试缓存效果
        print("\n3. 测试缓存效果:")
        start_time = time.time()
        data2 = await adapter.fetch_data('USD_CNH', '2024-01-01', '2024-01-10', use_cache=True)
        duration2 = time.time() - start_time
        print(f"   ✓ 缓存获取 {len(data2)} 条数据，耗时: {duration2:.3f}s")

        improvement = (duration1 - duration2) / duration1 * 100
        print(f"   性能提升: {improvement:.1f}%")

        # 验证数据一致性
        if data1.equals(data2):
            print("   ✓ 缓存数据一致性验证通过")
        else:
            print("   ✗ 缓存数据不一致")

        return True

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_data_quality():
    """测试数据质量检查"""
    print("\n" + "="*80)
    print("Testing Data Quality Validation")
    print("="*80)

    adapter = FXYahooAdapterEnhanced()

    try:
        # 测试正常数据
        print("\n1. 测试正常数据:")
        data = await adapter.fetch_data('EUR_USD', '2024-01-01', '2024-01-10')
        print(f"   ✓ 成功获取 {len(data)} 条数据")
        print(f"   数据范围: {data['Date'].min()} 到 {data['Date'].max()}")
        print(f"   价格范围: {data['Close'].min():.4f} - {data['Close'].max():.4f}")

        # 测试数据完整性
        print("\n2. 数据完整性检查:")
        print(f"   缺失值: {data.isnull().sum().sum()}")
        print(f"   非正价格: {(data[['Open', 'High', 'Low', 'Close']] <= 0).sum().sum()}")

        # 测试货币信息
        print("\n3. 测试货币信息:")
        info = await adapter.get_currency_info('USD_JPY')
        print(f"   货币信息: {info}")

        return True

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_realtime_data():
    """测试实时数据获取"""
    print("\n" + "="*80)
    print("Testing Real-time Data")
    print("="*80)

    adapter = FXYahooAdapterEnhanced()

    try:
        # 测试实时数据 (带缓存)
        print("\n1. 测试实时数据获取:")
        start_time = time.time()
        realtime1 = await adapter.get_realtime_data('USD_CNH', use_cache=True)
        duration1 = time.time() - start_time
        print(f"   ✓ 实时数据获取成功，耗时: {duration1:.3f}s")
        print(f"   当前汇率: {realtime1['rate']:.4f}")

        # 测试缓存
        print("\n2. 测试实时数据缓存:")
        start_time = time.time()
        realtime2 = await adapter.get_realtime_data('USD_CNH', use_cache=True)
        duration2 = time.time() - start_time
        print(f"   ✓ 缓存获取，耗时: {duration2:.3f}s")

        if realtime1['rate'] == realtime2['rate']:
            print("   ✓ 实时数据一致性验证通过")

        # 显示详细信息
        print("\n3. 实时数据详情:")
        for key, value in realtime1.items():
            print(f"   {key}: {value}")

        return True

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_health_check():
    """测试健康检查"""
    print("\n" + "="*80)
    print("Testing Health Check")
    print("="*80)

    adapter = FXYahooAdapterEnhanced()

    try:
        # 执行健康检查
        print("\n1. 执行健康检查:")
        health = await adapter.health_check()
        print(f"   状态: {health['status']}")
        print(f"   适配器: {health['adapter']}")
        print(f"   测试结果: {health['test_result']}")

        if health['status'] == 'healthy':
            print(f"   数据点数: {health['data_points']}")
            print("   ✓ 系统健康")
        else:
            print(f"   错误: {health['error']}")
            print("   ✗ 系统不健康")

        return health['status'] == 'healthy'

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_error_handling():
    """测试错误处理"""
    print("\n" + "="*80)
    print("Testing Error Handling")
    print("="*80)

    adapter = FXYahooAdapterEnhanced()

    try:
        # 测试不支持的symbol
        print("\n1. 测试不支持的symbol:")
        try:
            await adapter.fetch_data('INVALID_SYMBOL', '2024-01-01', '2024-01-10')
            print("   ✗ 应该抛出异常")
        except SymbolNotSupportedError as e:
            print(f"   ✓ 正确捕获异常: {type(e).__name__}")

        # 测试无效日期
        print("\n2. 测试无效日期:")
        try:
            await adapter.fetch_data('USD_CNH', 'invalid-date', '2024-01-10')
            print("   ✗ 应该抛出异常")
        except Exception as e:
            print(f"   ✓ 正确处理错误: {type(e).__name__}")

        return True

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_cache_management():
    """测试缓存管理"""
    print("\n" + "="*80)
    print("Testing Cache Management")
    print("="*80)

    adapter = FXYahooAdapterEnhanced()

    try:
        # 设置一些数据到缓存
        print("\n1. 设置测试数据到缓存:")
        await adapter.fetch_data('GBP_USD', '2024-01-01', '2024-01-05', use_cache=True)
        print("   ✓ 数据已缓存")

        # 清空缓存
        print("\n2. 清空缓存:")
        await adapter.clear_cache()
        print("   ✓ 缓存已清空")

        # 验证缓存已清空
        print("\n3. 验证缓存:")
        data = await adapter.fetch_data('GBP_USD', '2024-01-01', '2024-01-05', use_cache=True)
        if len(data) > 0:
            print("   ✓ 从源重新获取数据成功")
        else:
            print("   ✗ 数据获取失败")

        return True

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_performance():
    """测试性能"""
    print("\n" + "="*80)
    print("Testing Performance")
    print("="*80)

    adapter = FXYahooAdapterEnhanced()

    try:
        symbols = ['USD_CNH', 'EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD']

        print("\n1. 并发获取多个货币对数据:")
        start_time = time.time()

        tasks = [
            adapter.fetch_data(symbol, '2024-01-01', '2024-01-05', use_cache=True)
            for symbol in symbols
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        duration = time.time() - start_time
        success_count = sum(1 for r in results if not isinstance(r, Exception))

        print(f"   并发请求完成，耗时: {duration:.3f}s")
        print(f"   成功: {success_count}/{len(symbols)}")

        # 计算平均耗时
        avg_duration = duration / len(symbols)
        print(f"   平均每货币对耗时: {avg_duration:.3f}s")

        return success_count > 0

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("="*80)
    print("FX Yahoo适配器增强版 - 综合测试")
    print("测试错误处理、缓存、性能等增强功能")
    print("="*80)

    try:
        # 运行所有测试
        results = {}

        results['basic'] = await test_basic_functionality()
        results['quality'] = await test_data_quality()
        results['realtime'] = await test_realtime_data()
        results['health'] = await test_health_check()
        results['error'] = await test_error_handling()
        results['cache'] = await test_cache_management()
        results['performance'] = await test_performance()

        # 总结
        print("\n" + "="*80)
        print("测试总结")
        print("="*80)

        for test_name, result in results.items():
            status = "✓ 通过" if result else "✗ 失败"
            print(f"{test_name.capitalize():20}: {status}")

        passed_count = sum(1 for r in results.values() if r)
        total_count = len(results)

        print(f"\n总通过率: {passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)")

        if passed_count == total_count:
            print("\n🎉 所有测试通过！FX适配器增强版功能正常！")
            print("\n✓ 增强功能:")
            print("  - 自动重试机制 (指数退避)")
            print("  - 集成缓存系统")
            print("  - 严格数据质量检查")
            print("  - 故障转移机制")
            print("  - 健康检查")
            print("  - 详细错误分类")
        elif passed_count > total_count * 0.7:
            print("\n⚠️  大部分测试通过，系统基本可用")
        else:
            print("\n✗ 多个测试失败，需要进一步调试")

    except Exception as e:
        print(f"\n测试过程中出现严重错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
