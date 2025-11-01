import asyncio
from adapters.fx_yahoo_adapter import FXYahooAdapter
from adapters.hkex_adapter import HKEXAdapter

async def test_fx_yahoo():
    print("Testing Yahoo Finance FX Adapter...")
    adapter = FXYahooAdapter()

    try:
        # 测试USD/CNH数据
        print("\n1. 测试USD_CNH数据...")
        data = await adapter.fetch_data('USD_CNH', '2024-01-01', '2024-01-10')
        print(f"✓ 成功获取 {len(data)} 条FX数据")
        print(f"数据列: {list(data.columns)}")
        print(f"最新3条记录:")
        print(data.tail(3))

        # 测试其他FX对
        print("\n2. 测试EUR_USD数据...")
        data2 = await adapter.fetch_data('EUR_USD', '2024-01-01', '2024-01-10')
        print(f"✓ 成功获取 {len(data2)} 条EUR/USD数据")

        # 测试货币信息
        print("\n3. 获取货币信息...")
        info = adapter.get_currency_info('USD_CNH')
        print(f"货币信息: {info}")

        return True

    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_hkex_real():
    print("\n" + "="*80)
    print("Testing HKEX Adapter with Real Data...")
    adapter = HKEXAdapter()

    try:
        # 测试港股数据
        print("\n1. 测试0700.HK数据...")
        data = await adapter.fetch_data('0700.HK', '2024-01-01', '2024-01-10')
        print(f"✓ 成功获取 {len(data)} 条港股数据")
        print(f"数据列: {list(data.columns)}")
        print(f"最新3条记录:")
        print(data.tail(3))

        return True

    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("="*80)
    print("跨市场量化系统 - 真实数据源测试 (优化版)")
    print("使用混合数据源架构")
    print("="*80)

    # 测试FX数据（Yahoo Finance）
    fx_result = await test_fx_yahoo()

    # 测试港股数据（统一API）
    hkex_result = await test_hkex_real()

    # 输出总结
    print("\n" + "="*80)
    print("测试结果总结")
    print("="*80)

    print(f"Yahoo Finance FX Adapter: {'✓ 通过' if fx_result else '✗ 失败'}")
    print(f"HKEX Adapter (Real API):   {'✓ 通过' if hkex_result else '✗ 失败'}")

    if fx_result and hkex_result:
        print("\n🎉 所有测试通过！")
        print("✅ 成功实现混合数据源架构")
        print("✅ 港股数据：统一API端点")
        print("✅ FX数据：Yahoo Finance")
        print("✅ 系统现在使用真实数据源！")
    else:
        print("\n⚠️  部分测试失败，需要进一步优化")

if __name__ == "__main__":
    asyncio.run(main())
