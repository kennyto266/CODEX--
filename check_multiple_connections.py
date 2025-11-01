"""
Check for multiple FutuOpenD connections or different account configurations
"""
import asyncio

async def check_multiple_connections():
    try:
        import futu as ft
        from src.trading.futu_trading_api import create_futu_trading_api

        print("=" * 60)
        print("Check: Multiple FutuOpenD Connections")
        print("=" * 60)

        # Try different configurations
        configs = [
            {'host': '127.0.0.1', 'port': 11111, 'password': '677750'},
            {'host': '127.0.0.1', 'port': 11112, 'password': '677750'},
            {'host': '127.0.0.1', 'port': 11113, 'password': '677750'},
            {'host': 'localhost', 'port': 11111, 'password': '677750'},
        ]

        for i, config in enumerate(configs, 1):
            print(f"\n{i}. Trying {config['host']}:{config['port']}...")

            try:
                # Create API instance
                futu_api = create_futu_trading_api(
                    host=config['host'],
                    port=config['port'],
                    trade_password=config['password'],
                    market='US'
                )

                # Connect
                connected = await futu_api.connect()
                if not connected:
                    print(f"   Failed to connect")
                    continue

                # Authenticate
                auth_result = await futu_api.authenticate({'trade_password': config['password']})
                if not auth_result:
                    print(f"   Failed to authenticate")
                    continue

                # Query account info
                ret, data = futu_api.trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)
                if ret == ft.RET_OK and not data.empty:
                    total_assets = data.iloc[0]['total_assets']
                    cash = data.iloc[0]['cash']
                    user_id = "Unknown"

                    # Try to get user ID from connection info
                    print(f"   SUCCESS: Total Assets = ${total_assets:,.2f}")
                    print(f"   Cash = ${cash:,.2f}")

                    if abs(total_assets - 1098379.24) < 1:
                        print(f"   *** FOUND EXPECTED AMOUNT: ${total_assets:,.2f} ***")

                    # Check positions
                    ret_pos, data_pos = futu_api.trade_ctx.position_list_query(trd_env=ft.TrdEnv.SIMULATE)
                    if ret_pos == ft.RET_OK and not data_pos.empty:
                        print(f"   Positions: {len(data_pos)} stocks")
                        for _, pos in data_pos.iterrows():
                            symbol = pos['code']
                            qty = pos['qty']
                            market_val = pos['market_val']
                            print(f"     {symbol}: {qty} shares, ${market_val:,.2f}")
                else:
                    print(f"   No data returned")

                await futu_api.disconnect()

            except Exception as e:
                print(f"   Error: {e}")

        # Try to get user ID information
        print("\n" + "=" * 60)
        print("User ID Information:")
        print("=" * 60)
        print("Current User ID: 2860386")
        print("If you have a different User ID with $1,098,379.24,")
        print("please check:")
        print("1. Different FutuOpenD configuration")
        print("2. Different login credentials")
        print("3. Different account (real money vs demo)")

        print("\n" + "=" * 60)
        print("POSSIBLE EXPLANATIONS:")
        print("=" * 60)
        print("1. Different User Account:")
        print("   - You may be using a different Futu account")
        print("   - This account (2860386) has $43,615.94")
        print("   - Your account may have $1,098,379.24")
        print()
        print("2. Different Environment:")
        print("   - Real trading account vs Demo account")
        print("   - Different market permissions")
        print()
        print("3. Historical Data:")
        print("   - Previous balance before losses")
        print("   - Different time period")
        print("=" * 60)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_multiple_connections())
