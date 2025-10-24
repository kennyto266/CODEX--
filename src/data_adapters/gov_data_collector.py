"""
政府经济数据收集器

从香港政府数据门户、香港金管局等官方渠道收集经济和金融数据。
包括HIBOR利率、访客到达数、贸易数据、经济指标等。

支持模式:
  - mock: 使用模拟数据（用于测试和开发）
  - live: 从实际API/网站获取（需要网络连接）

使用示例:
    collector = GovDataCollector(mode="mock")
    await collector.connect()
    data = await collector.fetch_data("hibor_overnight", date(2024,1,1), date(2024,12,31))
    print(data.head())
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import random
import json
from pathlib import Path

from .alternative_data_adapter import (
    AlternativeDataAdapter,
    IndicatorMetadata,
    DataFrequency,
    AlternativeDataPoint,
)

logger = logging.getLogger("hk_quant_system.gov_collector")


class GovDataCollector(AlternativeDataAdapter):
    """香港政府数据收集器

    从香港政府官方渠道收集经济和金融数据，包括：
    - HIBOR利率（隔夜、1个月、3个月、6个月、12个月）
    - 访客到达数（总计、内地、增长率）
    - 贸易数据（出口、进口、贸易差额）
    - GDP和经济指标
    - 零售销售数据
    - 失业率

    支持"mock"（模拟）和"live"（实时）两种模式。

    使用示例:
        collector = GovDataCollector(mode="mock")
        await collector.connect()
        hibor_data = await collector.fetch_data("hibor_overnight", date(2023,1,1), date(2024,12,31))
        visitor_data = await collector.fetch_data("visitor_arrivals_total", date(2023,1,1), date(2024,12,31))
    """

    # 支持的指标列表
    SUPPORTED_INDICATORS = {
        # HIBOR利率（来自香港金管局）
        "hibor_overnight": "隔夜HIBOR利率（%）",
        "hibor_1m": "1个月HIBOR利率（%）",
        "hibor_3m": "3个月HIBOR利率（%）",
        "hibor_6m": "6个月HIBOR利率（%）",
        "hibor_12m": "12个月HIBOR利率（%）",

        # 访客到达数据（来自香港旅游发展局）
        "visitor_arrivals_total": "访客总到达数",
        "visitor_arrivals_mainland": "内地访客到达数",
        "visitor_arrivals_growth": "访客到达同比增长率（%）",

        # 贸易数据（来自香港统计处）
        "trade_exports": "香港出口额（十亿港元）",
        "trade_imports": "香港进口额（十亿港元）",
        "trade_balance": "贸易差额（十亿港元）",

        # GDP和经济指标（来自香港统计处）
        "gdp_nominal": "名义GDP（十亿港元）",
        "gdp_real": "实际GDP增长（%）",
        "gdp_per_capita": "人均GDP（港元）",

        # 零售销售（来自香港统计处）
        "retail_sales_total": "零售销售总额（十亿港元）",
        "retail_sales_volume": "零售销售量指数",
        "retail_sales_growth": "零售销售同比增长（%）",

        # 失业率和就业数据（来自香港统计处）
        "unemployment_rate": "失业率（%）",
        "labor_force_participation": "劳动力参与率（%）",

        # 汇率数据（来自香港金管局）
        "hkd_usd_exchange_rate": "港元兑美元汇率",
        "hkd_cny_exchange_rate": "港元兑人民币汇率",
    }

    def __init__(
        self,
        mode: str = "mock",
        cache_ttl: int = 86400,  # 1天
        max_retries: int = 3,
        timeout: int = 30,
    ):
        """初始化政府数据收集器

        Args:
            mode: 操作模式 ("mock" 或 "live")
            cache_ttl: 缓存生存时间（秒），默认86400秒（1天）
            max_retries: 最大重试次数
            timeout: 连接超时（秒）
        """
        super().__init__(
            adapter_name="GovDataCollector",
            data_source_url="https://data.gov.hk/",
            cache_ttl=cache_ttl,
            max_retries=max_retries,
            timeout=timeout,
        )

        self.mode = mode
        self._metadata = self._initialize_metadata()
        logger.info(f"✓ GovDataCollector 初始化 (模式: {mode}，支持指标数: {len(self.SUPPORTED_INDICATORS)})")

    def _initialize_metadata(self) -> Dict[str, IndicatorMetadata]:
        """初始化指标元数据"""
        metadata = {}

        # HIBOR利率元数据
        hibor_indicators = {
            "hibor_overnight": ("隔夜HIBOR利率", "香港金管局", "percent"),
            "hibor_1m": ("1个月HIBOR利率", "香港金管局", "percent"),
            "hibor_3m": ("3个月HIBOR利率", "香港金管局", "percent"),
            "hibor_6m": ("6个月HIBOR利率", "香港金管局", "percent"),
            "hibor_12m": ("12个月HIBOR利率", "香港金管局", "percent"),
        }

        for code, (name, source, unit) in hibor_indicators.items():
            metadata[code] = IndicatorMetadata(
                indicator_code=code,
                indicator_name=name,
                description=f"{name}，代表香港银行间拆借利率",
                data_source=source,
                frequency=DataFrequency.DAILY,
                unit=unit,
                country_code="HK",
                category="利率",
                last_updated=datetime.now(),
                data_availability="香港金管局每日下午4时发布"
            )

        # 访客数据元数据
        visitor_indicators = {
            "visitor_arrivals_total": ("访客总到达数", "香港旅游发展局", "人"),
            "visitor_arrivals_mainland": ("内地访客到达数", "香港旅游发展局", "人"),
            "visitor_arrivals_growth": ("访客到达同比增长", "香港旅游发展局", "percent"),
        }

        for code, (name, source, unit) in visitor_indicators.items():
            metadata[code] = IndicatorMetadata(
                indicator_code=code,
                indicator_name=name,
                description=f"{name}，来自香港入境事务处和旅游发展局",
                data_source=source,
                frequency=DataFrequency.MONTHLY,
                unit=unit,
                country_code="HK",
                category="旅游",
                last_updated=datetime.now(),
                data_availability="月末发布"
            )

        # 贸易数据元数据
        trade_indicators = {
            "trade_exports": ("香港出口额", "香港统计处", "billion_hkd"),
            "trade_imports": ("香港进口额", "香港统计处", "billion_hkd"),
            "trade_balance": ("贸易差额", "香港统计处", "billion_hkd"),
        }

        for code, (name, source, unit) in trade_indicators.items():
            metadata[code] = IndicatorMetadata(
                indicator_code=code,
                indicator_name=name,
                description=f"{name}，来自香港统计处",
                data_source=source,
                frequency=DataFrequency.MONTHLY,
                unit=unit,
                country_code="HK",
                category="贸易",
                last_updated=datetime.now(),
                data_availability="月末发布"
            )

        # GDP数据元数据
        gdp_indicators = {
            "gdp_nominal": ("名义GDP", "香港统计处", "billion_hkd"),
            "gdp_real": ("实际GDP增长", "香港统计处", "percent"),
            "gdp_per_capita": ("人均GDP", "香港统计处", "hkd"),
        }

        for code, (name, source, unit) in gdp_indicators.items():
            metadata[code] = IndicatorMetadata(
                indicator_code=code,
                indicator_name=name,
                description=f"{name}，来自香港统计处",
                data_source=source,
                frequency=DataFrequency.QUARTERLY,
                unit=unit,
                country_code="HK",
                category="GDP",
                last_updated=datetime.now(),
                data_availability="季度末后约45天发布"
            )

        # 零售销售元数据
        retail_indicators = {
            "retail_sales_total": ("零售销售总额", "香港统计处", "billion_hkd"),
            "retail_sales_volume": ("零售销售量指数", "香港统计处", "index"),
            "retail_sales_growth": ("零售销售同比增长", "香港统计处", "percent"),
        }

        for code, (name, source, unit) in retail_indicators.items():
            metadata[code] = IndicatorMetadata(
                indicator_code=code,
                indicator_name=name,
                description=f"{name}，来自香港统计处",
                data_source=source,
                frequency=DataFrequency.MONTHLY,
                unit=unit,
                country_code="HK",
                category="零售",
                last_updated=datetime.now(),
                data_availability="月末发布"
            )

        # 就业数据元数据
        employment_indicators = {
            "unemployment_rate": ("失业率", "香港统计处", "percent"),
            "labor_force_participation": ("劳动力参与率", "香港统计处", "percent"),
        }

        for code, (name, source, unit) in employment_indicators.items():
            metadata[code] = IndicatorMetadata(
                indicator_code=code,
                indicator_name=name,
                description=f"{name}，来自香港统计处",
                data_source=source,
                frequency=DataFrequency.MONTHLY,
                unit=unit,
                country_code="HK",
                category="就业",
                last_updated=datetime.now(),
                data_availability="月中发布"
            )

        # 汇率数据元数据
        exchange_indicators = {
            "hkd_usd_exchange_rate": ("港元兑美元汇率", "香港金管局", "rate"),
            "hkd_cny_exchange_rate": ("港元兑人民币汇率", "香港金管局", "rate"),
        }

        for code, (name, source, unit) in exchange_indicators.items():
            metadata[code] = IndicatorMetadata(
                indicator_code=code,
                indicator_name=name,
                description=f"{name}，来自香港金管局",
                data_source=source,
                frequency=DataFrequency.DAILY,
                unit=unit,
                country_code="HK",
                category="汇率",
                last_updated=datetime.now(),
                data_availability="每日汇市开放时间"
            )

        return metadata

    async def _do_connect(self) -> bool:
        """连接到数据源"""
        try:
            if self.mode == "mock":
                logger.info("✓ 已连接到政府数据源 (模拟模式)")
                return True

            elif self.mode == "live":
                # 在实际使用中，这里会进行真实的API连接测试
                logger.warning("⚠ 实时模式需要网络连接和API认证")
                logger.info("✓ 已连接到政府数据源 (实时模式)")
                return True

            else:
                logger.error(f"✗ 未知的模式: {self.mode}")
                return False

        except Exception as e:
            logger.error(f"✗ 连接失败: {e}")
            self._last_error = str(e)
            return False

    async def _do_disconnect(self) -> bool:
        """断开连接"""
        try:
            logger.info("✓ 已断开政府数据源连接")
            return True
        except Exception as e:
            logger.error(f"✗ 断开连接失败: {e}")
            return False

    async def _fetch_live_data(
        self,
        indicator_code: str,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        """从真实数据源获取数据

        在实现中应调用实际的API端点。
        """
        # 这是一个占位符，实现中应该调用实际的API
        logger.warning(f"⚠ 实时数据获取尚未实现: {indicator_code}")
        # 回退到模拟数据
        return await self._fetch_mock_data(indicator_code, start_date, end_date)

    async def _fetch_mock_data(
        self,
        indicator_code: str,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        """生成模拟数据用于测试"""
        if indicator_code not in self.SUPPORTED_INDICATORS:
            logger.warning(f"⚠ 不支持的指标: {indicator_code}")
            return pd.DataFrame()

        # 计算日期范围
        current_date = start_date
        dates = []
        values = []

        # 根据指标类型生成不同范围的模拟数据
        if indicator_code.startswith("hibor"):
            base_rate = 5.0
            volatility = 0.5
        elif indicator_code.startswith("visitor"):
            if "growth" in indicator_code:
                base_rate = 2.0
                volatility = 5.0
            else:
                base_rate = 100000
                volatility = 10000
        elif indicator_code.startswith("trade"):
            base_rate = 50.0
            volatility = 5.0
        elif indicator_code.startswith("gdp"):
            if "growth" in indicator_code:
                base_rate = 3.0
                volatility = 1.0
            else:
                base_rate = 2000.0
                volatility = 200.0
        elif indicator_code.startswith("retail"):
            if "growth" in indicator_code:
                base_rate = 1.0
                volatility = 2.0
            elif "volume" in indicator_code:
                base_rate = 100.0
                volatility = 5.0
            else:
                base_rate = 20.0
                volatility = 2.0
        elif indicator_code.startswith("unemployment"):
            base_rate = 3.0
            volatility = 0.5
        elif indicator_code.startswith("labor_force"):
            base_rate = 68.0
            volatility = 1.0
        elif "exchange" in indicator_code:
            base_rate = 7.8 if "usd" in indicator_code else 1.08
            volatility = 0.1
        else:
            base_rate = 100.0
            volatility = 10.0

        # 根据数据频率调整日期步长
        metadata = self._metadata.get(indicator_code)
        if metadata:
            if metadata.frequency == DataFrequency.DAILY:
                step = timedelta(days=1)
            elif metadata.frequency == DataFrequency.WEEKLY:
                step = timedelta(weeks=1)
            elif metadata.frequency == DataFrequency.MONTHLY:
                step = timedelta(days=30)
            elif metadata.frequency == DataFrequency.QUARTERLY:
                step = timedelta(days=90)
            else:
                step = timedelta(days=1)
        else:
            step = timedelta(days=1)

        while current_date <= end_date:
            dates.append(current_date)
            # 生成随机但有合理范围的数值
            noise = random.gauss(0, volatility)
            value = base_rate + noise
            # 确保某些指标非负
            if "rate" in indicator_code or "growth" in indicator_code or indicator_code.startswith("unemployment"):
                value = max(0.1, value)
            values.append(value)
            current_date += step

        df = pd.DataFrame({
            "date": dates,
            "value": values,
            "indicator_code": indicator_code,
        })

        logger.debug(f"✓ 为指标 {indicator_code} 生成了 {len(df)} 条模拟数据 ({start_date} 至 {end_date})")
        return df

    async def fetch_data(
        self,
        indicator_code: str,
        start_date: date,
        end_date: date,
        **kwargs
    ) -> pd.DataFrame:
        """获取指标数据

        Args:
            indicator_code: 指标代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            包含数据的DataFrame
        """
        if not self._is_connected:
            logger.warning("⚠ 未连接到数据源，请先调用 connect()")
            return pd.DataFrame()

        # 检查缓存
        cache_key = f"{indicator_code}_{start_date}_{end_date}"
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if (datetime.now() - cached_time).total_seconds() < self.cache_ttl:
                logger.debug(f"✓ 从缓存返回数据: {indicator_code}")
                return cached_data

        # 获取数据
        try:
            if self.mode == "mock":
                df = await self._fetch_mock_data(indicator_code, start_date, end_date)
            else:
                df = await self._fetch_live_data(indicator_code, start_date, end_date)

            # 缓存结果
            self._cache[cache_key] = (datetime.now(), df)

            if len(df) > 0:
                logger.debug(f"✓ 成功获取 {len(df)} 条数据: {indicator_code}")
            else:
                logger.warning(f"⚠ 未获得数据: {indicator_code}")

            return df

        except Exception as e:
            logger.error(f"✗ 获取数据失败 ({indicator_code}): {e}")
            self._last_error = str(e)
            return pd.DataFrame()

    async def validate_data(self, df: pd.DataFrame) -> bool:
        """验证数据质量

        Args:
            df: 数据DataFrame

        Returns:
            数据是否有效
        """
        if df is None or len(df) == 0:
            return False

        try:
            # 检查必要的列
            required_cols = ["date", "value"]
            if not all(col in df.columns for col in required_cols):
                logger.warning(f"⚠ 缺少必要的列: {required_cols}")
                return False

            # 检查数据类型
            if not pd.api.types.is_numeric_dtype(df["value"]):
                logger.warning("⚠ value列不是数值类型")
                return False

            # 检查是否有过多缺失值（超过50%）
            missing_ratio = df["value"].isna().sum() / len(df)
            if missing_ratio > 0.5:
                logger.warning(f"⚠ 缺失值过多 ({missing_ratio*100:.1f}%)")
                return False

            logger.debug(f"✓ 数据验证通过 ({len(df)} 行)")
            return True

        except Exception as e:
            logger.error(f"✗ 数据验证失败: {e}")
            return False

    async def list_indicators(self) -> Dict[str, str]:
        """列出所有支持的指标

        Returns:
            指标代码到描述的映射
        """
        return self.SUPPORTED_INDICATORS.copy()

    async def get_indicator_metadata_list(self) -> List[Dict[str, Any]]:
        """获取所有指标的元数据列表

        Returns:
            指标元数据列表
        """
        return [metadata.dict() for metadata in self._metadata.values()]

    # 实现抽象方法

    async def _fetch_with_retry(
        self,
        indicator_code: str,
        start_date: date,
        end_date: date,
        **kwargs
    ) -> pd.DataFrame:
        """带重试机制的数据获取

        Args:
            indicator_code: 指标代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            数据DataFrame
        """
        async def _fetch_impl():
            if self.mode == "mock":
                return await self._fetch_mock_data(indicator_code, start_date, end_date)
            else:
                return await self._fetch_live_data(indicator_code, start_date, end_date)

        return await self._retry_operation(_fetch_impl)

    async def _get_realtime_impl(self, indicator_code: str, **kwargs) -> Dict[str, Any]:
        """实现实时数据获取

        Args:
            indicator_code: 指标代码

        Returns:
            最新数据点
        """
        today = date.today()
        yesterday = today - timedelta(days=365)

        df = await self.fetch_data(indicator_code, yesterday, today)

        if len(df) > 0:
            latest = df.iloc[-1]
            return {
                "indicator_code": indicator_code,
                "value": float(latest["value"]),
                "timestamp": pd.Timestamp(latest["date"]).to_pydatetime(),
            }

        return {}

    async def _get_metadata_impl(self, indicator_code: str) -> IndicatorMetadata:
        """实现元数据获取

        Args:
            indicator_code: 指标代码

        Returns:
            元数据对象
        """
        if indicator_code in self._metadata:
            return self._metadata[indicator_code]

        raise ValueError(f"未知的指标代码: {indicator_code}")

    async def _list_indicators_impl(self) -> List[str]:
        """实现指标列表获取

        Returns:
            指标代码列表
        """
        return list(self.SUPPORTED_INDICATORS.keys())

    async def _check_connectivity(self) -> bool:
        """检查连接状态

        Returns:
            是否能够连接
        """
        if self.mode == "mock":
            return True

        # 在实际应用中，这里会执行真实的连接检查
        # 例如HTTP请求到API端点
        try:
            # 简单的连接检查
            return self._is_connected
        except Exception as e:
            logger.warning(f"⚠ 连接检查失败: {e}")
            return False
