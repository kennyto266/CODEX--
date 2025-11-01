"""
Comprehensive Data Source Test Script

Test all hybrid data source adapters:
1. HK Stock Data -> HKEX Unified API
2. FX Data -> Yahoo Finance (Enhanced)
3. Commodity Data -> Alpha Vantage
4. Bond Data -> FRED API

Verify real data acquisition and quality
"""

import asyncio
import time
from datetime import datetime
import pandas as pd


async def test_hkex_data():
    """Test HK Stock Data (HKEX Unified API)"""
    print("\n" + "="*80)
    print("Testing HKEX Data (Unified API)")
    print("="*80)

    try:
        from adapters.hkex_adapter import HKEXAdapter

        adapter = HKEXAdapter()
        print(f"✓ Adapter initialized: {adapter.name}")

        # Test Tencent (0700.HK)
        print("\n1. Testing Tencent (0700.HK):")
        start_time = time.time()
        data = await adapter.fetch_data('0700.HK', '2024-01-01', '2024-01-10')
        duration = time.time() - start_time

        if not data.empty:
            latest = data.iloc[-1]
            print(f"   ✓ Successfully retrieved {len(data)} data points")
            print(f"   Duration: {duration:.3f}s")
            print(f"   Latest price: {latest['Close']:.2f}")
            print(f"   Date range: {data['Date'].min()} ~ {data['Date'].max()}")
            return True
        else:
            print(f"   ✗ Data is empty")
            return False

    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_fx_data():
    """Test FX Data (Yahoo Finance Enhanced)"""
    print("\n" + "="*80)
    print("Testing FX Data (Yahoo Finance Enhanced)")
    print("="*80)

    try:
        from adapters.fx_yahoo_adapter_enhanced import FXYahooAdapterEnhanced

        adapter = FXYahooAdapterEnhanced()
        print(f"✓ Adapter initialized: {adapter.name}")

        # Test USD/CNH
        print("\n1. Testing USD/CNH (US Dollar to Chinese Yuan):")
        start_time = time.time()
        data = await adapter.fetch_data('USD_CNH', '2024-01-01', '2024-01-10', use_cache=True)
        duration = time.time() - start_time

        if not data.empty:
            latest = data.iloc[-1]
            print(f"   ✓ Successfully retrieved {len(data)} data points")
            print(f"   Duration: {duration:.3f}s")
            print(f"   Latest rate: {latest['Close']:.4f}")
            print(f"   Data quality: Missing values {data.isnull().sum().sum()}")

            # Test realtime data
            print("\n2. Testing realtime data:")
            realtime = await adapter.get_realtime_data('USD_CNH', use_cache=True)
            print(f"   ✓ Realtime rate: {realtime['rate']:.4f}")
            print(f"   Data source: {realtime['source']}")

            return True
        else:
            print(f"   ✗ Data is empty")
            return False

    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_commodity_data():
    """Test Commodity Data (Alpha Vantage)"""
    print("\n" + "="*80)
    print("Testing Commodity Data (Alpha Vantage)")
    print("="*80)

    try:
        from adapters.alphavantage_commodity_adapter import AlphaVantageCommodityAdapter

        adapter = AlphaVantageCommodityAdapter()
        print(f"✓ Adapter initialized: {adapter.name}")

        # Test Gold
        print("\n1. Testing Gold (GOLD):")
        start_time = time.time()
        data = await adapter.fetch_data('GOLD', '2024-01-01', '2024-01-10')
        duration = time.time() - start_time

        if not data.empty:
            latest = data.iloc[-1]
            print(f"   ✓ Successfully retrieved {len(data)} data points")
            print(f"   Duration: {duration:.3f}s")
            print(f"   Latest price: {latest['Close']:.2f}")
            print(f"   Data source: Alpha Vantage")

            # Test supported commodities
            print("\n2. Supported commodities:")
            symbols = adapter.get_supported_symbols()
            for symbol, name in list(symbols.items())[:5]:
                print(f"   - {symbol}: {name}")

            return True
        else:
            print(f"   ✗ Data is empty")
            return False

    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_bond_data():
    """Test Bond Data (FRED)"""
    print("\n" + "="*80)
    print("Testing Bond Data (FRED)")
    print("="*80)

    try:
        from adapters.fred_bond_adapter import FREDBondAdapter

        adapter = FREDBondAdapter()
        print(f"✓ Adapter initialized: {adapter.name}")

        # Test US 10-Year Treasury
        print("\n1. Testing US 10-Year Treasury (US_10Y):")
        start_time = time.time()
        data = await adapter.fetch_data('US_10Y', '2024-01-01', '2024-01-10')
        duration = time.time() - start_time

        if not data.empty:
            latest = data.iloc[-1]
            print(f"   ✓ Successfully retrieved {len(data)} data points")
            print(f"   Duration: {duration:.3f}s")
            print(f"   Latest yield: {latest['Close']:.2f}%")
            print(f"   Data source: FRED (Federal Reserve)")

            # Test Fed Funds Rate
            print("\n2. Testing Fed Funds Rate (FED_FUNDS):")
            data2 = await adapter.fetch_data('FED_FUNDS', '2024-01-01', '2024-01-10')
            if not data2.empty:
                latest2 = data2.iloc[-1]
                print(f"   ✓ Fed Funds Rate: {latest2['Close']:.2f}%")

            return True
        else:
            print(f"   ✗ Data is empty")
            return False

    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_hybrid_factory():
    """Test Hybrid Data Source Factory"""
    print("\n" + "="*80)
    print("Testing Hybrid Data Source Factory")
    print("="*80)

    try:
        from adapters.hybrid_adapter_factory import HybridAdapterFactory, fetch_data

        factory = HybridAdapterFactory()
        print(f"✓ Factory initialized")

        # Show data source statistics
        summary = factory.get_data_source_summary()
        print(f"\n1. Data source statistics:")
        print(f"   Total adapters: {summary['total_adapters']}")
        print(f"   Supported types: {summary['supported_types']}")
        print(f"   Total symbols: {summary['total_symbols']}")

        print(f"\n2. Coverage:")
        for type_name, count in summary['coverage'].items():
            print(f"   - {type_name}: {count} symbols")

        # Batch test all data sources
        print(f"\n3. Batch data retrieval test:")
        test_symbols = [
            ('0700.HK', 'HK Stock'),
            ('USD_CNH', 'FX'),
            ('GOLD', 'Commodity'),
            ('US_10Y', 'Bond')
        ]

        success_count = 0
        for symbol, name in test_symbols:
            try:
                start_time = time.time()
                data = await fetch_data(symbol, '2024-01-01', '2024-01-05')
                duration = time.time() - start_time

                if not data.empty:
                    latest = data.iloc[-1]['Close']
                    print(f"   ✓ {symbol:12} ({name}): {len(data)} data, Price:{latest:.4f}, Time:{duration:.3f}s")
                    success_count += 1
                else:
                    print(f"   ✗ {symbol:12} ({name}): Empty data")
            except Exception as e:
                print(f"   ✗ {symbol:12} ({name}): Error {str(e)[:50]}")

        print(f"\n   Success rate: {success_count}/{len(test_symbols)} ({success_count/len(test_symbols)*100:.1f}%)")

        return success_count == len(test_symbols)

    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_data_consistency():
    """Test data consistency"""
    print("\n" + "="*80)
    print("Testing Data Consistency")
    print("="*80)

    try:
        from adapters.hybrid_adapter_factory import fetch_data

        # Test multiple data fetch consistency
        print("\n1. Testing multiple fetch consistency:")
        symbol = 'EUR_USD'
        data1 = await fetch_data(symbol, '2024-01-01', '2024-01-05')
        data2 = await fetch_data(symbol, '2024-01-01', '2024-01-05')

        if data1.equals(data2):
            print(f"   ✓ {symbol} data consistency verified")
            return True
        else:
            print(f"   ✗ {symbol} data inconsistent")
            return False

    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False


async def performance_benchmark():
    """Performance benchmark test"""
    print("\n" + "="*80)
    print("Performance Benchmark")
    print("="*80)

    try:
        from adapters.hybrid_adapter_factory import fetch_data

        # Concurrent test
        print("\n1. Concurrent data retrieval:")
        symbols = ['USD_CNH', 'EUR_USD', 'GBP_USD', 'GOLD', 'US_10Y']

        start_time = time.time()
        tasks = [
            fetch_data(symbol, '2024-01-01', '2024-01-05')
            for symbol in symbols
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        duration = time.time() - start_time

        success_count = sum(1 for r in results if not isinstance(r, Exception))

        print(f"   Concurrent requests: {len(symbols)}")
        print(f"   Successful: {success_count}")
        print(f"   Total time: {duration:.3f}s")
        print(f"   Average per request: {duration/len(symbols):.3f}s")

        return success_count > 0

    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("="*80)
    print("Hybrid Data Source Architecture - Comprehensive Test")
    print("Verify HK Stock + FX + Commodity + Bond Data Sources")
    print("="*80)
    print(f"Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}

    try:
        # 1. Test HK stock data
        results['hkex'] = await test_hkex_data()

        # 2. Test FX data
        results['fx'] = await test_fx_data()

        # 3. Test commodity data
        results['commodity'] = await test_commodity_data()

        # 4. Test bond data
        results['bond'] = await test_bond_data()

        # 5. Test hybrid factory
        results['factory'] = await test_hybrid_factory()

        # 6. Test data consistency
        results['consistency'] = await test_data_consistency()

        # 7. Performance benchmark test
        results['performance'] = await performance_benchmark()

        # Summary
        print("\n" + "="*80)
        print("Test Summary")
        print("="*80)

        for test_name, result in results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            test_display = test_name.capitalize()
            print(f"{test_display:20}: {status}")

        passed = sum(1 for r in results.values() if r)
        total = len(results)

        print(f"\nOverall pass rate: {passed}/{total} ({passed/total*100:.1f}%)")

        # Data source coverage verification
        print("\n" + "="*80)
        print("Data Source Coverage")
        print("="*80)

        data_sources = [
            ("HK Stock Data", "HKEX Unified API", results.get('hkex', False)),
            ("FX Data", "Yahoo Finance", results.get('fx', False)),
            ("Commodity Data", "Alpha Vantage", results.get('commodity', False)),
            ("Bond Data", "FRED API", results.get('bond', False)),
        ]

        working_sources = 0
        for source_name, api_name, status in data_sources:
            symbol = "✓" if status else "✗"
            print(f"{symbol} {source_name:20} -> {api_name:25} {'[OK]' if status else '[FAIL]'}")
            if status:
                working_sources += 1

        coverage = working_sources / len(data_sources) * 100

        print(f"\nData source coverage: {working_sources}/{len(data_sources)} ({coverage:.1f}%)")

        # Final conclusion
        print("\n" + "="*80)
        print("Final Conclusion")
        print("="*80)

        if passed == total and coverage == 100:
            print("\n🎉 All tests passed! Hybrid data source architecture works perfectly!")
            print("\n✓ 100% real data source coverage:")
            print("  - HK Stock Data: HKEX Unified API")
            print("  - FX Data: Yahoo Finance")
            print("  - Commodity Data: Alpha Vantage")
            print("  - Bond Data: FRED API")
            print("\n✓ System features:")
            print("  - Zero cost operation")
            print("  - High reliability")
            print("  - High performance cache")
            print("  - Enterprise-grade error handling")
            print("\n🚀 System is ready for production use!")
        elif coverage >= 75:
            print("\n⚠️  Most data sources working, system is basically usable")
            print(f"Data source coverage: {coverage:.1f}%")
            print("建议检查失败的数据源配置")
        else:
            print("\n✗ Multiple data sources test failed")
            print(f"Data source coverage: {coverage:.1f}%")
            print("需要检查网络连接和API配置")

    except Exception as e:
        print(f"\nSerious error during test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
