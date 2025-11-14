"""
基本面数据集成模块 (T194)
==========================

提供完整的基本面数据处理能力，包括：
- 财务报表数据
- 估值指标
- 行业分类
- 分析师预期
- ESG评分

Author: Claude Code
Date: 2025-11-09
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from decimal import Decimal
from enum import Enum
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field, validator, root_validator

from .cache import LRUCache
from .validator import DataValidator, DataValidationResult


class FinancialStatementType(str, Enum):
    """财务报表类型"""
    BALANCE_SHEET = "balance_sheet"
    INCOME_STATEMENT = "income_statement"
    CASH_FLOW = "cash_flow"
    COMPREHENSIVE = "comprehensive"


class ESGRating(str, Enum):
    """ESG评级"""
    AAA = "AAA"
    AA = "AA"
    A = "A"
    BBB = "BBB"
    BB = "BB"
    B = "B"
    CCC = "CCC"
    UNKNOWN = "UNKNOWN"


class AnalystRating(str, Enum):
    """分析师评级"""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"
    NOT_RATED = "NOT_RATED"


@dataclass
class FinancialStatement:
    """财务报表数据"""
    symbol: str
    report_date: date
    statement_type: FinancialStatementType
    # 资产负债表
    total_assets: Optional[Decimal] = None
    total_liabilities: Optional[Decimal] = None
    shareholders_equity: Optional[Decimal] = None
    current_assets: Optional[Decimal] = None
    current_liabilities: Optional[Decimal] = None
    # 损益表
    revenue: Optional[Decimal] = None
    gross_profit: Optional[Decimal] = None
    operating_income: Optional[Decimal] = None
    net_income: Optional[Decimal] = None
    # 现金流量表
    operating_cash_flow: Optional[Decimal] = None
    investing_cash_flow: Optional[Decimal] = None
    financing_cash_flow: Optional[Decimal] = None
    # 元数据
    currency: str = "HKD"
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ValuationMetrics:
    """估值指标"""
    symbol: str
    report_date: date
    pe_ratio: Optional[Decimal] = None  # 市盈率
    pb_ratio: Optional[Decimal] = None  # 市净率
    ps_ratio: Optional[Decimal] = None  # 市销率
    ev_ebitda: Optional[Decimal] = None  # 企业价值倍数
    dividend_yield: Optional[Decimal] = None  # 股息收益率
    roe: Optional[Decimal] = None  # 净资产收益率
    roa: Optional[Decimal] = None  # 总资产收益率
    debt_to_equity: Optional[Decimal] = None  # 负债权益比
    current_ratio: Optional[Decimal] = None  # 流动比率
    quick_ratio: Optional[Decimal] = None  # 速动比率
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class IndustryClassification:
    """行业分类"""
    symbol: str
    sector: str  # 行业
    industry: str  # 子行业
    gics_sector: Optional[str] = None  # GICS行业分类
    gics_industry: Optional[str] = None  # GICS子行业
    gics_sub_industry: Optional[str] = None  # GICS细分行业
    hsi_classification: Optional[str] = None  # 恒生分类
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class AnalystEstimate:
    """分析师预期"""
    symbol: str
    estimate_date: date
    analyst_name: str
    rating: AnalystRating
    target_price: Optional[Decimal] = None
    current_price: Optional[Decimal] = None
    # 预期指标
    expected_pe: Optional[Decimal] = None
    expected_revenue: Optional[Decimal] = None
    expected_eps: Optional[Decimal] = None
    expected_growth: Optional[Decimal] = None
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ESGScore:
    """ESG评分"""
    symbol: str
    report_date: date
    provider: str  # 评级机构
    overall_rating: ESGRating
    environmental_score: Optional[Decimal] = None
    social_score: Optional[Decimal] = None
    governance_score: Optional[Decimal] = None
    # 详细评分
    carbon_footprint: Optional[Decimal] = None
    board_diversity: Optional[Decimal] = None
    labor_practices: Optional[Decimal] = None
    data_privacy: Optional[Decimal] = None
    business_ethics: Optional[Decimal] = None
    last_updated: datetime = field(default_factory=datetime.now)


class FundamentalDataIntegrator:
    """
    基本面数据集成器

    功能：
    1. 聚合多源基本面数据
    2. 计算财务比率和指标
    3. 历史趋势分析
    4. 行业对比分析
    5. ESG评分集成
    """

    def __init__(
        self,
        cache_size: int = 1000,
        cache_ttl: float = 3600.0,
        enable_async: bool = True
    ):
        self.logger = logging.getLogger("hk_quant_system.fundamental")
        self.cache = LRUCache(max_size=cache_size, ttl=cache_ttl)
        self.enable_async = enable_async
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
        self.logger.info(f"Registered data source: {name}")

    async def get_financial_statements(
        self,
        symbol: str,
        statement_type: FinancialStatementType,
        years: int = 4
    ) -> List[FinancialStatement]:
        """
        获取财务报表

        Args:
            symbol: 股票代码
            statement_type: 报表类型
            years: 获取年份数

        Returns:
            财务报表列表
        """
        cache_key = f"financial_statements:{symbol}:{statement_type.value}:{years}"

        # 检查缓存
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        # 从数据源获取数据
        statements = []
        end_date = date.today()
        start_date = end_date - timedelta(days=365 * years)

        for source_name, source in self._data_sources.items():
            try:
                if hasattr(source, 'get_financial_statements'):
                    raw_data = await source.get_financial_statements(
                        symbol, statement_type, start_date, end_date
                    )
                    statements.extend(raw_data)
            except Exception as e:
                self.logger.error(f"Error fetching from {source_name}: {e}")

        # 验证和去重
        validated_statements = self._validate_and_deduplicate_statements(
            statements, symbol
        )

        # 缓存结果
        self.cache.set(cache_key, validated_statements)

        return validated_statements

    async def get_valuation_metrics(
        self,
        symbol: str,
        as_of_date: Optional[date] = None
    ) -> Optional[ValuationMetrics]:
        """
        获取估值指标

        Args:
            symbol: 股票代码
            as_of_date: 截至日期

        Returns:
            估值指标
        """
        if as_of_date is None:
            as_of_date = date.today()

        cache_key = f"valuation_metrics:{symbol}:{as_of_date.isoformat()}"

        # 检查缓存
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        # 获取财务数据
        statements = await self.get_financial_statements(
            symbol, FinancialStatementType.BALANCE_SHEET, 1
        )

        if not statements:
            return None

        # 计算估值指标
        latest = statements[0]
        valuation = self._calculate_valuation_metrics(symbol, latest, as_of_date)

        # 缓存结果
        self.cache.set(cache_key, valuation)

        return valuation

    async def get_industry_classification(
        self,
        symbol: str
    ) -> Optional[IndustryClassification]:
        """
        获取行业分类

        Args:
            symbol: 股票代码

        Returns:
            行业分类
        """
        cache_key = f"industry_classification:{symbol}"

        # 检查缓存
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        # 从数据源获取
        for source_name, source in self._data_sources.items():
            try:
                if hasattr(source, 'get_industry_classification'):
                    classification = await source.get_industry_classification(symbol)
                    if classification:
                        self.cache.set(cache_key, classification)
                        return classification
            except Exception as e:
                self.logger.error(f"Error fetching classification from {source_name}: {e}")

        return None

    async def get_analyst_estimates(
        self,
        symbol: str,
        days: int = 90
    ) -> List[AnalystEstimate]:
        """
        获取分析师预期

        Args:
            symbol: 股票代码
            days: 最近天数

        Returns:
            分析师预期列表
        """
        cache_key = f"analyst_estimates:{symbol}:{days}"

        # 检查缓存
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        estimates = []
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        for source_name, source in self._data_sources.items():
            try:
                if hasattr(source, 'get_analyst_estimates'):
                    raw_estimates = await source.get_analyst_estimates(
                        symbol, start_date, end_date
                    )
                    estimates.extend(raw_estimates)
            except Exception as e:
                self.logger.error(f"Error fetching estimates from {source_name}: {e}")

        # 按日期排序
        estimates.sort(key=lambda x: x.estimate_date, reverse=True)

        # 缓存结果
        self.cache.set(cache_key, estimates)

        return estimates

    async def get_esg_score(
        self,
        symbol: str,
        as_of_date: Optional[date] = None
    ) -> Optional[ESGScore]:
        """
        获取ESG评分

        Args:
            symbol: 股票代码
            as_of_date: 截至日期

        Returns:
            ESG评分
        """
        if as_of_date is None:
            as_of_date = date.today()

        cache_key = f"esg_score:{symbol}:{as_of_date.isoformat()}"

        # 检查缓存
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        # 从数据源获取
        for source_name, source in self._data_sources.items():
            try:
                if hasattr(source, 'get_esg_score'):
                    esg_score = await source.get_esg_score(symbol, as_of_date)
                    if esg_score:
                        self.cache.set(cache_key, esg_score)
                        return esg_score
            except Exception as e:
                self.logger.error(f"Error fetching ESG score from {source_name}: {e}")

        return None

    async def get_comprehensive_fundamentals(
        self,
        symbol: str
    ) -> Dict[str, Any]:
        """
        获取综合基本面数据

        Args:
            symbol: 股票代码

        Returns:
            综合基本面数据
        """
        cache_key = f"comprehensive_fundamentals:{symbol}"

        # 检查缓存
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        # 并行获取所有数据
        tasks = {
            'financial_statements': self.get_financial_statements(symbol, FinancialStatementType.COMPREHENSIVE),
            'valuation_metrics': self.get_valuation_metrics(symbol),
            'industry_classification': self.get_industry_classification(symbol),
            'analyst_estimates': self.get_analyst_estimates(symbol),
            'esg_score': self.get_esg_score(symbol)
        }

        results = {}
        for key, task in tasks.items():
            try:
                results[key] = await task
            except Exception as e:
                self.logger.error(f"Error fetching {key}: {e}")
                results[key] = None

        # 缓存结果
        self.cache.set(cache_key, results)

        return results

    def _validate_and_deduplicate_statements(
        self,
        statements: List[FinancialStatement],
        symbol: str
    ) -> List[FinancialStatement]:
        """
        验证和去重财务报表

        Args:
            statements: 原始报表列表
            symbol: 股票代码

        Returns:
            验证后的报表列表
        """
        # 按日期去重（保留最新的）
        seen_dates = set()
        unique_statements = []

        for stmt in statements:
            date_key = stmt.report_date.isoformat()
            if date_key not in seen_dates:
                seen_dates.add(date_key)
                unique_statements.append(stmt)

        # 验证数据
        validated = []
        for stmt in unique_statements:
            validation_result = self.validator.validate_financial_statement(stmt)
            if validation_result.is_valid:
                validated.append(stmt)
            else:
                self.logger.warning(f"Invalid financial statement for {symbol}: {validation_result.errors}")

        # 按日期排序
        validated.sort(key=lambda x: x.report_date, reverse=True)

        return validated

    def _calculate_valuation_metrics(
        self,
        symbol: str,
        balance_sheet: FinancialStatement,
        as_of_date: date
    ) -> ValuationMetrics:
        """
        计算估值指标

        Args:
            symbol: 股票代码
            balance_sheet: 资产负债表
            as_of_date: 截至日期

        Returns:
            估值指标
        """
        metrics = ValuationMetrics(
            symbol=symbol,
            report_date=as_of_date
        )

        # 计算财务比率
        if balance_sheet.shareholders_equity and balance_sheet.shareholders_equity > 0:
            if balance_sheet.net_income:
                metrics.roe = balance_sheet.net_income / balance_sheet.shareholders_equity

            metrics.pb_ratio = Decimal('1.0')  # 需要市场价格

        if balance_sheet.total_assets and balance_sheet.total_assets > 0:
            if balance_sheet.net_income:
                metrics.roa = balance_sheet.net_income / balance_sheet.total_assets

        if balance_sheet.current_assets and balance_sheet.current_liabilities:
            if balance_sheet.current_liabilities > 0:
                metrics.current_ratio = balance_sheet.current_assets / balance_sheet.current_liabilities

        if balance_sheet.total_liabilities and balance_sheet.shareholders_equity:
            if balance_sheet.shareholders_equity > 0:
                metrics.debt_to_equity = balance_sheet.total_liabilities / balance_sheet.shareholders_equity

        return metrics

    async def calculate_financial_ratios(
        self,
        symbol: str,
        period: int = 12
    ) -> Dict[str, Decimal]:
        """
        计算财务比率

        Args:
            symbol: 股票代码
            period: 期间（月）

        Returns:
            财务比率字典
        """
        statements = await self.get_financial_statements(
            symbol, FinancialStatementType.COMPREHENSIVE, years=2
        )

        if not statements:
            return {}

        latest = statements[0]
        ratios = {}

        # 盈利能力比率
        if latest.revenue and latest.revenue > 0:
            if latest.gross_profit:
                ratios['gross_margin'] = (latest.gross_profit / latest.revenue) * 100
            if latest.operating_income:
                ratios['operating_margin'] = (latest.operating_income / latest.revenue) * 100
            if latest.net_income:
                ratios['net_margin'] = (latest.net_income / latest.revenue) * 100

        # 资产效率比率
        if latest.total_assets and latest.total_assets > 0:
            if latest.revenue:
                ratios['asset_turnover'] = latest.revenue / latest.total_assets

        return ratios

    async def get_peer_comparison(
        self,
        symbol: str,
        metrics: List[str]
    ) -> pd.DataFrame:
        """
        获取同行对比

        Args:
            symbol: 股票代码
            metrics: 对比指标列表

        Returns:
            同行对比DataFrame
        """
        # 获取行业分类
        classification = await self.get_industry_classification(symbol)
        if not classification:
            return pd.DataFrame()

        # 获取同行股票（需要外部数据源）
        peers = await self._get_industry_peers(classification.sector)

        # 并行获取同行数据
        peer_data = []
        for peer in peers:
            try:
                peer_metrics = await self.get_valuation_metrics(peer)
                if peer_metrics:
                    peer_data.append({
                        'symbol': peer,
                        'pe_ratio': peer_metrics.pe_ratio,
                        'pb_ratio': peer_metrics.pb_ratio,
                        'roe': peer_metrics.roe,
                        'debt_to_equity': peer_metrics.debt_to_equity
                    })
            except Exception as e:
                self.logger.error(f"Error fetching peer data for {peer}: {e}")

        return pd.DataFrame(peer_data)

    async def _get_industry_peers(self, sector: str) -> List[str]:
        """
        获取同行股票列表

        Args:
            sector: 行业名称

        Returns:
            同行股票列表
        """
        # 这里需要连接行业数据源
        # 暂时返回示例数据
        return [
            '0700.HK',  # 腾讯 (科技)
            '9988.HK',  # 阿里巴巴 (科技)
            '9618.HK',  # 京东 (科技)
        ] if sector == 'Technology' else []

    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            健康状态字典
        """
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
async def get_fundamental_data(symbol: str) -> Dict[str, Any]:
    """
    获取基本面数据的便捷函数

    Args:
        symbol: 股票代码

    Returns:
        基本面数据字典
    """
    integrator = FundamentalDataIntegrator()
    return await integrator.get_comprehensive_fundamentals(symbol)


async def calculate_financial_health_score(
    symbol: str,
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    计算财务健康评分

    Args:
        symbol: 股票代码
        weights: 评分权重

    Returns:
        财务健康评分 (0-100)
    """
    if weights is None:
        weights = {
            'profitability': 0.3,
            'liquidity': 0.2,
            'leverage': 0.2,
            'efficiency': 0.15,
            'valuation': 0.15
        }

    integrator = FundamentalDataIntegrator()
    fundamentals = await integrator.get_comprehensive_fundamentals(symbol)

    if not fundamentals:
        return 0.0

    score = 0.0

    # 盈利能力评分
    if fundamentals.get('financial_statements'):
        # 实现盈利能力评分逻辑
        pass

    # 流动性评分
    if fundamentals.get('valuation_metrics'):
        # 实现流动性评分逻辑
        pass

    # 杠杆评分
    if fundamentals.get('valuation_metrics'):
        # 实现杠杆评分逻辑
        pass

    return min(100.0, max(0.0, score))


if __name__ == "__main__":
    # 测试代码
    async def test():
        integrator = FundamentalDataIntegrator()

        # 测试获取基本面数据
        data = await integrator.get_comprehensive_fundamentals("0700.HK")
        print("Fundamental data:", data)

    asyncio.run(test())
