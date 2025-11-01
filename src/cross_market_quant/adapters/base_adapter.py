"""
BaseAdapter - 所有数据适配器的基类

定义了统一的数据获取接口，确保所有适配器实现一致的数据返回格式
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class BaseAdapter(ABC):
    """数据适配器基类"""

    def __init__(self, name: str):
        """
        初始化适配器

        Args:
            name: 适配器名称
        """
        self.name = name
        self.logger = logging.getLogger(f"cross_market_quant.adapters.{name}")

    @abstractmethod
    async def fetch_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        **kwargs
    ) -> pd.DataFrame:
        """
        获取历史数据

        Args:
            symbol: 数据符号
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            **kwargs: 额外参数

        Returns:
            DataFrame，包含列: Date, Open, High, Low, Close, Volume
        """
        pass

    @abstractmethod
    async def get_realtime_data(self, symbol: str, **kwargs) -> Dict:
        """
        获取实时数据

        Args:
            symbol: 数据符号
            **kwargs: 额外参数

        Returns:
            实时数据字典
        """
        pass

    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        验证数据完整性

        Args:
            df: 待验证的数据

        Returns:
            数据是否有效
        """
        try:
            if df is None or df.empty:
                self.logger.warning("数据为空")
                return False

            required_columns = ['Date', 'Open', 'High', 'Low', 'Close']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                self.logger.error(f"缺少必要列: {missing_columns}")
                return False

            if df.isnull().any().any():
                self.logger.warning("数据包含空值")
                return False

            return True
        except Exception as e:
            self.logger.error(f"数据验证失败: {e}")
            return False

    def normalize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化数据格式

        Args:
            df: 原始数据

        Returns:
            标准化后的数据
        """
        df = df.copy()

        # 确保Date列是datetime类型
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])

        # 确保数值列是float类型
        numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # 按日期排序
        if 'Date' in df.columns:
            df = df.sort_values('Date')

        # 重置索引
        df = df.reset_index(drop=True)

        return df

    async def handle_error(self, error: Exception) -> None:
        """
        处理错误

        Args:
            error: 异常对象
        """
        self.logger.error(f"{self.name}发生错误: {error}")

        # 可以在这里添加重试逻辑、告警等
        pass
