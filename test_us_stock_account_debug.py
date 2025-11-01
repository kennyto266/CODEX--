"""
Debug US Stock Account - Check raw data
"""
import asyncio

async def debug_us_account():
    try:
        import futu as ft
        from src.trading.futu_trading_api import create_futu_trading_api

        print("=" * 60)
        print("DEBUG: US Stock Account Raw Data")
        print("=" * 60)

        # Create connection for US market
        print("\n1. Creating US market API instance...")
        futu_api = create_futu_trading_api(
            host='127.0.0.1',
            port=11111,
            trade_password='677750',
            market='US'  # US market
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

        # Query account info directly
        print("\n4. Querying US account info directly...")
        ret, data = futu_api.trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)

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

            # Show cash-related fields
            print("\n" + "="*60)
            print("Cash/Asset Related Fields:")
            print("="*60)
            cash_fields = ['cash', 'power', 'total_assets', 'securities_assets', 'fund_assets', 'bond_assets']
            for col in cash_fields:
                if col in data.columns:
                    print(f"  {col}: {data.iloc[0][col]}")
            print("="*60)

        # Get positions
        print("\n5. Getting positions...")
        positions = await futu_api.get_positions()
        if positions:
            print(f"   Current positions: {len(positions)}")
            for pos in positions[:5]:
                print(f"     - {pos.symbol}: {pos.quantity} shares")
        else:
            print("   No positions")

        # Try to check if this is the same account as HK
        print("\n6. Checking if this is the same DEMO account...")
        print(f"   User ID: 2860386 (same for all markets)")
        print(f"   This DEMO account 2860386 supports HK, US, CN markets")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_us_account())
