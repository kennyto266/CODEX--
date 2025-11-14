"""
HKMA HIBOR利率数据适配器

从香港金融管理局(HKMA)获取HIBOR（香港银行同业拆息）利率数据。
支持3个主要指标：隔夜、1个月、3个月。

数据源：https://www.hkma.gov.hk/
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np

from ..base_adapter import BaseDataAdapter, NonPriceDataPoint, DataValidationResult, DataSourceCategory


logger = logging.getLogger(__name__)


class HKMARateAdapter(BaseDataAdapter):
    """
    HKMA HIBOR利率适配器

    获取香港银行同业拆息(HIBOR)数据，包括：
    - HIBOR隔夜 (HIBOR Overnight)
    - HIBOR 1个月 (HIBOR 1M)
    - HIBOR 3个月 (HIBOR 3M)
    """

    # HIBOR期限类型
    HIBOR_TERMS = {
        'hibor_overnight': 'hibor_overnight',
        'hibor_1m': 'hibor_1m',
        'hibor_3m': 'hibor_3m',
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化HKMA适配器

        Args:
            config: 配置参数
                - source_id: 'hibor_overnight' | 'hibor_1m' | 'hibor_3m'
                - use_mock_data: 是否使用模拟数据 (默认: True)
                - update_frequency: 更新频率（天，默认: 1）
                - csv_path: 真实数据CSV文件路径 (可选，默认自动检测)
        """
        default_config = {
            'source_id': 'hibor_overnight',
            'provider': 'HKMA',
            'category': DataSourceCategory.CENTRAL_BANK,
            'update_frequency': 1,
            'use_mock_data': False,
        }
        default_config.update(config or {})
        super().__init__(default_config)

        self.term = self.source_id
        self.use_mock_data = self.config.get('use_mock_data', True)

        # 设置CSV文件路径
        if 'csv_path' in self.config:
            self.csv_path = self.config['csv_path']
        else:
            # 自动检测CSV文件路径
            project_root = Path(__file__).parent.parent.parent.parent.parent.parent
            self.csv_path = project_root / 'data' / 'real_gov_data' / 'hibor' / 'hibor_overnight.csv'

        self._cached_data: Dict[str, Any] = {}
        self._last_update: Optional[datetime] = None

        logger.info(f"初始化HKMA适配器 - 期限: {self.term}, 模拟数据: {self.use_mock_data}")

    async def fetch_data(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        **kwargs
    ) -> List[NonPriceDataPoint]:
        """
        获取HIBOR利率数据

        Args:
            start_date: 开始日期
            end_date: 结束日期
            **kwargs: 额外参数

        Returns:
            List[NonPriceDataPoint]: HIBOR利率数据点列表

        Raises:
            Exception: 数据获取失败
        """
        # 设置默认日期范围
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=365)  # 默认获取1年数据

        logger.info(f"获取HIBOR数据: {self.term}, {start_date} 到 {end_date}")

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
                    value_type='rate',
                    source_id=self.source_id,
                    metadata={
                        'term': self.term,
                        'provider': self.provider,
                        'currency': 'HKD'
                    },
                    quality_score=item.get('quality_score', 0.9)
                ))

            logger.info(f"成功获取 {len(data_points)} 条HIBOR数据")
            return data_points

        except Exception as e:
            logger.error(f"获取HIBOR数据失败: {str(e)}")
            raise

    async def _fetch_mock_data(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        获取模拟HIBOR数据

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            List[Dict]: 模拟数据列表
        """
        # 基于期限的基准利率
        term_rates = {
            'hibor_overnight': 3.50,
            'hibor_1m': 3.70,
            'hibor_3m': 3.85,
        }

        base_rate = term_rates.get(self.term, 3.50)

        # 生成日期范围
        dates = pd.date_range(start=start_date, end=end_date, freq='D')

        # 使用日期作为随机种子以确保可重现性
        np.random.seed(42)

        data = []
        for dt in dates:
            # 跳过周末
            if dt.weekday() >= 5:
                continue

            # 添加时间序列相关性（基于AR模型）
            if data:
                prev_rate = data[-1]['value']
                # AR(1)模型：current = 0.9 * previous + noise
                noise = np.random.normal(0, 0.05)
                rate = 0.9 * prev_rate + 0.1 * base_rate + noise
            else:
                rate = base_rate + np.random.normal(0, 0.1)

            # 确保利率在合理范围内
            rate = max(0.0, min(20.0, rate))

            data.append({
                'timestamp': datetime.combine(dt.date(), datetime.min.time()),
                'value': round(rate, 4),
                'quality_score': 0.95
            })

        logger.debug(f"生成 {len(data)} 条模拟HIBOR数据")
        return data

    async def _fetch_real_data(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        从CSV文件获取真实HIBOR数据

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            List[Dict]: 真实数据列表

        Raises:
            FileNotFoundError: CSV文件不存在
            Exception: 读取数据失败
        """
        logger.info(f"从CSV文件获取真实HIBOR数据: {self.csv_path}")

        # 检查文件是否存在
        if not Path(self.csv_path).exists():
            error_msg = f"CSV文件不存在: {self.csv_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        try:
            # 1. 读取CSV文件
            logger.debug("读取CSV文件...")
            df = pd.read_csv(self.csv_path)
            logger.debug(f"CSV包含 {len(df)} 行数据")

            # 2. 日期转换和过滤
            logger.debug("转换日期格式...")
            df['Date'] = pd.to_datetime(df['Date'])

            logger.debug(f"过滤日期范围: {start_date} 到 {end_date}")
            df = df[(df['Date'] >= pd.Timestamp(start_date)) &
                    (df['Date'] <= pd.Timestamp(end_date))]

            logger.debug(f"过滤后剩余 {len(df)} 行数据")

            # 3. 转换为标准格式
            data = []
            for _, row in df.iterrows():
                data.append({
                    'timestamp': row['Date'].to_pydatetime(),
                    'value': float(row['Rate']),
                    'quality_score': 0.98  # 真实数据高质量评分
                })

            logger.info(f"✅ 成功从CSV获取 {len(data)} 条真实HIBOR数据")
            return data

        except Exception as e:
            logger.error(f"❌ 读取CSV失败: {str(e)}")
            raise

    def validate_data(self, data: List[NonPriceDataPoint]) -> DataValidationResult:
        """
        验证HIBOR数据

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
        if len(data) < 10:
            warnings.append(f"数据点数量较少: {len(data)}")

        # 检查时间范围
        timestamps = [d.timestamp for d in data]
        time_span = (max(timestamps) - min(timestamps)).days
        if time_span < 30:
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

        # HIBOR利率合理性检查
        if min_val < 0:
            errors.append(f"利率不能为负数: {min_val}")
        if max_val > 20:
            errors.append(f"利率异常高: {max_val}")

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
        将HIBOR数据转换为OHLCV格式

        Args:
            data: HIBOR数据点列表

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

        # 生成OHLC（对于利率数据，使用5日滚动窗口）
        window = min(5, len(df))
        df['open'] = df['close'].shift(1).fillna(df['close'])
        df['high'] = df['close'].rolling(window=window, min_periods=1).max()
        df['low'] = df['close'].rolling(window=window, min_periods=1).min()

        # 成交量：使用质量评分
        df['volume'] = (df['quality_score'] * 1000000).round().astype(int)

        # 选择列
        result = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].copy()
        result['timestamp'] = pd.to_datetime(result['timestamp'])

        logger.debug(f"转换 {len(data)} 条HIBOR数据为OHLCV格式")
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
