"""
富途牛牛模拟交易控制器

基于现有 FutuTradingAPI 实现统一的模拟交易管理系统
提供完整的交易流程管理、信号处理和实时监控功能
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from decimal import Decimal
import json

from .futu_trading_api import FutuTradingAPI, create_futu_trading_api
from .paper_trading_engine import PaperTradingEngine
from .base_trading_api import Order, OrderStatus, Position, AccountInfo
from .realtime_execution_engine import TradeSignal, ExecutionStrategy


class TradingControllerConfig:
    """交易控制器配置"""

    def __init__(
        self,
        initial_balance: Decimal = Decimal('1000000'),
        max_position_size: Decimal = Decimal('100000'),
        max_daily_trades: int = 100,
        trading_enabled: bool = True,
        commission_rate: Decimal = Decimal('0.001'),
        min_commission: Decimal = Decimal('10'),
        emergency_stop: bool = False
    ):
        self.initial_balance = initial_balance
        self.max_position_size = max_position_size
        self.max_daily_trades = max_daily_trades
        self.trading_enabled = trading_enabled
        self.commission_rate = commission_rate
        self.min_commission = min_commission
        self.emergency_stop = emergency_stop


class FutuPaperTradingController:
    """
    富途模拟交易控制器

    负责管理整个模拟交易流程，包括：
    - 交易状态管理
    - 信号处理和验证
    - 订单执行协调
    - 实时监控
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("hk_quant_system.futu_paper_trading")

        # 富途API配置
        self.futu_config = config.get('futu', {})
        self.auth_config = config.get('auth', {})

        # 交易控制器配置
        self.trading_config = TradingControllerConfig(**config.get('trading', {}))

        # 组件初始化
        self.futu_api: Optional[FutuTradingAPI] = None
        self.engine: Optional[PaperTradingEngine] = None

        # 状态管理
        self._initialized = False
        self._running = False
        self._stopped = False

        # 统计信息
        self.stats = {
            'total_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'total_commission': Decimal('0'),
            'start_time': None,
            'last_trade_time': None
        }

        # 回调函数
        self.on_trade_executed: Optional[Callable] = None
        self.on_order_status_change: Optional[Callable] = None
        self.on_position_change: Optional[Callable] = None
        self.on_error: Optional[Callable] = None

        self.logger.info("FutuPaperTradingController 已创建")

    async def initialize(self) -> bool:
        """
        初始化模拟交易控制器

        Returns:
            bool: 初始化是否成功
        """
        try:
            self.logger.info("=" * 60)
            self.logger.info("初始化富途模拟交易控制器")
            self.logger.info("=" * 60)

            # 1. 创建富途API实例
            self.logger.info("步骤 1/4: 创建富途API实例...")
            self.futu_api = create_futu_trading_api(
                host=self.futu_config.get('host', '127.0.0.1'),
                port=self.futu_config.get('port', 11111),
                trade_password=self.futu_config.get('trade_password', ''),
                market=self.futu_config.get('market', 'HK')
            )

            # 2. 连接富途API
            self.logger.info("步骤 2/4: 连接到富途DEMO环境...")
            if not await self.futu_api.connect():
                raise Exception("富途API连接失败")

            # 3. 身份验证
            self.logger.info("步骤 3/4: 解锁交易接口...")
            auth_success = await self.futu_api.authenticate(self.auth_config)
            if not auth_success:
                raise Exception("富途API认证失败")

            # 4. 创建模拟交易引擎
            self.logger.info("步骤 4/4: 初始化模拟交易引擎...")
            self.engine = PaperTradingEngine(
                futu_api=self.futu_api,
                initial_balance=self.trading_config.initial_balance,
                commission_rate=self.trading_config.commission_rate,
                min_commission=self.trading_config.min_commission
            )
            await self.engine.initialize()

            # 设置回调
            await self._setup_callbacks()

            self._initialized = True
            self.stats['start_time'] = datetime.now()

            self.logger.info("=" * 60)
            self.logger.info("✅ 富途模拟交易控制器初始化完成")
            self.logger.info(f"   初始资金: {self.trading_config.initial_balance:,.2f} HKD")
            self.logger.info(f"   最大仓位: {self.trading_config.max_position_size:,.2f} HKD")
            self.logger.info(f"   最大日交易次数: {self.trading_config.max_daily_trades}")
            self.logger.info("=" * 60)

            return True

        except Exception as e:
            self.logger.error(f"❌ 初始化失败: {e}", exc_info=True)
            await self.cleanup()
            return False

    async def _setup_callbacks(self):
        """设置引擎回调函数"""
        if self.engine:
            # 设置交易执行回调
            self.engine.on_trade_executed = self._handle_trade_executed
            self.engine.on_order_status_change = self._handle_order_status_change
            self.engine.on_position_change = self._handle_position_change

    async def _handle_trade_executed(self, trade_data: Dict[str, Any]):
        """处理交易执行事件"""
        self.stats['total_trades'] += 1
        self.stats['last_trade_time'] = datetime.now()

        if trade_data.get('success', False):
            self.stats['successful_trades'] += 1
            self.stats['total_commission'] += trade_data.get('commission', Decimal('0'))
        else:
            self.stats['failed_trades'] += 1

        self.logger.info(f"交易执行: {trade_data}")

        if self.on_trade_executed:
            await self.on_trade_executed(trade_data)

    async def _handle_order_status_change(self, order_data: Dict[str, Any]):
        """处理订单状态变更"""
        if self.on_order_status_change:
            await self.on_order_status_change(order_data)

    async def _handle_position_change(self, position_data: Dict[str, Any]):
        """处理持仓变更"""
        if self.on_position_change:
            await self.on_position_change(position_data)

    async def start_trading(self) -> None:
        """
        启动交易系统

        开始处理交易信号，执行模拟交易
        """
        if not self._initialized:
            raise Exception("系统未初始化，请先调用 initialize()")

        if self._running:
            self.logger.warning("交易系统已在运行")
            return

        self.logger.info("🚀 启动富途模拟交易系统")

        self._running = True
        self._stopped = False

        # 启动引擎
        if self.engine:
            await self.engine.start()

        self.logger.info("✅ 交易系统已启动")

    async def stop_trading(self) -> None:
        """
        停止交易系统

        取消所有待执行订单，停止处理新信号
        """
        if not self._running:
            return

        self.logger.info("⏹️ 停止交易系统")

        self._running = False
        self._stopped = True

        # 停止引擎
        if self.engine:
            await self.engine.stop()

        self.logger.info("✅ 交易系统已停止")

    async def execute_signal(self, signal: TradeSignal) -> Dict[str, Any]:
        """
        执行交易信号

        Args:
            signal: 交易信号

        Returns:
            Dict[str, Any]: 执行结果
        """
        if not self._initialized or not self._running:
            return {
                'success': False,
                'error': '系统未初始化或未启动'
            }

        if self.trading_config.emergency_stop:
            return {
                'success': False,
                'error': '紧急停止模式已启用'
            }

        if not self.trading_config.trading_enabled:
            return {
                'success': False,
                'error': '交易功能已禁用'
            }

        try:
            # 设置默认执行策略
            if not hasattr(signal, 'strategy') or not signal.strategy:
                signal.strategy = ExecutionStrategy.IMMEDIATE

            self.logger.info(f"📊 收到交易信号: {signal.symbol} {signal.side} {signal.quantity}")

            # 检查日交易次数限制
            if self.engine and self.engine.get_daily_trade_count() >= self.trading_config.max_daily_trades:
                return {
                    'success': False,
                    'error': f'超过日交易次数限制 ({self.trading_config.max_daily_trades})'
                }

            # 通过引擎执行交易
            result = await self.engine.execute_signal(signal)

            return result

        except Exception as e:
            self.logger.error(f"执行交易信号失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    async def emergency_stop(self) -> bool:
        """
        紧急停止所有交易

        Returns:
            bool: 是否成功执行
        """
        try:
            self.logger.warning("⚠️ 执行紧急停止！")

            self.trading_config.emergency_stop = True
            self.trading_config.trading_enabled = False

            # 取消所有待执行订单
            if self.engine:
                await self.engine.cancel_all_orders()

            # 停止交易
            await self.stop_trading()

            self.logger.warning("✅ 紧急停止执行完成")
            return True

        except Exception as e:
            self.logger.error(f"紧急停止失败: {e}", exc_info=True)
            return False

    async def unlock_trading(self) -> bool:
        """
        解锁交易功能

        Returns:
            bool: 是否成功解锁
        """
        try:
            self.logger.info("🔓 解锁交易功能")

            self.trading_config.emergency_stop = False
            self.trading_config.trading_enabled = True

            if self._initialized and not self._running:
                await self.start_trading()

            self.logger.info("✅ 交易功能已解锁")
            return True

        except Exception as e:
            self.logger.error(f"解锁交易功能失败: {e}", exc_info=True)
            return False

    async def get_status(self) -> Dict[str, Any]:
        """
        获取交易状态

        Returns:
            Dict[str, Any]: 状态信息
        """
        account_info = None
        positions = []
        if self.engine:
            account_info = await self.engine.get_account_info()
            positions = await self.engine.get_positions()

        return {
            'initialized': self._initialized,
            'running': self._running,
            'emergency_stop': self.trading_config.emergency_stop,
            'trading_enabled': self.trading_config.trading_enabled,
            'account': account_info.dict() if account_info else None,
            'positions': [p.dict() for p in positions],
            'stats': {
                **self.stats,
                'daily_trade_count': self.engine.get_daily_trade_count() if self.engine else 0
            },
            'config': {
                'initial_balance': str(self.trading_config.initial_balance),
                'max_position_size': str(self.trading_config.max_position_size),
                'max_daily_trades': self.trading_config.max_daily_trades
            },
            'futu_api_status': await self.futu_api.health_check() if self.futu_api else None,
            'last_updated': datetime.now().isoformat()
        }

    async def get_orders(self, status_filter: Optional[OrderStatus] = None) -> List[Order]:
        """
        获取订单列表

        Args:
            status_filter: 订单状态过滤

        Returns:
            List[Order]: 订单列表
        """
        if not self.engine:
            return []

        return await self.engine.get_orders(status_filter)

    async def cancel_order(self, order_id: str) -> bool:
        """
        取消订单

        Args:
            order_id: 订单ID

        Returns:
            bool: 是否成功取消
        """
        if not self.engine:
            return False

        return await self.engine.cancel_order(order_id)

    async def reset_account(self, balance: Optional[Decimal] = None) -> bool:
        """
        重置模拟账户

        Args:
            balance: 新的初始余额，默认使用配置中的值

        Returns:
            bool: 是否成功重置
        """
        try:
            new_balance = balance or self.trading_config.initial_balance

            self.logger.info(f"🔄 重置模拟账户，新余额: {new_balance:,.2f} HKD")

            if self.engine:
                await self.engine.reset_account(new_balance)

            # 重置统计
            self.stats = {
                'total_trades': 0,
                'successful_trades': 0,
                'failed_trades': 0,
                'total_commission': Decimal('0'),
                'start_time': datetime.now(),
                'last_trade_time': None
            }

            self.logger.info("✅ 账户重置完成")
            return True

        except Exception as e:
            self.logger.error(f"重置账户失败: {e}", exc_info=True)
            return False

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        获取性能指标

        Returns:
            Dict[str, Any]: 性能指标
        """
        if not self.engine:
            return {}

        return await self.engine.get_performance_metrics()

    async def cleanup(self) -> None:
        """清理资源"""
        try:
            self.logger.info("清理模拟交易控制器资源...")

            await self.stop_trading()

            if self.engine:
                await self.engine.cleanup()
                self.engine = None

            if self.futu_api:
                await self.futu_api.disconnect()
                self.futu_api = None

            self._initialized = False

            self.logger.info("✅ 资源清理完成")

        except Exception as e:
            self.logger.error(f"清理资源失败: {e}", exc_info=True)

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.cleanup()


# 便捷函数：创建模拟交易控制器
def create_paper_trading_controller(
    futu_host: str = '127.0.0.1',
    futu_port: int = 11111,
    trade_password: str = '',
    market: str = 'HK',
    initial_balance: Decimal = Decimal('1000000'),
    max_position_size: Decimal = Decimal('100000'),
    max_daily_trades: int = 100
) -> FutuPaperTradingController:
    """
    创建富途模拟交易控制器实例

    Args:
        futu_host: 富途API主机
        futu_port: 富途API端口
        trade_password: 交易密码
        market: 市场 (HK/US/CN)
        initial_balance: 初始资金
        max_position_size: 最大仓位
        max_daily_trades: 最大日交易次数

    Returns:
        FutuPaperTradingController: 控制器实例
    """
    config = {
        'futu': {
            'host': futu_host,
            'port': futu_port,
            'trade_password': trade_password,
            'market': market
        },
        'auth': {
            'trade_password': trade_password
        },
        'trading': {
            'initial_balance': initial_balance,
            'max_position_size': max_position_size,
            'max_daily_trades': max_daily_trades
        }
    }

    return FutuPaperTradingController(config)
