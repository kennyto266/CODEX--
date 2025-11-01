"""
模拟交易API - 用于测试和演示

模拟真实的交易环境，包括：
- 账户管理
- 订单执行
- 市场数据
- 持仓管理
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal
import uuid

from base_trading_api import (
    BaseTradingAPI, Order, OrderType, OrderSide, OrderStatus,
    Position, AccountInfo, MarketData
)


class PaperTradingAPI(BaseTradingAPI):
    """模拟交易API"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # 模拟资金
        self.initial_cash = Decimal(str(config.get('initial_cash', 1000000)))
        self.cash = self.initial_cash
        self.buying_power = self.cash * Decimal('4')  # 4倍杠杆

        # 存储
        self.orders: Dict[str, Order] = {}
        self.positions: Dict[str, Position] = {}
        self.market_data: Dict[str, MarketData] = {}

        # 模拟参数
        self.commission_rate = Decimal('0.001')  # 0.1% 手续费
        self.slippage_rate = Decimal('0.0005')  # 0.05% 滑点
        self.execution_delay = config.get('execution_delay', 0.5)  # 执行延迟（秒）

        # 初始数据
        self._initialize_market_data()
        self._initialize_positions()

    def _initialize_market_data(self):
        """初始化市场数据"""
        symbols = ['0700.HK', '0388.HK', '1398.HK', '0939.HK', '3988.HK']

        for symbol in symbols:
            # 模拟真实价格波动
            base_price = Decimal(str(random.uniform(100, 1000)))
            spread = base_price * Decimal('0.001')

            self.market_data[symbol] = MarketData(
                symbol=symbol,
                bid_price=base_price - spread / 2,
                ask_price=base_price + spread / 2,
                last_price=base_price,
                volume=int(random.uniform(1000000, 10000000)),
                high_price=base_price * Decimal('1.05'),
                low_price=base_price * Decimal('0.95'),
                open_price=base_price * Decimal('0.98'),
                timestamp=datetime.now()
            )

    def _initialize_positions(self):
        """初始化持仓"""
        # 初始空仓
        pass

    async def connect(self) -> bool:
        """连接到模拟交易系统"""
        try:
            await asyncio.sleep(0.1)  # 模拟连接延迟
            self._connected = True
            self.logger.info("模拟交易API已连接")
            return True
        except Exception as e:
            self.logger.error(f"连接失败: {e}")
            return False

    async def disconnect(self) -> bool:
        """断开连接"""
        try:
            await asyncio.sleep(0.1)
            self._connected = False
            self.logger.info("模拟交易API已断开")
            return True
        except Exception as e:
            self.logger.error(f"断开失败: {e}")
            return False

    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        """身份验证（模拟）"""
        try:
            await asyncio.sleep(0.1)
            self._authenticated = True
            self.logger.info("模拟交易API已认证")
            return True
        except Exception as e:
            self.logger.error(f"认证失败: {e}")
            return False

    async def get_account_info(self) -> Optional[AccountInfo]:
        """获取账户信息"""
        try:
            total_equity = self.cash + sum(
                pos.market_value or Decimal('0')
                for pos in self.positions.values()
            )

            return AccountInfo(
                account_id="PAPER_TRADING_001",
                account_type="模拟账户",
                buying_power=self.buying_power,
                cash=self.cash,
                equity=total_equity,
                margin_used=Decimal('0'),
                margin_available=self.buying_power,
                day_trading_buying_power=self.buying_power,
                last_updated=datetime.now()
            )

        except Exception as e:
            self.logger.error(f"获取账户信息失败: {e}")
            return None

    async def get_positions(self) -> List[Position]:
        """获取持仓信息"""
        try:
            # 更新持仓的市场价值和损益
            for symbol, position in self.positions.items():
                market_data = self.market_data.get(symbol)
                if market_data and market_data.last_price:
                    position.current_price = market_data.last_price
                    position.market_value = position.quantity * position.current_price
                    position.unrealized_pnl = (
                        (position.current_price - position.average_price) * position.quantity
                    )

            return list(self.positions.values())

        except Exception as e:
            self.logger.error(f"获取持仓失败: {e}")
            return []

    async def get_orders(self, status_filter: Optional[OrderStatus] = None) -> List[Order]:
        """获取订单列表"""
        try:
            orders = list(self.orders.values())
            if status_filter:
                orders = [o for o in orders if o.status == status_filter]
            return orders

        except Exception as e:
            self.logger.error(f"获取订单失败: {e}")
            return []

    async def place_order(self, order: Order) -> Optional[str]:
        """下单"""
        try:
            # 验证订单
            errors = await self.validate_order(order)
            if errors:
                self.logger.error(f"订单验证失败: {errors}")
                return None

            # 生成订单ID
            order_id = str(uuid.uuid4())
            order.order_id = order_id
            order.created_at = datetime.now()
            order.status = OrderStatus.PENDING

            # 保存订单
            self.orders[order_id] = order

            # 异步执行订单
            asyncio.create_task(self._execute_order(order_id))

            self.logger.info(f"订单已提交: {order_id}")
            return order_id

        except Exception as e:
            self.logger.error(f"下单失败: {e}")
            return None

    async def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        try:
            if order_id not in self.orders:
                return False

            order = self.orders[order_id]
            if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]:
                return False

            order.status = OrderStatus.CANCELLED
            order.updated_at = datetime.now()

            self.logger.info(f"订单已取消: {order_id}")
            return True

        except Exception as e:
            self.logger.error(f"取消订单失败: {e}")
            return False

    async def modify_order(self, order_id: str, modifications: Dict[str, Any]) -> bool:
        """修改订单"""
        try:
            if order_id not in self.orders:
                return False

            order = self.orders[order_id]
            if order.status != OrderStatus.PENDING:
                return False

            # 应用修改
            for key, value in modifications.items():
                if hasattr(order, key):
                    setattr(order, key, value)

            order.updated_at = datetime.now()
            self.logger.info(f"订单已修改: {order_id}")
            return True

        except Exception as e:
            self.logger.error(f"修改订单失败: {e}")
            return False

    async def get_order_status(self, order_id: str) -> Optional[OrderStatus]:
        """获取订单状态"""
        try:
            if order_id not in self.orders:
                return None

            return self.orders[order_id].status

        except Exception as e:
            self.logger.error(f"获取订单状态失败: {e}")
            return None

    async def get_market_data(self, symbol: str) -> Optional[MarketData]:
        """获取市场数据"""
        try:
            # 模拟价格波动
            if symbol in self.market_data:
                data = self.market_data[symbol]
                price_change = Decimal(str(random.uniform(-0.02, 0.02)))  # ±2% 波动
                new_price = data.last_price * (Decimal('1') + price_change)

                # 更新数据
                data.last_price = new_price
                data.bid_price = new_price - (new_price * self.slippage_rate)
                data.ask_price = new_price + (new_price * self.slippage_rate)
                data.timestamp = datetime.now()

                # 更新成交量（随机增量）
                data.volume += int(random.uniform(1000, 100000))

            return self.market_data.get(symbol)

        except Exception as e:
            self.logger.error(f"获取市场数据失败: {e}")
            return None

    async def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> List[Dict[str, Any]]:
        """获取历史数据（模拟）"""
        try:
            # 生成模拟历史数据
            data = []
            current_date = start_date
            base_price = Decimal(str(random.uniform(100, 1000)))

            while current_date <= end_date:
                # 随机价格变动
                price_change = Decimal(str(random.uniform(-0.05, 0.05)))
                open_price = base_price
                close_price = base_price * (Decimal('1') + price_change)
                high_price = max(open_price, close_price) * Decimal(str(random.uniform(1.0, 1.03)))
                low_price = min(open_price, close_price) * Decimal(str(random.uniform(0.97, 1.0)))
                volume = int(random.uniform(1000000, 10000000))

                data.append({
                    'timestamp': current_date.isoformat(),
                    'open': float(open_price),
                    'high': float(high_price),
                    'low': float(low_price),
                    'close': float(close_price),
                    'volume': volume
                })

                base_price = close_price
                current_date += timedelta(days=1)

            return data

        except Exception as e:
            self.logger.error(f"获取历史数据失败: {e}")
            return []

    async def _execute_order(self, order_id: str):
        """执行订单（异步）"""
        try:
            order = self.orders[order_id]
            if not order:
                return

            # 延迟执行模拟真实交易
            await asyncio.sleep(self.execution_delay)

            # 检查是否已取消
            if order.status == OrderStatus.CANCELLED:
                return

            # 模拟执行
            execution_price = await self._calculate_execution_price(order)
            if not execution_price:
                order.status = OrderStatus.REJECTED
                return

            # 计算成交数量（部分成交或全部成交）
            available_qty = await self._calculate_available_quantity(order, execution_price)
            filled_qty = min(Decimal(str(available_qty)), order.quantity)

            # 计算手续费
            commission = filled_qty * execution_price * self.commission_rate

            # 更新订单
            order.status = OrderStatus.FILLED if filled_qty == order.quantity else OrderStatus.PARTIALLY_FILLED
            order.filled_quantity = filled_qty
            order.average_fill_price = execution_price
            order.commission = commission
            order.updated_at = datetime.now()

            # 更新持仓
            await self._update_position(order, filled_qty, execution_price)

            # 更新现金
            if order.side == OrderSide.BUY:
                self.cash -= (filled_qty * execution_price + commission)
            else:
                self.cash += (filled_qty * execution_price - commission)

            self.logger.info(
                f"订单执行: {order_id}, 成交: {filled_qty}, "
                f"价格: {execution_price}, 手续费: {commission}"
            )

        except Exception as e:
            self.logger.error(f"执行订单失败: {e}")
            order = self.orders.get(order_id)
            if order:
                order.status = OrderStatus.REJECTED

    async def _calculate_execution_price(self, order: Order) -> Optional[Decimal]:
        """计算执行价格"""
        try:
            market_data = self.market_data.get(order.symbol)
            if not market_data:
                return None

            # 根据订单类型计算价格
            if order.order_type == OrderType.MARKET:
                # 市价单：使用当前买卖价
                if order.side == OrderSide.BUY:
                    price = market_data.ask_price
                else:
                    price = market_data.bid_price
            elif order.order_type == OrderType.LIMIT:
                # 限价单：检查价格限制
                if order.side == OrderSide.BUY and order.price >= market_data.ask_price:
                    price = market_data.ask_price
                elif order.side == OrderSide.SELL and order.price <= market_data.bid_price:
                    price = market_data.bid_price
                else:
                    return None  # 价格不满足条件
            else:
                # 其他订单类型使用当前价格
                price = market_data.last_price

            # 添加滑点
            slippage = price * self.slippage_rate
            if order.side == OrderSide.BUY:
                execution_price = price + slippage
            else:
                execution_price = price - slippage

            return execution_price

        except Exception as e:
            self.logger.error(f"计算执行价格失败: {e}")
            return None

    async def _calculate_available_quantity(self, order: Order, price: Decimal) -> int:
        """计算可成交数量"""
        try:
            if order.side == OrderSide.BUY:
                # 买入：检查现金是否足够
                max_qty = self.cash / (price * (Decimal('1') + self.commission_rate))
                return int(max_qty)
            else:
                # 卖出：检查持仓
                position = self.positions.get(order.symbol)
                if position:
                    return int(position.quantity)
                return 0

        except Exception as e:
            self.logger.error(f"计算可成交数量失败: {e}")
            return 0

    async def _update_position(self, order: Order, filled_qty: Decimal, price: Decimal):
        """更新持仓"""
        try:
            symbol = order.symbol

            if symbol not in self.positions:
                # 新建持仓
                if order.side == OrderSide.BUY:
                    self.positions[symbol] = Position(
                        symbol=symbol,
                        quantity=filled_qty,
                        average_price=price,
                        current_price=price,
                        market_value=filled_qty * price
                    )
                else:
                    self.positions[symbol] = Position(
                        symbol=symbol,
                        quantity=-filled_qty,
                        average_price=price,
                        current_price=price,
                        market_value=-filled_qty * price
                    )
            else:
                # 更新现有持仓
                position = self.positions[symbol]

                if order.side == OrderSide.BUY:
                    # 买入：加权平均成本
                    total_cost = (position.quantity * position.average_price) + (filled_qty * price)
                    new_quantity = position.quantity + filled_qty
                    position.average_price = total_cost / new_quantity if new_quantity != 0 else price
                    position.quantity = new_quantity
                else:
                    # 卖出：减少持仓
                    position.quantity -= filled_qty

                    # 如果持仓变为0，删除该持仓
                    if position.quantity == 0:
                        del self.positions[symbol]

        except Exception as e:
            self.logger.error(f"更新持仓失败: {e}")

    async def reset_account(self):
        """重置账户（用于测试）"""
        self.cash = self.initial_cash
        self.buying_power = self.cash * Decimal('4')
        self.orders.clear()
        self.positions.clear()
        self._initialize_market_data()
        self.logger.info("账户已重置")

    async def get_trading_summary(self) -> Dict[str, Any]:
        """获取交易摘要"""
        try:
            account = await self.get_account_info()
            positions = await self.get_positions()

            # 计算总市值
            total_market_value = sum(
                pos.market_value or Decimal('0')
                for pos in positions
            )

            # 计算总未实现损益
            total_unrealized_pnl = sum(
                pos.unrealized_pnl or Decimal('0')
                for pos in positions
            )

            return {
                'account_id': account.account_id if account else 'N/A',
                'cash': float(account.cash) if account and account.cash else 0,
                'equity': float(account.equity) if account and account.equity else 0,
                'total_market_value': float(total_market_value),
                'total_unrealized_pnl': float(total_unrealized_pnl),
                'total_positions': len(positions),
                'total_orders': len(self.orders),
                'active_orders': len([o for o in self.orders.values() if o.status not in [
                    OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED
                ]]),
                'filled_orders': len([o for o in self.orders.values() if o.status == OrderStatus.FILLED])
            }

        except Exception as e:
            self.logger.error(f"获取交易摘要失败: {e}")
            return {}
