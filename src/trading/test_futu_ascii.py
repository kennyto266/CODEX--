"""
ASCII-only Futu API Test
"""

import asyncio
import sys
sys.path.append('.')

from futu_config import FUTU_CONFIG

# Try to import Futu API
try:
    import futu as ft
    from futu import *
    print("[OK] Futu API imported successfully")
    FUTU_AVAILABLE = True
except ImportError as e:
    print(f"[ERROR] Failed to import Futu API: {e}")
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

        quote_ctx = ft.OpenQuoteContext(
            host=FUTU_CONFIG['host'],
            port=FUTU_CONFIG['port']
        )

        try:
            print(f"\n[1] Starting connection...")
            ret = quote_ctx.start()
            if ret == RET_OK:
                print(f"   [OK] Connection started")
            else:
                print(f"   [ERROR] Failed: {ret}")
                print(f"\n   Please check:")
                print(f"   1. FutuOpenD is running")
                print(f"   2. Using account {FUTU_CONFIG['user_id']} to login")
                print(f"   3. Port {FUTU_CONFIG['port']} is open")
                return False

            print(f"\n[2] Testing market data...")
            ret, data = quote_ctx.get_market_snapshot(['00700.HK'])

            if ret == RET_OK:
                print(f"   [OK] Retrieved data for 00700.HK")
                if len(data) > 0:
                    row = data.iloc[0]
                    print(f"   Price: ${row['last_price']:.2f}")
                    print(f"   Change: {row.get('change_pct', 0):.2f}%")
                return True
            else:
                print(f"   [ERROR] {data}")
                return False

        except Exception as e:
            print(f"   [ERROR] {e}")
            return False
        finally:
            quote_ctx.stop()
            quote_ctx.close()

    async def test_websocket():
        print(f"\n\nTesting WebSocket...")
        print(f"  Port: {FUTU_CONFIG['websocket_port']}")

        quote_ctx = ft.OpenQuoteContext(
            host=FUTU_CONFIG['host'],
            port=FUTU_CONFIG['websocket_port']
        )

        try:
            print(f"\n[1] Starting WebSocket...")
            ret = quote_ctx.start()
            if ret == RET_OK:
                print(f"   [OK] WebSocket started")
            else:
                print(f"   [ERROR] Failed: {ret}")
                return False

            print(f"\n[2] Setting WebSocket key...")
            ret, data = quote_ctx.set_web_socket_key(key=FUTU_CONFIG['websocket_key'])
            if ret == RET_OK:
                print(f"   [OK] Key set")
            else:
                print(f"   [ERROR] {data}")
                return False

            print(f"\n[3] Subscribing...")
            ret = quote_ctx.subscribe(code='00700.HK', subtype_list=[SubType.QUOTE])
            if ret == RET_OK:
                print(f"   [OK] Subscribed")
                print(f"\n   WebSocket is working!")
                return True
            else:
                print(f"   [ERROR] Failed to subscribe")
                return False

        except Exception as e:
            print(f"   [ERROR] {e}")
            return False
        finally:
            quote_ctx.stop()
            quote_ctx.close()

    async def main():
        print("="*60)
        print("FUTU API CONNECTION TEST")
        print("="*60)

        connection_ok = await test_connection()

        if connection_ok:
            websocket_ok = await test_websocket()

            print("\n" + "="*60)
            print("TEST SUMMARY")
            print("="*60)

            if connection_ok:
                print("[OK] Basic API connection")
            else:
                print("[ERROR] Basic API connection failed")

            if websocket_ok:
                print("[OK] WebSocket connection")
            else:
                print("[ERROR] WebSocket connection failed")

            print("\n" + "="*60)
            if connection_ok and websocket_ok:
                print("SUCCESS! Futu API is working!")
            else:
                print("FAILED! Check errors above.")
            print("="*60)
        else:
            print("\n" + "="*60)
            print("Cannot proceed - Basic connection failed")
            print("="*60)
            print("\nTo fix:")
            print("1. Download FutuOpenD:")
            print("   https://www.futunn.com/download/openAPI")
            print("2. Login with:", FUTU_CONFIG['user_id'])
            print("3. Enable API access")

    asyncio.run(main())
else:
    print("\nPlease install futu-api:")
    print("  pip install futu-api")
