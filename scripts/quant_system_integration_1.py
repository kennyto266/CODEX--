"""
量化系统集成器
将真实非价格数据融入量化交易系统

基于OpenSpec规范实现：
- 数据接入量化系统
- 与现有AI Agent整合
- 支持实时决策
- 回测功能
- 策略优化

功能：
1. 使用真实HIBOR影响交易决策
2. 旅客数据预测消费股表现
3. 物业数据分析地产股走势
4. 宏观因子提升预测准确性
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass
import pandas as pd
import numpy as np
import asyncio

from ..data_adapters.real.hibor_adapter import HKMHiborAdapter
from ..data_adapters.real.property_adapter import PropertyDataAdapter
from ..data_adapters.real.tourism_adapter import TourismDataAdapter
from ..data_processing.real_data_cleaner import RealDataCleaner

logger = logging.getLogger(__name__)


@dataclass
class TradingSignal:
    """交易信号"""
    symbol: str
    signal_type: str  # 'BUY', 'SELL', 'HOLD'
    strength: float  # 信号强度 (0-1)
    price: float  # 当前价格
    timestamp: datetime
    factors: Dict[str, float]  # 影响因素
    confidence: float  # 信心度 (0-1)
    reason: str  # 信号原因


@dataclass
class EnhancedStrategy:
    """增强策略"""
    name: str
    base_strategy: str
    signals: List[TradingSignal]
    data_sources: List[str]
    performance_metrics: Dict[str, float]
    created_at: datetime


class FactorCalculator:
    """因子计算器

    计算基于真实非价格数据的交易因子
    """

    @staticmethod
    def calculate_hibor_impact(
        hibor_data: pd.DataFrame,
        price_data: pd.DataFrame,
        symbols: List[str]
    ) -> pd.DataFrame:
        """
        计算HIBOR对股价的影响

        HIBOR上升对利率敏感股(如银行股)负面影响
        """
        factors = pd.DataFrame(index=price_data.index)

        # 获取HIBOR数据
        if not hibor_data.empty:
            # 计算HIBOR变化率
            hibor_change = hibor_data['rate'].pct_change()
            hibor_level = (hibor_data['rate'] - hibor_data['rate'].rolling(30).mean()) / hibor_data['rate'].rolling(30).std()

            # 银行股受HIBOR影响较大
            bank_stocks = ['0939.HK', '3988.HK', '1398.HK']  # 建行、工行、中行

            for symbol in symbols:
                if symbol in price_data.columns:
                    # 计算股价变化
                    price_change = price_data[symbol].pct_change()

                    # HIBOR上升，股价下跌 (负相关)
                    if not hibor_change.empty:
                        correlation = hibor_change.corr(price_change.dropna())

                        # 影响因子 = HIBOR变化 * 相关性
                        impact = -hibor_change * correlation if not pd.isna(correlation) else 0
                        factors[f'{symbol}_hibor_impact'] = impact.fillna(0)

                        # HIBOR水平因子
                        factors[f'{symbol}_hibor_level'] = -hibor_level.fillna(0)

                        # HIBOR趋势因子
                        hibor_trend = hibor_data['rate'].rolling(5).mean().pct_change()
                        factors[f'{symbol}_hibor_trend'] = -hibor_trend.fillna(0)
                    else:
                        factors[f'{symbol}_hibor_impact'] = 0
                        factors[f'{symbol}_hibor_level'] = 0
                        factors[f'{symbol}_hibor_trend'] = 0
        else:
            # 如果没有HIBOR数据，填充0
            for symbol in symbols:
                factors[f'{symbol}_hibor_impact'] = 0
                factors[f'{symbol}_hibor_level'] = 0
                factors[f'{symbol}_hibor_trend'] = 0

        return factors

    @staticmethod
    def calculate_property_sentiment(
        property_data: pd.DataFrame,
        symbols: List[str]
    ) -> pd.DataFrame:
        """
        计算物业市场情绪因子

        物业市场火热可能带动地产股上涨
        """
        factors = pd.DataFrame(index=[0])  # 物业数据通常是月度数据

        # 计算物业市场指标
        if not property_data.empty:
            # 平均成交价格
            avg_price = property_data['price_per_sqft'].mean()

            # 交易量
            transaction_volume = len(property_data)

            # 价格趋势 (最近3个月)
            if len(property_data) >= 3:
                recent_prices = property_data['price_per_sqft'].tail(3)
                price_trend = (recent_prices.iloc[-1] - recent_prices.iloc[0]) / recent_prices.iloc[0]
            else:
                price_trend = 0

            # 市场情绪评分 (0-1)
            if price_trend > 0.05:  # 上涨超过5%
                sentiment = 0.8
            elif price_trend > 0:
                sentiment = 0.6
            elif price_trend > -0.05:
                sentiment = 0.4
            else:
                sentiment = 0.2

            factors['property_sentiment'] = sentiment
            factors['property_price_trend'] = price_trend
            factors['property_volume'] = transaction_volume / 1000  # 标准化
            factors['property_avg_price'] = avg_price / 10000  # 标准化

        else:
            factors['property_sentiment'] = 0.5
            factors['property_price_trend'] = 0
            factors['property_volume'] = 0
            factors['property_avg_price'] = 0

        # 地产股列表
        property_stocks = ['0001.HK', '0012.HK', '0016.HK', '0823.HK']  # 长江、新鸿基、新世界、领展

        for symbol in symbols:
            if symbol in property_stocks:
                # 地产股受物业市场情绪影响
                factors[f'{symbol}_property_sentiment'] = factors['property_sentiment']
                factors[f'{symbol}_property_trend'] = factors['property_price_trend']
            else:
                factors[f'{symbol}_property_sentiment'] = 0
                factors[f'{symbol}_property_trend'] = 0

        return factors

    @staticmethod
    def calculate_tourism_momentum(
        tourism_data: pd.DataFrame,
        symbols: List[str]
    ) -> pd.DataFrame:
        """
        计算旅客流量动量因子

        旅客流量增长可能带动消费股上涨
        """
        factors = pd.DataFrame(index=[0])  # 旅客数据通常是月度数据

        # 计算旅客流量指标
        if not tourism_data.empty:
            # 总访客数
            total_visitors = tourism_data['visitor_count'].sum()

            # 访客增长趋势
            if len(tourism_data) >= 3:
                recent_visitors = tourism_data['visitor_count'].tail(3)
                visitor_growth = (recent_visitors.iloc[-1] - recent_visitors.iloc[0]) / recent_visitors.iloc[0]
            else:
                visitor_growth = 0

            # 大陆访客比例
            mainland_visitors = tourism_data[tourism_data['country'] == 'CN']['visitor_count'].sum()
            mainland_ratio = mainland_visitors / total_visitors if total_visitors > 0 else 0

            # 旅游动量评分 (0-1)
            if visitor_growth > 0.1:  # 增长超过10%
                momentum = 0.8
            elif visitor_growth > 0:
                momentum = 0.6
            elif visitor_growth > -0.1:
                momentum = 0.4
            else:
                momentum = 0.2

            factors['tourism_momentum'] = momentum
            factors['visitor_growth'] = visitor_growth
            factors['mainland_ratio'] = mainland_ratio
            factors['total_visitors'] = total_visitors / 1000000  # 标准化

        else:
            factors['tourism_momentum'] = 0.5
            factors['visitor_growth'] = 0
            factors['mainland_ratio'] = 0.5
            factors['total_visitors'] = 0

        # 消费股列表 (零售、餐饮、酒店等)
        consumer_stocks = [
            '0197.HK',  # 六福
            '1928.HK',  # 金沙
            '2382.HK',  # 周大福
            '2319.HK',  # 蒙牛
            '1068.HK'   # 雨润
        ]

        for symbol in symbols:
            if symbol in consumer_stocks:
                # 消费股受旅客流量影响
                factors[f'{symbol}_tourism_momentum'] = factors['tourism_momentum']
                factors[f'{symbol}_visitor_boost'] = factors['visitor_growth']
            else:
                factors[f'{symbol}_tourism_momentum'] = 0
                factors[f'{symbol}_visitor_boost'] = 0

        return factors

    @staticmethod
    def calculate_macro_composite(
        hibor_data: pd.DataFrame,
        property_data: pd.DataFrame,
        tourism_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        计算宏观综合因子

        综合考虑HIBOR、物业、旅客数据
        """
        factors = pd.DataFrame(index=[0])

        # HIBOR因子
        if not hibor_data.empty:
            # HIBOR处于历史高位是负面因子
            hibor_level = (hibor_data['rate'].iloc[-1] - hibor_data['rate'].mean()) / hibor_data['rate'].std()
            hibor_factor = max(0, 1 - (hibor_level + 2) / 4)  # 标准化到0-1
        else:
            hibor_factor = 0.5

        # 物业因子
        if not property_data.empty:
            if len(property_data) >= 2:
                property_trend = (property_data['price_per_sqft'].iloc[-1] - property_data['price_per_sqft'].iloc[0]) / property_data['price_per_sqft'].iloc[0]
            else:
                property_trend = 0
            property_factor = 0.5 + property_trend  # 基于趋势调整
        else:
            property_factor = 0.5

        # 旅客因子
        if not tourism_data.empty:
            visitor_growth = tourism_data['visitor_count'].pct_change().mean()
            tourism_factor = 0.5 + visitor_growth if not pd.isna(visitor_growth) else 0.5
        else:
            tourism_factor = 0.5

        # 综合因子 (加权平均)
        macro_factor = (hibor_factor * 0.4 + property_factor * 0.3 + tourism_factor * 0.3)

        factors['macro_composite'] = macro_factor
        factors['hibor_factor'] = hibor_factor
        factors['property_factor'] = property_factor
        factors['tourism_factor'] = tourism_factor
        factors['macro_stability'] = 1 - abs(macro_factor - 0.5) * 2  # 稳定性指标

        return factors


class QuantSystemIntegrator:
    """量化系统集成器

    将真实非价格数据融入量化交易系统
    """

    def __init__(self):
        self.factor_calculator = FactorCalculator()
        self.cleaner = RealDataCleaner()

    async def enhance_strategy_with_real_data(
        self,
        strategy: str,  # 策略名称
        symbols: List[str],
        price_data: pd.DataFrame,
        start_date: str,
        end_date: str
    ) -> EnhancedStrategy:
        """
        使用真实非价格数据增强策略

        Args:
            strategy: 策略名称
            symbols: 股票代码列表
            price_data: 价格数据
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            EnhancedStrategy: 增强后的策略
        """
        logger.info(f"开始增强{strategy}策略，股票: {symbols}")

        # 1. 获取股票价格数据 (已有)
        if price_data.empty:
            raise ValueError("价格数据为空")

        # 2. 获取真实非价格数据
        hibor_data = await self._fetch_real_hibor_data(start_date, end_date)
        property_data = await self._fetch_real_property_data(start_date, end_date)
        tourism_data = await self._fetch_real_tourism_data(start_date, end_date)

        # 3. 计算增强因子
        enhanced_factors = self.factor_calculator.calculate_enhanced_factors(
            price_data=price_data,
            hibor_data=hibor_data,
            property_data=property_data,
            tourism_data=tourism_data
        )

        # 4. 生成增强信号
        enhanced_signals = await self._generate_enhanced_signals(
            strategy=strategy,
            symbols=symbols,
            price_data=price_data,
            enhanced_factors=enhanced_factors
        )

        # 5. 计算性能指标
        performance_metrics = self._calculate_performance_metrics(
            price_data, enhanced_signals
        )

        enhanced_strategy = EnhancedStrategy(
            name=f"Enhanced_{strategy}",
            base_strategy=strategy,
            signals=enhanced_signals,
            data_sources=['PRICE', 'HIBOR', 'PROPERTY', 'TOURISM'],
            performance_metrics=performance_metrics,
            created_at=datetime.now()
        )

        logger.info(f"策略增强完成，生成了{len(enhanced_signals)}个信号")
        return enhanced_strategy

    async def _fetch_real_hibor_data(
        self,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """获取真实HIBOR数据"""
        try:
            # 模拟真实数据获取
            # 在实际实现中，这里会调用真实的适配器
            adapter = HKMHiborAdapter(
                type('Config', (), {
                    'api_key': 'your_api_key',
                    'base_url': 'https://api.hkma.gov.hk'
                })()
            )

            async with adapter as hibor_adapter:
                raw_data = await hibor_adapter.fetch_real_data(
                    period=['1m', '3m', '6m'],
                    start_date=start_date,
                    end_date=end_date
                )

            # 转换为DataFrame
            if raw_data:
                data_dict = {}
                for item in raw_data:
                    period = item.data['period']
                    if period not in data_dict:
                        data_dict[period] = []

                    data_dict[period].append({
                        'date': pd.to_datetime(item.data['date']),
                        'rate': float(item.data['rate'])
                    })

                # 合并为一个DataFrame
                dfs = []
                for period, data in data_dict.items():
                    df = pd.DataFrame(data).set_index('date')
                    df.columns = [f'rate_{period}']
                    dfs.append(df)

                if dfs:
                    return pd.concat(dfs, axis=1).sort_index()
            return pd.DataFrame()

        except Exception as e:
            logger.error(f"获取HIBOR数据失败: {e}")
            return pd.DataFrame()

    async def _fetch_real_property_data(
        self,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """获取真实物业数据"""
        try:
            # 模拟真实数据获取
            adapter = PropertyDataAdapter(
                type('Config', (), {
                    'api_key': 'your_api_key',
                    'base_url': 'https://www.rvd.gov.hk'
                })()
            )

            async with adapter as property_adapter:
                raw_data = await property_adapter.fetch_real_data(
                    start_date=start_date,
                    end_date=end_date,
                    data_type='transaction'
                )

            # 转换为DataFrame
            if raw_data:
                data = []
                for item in raw_data:
                    data.append({
                        'date': pd.to_datetime(item.data['transaction_date']),
                        'price_per_sqft': float(item.data['price_per_sqft']),
                        'area': float(item.data['area']),
                        'price': float(item.data['price'])
                    })

                df = pd.DataFrame(data)
                if not df.empty:
                    return df.set_index('date').sort_index()
            return pd.DataFrame()

        except Exception as e:
            logger.error(f"获取物业数据失败: {e}")
            return pd.DataFrame()

    async def _fetch_real_tourism_data(
        self,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """获取真实旅客数据"""
        try:
            # 模拟真实数据获取
            adapter = TourismDataAdapter(
                type('Config', (), {
                    'api_key': 'your_api_key',
                    'base_url': 'https://www.discoverhongkong.com'
                })()
            )

            async with adapter as tourism_adapter:
                raw_data = await tourism_adapter.fetch_real_data(
                    visitor_type='arrival'
                )

            # 转换为DataFrame
            if raw_data:
                data = []
                for item in raw_data:
                    data.append({
                        'date': pd.to_datetime(item.data['date']),
                        'country': item.data['country'],
                        'visitor_count': int(item.data['visitor_count'])
                    })

                df = pd.DataFrame(data)
                if not df.empty:
                    return df.set_index('date').sort_index()
            return pd.DataFrame()

        except Exception as e:
            logger.error(f"获取旅客数据失败: {e}")
            return pd.DataFrame()

    async def _generate_enhanced_signals(
        self,
        strategy: str,
        symbols: List[str],
        price_data: pd.DataFrame,
        enhanced_factors: pd.DataFrame
    ) -> List[TradingSignal]:
        """生成增强交易信号"""
        signals = []

        # 获取最新数据点
        latest_price = price_data.iloc[-1] if not price_data.empty else None
        latest_factors = enhanced_factors.iloc[-1] if not enhanced_factors.empty else pd.Series()

        for symbol in symbols:
            if symbol not in price_data.columns:
                continue

            current_price = latest_price[symbol] if latest_price is not None else 0

            # 基础技术信号
            rsi = self._calculate_rsi(price_data[symbol])
            macd = self._calculate_macd(price_data[symbol])

            # 真实数据增强因子
            hibor_factor = latest_factors.get(f'{symbol}_hibor_impact', 0)
            property_factor = latest_factors.get(f'{symbol}_property_sentiment', 0)
            tourism_factor = latest_factors.get(f'{symbol}_tourism_momentum', 0)
            macro_factor = latest_factors.get('macro_composite', 0.5)

            # 综合评分
            signal_score = self._calculate_signal_score(
                rsi=rsi,
                macd=macd,
                hibor_factor=hibor_factor,
                property_factor=property_factor,
                tourism_factor=tourism_factor,
                macro_factor=macro_factor
            )

            # 生成信号
            signal_type = 'HOLD'
            if signal_score > 0.6:
                signal_type = 'BUY'
            elif signal_score < 0.4:
                signal_type = 'SELL'

            # 计算信心度
            confidence = abs(signal_score - 0.5) * 2

            signal = TradingSignal(
                symbol=symbol,
                signal_type=signal_type,
                strength=abs(signal_score - 0.5),
                price=current_price,
                timestamp=datetime.now(),
                factors={
                    'rsi': rsi,
                    'macd': macd,
                    'hibor_impact': hibor_factor,
                    'property_sentiment': property_factor,
                    'tourism_momentum': tourism_factor,
                    'macro_composite': macro_factor
                },
                confidence=confidence,
                reason=f"综合评分: {signal_score:.2f}"
            )

            signals.append(signal)

        return signals

    def _calculate_rsi(self, price_series: pd.Series, period: int = 14) -> float:
        """计算RSI指标"""
        if len(price_series) < period + 1:
            return 50.0

        delta = price_series.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi.iloc[-1] if not rsi.empty else 50.0

    def _calculate_macd(self, price_series: pd.Series) -> float:
        """计算MACD指标"""
        if len(price_series) < 26:
            return 0.0

        exp1 = price_series.ewm(span=12).mean()
        exp2 = price_series.ewm(span=26).mean()
        macd = exp1 - exp2

        return macd.iloc[-1] if not macd.empty else 0.0

    def _calculate_signal_score(
        self,
        rsi: float,
        macd: float,
        hibor_factor: float,
        property_factor: float,
        tourism_factor: float,
        macro_factor: float
    ) -> float:
        """计算综合信号评分"""
        # 基础技术评分
        technical_score = 0.5
        if rsi < 30:  # 超卖
            technical_score += 0.3
        elif rsi > 70:  # 超买
            technical_score -= 0.3

        if macd > 0:  # MACD为正
            technical_score += 0.1
        else:
            technical_score -= 0.1

        # 真实数据增强评分
        real_data_score = (
            (1 - hibor_factor) * 0.3 +  # HIBOR负面影响
            property_factor * 0.3 +  # 物业市场正面
            tourism_factor * 0.2 +  # 旅客流量正面
            macro_factor * 0.2  # 宏观环境
        )

        # 综合评分 (技术60% + 真实数据40%)
        combined_score = technical_score * 0.6 + real_data_score * 0.4

        return max(0, min(1, combined_score))

    def _calculate_performance_metrics(
        self,
        price_data: pd.DataFrame,
        signals: List[TradingSignal]
    ) -> Dict[str, float]:
        """计算性能指标"""
        metrics = {
            'signal_count': len(signals),
            'buy_signals': len([s for s in signals if s.signal_type == 'BUY']),
            'sell_signals': len([s for s in signals if s.signal_type == 'SELL']),
            'hold_signals': len([s for s in signals if s.signal_type == 'HOLD']),
            'average_confidence': np.mean([s.confidence for s in signals]) if signals else 0,
            'strong_signals': len([s for s in signals if s.strength > 0.5]) if signals else 0
        }

        return metrics

    async def backtest_enhanced_strategy(
        self,
        enhanced_strategy: EnhancedStrategy,
        price_data: pd.DataFrame,
        benchmark_symbol: str = '0700.HK'
    ) -> Dict[str, Any]:
        """
        回测增强策略

        Args:
            enhanced_strategy: 增强策略
            price_data: 价格数据
            benchmark_symbol: 基准股票

        Returns:
            Dict[str, Any]: 回测结果
        """
        logger.info(f"开始回测策略: {enhanced_strategy.name}")

        # 模拟交易过程
        portfolio_value = 100000  # 初始资金10万
        positions = {}
        trades = []

        for signal in enhanced_strategy.signals:
            symbol = signal.symbol
            signal_type = signal.signal_type
            current_price = signal.price

            # 模拟交易
            if signal_type == 'BUY' and signal.confidence > 0.6:
                # 买入逻辑
                if symbol not in positions:
                    positions[symbol] = {'shares': 0, 'cost': 0}

                # 计算买入金额 (10%资金)
                buy_amount = portfolio_value * 0.1
                shares = int(buy_amount / current_price)

                if shares > 0:
                    trades.append({
                        'date': signal.timestamp,
                        'symbol': symbol,
                        'action': 'BUY',
                        'shares': shares,
                        'price': current_price,
                        'confidence': signal.confidence
                    })

                    positions[symbol]['shares'] += shares
                    positions[symbol]['cost'] += shares * current_price
                    portfolio_value -= shares * current_price

            elif signal_type == 'SELL' and symbol in positions:
                # 卖出逻辑
                shares = positions[symbol]['shares']
                if shares > 0:
                    trades.append({
                        'date': signal.timestamp,
                        'symbol': symbol,
                        'action': 'SELL',
                        'shares': shares,
                        'price': current_price,
                        'confidence': signal.confidence
                    })

                    portfolio_value += shares * current_price
                    del positions[symbol]

        # 计算最终收益
        final_portfolio_value = portfolio_value
        for symbol, position in positions.items():
            # 使用最后一个价格计算持仓价值
            if symbol in price_data.columns:
                last_price = price_data[symbol].iloc[-1]
                final_portfolio_value += position['shares'] * last_price

        total_return = (final_portfolio_value - 100000) / 100000

        # 计算基准收益
        benchmark_return = 0
        if benchmark_symbol in price_data.columns:
            benchmark_start = price_data[benchmark_symbol].iloc[0]
            benchmark_end = price_data[benchmark_symbol].iloc[-1]
            benchmark_return = (benchmark_end - benchmark_start) / benchmark_start

        backtest_result = {
            'strategy_name': enhanced_strategy.name,
            'initial_value': 100000,
            'final_value': final_portfolio_value,
            'total_return': total_return,
            'benchmark_return': benchmark_return,
            'excess_return': total_return - benchmark_return,
            'total_trades': len(trades),
            'winning_trades': len([t for t in trades if t['action'] == 'SELL']) if trades else 0,
            'win_rate': len([t for t in trades if t['action'] == 'SELL']) / len(trades) if trades else 0,
            'data_sources_used': enhanced_strategy.data_sources,
            'trades': trades
        }

        logger.info(f"回测完成: 收益率 {total_return:.2%}")
        return backtest_result


# 扩展因子计算器
class EnhancedFactorCalculator(FactorCalculator):
    """扩展的因子计算器"""

    def calculate_enhanced_factors(
        self,
        price_data: pd.DataFrame,
        hibor_data: pd.DataFrame,
        property_data: pd.DataFrame,
        tourism_data: pd.DataFrame
    ) -> pd.DataFrame:
        """计算增强因子"""
        factors = pd.DataFrame(index=price_data.index)

        # 获取所有股票列表
        symbols = [col for col in price_data.columns if col.endswith('.HK')]

        # 1. HIBOR影响因子
        hibor_factors = self.calculate_hibor_impact(hibor_data, price_data, symbols)
        factors = pd.concat([factors, hibor_factors], axis=1)

        # 2. 物业市场因子
        if not property_data.empty:
            property_factors = self.calculate_property_sentiment(property_data, symbols)
            # 扩展到价格数据的时间索引
            expanded_property = pd.DataFrame(
                index=price_data.index,
                columns=property_factors.columns
            )
            expanded_property = expanded_property.fillna(method='ffill').fillna(0)
            factors = pd.concat([factors, expanded_property], axis=1)

        # 3. 旅客流量因子
        if not tourism_data.empty:
            tourism_factors = self.calculate_tourism_momentum(tourism_data, symbols)
            # 扩展到价格数据的时间索引
            expanded_tourism = pd.DataFrame(
                index=price_data.index,
                columns=tourism_factors.columns
            )
            expanded_tourism = expanded_tourism.fillna(method='ffill').fillna(0)
            factors = pd.concat([factors, expanded_tourism], axis=1)

        # 4. 宏观综合因子
        macro_factors = self.calculate_macro_composite(hibor_data, property_data, tourism_data)
        # 扩展到价格数据的时间索引
        expanded_macro = pd.DataFrame(
            index=price_data.index,
            columns=macro_factors.columns
        )
        expanded_macro = expanded_macro.fillna(method='ffill').fillna(0.5)
        factors = pd.concat([factors, expanded_macro], axis=1)

        return factors
