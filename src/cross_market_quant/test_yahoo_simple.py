import asyncio
from adapters.fx_yahoo_adapter import FXYahooAdapter
from adapters.hkex_adapter import HKEXAdapter

async def test_fx_yahoo():
    print("\n" + "="*80)
    print("Testing Yahoo Finance FX Adapter (Real Data)")
    print("="*80)

    adapter = FXYahooAdapter()

    try:
        # Test USD/CNH
        print("\n1. Testing USD_CNH data...")
        data = await adapter.fetch_data('USD_CNH', '2024-01-01', '2024-01-10')
        print(f"SUCCESS: Got {len(data)} FX data points")
        print(f"Columns: {list(data.columns)}")
        print(f"Latest data:")
        print(data.tail(3))
        return True

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_hkex():
    print("\n" + "="*80)
    print("Testing HKEX Adapter (Real API)")
    print("="*80)

    adapter = HKEXAdapter()

    try:
        # Test HK stock
        print("\n1. Testing 0700.HK data...")
        data = await adapter.fetch_data('0700.HK', '2024-01-01', '2024-01-10')
        print(f"SUCCESS: Got {len(data)} HKEX data points")
        print(f"Columns: {list(data.columns)}")
        print(f"Latest data:")
        print(data.tail(3))
        return True

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("="*80)
    print("Cross-Market Quant System - Real Data Source Test (Optimized)")
    print("Using Hybrid Data Source Architecture")
    print("="*80)

    fx_result = await test_fx_yahoo()
    hkex_result = await test_hkex()

    print("\n" + "="*80)
    print("Test Summary")
    print("="*80)

    print(f"Yahoo Finance FX Adapter: {'PASS' if fx_result else 'FAIL'}")
    print(f"HKEX Adapter (Real API):   {'PASS' if hkex_result else 'FAIL'}")

    if fx_result and hkex_result:
        print("\nSUCCESS!")
        print("Hybrid data source architecture working!")
        print("Real data from multiple sources:")
        print("  - HK stocks: Unified API")
        print("  - FX data: Yahoo Finance")
    else:
        print("\nPARTIAL SUCCESS - Need optimization")

if __name__ == "__main__":
    asyncio.run(main())
