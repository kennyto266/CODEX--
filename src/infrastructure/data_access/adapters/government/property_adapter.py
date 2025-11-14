"""
房地产价格指数适配器

从香港差饷物业估价署(RVD)获取房地产价格指数数据。

数据源：https://www.rvd.gov.hk/
"""

import asyncio
import json
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np

from ..base_adapter import BaseDataAdapter, NonPriceDataPoint, DataValidationResult, DataSourceCategory


logger = logging.getLogger(__name__)


class PropertyPriceAdapter(BaseDataAdapter):
    """
    房地产价格指数适配器

    获取香港房地产价格指数数据。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化房地产价格指数适配器

        Args:
            config: 配置参数
                - source_id: 'property_price_index'
                - use_mock_data: 是否使用模拟数据 (默认: True)
                - update_frequency: 更新频率（天，默认: 30）
        """
        default_config = {
            'source_id': 'property_price_index',
            'provider': 'RVD',
            'category': DataSourceCategory.GOVERNMENT,
            'update_frequency': 30,
            'use_mock_data': False,
        }
        default_config.update(config or {})
        super().__init__(default_config)

        self.use_mock_data = self.config.get('use_mock_data', True)

        logger.info("初始化房地产价格指数适配器")

    async def fetch_data(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        **kwargs
    ) -> List[NonPriceDataPoint]:
        """
        获取房地产价格指数数据

        Args:
            start_date: 开始日期
            end_date: 结束日期
            **kwargs: 额外参数

        Returns:
            List[NonPriceDataPoint]: 房地产价格指数数据点列表

        Raises:
            Exception: 数据获取失败
        """
        # 设置默认日期范围
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=365 * 10)  # 默认获取10年数据

        logger.info(f"获取房地产价格指数数据: {start_date} 到 {end_date}")

        try:
            if self.use_mock_data:
                data = await self._fetch_mock_data(start_date, end_date)
            else:
                data = await self._fetch_real_data(start_date, end_date)

            # 转换为NonPriceDataPoint列表
            data_points = []
            for item in data:
                data_points.append(NonPriceDataPoint(
                    timestamp=item['timestamp'],
                    value=item['value'],
                    value_type='index',
                    source_id=self.source_id,
                    metadata={
                        'base_period': item.get('base_period', '1999=100'),
                        'provider': self.provider,
                        'frequency': 'monthly'
                    },
                    quality_score=item.get('quality_score', 0.9)
                ))

            logger.info(f"成功获取 {len(data_points)} 条房地产价格指数数据")
            return data_points

        except Exception as e:
            logger.error(f"获取房地产价格指数数据失败: {str(e)}")
            raise

    async def _fetch_mock_data(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        获取模拟房地产价格指数数据

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            List[Dict]: 模拟数据列表
        """
        # 基准指数（以1999年为基期100）
        base_index = 180  # 当前约180

        # 生成月度日期范围
        dates = pd.date_range(start=start_date, end=end_date, freq='M')

        # 使用固定种子确保可重现性
        np.random.seed(42)

        data = []
        for i, dt in enumerate(dates):
            # 模拟房价指数的长期趋势
            # 年均增长约4-6%，但有周期性
            time_trend = 0.004 * i  # 月度增长0.4%
            cyclical = 0.05 * np.sin(2 * np.pi * i / 48)  # 4年周期
            noise = np.random.normal(0, 0.02)

            index_value = base_index * (1 + time_trend) * (1 + cyclical + noise)

            # 确保指数为正值
            index_value = max(50, index_value)

            data.append({
                'timestamp': datetime.combine(dt.date(), datetime.min.time()),
                'value': round(index_value, 2),
                'base_period': '1999=100',
                'quality_score': 0.95
            })

        logger.debug(f"生成 {len(data)} 条模拟房地产价格指数数据")
        return data

    async def _fetch_real_data(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        获取真实房地产价格指数数据

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            List[Dict]: 真实数据列表
        """
        try:
            # 读取真实数据文件
            data_file = Path(__file__).parent.parent.parent.parent.parent / "data" / "real_gov_data" / "property_data_2025_11.json"

            if not data_file.exists():
                logger.warning(f"数据文件不存在: {data_file}, 使用模拟数据")
                return await self._fetch_mock_data(start_date, end_date)

            with open(data_file, 'r', encoding='utf-8') as f:
                real_data = json.load(f)

            # 过滤日期范围
            filtered_data = []
            for item in real_data:
                item_date = datetime.fromisoformat(item['timestamp']).date()
                if start_date <= item_date <= end_date:
                    filtered_data.append({
                        'timestamp': datetime.fromisoformat(item['timestamp']),
                        'value': item['price_index'],
                        'base_period': item.get('base_period', '1999=100'),
                        'quality_score': item.get('quality_score', 0.95)
                    })

            logger.info(f"成功加载 {len(filtered_data)} 条真实房地产价格数据")
            return filtered_data

        except Exception as e:
            logger.error(f"读取真实房地产价格数据失败: {str(e)}, 使用模拟数据")
            return await self._fetch_mock_data(start_date, end_date)

    def validate_data(self, data: List[NonPriceDataPoint]) -> DataValidationResult:
        """
        验证房地产价格指数数据

        Args:
            data: 待验证的数据点列表

        Returns:
            DataValidationResult: 验证结果
        """
        errors = []
        warnings = []
        statistics = {}

        if not data:
            return DataValidationResult(
                is_valid=False,
                quality_score=0.0,
                quality_level='unknown',
                errors=['数据为空'],
                warnings=warnings,
                statistics=statistics
            )

        # 检查数据完整性
        if len(data) < 12:
            warnings.append(f"数据点数量较少: {len(data)} (至少需要12个月)")

        # 检查时间范围
        timestamps = [d.timestamp for d in data]
        time_span = (max(timestamps) - min(timestamps)).days
        if time_span < 365:
            warnings.append(f"时间范围较短: {time_span}天")

        # 检查数据值范围
        values = [d.value for d in data]
        min_val = min(values)
        max_val = max(values)
        mean_val = sum(values) / len(values)

        statistics['min_value'] = min_val
        statistics['max_value'] = max_val
        statistics['mean_value'] = mean_val
        statistics['count'] = len(data)

        # 房价指数合理性检查
        if min_val < 0:
            errors.append(f"价格指数不能为负数: {min_val}")

        if max_val > 1000:
            warnings.append(f"价格指数较高: {max_val}")

        # 检查异常值（超过3个标准差）
        if len(values) > 3:
            std_val = np.std(values)
            mean_of_values = mean_val
            outliers = sum(1 for v in values if abs(v - mean_of_values) > 3 * std_val)
            if outliers > 0:
                warnings.append(f"发现 {outliers} 个异常值")

        # 计算质量评分
        quality_score, _ = self.calculate_quality_score(data)
        quality_level = self.get_quality_level(quality_score)

        is_valid = len(errors) == 0

        logger.info(
            f"数据验证完成: valid={is_valid}, "
            f"quality={quality_score:.2f}, "
            f"points={len(data)}"
        )

        return DataValidationResult(
            is_valid=is_valid,
            quality_score=quality_score,
            quality_level=quality_level,
            errors=errors,
            warnings=warnings,
            statistics=statistics
        )

    def to_ohlcv(
        self,
        data: List[NonPriceDataPoint]
    ) -> pd.DataFrame:
        """
        将房地产价格指数数据转换为OHLCV格式

        Args:
            data: 房地产价格指数数据点列表

        Returns:
            pd.DataFrame: OHLCV格式数据
        """
        if not data:
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

        # 转换为DataFrame
        df = pd.DataFrame([{
            'timestamp': d.timestamp,
            'close': d.value,
            'quality_score': d.quality_score
        } for d in data])

        # 按时间排序
        df = df.sort_values('timestamp')

        # 生成OHLC（月度数据）
        window = min(3, len(df))
        df['open'] = df['close'].shift(1).fillna(df['close'])
        df['high'] = df['close'].rolling(window=window, min_periods=1).max()
        df['low'] = df['close'].rolling(window=window, min_periods=1).min()

        # 成交量：使用质量评分
        df['volume'] = (df['quality_score'] * 1000000).round().astype(int)

        # 选择列
        result = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].copy()
        result['timestamp'] = pd.to_datetime(result['timestamp'])

        logger.debug(f"转换 {len(data)} 条房地产价格指数数据为OHLCV格式")
        return result

    def get_quality_level(self, score: float) -> str:
        """
        根据评分获取质量等级

        Args:
            score: 质量评分

        Returns:
            str: 质量等级
        """
        if score >= 0.95:
            return 'excellent'
        elif score >= 0.85:
            return 'good'
        elif score >= 0.70:
            return 'fair'
        elif score >= 0.50:
            return 'poor'
        else:
            return 'unknown'
