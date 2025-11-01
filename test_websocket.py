#!/usr/bin/env python3
"""
WebSocket连接测试脚本
"""

import asyncio
import json
import websockets
import sys

async def test_websocket(endpoint: str):
    """测试WebSocket连接"""
    uri = f"ws://localhost:8001{endpoint}"
    print(f"\n🔌 测试 WebSocket: {uri}")

    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ 连接成功: {endpoint}")

            # 发送订阅消息
            subscribe_msg = {
                "type": "subscribe",
                "subscription": "portfolio_updates"
            }
            await websocket.send(json.dumps(subscribe_msg))
            print(f"📤 发送消息: {subscribe_msg}")

            # 发送ping消息
            ping_msg = {"type": "ping"}
            await websocket.send(json.dumps(ping_msg))
            print(f"📤 发送 Ping")

            # 等待回复（最多3秒）
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                print(f"📥 收到回复: {response}")
            except asyncio.TimeoutError:
                print(f"⏱️ 等待回复超时（这是正常的，服务可能不会立即回复）")

            print(f"✅ WebSocket测试完成: {endpoint}")
            return True

    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 CODEX Dashboard - WebSocket 连接测试")
    print("=" * 60)

    # 测试所有WebSocket端点
    endpoints = [
        "/ws/portfolio",
        "/ws/orders",
        "/ws/risk",
        "/ws/system"
    ]

    results = {}
    for endpoint in endpoints:
        results[endpoint] = await test_websocket(endpoint)
        await asyncio.sleep(0.5)  # 等待0.5秒再测试下一个

    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)

    success_count = sum(1 for result in results.values() if result)
    total_count = len(results)

    for endpoint, result in results.items():
        status = "✅ 成功" if result else "❌ 失败"
        print(f"{endpoint:30} {status}")

    print(f"\n总计: {success_count}/{total_count} 个端点连接成功")

    if success_count == total_count:
        print("\n🎉 所有 WebSocket 端点都工作正常！")
        return 0
    else:
        print(f"\n⚠️  {total_count - success_count} 个端点连接失败")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n🛑 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 致命错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
