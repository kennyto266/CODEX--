"""
期权数据支持模块 (T195)
=======================

提供完整的期权数据处理能力，包括：
- 期权链数据
- 隐含波动率
- Greeks计算
- 期权策略
- 波动率曲面

Author: Claude Code
Date: 2025-11-09
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from scipy import optimize
from scipy.stats import norm

from .cache import LRUCache
from .validator import DataValidator


class OptionType(str, Enum):
    """期权类型"""
    CALL = "CALL"
    PUT = "PUT"


class OptionStyle(str, Enum):
    """期权风格"""
    EUROPEAN = "EUROPEAN"
    AMERICAN = "AMERICAN"
    BARRIER = "BARRIER"


class GreeksType(str, Enum):
    """Greeks类型"""
    DELTA = "DELTA"
    GAMMA = "GAMMA"
    THETA = "THETA"
    VEGA = "VEGA"
    RHO = "RHO"


@dataclass
class OptionContract:
    """期权合约"""
    symbol: str  # 标的股票代码
    option_symbol: str  # 期权代码
    expiration_date: date  # 到期日
    strike_price: Decimal  # 行权价
    option_type: OptionType  # 期权类型
    style: OptionStyle = OptionStyle.EUROPEAN
    # 市场数据
    bid: Optional[Decimal] = None  # 买价
    ask: Optional[Decimal] = None  # 卖价
    last_price: Optional[Decimal] = None  # 最新价
    volume: Optional[int] = None  # 成交量
    open_interest: Optional[int] = None  # 未平仓合约
    # Greeks
    delta: Optional[Decimal] = None  # Delta
    gamma: Optional[Decimal] = None  # Gamma
    theta: Optional[Decimal] = None  # Theta
    vega: Optional[Decimal] = None  # Vega
    rho: Optional[Decimal] = None  # Rho
    # 隐含波动率
    implied_volatility: Optional[Decimal] = None  # 隐含波动率
    # 元数据
    contract_size: int = 100  # 合约乘数
    currency: str = "HKD"
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class OptionChain:
    """期权链"""
    symbol: str  # 标的股票代码
    as_of_date: date  # 数据日期
    underlying_price: Decimal  # 标的价格
    expiration_date: date  # 到期日
    calls: List[OptionContract] = field(default_factory=list)  # 认购期权
    puts: List[OptionContract] = field(default_factory=list)  # 认沽期权
    # 期权链指标
    call_volume: Optional[int] = None
    put_volume: Optional[int] = None
    put_call_ratio: Optional[Decimal] = None  # 认沽认购比
    max_pain: Optional[Decimal] = None  # 最大痛点
    open_interest_ratio: Optional[Decimal] = None
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class VolatilitySmile:
    """波动率微笑"""
    symbol: str
    date: date
    expiration_date: date
    strikes: List[Decimal]  # 行权价列表
    call_vols: List[Decimal]  # 认购期权隐含波动率
    put_vols: List[Decimal]  # 认沽期权隐含波动率
    model: str = "SABR"  # 波动率模型
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class VolatilitySurface:
    """波动率曲面"""
    symbol: str
    date: date
    strikes: List[Decimal]
    expirations: List[date]
    vol_matrix: np.ndarray  # 波动率矩阵 [expirations x strikes]
    interpolation_method: str = "SABR"
    last_updated: datetime = field(default_factory=datetime.now)


class OptionsDataManager:
    """
    期权数据管理器

    功能：
    1. 获取期权链数据
    2. 计算隐含波动率
    3. 计算Greeks
    4. 构建波动率曲面
    5. 分析期权策略
    """

    def __init__(
        self,
        cache_size: int = 1000,
        cache_ttl: float = 300.0,  # 5分钟
        risk_free_rate: float = 0.03
    ):
        self.logger = logging.getLogger("hk_quant_system.options")
        self.cache = LRUCache(max_size=cache_size, ttl=cache_ttl)
        self.risk_free_rate = risk_free_rate
        self.validator = DataValidator()
        self._data_sources: Dict[str, Any] = {}

    def register_data_source(self, name: str, source: Any) -> None:
        """
        注册数据源

        Args:
            name: 数据源名称
            source: 数据源对象
        """
        self._data_sources[name] = source
        self.logger.info(f"Registered options data source: {name}")

    async def get_option_chain(
        self,
        symbol: str,
        as_of_date: Optional[date] = None
    ) -> Dict[date, OptionChain]:
        """
        获取期权链

        Args:
            symbol: 股票代码
            as_of_date: 数据日期

        Returns:
            到期日 -> 期权链的字典
        """
        if as_of_date is None:
            as_of_date = date.today()

        cache_key = f"option_chain:{symbol}:{as_of_date.isoformat()}"

        # 检查缓存
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        # 从数据源获取
        option_chains = {}

        for source_name, source in self._data_sources.items():
            try:
                if hasattr(source, 'get_option_chain'):
                    raw_chains = await source.get_option_chain(symbol, as_of_date)
                    option_chains.update(raw_chains)
            except Exception as e:
                self.logger.error(f"Error fetching option chain from {source_name}: {e}")

        # 验证和计算
        validated_chains = {}
        for exp_date, chain in option_chains.items():
            validated_chain = self._validate_and_enhance_chain(chain)
            if validated_chain:
                validated_chains[exp_date] = validated_chain

        # 缓存结果
        self.cache.set(cache_key, validated_chains)

        return validated_chains

    async def get_implied_volatility(
        self,
        option: OptionContract,
        underlying_price: Decimal,
        time_to_expiration: float
    ) -> Decimal:
        """
        计算隐含波动率

        使用Newton-Raphson方法

        Args:
            option: 期权合约
            underlying_price: 标的价格
            time_to_expiration: 到期时间（年）

        Returns:
            隐含波动率
        """
        if option.last_price is None:
            raise ValueError("期权价格未提供")

        # 使用中间价
        if option.bid and option.ask:
            option_price = (option.bid + option.ask) / 2
        else:
            option_price = option.last_price

        # 初始猜测
        vol_guess = 0.2

        try:
            # Newton-Raphson迭代
            for _ in range(100):  # 最多迭代100次
                price = self._bsm_price(
                    option_price=option_price,
                    underlying=underlying_price,
                    strike=option.strike_price,
                    time_to_exp=time_to_expiration,
                    risk_free_rate=self.risk_free_rate,
                    volatility=vol_guess,
                    option_type=option.option_type
                )

                # 计算Vega
                vega = self._bsm_vega(
                    underlying=underlying_price,
                    strike=option.strike_price,
                    time_to_exp=time_to_expiration,
                    risk_free_rate=self.risk_free_rate,
                    volatility=vol_guess
                )

                if abs(vega) < 1e-6:
                    break

                # 更新波动率
                diff = price - float(option_price)
                vol_guess -= diff / vega

                if abs(diff) < 1e-6:
                    break

            return Decimal(str(vol_guess))
        except Exception as e:
            self.logger.error(f"Error calculating implied volatility: {e}")
            return Decimal('0.2')  # 默认值

    async def calculate_greeks(
        self,
        option: OptionContract,
        underlying_price: Decimal,
        time_to_expiration: float,
        implied_vol: Optional[Decimal] = None
    ) -> Dict[str, Decimal]:
        """
        计算期权Greeks

        Args:
            option: 期权合约
            underlying_price: 标的价格
            time_to_expiration: 到期时间（年）
            implied_vol: 隐含波动率

        Returns:
            Greeks字典
        """
        if implied_vol is None:
            if option.implied_volatility:
                implied_vol = option.implied_volatility
            else:
                # 使用默认值
                implied_vol = Decimal('0.2')

        greeks = {}

        try:
            greeks['delta'] = self._bsm_delta(
                underlying=underlying_price,
                strike=option.strike_price,
                time_to_exp=time_to_expiration,
                risk_free_rate=self.risk_free_rate,
                volatility=implied_vol,
                option_type=option.option_type
            )

            greeks['gamma'] = self._bsm_gamma(
                underlying=underlying_price,
                strike=option.strike_price,
                time_to_exp=time_to_expiration,
                risk_free_rate=self.risk_free_rate,
                volatility=implied_vol
            )

            greeks['theta'] = self._bsm_theta(
                underlying=underlying_price,
                strike=option.strike_price,
                time_to_exp=time_to_expiration,
                risk_free_rate=self.risk_free_rate,
                volatility=implied_vol,
                option_type=option.option_type
            )

            greeks['vega'] = self._bsm_vega(
                underlying=underlying_price,
                strike=option.strike_price,
                time_to_exp=time_to_expiration,
                risk_free_rate=self.risk_free_rate,
                volatility=implied_vol
            )

            greeks['rho'] = self._bsm_rho(
                underlying=underlying_price,
                strike=option.strike_price,
                time_to_exp=time_to_expiration,
                risk_free_rate=self.risk_free_rate,
                volatility=implied_vol,
                option_type=option.option_type
            )

        except Exception as e:
            self.logger.error(f"Error calculating greeks: {e}")

        return greeks

    async def build_volatility_smile(
        self,
        symbol: str,
        expiration_date: date,
        as_of_date: Optional[date] = None
    ) -> Optional[VolatilitySmile]:
        """
        构建波动率微笑

        Args:
            symbol: 股票代码
            expiration_date: 到期日
            as_of_date: 数据日期

        Returns:
            波动率微笑
        """
        if as_of_date is None:
            as_of_date = date.today()

        cache_key = f"vol_smile:{symbol}:{expiration_date.isoformat()}:{as_of_date.isoformat()}"

        # 检查缓存
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        # 获取期权链
        option_chains = await self.get_option_chain(symbol, as_of_date)
        chain = option_chains.get(expiration_date)

        if not chain:
            return None

        # 提取行权价和隐含波动率
        calls = chain.calls
        puts = chain.puts

        strikes = sorted(list(set([c.strike_price for c in calls] + [p.strike_price for p in puts])))
        call_vols = []
        put_vols = []

        for strike in strikes:
            # 认购期权
            call = next((c for c in calls if c.strike_price == strike), None)
            call_vol = call.implied_volatility if call and call.implied_volatility else Decimal('0.0')
            call_vols.append(call_vol)

            # 认沽期权
            put = next((p for p in puts if p.strike_price == strike), None)
            put_vol = put.implied_volatility if put and put.implied_volatility else Decimal('0.0')
            put_vols.append(put_vol)

        # 构建波动率微笑
        smile = VolatilitySmile(
            symbol=symbol,
            date=as_of_date,
            expiration_date=expiration_date,
            strikes=strikes,
            call_vols=call_vols,
            put_vols=put_vols
        )

        # 缓存结果
        self.cache.set(cache_key, smile)

        return smile

    async def build_volatility_surface(
        self,
        symbol: str,
        as_of_date: Optional[date] = None
    ) -> Optional[VolatilitySurface]:
        """
        构建波动率曲面

        Args:
            symbol: 股票代码
            as_of_date: 数据日期

        Returns:
            波动率曲面
        """
        if as_of_date is None:
            as_of_date = date.today()

        cache_key = f"vol_surface:{symbol}:{as_of_date.isoformat()}"

        # 检查缓存
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        # 获取所有期权链
        option_chains = await self.get_option_chain(symbol, as_of_date)

        if not option_chains:
            return None

        # 收集所有行权价和到期日
        all_strikes = set()
        all_expirations = sorted(option_chains.keys())

        for chain in option_chains.values():
            all_strikes.update([c.strike_price for c in chain.calls])
            all_strikes.update([p.strike_price for p in chain.puts])

        strikes = sorted(all_strikes)

        # 构建波动率矩阵
        vol_matrix = np.zeros((len(all_expirations), len(strikes)))

        for i, exp_date in enumerate(all_expirations):
            chain = option_chains[exp_date]

            # 计算平均隐含波动率
            all_vols = []
            for contract in chain.calls + chain.puts:
                if contract.implied_volatility:
                    all_vols.append(float(contract.implied_volatility))

            avg_vol = np.mean(all_vols) if all_vols else 0.2
            vol_matrix[i, :] = avg_vol

        surface = VolatilitySurface(
            symbol=symbol,
            date=as_of_date,
            strikes=strikes,
            expirations=all_expirations,
            vol_matrix=vol_matrix
        )

        # 缓存结果
        self.cache.set(cache_key, surface)

        return surface

    async def analyze_option_strategy(
        self,
        strategy_type: str,
        symbol: str,
        underlying_price: Decimal,
        **params
    ) -> Dict[str, Any]:
        """
        分析期权策略

        Args:
            strategy_type: 策略类型
            symbol: 股票代码
            underlying_price: 标的价格
            **params: 策略参数

        Returns:
            策略分析结果
        """
        analysis = {
            'strategy_type': strategy_type,
            'symbol': symbol,
            'underlying_price': underlying_price,
            'max_profit': None,
            'max_loss': None,
            'breakeven': [],
            'probability': None,
            'payoff_diagram': []
        }

        if strategy_type == 'covered_call':
            analysis.update(self._analyze_covered_call(underlying_price, **params))
        elif strategy_type == 'protective_put':
            analysis.update(self._analyze_protective_put(underlying_price, **params))
        elif strategy_type == 'straddle':
            analysis.update(self._analyze_straddle(underlying_price, **params))
        elif strategy_type == 'strangle':
            analysis.update(self._analyze_strangle(underlying_price, **params))
        elif strategy_type == 'iron_condor':
            analysis.update(self._analyze_iron_condor(underlying_price, **params))

        return analysis

    def _bsm_price(
        self,
        option_price: Decimal,
        underlying: Decimal,
        strike: Decimal,
        time_to_exp: float,
        risk_free_rate: float,
        volatility: Decimal,
        option_type: OptionType
    ) -> float:
        """Black-Scholes-Merton期权定价"""
        S = float(underlying)
        K = float(strike)
        T = time_to_exp
        r = risk_free_rate
        sigma = float(volatility)

        if T <= 0:
            # 到期时期权价值
            if option_type == OptionType.CALL:
                return max(0, S - K)
            else:
                return max(0, K - S)

        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        if option_type == OptionType.CALL:
            price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

        return price

    def _bsm_delta(
        self,
        underlying: Decimal,
        strike: Decimal,
        time_to_exp: float,
        risk_free_rate: float,
        volatility: Decimal,
        option_type: OptionType
    ) -> Decimal:
        """计算Delta"""
        S = float(underlying)
        K = float(strike)
        T = time_to_exp
        r = risk_free_rate
        sigma = float(volatility)

        if T <= 0:
            return Decimal('0')

        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))

        if option_type == OptionType.CALL:
            return Decimal(str(norm.cdf(d1)))
        else:
            return Decimal(str(norm.cdf(d1) - 1))

    def _bsm_gamma(
        self,
        underlying: Decimal,
        strike: Decimal,
        time_to_exp: float,
        risk_free_rate: float,
        volatility: Decimal
    ) -> Decimal:
        """计算Gamma"""
        S = float(underlying)
        K = float(strike)
        T = time_to_exp
        r = risk_free_rate
        sigma = float(volatility)

        if T <= 0:
            return Decimal('0')

        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))

        return Decimal(str(gamma))

    def _bsm_theta(
        self,
        underlying: Decimal,
        strike: Decimal,
        time_to_exp: float,
        risk_free_rate: float,
        volatility: Decimal,
        option_type: OptionType
    ) -> Decimal:
        """计算Theta"""
        S = float(underlying)
        K = float(strike)
        T = time_to_exp
        r = risk_free_rate
        sigma = float(volatility)

        if T <= 0:
            return Decimal('0')

        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        term1 = -S * norm.pdf(d1) * sigma / (2 * np.sqrt(T))
        if option_type == OptionType.CALL:
            term2 = -r * K * np.exp(-r * T) * norm.cdf(d2)
            theta = term1 + term2
        else:
            term2 = r * K * np.exp(-r * T) * norm.cdf(-d2)
            theta = term1 + term2

        return Decimal(str(theta))

    def _bsm_vega(
        self,
        underlying: Decimal,
        strike: Decimal,
        time_to_exp: float,
        risk_free_rate: float,
        volatility: Decimal
    ) -> Decimal:
        """计算Vega"""
        S = float(underlying)
        K = float(strike)
        T = time_to_exp
        r = risk_free_rate
        sigma = float(volatility)

        if T <= 0:
            return Decimal('0')

        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        vega = S * norm.pdf(d1) * np.sqrt(T)

        return Decimal(str(vega))

    def _bsm_rho(
        self,
        underlying: Decimal,
        strike: Decimal,
        time_to_exp: float,
        risk_free_rate: float,
        volatility: Decimal,
        option_type: OptionType
    ) -> Decimal:
        """计算Rho"""
        S = float(underlying)
        K = float(strike)
        T = time_to_exp
        r = risk_free_rate
        sigma = float(volatility)

        if T <= 0:
            return Decimal('0')

        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        if option_type == OptionType.CALL:
            rho = K * T * np.exp(-r * T) * norm.cdf(d2)
        else:
            rho = -K * T * np.exp(-r * T) * norm.cdf(-d2)

        return Decimal(str(rho))

    def _validate_and_enhance_chain(
        self,
        chain: OptionChain
    ) -> Optional[OptionChain]:
        """
        验证和增强期权链

        Args:
            chain: 原始期权链

        Returns:
            增强后的期权链
        """
        # 计算最大痛点
        chain.max_pain = self._calculate_max_pain(chain)

        # 计算认沽认购比
        total_call_volume = sum(c.volume or 0 for c in chain.calls)
        total_put_volume = sum(p.volume or 0 for p in chain.puts)

        if total_call_volume > 0:
            chain.put_call_ratio = Decimal(str(total_put_volume / total_call_volume))

        return chain

    def _calculate_max_pain(self, chain: OptionChain) -> Decimal:
        """
        计算最大痛点

        Args:
            chain: 期权链

        Returns:
            最大痛点价格
        """
        all_strikes = set([c.strike_price for c in chain.calls] + [p.strike_price for p in chain.puts])
        pain_values = {}

        for strike in all_strikes:
            total_pain = Decimal('0')

            # 计算认购期权损失
            for call in chain.calls:
                if call.strike_price == strike and call.open_interest:
                    total_pain += call.open_interest * max(0, call.strike_price - strike)

            # 计算认沽期权损失
            for put in chain.puts:
                if put.strike_price == strike and put.open_interest:
                    total_pain += put.open_interest * max(0, strike - put.strike_price)

            pain_values[strike] = total_pain

        # 找到最大痛点
        if pain_values:
            return max(pain_values.keys(), key=lambda k: pain_values[k])
        return Decimal('0')

    def _analyze_covered_call(
        self,
        underlying_price: Decimal,
        **params
    ) -> Dict[str, Any]:
        """分析备兑看涨期权策略"""
        call_strike = params.get('call_strike', underlying_price)
        call_premium = params.get('call_premium', Decimal('0'))

        return {
            'max_profit': (call_strike - underlying_price) + call_premium,
            'max_loss': underlying_price,
            'breakeven': [underlying_price - call_premium],
            'probability': 0.5
        }

    def _analyze_protective_put(
        self,
        underlying_price: Decimal,
        **params
    ) -> Dict[str, Any]:
        """分析保护性看跌期权策略"""
        put_strike = params.get('put_strike', underlying_price)
        put_premium = params.get('put_premium', Decimal('0'))

        return {
            'max_profit': float('inf'),
            'max_loss': (underlying_price - put_strike) + put_premium,
            'breakeven': [underlying_price + put_premium],
            'probability': 0.5
        }

    def _analyze_straddle(
        self,
        underlying_price: Decimal,
        **params
    ) -> Dict[str, Any]:
        """分析跨式策略"""
        strike = params.get('strike', underlying_price)
        call_premium = params.get('call_premium', Decimal('0'))
        put_premium = params.get('put_premium', Decimal('0'))
        total_premium = call_premium + put_premium

        return {
            'max_profit': float('inf'),
            'max_loss': total_premium,
            'breakeven': [strike - total_premium, strike + total_premium],
            'probability': 0.4
        }

    def _analyze_strangle(
        self,
        underlying_price: Decimal,
        **params
    ) -> Dict[str, Any]:
        """分析宽跨式策略"""
        call_strike = params.get('call_strike', underlying_price * Decimal('1.05'))
        put_strike = params.get('put_strike', underlying_price * Decimal('0.95'))
        call_premium = params.get('call_premium', Decimal('0'))
        put_premium = params.get('put_premium', Decimal('0'))
        total_premium = call_premium + put_premium

        return {
            'max_profit': float('inf'),
            'max_loss': total_premium,
            'breakeven': [put_strike - total_premium, call_strike + total_premium],
            'probability': 0.35
        }

    def _analyze_iron_condor(
        self,
        underlying_price: Decimal,
        **params
    ) -> Dict[str, Any]:
        """分析铁鹰式策略"""
        # 简化实现
        return {
            'max_profit': params.get('credit', Decimal('0')),
            'max_loss': params.get('width', Decimal('5')) - params.get('credit', Decimal('0')),
            'breakeven': [params.get('lower_breakeven', underlying_price * Decimal('0.98')),
                         params.get('upper_breakeven', underlying_price * Decimal('1.02'))],
            'probability': 0.6
        }

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "status": "healthy",
            "cache_size": len(self.cache._cache),
            "data_sources": list(self._data_sources.keys()),
            "risk_free_rate": self.risk_free_rate,
            "last_check": datetime.now().isoformat()
        }


# 辅助函数
async def get_option_chain(symbol: str) -> Dict[date, OptionChain]:
    """
    获取期权链的便捷函数

    Args:
        symbol: 股票代码

    Returns:
        期权链字典
    """
    manager = OptionsDataManager()
    return await manager.get_option_chain(symbol)


async def calculate_implied_volatility(
    option_price: float,
    underlying_price: float,
    strike_price: float,
    time_to_expiration: float,
    risk_free_rate: float = 0.03,
    option_type: str = "CALL"
) -> float:
    """
    计算隐含波动率的便捷函数

    Args:
        option_price: 期权价格
        underlying_price: 标的价格
        strike_price: 行权价
        time_to_expiration: 到期时间（年）
        risk_free_rate: 无风险利率
        option_type: 期权类型

    Returns:
        隐含波动率
    """
    manager = OptionsDataManager(risk_free_rate=risk_free_rate)

    # 创建临时期权合约
    contract = OptionContract(
        symbol="TEMP",
        option_symbol="TEMP",
        expiration_date=date.today() + timedelta(days=365),
        strike_price=Decimal(str(strike_price)),
        option_type=OptionType.CALL if option_type == "CALL" else OptionType.PUT,
        last_price=Decimal(str(option_price))
    )

    iv = await manager.get_implied_volatility(
        contract,
        Decimal(str(underlying_price)),
        time_to_expiration
    )

    return float(iv)


if __name__ == "__main__":
    # 测试代码
    async def test():
        manager = OptionsDataManager()

        # 测试获取期权链
        chains = await manager.get_option_chain("0700.HK")
        print(f"Option chains: {len(chains)}")

    asyncio.run(test())
