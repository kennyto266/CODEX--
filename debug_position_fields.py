"""
Debug Position List Query - Check actual fields
"""
import asyncio

async def debug_positions():
    try:
        import futu as ft
        from src.trading.futu_trading_api import create_futu_trading_api

        print("=" * 60)
        print("Debug: Position List Query Fields")
        print("=" * 60)

        # Create US market API instance
        print("\n1. Creating US market API instance...")
        futu_api = create_futu_trading_api(
            host='127.0.0.1',
            port=11111,
            trade_password='677750',
            market='US'
        )
        print("   Success: US API instance created")

        # Connect
        print("\n2. Connecting to FutuOpenD...")
        connected = await futu_api.connect()
        if not connected:
            print("   Failed: Cannot connect to OpenD")
            return
        print("   Success: Connected to OpenD")

        # Authenticate
        print("\n3. Authenticating...")
        auth_result = await futu_api.authenticate({'trade_password': '677750'})
        if not auth_result:
            print("   Failed: Authentication failed")
            return
        print("   SUCCESS: Authentication successful!")

        # Query position list directly
        print("\n4. Querying position list directly...")
        ret, data = futu_api.trade_ctx.position_list_query(trd_env=ft.TrdEnv.SIMULATE)

        if ret != ft.RET_OK:
            print(f"   Query failed: {data}")
            return

        print(f"   Ret type: {type(ret)}")
        print(f"   Data type: {type(data)}")
        print(f"   Data is empty: {data.empty}")
        print(f"   Data shape: {data.shape if not data.empty else 'empty'}")

        if not data.empty:
            print(f"\n   Columns: {list(data.columns)}")
            print(f"\n   First row data:")
            print(data.iloc[0])

            # Print all available columns and their values
            print("\n" + "="*60)
            print("All available position fields:")
            print("="*60)
            for col in data.columns:
                print(f"  {col}: {data.iloc[0][col]}")
            print("="*60)
        else:
            print("   No position data returned")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_positions())
