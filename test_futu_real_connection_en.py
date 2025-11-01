"""
Test Futu Real Connection - Using correct password
"""
import asyncio

async def test_real_connection():
    try:
        from src.trading.futu_trading_api import create_futu_trading_api

        print("=" * 60)
        print("Testing Futu Real Connection")
        print("=" * 60)

        # Create connection
        print("\n1. Creating API instance...")
        futu_api = create_futu_trading_api(
            host='127.0.0.1',
            port=11111,
            trade_password='677750',
            market='HK'
        )
        print("   Success: API instance created")

        # Connect
        print("\n2. Connecting to FutuOpenD...")
        connected = await futu_api.connect()
        if not connected:
            print("   Failed: Cannot connect to OpenD")
            return
        print("   Success: Connected to OpenD")

        # Login
        print("\n3. Logging in to trading account...")
        login_result = await futu_api.login()
        if not login_result:
            print("   Failed: Login failed")
            return
        print("   SUCCESS: Login successful!")

        # Get account info
        print("\n4. Getting account information...")
        account = await futu_api.get_account_info()
        if account:
            print(f"   Account ID: {account.account_id}")
            print(f"   Account Type: {account.account_type}")
            print(f"   Buying Power: {account.buying_power:,.2f}")
            print(f"   Cash: {account.cash:,.2f}")
            print(f"   Equity: {account.equity:,.2f}")
        else:
            print("   Failed: Cannot get account info")
            return

        # Get positions
        print("\n5. Getting positions...")
        positions = await futu_api.get_positions()
        if positions:
            print(f"   Current positions: {len(positions)}")
            for pos in positions[:3]:  # Show only first 3
                print(f"     - {pos.symbol}: {pos.quantity} shares")
        else:
            print("   No positions")

        print("\n" + "=" * 60)
        print("SUCCESS: Futu connection test passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_real_connection())
