"""
Get All Trading Accounts List - As per Futu API Q&A Q17
"""
import asyncio

async def get_all_accounts():
    try:
        import futu as ft
        from src.trading.futu_trading_api import create_futu_trading_api

        print("=" * 60)
        print("Get All Trading Accounts - As per API Q&A Q17")
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

        # Get all accounts using get_acc_list
        print("\n4. Getting all trading accounts...")
        print("   Using trd_ctx.get_acc_list() as per API Q&A Q17...")

        # First get all accounts with NO filter (filter_trdmarket=NONE)
        print("\n   Step 1: Get ALL accounts (no market filter)...")
        # This is equivalent to filter_trdmarket=NONE
        # We need to use the raw Futu API
        ret, data = futu_api.trade_ctx.get_acc_list()

        if ret != ft.RET_OK:
            print(f"   Failed to get account list: {data}")
            return

        print(f"   SUCCESS! Found {len(data)} accounts")
        print("\n" + "="*60)
        print("ALL ACCOUNTS LIST:")
        print("="*60)

        # Print all accounts with details
        for i, (_, row) in enumerate(data.iterrows()):
            print(f"\nAccount {i+1}:")
            print(f"  acc_id: {row['acc_id']}")
            print(f"  trd_env: {row['trd_env']}")
            print(f"  acc_type: {row['acc_type']}")
            print(f"  card_num: {row['card_num']}")
            print(f"  security_firm: {row['security_firm']}")
            if 'sim_acc_type' in row:
                print(f"  sim_acc_type: {row['sim_acc_type']}")
            if 'trdmarket_auth' in row:
                print(f"  trdmarket_auth: {row['trdmarket_auth']}")
            print(f"  acc_status: {row['acc_status']}")

        # Now filter to only SIMULATE accounts
        print("\n" + "="*60)
        print("SIMULATE ACCOUNTS ONLY:")
        print("="*60)
        simulate_accounts = data[data['trd_env'] == 'SIMULATE']
        print(f"\nFound {len(simulate_accounts)} SIMULATE accounts")

        for i, (idx, row) in enumerate(simulate_accounts.iterrows()):
            print(f"\nSim Account {i+1} (acc_id: {row['acc_id']}):")
            print(f"  acc_type: {row['acc_type']}")
            if 'sim_acc_type' in row:
                print(f"  sim_acc_type: {row['sim_acc_type']}")
            if 'trdmarket_auth' in row:
                print(f"  trdmarket_auth: {row['trdmarket_auth']}")

        # Check if any account has $1,098,379.24
        print("\n" + "="*60)
        print("CHECKING EACH SIMULATE ACCOUNT BALANCE:")
        print("="*60)

        for i, (idx, row) in enumerate(simulate_accounts.iterrows()):
            acc_id = row['acc_id']
            print(f"\n{i+1}. Testing Account {acc_id}...")

            try:
                # Query account info for this specific account
                ret, acc_data = futu_api.trade_ctx.accinfo_query(
                    trd_env=ft.TrdEnv.SIMULATE,
                    acc_id=acc_id
                )

                if ret == ft.RET_OK and not acc_data.empty:
                    total_assets = acc_data.iloc[0]['total_assets']
                    cash = acc_data.iloc[0]['cash']
                    print(f"   Total Assets: ${total_assets:,.2f}")
                    print(f"   Cash: ${cash:,.2f}")

                    # Check if this matches expected amount
                    if abs(total_assets - 1098379.24) < 1:
                        print(f"   *** MATCH FOUND! This is the expected account! ***")
                        print(f"   Account ID: {acc_id}")
                        print(f"   Balance: ${total_assets:,.2f}")
                else:
                    print(f"   Failed to get balance: {acc_data}")
            except Exception as e:
                print(f"   Error querying account {acc_id}: {e}")

        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Total accounts found: {len(data)}")
        print(f"Simulate accounts: {len(simulate_accounts)}")
        print("\nThis explains the discrepancy!")
        print("Your platform account (2860386) may have multiple trading sub-accounts.")
        print("Each market (HK, US, CN) may have separate sub-accounts.")
        print("Each account type (CASH, MARGIN) may be separate.")
        print("="*60)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(get_all_accounts())
