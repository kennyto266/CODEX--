"""
Debug US Account - Check ALL possible account data sources
"""
import asyncio

async def debug_all_account_data():
    try:
        import futu as ft
        from src.trading.futu_trading_api import create_futu_trading_api

        print("=" * 60)
        print("Debug: US Account - ALL Data Sources")
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

        # 1. Query account info with SIMULATE environment
        print("\n4. Querying account info (SIMULATE)...")
        ret, data = futu_api.trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)
        if ret == ft.RET_OK and not data.empty:
            print(f"   SIMULATE - Total Assets: {data.iloc[0]['total_assets']}")
            print(f"   SIMULATE - Securities Assets: {data.iloc[0]['securities_assets']}")
            print(f"   SIMULATE - Cash: {data.iloc[0]['cash']}")

        # 2. Query account info with REAL environment
        print("\n5. Querying account info (REAL)...")
        ret, data_real = futu_api.trade_ctx.accinfo_query(trd_env=ft.TrdEnv.REAL)
        if ret == ft.RET_OK and not data_real.empty:
            print(f"   REAL - Total Assets: {data_real.iloc[0]['total_assets']}")
            print(f"   REAL - Securities Assets: {data_real.iloc[0]['securities_assets']}")
            print(f"   REAL - Cash: {data_real.iloc[0]['cash']}")
        else:
            print(f"   REAL - Query failed or empty: {data_real}")

        # 3. Check if different currency fields have different values
        print("\n6. Checking all currency-related fields...")
        if ret == ft.RET_OK and not data.empty:
            row = data.iloc[0]
            usd_fields = ['us_cash', 'us_avl_withdrawal_cash', 'usd_net_cash_power', 'usd_assets']
            print("   USD-specific fields:")
            for field in usd_fields:
                if field in row:
                    print(f"     {field}: {row[field]}")

        # 4. Check position list to see total market value
        print("\n7. Getting detailed positions...")
        ret_pos, data_pos = futu_api.trade_ctx.position_list_query(trd_env=ft.TrdEnv.SIMULATE)
        if ret_pos == ft.RET_OK and not data_pos.empty:
            total_market_val = 0
            for _, pos in data_pos.iterrows():
                symbol = pos['code']
                qty = pos['qty']
                market_val = pos['market_val']
                total_market_val += market_val
                print(f"   {symbol}: {qty} shares, Market Value: {market_val}")
            print(f"   Total Position Market Value: {total_market_val}")

        # 5. Try account info without specifying trd_env (might use default)
        print("\n8. Querying account info (no trd_env specified)...")
        try:
            ret_default, data_default = futu_api.trade_ctx.accinfo_query()
            if ret_default == ft.RET_OK and not data_default.empty:
                print(f"   DEFAULT - Total Assets: {data_default.iloc[0]['total_assets']}")
        except Exception as e:
            print(f"   DEFAULT - Error: {e}")

        print("\n" + "=" * 60)
        print("EXPECTED: $1,098,379.24")
        print("FOUND: Check results above")
        print("=" * 60)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_all_account_data())
