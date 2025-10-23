"""
GOV 爬蟲系統 - 數據處理模塊
"""

import logging
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class DataProcessor:
    """數據處理器"""

    def __init__(self):
        """初始化數據處理器"""
        self.processed_data = {}

    def process_finance_data(self, raw_data: Dict[str, Any]) -> pd.DataFrame:
        """
        處理財經數據

        Args:
            raw_data: 原始數據字典

        Returns:
            處理後的 DataFrame
        """
        try:
            logger.info("正在處理財經數據...")

            records = raw_data.get('records', [])
            if not records:
                logger.warning("未找到財經數據記錄")
                return pd.DataFrame()

            df = pd.DataFrame(records)

            # 數據清理
            df = self._clean_dataframe(df)

            # 數據標準化
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
            if 'value' in df.columns:
                df['value'] = pd.to_numeric(df['value'], errors='coerce')

            logger.info(f"財經數據處理完成 - {len(df)} 行數據")
            return df

        except Exception as e:
            logger.error(f"處理財經數據失敗: {e}")
            return pd.DataFrame()

    def process_property_data(self, raw_data: Dict[str, Any]) -> pd.DataFrame:
        """
        處理物業市場數據

        Args:
            raw_data: 原始數據字典

        Returns:
            處理後的 DataFrame
        """
        try:
            logger.info("正在處理物業市場數據...")

            records = raw_data.get('records', [])
            if not records:
                logger.warning("未找到物業數據記錄")
                return pd.DataFrame()

            df = pd.DataFrame(records)

            # 數據清理
            df = self._clean_dataframe(df)

            # 提取關鍵字段
            key_columns = [col for col in df.columns if any(
                keyword in col.lower() for keyword in ['date', 'price', 'rent', 'transaction', 'volume']
            )]
            if key_columns:
                df = df[key_columns]

            # 數值轉換
            numeric_cols = df.select_dtypes(include=['object']).columns
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            logger.info(f"物業數據處理完成 - {len(df)} 行數據")
            return df

        except Exception as e:
            logger.error(f"處理物業數據失敗: {e}")
            return pd.DataFrame()

    def process_retail_data(self, raw_data: Dict[str, Any]) -> pd.DataFrame:
        """
        處理零售業數據

        Args:
            raw_data: 原始數據字典

        Returns:
            處理後的 DataFrame
        """
        try:
            logger.info("正在處理零售業數據...")

            records = raw_data.get('records', [])
            if not records:
                logger.warning("未找到零售業數據記錄")
                return pd.DataFrame()

            df = pd.DataFrame(records)

            # 數據清理
            df = self._clean_dataframe(df)

            # 數值轉換
            numeric_cols = df.select_dtypes(include=['object']).columns
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            logger.info(f"零售業數據處理完成 - {len(df)} 行數據")
            return df

        except Exception as e:
            logger.error(f"處理零售業數據失敗: {e}")
            return pd.DataFrame()

    def process_traffic_data(self, raw_data: Dict[str, Any]) -> pd.DataFrame:
        """
        處理交通數據

        Args:
            raw_data: 原始數據字典

        Returns:
            處理後的 DataFrame
        """
        try:
            logger.info("正在處理交通數據...")

            records = raw_data.get('records', [])
            if not records:
                logger.warning("未找到交通數據記錄")
                return pd.DataFrame()

            df = pd.DataFrame(records)

            # 數據清理
            df = self._clean_dataframe(df)

            # 數值轉換
            numeric_cols = df.select_dtypes(include=['object']).columns
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            logger.info(f"交通數據處理完成 - {len(df)} 行數據")
            return df

        except Exception as e:
            logger.error(f"處理交通數據失敗: {e}")
            return pd.DataFrame()

    @staticmethod
    def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        清理 DataFrame

        Args:
            df: 輸入 DataFrame

        Returns:
            清理後的 DataFrame
        """
        # 移除完全空的行
        df = df.dropna(how='all')

        # 移除完全空的列
        df = df.dropna(axis=1, how='all')

        # 去除重複行
        df = df.drop_duplicates()

        # 重置索引
        df = df.reset_index(drop=True)

        return df

    def aggregate_data(self, df: pd.DataFrame, group_by: Optional[List[str]] = None,
                      agg_func: str = 'mean') -> pd.DataFrame:
        """
        聚合數據

        Args:
            df: 輸入 DataFrame
            group_by: 分組列
            agg_func: 聚合函數

        Returns:
            聚合後的 DataFrame
        """
        if group_by is None or not group_by:
            return df

        try:
            aggregated = df.groupby(group_by).agg(agg_func)
            logger.info(f"數據聚合完成 - 按 {group_by} 分組")
            return aggregated
        except Exception as e:
            logger.error(f"數據聚合失敗: {e}")
            return df

    def calculate_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        計算統計數據

        Args:
            df: 輸入 DataFrame

        Returns:
            統計數據字典
        """
        try:
            stats = {
                'row_count': len(df),
                'column_count': len(df.columns),
                'columns': list(df.columns),
                'missing_values': df.isnull().sum().to_dict(),
                'dtypes': df.dtypes.to_dict(),
                'describe': df.describe().to_dict() if len(df) > 0 else {}
            }
            logger.info("統計計算完成")
            return stats
        except Exception as e:
            logger.error(f"計算統計失敗: {e}")
            return {}

    def merge_datasets(self, dataframes: List[pd.DataFrame], how: str = 'outer') -> pd.DataFrame:
        """
        合併多個數據集

        Args:
            dataframes: DataFrame 列表
            how: 合併方式 ('inner', 'outer', 'left', 'right')

        Returns:
            合併後的 DataFrame
        """
        if not dataframes:
            logger.warning("沒有要合併的數據集")
            return pd.DataFrame()

        try:
            result = dataframes[0]
            for df in dataframes[1:]:
                result = pd.merge(result, df, how=how)
            logger.info(f"數據集合併完成 ({how} 合併)")
            return result
        except Exception as e:
            logger.error(f"合併數據集失敗: {e}")
            return pd.DataFrame()

    @staticmethod
    def normalize_columns(df: pd.DataFrame, exclude: Optional[List[str]] = None) -> pd.DataFrame:
        """
        標準化列名

        Args:
            df: 輸入 DataFrame
            exclude: 排除的列

        Returns:
            標準化後的 DataFrame
        """
        exclude = exclude or []
        rename_dict = {}

        for col in df.columns:
            if col not in exclude:
                # 轉換為小寫，用下劃線替換空格
                new_name = col.lower().replace(' ', '_').replace('-', '_')
                rename_dict[col] = new_name

        return df.rename(columns=rename_dict)

    def validate_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        驗證數據質量

        Args:
            df: 輸入 DataFrame

        Returns:
            質量檢查結果
        """
        if df.empty:
            return {'is_valid': False, 'reason': '數據集為空'}

        quality_report = {
            'is_valid': True,
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'missing_values_ratio': (df.isnull().sum().sum() / (len(df) * len(df.columns))),
            'duplicate_rows': df.duplicated().sum(),
            'issues': []
        }

        # 檢查缺失值
        if quality_report['missing_values_ratio'] > 0.5:
            quality_report['issues'].append("缺失值過多 (>50%)")
            quality_report['is_valid'] = False

        # 檢查重複行
        if quality_report['duplicate_rows'] > 0:
            quality_report['issues'].append(f"發現 {quality_report['duplicate_rows']} 行重複數據")

        logger.info(f"數據質量檢查完成 - 有效: {quality_report['is_valid']}")
        return quality_report
