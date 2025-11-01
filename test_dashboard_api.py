#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard API 测试脚本

验证所有 API 端点是否正常工作：
1. 健康检查
2. 投资组合数据
3. 性能指标
4. 系统状态
5. 系统刷新
6. WebSocket 连接

使用方法:
    python test_dashboard_api.py
"""

import asyncio
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any

try:
    import httpx
except ImportError:
    print("❌ 错误: 需要安装 httpx 库")
    print("运行: pip install httpx")
    sys.exit(1)

# 配置
API_BASE_URL = "http://localhost:8001"
API_TIMEOUT = 10.0


class DashboardAPITester:
    """仪表板 API 测试器"""

    def __init__(self):
        self.base_url = API_BASE_URL
        self.timeout = API_TIMEOUT
        self.results = []
        self.passed = 0
        self.failed = 0

    async def test_endpoint(self, method: str, endpoint: str, expected_status: int = 200, description: str = "") -> Dict[str, Any]:
        """测试单个端点"""
        url = f"{self.base_url}{endpoint}"
        test_name = description or f"{method} {endpoint}"

        print(f"\n🧪 测试: {test_name}")
        print(f"   URL: {url}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url)
                elif method.upper() == "POST":
                    response = await client.post(url)
                else:
                    raise ValueError(f"不支持的方法: {method}")

                status = response.status_code
                elapsed = response.elapsed.total_seconds()

                # 检查状态码
                if status == expected_status:
                    print(f"   ✅ 状态码: {status} (期望: {expected_status})")
                    print(f"   ⏱️ 响应时间: {elapsed:.3f}s")

                    # 尝试解析 JSON
                    try:
                        data = response.json()
                        print(f"   📄 响应数据: {json.dumps(data, indent=4, ensure_ascii=False)[:200]}...")
                        result = {
                            "name": test_name,
                            "url": url,
                            "status": "PASS",
                            "status_code": status,
                            "response_time": elapsed,
                            "data": data
                        }
                        self.passed += 1
                    except json.JSONDecodeError:
                        print(f"   ⚠️ 响应不是有效的 JSON")
                        result = {
                            "name": test_name,
                            "url": url,
                            "status": "PARTIAL",
                            "status_code": status,
                            "response_time": elapsed,
                            "error": "响应不是有效的 JSON"
                        }
                        self.passed += 1
                else:
                    print(f"   ❌ 状态码: {status} (期望: {expected_status})")
                    print(f"   📄 响应内容: {response.text[:200]}")
                    result = {
                        "name": test_name,
                        "url": url,
                        "status": "FAIL",
                        "status_code": status,
                        "response_time": elapsed,
                        "error": f"状态码不匹配: {status} != {expected_status}"
                    }
                    self.failed += 1

                self.results.append(result)
                return result

        except httpx.TimeoutException:
            print(f"   ❌ 超时 (>{self.timeout}s)")
            result = {
                "name": test_name,
                "url": url,
                "status": "FAIL",
                "error": f"请求超时 (>{self.timeout}s)"
            }
            self.failed += 1
            self.results.append(result)
            return result

        except httpx.ConnectError:
            print(f"   ❌ 连接失败 - 请确保仪表板正在运行")
            print(f"   💡 运行: python run_dashboard.py")
            result = {
                "name": test_name,
                "url": url,
                "status": "FAIL",
                "error": "连接失败 - 请确保仪表板正在运行"
            }
            self.failed += 1
            self.results.append(result)
            return result

        except Exception as e:
            print(f"   ❌ 异常: {str(e)}")
            result = {
                "name": test_name,
                "url": url,
                "status": "FAIL",
                "error": str(e)
            }
            self.failed += 1
            self.results.append(result)
            return result

    async def test_health_endpoint(self):
        """测试健康检查端点"""
        print("\n" + "="*70)
        print("📋 测试 1: 健康检查端点")
        print("="*70)

        await self.test_endpoint("GET", "/api/health", 200, "健康检查 (主路径)")
        await self.test_endpoint("GET", "/health", 200, "健康检查 (别名)")

    async def test_portfolio_endpoint(self):
        """测试投资组合端点"""
        print("\n" + "="*70)
        print("📋 测试 2: 投资组合数据端点")
        print("="*70)

        result = await self.test_endpoint("GET", "/api/trading/portfolio", 200, "投资组合数据")

        # 验证响应数据结构
        if result["status"] == "PASS":
            data = result["data"]
            required_fields = ["initial_capital", "portfolio_value", "active_positions", "total_return", "currency"]
            missing_fields = [f for f in required_fields if f not in data]

            if missing_fields:
                print(f"   ⚠️ 缺少字段: {missing_fields}")
            else:
                print(f"   ✅ 所有必需字段都存在")

    async def test_performance_endpoint(self):
        """测试性能指标端点"""
        print("\n" + "="*70)
        print("📋 测试 3: 性能指标端点")
        print("="*70)

        result = await self.test_endpoint("GET", "/api/trading/performance", 200, "性能指标")

        # 验证响应数据结构
        if result["status"] == "PASS":
            data = result["data"]
            required_fields = ["total_return_pct", "sharpe_ratio", "max_drawdown", "win_rate"]
            missing_fields = [f for f in required_fields if f not in data]

            if missing_fields:
                print(f"   ⚠️ 缺少字段: {missing_fields}")
            else:
                print(f"   ✅ 所有必需字段都存在")

    async def test_system_status_endpoint(self):
        """测试系统状态端点"""
        print("\n" + "="*70)
        print("📋 测试 4: 系统状态端点")
        print("="*70)

        result = await self.test_endpoint("GET", "/api/system/status", 200, "系统状态")

        # 验证响应数据结构
        if result["status"] == "PASS":
            data = result["data"]
            required_fields = ["status", "agents", "uptime_seconds", "resources"]
            missing_fields = [f for f in required_fields if f not in data]

            if missing_fields:
                print(f"   ⚠️ 缺少字段: {missing_fields}")
            else:
                print(f"   ✅ 所有必需字段都存在")
                print(f"   📊 系统状态: {data['status']}")
                print(f"   🤖 Agent 状态: {data['agents']['active']}/{data['agents']['total']} 运行中")

    async def test_system_refresh_endpoint(self):
        """测试系统刷新端点"""
        print("\n" + "="*70)
        print("📋 测试 5: 系统刷新端点")
        print("="*70)

        await self.test_endpoint("POST", "/api/system/refresh", 200, "软刷新系统")

        # 测试硬刷新
        print(f"\n🧪 测试: POST /api/system/refresh (hard_refresh=true)")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/system/refresh",
                    json={"hard_refresh": True}
                )
                if response.status_code == 200:
                    print(f"   ✅ 状态码: 200")
                    print(f"   📄 响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
                    self.passed += 1
                    self.results.append({
                        "name": "硬刷新系统",
                        "url": f"{self.base_url}/api/system/refresh",
                        "status": "PASS",
                        "status_code": 200,
                        "data": response.json()
                    })
                else:
                    print(f"   ❌ 状态码: {response.status_code}")
                    self.failed += 1
        except Exception as e:
            print(f"   ❌ 异常: {str(e)}")
            self.failed += 1

    async def test_stock_data_endpoint(self):
        """测试股票数据端点"""
        print("\n" + "="*70)
        print("📋 测试 6: 股票数据端点")
        print("="*70)

        # 测试腾讯股票
        await self.test_endpoint("GET", "/api/stock/data?symbol=0700.HK&duration=365", 200, "腾讯股票数据")

        # 测试建行股票
        await self.test_endpoint("GET", "/api/stock/data?symbol=0939.HK&duration=365", 200, "建行股票数据")

    async def test_favicon_endpoint(self):
        """测试 Favicon 端点"""
        print("\n" + "="*70)
        print("📋 测试 7: Favicon 端点")
        print("="*70)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/favicon.ico")
                if response.status_code == 200:
                    print(f"   ✅ 状态码: 200")
                    print(f"   📦 内容类型: {response.headers.get('content-type', 'N/A')}")
                    print(f"   📏 内容大小: {len(response.content)} 字节")
                    self.passed += 1
                    self.results.append({
                        "name": "Favicon",
                        "url": f"{self.base_url}/favicon.ico",
                        "status": "PASS",
                        "status_code": 200,
                        "content_size": len(response.content)
                    })
                else:
                    print(f"   ❌ 状态码: {response.status_code}")
                    self.failed += 1
        except Exception as e:
            print(f"   ❌ 异常: {str(e)}")
            self.failed += 1

    async def test_gov_data_endpoint(self):
        """测试 gov_crawler 数据端点"""
        print("\n" + "="*70)
        print("📋 测试 8: gov_crawler 数据端点")
        print("="*70)

        # 测试 gov_crawler 状态
        await self.test_endpoint("GET", "/api/gov/status", 200, "gov_crawler 系统状态")

        # 测试可用指标列表
        await self.test_endpoint("GET", "/api/gov/indicators", 200, "gov_crawler 指标列表")

        # 测试获取特定指标数据（即使失败，也验证错误处理）
        print(f"\n🧪 测试: GET /api/gov/data?indicator=hibor_overnight")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/gov/data?indicator=hibor_overnight")
                # 可能返回 200（如果数据存在）或 503（如果数据不存在）
                if response.status_code in [200, 503]:
                    print(f"   ✅ 状态码: {response.status_code} (预期的状态码)")
                    print(f"   📄 响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)[:200]}...")
                    self.passed += 1
                    self.results.append({
                        "name": "gov_crawler 数据获取",
                        "url": f"{self.base_url}/api/gov/data",
                        "status": "PASS",
                        "status_code": response.status_code,
                        "data": response.json()
                    })
                else:
                    print(f"   ❌ 状态码: {response.status_code} (意外的响应)")
                    self.failed += 1
        except Exception as e:
            print(f"   ❌ 异常: {str(e)}")
            self.failed += 1

    async def test_websocket_connection(self):
        """测试 WebSocket 连接"""
        print("\n" + "="*70)
        print("📋 测试 8: WebSocket 连接")
        print("="*70)

        try:
            import websockets
        except ImportError:
            print("   ⚠️ 需要安装 websockets 库进行 WebSocket 测试")
            print("   运行: pip install websockets")
            return

        ws_urls = [
            "ws://localhost:8001/ws/portfolio",
            "ws://localhost:8001/ws/orders",
            "ws://localhost:8001/ws/risk",
            "ws://localhost:8001/ws/system"
        ]

        for ws_url in ws_urls:
            try:
                print(f"\n🧪 测试 WebSocket: {ws_url}")
                async with websockets.connect(ws_url, timeout=5) as websocket:
                    print(f"   ✅ 连接成功")
                    # 发送测试消息
                    await websocket.send(json.dumps({"action": "ping"}))
                    response = await asyncio.wait_for(websocket.recv(), timeout=2)
                    print(f"   📄 收到响应: {response[:100]}...")
                    self.passed += 1
                    self.results.append({
                        "name": f"WebSocket - {ws_url.split('/')[-1]}",
                        "url": ws_url,
                        "status": "PASS"
                    })
            except Exception as e:
                print(f"   ❌ 连接失败: {str(e)}")
                self.failed += 1
                self.results.append({
                    "name": f"WebSocket - {ws_url.split('/')[-1]}",
                    "url": ws_url,
                    "status": "FAIL",
                    "error": str(e)
                })

    async def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*70)
        print("🚀 开始 Dashboard API 测试")
        print("="*70)
        print(f"📍 测试地址: {self.base_url}")
        print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        start_time = time.time()

        # 运行所有测试
        await self.test_health_endpoint()
        await self.test_portfolio_endpoint()
        await self.test_performance_endpoint()
        await self.test_system_status_endpoint()
        await self.test_system_refresh_endpoint()
        await self.test_stock_data_endpoint()
        await self.test_favicon_endpoint()
        await self.test_gov_data_endpoint()
        await self.test_websocket_connection()

        # 计算总耗时
        total_time = time.time() - start_time

        # 打印总结
        print("\n" + "="*70)
        print("📊 测试总结")
        print("="*70)
        print(f"✅ 通过: {self.passed}")
        print(f"❌ 失败: {self.failed}")
        print(f"📈 总计: {self.passed + self.failed}")
        print(f"⏱️ 总耗时: {total_time:.2f}s")

        if self.failed == 0:
            print("\n🎉 所有测试通过！仪表板 API 正常运行")
        else:
            print(f"\n⚠️ 有 {self.failed} 个测试失败，请检查上述错误")

        # 保存详细结果
        results_file = f"dashboard_api_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 详细测试结果已保存到: {results_file}")

        return self.failed == 0


async def main():
    """主函数"""
    tester = DashboardAPITester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 致命错误: {e}", exc_info=True)
        sys.exit(1)
