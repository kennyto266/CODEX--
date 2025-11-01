#!/usr/bin/env python3
"""
测试 gov_crawler API 端点
"""
import asyncio
import sys
import json
import time
from datetime import datetime

try:
    import httpx
except ImportError:
    print("需要安装 httpx: pip install httpx")
    sys.exit(1)

API_BASE_URL = "http://localhost:8002"
API_TIMEOUT = 10.0


async def test_gov_crawler():
    """测试 gov_crawler API"""
    print("=" * 70)
    print("Testing gov_crawler API Endpoints")
    print("=" * 70)

    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            # 1. 测试健康检查
            print("\n1. Testing /api/health")
            response = await client.get(f"{API_BASE_URL}/api/health")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   Response: {json.dumps(response.json(), indent=2)}")
            else:
                print(f"   Error: {response.text}")

            # 2. 测试 gov_crawler 状态
            print("\n2. Testing /api/gov/status")
            response = await client.get(f"{API_BASE_URL}/api/gov/status")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Project: {data.get('project')}")
                print(f"   Status: {data.get('status')}")
                print(f"   Indicators: {data.get('total_indicators', 'N/A')}")
            else:
                print(f"   Error: {response.text}")

            # 3. 测试指标列表
            print("\n3. Testing /api/gov/indicators")
            response = await client.get(f"{API_BASE_URL}/api/gov/indicators")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Total indicators: {data.get('total_indicators')}")
                print(f"   Categories: {data.get('total_categories')}")
                print(f"   Available indicators: {data.get('indicators', [])[:10]}")
            else:
                print(f"   Error: {response.text}")

            # 4. 测试获取 hibor_overnight 数据
            print("\n4. Testing /api/gov/data?indicator=hibor_overnight")
            response = await client.get(f"{API_BASE_URL}/api/gov/data?indicator=hibor_overnight")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Indicator: {data.get('indicator')}")
                print(f"   Source: {data.get('source')}")
                if 'data' in data:
                    print(f"   Data keys: {list(data['data'].keys()) if isinstance(data['data'], dict) else 'N/A'}")
                    if isinstance(data['data'], dict) and 'values' in data['data']:
                        print(f"   Sample values: {data['data']['values'][:5]}")
            else:
                print(f"   Error: {response.text}")

            # 5. 测试获取 gdp 数据
            print("\n5. Testing /api/gov/data?indicator=gdp")
            response = await client.get(f"{API_BASE_URL}/api/gov/data?indicator=gdp")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Indicator: {data.get('indicator')}")
                print(f"   Category: {data.get('category', 'N/A')}")
            else:
                print(f"   Error: {response.text}")

            # 6. 测试不存在的指标
            print("\n6. Testing non-existent indicator")
            response = await client.get(f"{API_BASE_URL}/api/gov/data?indicator=nonexistent")
            print(f"   Status: {response.status_code}")
            if response.status_code == 404:
                print(f"   Expected error for non-existent indicator")
            else:
                print(f"   Unexpected response: {response.text}")

    except httpx.ConnectError:
        print("\n❌ 无法连接到服务器")
        print("请先启动 dashboard: python run_dashboard.py")
        return False
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 70)
    print("All tests completed!")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = asyncio.run(test_gov_crawler())
    sys.exit(0 if success else 1)
