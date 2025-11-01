"""
富途牛牛API真实交易测试

使用富途DEMO环境进行安全测试
⚠️ 注意事项：
1. 需要先启动FutuOpenD网关客户端
2. 配置DEMO账户（模拟环境）
3. 使用模拟资金进行交易
"""

import asyncio
import sys
sys.path.append('.')

from futu_trading_api import FutuTradingAPI, create_futu_trading_api
from base_trading_api import Order, OrderType, OrderSide
from decimal import Decimal
import json


async def test_futu_connection():
    """测试富途API连接"""
    print("\n" + "="*60)
    print("富途API连接测试")
    print("="*60)

    # 创建富途API实例
    print("\n1. 创建富途API实例...")
    api = create_futu_trading_api(
        host='127.0.0.1',
        port=11111,
        market='HK'
    )
    print("   富途API实例已创建")

    # 连接
    print("\n2. 连接到富途API...")
    try:
        await api.connect()
        print("   ✓ 连接成功")
    except Exception as e:
        print(f"   ✗ 连接失败: {e}")
        print("\n   请确保：")
        print("   1. FutuOpenD网关客户端已启动")
        print("   2. 端口11111已开放")
        return None

    # 认证
    print("\n3. 解锁交易接口 (DEMO环境)...")
    try:
        success = await api.authenticate({'trade_password': '123456'})
        if success:
            print("   ✓ 解锁成功")
        else:
            print("   ✗ 解锁失败")
            print("   请检查DEMO账户密码设置")
    except Exception as e:
        print(f"   ✗ 认证失败: {e}")
        return None

    return api


async def test_futu_account_info(api: FutuTradingAPI):
    """测试获取账户信息"""
    print("\n" + "="*60)
    print("账户信息查询测试")
    print("="*60)

    print("\n查询账户信息...")
    account = await api.get_account_info()

    if account:
        print("\n✅ 账户信息:")
        print(f"   账户ID: {account.account_id}")
        print(f"   账户类型: {account.account_type}")
        print(f"   现金余额: ${account.cash:,.2f}")
        print(f"   购买力: ${account.buying_power:,.2f}")
        print(f"   权益: ${account.equity:,.2f}")
        print(f"   已用保证金: ${account.margin_used:,.2f}")
        print(f"   可用保证金: ${account.margin_available:,.2f}")
    else:
        print("\n❌ 获取账户信息失败")


async def test_futu_market_data(api: FutuTradingAPI):
    """测试获取市场数据"""
    print("\n" + "="*60)
    print("市场数据查询测试")
    print("="*60)

    symbols = ['00700.HK', '0388.HK']  # 腾讯、港交所

    for symbol in symbols:
        print(f"\n获取{symbol}市场数据...")
        market_data = await api.get_market_data(symbol)

        if market_data:
            print(f"\n✅ {symbol}市场数据:")
            print(f"   最新价: ${market_data.last_price:.2f}")
            print(f"   买入价: ${market_data.bid_price:.2f}")
            print(f"   卖出价: ${market_data.ask_price:.2f}")
            print(f"   成交量: {market_data.volume:,}")
            print(f"   开盘价: ${market_data.open_price:.2f}")
            print(f"   最高价: ${market_data.high_price:.2f}")
            print(f"   最低价: ${market_data.low_price:.2f}")
        else:
            print(f"   ❌ 获取{symbol}数据失败")


async def test_futu_positions(api: FutuTradingAPI):
    """测试获取持仓"""
    print("\n" + "="*60)
    print("持仓查询测试")
    print("="*60)

    print("\n查询持仓信息...")
    positions = await api.get_positions()

    if positions:
        print(f"\n✅ 当前持仓 ({len(positions)}只):")
        for pos in positions:
            print(f"\n   {pos.symbol}:")
            print(f"     数量: {pos.quantity}")
            print(f"     平均成本: ${pos.average_price:.2f}")
            print(f"     当前价格: ${pos.current_price:.2f}")
            print(f"     市值: ${pos.market_value:,.2f}")
            print(f"     未实现损益: ${pos.unrealized_pnl:.2f}")
    else:
        print("\n✅ 当前无持仓")


async def test_futu_orders(api: FutuTradingAPI):
    """测试获取订单"""
    print("\n" + "="*60)
    print("订单查询测试")
    print("="*60)

    print("\n查询订单信息...")
    orders = await api.get_orders()

    if orders:
        print(f"\n✅ 当前订单 ({len(orders)}笔):")
        for order in orders:
            print(f"\n   订单ID: {order.order_id}")
            print(f"   股票: {order.symbol}")
            print(f"   方向: {order.side.value}")
            print(f"   数量: {order.quantity}")
            print(f"   价格: ${order.price:.2f}" if order.price else "   价格: 市价")
            print(f"   状态: {order.status.value}")
            print(f"   已成交: {order.filled_quantity}")
            print(f"   平均成交价: ${order.average_fill_price:.2f}" if order.average_fill_price else "   平均成交价: N/A")
    else:
        print("\n✅ 当前无订单")


async def test_futu_place_order(api: FutuTradingAPI):
    """测试下单"""
    print("\n" + "="*60)
    print("下单测试 (DEMO环境)")
    print("="*60)

    print("\n⚠️  警告：将在DEMO环境执行模拟交易")
    print("   这不会使用真实资金，仅用于测试")

    # 确认继续
    print("\n是否继续？(y/N): ", end='')
    try:
        confirm = input()
        if confirm.lower() != 'y':
            print("已取消下单测试")
            return None
    except:
        print("已取消下单测试")
        return None

    print("\n准备下单...")

    # 创建限价买单
    print("\n创建限价买单 (00700.HK)...")
    buy_order = Order(
        order_id=f"BUY_{int(asyncio.get_event_loop().time())}",
        symbol="00700.HK",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal('100'),  # 100股
        price=Decimal('400.0')  # 限价400港元
    )

    print(f"   订单信息:")
    print(f"   股票: {buy_order.symbol}")
    print(f"   方向: 买入")
    print(f"   数量: {buy_order.quantity}")
    print(f"   价格: ${buy_order.price}")

    # 下单
    print("\n正在下单...")
    order_id = await api.place_order(buy_order)

    if order_id:
        print(f"\n✅ 下单成功!")
        print(f"   本地订单ID: {order_id}")

        # 等待几秒
        print("\n等待订单处理...")
        await asyncio.sleep(3)

        # 查询订单状态
        print("\n查询订单状态...")
        status = await api.get_order_status(order_id)
        if status:
            print(f"   订单状态: {status.value}")
        else:
            print("   无法获取订单状态")

        return order_id
    else:
        print("\n❌ 下单失败")
        print("   可能原因:")
        print("   1. DEMO账户余额不足")
        print("   2. 价格无效")
        print("   3. 市场未开盘")
        return None


async def test_futu_cancel_order(api: FutuTradingAPI, order_id: str):
    """测试取消订单"""
    print("\n" + "="*60)
    print("取消订单测试")
    print("="*60)

    if not order_id:
        print("\n❌ 无有效订单可取消")
        return

    print(f"\n准备取消订单: {order_id}")
    print("确认取消？(y/N): ", end='')
    try:
        confirm = input()
        if confirm.lower() != 'y':
            print("已取消")
            return
    except:
        print("已取消")
        return

    # 取消订单
    success = await api.cancel_order(order_id)

    if success:
        print(f"\n✅ 取消成功: {order_id}")
    else:
        print(f"\n❌ 取消失败: {order_id}")


async def test_futu_health_check(api: FutuTradingAPI):
    """测试健康检查"""
    print("\n" + "="*60)
    print("健康检查")
    print("="*60)

    print("\n执行健康检查...")
    health = await api.health_check()

    print(f"\n✅ 健康状态:")
    print(json.dumps(health, indent=2, default=str))


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("富途牛牛API真实交易测试 (DEMO环境)")
    print("="*60)
    print("\n前置要求:")
    print("1. 安装富途API: pip install futu-api")
    print("2. 启动FutuOpenD网关客户端")
    print("3. 配置DEMO账户")
    print("4. 连接地址: 127.0.0.1:11111")

    api = None

    try:
        # 测试连接
        api = await test_futu_connection()
        if not api:
            print("\n❌ 连接失败，测试终止")
            return

        # 测试账户信息
        await test_futu_account_info(api)

        # 测试市场数据
        await test_futu_market_data(api)

        # 测试持仓
        await test_futu_positions(api)

        # 测试订单
        await test_futu_orders(api)

        # 测试下单
        order_id = await test_futu_place_order(api)

        # 测试取消订单
        await test_futu_cancel_order(api, order_id)

        # 健康检查
        await test_futu_health_check(api)

        print("\n" + "="*60)
        print("测试完成!")
        print("="*60)

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if api:
            print("\n正在断开连接...")
            await api.disconnect()
            print("已断开连接")


if __name__ == "__main__":
    asyncio.run(main())
