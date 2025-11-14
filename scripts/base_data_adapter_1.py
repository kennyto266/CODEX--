"""
基礎數據適配器抽象類
Sprint 1 - US-003

實現IDataAdapter接口的基礎適配器類，提供數據獲取、驗證和重試機制。
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Type
import pandas as pd
from pandas import DataFrame, isna, Series

from src.core.interfaces.data_adapter import IDataAdapter, DataValidationError


logger = logging.getLogger(__name__)


class BaseDataAdapter(IDataAdapter, ABC):
    """
    基礎數據適配器

    實現IDataAdapter接口，提供通用功能。
    子類必須實現抽象方法。
    """

    # 配置參數
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0
    QUALITY_THRESHOLD: float = 0.8

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化適配器

        Args:
            config: 配置參數
        """
        self.config = config or {}
        self._name = self._extract_name()
        self._data_source = self._extract_data_source()
        self._validate_config()

    @property
    def name(self) -> str:
        """適配器名稱"""
        return self._name

    @property
    def data_source(self) -> str:
        """數據源名稱"""
        return self._data_source

    def _extract_name(self) -> str:
        """從類名提取適配器名稱"""
        return self.__class__.__name__

    def _extract_data_source(self) -> str:
        """從類名提取數據源名稱"""
        name = self.__class__.__name__
        if 'Adapter' in name:
            return name.replace('Adapter', '').lower()
        return name.lower()

    def _validate_config(self):
        """驗證配置參數"""
        # 子類可以重寫此方法
        pass

    async def fetch_data(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        **kwargs
    ) -> DataFrame:
        """
        獲取歷史數據（帶重試機制）

        Args:
            symbol: 股票代碼
            start_date: 開始日期
            end_date: 結束日期
            **kwargs: 其他參數

        Returns:
            DataFrame: 標準化的數據

        Raises:
            DataValidationError: 數據驗證失敗
            ConnectionError: 網絡連接失敗
        """
        return await self._retry(
            self._fetch_data_impl,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            **kwargs
        )

    async def fetch_realtime_data(self, symbol: str, **kwargs) -> Dict:
        """
        獲取實時數據（帶重試機制）

        Args:
            symbol: 股票代碼
            **kwargs: 其他參數

        Returns:
            Dict: 實時數據字典
        """
        return await self._retry(
            self._fetch_realtime_data_impl,
            symbol=symbol,
            **kwargs
        )

    async def validate_data(self, data: DataFrame) -> bool:
        """
        驗證數據質量

        Args:
            data: 待驗證的數據

        Returns:
            bool: 驗證是否通過

        Raises:
            DataValidationError: 驗證失敗拋出異常
        """
        try:
            # 基本結構驗證
            if data is None:
                raise DataValidationError("數據為空")

            if data.empty:
                raise DataValidationError("數據為空DataFrame")

            # 檢查必需的列
            required_columns = await self._get_required_columns()
            missing_columns = set(required_columns) - set(data.columns)
            if missing_columns:
                raise DataValidationError(
                    f"缺少必需的列: {missing_columns}"
                )

            # 數據完整性檢查
            total_cells = len(data) * len(data.columns)
            if total_cells > 0:
                null_count = data.isnull().sum().sum()
                null_ratio = null_count / total_cells
                if null_ratio > 0.5:  # 超過50%空值
                    raise DataValidationError(
                        f"數據空值過多: {null_ratio:.2%}"
                    )

            # 數值列檢查
            numeric_columns = data.select_dtypes(include=['number']).columns
            if len(numeric_columns) == 0:
                raise DataValidationError("沒有數值列")

            # 檢查異常值
            for col in numeric_columns:
                if col in data.columns and len(data) > 0:
                    q1 = data[col].quantile(0.01)
                    q3 = data[col].quantile(0.99)
                    if q3 != q1:  # 避免除零
                        outliers = data[(data[col] < q1) | (data[col] > q3)][col]
                        if len(outliers) > len(data) * 0.1:  # 超過10%異常值
                            logger.warning(
                                f"列 {col} 異常值較多: {len(outliers)}/{len(data)}"
                            )

            # 執行子類自定義驗證
            await self._custom_validate(data)

            logger.info(f"數據驗證通過: {len(data)} 行, {len(data.columns)} 列")
            return True

        except Exception as e:
            error_msg = f"數據驗證失敗: {e}"
            logger.error(error_msg)
            raise DataValidationError(error_msg) from e

    async def get_data_quality_score(self, data: DataFrame) -> float:
        """
        計算數據質量評分 (0-1)

        Args:
            data: 數據

        Returns:
            float: 質量評分
        """
        if data is None or data.empty:
            return 0.0

        score = 1.0
        total_cells = len(data) * len(data.columns)

        if total_cells == 0:
            return 0.0

        # 減分項：空值比例
        null_ratio = data.isnull().sum().sum() / total_cells
        score -= null_ratio * 0.4

        # 減分項：重複行比例
        duplicate_ratio = data.duplicated().sum() / len(data)
        score -= duplicate_ratio * 0.3

        # 減分項：列缺失
        required_columns = await self._get_required_columns()
        missing_ratio = len(set(required_columns) - set(data.columns)) / max(len(required_columns), 1)
        score -= missing_ratio * 0.3

        # 確保評分在 [0, 1] 範圍內
        return max(0.0, min(1.0, score))

    async def get_supported_symbols(self) -> List[str]:
        """
        獲取支持的股票代碼列表

        Returns:
            List[str]: 股票代碼列表
        """
        # 子類應重寫此方法
        return []

    async def cleanup(self) -> None:
        """清理資源"""
        logger.info(f"清理適配器資源: {self.name}")

    # ==================== 抽象方法 ====================

    @abstractmethod
    async def _fetch_data_impl(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        **kwargs
    ) -> DataFrame:
        """
        實際的數據獲取實現

        子類必須實現此方法。

        Args:
            symbol: 股票代碼
            start_date: 開始日期
            end_date: 結束日期
            **kwargs: 其他參數

        Returns:
            DataFrame: 數據

        Raises:
            Exception: 獲取失敗
        """
        pass

    @abstractmethod
    async def _fetch_realtime_data_impl(self, symbol: str, **kwargs) -> Dict:
        """
        實際的實時數據獲取實現

        子類必須實現此方法。

        Args:
            symbol: 股票代碼
            **kwargs: 其他參數

        Returns:
            Dict: 實時數據

        Raises:
            Exception: 獲取失敗
        """
        pass

    @abstractmethod
    async def _get_required_columns(self) -> List[str]:
        """
        獲取必需的列名

        子類應返回所需的列名列表。

        Returns:
            List[str]: 必需的列名列表
        """
        pass

    async def _custom_validate(self, data: DataFrame) -> None:
        """
        自定義數據驗證

        子類可以重寫此方法進行特定驗證。

        Args:
            data: 待驗證的數據

        Raises:
            DataValidationError: 驗證失敗
        """
        pass

    # ==================== 工具方法 ====================

    async def _retry(
        self,
        func,
        max_retries: Optional[int] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        異步重試機制

        Args:
            func: 要重試的函數
            max_retries: 最大重試次數
            *args: 位置參數
            **kwargs: 關鍵字參數

        Returns:
            函數執行結果

        Raises:
            最後一次重試的異常
        """
        max_retries = max_retries or self.MAX_RETRIES
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    wait_time = self.RETRY_DELAY * (2 ** attempt)  # 指數退避
                    logger.warning(
                        f"適配器 {self.name} 第 {attempt + 1} 次嘗試失敗: {e}，"
                        f"{wait_time:.1f}秒後重試..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"適配器 {self.name} 所有重試嘗試失敗，"
                        f"已達到最大重試次數 {max_retries}"
                    )
                    break

        if last_exception:
            raise last_exception

    def _normalize_symbol(self, symbol: str) -> str:
        """
        標準化股票代碼格式

        Args:
            symbol: 原始股票代碼

        Returns:
            str: 標準化的股票代碼
        """
        if not symbol:
            return symbol

        # 轉換為大寫，移除多餘空格
        symbol = symbol.strip().upper()

        # 標準化香港股票代碼格式
        if not symbol.endswith('.HK'):
            if symbol.replace('.', '').isdigit():
                symbol = f"{symbol.zfill(4)}.HK"
            else:
                symbol = f"{symbol}.HK"

        return symbol

    def _ensure_date_range(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        default_days: int = 365
    ) -> tuple[datetime, datetime]:
        """
        確保日期範圍有效

        Args:
            start_date: 開始日期
            end_date: 結束日期
            default_days: 默認天數

        Returns:
            tuple: (start_date, end_date)
        """
        now = datetime.now()

        if end_date is None:
            end_date = now

        if start_date is None:
            start_date = end_date - timedelta(days=default_days)

        # 確保開始日期不晚於結束日期
        if start_date > end_date:
            start_date, end_date = end_date, start_date

        return start_date, end_date

    def _standardize_dataframe(
        self,
        data: DataFrame,
        required_columns: Optional[List[str]] = None
    ) -> DataFrame:
        """
        標準化 DataFrame 格式

        Args:
            data: 原始數據
            required_columns: 必需的列

        Returns:
            DataFrame: 標準化後的數據
        """
        if data is None or data.empty:
            return data

        # 複製數據避免修改原始數據
        df = data.copy()

        # 重置索引（如果索引不是日期）
        if not isinstance(df.index, pd.DatetimeIndex):
            df = df.reset_index(drop=True)

        # 確保日期列是 datetime 類型
        date_columns = ['date', 'timestamp', 'datetime', 'Date', 'DateTime']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # 按日期排序
        date_col = None
        for col in date_columns:
            if col in df.columns:
                date_col = col
                break

        if date_col:
            df = df.sort_values(by=date_col)

        # 移除重複行
        df = df.drop_duplicates()

        # 處理缺失值
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            df[numeric_cols] = df[numeric_cols].fillna(method='ffill')

        return df

    def _log_data_info(self, data: DataFrame, operation: str):
        """
        記錄數據信息

        Args:
            data: 數據
            operation: 操作名稱
        """
        if data is not None and not data.empty:
            logger.info(
                f"{operation} 完成: {len(data)} 行, "
                f"{len(data.columns)} 列, "
                f"數據源: {self.data_source}"
            )
        else:
            logger.warning(f"{operation} 返回空數據")


# 便捷基類別名
BaseAdapter = BaseDataAdapter
