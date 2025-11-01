"""
商品-股票策略实现

基于商品价格变动预测相关股票走势

示例：
Given: Gold 4天累积回报 = 0.03 (3%)
When: Running CommodityStockStrategy.generate_signals()
Then: Return BUY signal for gold mining stocks
"""

from typing import Dict, List, Optional
import pandas as pd
import logging

from adapters.commodity_adapter import CommodityAdapter
from adapters.hkex_adapter import HKEXAdapter
from utils.cumulative_filter import CumulativeReturnFilter


class CommodityStockStrategy:
    """商品到股票的跨市场策略"""

    def __init__(
        self,
        commodity_symbol: str = 'GOLD',
        stock_symbol: str = '0883.HK',  # 中海油作为商品股代表
        window: int = 4,
        threshold: float = 0.03,  # 3%阈值（商品波动更大）
        holding_period: int = 14
    ):
        self.commodity_symbol = commodity_symbol
        self.stock_symbol = stock_symbol
        self.window = window
        self.threshold = threshold
        self.holding_period = holding_period

        self.commodity_adapter = CommodityAdapter()
        self.hkex_adapter = HKEXAdapter()
        self.cumulative_filter = CumulativeReturnFilter(
            window=window,
            threshold=threshold,
            enable_dynamic_threshold=True
        )

        self.logger = logging.getLogger("cross_market_quant.CommodityStockStrategy")

    async def generate_signals(
        self,
        start_date: str,
        end_date: str,
        **kwargs
    ) -> pd.DataFrame:
        """生成交易信号"""
        try:
            self.logger.info(f"生成{self.commodity_symbol} -> {self.stock_symbol}信号")

            # 获取商品数据
            commodity_data = await self.commodity_adapter.fetch_data(
                self.commodity_symbol, start_date, end_date
            )

            if commodity_data.empty:
                raise Exception(f"未能获取到{self.commodity_symbol}数据")

            # 计算累积回报
            cumulative_returns = self.cumulative_filter.calculate_cumulative_returns(
                commodity_data['Close']
            )

            # 生成信号
            signals = self.cumulative_filter.filter_signals(
                cumulative_returns=cumulative_returns,
                price_data=commodity_data['Close'],
                signal_type='auto'
            )

            result = pd.DataFrame({
                'Date': commodity_data['Date'],
                'Commodity_Price': commodity_data['Close'],
                'Cumulative_Return': cumulative_returns,
                'Signal': signals,
                'Action': signals.map(self._signal_to_action),
                'Position': 0
            })

            result['Position'] = self._calculate_positions(result['Signal'])

            return result

        except Exception as e:
            self.logger.error(f"生成信号失败: {e}")
            return pd.DataFrame()

    def _signal_to_action(self, signal: float) -> str:
        if signal == 1:
            return 'BUY'
        elif signal == -1:
            return 'SELL'
        elif signal == 0:
            return 'HOLD'
        else:
            return 'NONE'

    def _calculate_positions(self, signals: pd.Series) -> pd.Series:
        """计算持仓"""
        positions = pd.Series(index=signals.index, dtype=float)
        current_position = 0
        days_in_position = 0

        for i, signal in enumerate(signals):
            if pd.isna(signal):
                positions.iloc[i] = current_position
                continue

            if signal != 0 and current_position == 0:
                current_position = signal
                days_in_position = 1
            elif days_in_position >= self.holding_period or signal == 0:
                current_position = 0
                days_in_position = 0
            else:
                days_in_position += 1

            positions.iloc[i] = current_position

        return positions
