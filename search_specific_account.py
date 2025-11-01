"""
Search for the expected $1,098,379.24 amount
"""
import asyncio

async def search_specific_account():
    try:
        import futu as ft
        from src.trading.futu_trading_api import create_futu_trading_api

        print("=" * 60)
        print("Search: Finding $1,098,379.24")
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

        # Try 1: Query account info with REAL environment using unlock_trade
        print("\n4. Trying REAL environment with unlock_trade...")
        ret, data_real = futu_api.trade_ctx.accinfo_query(trd_env=ft.TrdEnv.REAL)
        if ret == ft.RET_OK and not data_real.empty:
            total = data_real.iloc[0]['total_assets']
            print(f"   REAL (after unlock_trade) - Total Assets: {total}")
            if abs(total - 1098379.24) < 1:
                print(f"   *** FOUND EXPECTED AMOUNT: {total} ***")

        # Try 2: Get all available account info fields
        print("\n5. Checking ALL possible account fields...")
        ret, data = futu_api.trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)
        if ret == ft.RET_OK and not data.empty:
            row = data.iloc[0]
            for col in data.columns:
                value = row[col]
                # Check if value is close to expected
                try:
                    if isinstance(value, (int, float)) and abs(value - 1098379.24) < 1:
                        print(f"   *** FOUND IN FIELD '{col}': {value} ***")
                except:
                    pass

        # Try 3: Check if there's a multi-account scenario
        print("\n6. Checking for multiple accounts...")
        ret, data = futu_api.trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)
        if ret == ft.RET_OK and not data.empty:
            print(f"   Number of accounts returned: {len(data)}")
            for i, (_, row) in enumerate(data.iterrows()):
                print(f"   Account {i+1}: Total Assets = {row['total_assets']}")
                if abs(row['total_assets'] - 1098379.24) < 1:
                    print(f"   *** FOUND EXPECTED AMOUNT IN ACCOUNT {i+1} ***")

        # Try 4: Check different unlock combinations
        print("\n7. Trying different unlock combinations...")
        unlock_methods = [
            {'trade_password': '677750'},
            {'trade_password': '677750', 'session': 'REAL'},
            {'password': '677750'},
        ]

        for i, creds in enumerate(unlock_methods):
            try:
                print(f"   Method {i+1}: {creds}")
                if i == 0:
                    # Already unlocked
                    pass
                elif i == 1:
                    # Try unlock again
                    ret_unlock, _ = futu_api.trade_ctx.unlock_trade(password='677750')
                    print(f"      Unlock result: {ret_unlock}")
                elif i == 2:
                    # Try different method
                    ret_unlock, _ = futu_api.trade_ctx.unlock_trade(password='677750')
                    print(f"      Unlock result: {ret_unlock}")

                # Query both SIMULATE and REAL
                for env_name, env_val in [('SIMULATE', ft.TrdEnv.SIMULATE), ('REAL', ft.TrdEnv.REAL)]:
                    ret, data = futu_api.trade_ctx.accinfo_query(trd_env=env_val)
                    if ret == ft.RET_OK and not data.empty:
                        total = data.iloc[0]['total_assets']
                        if total > 0:
                            print(f"      {env_name} - Total Assets: {total}")
                            if abs(total - 1098379.24) < 1:
                                print(f"      *** FOUND EXPECTED AMOUNT: {total} ***")
            except Exception as e:
                print(f"      Method {i+1} failed: {e}")

        # Try 5: Check order history to see if there are large transactions
        print("\n8. Checking order history for large amounts...")
        try:
            ret, data = futu_api.trade_ctx.order_list_query(trd_env=ft.TrdEnv.SIMULATE)
            if ret == ft.RET_OK and not data.empty:
                print(f"   Found {len(data)} orders")
                for _, order in data.iterrows():
                    qty = order.get('qty', 0)
                    price = order.get('price', 0)
                    if qty and price:
                        value = qty * price
                        if value > 100000:  # Orders over $100k
                            print(f"   Large Order: {order.get('code', 'N/A')} - Qty: {qty}, Price: {price}, Value: ${value:,.2f}")
        except Exception as e:
            print(f"   Order history check failed: {e}")

        print("\n" + "=" * 60)
        print("RESULT SUMMARY:")
        print("EXPECTED: $1,098,379.24")
        print("CHECK: All outputs above for this amount")
        print("=" * 60)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(search_specific_account())
