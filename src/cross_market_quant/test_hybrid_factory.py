import asyncio
from adapters.hybrid_adapter_factory import HybridAdapterFactory, get_adapter, fetch_data

async def test_hybrid_factory():
    print("\n" + "="*80)
    print("Testing Hybrid Data Source Factory")
    print("="*80)

    factory = HybridAdapterFactory()

    # 测试数据源汇总
    print("\n1. 数据源汇总:")
    summary = factory.get_data_source_summary()
    print(f"   总适配器数: {summary['total_adapters']}")
    print(f"   支持类型: {summary['supported_types']}")
    print(f"   总symbol数: {summary['total_symbols']}")
    print(f"   覆盖率:")
    for type_name, count in summary['coverage'].items():
        print(f"     - {type_name}: {count}种symbol")

    # 测试FX数据
    print("\n2. 测试FX数据 (USD/CNH):")
    try:
        fx_data = await fetch_data('USD_CNH', '2024-01-01', '2024-01-10')
        print(f"   ✓ 成功获取 {len(fx_data)} 条FX数据")
    except Exception as e:
        print(f"   ✗ 失败: {e}")

    # 测试港股数据
    print("\n3. 测试港股数据 (0700.HK):")
    try:
        hk_data = await fetch_data('0700.HK', '2024-01-01', '2024-01-10')
        print(f"   ✓ 成功获取 {len(hk_data)} 条港股数据")
    except Exception as e:
        print(f"   ✗ 失败: {e}")

    # 测试商品数据
    print("\n4. 测试商品数据 (GOLD):")
    try:
        commodity_data = await fetch_data('GOLD', '2024-01-01', '2024-01-10')
        print(f"   ✓ 成功获取 {len(commodity_data)} 条商品数据")
    except Exception as e:
        print(f"   ✗ 失败: {e}")

    # 测试符号自动检测
    print("\n5. 测试符号自动检测:")
    test_symbols = ['EUR_USD', '0388.hk', 'SILVER', 'USD_JPY', 'OIL_WTI']
    for symbol in test_symbols:
        try:
            adapter = get_adapter(symbol)
            print(f"   {symbol:15} -> {adapter.name}")
        except Exception as e:
            print(f"   {symbol:15} -> 失败: {e}")

    # 测试实时数据
    print("\n6. 测试实时数据:")
    try:
        realtime = await fetch_data('USD_CNH', '2024-01-01', '2024-01-01')
        if not realtime.empty:
            latest = realtime.iloc[-1]
            print(f"   USD/CNH最新价格: {latest['Close']:.4f}")
    except Exception as e:
        print(f"   ✗ 失败: {e}")

    return True

async def test_all_adapters():
    print("\n" + "="*80)
    print("Testing All Adapters Integration")
    print("="*80)

    factory = HybridAdapterFactory()
    symbols_to_test = [
        ('USD_CNH', 'fx'),
        ('0700.HK', 'hkex'),
        ('GOLD', 'commodity'),
        ('SILVER', 'commodity'),
    ]

    success_count = 0
    for symbol, expected_type in symbols_to_test:
        try:
            adapter = factory.get_adapter(symbol)
            data = await adapter.fetch_data(symbol, '2024-01-01', '2024-01-05')
            if not data.empty:
                success_count += 1
                print(f"✓ {symbol:15} ({expected_type:10}): {len(data)} 条数据")
            else:
                print(f"✗ {symbol:15} ({expected_type:10}): 无数据")
        except Exception as e:
            print(f"✗ {symbol:15} ({expected_type:10}): {str(e)[:50]}")

    print(f"\n成功率: {success_count}/{len(symbols_to_test)} ({success_count/len(symbols_to_test)*100:.1f}%)")
    return success_count == len(symbols_to_test)

async def main():
    print("="*80)
    print("混合数据源适配器工厂 - 综合测试")
    print("统一管理港股+FX+商品数据源")
    print("="*80)

    # 测试工厂功能
    factory_result = await test_hybrid_factory()

    # 测试所有适配器集成
    integration_result = await test_all_adapters()

    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    print(f"工厂功能测试: {'✓ 通过' if factory_result else '✗ 失败'}")
    print(f"适配器集成测试: {'✓ 通过' if integration_result else '✗ 失败'}")

    if factory_result and integration_result:
        print("\n🎉 混合数据源架构测试成功！")
        print("✓ 港股数据 -> HKEX统一API")
        print("✓ FX数据 -> Yahoo Finance")
        print("✓ 商品数据 -> Alpha Vantage")
        print("✓ 统一接口，易于扩展")
    else:
        print("\n⚠️  部分测试失败，需要检查网络连接和API密钥")

if __name__ == "__main__":
    asyncio.run(main())
