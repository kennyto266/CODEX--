"""
实时交易执行引擎 - 核心交易执行系统

负责：
- 实时订单执行
- 风险控制
- 交易信号处理
- 订单状态监控
- 性能统计
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum
import json

from .base_trading_api import (
    BaseTradingAPI, Order, OrderType, OrderSide, OrderStatus,
    Position, AccountInfo, MarketData
)


class ExecutionStrategy(str, Enum):
    """执行策略"""
    IMMEDIATE = "immediate"      # 立即执行
    BEST_PRICE = "best_price"    # 最优价格
    TWAP = "twap"               # 时间加权平均
    VWAP = "vwap"               # 成交量加权平均
    ICEBERG = "iceberg"         # 冰山订单
    SMART = "smart"             # 智能执行


@dataclass
class TradeSignal:
    """交易信号"""
    signal_id: str
    symbol: str
    side: OrderSide
    quantity: Decimal
    strategy: ExecutionStrategy
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionReport:
    """执行报告"""
    order_id: str
    symbol: str
    side: OrderSide
    quantity: Decimal
    filled_quantity: Decimal
    average_price: Decimal
    commission: Decimal
    timestamp: datetime = field(default_factory=datetime.now)
    status: OrderStatus = OrderStatus.FILLED
    execution_time_ms: int = 0
    slippage: Optional[Decimal] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class RiskManager:
    """风险管理器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("hk_quant_system.trading.risk")

        # 风险控制参数
        self.max_position_size = Decimal(str(config.get('max_position_size', 1000000)))
        self.max_daily_loss = Decimal(str(config.get('max_daily_loss', 50000)))
        self.max_order_size = Decimal(str(config.get('max_order_size', 100000)))
        self.min_cash_reserve = Decimal(str(config.get('min_cash_reserve', 10000)))

        # 实时统计
        self.daily_pnl = Decimal('0')
        self.current_positions: Dict[str, Position] = {}

    async def check_pre_trade_risk(self, signal: TradeSignal, account: AccountInfo) -> tuple[bool, str]:
        """
        预交易风险检查

        Returns:
            (是否通过, 错误信息)
        """
        try:
            # 1. 检查现金充足性
            required_cash = signal.quantity * (signal.price or Decimal('0'))
            if account.cash is not None and required_cash > (account.cash - self.min_cash_reserve):
                return False, f"现金不足: 需要 {required_cash}, 可用 {account.cash - self.min_cash_reserve}"

            # 2. 检查订单大小
            if signal.quantity > self.max_order_size:
                return False, f"订单过大: {signal.quantity} > {self.max_order_size}"

            # 3. 检查当前持仓
            current_pos = self.current_positions.get(signal.symbol, Position(
                symbol=signal.symbol,
                quantity=Decimal('0'),
                average_price=Decimal('0')
            ))

            new_quantity = current_pos.quantity
            if signal.side == OrderSide.BUY:
                new_quantity += signal.quantity
            elif signal.side == OrderSide.SELL:
                new_quantity -= signal.quantity

            if abs(new_quantity) > self.max_position_size:
                return False, f"持仓超限: {abs(new_quantity)} > {self.max_position_size}"

            # 4. 检查日内损失
            if self.daily_pnl < -self.max_daily_loss:
                return False, f"日内损失超限: {self.daily_pnl} < -{self.max_daily_loss}"

            return True, ""

        except Exception as e:
            self.logger.error(f"风险检查失败: {e}")
            return False, f"风险检查错误: {e}"

    def update_position(self, position: Position):
        """更新持仓信息"""
        self.current_positions[position.symbol] = position

    def update_daily_pnl(self, pnl: Decimal):
        """更新日内盈亏"""
        self.daily_pnl += pnl


class RealtimeExecutionEngine:
    """实时交易执行引擎"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("hk_quant_system.trading.execution")

        # 核心组件
        self.trading_apis: Dict[str, BaseTradingAPI] = {}
        self.risk_manager = RiskManager(config.get('risk', {}))
        self.primary_api = config.get('primary_api', 'paper_trading')
        self.active_orders: Dict[str, Order] = {}
        self.order_callbacks: List[Callable] = []

        # 性能统计
        self.execution_stats = {
            'total_orders': 0,
            'filled_orders': 0,
            'cancelled_orders': 0,
            'rejected_orders': 0,
            'avg_execution_time_ms': 0,
            'total_slippage': Decimal('0'),
            'total_commission': Decimal('0')
        }

        self.is_running = False
        self._execution_loop = None

    async def add_trading_api(self, name: str, api: BaseTradingAPI):
        """添加交易API"""
        self.trading_apis[name] = api
        self.logger.info(f"添加交易API: {name}")

    async def start(self):
        """启动执行引擎"""
        try:
            self.logger.info("启动实时交易执行引擎...")
            self.is_running = True

            # 启动执行循环
            self._execution_loop = asyncio.create_task(self._execution_loop())
            self.logger.info("实时交易执行引擎已启动")
            return True

        except Exception as e:
            self.logger.error(f"启动失败: {e}")
            return False

    async def stop(self):
        """停止执行引擎"""
        try:
            self.logger.info("停止实时交易执行引擎...")
            self.is_running = False

            if self._execution_loop:
                self._execution_loop.cancel()

            # 取消所有活跃订单
            for order_id in list(self.active_orders.keys()):
                await self.cancel_order(order_id)

            self.logger.info("实时交易执行引擎已停止")
            return True

        except Exception as e:
            self.logger.error(f"停止失败: {e}")
            return False

    async def execute_signal(self, signal: TradeSignal) -> Optional[str]:
        """
        执行交易信号

        Returns:
            订单ID，如果失败返回None
        """
        try:
            self.logger.info(f"执行信号: {signal.symbol} {signal.side.value} {signal.quantity}")

            # 1. 获取账户信息
            api = self.trading_apis.get(self.primary_api)
            if not api:
                self.logger.error(f"未找到交易API: {self.primary_api}")
                return None

            account = await api.get_account_info()
            if not account:
                self.logger.error("无法获取账户信息")
                return None

            # 2. 风险检查
            passed, reason = await self.risk_manager.check_pre_trade_risk(signal, account)
            if not passed:
                self.logger.warning(f"风险检查失败: {reason}")
                return None

            # 3. 创建订单
            order = await self._create_order_from_signal(signal)
            order_id = await api.place_order(order)

            if not order_id:
                self.logger.error("下单失败")
                return None

            # 4. 跟踪订单
            self.active_orders[order_id] = order
            self.execution_stats['total_orders'] += 1

            # 5. 启动订单监控
            asyncio.create_task(self._monitor_order(order_id, api))

            self.logger.info(f"订单已提交: {order_id}")
            return order_id

        except Exception as e:
            self.logger.error(f"执行信号失败: {e}")
            return None

    async def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        try:
            if order_id not in self.active_orders:
                return False

            api = self.trading_apis.get(self.primary_api)
            if not api:
                return False

            success = await api.cancel_order(order_id)
            if success:
                self.active_orders[order_id].status = OrderStatus.CANCELLED
                self.execution_stats['cancelled_orders'] += 1

            return success

        except Exception as e:
            self.logger.error(f"取消订单失败: {e}")
            return False

    async def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """获取订单状态"""
        try:
            if order_id not in self.active_orders:
                return None

            api = self.trading_apis.get(self.primary_api)
            if not api:
                return None

            order = await api.get_order_status(order_id)
            if order:
                return {
                    'order_id': order_id,
                    'status': order,
                    'filled_quantity': self.active_orders[order_id].filled_quantity,
                    'average_fill_price': self.active_orders[order_id].average_fill_price
                }

            return None

        except Exception as e:
            self.logger.error(f"获取订单状态失败: {e}")
            return None

    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """获取投资组合摘要"""
        try:
            api = self.trading_apis.get(self.primary_api)
            if not api:
                return {}

            # 获取账户信息
            account = await api.get_account_info()

            # 获取持仓
            positions = await api.get_positions()

            # 更新风险管理器的持仓
            for pos in positions:
                self.risk_manager.update_position(pos)

            return {
                'account': account.dict() if account else {},
                'positions': [pos.dict() for pos in positions],
                'active_orders': len(self.active_orders),
                'daily_pnl': self.risk_manager.daily_pnl,
                'execution_stats': self.execution_stats
            }

        except Exception as e:
            self.logger.error(f"获取投资组合摘要失败: {e}")
            return {}

    async def _execution_loop(self):
        """主执行循环"""
        while self.is_running:
            try:
                # 检查订单状态
                for order_id in list(self.active_orders.keys()):
                    api = self.trading_apis.get(self.primary_api)
                    if api:
                        order_status = await api.get_order_status(order_id)

                        if order_status == OrderStatus.FILLED:
                            await self._handle_filled_order(order_id, api)
                        elif order_status == OrderStatus.CANCELLED:
                            await self._handle_cancelled_order(order_id, api)
                        elif order_status == OrderStatus.REJECTED:
                            await self._handle_rejected_order(order_id, api)

                await asyncio.sleep(1)  # 每秒检查一次

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"执行循环错误: {e}")
                await asyncio.sleep(5)

    async def _monitor_order(self, order_id: str, api: BaseTradingAPI):
        """监控订单执行"""
        try:
            max_attempts = 300  # 5分钟超时
            attempts = 0

            while attempts < max_attempts and self.is_running:
                order_status = await api.get_order_status(order_id)

                if order_status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]:
                    break

                await asyncio.sleep(1)
                attempts += 1

            # 超时处理
            if attempts >= max_attempts:
                await self.cancel_order(order_id)

        except Exception as e:
            self.logger.error(f"监控订单失败: {e}")

    async def _create_order_from_signal(self, signal: TradeSignal) -> Order:
        """从交易信号创建订单"""
        return Order(
            order_id=f"SIG_{signal.signal_id}_{int(datetime.now().timestamp())}",
            symbol=signal.symbol,
            side=signal.side,
            order_type=OrderType.LIMIT if signal.price else OrderType.MARKET,
            quantity=signal.quantity,
            price=signal.price,
            stop_price=signal.stop_price,
            client_order_id=signal.signal_id
        )

    async def _handle_filled_order(self, order_id: str, api: BaseTradingAPI):
        """处理已成交订单"""
        try:
            order = self.active_orders.get(order_id)
            if not order:
                return

            # 获取成交信息
            filled_qty = order.filled_quantity
            avg_price = order.average_fill_price or Decimal('0')
            commission = order.commission or Decimal('0')

            # 更新统计
            self.execution_stats['filled_orders'] += 1
            self.execution_stats['total_commission'] += commission

            # 计算滑点
            # 这里简化处理，实际应该获取理想执行价格
            slippage = Decimal('0')  # 模拟成交价格与理想价格的差异
            self.execution_stats['total_slippage'] += slippage

            # 更新持仓
            positions = await api.get_positions()
            for pos in positions:
                self.risk_manager.update_position(pos)

            self.logger.info(f"订单成交: {order_id}, 数量: {filled_qty}, 价格: {avg_price}")

        except Exception as e:
            self.logger.error(f"处理成交订单失败: {e}")

    async def _handle_cancelled_order(self, order_id: str, api: BaseTradingAPI):
        """处理已取消订单"""
        try:
            self.logger.info(f"订单已取消: {order_id}")
            if order_id in self.active_orders:
                del self.active_orders[order_id]

        except Exception as e:
            self.logger.error(f"处理取消订单失败: {e}")

    async def _handle_rejected_order(self, order_id: str, api: BaseTradingAPI):
        """处理已拒绝订单"""
        try:
            self.logger.warning(f"订单被拒绝: {order_id}")
            self.execution_stats['rejected_orders'] += 1

            if order_id in self.active_orders:
                del self.active_orders[order_id]

        except Exception as e:
            self.logger.error(f"处理拒绝订单失败: {e}")

    def add_order_callback(self, callback: Callable):
        """添加订单状态回调"""
        self.order_callbacks.append(callback)

    async def _notify_callbacks(self, event_type: str, data: Dict[str, Any]):
        """通知所有回调函数"""
        for callback in self.order_callbacks:
            try:
                await callback(event_type, data)
            except Exception as e:
                self.logger.error(f"回调函数执行失败: {e}")

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        try:
            total_orders = self.execution_stats['total_orders']
            if total_orders == 0:
                return {'message': '暂无交易记录'}

            filled_rate = (self.execution_stats['filled_orders'] / total_orders) * 100
            cancelled_rate = (self.execution_stats['cancelled_orders'] / total_orders) * 100
            rejected_rate = (self.execution_stats['rejected_orders'] / total_orders) * 100

            return {
                'total_orders': total_orders,
                'filled_orders': self.execution_stats['filled_orders'],
                'filled_rate': f"{filled_rate:.2f}%",
                'cancelled_orders': self.execution_stats['cancelled_orders'],
                'cancelled_rate': f"{cancelled_rate:.2f}%",
                'rejected_orders': self.execution_stats['rejected_orders'],
                'rejected_rate': f"{rejected_rate:.2f}%",
                'total_commission': float(self.execution_stats['total_commission']),
                'total_slippage': float(self.execution_stats['total_slippage']),
                'avg_execution_time_ms': self.execution_stats['avg_execution_time_ms'],
                'daily_pnl': float(self.risk_manager.daily_pnl)
            }

        except Exception as e:
            self.logger.error(f"获取性能指标失败: {e}")
            return {}
