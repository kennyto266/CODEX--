"""
富途API集成 - 真实交易执行系统

使用富途牛牛API进行真实交易（DEMO环境）
集成到现有交易执行引擎中

⚠️ 重要提示：
- 本系统使用DEMO环境 (SIMULATE)
- 使用模拟资金，不会造成真实损失
- 适合策略验证和测试
"""

import asyncio
import logging
import sys
sys.path.append('.')

from futu_trading_api import FutuTradingAPI
from realtime_execution_engine import RealtimeExecutionEngine, TradeSignal, ExecutionStrategy, OrderSide
from signal_generator import SignalManager, SignalConfig
from base_trading_api import Order, OrderType, OrderSide
from decimal import Decimal
import json


class FutuLiveTradingSystem:
    """富途真实交易系统"""

    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger("hk_quant_system.futu_live_trading")

        # 初始化富途API
        self.futu_api = FutuTradingAPI(config.get('futu', {}))
        self.execution_engine = None
        self.signal_manager = None

        self.is_running = False

    async def initialize(self):
        """初始化系统"""
        try:
            self.logger.info("初始化富途交易系统...")

            # 连接富途API
            self.logger.info("连接富途API...")
            await self.futu_api.connect()
            self.logger.info("富途API连接成功")

            # 认证
            self.logger.info("解锁交易接口...")
            auth_config = self.config.get('auth', {})
            success = await self.futu_api.authenticate(auth_config)
            if not success:
                raise Exception("富途API认证失败")

            # 初始化执行引擎
            self.execution_engine = RealtimeExecutionEngine(
                config={
                    'primary_api': 'futu',
                    'risk': self.config.get('risk', {})
                }
            )

            await self.execution_engine.add_trading_api('futu', self.futu_api)
            await self.execution_engine.start()
            self.logger.info("执行引擎启动成功")

            # 初始化信号管理器
            self.signal_manager = SignalManager()
            self.logger.info("信号管理器初始化完成")

            self.logger.info("富途交易系统初始化完成")
            return True

        except Exception as e:
            self.logger.error(f"初始化失败: {e}")
            await self.cleanup()
            return False

    async def add_signal_config(self, config: SignalConfig):
        """添加信号配置"""
        if self.signal_manager:
            await self.signal_manager.add_signal_config(config)
            self.logger.info(f"添加信号配置: {config.symbol} {config.strategy}")

    async def start_trading(self, enable_auto_trading: bool = True):
        """启动交易系统"""
        try:
            if not self.execution_engine or not self.signal_manager:
                raise Exception("系统未初始化")

            self.is_running = True
            self.logger.info(f"启动交易系统 (自动交易: {enable_auto_trading})")

            # 主交易循环
            trade_count = 0
            cycle = 0

            while self.is_running:
                cycle += 1
                self.logger.info(f"交易周期 {cycle}")

                try:
                    # 1. 扫描交易信号
                    signals = await self.signal_manager.scan_signals()

                    if signals:
                        self.logger.info(f"发现 {len(signals)} 个交易信号")

                        for signal in signals:
                            # 2. 执行交易信号
                            if enable_auto_trading:
                                order_id = await self.execution_engine.execute_signal(signal)

                                if order_id:
                                    trade_count += 1
                                    self.logger.info(
                                        f"交易执行成功 #{trade_count}: "
                                        f"{signal.symbol} {signal.side.value} -> 订单 {order_id}"
                                    )

                                    # 等待订单处理
                                    await asyncio.sleep(2)

                                    # 查看订单状态
                                    status = await self.execution_engine.get_order_status(order_id)
                                    if status:
                                        self.logger.info(f"订单状态: {status}")

                                else:
                                    self.logger.warning(f"交易执行失败: {signal.symbol} {signal.side.value}")
                            else:
                                # 仅显示信号，不执行交易
                                self.logger.info(
                                    f"交易信号: {signal.symbol} {signal.side.value} "
                                    f"(自动交易已禁用)"
                                )

                    # 3. 显示投资组合摘要
                    portfolio = await self.execution_engine.get_portfolio_summary()
                    if portfolio:
                        account = portfolio.get('account', {})
                        positions = portfolio.get('positions', [])

                        self.logger.info(
                            f"投资组合: 现金=${account.get('cash', 0):,.2f}, "
                            f"权益=${account.get('equity', 0):,.2f}, "
                            f"持仓={len(positions)}只"
                        )

                    # 4. 等待下一周期
                    await asyncio.sleep(self.config.get('scan_interval', 60))

                except Exception as e:
                    self.logger.error(f"交易周期错误: {e}")
                    await asyncio.sleep(10)

            self.logger.info(f"交易系统已停止 (总交易次数: {trade_count})")

        except Exception as e:
            self.logger.error(f"交易系统错误: {e}")
            self.is_running = False

    async def stop_trading(self):
        """停止交易系统"""
        self.logger.info("正在停止交易系统...")
        self.is_running = False

        if self.execution_engine:
            await self.execution_engine.stop()

        self.logger.info("交易系统已停止")

    async def cleanup(self):
        """清理资源"""
        self.logger.info("清理资源...")

        if self.execution_engine:
            await self.execution_engine.stop()

        if self.futu_api:
            await self.futu_api.disconnect()

        self.logger.info("资源清理完成")

    async def get_status(self) -> dict:
        """获取系统状态"""
        status = {
            'running': self.is_running,
            'futu_connected': self.futu_api._connected if self.futu_api else False,
            'futu_authenticated': self.futu_api._authenticated if self.futu_api else False,
            'execution_engine_running': self.execution_engine.is_running if self.execution_engine else False
        }

        # 获取富途API健康状态
        if self.futu_api:
            health = await self.futu_api.health_check()
            status['futu_health'] = health

        # 获取执行引擎状态
        if self.execution_engine:
            metrics = await self.execution_engine.get_performance_metrics()
            status['execution_metrics'] = metrics

        # 获取账户信息
        if self.futu_api:
            account = await self.futu_api.get_account_info()
            if account:
                status['account'] = {
                    'id': account.account_id,
                    'cash': float(account.cash),
                    'equity': float(account.equity),
                    'buying_power': float(account.buying_power)
                }

        return status

    async def manual_trade(self, symbol: str, side: str, quantity: int, price: float = None):
        """手动交易"""
        try:
            self.logger.info(f"手动交易: {symbol} {side} {quantity} @ {price or '市价'}")

            order = Order(
                order_id=f"MANUAL_{int(asyncio.get_event_loop().time())}",
                symbol=symbol,
                side=OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL,
                order_type=OrderType.LIMIT if price else OrderType.MARKET,
                quantity=Decimal(str(quantity)),
                price=Decimal(str(price)) if price else None
            )

            order_id = await self.futu_api.place_order(order)

            if order_id:
                self.logger.info(f"手动下单成功: {order_id}")
                return order_id
            else:
                self.logger.error("手动下单失败")
                return None

        except Exception as e:
            self.logger.error(f"手动交易错误: {e}")
            return None

    async def get_portfolio(self) -> dict:
        """获取投资组合"""
        try:
            if not self.execution_engine:
                return {}

            return await self.execution_engine.get_portfolio_summary()

        except Exception as e:
            self.logger.error(f"获取投资组合失败: {e}")
            return {}


async def main():
    """主函数 - 演示如何使用"""
    # 配置
    config = {
        'futu': {
            'host': '127.0.0.1',
            'port': 11111,
            'market': 'HK',
            'trade_password': '123456'  # DEMO密码
        },
        'auth': {
            'trade_password': '123456'
        },
        'risk': {
            'max_position_size': 500000,
            'max_daily_loss': 50000,
            'max_order_size': 100000,
            'min_cash_reserve': 10000
        },
        'scan_interval': 60,  # 扫描间隔60秒
        'auto_trading': False  # 禁用自动交易，仅演示
    }

    # 创建交易系统
    trading_system = FutuLiveTradingSystem(config)

    try:
        # 初始化
        print("\n初始化富途交易系统...")
        if not await trading_system.initialize():
            print("初始化失败")
            return

        print("✅ 初始化成功")

        # 添加信号配置
        await trading_system.add_signal_config(
            SignalConfig('00700.HK', 'rsi', {
                'period': 14,
                'oversold': 30,
                'overbought': 70
            })
        )

        await trading_system.add_signal_config(
            SignalConfig('0388.HK', 'macd', {
                'fast': 12,
                'slow': 26,
                'signal': 9
            })
        )

        print("✅ 信号配置已添加")

        # 显示系统状态
        print("\n系统状态:")
        status = await trading_system.get_status()
        print(json.dumps(status, indent=2, default=str))

        # 演示手动交易
        print("\n演示手动交易...")
        order_id = await trading_system.manual_trade(
            symbol='00700.HK',
            side='buy',
            quantity=100,
            price=400.0
        )

        if order_id:
            print(f"✅ 手动下单成功: {order_id}")

            # 等待几秒
            await asyncio.sleep(3)

            # 查询订单状态
            if trading_system.execution_engine:
                status = await trading_system.execution_engine.get_order_status(order_id)
                print(f"订单状态: {status}")

        # 获取投资组合
        print("\n投资组合:")
        portfolio = await trading_system.get_portfolio()
        print(json.dumps(portfolio, indent=2, default=str))

        # 演示自动交易（可选）
        print("\n是否启动自动交易？(y/N): ", end='')
        try:
            confirm = input()
            if confirm.lower() == 'y':
                print("\n启动自动交易 (按Ctrl+C停止)...")
                await trading_system.start_trading(enable_auto_trading=True)
        except:
            print("已跳过自动交易")

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n正在停止系统...")
        await trading_system.cleanup()
        print("系统已停止")


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    asyncio.run(main())
