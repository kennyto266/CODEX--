"""
富途API WebSocket实时数据推送演示

使用用户的WebSocket凭证实现实时行情推送
- WebSocket端口: 33333
- WebSocket密钥: fc724f767796db1f
"""

import asyncio
import sys
sys.path.append('.')

# 尝试导入富途API
try:
    import futu as ft
    from futu import *

    class StockQuoteHandler(StockQuoteHandlerBase):
        """行情推送处理器"""
        def on_recv_rsp(self, rsp_pb):
            """接收推送数据"""
            try:
                ret_code, data = super().on_recv_rsp(rsp_pb)
                if ret_code == RET_OK:
                    # 打印行情数据
                    print(f"\n📈 实时行情更新:")
                    for i, row in data.iterrows():
                        code = row['code']
                        name = row.get('name', code)
                        last_price = row['last_price']
                        change = row.get('change_pct', 0)
                        volume = row.get('volume', 0)

                        # 根据涨跌调整颜色
                        if change > 0:
                            arrow = "🔺"
                            color = "🟢"
                        elif change < 0:
                            arrow = "🔻"
                            color = "🔴"
                        else:
                            arrow = "➖"
                            color = "🟡"

                        print(f"   {color} {code} {name}: ${last_price:.2f} "
                              f"{arrow} {change:+.2f}% (成交量: {volume:,})")
                return ret_code, data
            except Exception as e:
                print(f"❌ 处理行情数据错误: {e}")
                return RET_ERROR, None

    class TickerHandler(TickerHandlerBase):
        """逐笔数据处理器"""
        def on_recv_rsp(self, rsp_pb):
            """接收推送数据"""
            try:
                ret_code, data = super().on_recv_rsp(rsp_pb)
                if ret_code == RET_OK:
                    # 打印逐笔数据
                    for i, row in data.iterrows():
                        code = row['code']
                        price = row['price']
                        volume = row['volume']
                        timestamp = row['timestamp']
                        print(f"   📊 逐笔: {code} ${price:.2f} x{volume} @ {timestamp}")
                return ret_code, data
            except Exception as e:
                print(f"❌ 处理逐笔数据错误: {e}")
                return RET_ERROR, None

    WEB_SOCKET_AVAILABLE = True
except ImportError:
    print("⚠️  富途API未安装，请运行: pip install futu-api")
    WEB_SOCKET_AVAILABLE = False

from futu_config import FUTU_CONFIG, SUPPORTED_HK_SYMBOLS


async def start_websocket_subscription():
    """启动WebSocket订阅"""
    if not WEB_SOCKET_AVAILABLE:
        print("❌ 富途API未安装，无法使用WebSocket功能")
        return

    print("\n" + "="*60)
    print("WebSocket实时数据推送演示")
    print("="*60)

    print(f"\n📋 配置信息:")
    print(f"   WebSocket端口: {FUTU_CONFIG['websocket_port']}")
    print(f"   WebSocket密钥: {FUTU_CONFIG['websocket_key']}")

    # 创建行情上下文
    quote_ctx = OpenQuoteContext(
        host=FUTU_CONFIG['host'],
        port=FUTU_CONFIG['websocket_port']
    )

    try:
        # 启动
        print(f"\n1. 启动WebSocket连接...")
        ret = quote_ctx.start()
        if ret == RET_OK:
            print("   ✅ WebSocket连接成功")
        else:
            print(f"   ❌ WebSocket连接失败: {ret}")
            return

        # 设置WebSocket密钥
        print(f"\n2. 设置WebSocket密钥...")
        ret, data = quote_ctx.set_web_socket_key(key=FUTU_CONFIG['websocket_key'])
        if ret == RET_OK:
            print("   ✅ WebSocket密钥设置成功")
        else:
            print(f"   ❌ WebSocket密钥设置失败: {data}")
            return

        # 选择订阅的股票
        test_symbols = ['00700.HK', '0388.HK', '1398.HK']
        print(f"\n3. 订阅股票: {', '.join(test_symbols)}")

        # 订阅实时行情
        for symbol in test_symbols:
            ret = quote_ctx.subscribe(code=symbol, subtype_list=[SubType.QUOTE, SubType.TICKER])
            if ret == RET_OK:
                print(f"   ✅ {symbol} 订阅成功")
            else:
                print(f"   ❌ {symbol} 订阅失败")

        # 设置回调处理器
        print(f"\n4. 设置数据处理器...")
        quote_ctx.set_handler(StockQuoteHandler())
        print("   ✅ 行情处理器已设置")

        print(f"\n5. 开始接收实时数据 (按Ctrl+C停止)...")
        print("   正在等待数据推送...")

        # 保持连接并接收数据
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断，正在停止...")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 停止WebSocket连接
        print("\n正在停止WebSocket连接...")
        quote_ctx.stop()
        quote_ctx.close()
        print("✅ WebSocket连接已关闭")


async def demo_snapshot_updates():
    """演示批量快照更新"""
    if not WEB_SOCKET_AVAILABLE:
        print("❌ 富途API未安装")
        return

    print("\n" + "="*60)
    print("批量快照更新演示")
    print("="*60)

    # 创建行情上下文
    quote_ctx = OpenQuoteContext(
        host=FUTU_CONFIG['host'],
        port=FUTU_CONFIG['port']
    )

    try:
        # 启动
        print(f"\n1. 启动行情接口...")
        ret = quote_ctx.start()
        if ret == RET_OK:
            print("   ✅ 行情接口启动成功")
        else:
            print(f"   ❌ 行情接口启动失败: {ret}")
            return

        # 批量获取快照
        symbols = list(SUPPORTED_HK_SYMBOLS.keys())[:10]  # 前10只股票
        print(f"\n2. 获取 {len(symbols)} 只股票快照...")

        for i in range(3):  # 每2秒更新一次，共3次
            print(f"\n📊 第 {i+1} 次更新 ({len(symbols)} 只股票):")

            ret, data = quote_ctx.get_market_snapshot(symbols)
            if ret == RET_OK:
                for _, row in data.iterrows():
                    code = row['code']
                    name = SUPPORTED_HK_SYMBOLS.get(code, 'Unknown')
                    last_price = row['last_price']
                    change = row.get('change_pct', 0)

                    # 格式化输出
                    if change > 0:
                        arrow = "🔺"
                    elif change < 0:
                        arrow = "🔻"
                    else:
                        arrow = "➖"

                    print(f"   {arrow} {code} {name[:15]:15} "
                          f"${last_price:8.2f} {change:+6.2f}%")
            else:
                print(f"   ❌ 获取快照失败: {data}")

            if i < 2:  # 最后一次不等待
                print(f"\n   等待2秒后更新...")
                await asyncio.sleep(2)

        print(f"\n✅ 演示完成")

    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        quote_ctx.close()
        print("✅ 行情接口已关闭")


async def show_websocket_guide():
    """显示WebSocket使用指南"""
    print("\n" + "="*60)
    print("WebSocket使用指南")
    print("="*60)

    print(f"\n💡 WebSocket实时数据推送特点:")
    print(f"   ✅ 低延迟: 数据实时推送")
    print(f"   ✅ 高频率: 毫秒级更新")
    print(f"   ✅ 多类型: 支持行情、逐笔、摆盘等")
    print(f"   ✅ 自动重连: 连接断开自动重连")

    print(f"\n📊 支持的推送类型:")
    print(f"   1. QUOTE - 实时行情 (最新价、涨跌幅等)")
    print(f"   2. TICKER - 逐笔数据 (每笔成交)")
    print(f" " * 10 + "3. K_DAY - 日K线数据")
    print(f" " * 10 + "4. ORDER_BOOK - 摆盘数据 (买卖盘)")
    print(f" " * 10 + "5. RT_DATA - 分时数据")
    print(f" " * 10 + "6. BROKER - 经纪队列")

    print(f"\n⚡ 订阅示例:")
    print(f"   quote_ctx.subscribe('00700.HK', [SubType.QUOTE, SubType.TICKER])")

    print(f"\n🛑 取消订阅:")
    print(f"   quote_ctx.unsubscribe('00700.HK', [SubType.QUOTE])")

    print(f"\n📝 注意事项:")
    print(f"   - 需要使用WebSocket端口 33333")
    print(f"   - 需要设置WebSocket密钥")
    print(f"   - 建议设置数据处理回调函数")
    print(f"   - 及时取消不需要的订阅以节省资源")


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("富途API WebSocket实时数据推送演示")
    print("="*60)

    print(f"\n🎯 当前功能:")
    print(f"   ✅ WebSocket实时数据推送")
    print(f"   ✅ 行情数据实时更新")
    print(f"   ✅ 逐笔数据推送")
    print(f"   ✅ 批量快照更新")

    # 显示使用指南
    await show_websocket_guide()

    print(f"\n" + "="*60)
    print("请选择演示模式:")
    print("="*60)
    print("1. WebSocket实时推送 (持续接收数据)")
    print("2. 批量快照更新 (定时获取快照)")
    print("3. 退出")

    try:
        choice = input("\n请输入选择 (1-3): ")
        if choice == '1':
            await start_websocket_subscription()
        elif choice == '2':
            await demo_snapshot_updates()
        elif choice == '3':
            print("\n已退出")
        else:
            print("\n❌ 无效选择")
    except KeyboardInterrupt:
        print("\n\n👋 已退出")
    except Exception as e:
        print(f"\n❌ 错误: {e}")


if __name__ == "__main__":
    asyncio.run(main())
