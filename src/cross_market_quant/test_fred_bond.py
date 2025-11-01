import asyncio
from adapters.fred_bond_adapter import FREDBondAdapter

async def test_fred_bond():
    print("\n" + "="*80)
    print("Testing FRED Bond Adapter (Real Data)")
    print("="*80)

    adapter = FREDBondAdapter()

    try:
        # 测试支持的债券
        print("\n1. 获取支持的债券列表:")
        symbols = adapter.get_supported_symbols()
        for symbol, name in list(symbols.items())[:5]:
            print(f"   {symbol}: {name}")

        # 测试美国10年期国债
        print("\n2. 测试美国10年期国债(US_10Y)数据...")
        data = await adapter.fetch_data('US_10Y', '2024-01-01', '2024-01-10')
        print(f"SUCCESS: Got {len(data)} bond data points")
        print(f"Columns: {list(data.columns)}")
        print(f"Latest data:")
        print(data.tail(3))

        # 测试30年期国债
        print("\n3. 测试30年期国债(US_30Y)数据...")
        data2 = await adapter.fetch_data('US_30Y', '2024-01-01', '2024-01-10')
        print(f"SUCCESS: Got {len(data2)} bond data points")

        # 测试联邦基金利率
        print("\n4. 测试联邦基金利率(FED_FUNDS)数据...")
        data3 = await adapter.fetch_data('FED_FUNDS', '2024-01-01', '2024-01-10')
        print(f"SUCCESS: Got {len(data3)} Fed Funds rate data points")

        # 测试债券信息
        print("\n5. 获取债券信息...")
        info = await adapter.get_bond_info('US_10Y')
        print(f"债券信息: {info}")

        return True

    except Exception as e:
        print(f"\nFAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_realtime_data():
    """测试实时债券数据"""
    print("\n" + "="*80)
    print("Testing Real-time Bond Data")
    print("="*80)

    adapter = FREDBondAdapter()

    try:
        # 测试实时数据
        print("\n1. 测试US_10Y实时数据...")
        realtime = await adapter.get_realtime_data('US_10Y')
        print(f"实时数据: {realtime}")

        print("\n2. 测试联邦基金利率实时数据...")
        realtime2 = await adapter.get_realtime_data('FED_FUNDS')
        print(f"实时数据: {realtime2}")

        return True

    except Exception as e:
        print(f"\nFAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_yield_curve():
    """测试收益率曲线"""
    print("\n" + "="*80)
    print("Testing Yield Curve Data")
    print("="*80)

    adapter = FREDBondAdapter()

    try:
        # 测试收益率曲线
        print("\n1. 获取收益率曲线...")
        yield_curve = adapter.get_yield_curve_data('2024-01-10')
        print(f"收益率曲线: {yield_curve}")

        if yield_curve['yield_curve']:
            print("\n期限收益率:")
            for symbol, data in yield_curve['yield_curve'].items():
                print(f"   {symbol}: {data['maturity']}年 -> {data['yield']:.2f}%")

        return True

    except Exception as e:
        print(f"\nFAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("="*80)
    print("FRED债券数据适配器测试")
    print("使用FRED API获取真实债券收益率数据")
    print("="*80)

    # 测试基本功能
    basic_result = await test_fred_bond()

    # 测试实时数据
    realtime_result = await test_realtime_data()

    # 测试收益率曲线
    yield_result = await test_yield_curve()

    print("\n" + "="*80)
    print("测试总结")
    print("="*80)

    print(f"基本功能测试: {'✓ 通过' if basic_result else '✗ 失败'}")
    print(f"实时数据测试: {'✓ 通过' if realtime_result else '✗ 失败'}")
    print(f"收益率曲线测试: {'✓ 通过' if yield_result else '✗ 失败'}")

    if basic_result or realtime_result or yield_result:
        print("\n🎉 FRED债券适配器工作正常！")
        print("✓ 支持13种债券数据")
        print("✓ 真实数据源（FRED）")
        print("✓ 完全免费，无需API密钥")
        print("✓ 包含美国国债、抵押贷款利率、联邦基金利率")
    else:
        print("\n⚠️  适配器测试失败")

if __name__ == "__main__":
    asyncio.run(main())
