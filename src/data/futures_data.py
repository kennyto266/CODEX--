"""
期货数据支持模块 (T196)
=======================

提供完整的期货数据处理能力，包括：
- 期货合约数据
- 基差分析
- 展期策略
- 仓储成本
- 交割数据

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

from .cache import LRUCache
from .validator import DataValidator


class FuturesType(str, Enum):
    """期货类型"""
    COMMODITY = "COMMODITY"  # 商品
    FINANCIAL = "FINANCIAL"  # 金融
    CURRENCY = "CURRENCY"    # 货币
    INDEX = "INDEX"          # 指数
    ENERGY = "ENERGY"        # 能源
    METAL = "METAL"          # 金属
    AGRICULTURAL = "AGRICULTURAL"  # 农产品


class DeliveryType(str, Enum):
    """交割类型"""
    PHYSICAL = "PHYSICAL"  # 实物交割
    CASH = "CASH"          # 现金交割


class ContractStatus(str, Enum):
    """合约状态"""
    ACTIVE = "ACTIVE"      # 活跃
    EXPIRED = "EXPIRED"    # 已到期
    DELIVERED = "DELIVERED"  # 已交割
    SUSPENDED = "SUSPENDED"  # 暂停


@dataclass
class FuturesContract:
    """期货合约"""
    symbol: str  # 合约代码 (如: HSI2024M)
    underlying: str  # 标的资产 (如: HSI)
    contract_month: str  # 合约月份 (如: 2024-03)
    expiration_date: date  # 到期日
    delivery_date: Optional[date] = None  # 交割日
    # 市场数据
    open_price: Optional[Decimal] = None  # 开盘价
    high_price: Optional[Decimal] = None  # 最高价
    low_price: Optional[Decimal] = None  # 最低价
    last_price: Optional[Decimal] = None  # 最新价
    volume: Optional[int] = None  # 成交量
    open_interest: Optional[int] = None  # 未平仓合约
    # 合约规格
    contract_size: Optional[Decimal] = None  # 合约乘数
    tick_size: Optional[Decimal] = None  # 最小变动价位
    margin_requirement: Optional[Decimal] = None  # 保证金要求
    # 交割信息
    delivery_type: DeliveryType = DeliveryType.CASH
    last_trading_date: Optional[date] = None  # 最后交易日
    delivery_location: Optional[str] = None  # 交割地点
    # 期货类型
    futures_type: FuturesType = FuturesType.FINANCIAL
    currency: str = "HKD"
    status: ContractStatus = ContractStatus.ACTIVE
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class BasisAnalysis:
    """基差分析"""
    symbol: str  # 期货合约代码
    date: date  # 分析日期
    futures_price: Decimal  # 期货价格
    spot_price: Decimal  # 现货价格
    basis: Decimal  # 基差 (现货 - 期货)
    basis_percent: Decimal  # 基差百分比
    # 成本分析
    carry_cost: Optional[Decimal] = None  # 持有成本
    storage_cost: Optional[Decimal] = None  # 仓储成本
    financing_cost: Optional[Decimal] = None  # 融资成本
    convenience_yield: Optional[Decimal] = None  # 便利收益
    # 统计指标
    historical_mean: Optional[Decimal] = None  # 历史均值
    historical_std: Optional[Decimal] = None  # 历史标准差
    z_score: Optional[Decimal] = None  # Z-score
    percentile: Optional[Decimal] = None  # 百分位数
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class RollStrategy:
    """展期策略"""
    symbol: str  # 标的资产
    strategy_name: str  # 策略名称
    # 当前持仓
    current_contract: str  # 当前合约
    current_expiry: date  # 当前到期日
    next_contract: str  # 下一合约
    next_expiry: date  # 下一到期日
    # 展期参数
    roll_date: date  # 展期日期
    roll_threshold: Optional[Decimal] = None  # 展期阈值
    roll_cost: Decimal = Decimal('0')  # 展期成本
    # 策略表现
    historical_rolls: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class CostOfCarry:
    """持有成本模型"""
    symbol: str
    date: date
    # 利率
    risk_free_rate: Decimal  # 无风险利率
    financing_rate: Decimal  # 融资利率
    # 成本
    storage_cost: Decimal = Decimal('0')  # 仓储成本
    insurance_cost: Decimal = Decimal('0')  # 保险成本
    transaction_cost: Decimal = Decimal('0')  # 交易成本
    # 收益
    dividend_yield: Decimal = Decimal('0')  # 股息收益率
    convenience_yield: Decimal = Decimal('0')  # 便利收益
    # 理论价格
    implied_futures_price: Optional[Decimal] = None
    fair_value: Optional[Decimal] = None
    last_updated: datetime = field(default_factory=datetime.now)


class FuturesDataManager:
    """
    期货数据管理器

    功能：
    1. 获取期货合约数据
    2. 基差分析
    3. 展期策略
    4. 持有成本计算
    5. 交割数据管理
    """

    def __init__(
        self,
        cache_size: int = 1000,
        cache_ttl: float = 300.0
    ):
        self.logger = logging.getLogger("hk_quant_system.futures")
        self.cache = LRUCache(max_size=cache_size, ttl=cache_ttl)
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
        self.logger.info(f"Registered futures data source: {name}")

    async def get_active_contracts(
        self,
        underlying: str,
        as_of_date: Optional[date] = None
    ) -> List[FuturesContract]:
        """
        获取活跃期货合约

        Args:
            underlying: 标的资产
            as_of_date: 数据日期

        Returns:
            活跃期货合约列表
        """
        if as_of_date is None:
            as_of_date = date.today()

        cache_key = f"active_contracts:{underlying}:{as_of_date.isoformat()}"

        # 检查缓存
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        # 从数据源获取
        contracts = []

        for source_name, source in self._data_sources.items():
            try:
                if hasattr(source, 'get_futures_contracts'):
                    raw_contracts = await source.get_futures_contracts(underlying, as_of_date)
                    contracts.extend(raw_contracts)
            except Exception as e:
                self.logger.error(f"Error fetching contracts from {source_name}: {e}")

        # 验证和筛选活跃合约
        active_contracts = [
            c for c in contracts
            if c.status == ContractStatus.ACTIVE and c.expiration_date >= as_of_date
        ]

        # 按到期日排序
        active_contracts.sort(key=lambda x: x.expiration_date)

        # 缓存结果
        self.cache.set(cache_key, active_contracts)

        return active_contracts

    async def get_contract_history(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        获取期货合约历史数据

        Args:
            symbol: 合约代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            历史价格DataFrame
        """
        cache_key = f"contract_history:{symbol}:{start_date.isoformat()}:{end_date.isoformat()}"

        # 检查缓存
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # 从数据源获取
        history = pd.DataFrame()

        for source_name, source in self._data_sources.items():
            try:
                if hasattr(source, 'get_futures_history'):
                    raw_history = await source.get_futures_history(symbol, start_date, end_date)
                    if not raw_history.empty:
                        history = raw_history
                        break
            except Exception as e:
                self.logger.error(f"Error fetching history from {source_name}: {e}")

        # 缓存结果
        self.cache.set(cache_key, history)

        return history

    async def analyze_basis(
        self,
        futures_symbol: str,
        spot_symbol: str,
        as_of_date: Optional[date] = None
    ) -> Optional[BasisAnalysis]:
        """
        分析基差

        Args:
            futures_symbol: 期货合约代码
            spot_symbol: 现货标的代码
            as_of_date: 分析日期

        Returns:
            基差分析结果
        """
        if as_of_date is None:
            as_of_date = date.today()

        cache_key = f"basis_analysis:{futures_symbol}:{spot_symbol}:{as_of_date.isoformat()}"

        # 检查缓存
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            # 获取期货价格
            futures_price = await self._get_latest_price(futures_symbol, as_of_date)
            # 获取现货价格
            spot_price = await self._get_latest_price(spot_symbol, as_of_date)

            if not futures_price or not spot_price:
                return None

            # 计算基差
            basis = spot_price - futures_price
            basis_percent = (basis / futures_price * 100) if futures_price > 0 else Decimal('0')

            # 创建分析对象
            analysis = BasisAnalysis(
                symbol=futures_symbol,
                date=as_of_date,
                futures_price=futures_price,
                spot_price=spot_price,
                basis=basis,
                basis_percent=basis_percent
            )

            # 计算统计指标
            historical_basis = await self._get_historical_basis(
                futures_symbol, spot_symbol, as_of_date, 252
            )
            if historical_basis:
                analysis.historical_mean = historical_basis.mean()
                analysis.historical_std = historical_basis.std()

                if analysis.historical_std and analysis.historical_std > 0:
                    analysis.z_score = (basis - analysis.historical_mean) / analysis.historical_std

                # 计算百分位数
                analysis.percentile = self._calculate_percentile(
                    basis, historical_basis
                )

            # 缓存结果
            self.cache.set(cache_key, analysis)

            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing basis: {e}")
            return None

    async def get_roll_strategy(
        self,
        underlying: str,
        strategy_type: str = "calendar_spread",
        as_of_date: Optional[date] = None
    ) -> Optional[RollStrategy]:
        """
        获取展期策略

        Args:
            underlying: 标的资产
            strategy_type: 策略类型
            as_of_date: 数据日期

        Returns:
            展期策略
        """
        if as_of_date is None:
            as_of_date = date.today()

        cache_key = f"roll_strategy:{underlying}:{strategy_type}:{as_of_date.isoformat()}"

        # 检查缓存
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        # 获取活跃合约
        contracts = await self.get_active_contracts(underlying, as_of_date)

        if len(contracts) < 2:
            return None

        current_contract = contracts[0]
        next_contract = contracts[1]

        # 创建展期策略
        strategy = RollStrategy(
            symbol=underlying,
            strategy_name=strategy_type,
            current_contract=current_contract.symbol,
            current_expiry=current_contract.expiration_date,
            next_contract=next_contract.symbol,
            next_expiry=next_contract.expiration_date,
            roll_date=as_of_date
        )

        # 计算展期成本
        if current_contract.last_price and next_contract.last_price:
            strategy.roll_cost = next_contract.last_price - current_contract.last_price

        # 缓存结果
        self.cache.set(cache_key, strategy)

        return strategy

    async def calculate_cost_of_carry(
        self,
        futures_symbol: str,
        spot_price: Decimal,
        time_to_expiration: float,
        **params
    ) -> CostOfCarry:
        """
        计算持有成本

        Args:
            futures_symbol: 期货合约代码
            spot_price: 现货价格
            time_to_expiration: 到期时间（年）
            **params: 成本参数

        Returns:
            持有成本模型
        """
        # 获取参数
        risk_free_rate = params.get('risk_free_rate', Decimal('0.03'))
        financing_rate = params.get('financing_rate', Decimal('0.05'))
        storage_cost = params.get('storage_cost', Decimal('0'))
        insurance_cost = params.get('insurance_cost', Decimal('0'))
        transaction_cost = params.get('transaction_cost', Decimal('0'))
        dividend_yield = params.get('dividend_yield', Decimal('0'))
        convenience_yield = params.get('convenience_yield', Decimal('0'))

        # 计算理论期货价格 (Cost of Carry Model)
        carry = (financing_rate + storage_cost + insurance_cost + transaction_cost
                 - dividend_yield - convenience_yield)

        implied_futures_price = spot_price * (1 + carry * time_to_expiration)

        # 创建成本模型
        carry_model = CostOfCarry(
            symbol=futures_symbol,
            date=date.today(),
            risk_free_rate=risk_free_rate,
            financing_rate=financing_rate,
            storage_cost=storage_cost,
            insurance_cost=insurance_cost,
            transaction_cost=transaction_cost,
            dividend_yield=dividend_yield,
            convenience_yield=convenience_yield,
            implied_futures_price=implied_futures_price,
            fair_value=implied_futures_price
        )

        return carry_model

    async def get_delivery_schedule(
        self,
        underlying: str,
        year: int
    ) -> List[Dict[str, Any]]:
        """
        获取交割日程

        Args:
            underlying: 标的资产
            year: 年份

        Returns:
            交割日程列表
        """
        cache_key = f"delivery_schedule:{underlying}:{year}"

        # 检查缓存
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        schedule = []

        # 遍历所有月份
        for month in range(1, 13):
            contract_month = f"{year}-{month:02d}"
            # 这里需要根据具体合约规则生成交割日期
            # 简化实现
            expiry_date = date(year, month, 28)  # 假设每月28日到期

            schedule.append({
                'contract_month': contract_month,
                'expiration_date': expiry_date,
                'last_trading_date': expiry_date - timedelta(days=2),
                'delivery_date': expiry_date,
                'delivery_type': 'CASH'
            })

        # 缓存结果
        self.cache.set(cache_key, schedule)

        return schedule

    async def analyze_calendar_spread(
        self,
        front_month: str,
        deferred_month: str,
        as_of_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        分析日历价差

        Args:
            front_month: 近月合约代码
            deferred_month: 远月合约代码
            as_of_date: 分析日期

        Returns:
            日历价差分析
        """
        if as_of_date is None:
            as_of_date = date.today()

        # 获取两个合约的价格
        front_price = await self._get_latest_price(front_month, as_of_date)
        deferred_price = await self._get_latest_price(deferred_month, as_of_date)

        if not front_price or not deferred_price:
            return {}

        spread = deferred_price - front_price
        spread_percent = (spread / front_price * 100) if front_price > 0 else Decimal('0')

        # 计算时间价值
        front_expiry = await self._get_expiry_date(front_month)
        deferred_expiry = await self._get_expiry_date(deferred_month)

        if front_expiry and deferred_expiry:
            time_spread = (deferred_expiry - front_expiry).days / 365.25
            daily_roll = spread / time_spread / 365 if time_spread > 0 else Decimal('0')
        else:
            time_spread = Decimal('0')
            daily_roll = Decimal('0')

        return {
            'front_month': front_month,
            'deferred_month': deferred_month,
            'front_price': front_price,
            'deferred_price': deferred_price,
            'spread': spread,
            'spread_percent': spread_percent,
            'time_spread_years': time_spread,
            'daily_roll_value': daily_roll,
            'roll_yield': (daily_roll / front_price * 365) if front_price > 0 else Decimal('0')
        }

    async def get_commodity_storage_rates(
        self,
        commodity: str,
        location: str,
        as_of_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        获取商品仓储费率

        Args:
            commodity: 商品名称
            location: 仓储地点
            as_of_date: 数据日期

        Returns:
            仓储费率信息
        """
        cache_key = f"storage_rates:{commodity}:{location}"

        # 检查缓存
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        # 模拟仓储费率数据 (实际应用中需要连接仓储数据源)
        storage_rates = {
            'commodity': commodity,
            'location': location,
            'base_rate': Decimal('0.50'),  # 每单位每日
            'currency': 'HKD',
            'units': 'per_ton_per_day',
            'min_storage_days': 1,
            'special_conditions': []
        }

        # 缓存结果
        self.cache.set(cache_key, storage_rates)

        return storage_rates

    async def calculate_fair_value(
        self,
        spot_price: Decimal,
        time_to_expiration: float,
        dividend_yield: Decimal,
        risk_free_rate: Decimal,
        convenience_yield: Decimal = Decimal('0'),
        storage_cost: Decimal = Decimal('0')
    ) -> Decimal:
        """
        计算期货公允价值

        Args:
            spot_price: 现货价格
            time_to_expiration: 到期时间（年）
            dividend_yield: 股息收益率
            risk_free_rate: 无风险利率
            convenience_yield: 便利收益
            storage_cost: 仓储成本

        Returns:
            期货公允价值
        """
        # 净持有成本
        net_carry = risk_free_rate + storage_cost - dividend_yield - convenience_yield

        # 计算公允价值
        fair_value = spot_price * (1 + net_carry * time_to_expiration)

        return fair_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    async def _get_latest_price(
        self,
        symbol: str,
        date: date
    ) -> Optional[Decimal]:
        """获取最新价格"""
        for source_name, source in self._data_sources.items():
            try:
                if hasattr(source, 'get_latest_price'):
                    price = await source.get_latest_price(symbol, date)
                    if price:
                        return price
            except Exception as e:
                self.logger.error(f"Error getting price from {source_name}: {e}")

        return None

    async def _get_expiry_date(self, symbol: str) -> Optional[date]:
        """获取合约到期日"""
        contracts = await self.get_active_contracts(symbol.split('.')[0])
        for contract in contracts:
            if contract.symbol == symbol:
                return contract.expiration_date

        return None

    async def _get_historical_basis(
        self,
        futures_symbol: str,
        spot_symbol: str,
        end_date: date,
        lookback_days: int
    ) -> Optional[pd.Series]:
        """获取历史基差数据"""
        start_date = end_date - timedelta(days=lookback_days)

        try:
            # 获取历史价格数据
            futures_history = await self.get_contract_history(
                futures_symbol, start_date, end_date
            )
            # 这里需要获取现货历史数据 (简化实现)
            # 实际应用中需要从现货数据源获取

            if not futures_history.empty:
                # 模拟现货数据 (实际应用中需要替换)
                np.random.seed(42)
                spot_prices = futures_history['last_price'].values * np.random.uniform(
                    0.98, 1.02, len(futures_history)
                )

                # 计算基差
                basis = spot_prices - futures_history['last_price'].values
                return pd.Series(basis, index=futures_history.index)

        except Exception as e:
            self.logger.error(f"Error getting historical basis: {e}")

        return None

    def _calculate_percentile(
        self,
        value: Decimal,
        series: pd.Series
    ) -> Decimal:
        """计算百分位数"""
        return Decimal(str((series < float(value)).mean() * 100))

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "status": "healthy",
            "cache_size": len(self.cache._cache),
            "data_sources": list(self._data_sources.keys()),
            "last_check": datetime.now().isoformat()
        }

    def clear_cache(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.logger.info("Cache cleared")


# 辅助函数
async def get_futures_contracts(underlying: str) -> List[FuturesContract]:
    """
    获取期货合约的便捷函数

    Args:
        underlying: 标的资产

    Returns:
        期货合约列表
    """
    manager = FuturesDataManager()
    return await manager.get_active_contracts(underlying)


async def calculate_futures_fair_value(
    spot_price: float,
    days_to_expiry: int,
    dividend_yield: float = 0.0,
    risk_free_rate: float = 0.03,
    convenience_yield: float = 0.0,
    storage_cost: float = 0.0
) -> float:
    """
    计算期货公允价值的便捷函数

    Args:
        spot_price: 现货价格
        days_to_expiry: 到期天数
        dividend_yield: 股息收益率
        risk_free_rate: 无风险利率
        convenience_yield: 便利收益
        storage_cost: 仓储成本

    Returns:
        期货公允价值
    """
    manager = FuturesDataManager()

    time_to_expiration = days_to_expiry / 365.25

    fair_value = await manager.calculate_fair_value(
        spot_price=Decimal(str(spot_price)),
        time_to_expiration=time_to_expiration,
        dividend_yield=Decimal(str(dividend_yield)),
        risk_free_rate=Decimal(str(risk_free_rate)),
        convenience_yield=Decimal(str(convenience_yield)),
        storage_cost=Decimal(str(storage_cost))
    )

    return float(fair_value)


if __name__ == "__main__":
    # 测试代码
    async def test():
        manager = FuturesDataManager()

        # 测试获取期货合约
        contracts = await manager.get_active_contracts("HSI")
        print(f"Active contracts: {len(contracts)}")

    asyncio.run(test())
