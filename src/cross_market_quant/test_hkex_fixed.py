"""
测试修复版HKEX适配器
验证API响应解析是否正常工作
"""

import asyncio
from adapters.hkex_adapter_fixed import HKEXAdapterFixed


async def test_hkex_fixed():
    """测试修复版HKEX适配器"""
    print("\n" + "="*80)
    print("Testing Fixed HKEX Adapter")
    print("="*80)

    adapter = HKEXAdapterFixed()
    print(f"Adapter initialized: {adapter.name}")

    try:
        # 测试腾讯 (0700.HK)
        print("\n1. Testing Tencent (0700.HK):")
        data = await adapter.fetch_data('0700.HK', '2024-01-01', '2024-01-10')

        if not data.empty:
            latest = data.iloc[-1]
            print(f"   [OK] Successfully retrieved {len(data)} data points")
            print(f"   Latest price: {latest['Close']:.2f}")
            print(f"   Date range: {data['Date'].min()} to {data['Date'].max()}")
            print(f"   Columns: {list(data.columns)}")
            print(f"\n   Sample data:")
            print(data.head(3).to_string(index=False))

            return True
        else:
            print(f"   [FAIL] Data is empty")
            return False

    except Exception as e:
        print(f"   [FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_multiple_stocks():
    """测试多只股票"""
    print("\n" + "="*80)
    print("Testing Multiple Stocks")
    print("="*80)

    adapter = HKEXAdapterFixed()
    test_symbols = ['0700.HK', '0388.HK', '1398.HK', '0939.HK']

    success_count = 0
    for symbol in test_symbols:
        try:
            data = await adapter.fetch_data(symbol, '2024-01-01', '2024-01-05')

            if not data.empty:
                latest = data.iloc[-1]
                name = adapter.SUPPORTED_SYMBOLS.get(symbol, 'Unknown')
                print(f"   [OK] {symbol:12} ({name:15}): {len(data)} data, Price: {latest['Close']:.2f}")
                success_count += 1
            else:
                print(f"   [FAIL] {symbol}: Empty data")
        except Exception as e:
            print(f"   [FAIL] {symbol}: {str(e)[:60]}")

    print(f"\n   Success rate: {success_count}/{len(test_symbols)} ({success_count/len(test_symbols)*100:.1f}%)")
    return success_count > 0


async def test_realtime_data():
    """测试实时数据"""
    print("\n" + "="*80)
    print("Testing Realtime Data")
    print("="*80)

    adapter = HKEXAdapterFixed()

    try:
        print("\n1. Testing realtime data for 0700.HK:")
        realtime = await adapter.get_realtime_data('0700.HK')

        if realtime:
            print(f"   [OK] Symbol: {realtime['symbol']}")
            print(f"   [OK] Price: {realtime['price']:.2f}")
            print(f"   [OK] Source: {realtime['source']}")
            print(f"   [OK] Timestamp: {realtime['timestamp']}")

            return True
        else:
            print(f"   [FAIL] No realtime data")
            return False

    except Exception as e:
        print(f"   [FAIL] Error: {e}")
        return False


async def test_health_check():
    """测试健康检查"""
    print("\n" + "="*80)
    print("Testing Health Check")
    print("="*80)

    adapter = HKEXAdapterFixed()

    try:
        print("\n1. Running health check:")
        health = await adapter.health_check()

        print(f"   Status: {health['status']}")
        print(f"   Adapter: {health['adapter']}")
        print(f"   Test result: {health['test_result']}")

        if health['status'] == 'healthy':
            print(f"   Data points: {health['data_points']}")
            print(f"   [OK] System is healthy")
            return True
        else:
            print(f"   Error: {health.get('error', 'Unknown')}")
            print(f"   [FAIL] System is unhealthy")
            return False

    except Exception as e:
        print(f"   [FAIL] Error: {e}")
        return False


async def main():
    print("="*80)
    print("HKEX Adapter Fix Verification")
    print("="*80)

    results = {}

    try:
        # 1. 测试基本功能
        results['basic'] = await test_hkex_fixed()

        # 2. 测试多只股票
        results['multiple'] = await test_multiple_stocks()

        # 3. 测试实时数据
        results['realtime'] = await test_realtime_data()

        # 4. 测试健康检查
        results['health'] = await test_health_check()

        # 总结
        print("\n" + "="*80)
        print("Test Summary")
        print("="*80)

        for test_name, result in results.items():
            status = "[PASS]" if result else "[FAIL]"
            print(f"{test_name.capitalize():15}: {status}")

        passed = sum(1 for r in results.values() if r)
        total = len(results)

        print(f"\nOverall pass rate: {passed}/{total} ({passed/total*100:.1f}%)")

        if passed == total:
            print("\n[SUCCESS] All tests passed! HKEX adapter is working correctly!")
            print("\n[OK] Fixed issues:")
            print("  - API response parsing")
            print("  - Data format conversion")
            print("  - Error handling")
            print("  - Real data acquisition")
        else:
            print("\n[WARNING] Some tests failed")

    except Exception as e:
        print(f"\n[ERROR] Serious error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
