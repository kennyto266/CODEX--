"""
Trading Domain Services
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio

from ..entities import Order, OrderId, Trade, TradeId, Position, PositionId, OrderSide, OrderStatus, OrderType
from ...repositories import Repository


class OrderService:
    """Domain service for order operations"""

    def __init__(self, order_repository: Repository[Order]):
        self._order_repository = order_repository

    async def create_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: int,
        order_type: OrderType,
        price: Optional[float] = None
    ) -> Order:
        """Create a new order"""
        order_id = OrderId.create()
        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            price=price
        )

        await self._order_repository.save(order)
        return order

    async def execute_order(
        self,
        order_id: OrderId,
        executed_quantity: int,
        executed_price: float
    ) -> Order:
        """Execute an order"""
        order = await self._order_repository.find_by_id(order_id.value)
        if not order:
            raise ValueError(f"Order not found: {order_id}")

        order.execute(executed_quantity, executed_price)
        await self._order_repository.save(order)
        return order

    async def cancel_order(self, order_id: OrderId) -> Order:
        """Cancel an order"""
        order = await self._order_repository.find_by_id(order_id.value)
        if not order:
            raise ValueError(f"Order not found: {order_id}")

        order.cancel()
        await self._order_repository.save(order)
        return order

    async def reject_order(self, order_id: OrderId, reason: str) -> Order:
        """Reject an order"""
        order = await self._order_repository.find_by_id(order_id.value)
        if not order:
            raise ValueError(f"Order not found: {order_id}")

        order.reject(reason)
        await self._order_repository.save(order)
        return order

    async def get_order_by_id(self, order_id: OrderId) -> Optional[Order]:
        """Get order by ID"""
        return await self._order_repository.find_by_id(order_id.value)

    async def get_orders_by_symbol(self, symbol: str) -> List[Order]:
        """Get all orders for a symbol"""
        all_orders = await self._order_repository.find_all()
        return [order for order in all_orders if order.symbol == symbol]

    async def get_pending_orders(self) -> List[Order]:
        """Get all pending orders"""
        all_orders = await self._order_repository.find_all()
        return [order for order in all_orders if order.status == OrderStatus.PENDING]

    async def get_orders_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Order]:
        """Get orders within date range"""
        all_orders = await self._order_repository.find_all()
        return [
            order for order in all_orders
            if start_date <= order.created_at <= end_date
        ]

    async def get_order_statistics(self) -> Dict[str, Any]:
        """Get order statistics"""
        all_orders = await self._order_repository.find_all()

        stats = {
            "total_orders": len(all_orders),
            "pending_orders": len([o for o in all_orders if o.status == OrderStatus.PENDING]),
            "executed_orders": len([o for o in all_orders if o.status == OrderStatus.EXECUTED]),
            "cancelled_orders": len([o for o in all_orders if o.status == OrderStatus.CANCELLED]),
            "rejected_orders": len([o for o in all_orders if o.status == OrderStatus.REJECTED]),
        }

        # Calculate success rate
        if stats["total_orders"] > 0:
            stats["success_rate"] = (stats["executed_orders"] / stats["total_orders"]) * 100
        else:
            stats["success_rate"] = 0.0

        # Calculate average execution price
        executed_orders = [o for o in all_orders if o.status == OrderStatus.EXECUTED]
        if executed_orders:
            total_value = sum(o.executed_price * o.executed_quantity for o in executed_orders)
            total_quantity = sum(o.executed_quantity for o in executed_orders)
            stats["avg_execution_price"] = total_value / total_quantity if total_quantity > 0 else 0
        else:
            stats["avg_execution_price"] = 0.0

        return stats


class TradeService:
    """Domain service for trade operations"""

    def __init__(self, trade_repository: Repository[Trade]):
        self._trade_repository = trade_repository

    async def create_trade(
        self,
        symbol: str,
        side: OrderSide,
        quantity: int,
        price: float,
        commission: float = 0.0,
        trade_type: str = "trade"
    ) -> Trade:
        """Create a new trade"""
        trade_id = TradeId.create()
        from ..entities import TradeType
        trade = Trade(
            trade_id=trade_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            trade_type=TradeType(trade_type),
            commission=commission
        )

        await self._trade_repository.save(trade)
        return trade

    async def get_trade_by_id(self, trade_id: TradeId) -> Optional[Trade]:
        """Get trade by ID"""
        return await self._trade_repository.find_by_id(trade_id.value)

    async def get_trades_by_symbol(self, symbol: str) -> List[Trade]:
        """Get all trades for a symbol"""
        all_trades = await self._trade_repository.find_all()
        return [trade for trade in all_trades if trade.symbol == symbol]

    async def get_trades_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Trade]:
        """Get trades within date range"""
        all_trades = await self._trade_repository.find_all()
        return [
            trade for trade in all_trades
            if start_date <= trade.created_at <= end_date
        ]

    async def get_trade_statistics(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get trade statistics"""
        if symbol:
            trades = await self.get_trades_by_symbol(symbol)
        else:
            trades = await self._trade_repository.find_all()

        if not trades:
            return {
                "total_trades": 0,
                "total_volume": 0,
                "total_commission": 0,
                "avg_price": 0,
                "buy_volume": 0,
                "sell_volume": 0,
            }

        total_volume = sum(trade.quantity for trade in trades)
        total_commission = sum(trade.commission for trade in trades)
        total_value = sum(trade.gross_amount for trade in trades)
        avg_price = total_value / total_volume if total_volume > 0 else 0

        buy_volume = sum(trade.quantity for trade in trades if trade.side == OrderSide.BUY)
        sell_volume = sum(trade.quantity for trade in trades if trade.side == OrderSide.SELL)

        return {
            "total_trades": len(trades),
            "total_volume": total_volume,
            "total_commission": total_commission,
            "avg_price": avg_price,
            "buy_volume": buy_volume,
            "sell_volume": sell_volume,
        }


class PositionService:
    """Domain service for position operations"""

    def __init__(self, position_repository: Repository[Position]):
        self._position_repository = position_repository

    async def get_or_create_position(self, symbol: str) -> Position:
        """Get existing position or create new one"""
        all_positions = await self._position_repository.find_all()
        position = next((p for p in all_positions if p.symbol == symbol), None)

        if position is None:
            position_id = PositionId.create()
            position = Position(
                position_id=position_id,
                symbol=symbol,
                quantity=0,
                avg_price=0.0
            )
            await self._position_repository.save(position)

        return position

    async def update_position_from_trade(self, trade: Trade) -> Position:
        """Update position based on a trade"""
        position = await self.get_or_create_position(trade.symbol)
        position.update_position(trade)
        await self._position_repository.save(position)
        return position

    async def get_position_by_symbol(self, symbol: str) -> Optional[Position]:
        """Get position by symbol"""
        all_positions = await self._position_repository.find_all()
        return next((p for p in all_positions if p.symbol == symbol), None)

    async def get_all_positions(self) -> List[Position]:
        """Get all positions"""
        return await self._position_repository.find_all()

    async def get_positions_with_market_value(self, market_prices: Dict[str, float]) -> List[Dict[str, Any]]:
        """Get all positions with calculated market values"""
        positions = await self.get_all_positions()

        result = []
        for position in positions:
            current_price = market_prices.get(position.symbol, 0.0)
            position_dict = position.to_dict(current_price)
            result.append(position_dict)

        return result

    async def get_portfolio_summary(self, market_prices: Dict[str, float]) -> Dict[str, Any]:
        """Get portfolio summary with all positions"""
        positions = await self.get_positions_with_market_value(market_prices)

        total_market_value = sum(p.get("market_value", 0) for p in positions)
        total_cost_basis = sum(p.get("cost_basis", 0) for p in positions)
        total_unrealized_pnl = sum(p.get("unrealized_pnl", 0) for p in positions)

        # Calculate weighted average metrics
        long_positions = [p for p in positions if p.get("is_long", False)]
        short_positions = [p for p in positions if p.get("is_short", False)]

        return {
            "total_market_value": total_market_value,
            "total_cost_basis": total_cost_basis,
            "total_unrealized_pnl": total_unrealized_pnl,
            "total_return_percent": (total_unrealized_pnl / total_cost_basis * 100) if total_cost_basis > 0 else 0,
            "position_count": len(positions),
            "long_positions": len(long_positions),
            "short_positions": len(short_positions),
            "positions": positions,
        }

    async def get_concentration_risk(self, market_prices: Dict[str, float]) -> List[Dict[str, Any]]:
        """Get concentration risk analysis"""
        summary = await self.get_portfolio_summary(market_prices)
        total_value = summary["total_market_value"]

        if total_value == 0:
            return []

        concentration_risk = []
        for position in summary["positions"]:
            weight = (position["market_value"] / total_value) * 100
            concentration_risk.append({
                "symbol": position["symbol"],
                "weight_percent": weight,
                "risk_level": "HIGH" if weight > 20 else "MEDIUM" if weight > 10 else "LOW"
            })

        # Sort by weight descending
        concentration_risk.sort(key=lambda x: x["weight_percent"], reverse=True)

        return concentration_risk
