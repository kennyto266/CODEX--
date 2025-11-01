"""
交易信号生成器

根据技术指标和策略生成交易信号
支持多种策略：
- RSI超买超卖
- MACD交叉
- 移动平均线
- 布林带
- KDJ指标
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np

from realtime_execution_engine import TradeSignal, ExecutionStrategy, OrderSide


class SignalType(str, Enum):
    """信号类型"""
    TECHNICAL = "technical"    # 技术指标信号
    FUNDAMENTAL = "fundamental"  # 基本面信号
    NEWS = "news"              # 新闻事件信号
    ALGO = "algo"              # 算法交易信号


class SignalStrength(str, Enum):
    """信号强度"""
    WEAK = "weak"
    MEDIUM = "medium"
    STRONG = "strong"


@dataclass
class SignalConfig:
    """信号配置"""
    symbol: str
    strategy: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    min_confidence: float = 0.6


class TechnicalSignalGenerator:
    """技术指标信号生成器"""

    def __init__(self, data_source=None):
        self.data_source = data_source  # 数据源接口
        self.logger = logging.getLogger("hk_quant_system.trading.signals")

        # 策略配置
        self.strategies = {
            'rsi': self._rsi_signal,
            'macd': self._macd_signal,
            'ma_crossover': self._ma_crossover_signal,
            'bollinger_bands': self._bollinger_bands_signal,
            'kdj': self._kdj_signal,
            ' CCI': self._cci_signal,
        }

        # 信号缓存
        self.signal_cache: Dict[str, Dict] = {}

    async def generate_signal(
        self,
        symbol: str,
        strategy: str,
        data: pd.DataFrame,
        **kwargs
    ) -> Optional[TradeSignal]:
        """生成交易信号"""
        try:
            # 验证数据
            if data.empty or len(data) < 50:  # 需要足够的历史数据
                self.logger.warning(f"数据不足，无法生成信号: {symbol}")
                return None

            # 执行策略
            if strategy not in self.strategies:
                self.logger.error(f"未知策略: {strategy}")
                return None

            signal_data = await self.strategies[strategy](symbol, data, **kwargs)

            if not signal_data:
                return None

            # 构建交易信号
            trade_signal = TradeSignal(
                signal_id=f"{symbol}_{strategy}_{int(datetime.now().timestamp())}",
                symbol=symbol,
                side=signal_data['side'],
                quantity=Decimal(str(signal_data.get('quantity', 1000))),
                strategy=signal_data.get('strategy', ExecutionStrategy.IMMEDIATE),
                price=signal_data.get('price'),
                timestamp=datetime.now(),
                metadata={
                    'signal_type': SignalType.TECHNICAL.value,
                    'strategy': strategy,
                    'confidence': signal_data.get('confidence', 0.0),
                    'strength': signal_data.get('strength', SignalStrength.MEDIUM.value),
                    'indicators': signal_data.get('indicators', {}),
                    'reason': signal_data.get('reason', '')
                }
            )

            self.logger.info(
                f"生成信号: {symbol} {signal_data['side'].value} "
                f"数量:{trade_signal.quantity} 策略:{strategy}"
            )

            return trade_signal

        except Exception as e:
            self.logger.error(f"生成信号失败: {e}")
            return None

    async def _rsi_signal(
        self,
        symbol: str,
        data: pd.DataFrame,
        period: int = 14,
        oversold: float = 30,
        overbought: float = 70
    ) -> Optional[Dict]:
        """RSI超买超卖信号"""
        try:
            # 计算RSI
            close = data['Close']
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            # 获取最新值
            current_rsi = rsi.iloc[-1]
            prev_rsi = rsi.iloc[-2]

            # 生成信号
            if prev_rsi <= oversold and current_rsi > oversold:
                # RSI从超卖区域向上突破
                return {
                    'side': OrderSide.BUY,
                    'confidence': min((current_rsi - oversold) / 30, 1.0),
                    'strength': SignalStrength.STRONG if current_rsi < 20 else SignalStrength.MEDIUM,
                    'indicators': {'rsi': current_rsi},
                    'reason': f'RSI从超卖区域({prev_rsi:.2f})向上突破{oversold}'
                }
            elif prev_rsi >= overbought and current_rsi < overbought:
                # RSI从超买区域向下突破
                return {
                    'side': OrderSide.SELL,
                    'confidence': min((overbought - current_rsi) / 30, 1.0),
                    'strength': SignalStrength.STRONG if current_rsi > 80 else SignalStrength.MEDIUM,
                    'indicators': {'rsi': current_rsi},
                    'reason': f'RSI从超买区域({prev_rsi:.2f})向下跌破{overbought}'
                }

            return None

        except Exception as e:
            self.logger.error(f"RSI信号生成失败: {e}")
            return None

    async def _macd_signal(
        self,
        symbol: str,
        data: pd.DataFrame,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Optional[Dict]:
        """MACD交叉信号"""
        try:
            close = data['Close']

            # 计算MACD
            ema_fast = close.ewm(span=fast).mean()
            ema_slow = close.ewm(span=slow).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            histogram = macd_line - signal_line

            # 获取最新值
            current_macd = macd_line.iloc[-1]
            current_signal = signal_line.iloc[-1]
            current_histogram = histogram.iloc[-1]

            prev_macd = macd_line.iloc[-2]
            prev_signal = signal_line.iloc[-2]
            prev_histogram = histogram.iloc[-2]

            # 生成信号
            if prev_macd <= prev_signal and current_macd > current_signal:
                # MACD线向上突破信号线（金叉）
                return {
                    'side': OrderSide.BUY,
                    'confidence': min(abs(current_histogram) / 2, 1.0),
                    'strength': SignalStrength.STRONG if current_histogram > 0 else SignalStrength.MEDIUM,
                    'indicators': {
                        'macd': current_macd,
                        'signal': current_signal,
                        'histogram': current_histogram
                    },
                    'reason': f'MACD金叉 MACD:{current_macd:.4f} > SIGNAL:{current_signal:.4f}'
                }
            elif prev_macd >= prev_signal and current_macd < current_signal:
                # MACD线向下突破信号线（死叉）
                return {
                    'side': OrderSide.SELL,
                    'confidence': min(abs(current_histogram) / 2, 1.0),
                    'strength': SignalStrength.STRONG if current_histogram < 0 else SignalStrength.MEDIUM,
                    'indicators': {
                        'macd': current_macd,
                        'signal': current_signal,
                        'histogram': current_histogram
                    },
                    'reason': f'MACD死叉 MACD:{current_macd:.4f} < SIGNAL:{current_signal:.4f}'
                }

            return None

        except Exception as e:
            self.logger.error(f"MACD信号生成失败: {e}")
            return None

    async def _ma_crossover_signal(
        self,
        symbol: str,
        data: pd.DataFrame,
        short_period: int = 20,
        long_period: int = 50
    ) -> Optional[Dict]:
        """移动平均线交叉信号"""
        try:
            close = data['Close']

            # 计算移动平均线
            ma_short = close.rolling(window=short_period).mean()
            ma_long = close.rolling(window=long_period).mean()

            # 获取最新值
            current_short = ma_short.iloc[-1]
            current_long = ma_long.iloc[-1]
            prev_short = ma_short.iloc[-2]
            prev_long = ma_long.iloc[-2]

            # 生成信号
            if prev_short <= prev_long and current_short > current_long:
                # 短期均线上穿长期均线（金叉）
                return {
                    'side': OrderSide.BUY,
                    'confidence': 0.7,
                    'strength': SignalStrength.STRONG,
                    'indicators': {
                        'ma_short': current_short,
                        'ma_long': current_long,
                        'crossover': 'golden'
                    },
                    'reason': f'MA{short_period}上穿MA{long_period}'
                }
            elif prev_short >= prev_long and current_short < current_long:
                # 短期均线下穿长期均线（死叉）
                return {
                    'side': OrderSide.SELL,
                    'confidence': 0.7,
                    'strength': SignalStrength.STRONG,
                    'indicators': {
                        'ma_short': current_short,
                        'ma_long': current_long,
                        'crossover': 'death'
                    },
                    'reason': f'MA{short_period}下穿MA{long_period}'
                }

            return None

        except Exception as e:
            self.logger.error(f"MA交叉信号生成失败: {e}")
            return None

    async def _bollinger_bands_signal(
        self,
        symbol: str,
        data: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Optional[Dict]:
        """布林带信号"""
        try:
            close = data['Close']

            # 计算布林带
            ma = close.rolling(window=period).mean()
            std = close.rolling(window=period).std()
            upper_band = ma + (std * std_dev)
            lower_band = ma - (std * std_dev)

            # 获取最新值
            current_price = close.iloc[-1]
            current_upper = upper_band.iloc[-1]
            current_lower = lower_band.iloc[-1]

            # 生成信号
            if current_price <= current_lower:
                # 价格触及或跌破下轨
                return {
                    'side': OrderSide.BUY,
                    'confidence': 0.6,
                    'strength': SignalStrength.MEDIUM,
                    'indicators': {
                        'price': current_price,
                        'upper': current_upper,
                        'lower': current_lower,
                        'bandwidth': (current_upper - current_lower) / current_lower * 100
                    },
                    'reason': f'价格触及下轨 {current_price:.2f} < {current_lower:.2f}'
                }
            elif current_price >= current_upper:
                # 价格触及或突破上轨
                return {
                    'side': OrderSide.SELL,
                    'confidence': 0.6,
                    'strength': SignalStrength.MEDIUM,
                    'indicators': {
                        'price': current_price,
                        'upper': current_upper,
                        'lower': current_lower,
                        'bandwidth': (current_upper - current_lower) / current_lower * 100
                    },
                    'reason': f'价格触及上轨 {current_price:.2f} > {current_upper:.2f}'
                }

            return None

        except Exception as e:
            self.logger.error(f"布林带信号生成失败: {e}")
            return None

    async def _kdj_signal(
        self,
        symbol: str,
        data: pd.DataFrame,
        k_period: int = 9,
        d_period: int = 3,
        oversold: float = 20,
        overbought: float = 80
    ) -> Optional[Dict]:
        """KDJ指标信号"""
        try:
            high = data['High']
            low = data['Low']
            close = data['Close']

            # 计算RSV
            lowest_low = low.rolling(window=k_period).min()
            highest_high = high.rolling(window=k_period).max()
            rsv = (close - lowest_low) / (highest_high - lowest_low) * 100

            # 计算K、D值
            k = rsv.ewm(com=d_period - 1).mean()
            d = k.ewm(com=d_period - 1).mean()

            # 获取最新值
            current_k = k.iloc[-1]
            current_d = d.iloc[-1]
            prev_k = k.iloc[-2]
            prev_d = d.iloc[-2]

            # 生成信号
            if prev_k <= oversold and current_k > oversold and current_k < 50:
                # K值从超卖区域向上
                return {
                    'side': OrderSide.BUY,
                    'confidence': 0.65,
                    'strength': SignalStrength.MEDIUM,
                    'indicators': {
                        'k': current_k,
                        'd': current_d,
                        'oversold_threshold': oversold
                    },
                    'reason': f'KDJ超卖反弹 K:{current_k:.2f} > {oversold}'
                }
            elif prev_k >= overbought and current_k < overbought and current_k > 50:
                # K值从超买区域向下
                return {
                    'side': OrderSide.SELL,
                    'confidence': 0.65,
                    'strength': SignalStrength.MEDIUM,
                    'indicators': {
                        'k': current_k,
                        'd': current_d,
                        'overbought_threshold': overbought
                    },
                    'reason': f'KDJ超买回调 K:{current_k:.2f} < {overbought}'
                }

            return None

        except Exception as e:
            self.logger.error(f"KDJ信号生成失败: {e}")
            return None

    async def _cci_signal(
        self,
        symbol: str,
        data: pd.DataFrame,
        period: int = 20
    ) -> Optional[Dict]:
        """CCI指标信号"""
        try:
            high = data['High']
            low = data['Low']
            close = data['Close']

            # 计算典型价格
            typical_price = (high + low + close) / 3

            # 计算CCI
            ma = typical_price.rolling(window=period).mean()
            mad = typical_price.rolling(window=period).apply(
                lambda x: np.mean(np.abs(x - x.mean()))
            )
            cci = (typical_price - ma) / (0.015 * mad)

            # 获取最新值
            current_cci = cci.iloc[-1]

            # 生成信号
            if current_cci < -100:
                return {
                    'side': OrderSide.BUY,
                    'confidence': min((abs(current_cci) - 100) / 200, 1.0),
                    'strength': SignalStrength.STRONG if current_cci < -150 else SignalStrength.MEDIUM,
                    'indicators': {'cci': current_cci},
                    'reason': f'CCI超卖区域 {current_cci:.2f}'
                }
            elif current_cci > 100:
                return {
                    'side': OrderSide.SELL,
                    'confidence': min((current_cci - 100) / 200, 1.0),
                    'strength': SignalStrength.STRONG if current_cci > 150 else SignalStrength.MEDIUM,
                    'indicators': {'cci': current_cci},
                    'reason': f'CCI超买区域 {current_cci:.2f}'
                }

            return None

        except Exception as e:
            self.logger.error(f"CCI信号生成失败: {e}")
            return None

    async def batch_generate_signals(
        self,
        symbol: str,
        strategies: List[str],
        data: pd.DataFrame,
        **kwargs
    ) -> List[TradeSignal]:
        """批量生成多个策略的信号"""
        signals = []

        for strategy in strategies:
            signal = await self.generate_signal(symbol, strategy, data, **kwargs)
            if signal:
                signals.append(signal)

        return signals


class SignalManager:
    """信号管理器"""

    def __init__(self, data_source=None):
        self.data_source = data_source
        self.logger = logging.getLogger("hk_quant_system.trading.signal_manager")

        # 初始化信号生成器
        self.generators = {
            'technical': TechnicalSignalGenerator(data_source)
        }

        # 活跃配置
        self.active_configs: Dict[str, SignalConfig] = {}

        # 信号历史
        self.signal_history: List[TradeSignal] = []

        # 统计
        self.stats = {
            'total_signals': 0,
            'buy_signals': 0,
            'sell_signals': 0,
            'avg_confidence': 0.0
        }

    async def add_signal_config(self, config: SignalConfig):
        """添加信号配置"""
        self.active_configs[config.symbol] = config
        self.logger.info(f"添加信号配置: {config.symbol} {config.strategy}")

    async def remove_signal_config(self, symbol: str):
        """移除信号配置"""
        if symbol in self.active_configs:
            del self.active_configs[symbol]
            self.logger.info(f"移除信号配置: {symbol}")

    async def scan_signals(self) -> List[TradeSignal]:
        """扫描所有配置的信号"""
        signals = []

        try:
            for symbol, config in self.active_configs.items():
                if not config.enabled:
                    continue

                # 获取数据
                data = await self._fetch_data(symbol)
                if data is None or data.empty:
                    continue

                # 生成信号
                generator = self.generators.get('technical')
                if generator:
                    signal = await generator.generate_signal(
                        symbol,
                        config.strategy,
                        data,
                        **config.parameters
                    )

                    if signal and signal.metadata.get('confidence', 0) >= config.min_confidence:
                        signals.append(signal)
                        self.signal_history.append(signal)

                        # 更新统计
                        self.stats['total_signals'] += 1
                        if signal.side == OrderSide.BUY:
                            self.stats['buy_signals'] += 1
                        else:
                            self.stats['sell_signals'] += 1

                        self.logger.info(
                            f"生成信号: {symbol} {signal.side.value} "
                            f"置信度: {signal.metadata.get('confidence', 0):.2f}"
                        )

        except Exception as e:
            self.logger.error(f"扫描信号失败: {e}")

        return signals

    async def _fetch_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """获取数据"""
        try:
            if self.data_source:
                # 从数据源获取
                return await self.data_source.fetch_historical_data(
                    symbol,
                    datetime.now() - timedelta(days=100),
                    datetime.now()
                )
            else:
                # 生成模拟数据用于测试
                dates = pd.date_range(
                    start=datetime.now() - timedelta(days=100),
                    end=datetime.now(),
                    freq='D'
                )

                # 模拟价格数据
                np.random.seed(hash(symbol) % 2**32)  # 基于symbol的稳定随机数
                base_price = 100 + np.random.random() * 900

                price_changes = np.random.normal(0, 0.02, len(dates))
                prices = [base_price]

                for change in price_changes[1:]:
                    new_price = prices[-1] * (1 + change)
                    prices.append(max(new_price, 1))

                df = pd.DataFrame({
                    'Date': dates,
                    'Open': prices,
                    'High': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
                    'Low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
                    'Close': prices,
                    'Volume': np.random.randint(1000000, 10000000, len(dates))
                })

                df.set_index('Date', inplace=True)
                return df

        except Exception as e:
            self.logger.error(f"获取数据失败: {e}")
            return None

    async def get_signal_history(
        self,
        symbol: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[TradeSignal]:
        """获取信号历史"""
        filtered = self.signal_history

        if symbol:
            filtered = [s for s in filtered if s.symbol == symbol]

        if start_time:
            filtered = [s for s in filtered if s.timestamp >= start_time]

        if end_time:
            filtered = [s for s in filtered if s.timestamp <= end_time]

        return filtered

    async def get_stats(self) -> Dict[str, Any]:
        """获取信号统计"""
        return {
            'active_configs': len(self.active_configs),
            'signal_history': len(self.signal_history),
            'stats': self.stats
        }
