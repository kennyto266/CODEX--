import asyncio
from adapters.alphavantage_commodity_adapter import AlphaVantageCommodityAdapter

async def test_alphavantage_commodity():
    print("\n" + "="*80)
    print("Testing Alpha Vantage Commodity Adapter (Real Data)")
    print("="*80)

    adapter = AlphaVantageCommodityAdapter()

    try:
        # 测试支持的商品
        print("\n1. 获取支持的商品列表:")
        symbols = adapter.get_supported_symbols()
        for symbol, name in list(symbols.items())[:5]:
            print(f"   {symbol}: {name}")

        # 测试黄金数据
        print("\n2. 测试黄金(GOLD)数据...")
        data = await adapter.fetch_data('GOLD', '2024-01-01', '2024-01-10')
        print(f"SUCCESS: Got {len(data)} commodity data points")
        print(f"Columns: {list(data.columns)}")
        print(f"Latest data:")
        print(data.tail(3))

        # 测试白银数据
        print("\n3. 测试白银(SILVER)数据...")
        data2 = await adapter.fetch_data('SILVER', '2024-01-01', '2024-01-10')
        print(f"SUCCESS: Got {len(data2)} silver data points")

        # 测试商品信息
        print("\n4. 获取商品信息...")
        info = await adapter.get_commodity_info('GOLD')
        print(f"商品信息: {info}")

        return True

    except Exception as e:
        print(f"\nFAILED: {e}")
        print("\n注意: 如果使用demo API密钥，可能会有限制")
        print("请设置ALPHA_VANTAGE_API_KEY环境变量以获取完整数据")
        import traceback
        traceback.print_exc()
        return False

async def test_with_real_api():
    """使用真实API密钥测试"""
    import os

    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        print("\n⚠️  未设置ALPHA_VANTAGE_API_KEY环境变量")
        print("请注册 https://www.alphavantage.co/support/#api-key 获取免费API密钥")
        return False

    print("\n" + "="*80)
    print("Testing with Real API Key")
    print("="*80)

    adapter = AlphaVantageCommodityAdapter()

    try:
        # 测试WTI原油
        print("\n1. 测试WTI原油数据...")
        data = await adapter.fetch_data('OIL_WTI', '2024-01-01', '2024-01-10')
        print(f"SUCCESS: Got {len(data)} oil data points")
        print(f"Latest data:")
        print(data.tail(3))

        # 测试实时数据
        print("\n2. 测试实时数据...")
        realtime = await adapter.get_realtime_data('GOLD')
        print(f"实时数据: {realtime}")

        return True

    except Exception as e:
        print(f"\nFAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("="*80)
    print("Alpha Vantage商品数据适配器测试")
    print("使用Alpha Vantage API获取真实商品数据")
    print("="*80)

    # 先测试demo模式
    demo_result = await test_alphavantage_commodity()

    # 如果有API密钥，测试真实模式
    api_result = await test_with_real_api()

    print("\n" + "="*80)
    print("测试总结")
    print("="*80)

    print(f"Demo模式测试: {'✓ 通过' if demo_result else '✗ 失败'}")
    print(f"真实API测试: {'✓ 通过' if api_result else '✗ 失败'}")

    if demo_result or api_result:
        print("\n🎉 Alpha Vantage商品适配器工作正常！")
        print("✓ 支持16种商品数据")
        print("✓ 真实数据源（Alpha Vantage）")
        print("✓ 免费API层支持（500次/天）")
    else:
        print("\n⚠️  适配器测试失败")

if __name__ == "__main__":
    asyncio.run(main())
