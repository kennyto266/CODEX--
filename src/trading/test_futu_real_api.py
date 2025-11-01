"""
富途API真实环境测试 - 使用用户API凭证

⚠️ 权限说明：
- 当前权限：港股LV1
- 可用功能：实时行情、历史数据
- 不可用功能：交易下单（需LV3以上）
"""

import asyncio
import sys
sys.path.append('.')

from futu_trading_api import FutuTradingAPI, create_futu_trading_api
from futu_config import FUTU_CONFIG, PERMISSION_INFO, SUPPORTED_HK_SYMBOLS, QUICK_START


async def show_permission_info():
    """显示权限信息"""
    print("\n" + "="*60)
    print("富途API权限信息")
    print("="*60)

    print(f"\n📋 用户信息:")
    print(f"   牛牛号: {FUTU_CONFIG['user_id']}")
    print(f"   API端口: {FUTU_CONFIG['port']}")
    print(f"   WebSocket端口: {FUTU_CONFIG['websocket_port']}")

    print(f"\n🔑 权限详情:")
    for key, perm in PERMISSION_INFO.items():
        status = "✅" if perm['enabled'] else "❌"
        trading = "✅" if perm.get('trading_enabled', False) else "❌"
        print(f"\n   {status} {perm['name']} ({perm['level']}):")
        print(f"      功能: {perm['description']}")
        print(f"      交易权限: {trading}")
        if not perm.get('trading_enabled', False):
            print(f"      升级需求: 需要{perm['required_level']}")

    print("\n" + QUICK_START)


async def test_real_api_connection():
    """测试真实API连接"""
    print("\n" + "="*60)
    print("富途API真实连接测试")
    print("="*60)

    # 创建富途API实例（使用真实配置）
    print("\n1. 创建富途API实例（使用真实配置）...")
    api = create_futu_trading_api(
        host=FUTU_CONFIG['host'],
        port=FUTU_CONFIG['port'],
        market=FUTU_CONFIG['market']
    )
    print("   ✓ API实例已创建")
    print(f"     主机: {FUTU_CONFIG['host']}:{FUTU_CONFIG['port']}")
    print(f"     市场: {FUTU_CONFIG['market']}")

    # 连接
    print("\n2. 连接到富途API...")
    try:
        await api.connect()
        print("   ✅ 连接成功")
    except Exception as e:
        print(f"   ❌ 连接失败: {e}")
        print("\n   请检查:")
        print("   1. FutuOpenD客户端是否已启动")
        print("   2. 是否使用牛牛号2860386登录")
        print("   3. API端口11111是否开放")
        return None

    return api


async def test_market_data(api: FutuTradingAPI):
    """测试获取市场数据"""
    print("\n" + "="*60)
    print("市场数据获取测试")
    print("="*60)

    # 测试几个热门港股
    test_symbols = ['00700.HK', '0388.HK', '1398.HK']

    for symbol in test_symbols:
        print(f"\n获取 {symbol} ({SUPPORTED_HK_SYMBOLS.get(symbol, 'Unknown')}) 的市场数据...")
        try:
            market_data = await api.get_market_data(symbol)

            if market_data:
                print(f"\n✅ {symbol} 市场数据:")
                print(f"   最新价: ${market_data.last_price:.2f}")
                print(f"   买入价: ${market_data.bid_price:.2f}")
                print(f"   卖出价: ${market_data.ask_price:.2f}")
                print(f"   买卖价差: ${(market_data.ask_price - market_data.bid_price):.2f}")
                print(f"   成交量: {market_data.volume:,}")
                print(f"   开盘价: ${market_data.open_price:.2f}")
                print(f"   最高价: ${market_data.high_price:.2f}")
                print(f"   最低价: ${market_data.low_price:.2f}")
                print(f"   数据时间: {market_data.timestamp}")
            else:
                print(f"   ❌ 获取数据失败")

        except Exception as e:
            print(f"   ❌ 获取数据异常: {e}")


async def test_historical_data(api: FutuTradingAPI):
    """测试获取历史数据"""
    print("\n" + "="*60)
    print("历史数据获取测试")
    print("="*60)

    symbol = '00700.HK'
    print(f"\n获取 {symbol} (腾讯控股) 最近30天历史数据...")

    try:
        from datetime import datetime, timedelta

        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        historical_data = await api.get_historical_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval='1d'
        )

        if historical_data:
            print(f"\n✅ 成功获取 {len(historical_data)} 条历史数据")
            print("\n最新5天数据:")
            for i, data in enumerate(historical_data[-5:], 1):
                print(f"   {i}. {data['timestamp']}: "
                      f"O=${data['open']:.2f} H=${data['high']:.2f} "
                      f"L=${data['low']:.2f} C=${data['close']:.2f} "
                      f"V={data['volume']:,}")

            # 计算统计信息
            closes = [d['close'] for d in historical_data]
            avg_price = sum(closes) / len(closes)
            max_price = max(closes)
            min_price = min(closes)

            print(f"\n📊 统计信息 (30天):")
            print(f"   平均价格: ${avg_price:.2f}")
            print(f"   最高价格: ${max_price:.2f}")
            print(f"   最低价格: ${min_price:.2f}")
            print(f"   价格波动: ${max_price - min_price:.2f} ({(max_price - min_price)/avg_price*100:.2f}%)")
        else:
            print("   ❌ 获取历史数据失败")

    except Exception as e:
        print(f"   ❌ 获取历史数据异常: {e}")


async def test_trading_functions(api: FutuTradingAPI):
    """测试交易功能（预期失败）"""
    print("\n" + "="*60)
    print("交易功能测试 (预期LV1权限不足)")
    print("="*60)

    # 尝试获取账户信息（交易相关功能）
    print("\n1. 尝试查询账户信息...")
    try:
        account = await api.get_account_info()
        if account:
            print(f"   ✅ 账户信息: {account.account_id}")
        else:
            print("   ❌ 无法获取账户信息")
            print("      (LV1权限可能不支持交易相关功能)")
    except Exception as e:
        print(f"   ❌ 查询失败: {e}")
        print("      (LV1权限不足以访问交易功能)")

    # 尝试解锁交易
    print("\n2. 尝试解锁交易接口...")
    try:
        success = await api.authenticate({'trade_password': '123456'})
        if success:
            print("   ✅ 解锁成功")
        else:
            print("   ❌ 解锁失败")
            print("      (LV1权限可能不支持交易解锁)")
    except Exception as e:
        print(f"   ❌ 解锁失败: {e}")
        print("      (LV1权限不足以解锁交易)")


async def show_trading_guide():
    """显示交易功能升级指南"""
    print("\n" + "="*60)
    print("交易功能升级指南")
    print("="*60)

    print("\n📌 当前状态:")
    print("   ✅ 港股LV1权限 - 可获取实时行情和历史数据")
    print("   ❌ 无交易权限 - 无法下单和查询订单")

    print("\n💡 升级到交易权限的步骤:")
    print("   1. 在富途牛牛APP中点击【我的】")
    print("   2. 点击【行情权限】或【交易权限】")
    print("   3. 申请开通港股LV3或以上权限")
    print("   4. 完成资金验证和风险评估")
    print("   5. 等待审核通过（通常1-2个工作日）")

    print("\n💰 升级后的功能:")
    print("   ✅ 港股实时交易")
    print("   ✅ 订单查询和管理")
    print("   ✅ 持仓查询")
    print("   ✅ 资金查询")
    print("   ✅ 盈亏统计")

    print("\n📞 如需帮助:")
    print("   - 富途牛牛APP内在线咨询")
    print("   - 客服电话: 400-869-5500")
    print("   - OpenAPI群: 229850364")


async def test_all_supported_symbols(api: FutuTradingAPI):
    """测试所有支持的港股代码"""
    print("\n" + "="*60)
    print("批量市场数据测试")
    print("="*60)

    print(f"\n测试 {len(SUPPORTED_HK_SYMBOLS)} 只港股的市场数据...")

    success_count = 0
    failed_count = 0

    for symbol, name in SUPPORTED_HK_SYMBOLS.items():
        try:
            market_data = await api.get_market_data(symbol)
            if market_data:
                success_count += 1
                print(f"   ✅ {symbol:10} {name:20} ${market_data.last_price:8.2f}")
            else:
                failed_count += 1
                print(f"   ❌ {symbol:10} {name:20} 暂无数据")
        except Exception as e:
            failed_count += 1
            print(f"   ❌ {symbol:10} {name:20} 错误: {str(e)[:30]}")

        # 避免请求过快
        await asyncio.sleep(0.1)

    print(f"\n📊 测试结果:")
    print(f"   成功: {success_count}/{len(SUPPORTED_HK_SYMBOLS)}")
    print(f"   失败: {failed_count}/{len(SUPPORTED_HK_SYMBOLS)}")
    print(f"   成功率: {success_count/len(SUPPORTED_HK_SYMBOLS)*100:.1f}%")


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("富途API真实环境测试")
    print("牛牛号: 2860386")
    print("="*60)

    # 显示权限信息
    await show_permission_info()

    api = None

    try:
        # 测试连接
        api = await test_real_api_connection()
        if not api:
            print("\n❌ 连接失败，测试终止")
            return

        # 测试市场数据
        await test_market_data(api)

        # 测试历史数据
        await test_historical_data(api)

        # 测试交易功能（预期失败）
        await test_trading_functions(api)

        # 批量测试
        await test_all_supported_symbols(api)

        # 显示升级指南
        await show_trading_guide()

        print("\n" + "="*60)
        print("测试完成！")
        print("="*60)
        print("\n✅ 当前可用的功能:")
        print("   - 实时行情获取")
        print("   - 历史数据查询")
        print("   - 市场数据批量获取")
        print("\n⚠️  暂不可用的功能:")
        print("   - 交易下单")
        print("   - 订单查询")
        print("   - 账户资金查询")
        print("\n💡 升级到LV3权限后可解锁交易功能")

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
