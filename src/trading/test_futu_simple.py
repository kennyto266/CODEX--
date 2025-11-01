"""
Simplified Futu API Test - Avoiding Encoding Issues
"""

import asyncio
import sys
sys.path.append('.')

from futu_config import FUTU_CONFIG, SUPPORTED_HK_SYMBOLS

# Try to import Futu API
try:
    import futu as ft
    from futu import *
    FUTU_AVAILABLE = True
    print("✓ Futu API imported successfully")
except ImportError as e:
    print(f"✗ Failed to import Futu API: {e}")
    FUTU_AVAILABLE = False

if FUTU_AVAILABLE:
    print(f"\nConfig Info:")
    print(f"  Host: {FUTU_CONFIG['host']}")
    print(f"  Port: {FUTU_CONFIG['port']}")
    print(f"  User ID: {FUTU_CONFIG['user_id']}")
    print(f"  WebSocket Port: {FUTU_CONFIG['websocket_port']}")

    async def test_connection():
        print(f"\nTesting connection to FutuOpenD...")
        print(f"  Host: {FUTU_CONFIG['host']}:{FUTU_CONFIG['port']}")

        # Create quote context
        quote_ctx = ft.OpenQuoteContext(
            host=FUTU_CONFIG['host'],
            port=FUTU_CONFIG['port']
        )

        try:
            # Try to start
            print(f"\n1. Starting connection...")
            ret = quote_ctx.start()
            if ret == RET_OK:
                print(f"   ✓ Connection started successfully")
            else:
                print(f"   ✗ Failed to start connection: {ret}")
                print(f"\n   Please check:")
                print(f"   1. FutuOpenD is running")
                print(f"   2. Using account {FUTU_CONFIG['user_id']} to login")
                print(f"   3. Port {FUTU_CONFIG['port']} is open")
                return False

            # Try to get market snapshot
            print(f"\n2. Testing market data retrieval...")
            test_symbol = '00700.HK'  # Tencent
            ret, data = quote_ctx.get_market_snapshot([test_symbol])

            if ret == RET_OK:
                print(f"   ✓ Successfully retrieved data for {test_symbol}")
                if len(data) > 0:
                    row = data.iloc[0]
                    print(f"   Latest Price: ${row['last_price']:.2f}")
                    print(f"   Change: {row.get('change_pct', 0):.2f}%")
                return True
            else:
                print(f"   ✗ Failed to get market data: {data}")
                return False

        except Exception as e:
            print(f"   ✗ Error during test: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            quote_ctx.stop()
            quote_ctx.close()

    async def test_websocket():
        print(f"\n\nTesting WebSocket connection...")
        print(f"  WebSocket Port: {FUTU_CONFIG['websocket_port']}")

        quote_ctx = ft.OpenQuoteContext(
            host=FUTU_CONFIG['host'],
            port=FUTU_CONFIG['websocket_port']
        )

        try:
            print(f"\n1. Starting WebSocket...")
            ret = quote_ctx.start()
            if ret == RET_OK:
                print(f"   ✓ WebSocket started")
            else:
                print(f"   ✗ Failed to start WebSocket: {ret}")
                return False

            # Set WebSocket key
            print(f"\n2. Setting WebSocket key...")
            ret, data = quote_ctx.set_web_socket_key(key=FUTU_CONFIG['websocket_key'])
            if ret == RET_OK:
                print(f"   ✓ WebSocket key set")
            else:
                print(f"   ✗ Failed to set key: {data}")
                return False

            # Subscribe
            print(f"\n3. Subscribing to {test_symbol}...")
            ret = quote_ctx.subscribe(code='00700.HK', subtype_list=[SubType.QUOTE])
            if ret == RET_OK:
                print(f"   ✓ Subscribed successfully")
                print(f"\n   WebSocket is working!")
                print(f"   (Real-time data would be pushed here)")
                return True
            else:
                print(f"   ✗ Failed to subscribe")
                return False

        except Exception as e:
            print(f"   ✗ Error: {e}")
            return False
        finally:
            quote_ctx.stop()
            quote_ctx.close()

    async def main():
        print("="*60)
        print("Futu API Connection Test")
        print("="*60)

        # Test basic connection
        connection_ok = await test_connection()

        if connection_ok:
            # Test WebSocket
            websocket_ok = await test_websocket()

            print("\n" + "="*60)
            print("Test Summary")
            print("="*60)

            if connection_ok:
                print("✓ Basic API connection: SUCCESS")
            else:
                print("✗ Basic API connection: FAILED")

            if websocket_ok:
                print("✓ WebSocket connection: SUCCESS")
            else:
                print("✗ WebSocket connection: FAILED")

            print("\n" + "="*60)
            if connection_ok and websocket_ok:
                print("🎉 All tests passed! Futu API is working!")
            else:
                print("⚠️  Some tests failed. Check the errors above.")
            print("="*60)
        else:
            print("\n" + "="*60)
            print("⚠️  Cannot proceed - Basic connection failed")
            print("="*60)
            print("\nTo fix:")
            print("1. Download and install FutuOpenD from:")
            print("   https://www.futunn.com/download/openAPI")
            print("2. Login with account:", FUTU_CONFIG['user_id'])
            print("3. Ensure API port is enabled")

    # Run the test
    asyncio.run(main())
else:
    print("\nPlease install futu-api first:")
    print("  pip install futu-api")
