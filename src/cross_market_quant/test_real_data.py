#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test Real Data Fetching

Verify all adapters can fetch data from real API endpoints
No MOCK DATA used

Run:
    python test_real_data.py
"""

import asyncio
import sys
import os

# Set UTF-8 encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from adapters.fx_adapter import FXAdapter
from adapters.commodity_adapter import CommodityAdapter
from adapters.bond_adapter import BondAdapter
from adapters.hkex_adapter import HKEXAdapter


async def test_fx_adapter():
    """Test FX Adapter - Real Data Fetching"""
    print("\n" + "="*80)
    print("Testing FX Adapter - Real Data Fetching")
    print("="*80)

    adapter = FXAdapter()

    try:
        # Test USD/CNH data
        print("\n1. Testing USD_CNH data...")
        data = await adapter.fetch_data('USD_CNH', '2024-01-01', '2024-01-10')
        print(f"✓ Successfully fetched {len(data)} USD_CNH data points")
        print(f"  Date range: {data['Date'].min()} to {data['Date'].max()}")
        print(f"  Latest price: {data['Close'].iloc[-1]:.4f}")
        return True

    except Exception as e:
        print(f"✗ USD_CNH data fetch failed: {e}")
        return False


async def test_hkex_adapter():
    """测试HKEX适配器真实数据获取"""
    print("\n" + "="*80)
    print("测试HKEX适配器 - 真实数据获取")
    print("="*80)

    adapter = HKEXAdapter()

    try:
        # 测试腾讯数据
        print("\n1. 测试0700.HK数据...")
        data = await adapter.fetch_data('0700.HK', '2024-01-01', '2024-01-10')
        print(f"✓ 成功获取 {len(data)} 条0700.HK数据")
        print(f"  数据范围: {data['Date'].min()} 到 {data['Date'].max()}")
        print(f"  最新价格: {data['Close'].iloc[-1]:.2f}")
        return True

    except Exception as e:
        print(f"✗ 0700.HK数据获取失败: {e}")
        return False


async def test_commodity_adapter():
    """测试Commodity适配器真实数据获取"""
    print("\n" + "="*80)
    print("测试Commodity适配器 - 真实数据获取")
    print("="*80)

    adapter = CommodityAdapter()

    try:
        # 测试黄金数据
        print("\n1. 测试GOLD数据...")
        data = await adapter.fetch_data('GOLD', '2024-01-01', '2024-01-10')
        print(f"✓ 成功获取 {len(data)} 条GOLD数据")
        print(f"  数据范围: {data['Date'].min()} 到 {data['Date'].max()}")
        print(f"  最新价格: {data['Close'].iloc[-1]:.2f}")
        return True

    except Exception as e:
        print(f"✗ GOLD数据获取失败: {e}")
        return False


async def test_bond_adapter():
    """测试Bond适配器真实数据获取"""
    print("\n" + "="*80)
    print("测试Bond适配器 - 真实数据获取")
    print("="*80)

    adapter = BondAdapter()

    try:
        # 测试US 10Y数据
        print("\n1. 测试US_10Y数据...")
        data = await adapter.fetch_data('US_10Y', '2024-01-01', '2024-01-10')
        print(f"✓ 成功获取 {len(data)} 条US_10Y数据")
        print(f"  数据范围: {data['Date'].min()} 到 {data['Date'].max()}")
        print(f"  最新收益率: {data['Close'].iloc[-1]:.2f}%")
        return True

    except Exception as e:
        print(f"✗ US_10Y数据获取失败: {e}")
        return False


async def test_api_endpoint():
    """测试统一API端点是否可用"""
    print("\n" + "="*80)
    print("测试统一API端点可用性")
    print("="*80)

    import aiohttp

    base_url = "http://18.180.162.113:9191"
    endpoint = "/inst/getInst"

    try:
        async with aiohttp.ClientSession() as session:
            # 测试一个简单的请求
            url = f"{base_url}{endpoint}"
            params = {
                "symbol": "0700.hk",
                "duration": 10
            }

            print(f"\nAPI端点: {url}")
            print(f"测试参数: {params}")

            async with session.get(url, params=params, timeout=10) as response:
                print(f"\n✓ API端点可达")
                print(f"  状态码: {response.status}")

                if response.status == 200:
                    data = await response.json()
                    print(f"  响应数据键: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")

                    # Try to parse data
                    if 'data' in data:
                        records = data['data']
                        print(f"  Data records: {len(records)}")
                        if records:
                            print(f"  First record: {records[0]}")
                            # Check if we have enough records
                            if len(records) >= 10:
                                return True
                            else:
                                print(f"  ⚠️  Only {len(records)} records, expected at least 10")
                                return False
                    else:
                        print(f"  ⚠️  No 'data' field in response")
                        return False
                else:
                    print(f"✗ API响应错误")
                    return False

    except aiohttp.ClientError as e:
        print(f"✗ 无法连接到API端点: {e}")
        return False
    except Exception as e:
        print(f"✗ 测试API端点时发生错误: {e}")
        return False


async def main():
    """Main test function"""
    print("="*80)
    print("Cross-Market Quantitative Trading System - Real Data Fetching Test")
    print("No MOCK DATA used")
    print("="*80)

    # Test results
    results = {
        'api_endpoint': False,
        'fx_adapter': False,
        'hkex_adapter': False,
        'commodity_adapter': False,
        'bond_adapter': False
    }

    # 1. Test API endpoint
    results['api_endpoint'] = await test_api_endpoint()

    if not results['api_endpoint']:
        print("\n⚠️  API endpoint not available, skipping other tests")
        print("Please check network connection and API endpoint status")
        return

    # 2. Test each adapter
    results['fx_adapter'] = await test_fx_adapter()
    results['hkex_adapter'] = await test_hkex_adapter()
    results['commodity_adapter'] = await test_commodity_adapter()
    results['bond_adapter'] = await test_bond_adapter()

    # Output summary
    print("\n" + "="*80)
    print("Test Summary")
    print("="*80)

    for name, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{name:25s}: {status}")

    total_tests = len(results)
    passed_tests = sum(results.values())
    success_rate = passed_tests / total_tests * 100

    print(f"\nTotal tests: {total_tests}")
    print(f"Passed tests: {passed_tests}")
    print(f"Success rate: {success_rate:.1f}%")

    if success_rate == 100:
        print("\n🎉 All tests passed! System uses only real data sources!")
    elif success_rate >= 50:
        print("\n⚠️  Some tests passed, please check failed tests")
    else:
        print("\n✗ Most tests failed, please check API endpoint and network connection")


if __name__ == "__main__":
    asyncio.run(main())
