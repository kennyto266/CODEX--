"""
模拟交易执行引擎

负责模拟交易的执行、订单管理、仓位管理、资金管理等功能
基于 FutuTradingAPI 实现，添加模拟交易特有逻辑
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from decimal import Decimal
import json

from .base_trading_api import Order, OrderType, OrderSide, OrderStatus, Position, AccountInfo, MarketData
from .futu_trading_api import FutuTradingAPI
from .realtime_execution_engine import TradeSignal, ExecutionStrategy
from .paper_trading_risk_manager import PaperTradingRiskManager, RiskLimits, create_risk_manager


class PaperTradingEngine:
    """
    模拟交易引擎

    负责：
    - 订单生命周期管理
    - 仓位和资金跟踪
    - 交易日志记录
    - 模拟成交逻辑
    """

    def __init__(
        self,
        futu_api: FutuTradingAPI,
        initial_balance: Decimal = Decimal('1000000'),
        commission_rate: Decimal = Decimal('0.001'),
        min_commission: Decimal = Decimal('10'),
        risk_manager: Optional[PaperTradingRiskManager] = None
    ):
        self.futu_api = futu_api
        self.logger = logging.getLogger("hk_quant_system.paper_trading_engine")

        # 账户配置
        self.initial_balance = initial_balance
        self.commission_rate = commission_rate  # 0.1%
        self.min_commission = min_commission

        # 风险管理器
        self.risk_manager = risk_manager or create_risk_manager()

        # 账户状态
        self.account: Optional[AccountInfo] = None
        self.positions: Dict[str, Position] = {}
        self.orders: Dict[str, Order] = {}
        self.trade_history: List[Dict[str, Any]] = []

        # 模拟资金
        self.cash_balance = initial_balance
        self.total_commission_paid = Decimal('0')

        # 统计信息
        self.daily_trade_count = 0
        self.last_trade_date = datetime.now().date()

        # 执行引擎状态
        self._running = False
        self._initialization_time = datetime.now()

        # 回调函数
        self.on_trade_executed: Optional[Callable] = None
        self.on_order_status_change: Optional[Callable] = None
        self.on_position_change: Optional[Callable] = None

        self.logger.info(f"PaperTradingEngine 已创建，初始资金: {initial_balance:,.2f} HKD")

    async def initialize(self) -> bool:
        """
        初始化模拟交易引擎

        Returns:
            bool: 初始化是否成功
        """
        try:
            self.logger.info("初始化模拟交易引擎...")

            # 创建模拟账户
            self.account = AccountInfo(
                account_id="PAPER_TRADING_ACCOUNT",
                account_type="SIMULATED",
                buying_power=self.cash_balance,
                cash=self.cash_balance,
                equity=self.cash_balance,
                margin_used=Decimal('0'),
                margin_available=self.cash_balance,
                last_updated=datetime.now()
            )

            # 启动引擎
            await self.start()

            self.logger.info("✅ 模拟交易引擎初始化完成")
            return True

        except Exception as e:
            self.logger.error(f"初始化失败: {e}", exc_info=True)
            return False

    async def start(self):
        """启动引擎"""
        if self._running:
            return

        self.logger.info("启动模拟交易引擎...")
        self._running = True
        self.logger.info("✅ 模拟交易引擎已启动")

    async def stop(self):
        """停止引擎"""
        if not self._running:
            return

        self.logger.info("停止模拟交易引擎...")
        self._running = False
        self.logger.info("✅ 模拟交易引擎已停止")

    async def execute_signal(self, signal: TradeSignal) -> Dict[str, Any]:
        """
        执行交易信号

        Args:
            signal: 交易信号

        Returns:
            Dict[str, Any]: 执行结果
        """
        if not self._running:
            return {
                'success': False,
                'error': '引擎未启动'
            }

        try:
            # 步骤1: 执行风险检查
            if self.risk_manager and self.account:
                risk_passed, risk_message, risk_details = await self.risk_manager.check_pre_trade_risk(
                    signal=signal,
                    account=self.account,
                    positions=list(self.positions.values())
                )

                if not risk_passed:
                    self.logger.warning(f"❌ 风险检查未通过: {risk_message}")
                    return {
                        'success': False,
                        'error': f'风险检查未通过: {risk_message}',
                        'risk_details': risk_details
                    }

                self.logger.info(f"✅ 风险检查通过: {risk_message}")

            # 步骤2: 创建订单
            order = await self._create_order_from_signal(signal)
            if not order:
                return {
                    'success': False,
                    'error': '创建订单失败'
                }

            # 存储订单
            self.orders[order.order_id] = order

            # 步骤3: 模拟订单执行
            execution_result = await self._simulate_order_execution(order)

            if execution_result['success']:
                # 步骤4: 更新账户和持仓
                await self._update_account_and_positions(execution_result)

                # 步骤5: 记录交易
                self._record_trade(order, execution_result)

                # 步骤6: 增加日交易计数
                await self._increment_daily_trade_count()

                # 步骤7: 触发回调
                if self.on_trade_executed:
                    await self.on_trade_executed({
                        'order': order.dict(),
                        'execution': execution_result,
                        'success': True,
                        'risk_details': risk_details if 'risk_details' in locals() else None
                    })

            return execution_result

        except Exception as e:
            self.logger.error(f"执行信号失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    async def _create_order_from_signal(self, signal: TradeSignal) -> Optional[Order]:
        """从交易信号创建订单"""
        try:
            # 确定订单类型
            order_type = OrderType.MARKET
            price = None

            if signal.price:
                order_type = OrderType.LIMIT
                price = signal.price

            # 创建订单
            order = Order(
                order_id=f"PAPER_{signal.signal_id}",
                symbol=signal.symbol,
                side=signal.side,
                order_type=order_type,
                quantity=signal.quantity,
                price=price,
                status=OrderStatus.SUBMITTED,
                client_order_id=signal.signal_id,
                notes=f"模拟交易订单 - 策略: {signal.strategy}"
            )

            self.logger.info(f"创建订单: {order.symbol} {order.side} {order.quantity}")
            return order

        except Exception as e:
            self.logger.error(f"创建订单失败: {e}", exc_info=True)
            return None

    async def _simulate_order_execution(self, order: Order) -> Dict[str, Any]:
        """
        模拟订单执行

        在实际应用中，这里会调用真实的券商API
        但在模拟环境中，我们直接返回成功

        Args:
            order: 订单

        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            # 模拟执行延迟
            await asyncio.sleep(0.1)

            # 计算成交价格
            if order.order_type == OrderType.MARKET:
                # 市价单：使用当前市场价格
                market_data = await self._get_current_market_data(order.symbol)
                if not market_data or not market_data.last_price:
                    return {
                        'success': False,
                        'error': '无法获取市场价格'
                    }
                fill_price = market_data.last_price
            else:
                # 限价单：使用订单价格
                fill_price = order.price or Decimal('0')

            # 检查资金充足性（买入）
            if order.side == OrderSide.BUY:
                required_cash = order.quantity * fill_price
                commission = self._calculate_commission(required_cash)
                total_cost = required_cash + commission

                if total_cost > self.cash_balance:
                    order.status = OrderStatus.REJECTED
                    return {
                        'success': False,
                        'error': '资金不足',
                        'required': total_cost,
                        'available': self.cash_balance
                    }

            # 模拟成功成交
            order.status = OrderStatus.FILLED
            order.filled_quantity = order.quantity
            order.average_fill_price = fill_price
            order.commission = self._calculate_commission(order.quantity * fill_price)
            order.updated_at = datetime.now()

            # 记录交易到风险管理器
            pnl = self._calculate_trade_pnl(order)
            # 获取side值（兼容字符串和枚举类型）
            side_value = order.side.value if hasattr(order.side, 'value') else str(order.side)
            await self.risk_manager.record_trade(
                symbol=order.symbol,
                side=side_value,
                quantity=order.quantity,
                price=order.average_fill_price,
                pnl=pnl
            )

            return {
                'success': True,
                'order_id': order.order_id,
                'symbol': order.symbol,
                'side': order.side,
                'quantity': order.quantity,
                'filled_quantity': order.filled_quantity,
                'fill_price': fill_price,
                'commission': order.commission,
                'execution_time_ms': 100,  # 模拟执行时间
                'timestamp': datetime.now()
            }

        except Exception as e:
            self.logger.error(f"模拟订单执行失败: {e}", exc_info=True)
            order.status = OrderStatus.REJECTED
            return {
                'success': False,
                'error': str(e)
            }

    def _calculate_commission(self, trade_value: Decimal) -> Decimal:
        """
        计算手续费

        Args:
            trade_value: 交易金额

        Returns:
            Decimal: 手续费
        """
        commission = trade_value * self.commission_rate
        return max(commission, self.min_commission)

    def _calculate_trade_pnl(self, order: Order) -> Decimal:
        """
        计算交易盈亏

        Args:
            order: 订单

        Returns:
            Decimal: 盈亏金额
        """
        try:
            # 获取当前持仓
            current_position = self.positions.get(order.symbol)

            if not current_position or current_position.quantity == 0:
                # 没有持仓，买入不计盈亏，卖出为亏损
                if order.side == OrderSide.SELL:
                    return -order.quantity * order.average_fill_price
                return Decimal('0')

            # 计算平均成本
            if order.side == OrderSide.BUY:
                # 买入订单：更新成本价，不立即计算盈亏
                return Decimal('0')
            else:
                # 卖出订单：计算已实现盈亏
                if current_position.average_price > 0:
                    pnl_per_share = order.average_fill_price - current_position.average_price
                    return pnl_per_share * order.quantity
                return Decimal('0')

        except Exception as e:
            self.logger.error(f"计算交易盈亏失败: {e}", exc_info=True)
            return Decimal('0')

    async def _get_current_market_data(self, symbol: str) -> Optional[MarketData]:
        """
        获取当前市场数据

        Args:
            symbol: 股票代码

        Returns:
            Optional[MarketData]: 市场数据
        """
        try:
            if self.futu_api:
                return await self.futu_api.get_market_data(symbol)
            return None
        except Exception as e:
            self.logger.error(f"获取市场数据失败: {e}")
            return None

    async def _update_account_and_positions(self, execution_result: Dict[str, Any]):
        """更新账户和持仓信息"""
        try:
            symbol = execution_result['symbol']
            side = execution_result['side']
            quantity = execution_result['quantity']
            fill_price = execution_result['fill_price']
            commission = execution_result['commission']

            # 更新现金余额
            if side == OrderSide.BUY:
                # 买入：减少现金
                total_cost = quantity * fill_price + commission
                self.cash_balance -= total_cost
            else:
                # 卖出：增加现金
                total_proceeds = quantity * fill_price - commission
                self.cash_balance += total_proceeds

            # 更新持仓
            if symbol not in self.positions:
                self.positions[symbol] = Position(
                    symbol=symbol,
                    quantity=Decimal('0'),
                    average_price=Decimal('0'),
                    last_updated=datetime.now()
                )

            position = self.positions[symbol]

            if side == OrderSide.BUY:
                # 买入：增加持仓
                total_cost = quantity * fill_price + commission
                new_quantity = position.quantity + quantity
                new_avg_price = (position.quantity * position.average_price + total_cost) / new_quantity

                position.quantity = new_quantity
                position.average_price = new_avg_price
            else:
                # 卖出：减少持仓
                position.quantity -= quantity
                if position.quantity <= 0:
                    position.quantity = Decimal('0')
                    position.average_price = Decimal('0')

            position.current_price = fill_price
            position.market_value = position.quantity * fill_price
            position.last_updated = datetime.now()

            # 计算未实现盈亏
            if position.quantity > 0:
                position.unrealized_pnl = (fill_price - position.average_price) * position.quantity

            # 更新账户信息
            if self.account:
                total_market_value = sum(p.market_value or Decimal('0') for p in self.positions.values())
                self.account.cash = self.cash_balance
                self.account.equity = self.cash_balance + total_market_value
                self.account.buying_power = self.cash_balance
                self.account.last_updated = datetime.now()

            # 触发持仓变更回调
            if self.on_position_change:
                await self.on_position_change({
                    'symbol': symbol,
                    'position': self.positions[symbol].dict(),
                    'account': self.account.dict() if self.account else None
                })

            self.logger.info(f"账户更新: {symbol} 持仓={position.quantity}, 现金={self.cash_balance}")

        except Exception as e:
            self.logger.error(f"更新账户和持仓失败: {e}", exc_info=True)

    def _record_trade(self, order: Order, execution_result: Dict[str, Any]):
        """记录交易"""
        try:
            trade_record = {
                'trade_id': f"TRADE_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                'order_id': order.order_id,
                'symbol': order.symbol,
                'side': order.side,
                'quantity': str(execution_result['quantity']),
                'fill_price': str(execution_result['fill_price']),
                'commission': str(execution_result['commission']),
                'timestamp': execution_result['timestamp'].isoformat(),
                'strategy': order.notes
            }

            self.trade_history.append(trade_record)

            # 保持历史记录在合理范围内（最多保留1000条）
            if len(self.trade_history) > 1000:
                self.trade_history = self.trade_history[-1000:]

            self.logger.info(f"记录交易: {trade_record['trade_id']}")

        except Exception as e:
            self.logger.error(f"记录交易失败: {e}", exc_info=True)

    async def _increment_daily_trade_count(self):
        """增加日交易计数"""
        today = datetime.now().date()
        if today != self.last_trade_date:
            self.daily_trade_count = 0
            self.last_trade_date = today
        self.daily_trade_count += 1

    def get_daily_trade_count(self) -> int:
        """获取今日交易次数"""
        return self.daily_trade_count

    async def get_account_info(self) -> Optional[AccountInfo]:
        """
        获取账户信息

        Returns:
            Optional[AccountInfo]: 账户信息
        """
        return self.account

    async def get_positions(self) -> List[Position]:
        """
        获取持仓列表

        Returns:
            List[Position]: 持仓列表
        """
        return [pos for pos in self.positions.values() if pos.quantity > 0]

    async def get_orders(self, status_filter: Optional[OrderStatus] = None) -> List[Order]:
        """
        获取订单列表

        Args:
            status_filter: 状态过滤

        Returns:
            List[Order]: 订单列表
        """
        orders = list(self.orders.values())

        if status_filter:
            orders = [o for o in orders if o.status == status_filter]

        return orders

    async def cancel_order(self, order_id: str) -> bool:
        """
        取消订单

        Args:
            order_id: 订单ID

        Returns:
            bool: 是否成功取消
        """
        try:
            if order_id not in self.orders:
                return False

            order = self.orders[order_id]
            if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
                return False

            order.status = OrderStatus.CANCELLED
            order.updated_at = datetime.now()

            self.logger.info(f"取消订单: {order_id}")
            return True

        except Exception as e:
            self.logger.error(f"取消订单失败: {e}", exc_info=True)
            return False

    async def cancel_all_orders(self) -> int:
        """
        取消所有待执行订单

        Returns:
            int: 取消的订单数量
        """
        cancelled_count = 0
        for order_id in list(self.orders.keys()):
            if await self.cancel_order(order_id):
                cancelled_count += 1

        self.logger.info(f"取消了 {cancelled_count} 个订单")
        return cancelled_count

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        获取性能指标

        Returns:
            Dict[str, Any]: 性能指标
        """
        try:
            if not self.account:
                return {}

            # 从风险管理器获取回撤信息
            risk_status = await self.risk_manager.get_risk_status() if self.risk_manager else {}

            # 计算收益率
            total_return = self.account.equity - self.initial_balance
            return_rate = (total_return / self.initial_balance) * 100 if self.initial_balance > 0 else 0

            # 计算年化收益率
            days_running = (datetime.now() - self._initialization_time).days
            annual_return_rate = (return_rate * 365 / days_running) if days_running > 0 else 0

            # 计算胜率（简化版）
            total_trades = len(self.trade_history)
            profitable_trades = sum(1 for t in self.trade_history if t.get('pnl', 0) > 0)
            win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0

            # 获取最大回撤
            max_drawdown_pct = float(risk_status.get('current_drawdown', 0)) * 100

            # 计算夏普比率（简化版）
            # 假设无风险利率为 2%
            risk_free_rate = 2.0
            excess_return = return_rate - risk_free_rate
            # 简化计算，假设波动率为回报率的一半
            volatility = abs(return_rate) / 2 if return_rate != 0 else 1
            sharpe_ratio = excess_return / volatility if volatility > 0 else 0

            return {
                'total_return': float(total_return),
                'return_rate': float(return_rate),
                'annual_return_rate': float(annual_return_rate),
                'total_trades': total_trades,
                'profitable_trades': profitable_trades,
                'win_rate': float(win_rate),
                'max_drawdown': max_drawdown_pct,
                'sharpe_ratio': sharpe_ratio,
                'total_commission_paid': float(self.total_commission_paid),
                'cash_balance': float(self.cash_balance),
                'account_equity': float(self.account.equity),
                'days_running': days_running,
                'risk_status': risk_status
            }

        except Exception as e:
            self.logger.error(f"计算性能指标失败: {e}", exc_info=True)
            return {}

    async def reset_account(self, new_balance: Decimal):
        """
        重置账户

        Args:
            new_balance: 新余额
        """
        try:
            self.logger.info(f"重置模拟账户，余额: {new_balance:,.2f} HKD")

            self.cash_balance = new_balance
            self.positions.clear()
            self.orders.clear()
            self.trade_history.clear()
            self.daily_trade_count = 0
            self.last_trade_date = datetime.now().date()

            if self.account:
                self.account.cash = new_balance
                self.account.equity = new_balance
                self.account.buying_power = new_balance
                self.account.last_updated = datetime.now()

            # 重置风险管理器
            if self.risk_manager:
                await self.risk_manager.reset_risk_state()

            self.logger.info("✅ 账户重置完成")

        except Exception as e:
            self.logger.error(f"重置账户失败: {e}", exc_info=True)

    async def cleanup(self):
        """清理资源"""
        try:
            self.logger.info("清理模拟交易引擎资源...")

            await self.stop()

            # 清空数据
            self.positions.clear()
            self.orders.clear()
            self.trade_history.clear()

            self.logger.info("✅ 资源清理完成")

        except Exception as e:
            self.logger.error(f"清理资源失败: {e}", exc_info=True)
