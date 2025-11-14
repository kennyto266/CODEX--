"""
交易歷史管理
記錄和分析交易行為
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
class Trade:
    """交易記錄"""
    id: str
    portfolio_name: str
    symbol: str
    side: str  # buy, sell
    quantity: float
    price: float
    timestamp: str
    fees: float = 0.0
    pnl: float = 0.0  # 實現損益
    notes: str = ""
    strategy: str = ""  # 使用的策略

    @property
    def value(self) -> float:
        """交易金額"""
        return self.quantity * self.price

    @property
    def total_cost(self) -> float:
        """總成本（含手續費）"""
        if self.side == 'buy':
            return self.value + self.fees
        else:
            return self.value - self.fees


@dataclass
class TradeStats:
    """交易統計"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    avg_trade: float = 0.0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    total_fees: float = 0.0

    def calculate(self, trades: List[Trade]):
        """計算統計數據"""
        if not trades:
            return

        self.total_trades = len(trades)
        self.total_pnl = sum(t.pnl for t in trades)
        self.total_fees = sum(t.fees for t in trades)

        # 計算勝負
        winning = [t for t in trades if t.pnl > 0]
        losing = [t for t in trades if t.pnl < 0]

        self.winning_trades = len(winning)
        self.losing_trades = len(losing)

        if self.total_trades > 0:
            self.win_rate = (self.winning_trades / self.total_trades) * 100

        if winning:
            self.avg_win = np.mean([t.pnl for t in winning])
            self.largest_win = max(t.pnl for t in winning)

        if losing:
            self.avg_loss = np.mean([t.pnl for t in losing])
            self.largest_loss = min(t.pnl for t in losing)

        # 利潤因子
        total_wins = sum(t.pnl for t in winning) if winning else 0
        total_losses = abs(sum(t.pnl for t in losing)) if losing else 1
        self.profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')

        # 平均交易
        if trades:
            self.avg_trade = self.total_pnl / self.total_trades

        # 連勝連敗
        current_win_streak = 0
        current_loss_streak = 0
        max_win_streak = 0
        max_loss_streak = 0

        for trade in trades:
            if trade.pnl > 0:
                current_win_streak += 1
                current_loss_streak = 0
                max_win_streak = max(max_win_streak, current_win_streak)
            elif trade.pnl < 0:
                current_loss_streak += 1
                current_win_streak = 0
                max_loss_streak = max(max_loss_streak, current_loss_streak)

        self.max_consecutive_wins = max_win_streak
        self.max_consecutive_losses = max_loss_streak


class TradeHistoryManager:
    """交易歷史管理器"""

    def __init__(self, data_dir: str = "workspace_data/trades"):
        self.data_dir = data_dir
        self.trades: Dict[str, List[Trade]] = {}  # user_id -> trades
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """確保數據目錄存在"""
        import os
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def add_trade(
        self,
        user_id: str,
        portfolio_name: str,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        fees: float = 0.0,
        notes: str = "",
        strategy: str = ""
    ) -> Trade:
        """
        添加交易記錄

        Args:
            user_id: 用戶ID
            portfolio_name: 組合名稱
            symbol: 股票代碼
            side: 買賣方向 (buy/sell)
            quantity: 數量
            price: 價格
            fees: 手續費
            notes: 備註
            strategy: 策略名稱

        Returns:
            新交易記錄
        """
        import uuid

        trade = Trade(
            id=str(uuid.uuid4()),
            portfolio_name=portfolio_name,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            timestamp=datetime.now().isoformat(),
            fees=fees,
            notes=notes,
            strategy=strategy
        )

        if user_id not in self.trades:
            self.trades[user_id] = []

        self.trades[user_id].append(trade)
        self._save_trades(user_id)

        logger.info(f"Added trade: {side} {quantity} {symbol} @ {price}")
        return trade

    def get_trades(
        self,
        user_id: str,
        portfolio_name: Optional[str] = None,
        symbol: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Trade]:
        """
        獲取交易記錄

        Args:
            user_id: 用戶ID
            portfolio_name: 組合名稱（可選）
            symbol: 股票代碼（可選）
            start_date: 開始日期（可選）
            end_date: 結束日期（可選）

        Returns:
            交易記錄列表
        """
        if user_id not in self.trades:
            return []

        trades = self.trades[user_id]

        # 篩選
        if portfolio_name:
            trades = [t for t in trades if t.portfolio_name == portfolio_name]

        if symbol:
            trades = [t for t in trades if t.symbol == symbol]

        if start_date:
            trades = [t for t in trades if t.timestamp >= start_date]

        if end_date:
            trades = [t for t in trades if t.timestamp <= end_date]

        return trades

    def calculate_pnl(self, user_id: str, portfolio_name: str) -> float:
        """
        計算組合的實現損益

        Args:
            user_id: 用戶ID
            portfolio_name: 組合名稱

        Returns:
            總實現損益
        """
        trades = self.get_trades(user_id, portfolio_name)
        return sum(trade.pnl for trade in trades)

    def get_statistics(self, user_id: str, portfolio_name: Optional[str] = None) -> TradeStats:
        """
        獲取交易統計

        Args:
            user_id: 用戶ID
            portfolio_name: 組合名稱（可選）

        Returns:
            交易統計
        """
        trades = self.get_trades(user_id, portfolio_name)

        # 如果指定了組合名稱，只計算該組合的統計
        if portfolio_name:
            trades = [t for t in trades if t.portfolio_name == portfolio_name]

        stats = TradeStats()
        stats.calculate(trades)
        return stats

    def get_monthly_pnl(self, user_id: str, year: int, month: int) -> float:
        """
        獲取月度損益

        Args:
            user_id: 用戶ID
            year: 年份
            month: 月份

        Returns:
            月度損益
        """
        if user_id not in self.trades:
            return 0.0

        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"

        trades = self.get_trades(user_id, start_date=start_date, end_date=end_date)
        return sum(t.pnl for t in trades)

    def get_daily_pnl_series(self, user_id: str, days: int = 30) -> pd.DataFrame:
        """
        獲取每日損益序列

        Args:
            user_id: 用戶ID
            days: 天數

        Returns:
            每日損益DataFrame
        """
        if user_id not in self.trades:
            return pd.DataFrame(columns=['date', 'pnl'])

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        trades = self.get_trades(
            user_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )

        if not trades:
            return pd.DataFrame(columns=['date', 'pnl'])

        # 按日期分組
        daily_pnl = {}
        for trade in trades:
            date = trade.timestamp[:10]  # YYYY-MM-DD
            if date not in daily_pnl:
                daily_pnl[date] = 0.0
            daily_pnl[date] += trade.pnl

        # 轉換為DataFrame
        df = pd.DataFrame([
            {'date': date, 'pnl': pnl}
            for date, pnl in sorted(daily_pnl.items())
        ])

        return df

    def get_symbol_performance(self, user_id: str) -> Dict[str, Dict[str, float]]:
        """
        獲取股票表現統計

        Args:
            user_id: 用戶ID

        Returns:
            股票表現字典
        """
        if user_id not in self.trades:
            return {}

        performance = {}
        for trade in self.trades[user_id]:
            symbol = trade.symbol
            if symbol not in performance:
                performance[symbol] = {
                    'total_trades': 0,
                    'total_pnl': 0.0,
                    'total_fees': 0.0,
                    'buy_count': 0,
                    'sell_count': 0,
                }

            perf = performance[symbol]
            perf['total_trades'] += 1
            perf['total_pnl'] += trade.pnl
            perf['total_fees'] += trade.fees

            if trade.side == 'buy':
                perf['buy_count'] += 1
            else:
                perf['sell_count'] += 1

        return performance

    def export_trades(self, user_id: str, format: str = 'json') -> str:
        """
        導出交易記錄

        Args:
            user_id: 用戶ID
            format: 格式 (json, csv)

        Returns:
            導出的數據
        """
        if user_id not in self.trades:
            return ""

        trades = self.trades[user_id]

        if format == 'json':
            return json.dumps([asdict(t) for t in trades], indent=2, ensure_ascii=False)
        elif format == 'csv':
            df = pd.DataFrame([asdict(t) for t in trades])
            return df.to_csv(index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _save_trades(self, user_id: str):
        """保存交易記錄到文件"""
        import os
        file_path = os.path.join(self.data_dir, f"{user_id}.json")
        trades = self.trades.get(user_id, [])
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([asdict(t) for t in trades], f, indent=2, ensure_ascii=False)

    def _load_trades(self, user_id: str):
        """從文件加載交易記錄"""
        import os
        file_path = os.path.join(self.data_dir, f"{user_id}.json")
        if not os.path.exists(file_path):
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.trades[user_id] = [Trade(**t) for t in data]
        except Exception as e:
            logger.error(f"Failed to load trades for {user_id}: {e}")

    def delete_trade(self, user_id: str, trade_id: str) -> bool:
        """刪除交易記錄"""
        if user_id not in self.trades:
            return False

        for i, trade in enumerate(self.trades[user_id]):
            if trade.id == trade_id:
                del self.trades[user_id][i]
                self._save_trades(user_id)
                return True

        return False


# 導出
__all__ = [
    'TradeHistoryManager',
    'Trade',
    'TradeStats',
]
