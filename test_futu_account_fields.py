"""
Debug Futu API - Check actual returned data structure
"""
import asyncio

async def debug_account_info():
    try:
        from src.trading.futu_trading_api import create_futu_trading_api

        print("=" * 60)
        print("Debugging Futu Account Info Fields")
        print("=" * 60)

        # Create connection
        futu_api = create_futu_trading_api(
            host='127.0.0.1',
            port=11111,
            trade_password='677750',
            market='HK'
        )

        # Connect
        print("\nConnecting...")
        connected = await futu_api.connect()
        if not connected:
            print("Failed to connect")
            return

        # Authenticate
        print("Authenticating...")
        auth_result = await futu_api.authenticate({'trade_password': '677750'})
        if not auth_result:
            print("Failed to authenticate")
            return

        # Query account info
        print("\nQuerying account info...")
        import futu as ft
        ret, data = futu_api.trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)

        if ret != ft.RET_OK:
            print(f"Query failed: {data}")
            return

        print(f"\nRet type: {type(ret)}")
        print(f"Data type: {type(data)}")
        print(f"Data is empty: {data.empty}")
        print(f"Data shape: {data.shape if not data.empty else 'empty'}")

        if not data.empty:
            print(f"\nColumns: {list(data.columns)}")
            print(f"\nFirst row data:")
            print(data.iloc[0])

            # Print all available columns and their values
            print("\n" + "="*60)
            print("All available fields:")
            print("="*60)
            for col in data.columns:
                print(f"  {col}: {data.iloc[0][col]}")
            print("="*60)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_account_info())
