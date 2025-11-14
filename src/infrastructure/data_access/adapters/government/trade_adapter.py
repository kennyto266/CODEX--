"""
贸易数据适配器

从香港统计处获取对外贸易数据。

数据源：https://www.censtatd.gov.hk/
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


class TradeAdapter(BaseDataAdapter):
    """
    贸易数据适配器

    获取香港对外贸易数据，包括出口和进口。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        default_config = {
            'source_id': 'trade_export',
            'provider': 'C&SD',
            'category': DataSourceCategory.GOVERNMENT,
            'update_frequency': 30,
            'use_mock_data': False,
        }
        default_config.update(config or {})
        super().__init__(default_config)
        self.use_mock_data = self.config.get('use_mock_data', True)

        # 支持两种数据类型：export 或 import
        self.trade_type = self.source_id.split('_')[-1] if '_' in self.source_id else 'export'

        logger.info(f"初始化{self.trade_type}贸易数据适配器")

    async def fetch_data(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        **kwargs
    ) -> List[NonPriceDataPoint]:
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=365 * 5)

        logger.info(f"获取{self.trade_type}贸易数据: {start_date} 到 {end_date}")

        try:
            if self.use_mock_data:
                data = await self._fetch_mock_data(start_date, end_date)
            else:
                data = await self._fetch_real_data(start_date, end_date)

            data_points = []
            for item in data:
                data_points.append(NonPriceDataPoint(
                    timestamp=item['timestamp'],
                    value=item['value'],
                    value_type='trade_value',
                    source_id=self.source_id,
                    metadata={
                        'unit': item.get('unit', 'HKD Million'),
                        'trade_type': self.trade_type,
                        'provider': self.provider,
                        'frequency': 'monthly'
                    },
                    quality_score=item.get('quality_score', 0.9)
                ))

            logger.info(f"成功获取 {len(data_points)} 条{self.trade_type}贸易数据")
            return data_points

        except Exception as e:
            logger.error(f"获取{self.trade_type}贸易数据失败: {str(e)}")
            raise

    async def _fetch_mock_data(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        # 基准贸易值（百万港元）
        base_trade = 400000 if self.trade_type == 'export' else 450000
        dates = pd.date_range(start=start_date, end=end_date, freq='M')
        np.random.seed(42)

        data = []
        for i, dt in enumerate(dates):
            # 模拟长期趋势
            trend = 0.002 * i
            # 模拟季节性
            cyclical = 0.15 * np.sin(2 * np.pi * i / 12)
            noise = np.random.normal(0, 0.05)

            trade_value = base_trade * (1 + trend + cyclical + noise)
            trade_value = max(100000, trade_value)

            data.append({
                'timestamp': datetime.combine(dt.date(), datetime.min.time()),
                'value': round(trade_value, 2),
                'unit': 'HKD Million',
                'quality_score': 0.95
            })

        logger.debug(f"生成 {len(data)} 条模拟{self.trade_type}贸易数据")
        return data

    async def _fetch_real_data(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """获取真实对外贸易数据"""
        try:
            # 读取真实数据文件
            data_file = Path(__file__).parent.parent.parent.parent.parent / "data" / "real_gov_data" / "trade_data_2025_11.json"

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
                        'value': item['total_exports_hkd_billions'],
                        'quality_score': item.get('quality_score', 0.97)
                    })

            logger.info(f"成功加载 {len(filtered_data)} 条真实对外贸易数据")
            return filtered_data

        except Exception as e:
            logger.error(f"读取真实对外贸易数据失败: {str(e)}, 使用模拟数据")
            return await self._fetch_mock_data(start_date, end_date)

    def validate_data(self, data: List[NonPriceDataPoint]) -> DataValidationResult:
        errors = []
        warnings = []
        statistics = {}

        if not data:
            return DataValidationResult(
                is_valid=False, quality_score=0.0, quality_level='unknown',
                errors=['数据为空'], warnings=warnings, statistics=statistics
            )

        if len(data) < 12:
            warnings.append(f"数据点数量较少: {len(data)}")

        values = [d.value for d in data]
        min_val = min(values)
        max_val = max(values)
        mean_val = sum(values) / len(values)

        statistics['min_value'] = min_val
        statistics['max_value'] = max_val
        statistics['mean_value'] = mean_val
        statistics['count'] = len(data)

        if min_val < 0:
            errors.append(f"贸易额不能为负数: {min_val}")

        quality_score, _ = self.calculate_quality_score(data)
        quality_level = self.get_quality_level(quality_score)
        is_valid = len(errors) == 0

        logger.info(f"数据验证完成: valid={is_valid}, quality={quality_score:.2f}")

        return DataValidationResult(
            is_valid=is_valid,
            quality_score=quality_score,
            quality_level=quality_level,
            errors=errors,
            warnings=warnings,
            statistics=statistics
        )

    def to_ohlcv(self, data: List[NonPriceDataPoint]) -> pd.DataFrame:
        if not data:
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

        df = pd.DataFrame([{
            'timestamp': d.timestamp,
            'close': d.value,
            'quality_score': d.quality_score
        } for d in data])

        df = df.sort_values('timestamp')
        window = min(3, len(df))
        df['open'] = df['close'].shift(1).fillna(df['close'])
        df['high'] = df['close'].rolling(window=window, min_periods=1).max()
        df['low'] = df['close'].rolling(window=window, min_periods=1).min()
        df['volume'] = (df['quality_score'] * 1000000).round().astype(int)

        result = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].copy()
        result['timestamp'] = pd.to_datetime(result['timestamp'])

        logger.debug(f"转换 {len(data)} 条{self.trade_type}贸易数据为OHLCV格式")
        return result

    def get_quality_level(self, score: float) -> str:
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
