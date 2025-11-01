#!/usr/bin/env python3
"""
投資組合管理模組
支持投資組合的查看、添加、刪除和持久化存儲
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class PortfolioPosition:
    """投資組合持倉"""
    def __init__(self, stock_code: str, quantity: float, cost_price: float):
        self.stock_code = stock_code
        self.quantity = quantity
        self.cost_price = cost_price
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            'stock_code': self.stock_code,
            'quantity': self.quantity,
            'cost_price': self.cost_price,
            'timestamp': self.timestamp
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PortfolioPosition':
        position = cls(data['stock_code'], data['quantity'], data['cost_price'])
        position.timestamp = data.get('timestamp', datetime.now().isoformat())
        return position

class PortfolioManager:
    """投資組合管理器"""
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.portfolio_file = f"data/portfolio_{user_id}.json"
        self.positions: List[PortfolioPosition] = []
        self.load_portfolio()

    def load_portfolio(self) -> None:
        """從文件載入投資組合"""
        try:
            if os.path.exists(self.portfolio_file):
                os.makedirs(os.path.dirname(self.portfolio_file), exist_ok=True)
                with open(self.portfolio_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.positions = [PortfolioPosition.from_dict(pos) for pos in data]
                logger.info(f"載入投資組合: {self.user_id}, {len(self.positions)}個持倉")
            else:
                self.positions = []
        except Exception as e:
            logger.error(f"載入投資組合失敗: {e}")
            self.positions = []

    def save_portfolio(self) -> bool:
        """保存投資組合到文件"""
        try:
            os.makedirs(os.path.dirname(self.portfolio_file), exist_ok=True)
            with open(self.portfolio_file, 'w', encoding='utf-8') as f:
                json.dump([pos.to_dict() for pos in self.positions], f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存投資組合失敗: {e}")
            return False

    def add_position(self, stock_code: str, quantity: float, cost_price: float) -> Tuple[bool, str]:
        """添加持倉"""
        try:
            # 驗證輸入
            if not stock_code or not stock_code.endswith('.HK'):
                return False, "股票代碼格式無效，應以.HK結尾"

            if quantity <= 0:
                return False, "數量必須大於0"

            if cost_price <= 0:
                return False, "價格必須大於0"

            # 檢查是否已存在該股票
            for pos in self.positions:
                if pos.stock_code == stock_code:
                    return False, f"股票 {stock_code} 已存在於投資組合中"

            # 添加新持倉
            position = PortfolioPosition(stock_code, quantity, cost_price)
            self.positions.append(position)

            if self.save_portfolio():
                return True, f"成功添加持倉: {stock_code} {quantity}股 @ {cost_price}"
            else:
                self.positions.pop()  # 回滾
                return False, "保存失敗，請重試"
        except Exception as e:
            logger.error(f"添加持倉失敗: {e}")
            return False, f"添加持倉失敗: {str(e)}"

    def remove_position(self, stock_code: str) -> Tuple[bool, str]:
        """刪除持倉"""
        try:
            for i, pos in enumerate(self.positions):
                if pos.stock_code == stock_code:
                    removed = self.positions.pop(i)
                    if self.save_portfolio():
                        return True, f"已刪除持倉: {stock_code}"
                    else:
                        self.positions.insert(i, removed)  # 回滾
                        return False, "保存失敗，請重試"

            return False, f"投資組合中未找到股票 {stock_code}"
        except Exception as e:
            logger.error(f"刪除持倉失敗: {e}")
            return False, f"刪除持倉失敗: {str(e)}"

    def get_position(self, stock_code: str) -> Optional[PortfolioPosition]:
        """獲取指定股票持倉"""
        for pos in self.positions:
            if pos.stock_code == stock_code:
                return pos
        return None

    def list_positions(self) -> List[PortfolioPosition]:
        """列出所有持倉"""
        return self.positions.copy()

    def format_portfolio(self, market_data: Optional[Dict] = None) -> str:
        """格式化投資組合顯示"""
        if not self.positions:
            return "📊 投資組合為空\n\n使用 /portfolio add <股票代碼> <數量> <成本價> 添加持倉"

        # 計算統計信息
        total_cost = 0
        total_value = 0
        total_pnl = 0

        lines = ["📊 投資組合詳情", "=" * 40]

        for pos in self.positions:
            cost = pos.quantity * pos.cost_price
            total_cost += cost

            # 獲取市場價格
            current_price = market_data.get(pos.stock_code, {}).get('price', pos.cost_price) if market_data else pos.cost_price
            value = pos.quantity * current_price
            pnl = value - cost
            pnl_pct = (pnl / cost * 100) if cost > 0 else 0

            total_value += value
            total_pnl += pnl

            # 格式化單個持倉
            emoji = "📈" if pnl >= 0 else "📉"
            lines.append(
                f"{emoji} {pos.stock_code}\n"
                f"   數量: {pos.quantity:,.0f}股\n"
                f"   成本: ¥{pos.cost_price:,.2f}\n"
                f"   現價: ¥{current_price:,.2f}\n"
                f"   市值: ¥{value:,.2f}\n"
                f"   盈虧: ¥{pnl:,.2f} ({pnl_pct:+.2f}%)\n"
            )

        # 計算總體統計
        lines.append("=" * 40)
        total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
        lines.append(f"💰 總成本: ¥{total_cost:,.2f}")
        lines.append(f"💎 總市值: ¥{total_value:,.2f}")
        lines.append(f"📊 總盈虧: ¥{total_pnl:,.2f} ({total_pnl_pct:+.2f}%)")

        # 添加持倉占比
        if total_value > 0:
            lines.append("\n📈 持倉占比:")
            for pos in self.positions:
                current_price = market_data.get(pos.stock_code, {}).get('price', pos.cost_price) if market_data else pos.cost_price
                value = pos.quantity * current_price
                weight = (value / total_value * 100) if total_value > 0 else 0
                lines.append(f"   {pos.stock_code}: {weight:5.1f}%")

        return "\n".join(lines)
