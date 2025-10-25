"""
Kaggle数据集收集器

从Kaggle和本地文件系统加载结构化数据集。
支持CSV、XLSX、Parquet等多种格式。

使用示例:
    collector = KaggleDataCollector(mode="mock")
    await collector.connect()
    data = await collector.fetch_data("stock_prices", date(2024,1,1), date(2024,12,31))
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import pandas as pd
import random

from .alternative_data_adapter import (
    AlternativeDataAdapter,
    IndicatorMetadata,
    DataFrequency,
)

logger = logging.getLogger("hk_quant_system.kaggle_collector")


class KaggleDataCollector(AlternativeDataAdapter):
    """Kaggle数据集收集器

    从Kaggle和本地数据目录加载结构化数据集。
    支持CSV、XLSX、Parquet等多种格式。

    使用示例:
        collector = KaggleDataCollector(mode="mock", data_directory="./datasets")
        await collector.connect()
        data = await collector.fetch_data("hong_kong_gdp", date(2020,1,1), date(2024,12,31))
    """

    # 支持的数据集列表
    SUPPORTED_INDICATORS = {
        # 宏观经济数据
        "hong_kong_gdp": "香港国内生产总值",
        "hong_kong_unemployment": "香港失业率数据",
        "hk_property_prices": "香港房产价格指数",
        "hk_consumer_sentiment": "香港消费者信心指数",

        # 股市相关数据
        "hsi_historical": "恒生指数历史数据",
        "hang_seng_components": "恒生指数成分股数据",
        "hk_market_capitalization": "香港上市公司总市值",

        # 国际市场数据
        "us_stock_prices": "美国股票价格数据",
        "global_commodity_prices": "全球大宗商品价格",
        "exchange_rates": "主要货币汇率数据",
    }

    def __init__(
        self,
        mode: str = "mock",
        data_directory: str = "./datasets",
        cache_ttl: int = 86400,  # 1天
        max_retries: int = 3,
        timeout: int = 30,
    ):
        """初始化Kaggle数据收集器

        Args:
            mode: 操作模式 ("mock" 或 "live")
            data_directory: 本地数据集目录
            cache_ttl: 缓存生存时间（秒）
            max_retries: 最大重试次数
            timeout: 连接超时（秒）
        """
        super().__init__(
            adapter_name="KaggleDataCollector",
            data_source_url="https://www.kaggle.com/",
            cache_ttl=cache_ttl,
            max_retries=max_retries,
            timeout=timeout,
        )

        self.mode = mode
        self.data_directory = Path(data_directory)
        logger.info(f"✓ KaggleDataCollector 初始化 (模式: {mode})")

    async def _do_connect(self) -> bool:
        """连接到数据源"""
        if self.mode == "mock":
            logger.info("✓ 已连接到Kaggle数据源 (模拟模式)")
            return True

        if self.mode == "live":
            try:
                # 检查本地数据目录是否存在
                if not self.data_directory.exists():
                    logger.warning(
                        f"⚠️ 数据目录不存在: {self.data_directory}. "
                        f"将使用模拟数据。"
                    )
                    return True

                logger.info("✓ 已连接到Kaggle数据源 (实时模式)")
                return True
            except Exception as e:
                logger.error(f"✗ 连接失败: {e}")
                return False

        return False

    async def _do_disconnect(self) -> bool:
        """断开连接"""
        return True

    async def _fetch_with_retry(
        self,
        indicator_code: str,
        start_date: date,
        end_date: date,
        **kwargs,
    ) -> pd.DataFrame:
        """获取数据（带重试）"""
        if indicator_code not in self.SUPPORTED_INDICATORS:
            raise ValueError(f"不支持的指标: {indicator_code}")

        return await self._retry_operation(
            self._fetch_indicator_data,
            indicator_code,
            start_date,
            end_date,
            **kwargs,
        )

    async def _fetch_indicator_data(
        self,
        indicator_code: str,
        start_date: date,
        end_date: date,
        **kwargs,
    ) -> pd.DataFrame:
        """实现指标数据获取"""
        if self.mode == "mock":
            return self._generate_mock_data(indicator_code, start_date, end_date)

        if self.mode == "live":
            return await self._load_live_data(indicator_code, start_date, end_date)

        raise ValueError(f"不支持的模式: {self.mode}")

    def _generate_mock_data(
        self,
        indicator_code: str,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        """生成模拟数据"""

        # 根据指标类型生成日期范围
        trading_days = pd.bdate_range(start=start_date, end=end_date)

        data = []

        # 根据指标类型生成基础值
        base_values = {
            "hong_kong_gdp": 380000000000,  # 3800亿港元
            "hong_kong_unemployment": 3.2,  # 3.2%
            "hk_property_prices": 350000,  # 350万/平方尺
            "hk_consumer_sentiment": 55.0,  # 0-100指数
            "hsi_historical": 18000,  # 18000点
            "hang_seng_components": 5000,  # 股票价格平均5000港元
            "hk_market_capitalization": 45000000000000,  # 45万亿港元
            "us_stock_prices": 400,  # $400
            "global_commodity_prices": 100,  # 索引100
            "exchange_rates": 7.8,  # 美元兑港元
        }

        base_value = base_values.get(indicator_code, 100)

        for trading_day in trading_days:
            # 添加随机波动
            if "gdp" in indicator_code or "capitalization" in indicator_code:
                # GDP和市值：年度数据，波动较小
                noise = random.uniform(0.98, 1.02)
            elif "unemployment" in indicator_code or "sentiment" in indicator_code:
                # 百分比数据：小波动
                noise = random.uniform(0.99, 1.01)
            elif "price" in indicator_code or "stock" in indicator_code:
                # 价格数据：中等波动
                noise = random.uniform(0.95, 1.05)
            else:
                # 其他数据：中等波动
                noise = random.uniform(0.95, 1.05)

            value = base_value * noise

            data.append(
                {
                    "timestamp": trading_day,
                    "value": value,
                    "indicator": indicator_code,
                }
            )

        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        logger.info(
            f"✓ 生成{len(df)}条模拟数据 ({indicator_code}, {start_date} ~ {end_date})"
        )

        return df

    async def _load_live_data(
        self,
        indicator_code: str,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        """从本地文件加载实时数据"""

        try:
            # 构建文件路径
            file_path = self.data_directory / f"{indicator_code}.csv"

            if not file_path.exists():
                # 尝试XLSX格式
                file_path = self.data_directory / f"{indicator_code}.xlsx"

            if not file_path.exists():
                # 尝试Parquet格式
                file_path = self.data_directory / f"{indicator_code}.parquet"

            if not file_path.exists():
                logger.warning(
                    f"⚠️ 数据文件不存在: {indicator_code}. "
                    f"返回模拟数据。"
                )
                return self._generate_mock_data(indicator_code, start_date, end_date)

            # 根据文件格式加载
            if file_path.suffix.lower() == ".csv":
                df = pd.read_csv(file_path)
            elif file_path.suffix.lower() == ".xlsx":
                df = pd.read_excel(file_path)
            elif file_path.suffix.lower() == ".parquet":
                df = pd.read_parquet(file_path)
            else:
                logger.error(f"✗ 不支持的文件格式: {file_path.suffix}")
                return self._generate_mock_data(indicator_code, start_date, end_date)

            # 确保有timestamp和value列
            if "timestamp" not in df.columns:
                if "date" in df.columns:
                    df.rename(columns={"date": "timestamp"}, inplace=True)
                elif "time" in df.columns:
                    df.rename(columns={"time": "timestamp"}, inplace=True)
                else:
                    # 使用第一列作为时间戳
                    df.rename(columns={df.columns[0]: "timestamp"}, inplace=True)

            if "value" not in df.columns:
                if "close" in df.columns:
                    df.rename(columns={"close": "value"}, inplace=True)
                elif "price" in df.columns:
                    df.rename(columns={"price": "value"}, inplace=True)
                else:
                    # 使用第二列作为值
                    df.rename(columns={df.columns[1]: "value"}, inplace=True)

            # 转换时间戳
            df["timestamp"] = pd.to_datetime(df["timestamp"])

            # 过滤日期范围
            df = df[
                (df["timestamp"].dt.date >= start_date)
                & (df["timestamp"].dt.date <= end_date)
            ]

            logger.info(
                f"✓ 从文件加载{len(df)}条数据 ({indicator_code}, {file_path})"
            )

            return df

        except Exception as e:
            logger.error(f"✗ 加载数据失败: {e}")
            # 失败时返回模拟数据
            return self._generate_mock_data(indicator_code, start_date, end_date)

    async def _get_realtime_impl(
        self, indicator_code: str, **kwargs
    ) -> Dict[str, Any]:
        """获取实时数据"""
        if self.mode == "mock":
            base_values = {
                "hong_kong_gdp": 380000000000,
                "hong_kong_unemployment": 3.2,
                "hsi_historical": 18000,
                "us_stock_prices": 400,
            }
            base_value = base_values.get(indicator_code, 100)

            return {
                "indicator_code": indicator_code,
                "timestamp": datetime.now(),
                "value": base_value * random.uniform(0.99, 1.01),
                "unit": self._get_unit(indicator_code),
                "source": "Kaggle Mock",
            }

        if self.mode == "live":
            # 尝试从最新数据中获取最后一个值
            try:
                df = await self._load_live_data(
                    indicator_code,
                    date.today() - timedelta(days=30),
                    date.today(),
                )
                if len(df) > 0:
                    last_row = df.iloc[-1]
                    return {
                        "indicator_code": indicator_code,
                        "timestamp": last_row["timestamp"],
                        "value": last_row["value"],
                        "unit": self._get_unit(indicator_code),
                        "source": "Kaggle",
                    }
            except Exception as e:
                logger.error(f"✗ 获取实时数据失败: {e}")

            # 失败时返回模拟数据
            return await self._get_realtime_impl(indicator_code)

        raise ValueError(f"不支持的模式: {self.mode}")

    async def _get_metadata_impl(
        self, indicator_code: str
    ) -> IndicatorMetadata:
        """获取指标元数据"""
        if indicator_code not in self.SUPPORTED_INDICATORS:
            raise ValueError(f"不支持的指标: {indicator_code}")

        return IndicatorMetadata(
            indicator_code=indicator_code,
            indicator_name=self.SUPPORTED_INDICATORS[indicator_code],
            description=f"从Kaggle获取的{self.SUPPORTED_INDICATORS[indicator_code]}",
            data_source="Kaggle",
            frequency=DataFrequency.DAILY,
            unit=self._get_unit(indicator_code),
            country_code="HK",
            category="kaggle_datasets",
            last_updated=datetime.now(),
            next_update=datetime.now() + timedelta(days=1),
            data_availability="本地数据集或从Kaggle下载",
            quality_notes="数据来自公开Kaggle数据集",
        )

    async def _list_indicators_impl(self) -> List[str]:
        """列出所有支持的指标"""
        return list(self.SUPPORTED_INDICATORS.keys())

    async def _check_connectivity(self) -> bool:
        """检查连接状态"""
        if self.mode == "mock":
            return True

        try:
            # 检查数据目录是否可访问
            return self.data_directory.exists()
        except Exception as e:
            logger.error(f"✗ 连接检查失败: {e}")
            return False

    def _get_unit(self, indicator_code: str) -> str:
        """获取指标单位"""
        units = {
            "hong_kong_gdp": "HKD",
            "hong_kong_unemployment": "%",
            "hk_property_prices": "HKD/平方尺",
            "hk_consumer_sentiment": "指数",
            "hsi_historical": "点",
            "hang_seng_components": "HKD",
            "hk_market_capitalization": "HKD",
            "us_stock_prices": "USD",
            "global_commodity_prices": "指数",
            "exchange_rates": "HKD/USD",
        }
        return units.get(indicator_code, "单位")

    def set_data_directory(self, directory: str) -> None:
        """设置本地数据目录

        Args:
            directory: 数据目录路径
        """
        self.data_directory = Path(directory)
        logger.info(f"✓ 数据目录已更新: {self.data_directory}")


# 使用示例
async def main():
    """演示KaggleDataCollector的使用"""

    collector = KaggleDataCollector(mode="mock")

    # 连接
    connected = await collector.connect()
    print(f"Connected: {connected}\n")

    # 列出指标
    indicators = await collector.list_indicators()
    print(f"Available indicators ({len(indicators)}):")
    for ind in indicators[:5]:  # 显示前5个
        print(f"  - {ind}: {collector.SUPPORTED_INDICATORS[ind]}")
    print(f"  ... and {len(indicators)-5} more\n")

    # 获取GDP数据
    print("[GDP Data]")
    gdp_data = await collector.fetch_data(
        "hong_kong_gdp", date(2024, 1, 1), date(2024, 12, 31)
    )
    print(f"Shape: {gdp_data.shape}")
    print(f"Average: {gdp_data['value'].mean():,.0f}\n")

    # 获取股票数据
    print("[HSI Historical Data]")
    hsi_data = await collector.fetch_data(
        "hsi_historical", date(2024, 1, 1), date(2024, 12, 31)
    )
    print(f"Shape: {hsi_data.shape}")
    print(f"Average: {hsi_data['value'].mean():.0f}\n")

    # 健康检查
    health = await collector.health_check()
    print(f"Health: {health['status']}")

    await collector.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
