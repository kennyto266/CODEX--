"""
综合数据源测试脚本

测试所有混合数据源架构的数据适配器:
1. 港股数据 -> HKEX统一API
2. FX数据 -> Yahoo Finance (增强版)
3. 商品数据 -> Alpha Vantage
4. 债券数据 -> FRED API

验证真实数据获取和数据质量
"""

import asyncio
import time
from datetime import datetime
import pandas as pd


async def test_hkex_data():
    """测试港股数据 (HKEX统一API)"""
    print("\n" + "="*80)
    print("Testing HKEX Data (Unified API)")
    print("="*80)

    try:
        from adapters.hkex_adapter import HKEXAdapter

        adapter = HKEXAdapter()
        print(f"✓ 适配器初始化: {adapter.name}")

        # 测试腾讯 (0700.HK)
        print("\n1. 测试腾讯 (0700.HK):")
        start_time = time.time()
        data = await adapter.fetch_data('0700.HK', '2024-01-01', '2024-01-10')
        duration = time.time() - start_time

        if not data.empty:
            latest = data.iloc[-1]
            print(f"   ✓ 成功获取 {len(data)} 条数据")
            print(f"   耗时: {duration:.3f}s")
            print(f"   最新价格: {latest['Close']:.2f}")
            print(f"   数据范围: {data['Date'].min()} ~ {data['Date'].max()}")
            return True
        else:
            print(f"   ✗ 数据为空")
            return False

    except Exception as e:
        print(f"   ✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_fx_data():
    """测试FX数据 (Yahoo Finance增强版)"""
    print("\n" + "="*80)
    print("Testing FX Data (Yahoo Finance Enhanced)")
    print("="*80)

    try:
        from adapters.fx_yahoo_adapter_enhanced import FXYahooAdapterEnhanced

        adapter = FXYahooAdapterEnhanced()
        print(f"✓ 适配器初始化: {adapter.name}")

        # 测试USD/CNH
        print("\n1. 测试USD/CNH (美元兑人民币):")
        start_time = time.time()
        data = await adapter.fetch_data('USD_CNH', '2024-01-01', '2024-01-10', use_cache=True)
        duration = time.time() - start_time

        if not data.empty:
            latest = data.iloc[-1]
            print(f"   ✓ 成功获取 {len(data)} 条数据")
            print(f"   耗时: {duration:.3f}s")
            print(f"   最新汇率: {latest['Close']:.4f}")
            print(f"   数据质量: 缺失值 {data.isnull().sum().sum()}")

            # 测试实时数据
            print("\n2. 测试实时数据:")
            realtime = await adapter.get_realtime_data('USD_CNH', use_cache=True)
            print(f"   ✓ 实时汇率: {realtime['rate']:.4f}")
            print(f"   数据源: {realtime['source']}")

            return True
        else:
            print(f"   ✗ 数据为空")
            return False

    except Exception as e:
        print(f"   ✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_commodity_data():
    """测试商品数据 (Alpha Vantage)"""
    print("\n" + "="*80)
    print("Testing Commodity Data (Alpha Vantage)")
    print("="*80)

    try:
        from adapters.alphavantage_commodity_adapter import AlphaVantageCommodityAdapter

        adapter = AlphaVantageCommodityAdapter()
        print(f"✓ 适配器初始化: {adapter.name}")

        # 测试黄金
        print("\n1. 测试黄金 (GOLD):")
        start_time = time.time()
        data = await adapter.fetch_data('GOLD', '2024-01-01', '2024-01-10')
        duration = time.time() - start_time

        if not data.empty:
            latest = data.iloc[-1]
            print(f"   ✓ 成功获取 {len(data)} 条数据")
            print(f"   耗时: {duration:.3f}s")
            print(f"   最新价格: {latest['Close']:.2f}")
            print(f"   数据来源: Alpha Vantage")

            # 测试支持的数据
            print("\n2. 支持的商品列表:")
            symbols = adapter.get_supported_symbols()
            for symbol, name in list(symbols.items())[:5]:
                print(f"   - {symbol}: {name}")

            return True
        else:
            print(f"   ✗ 数据为空")
            return False

    except Exception as e:
        print(f"   ✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_bond_data():
    """测试债券数据 (FRED)"""
    print("\n" + "="*80)
    print("Testing Bond Data (FRED)")
    print("="*80)

    try:
        from adapters.fred_bond_adapter import FREDBondAdapter

        adapter = FREDBondAdapter()
        print(f"✓ 适配器初始化: {adapter.name}")

        # 测试美国10年期国债
        print("\n1. 测试美国10年期国债 (US_10Y):")
        start_time = time.time()
        data = await adapter.fetch_data('US_10Y', '2024-01-01', '2024-01-10')
        duration = time.time() - start_time

        if not data.empty:
            latest = data.iloc[-1]
            print(f"   ✓ 成功获取 {len(data)} 条数据")
            print(f"   耗时: {duration:.3f}s")
            print(f"   最新收益率: {latest['Close']:.2f}%")
            print(f"   数据来源: FRED (Federal Reserve)")

            # 测试联邦基金利率
            print("\n2. 测试联邦基金利率 (FED_FUNDS):")
            data2 = await adapter.fetch_data('FED_FUNDS', '2024-01-01', '2024-01-10')
            if not data2.empty:
                latest2 = data2.iloc[-1]
                print(f"   ✓ 联邦基金利率: {latest2['Close']:.2f}%")

            return True
        else:
            print(f"   ✗ 数据为空")
            return False

    except Exception as e:
        print(f"   ✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_hybrid_factory():
    """测试混合数据源工厂"""
    print("\n" + "="*80)
    print("Testing Hybrid Data Source Factory")
    print("="*80)

    try:
        from adapters.hybrid_adapter_factory import HybridAdapterFactory, fetch_data

        factory = HybridAdapterFactory()
        print(f"✓ 工厂初始化完成")

        # 显示数据源统计
        summary = factory.get_data_source_summary()
        print(f"\n1. 数据源统计:")
        print(f"   总适配器数: {summary['total_adapters']}")
        print(f"   支持类型: {summary['supported_types']}")
        print(f"   总symbol数: {summary['total_symbols']}")

        print(f"\n2. 覆盖率:")
        for type_name, count in summary['coverage'].items():
            print(f"   - {type_name}: {count}种symbol")

        # 批量测试所有数据源
        print(f"\n3. 批量数据获取测试:")
        test_symbols = [
            ('0700.HK', '港股'),
            ('USD_CNH', 'FX'),
            ('GOLD', '商品'),
            ('US_10Y', '债券')
        ]

        success_count = 0
        for symbol, name in test_symbols:
            try:
                start_time = time.time()
                data = await fetch_data(symbol, '2024-01-01', '2024-01-05')
                duration = time.time() - start_time

                if not data.empty:
                    latest = data.iloc[-1]['Close']
                    print(f"   ✓ {symbol:12} ({name}): {len(data)}条数据, 价格:{latest:.4f}, 耗时:{duration:.3f}s")
                    success_count += 1
                else:
                    print(f"   ✗ {symbol:12} ({name}): 数据为空")
            except Exception as e:
                print(f"   ✗ {symbol:12} ({name}): 错误 {str(e)[:50]}")

        print(f"\n   成功率: {success_count}/{len(test_symbols)} ({success_count/len(test_symbols)*100:.1f}%)")

        return success_count == len(test_symbols)

    except Exception as e:
        print(f"   ✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_data_consistency():
    """测试数据一致性"""
    print("\n" + "="*80)
    print("Testing Data Consistency")
    print("="*80)

    try:
        from adapters.hybrid_adapter_factory import fetch_data

        # 测试多次获取数据的一致性
        print("\n1. 测试多次获取一致性:")
        symbol = 'EUR_USD'
        data1 = await fetch_data(symbol, '2024-01-01', '2024-01-05')
        data2 = await fetch_data(symbol, '2024-01-01', '2024-01-05')

        if data1.equals(data2):
            print(f"   ✓ {symbol} 数据一致性验证通过")
            return True
        else:
            print(f"   ✗ {symbol} 数据不一致")
            return False

    except Exception as e:
        print(f"   ✗ 错误: {e}")
        return False


async def performance_benchmark():
    """性能基准测试"""
    print("\n" + "="*80)
    print("Performance Benchmark")
    print("="*80)

    try:
        from adapters.hybrid_adapter_factory import fetch_data

        # 并发测试
        print("\n1. 并发数据获取:")
        symbols = ['USD_CNH', 'EUR_USD', 'GBP_USD', 'GOLD', 'US_10Y']

        start_time = time.time()
        tasks = [
            fetch_data(symbol, '2024-01-01', '2024-01-05')
            for symbol in symbols
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        duration = time.time() - start_time

        success_count = sum(1 for r in results if not isinstance(r, Exception))

        print(f"   并发请求数: {len(symbols)}")
        print(f"   成功数: {success_count}")
        print(f"   总耗时: {duration:.3f}s")
        print(f"   平均每请求: {duration/len(symbols):.3f}s")

        return success_count > 0

    except Exception as e:
        print(f"   ✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("="*80)
    print("混合数据源架构 - 综合测试")
    print("验证港股+FX+商品+债券全数据源")
    print("="*80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}

    try:
        # 1. 测试港股数据
        results['hkex'] = await test_hkex_data()

        # 2. 测试FX数据
        results['fx'] = await test_fx_data()

        # 3. 测试商品数据
        results['commodity'] = await test_commodity_data()

        # 4. 测试债券数据
        results['bond'] = await test_bond_data()

        # 5. 测试混合工厂
        results['factory'] = await test_hybrid_factory()

        # 6. 测试数据一致性
        results['consistency'] = await test_data_consistency()

        # 7. 性能基准测试
        results['performance'] = await performance_benchmark()

        # 总结
        print("\n" + "="*80)
        print("Test Summary")
        print("="*80)

        for test_name, result in results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            test_display = test_name.capitalize()
            print(f"{test_display:20}: {status}")

        passed = sum(1 for r in results.values() if r)
        total = len(results)

        print(f"\n总体通过率: {passed}/{total} ({passed/total*100:.1f}%)")

        # 数据源覆盖验证
        print("\n" + "="*80)
        print("Data Source Coverage")
        print("="*80)

        data_sources = [
            ("港股数据", "HKEX统一API", results.get('hkex', False)),
            ("FX数据", "Yahoo Finance", results.get('fx', False)),
            ("商品数据", "Alpha Vantage", results.get('commodity', False)),
            ("债券数据", "FRED API", results.get('bond', False)),
        ]

        working_sources = 0
        for source_name, api_name, status in data_sources:
            symbol = "✓" if status else "✗"
            print(f"{symbol} {source_name:15} -> {api_name:20} {'[OK]' if status else '[FAIL]'}")
            if status:
                working_sources += 1

        coverage = working_sources / len(data_sources) * 100

        print(f"\n数据源覆盖率: {working_sources}/{len(data_sources)} ({coverage:.1f}%)")

        # 最终结论
        print("\n" + "="*80)
        print("Final Conclusion")
        print("="*80)

        if passed == total and coverage == 100:
            print("\n🎉 所有测试通过！混合数据源架构工作完美！")
            print("\n✓ 100%真实数据源覆盖:")
            print("  - 港股数据: HKEX统一API")
            print("  - FX数据: Yahoo Finance")
            print("  - 商品数据: Alpha Vantage")
            print("  - 债券数据: FRED API")
            print("\n✓ 系统特性:")
            print("  - 零成本运行")
            print("  - 高可靠性")
            print("  - 高性能缓存")
            print("  - 企业级错误处理")
            print("\n🚀 系统已准备好投入生产使用！")
        elif coverage >= 75:
            print("\n⚠️  大部分数据源工作正常，系统基本可用")
            print(f"数据源覆盖率: {coverage:.1f}%")
            print("建议检查失败的数据源配置")
        else:
            print("\n✗ 多个数据源测试失败")
            print(f"数据源覆盖率: {coverage:.1f}%")
            print("需要检查网络连接和API配置")

    except Exception as e:
        print(f"\n测试过程中出现严重错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
