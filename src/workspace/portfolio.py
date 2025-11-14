"""
投資組合追蹤
實時監控和記錄投資組合表現
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """持倉"""
    symbol: str
    quantity: float
    avg_cost: float  # 平均成本
    current_price: float = 0.0
    market_value: float = 0.0
    unrealized_pnl: float = 0.0  # 未實現損益
    unrealized_pnl_pct: float = 0.0  # 未實現損益百分比
    updated_at: str = None

    def __post_init__(self):
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()
        self._calculate_pnl()

    def _calculate_pnl(self):
        """計算損益"""
        if self.current_price > 0:
            self.market_value = self.quantity * self.current_price
            self.unrealized_pnl = (self.current_price - self.avg_cost) * self.quantity
            if self.avg_cost > 0:
                self.unrealized_pnl_pct = (self.current_price - self.avg_cost) / self.avg_cost * 100


@dataclass
class Portfolio:
    """投資組合"""
    user_id: str
    name: str
    cash: float
    positions: Dict[str, Position] = None
    total_value: float = 0.0
    total_pnl: float = 0.0
    total_pnl_pct: float = 0.0
    day_change: float = 0.0
    day_change_pct: float = 0.0
    created_at: str = None
    updated_at: str = None

    def __post_init__(self):
        if self.positions is None:
            self.positions = {}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'user_id': self.user_id,
            'name': self.name,
            'cash': self.cash,
            'positions': {k: asdict(v) for k, v in self.positions.items()},
            'total_value': self.total_value,
            'total_pnl': self.total_pnl,
            'total_pnl_pct': self.total_pnl_pct,
            'day_change': self.day_change,
            'day_change_pct': self.day_change_pct,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Portfolio':
        """從字典創建"""
        positions = {k: Position(**v) for k, v in data['positions'].items()}
        return cls(
            user_id=data['user_id'],
            name=data['name'],
            cash=data['cash'],
            positions=positions,
            total_value=data.get('total_value', 0.0),
            total_pnl=data.get('total_pnl', 0.0),
            total_pnl_pct=data.get('total_pnl_pct', 0.0),
            day_change=data.get('day_change', 0.0),
            day_change_pct=data.get('day_change_pct', 0.0),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
        )


class PortfolioManager:
    """投資組合管理器"""

    def __init__(self, data_dir: str = "workspace_data/portfolios"):
        self.data_dir = data_dir
        self.portfolios: Dict[str, Portfolio] = {}
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """確保數據目錄存在"""
        import os
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def create_portfolio(
        self,
        user_id: str,
        name: str,
        initial_cash: float = 100000.0
    ) -> Portfolio:
        """
        創建新投資組合

        Args:
            user_id: 用戶ID
            name: 組合名稱
            initial_cash: 初始現金

        Returns:
            新投資組合
        """
        portfolio = Portfolio(
            user_id=user_id,
            name=name,
            cash=initial_cash,
            positions={},
            total_value=initial_cash
        )

        portfolio_id = f"{user_id}_{name}"
        self.portfolios[portfolio_id] = portfolio
        self._save_portfolio(portfolio_id, portfolio)

        logger.info(f"Created portfolio {name} for user {user_id}")
        return portfolio

    def get_portfolio(self, user_id: str, name: str) -> Optional[Portfolio]:
        """
        獲取投資組合

        Args:
            user_id: 用戶ID
            name: 組合名稱

        Returns:
            投資組合或None
        """
        portfolio_id = f"{user_id}_{name}"

        if portfolio_id in self.portfolios:
            return self.portfolios[portfolio_id]

        # 嘗試從文件加載
        portfolio = self._load_portfolio(portfolio_id)
        if portfolio:
            self.portfolios[portfolio_id] = portfolio
            return portfolio

        return None

    def list_portfolios(self, user_id: str) -> List[str]:
        """
        列出用戶的投資組合

        Args:
            user_id: 用戶ID

        Returns:
            組合名稱列表
        """
        return [
            name for name in self.portfolios.keys()
            if name.startswith(f"{user_id}_")
        ]

    def add_position(
        self,
        user_id: str,
        portfolio_name: str,
        symbol: str,
        quantity: float,
        price: float
    ) -> bool:
        """
        添加持倉

        Args:
            user_id: 用戶ID
            portfolio_name: 組合名稱
            symbol: 股票代碼
            quantity: 數量
            price: 價格

        Returns:
            是否成功
        """
        portfolio = self.get_portfolio(user_id, portfolio_name)
        if not portfolio:
            return False

        if symbol in portfolio.positions:
            # 更新現有持倉
            pos = portfolio.positions[symbol]
            new_quantity = pos.quantity + quantity
            new_avg_cost = (pos.avg_cost * pos.quantity + price * quantity) / new_quantity
            pos.quantity = new_quantity
            pos.avg_cost = new_avg_cost
        else:
            # 新持倉
            portfolio.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                avg_cost=price
            )

        # 更新現金
        portfolio.cash -= price * quantity

        # 重新計算組合價值
        self._recalculate_portfolio(portfolio)

        portfolio.updated_at = datetime.now().isoformat()
        self._save_portfolio(f"{user_id}_{portfolio_name}", portfolio)

        logger.info(f"Added position {symbol} to portfolio {portfolio_name}")
        return True

    def remove_position(
        self,
        user_id: str,
        portfolio_name: str,
        symbol: str,
        quantity: Optional[float] = None
    ) -> bool:
        """
        移除持倉

        Args:
            user_id: 用戶ID
            portfolio_name: 組合名稱
            symbol: 股票代碼
            quantity: 移除數量（None表示全部）

        Returns:
            是否成功
        """
        portfolio = self.get_portfolio(user_id, portfolio_name)
        if not portfolio or symbol not in portfolio.positions:
            return False

        pos = portfolio.positions[symbol]

        if quantity is None or quantity >= pos.quantity:
            # 全部賣出
            del portfolio.positions[symbol]
            portfolio.cash += pos.quantity * pos.current_price
        else:
            # 部分賣出
            pos.quantity -= quantity
            portfolio.cash += quantity * pos.current_price

        # 重新計算組合價值
        self._recalculate_portfolio(portfolio)

        portfolio.updated_at = datetime.now().isoformat()
        self._save_portfolio(f"{user_id}_{portfolio_name}", portfolio)

        logger.info(f"Removed position {symbol} from portfolio {portfolio_name}")
        return True

    def update_prices(
        self,
        user_id: str,
        portfolio_name: str,
        price_data: Dict[str, float]
    ) -> bool:
        """
        更新價格

        Args:
            user_id: 用戶ID
            portfolio_name: 組合名稱
            price_data: 價格數據 {symbol: price}

        Returns:
            是否成功
        """
        portfolio = self.get_portfolio(user_id, portfolio_name)
        if not portfolio:
            return False

        # 保存舊價值
        old_total = portfolio.total_value

        # 更新價格
        for symbol, price in price_data.items():
            if symbol in portfolio.positions:
                pos = portfolio.positions[symbol]
                pos.current_price = price
                pos.updated_at = datetime.now().isoformat()

        # 重新計算組合價值
        self._recalculate_portfolio(portfolio)

        # 計算日變化
        if old_total > 0:
            portfolio.day_change = portfolio.total_value - old_total
            portfolio.day_change_pct = (portfolio.day_change / old_total) * 100

        portfolio.updated_at = datetime.now().isoformat()
        self._save_portfolio(f"{user_id}_{portfolio_name}", portfolio)

        return True

    def get_portfolio_summary(self, user_id: str, portfolio_name: str) -> Optional[Dict[str, Any]]:
        """
        獲取組合摘要

        Args:
            user_id: 用戶ID
            portfolio_name: 組合名稱

        Returns:
            組合摘要字典
        """
        portfolio = self.get_portfolio(user_id, portfolio_name)
        if not portfolio:
            return None

        # 計算持倉分佈
        position_weights = {}
        if portfolio.total_value > 0:
            for symbol, pos in portfolio.positions.items():
                weight = (pos.quantity * pos.current_price) / portfolio.total_value * 100
                position_weights[symbol] = weight

        # 計算表現指標
        performance = {
            'total_return': portfolio.total_pnl_pct,
            'day_return': portfolio.day_change_pct,
            'cash_percentage': (portfolio.cash / portfolio.total_value * 100) if portfolio.total_value > 0 else 100,
        }

        return {
            'name': portfolio.name,
            'total_value': portfolio.total_value,
            'cash': portfolio.cash,
            'total_pnl': portfolio.total_pnl,
            'total_pnl_pct': portfolio.total_pnl_pct,
            'day_change': portfolio.day_change,
            'day_change_pct': portfolio.day_change_pct,
            'position_count': len(portfolio.positions),
            'position_weights': position_weights,
            'performance': performance,
            'updated_at': portfolio.updated_at,
        }

    def _recalculate_portfolio(self, portfolio: Portfolio):
        """重新計算組合價值"""
        total_value = portfolio.cash
        total_pnl = 0

        for pos in portfolio.positions.values():
            pos._calculate_pnl()
            total_value += pos.market_value
            total_pnl += pos.unrealized_pnl

        portfolio.total_value = total_value
        portfolio.total_pnl = total_pnl

        if total_value > 0:
            portfolio.total_pnl_pct = (total_pnl / (total_value - total_pnl)) * 100

    def _save_portfolio(self, portfolio_id: str, portfolio: Portfolio):
        """保存組合到文件"""
        import os
        file_path = os.path.join(self.data_dir, f"{portfolio_id}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(portfolio.to_dict(), f, indent=2, ensure_ascii=False)

    def _load_portfolio(self, portfolio_id: str) -> Optional[Portfolio]:
        """從文件加載組合"""
        import os
        file_path = os.path.join(self.data_dir, f"{portfolio_id}.json")
        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return Portfolio.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load portfolio {portfolio_id}: {e}")
            return None

    def delete_portfolio(self, user_id: str, portfolio_name: str) -> bool:
        """刪除投資組合"""
        portfolio_id = f"{user_id}_{portfolio_name}"

        if portfolio_id not in self.portfolios:
            return False

        del self.portfolios[portfolio_id]

        # 刪除文件
        import os
        file_path = os.path.join(self.data_dir, f"{portfolio_id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)

        logger.info(f"Deleted portfolio {portfolio_name} for user {user_id}")
        return True


# 導出
__all__ = [
    'PortfolioManager',
    'Portfolio',
    'Position',
]
