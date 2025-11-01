#!/usr/bin/env python3
"""
WebSocket connection test
"""

import asyncio
import json
import websockets
import sys

async def test_websocket(endpoint):
    """Test WebSocket connection"""
    uri = f"ws://localhost:8001{endpoint}"
    print(f"\nTesting WebSocket: {uri}")

    try:
        async with websockets.connect(uri) as websocket:
            print(f"SUCCESS: Connected to {endpoint}")

            # Send ping message
            ping_msg = {"type": "ping"}
            await websocket.send(json.dumps(ping_msg))
            print(f"SENT: {ping_msg}")

            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                print(f"RECEIVED: {response}")
            except asyncio.TimeoutError:
                print("TIMEOUT: No response (OK)")

            print(f"OK: WebSocket test complete: {endpoint}")
            return True

    except Exception as e:
        print(f"ERROR: Failed to connect to {endpoint}: {e}")
        return False

async def main():
    """Main test function"""
    print("=" * 60)
    print("CODEX Dashboard - WebSocket Connection Test")
    print("=" * 60)

    endpoints = [
        "/ws/portfolio",
        "/ws/orders",
        "/ws/risk",
        "/ws/system"
    ]

    results = {}
    for endpoint in endpoints:
        results[endpoint] = await test_websocket(endpoint)
        await asyncio.sleep(0.5)

    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    success_count = sum(1 for result in results.values() if result)
    total_count = len(results)

    for endpoint, result in results.items():
        status = "SUCCESS" if result else "FAILED"
        print(f"{endpoint:30} {status}")

    print(f"\nTotal: {success_count}/{total_count} endpoints connected successfully")

    if success_count == total_count:
        print("\nAll WebSocket endpoints working!")
        return 0
    else:
        print(f"\n{total_count - success_count} endpoints failed")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
