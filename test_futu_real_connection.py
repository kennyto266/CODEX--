"""
测试富途真实连接 - 使用正确密码
"""
import asyncio
from decimal import Decimal

async def test_real_connection():
    try:
        from src.trading.futu_trading_api import create_futu_trading_api

        print("=" * 60)
        print("测试富途真实连接")
        print("=" * 60)

        # 创建连接
        print("\n1. 创建API实例...")
        futu_api = create_futu_trading_api(
            host='127.0.0.1',
            port=11111,
            trade_password='677750',
            market='HK'
        )
        print("   成功创建API实例")

        # 连接
        print("\n2. 连接到富途OpenD...")
        connected = await futu_api.connect()
        if not connected:
            print("   失败：无法连接到OpenD")
            return
        print("   成功连接到OpenD")

        # 登录
        print("\n3. 登录交易账户...")
        login_result = await futu_api.login()
        if not login_result:
            print("   失败：登录失败")
            return
        print("   登录成功！")

        # 获取账户信息
        print("\n4. 获取账户信息...")
        account = await futu_api.get_account_info()
        if account:
            print(f"   账户ID: {account.account_id}")
            print(f"   账户类型: {account.account_type}")
            print(f"   购买力: {account.buying_power:,.2f}")
            print(f"   现金: {account.cash:,.2f}")
            print(f"   净值: {account.equity:,.2f}")
        else:
            print("   失败：无法获取账户信息")
            return

        # 获取持仓
        print("\n5. 获取持仓列表...")
        positions = await futu_api.get_positions()
        if positions:
            print(f"   当前有 {len(positions)} 个持仓")
            for pos in positions[:3]:  # 只显示前3个
                print(f"     - {pos.symbol}: {pos.quantity} 股")
        else:
            print("   无持仓")

        print("\n" + "=" * 60)
        print("富途连接测试成功！")
        print("=" * 60)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_real_connection())
