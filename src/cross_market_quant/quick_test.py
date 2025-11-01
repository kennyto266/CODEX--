import asyncio
from adapters.fx_adapter import FXAdapter
from adapters.hkex_adapter import HKEXAdapter

async def test_fx():
    print("Testing FX Adapter...")
    adapter = FXAdapter()
    try:
        data = await adapter.fetch_data('usd_cnh', '2024-01-01', '2024-01-10')
        print(f"✓ 成功获取 {len(data)} 条FX数据")
        print(f"Columns: {list(data.columns)}")
        print(f"Latest data:")
        print(data.tail(3))
        return True
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_hkex():
    print("\nTesting HKEX Adapter...")
    adapter = HKEXAdapter()
    try:
        data = await adapter.fetch_data('0700.HK', '2024-01-01', '2024-01-10')
        print(f"✓ 成功获取 {len(data)} 条HKEX数据")
        print(f"Columns: {list(data.columns)}")
        print(f"Latest data:")
        print(data.tail(3))
        return True
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("="*80)
    print("Quick Test - Real Data Fetching")
    print("="*80)

    fx_result = await test_fx()
    hkex_result = await test_hkex()

    print("\n" + "="*80)
    print("Results:")
    print(f"FX Adapter: {'✓ PASS' if fx_result else '✗ FAIL'}")
    print(f"HKEX Adapter: {'✓ PASS' if hkex_result else '✗ FAIL'}")

    if fx_result and hkex_result:
        print("\n🎉 All tests passed! System uses real data!")
    else:
        print("\n⚠️  Some tests failed, need optimization")

if __name__ == "__main__":
    asyncio.run(main())
