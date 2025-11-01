"""
Check US Stock Account Balance
"""
import asyncio

async def check_us_account():
    try:
        from src.trading.futu_trading_api import create_futu_trading_api

        print("=" * 60)
        print("Checking US Stock Account Balance")
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

        # Get account info
        print("\n4. Getting US account information...")
        account = await futu_api.get_account_info()
        if account:
            print(f"   SUCCESS!")
            print(f"   Account ID: {account.account_id}")
            print(f"   Account Type: {account.account_type}")
            print(f"   Buying Power: ${account.buying_power:,.2f}")
            print(f"   Cash: ${account.cash:,.2f}")
            print(f"   Equity: ${account.equity:,.2f}")
            print(f"   Margin Used: ${account.margin_used:,.2f}")
            print(f"   Margin Available: ${account.margin_available:,.2f}")
        else:
            print("   Failed: Cannot get account info")
            return

        # Get positions
        print("\n5. Getting US positions...")
        positions = await futu_api.get_positions()
        if positions:
            print(f"   Current positions: {len(positions)}")
            for pos in positions[:5]:  # Show first 5
                print(f"     - {pos.symbol}: {pos.quantity} shares")
        else:
            print("   No positions")

        print("\n" + "=" * 60)
        print("US Stock Account Summary")
        print("=" * 60)
        if account:
            print(f"Cash Balance: ${account.cash:,.2f} USD")
            print(f"Total Equity: ${account.equity:,.2f} USD")
        print("=" * 60)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_us_account())
