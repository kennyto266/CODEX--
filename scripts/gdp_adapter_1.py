"""
GDP 數據適配器
Sprint 2 - US-006

實現香港統計處(C&SD) GDP數據的獲取和處理。
支持5個GDP指標：名義GDP、增長率、第一產業、第二產業、第三產業。
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pandas import DataFrame, date_range
import pandas as pd

from src.core.interfaces.data_adapter import IDataAdapter, DataValidationError
from .base_data_adapter import BaseDataAdapter


logger = logging.getLogger(__name__)


class GDPAdapter(BaseDataAdapter, IDataAdapter):
    """
    GDP 數據適配器

    獲取香港統計處 GDP 數據。
    目前使用模擬數據，後續可集成真實數據源。
    """

    # GDP 指標列表
    GDP_INDICATORS = {
        'gdp_nominal': '名義GDP',
        'gdp_growth': 'GDP增長率',
        'gdp_primary': '第一產業GDP',
        'gdp_secondary': '第二產業GDP',
        'gdp_tertiary': '第三產業GDP',
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化 GDP 適配器

        Args:
            config: 配置參數
                - use_mock_data: 是否使用模擬數據 (默認: True)
                - data_source_url: 真實數據源URL
                - api_key: API密鑰（如需要）
                - update_interval: 更新間隔（秒）
        """
        super().__init__(config)

        # 配置參數
        self.use_mock_data = self.config.get('use_mock_data', True)
        self.data_source_url = self.config.get('data_source_url', 'https://www.censtatd.gov.hk')
        self.update_interval = self.config.get('update_interval', 86400)  # 24小時

        # 緩存
        self._last_update: Optional[datetime] = None
        self._cached_data: Dict[str, float] = {}

        logger.info(f"初始化 GDP 適配器 - 使用模擬數據: {self.use_mock_data}")

    async def fetch_gdp_nominal(self) -> float:
        """
        獲取名義GDP

        Returns:
            float: 名義GDP (億港元)

        Raises:
            Exception: 獲取失敗
        """
        data = await self.fetch_all_gdp_indicators()
        gdp_value = data.get('gdp_nominal')

        if gdp_value is None:
            raise ValueError("無法獲取名義GDP")

        logger.info(f"獲取名義GDP: {gdp_value:.2f} 億港元")
        return gdp_value

    async def fetch_gdp_growth(self) -> float:
        """
        獲取GDP增長率

        Returns:
            float: GDP增長率 (%)

        Raises:
            Exception: 獲取失敗
        """
        data = await self.fetch_all_gdp_indicators()
        growth_rate = data.get('gdp_growth')

        if growth_rate is None:
            raise ValueError("無法獲取GDP增長率")

        logger.info(f"獲取GDP增長率: {growth_rate:.2f}%")
        return growth_rate

    async def fetch_gdp_sectoral(self) -> Dict[str, float]:
        """
        獲取三大產業GDP

        Returns:
            Dict[str, float]: 產業GDP字典，包含第一、二、三產業

        Raises:
            Exception: 獲取失敗
        """
        data = await self.fetch_all_gdp_indicators()

        sectoral_data = {
            'gdp_primary': data.get('gdp_primary'),
            'gdp_secondary': data.get('gdp_secondary'),
            'gdp_tertiary': data.get('gdp_tertiary')
        }

        # 檢查是否有缺失值
        missing = [k for k, v in sectoral_data.items() if v is None]
        if missing:
            raise ValueError(f"缺少產業GDP數據: {missing}")

        logger.info(f"獲取三大產業GDP: {sectoral_data}")
        return sectoral_data

    async def fetch_all_gdp_indicators(self) -> Dict[str, float]:
        """
        獲取全部5個GDP指標

        Returns:
            Dict[str, float]: GDP指標字典，包含名義GDP、增長率、三大產業

        Raises:
            Exception: 獲取失敗
        """
        # 檢查緩存
        if self._is_cache_valid():
            logger.debug("使用緩存的 GDP 數據")
            return self._cached_data.copy()

        # 獲取數據
        try:
            if self.use_mock_data:
                data = await self._fetch_mock_gdp_data()
            else:
                data = await self._fetch_real_gdp_data()

            # 驗證數據
            await self._validate_gdp_data(data)

            # 更新緩存
            self._cached_data = data
            self._last_update = datetime.now()

            logger.info(f"獲取GDP指標完成: {data}")
            return data

        except Exception as e:
            logger.error(f"獲取GDP數據失敗: {e}")
            raise

    async def get_historical_gdp(self, years: int = 5) -> DataFrame:
        """
        獲取歷史GDP數據

        Args:
            years: 年數

        Returns:
            DataFrame: 歷史數據，包含日期和各項GDP指標

        Raises:
            Exception: 獲取失敗
        """
        # 計算日期範圍
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)

        logger.info(f"獲取 {years} 年歷史GDP數據: {start_date.date()} - {end_date.date()}")

        # 生成日期範圍（季度數據）
        dates = pd.date_range(start=start_date, end=end_date, freq='Q')

        # 生成歷史數據（使用模擬數據）
        historical_data = []

        for date in dates:
            # 生成該日期的 GDP 數據
            quarter_data = await self._generate_quarterly_gdp(date)
            quarter_data['date'] = date
            historical_data.append(quarter_data)

        # 轉換為 DataFrame
        df = pd.DataFrame(historical_data)
        df = df.set_index('date')

        # 標準化數據格式
        df = self._standardize_dataframe(df, list(self.GDP_INDICATORS.keys()))

        self._log_data_info(df, "獲取歷史GDP數據")
        return df

    # ==================== 實現 IDataAdapter 接口 ====================

    async def _fetch_data_impl(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        **kwargs
    ) -> DataFrame:
        """
        獲取歷史數據的實現

        Args:
            symbol: 股票代碼（此處不使用）
            start_date: 開始日期
            end_date: 結束日期
            **kwargs: 其他參數

        Returns:
            DataFrame: GDP 歷史數據
        """
        # 計算年份
        if start_date and end_date:
            years = (end_date - start_date).days / 365
        else:
            years = kwargs.get('years', 5)

        return await self.get_historical_gdp(years=int(years))

    async def _fetch_realtime_data_impl(self, symbol: str, **kwargs) -> Dict:
        """
        獲取實時GDP數據的實現

        Args:
            symbol: 股票代碼（此處不使用）
            **kwargs: 其他參數

        Returns:
            Dict: 實時GDP數據
        """
        data = await self.fetch_all_gdp_indicators()

        # 添加時間戳
        result = {
            'timestamp': datetime.now(),
            'indicators': data,
            'data_source': self.data_source,
            'adapter': self.name
        }

        return result

    async def _get_required_columns(self) -> List[str]:
        """
        獲取必需的列名

        Returns:
            List[str]: 必需的列名列表
        """
        return list(self.GDP_INDICATORS.keys()) + ['date']

    async def _custom_validate(self, data: DataFrame) -> None:
        """
        自定義GDP數據驗證

        Args:
            data: 待驗證的數據

        Raises:
            DataValidationError: 驗證失敗
        """
        # 檢查GDP數值的合理性
        for indicator, name in self.GDP_INDICATORS.items():
            if indicator in data.columns:
                values = data[indicator].dropna()

                if len(values) > 0:
                    # 檢查是否為負值（GDP不應該是負的，但允許輕微負增長）
                    if indicator == 'gdp_growth':
                        # GDP增長率可以為負
                        negative_count = (values < -20).sum()  # 小於-20%認為異常
                        if negative_count > 0:
                            raise DataValidationError(
                                f"{name} 增長率過低 (<-20%): {negative_count} 個"
                            )
                    else:
                        # 其他指標不應該為負
                        negative_count = (values < 0).sum()
                        if negative_count > 0:
                            raise DataValidationError(
                                f"{name} 存在負值: {negative_count} 個"
                            )

                    # 檢查是否過高
                    if indicator == 'gdp_growth':
                        high_count = (values > 20).sum()  # 大於20%認為異常
                        if high_count > 0:
                            logger.warning(
                                f"{name} 增長率過高 (>20%): {high_count} 個"
                            )
                    elif indicator == 'gdp_nominal':
                        high_count = (values > 10000).sum()  # 大於10000億認為異常
                        if high_count > 0:
                            logger.warning(
                                f"{name} 過高 (>10000億): {high_count} 個"
                            )

                    # 檢查異常值
                    if len(values) > 4:  # 至少有4個季度的數據
                        q1 = values.quantile(0.25)
                        q3 = values.quantile(0.75)
                        iqr = q3 - q1
                        lower_bound = q1 - 3 * iqr
                        upper_bound = q3 + 3 * iqr

                        outliers = values[(values < lower_bound) | (values > upper_bound)]
                        if len(outliers) > len(values) * 0.1:  # 超過10%異常值
                            logger.warning(
                                f"{name} 異常值較多: {len(outliers)}/{len(values)}"
                            )

    # ==================== 私有方法 ====================

    async def _fetch_mock_gdp_data(self) -> Dict[str, float]:
        """
        獲取模擬GDP數據

        Returns:
            Dict[str, float]: GDP數據字典
        """
        # 模擬GDP數據（基於香港實際經濟水平）
        base_values = {
            'gdp_nominal': 2800.0,  # 2800億港元
            'gdp_growth': 2.5,      # 2.5%增長率
            'gdp_primary': 10.0,    # 第一產業 10億
            'gdp_secondary': 700.0, # 第二產業 700億
            'gdp_tertiary': 2090.0, # 第三產業 2090億
        }

        # 添加隨機波動
        import random
        data = {}
        for indicator, value in base_values.items():
            # 根據指標類型調整波動範圍
            if indicator == 'gdp_growth':
                fluctuation = random.uniform(-1.0, 1.0)  # ±1%
            elif indicator == 'gdp_nominal':
                fluctuation = random.uniform(-50, 50)    # ±50億
            else:
                fluctuation = random.uniform(-0.02, 0.02) * value  # ±2%

            data[indicator] = round(value + fluctuation, 4)

        logger.debug(f"生成模擬GDP數據: {data}")
        return data

    async def _fetch_real_gdp_data(self) -> Dict[str, float]:
        """
        獲取真實GDP數據
        從data/real_gov_data/real_gdp_data_2025_11_11.json讀取

        Returns:
            Dict[str, float]: GDP數據字典

        Raises:
            Exception: 讀取失敗
        """
        import json
        from pathlib import Path

        try:
            # 讀取真實GDP數據文件
            data_file = Path("data/real_gov_data/real_gdp_data_2025_11_11.json")

            if not data_file.exists():
                raise FileNotFoundError(f"真實GDP數據文件不存在: {data_file}")

            with open(data_file, 'r', encoding='utf-8') as f:
                real_data = json.load(f)

            # 獲取最新年度的數據
            nominal_gdp = real_data['gdp_nominal_hkd']['data']
            real_gdp = real_data['gdp_real_2023_base']['data']
            per_capita = real_data['gdp_per_capita_2023_base']['data']

            # 獲取2024年最新數據
            latest_year = '2024'

            if latest_year not in nominal_gdp or latest_year not in real_gdp:
                raise ValueError(f"無法找到{latest_year}年GDP數據")

            # 計算GDP增長率 (2023-2024)
            gdp_2023 = nominal_gdp.get('2023', 0)
            gdp_2024 = nominal_gdp.get('2024', 0)
            growth_rate = ((gdp_2024 - gdp_2023) / gdp_2023 * 100) if gdp_2023 else 0

            # 構建返回數據
            data = {
                'gdp_nominal': round(gdp_2024 / 100, 2),  # 轉換為百億港元
                'gdp_growth': round(growth_rate, 2),
                'gdp_primary': 0.1,  # TODO: 需要從政府統計處獲取產業分解數據
                'gdp_secondary': round(gdp_2024 * 0.08 / 100, 2),  # 估算第二產業約8%
                'gdp_tertiary': round(gdp_2024 * 0.90 / 100, 2),  # 估算第三產業約90%
            }

            # 驗證數據
            await self._validate_gdp_data(data)

            logger.info(f"成功獲取真實GDP數據: {data}")
            return data

        except FileNotFoundError as e:
            logger.error(f"真實GDP數據文件不存在: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"解析GDP數據文件失敗: {e}")
            raise
        except Exception as e:
            logger.error(f"獲取真實GDP數據失敗: {e}")
            raise

    async def _validate_gdp_data(self, data: Dict[str, float]) -> None:
        """
        驗證GDP數據

        Args:
            data: GDP數據字典

        Raises:
            DataValidationError: 驗證失敗
        """
        # 檢查是否包含所有必需的指標
        missing_indicators = set(self.GDP_INDICATORS.keys()) - set(data.keys())
        if missing_indicators:
            raise DataValidationError(f"缺少GDP指標: {missing_indicators}")

        # 檢查數值是否為數字
        for indicator, value in data.items():
            if not isinstance(value, (int, float)):
                raise DataValidationError(
                    f"{indicator} 值類型錯誤: {type(value)}"
                )

        # 檢查數值是否合理
        if 'gdp_nominal' in data and data['gdp_nominal'] <= 0:
            raise DataValidationError("名義GDP必須大於0")

        if 'gdp_growth' in data and data['gdp_growth'] < -50:
            raise DataValidationError("GDP增長率過低")

        if 'gdp_growth' in data and data['gdp_growth'] > 50:
            raise DataValidationError("GDP增長率過高")

    def _is_cache_valid(self) -> bool:
        """
        檢查緩存是否有效

        Returns:
            bool: 緩存是否有效
        """
        if not self._cached_data or not self._last_update:
            return False

        age = (datetime.now() - self._last_update).total_seconds()
        return age < self.update_interval

    async def _generate_quarterly_gdp(self, date: datetime) -> Dict[str, float]:
        """
        生成季度GDP數據

        Args:
            date: 日期

        Returns:
            Dict[str, float]: 季度GDP數據
        """
        # 基於實際經濟周期生成數據
        base_nominal = 2800.0
        base_growth = 2.5

        # 根據年份添加趨勢
        year_factor = (date.year - 2020) * 0.05  # 每年增長5%
        nominal = base_nominal * (1 + year_factor)

        # 根據季度添加季節性
        quarter = ((date.month - 1) // 3) + 1
        quarter_factor = [0.98, 1.00, 1.02, 1.00][quarter - 1]
        nominal *= quarter_factor

        # 增長率有波動
        import random
        random.seed(int(date.strftime('%Y%m%d')))
        growth = base_growth + random.normalvariate(0, 0.5)

        # 產業結構（基於香港實際情況）
        primary_ratio = 0.005   # 0.5%
        secondary_ratio = 0.25  # 25%
        tertiary_ratio = 0.745  # 74.5%

        sectoral_data = {
            'gdp_nominal': round(nominal, 4),
            'gdp_growth': round(growth, 4),
            'gdp_primary': round(nominal * primary_ratio, 4),
            'gdp_secondary': round(nominal * secondary_ratio, 4),
            'gdp_tertiary': round(nominal * tertiary_ratio, 4),
        }

        return sectoral_data
