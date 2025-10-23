"""
GOV 爬蟲系統 - 數據處理模塊 (Phase 2 增強版)

功能改進：
- Schema 驗證
- 數據類型檢查
- 範圍驗證
- 異常值檢測
- 一致性檢查
- 詳細驗證報告
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ValidationRule:
    """數據驗證規則"""
    column: str
    dtype: Optional[str] = None  # 期望的數據類型
    min_value: Optional[float] = None  # 最小值
    max_value: Optional[float] = None  # 最大值
    allowed_values: Optional[List[Any]] = None  # 允許的值
    required: bool = True  # 是否必需
    max_length: Optional[int] = None  # 字符串最大長度
    pattern: Optional[str] = None  # 正則表達式模式


@dataclass
class ValidationResult:
    """驗證結果"""
    is_valid: bool
    total_rows: int
    valid_rows: int
    invalid_rows: int
    errors: List[str]
    warnings: List[str]
    details: Dict[str, Any]


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
        驗證數據質量 (Legacy method - 保留向後兼容)

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

    # ========== Phase 2: 新增強數據驗證方法 ==========

    def validate_schema(self, df: pd.DataFrame, rules: List[ValidationRule]) -> ValidationResult:
        """
        驗證數據結構和類型

        Args:
            df: 輸入 DataFrame
            rules: 驗證規則列表

        Returns:
            驗證結果
        """
        errors = []
        warnings = []
        details = {}

        # 檢查必需的列
        required_columns = [r.column for r in rules if r.required]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            errors.append(f"缺少必需的列: {missing_columns}")

        # 逐列驗證
        for rule in rules:
            if rule.column not in df.columns:
                if rule.required:
                    errors.append(f"列 '{rule.column}' 不存在且被標記為必需")
                continue

            col_details = {'valid': 0, 'invalid': 0, 'issues': []}

            # 驗證數據類型
            if rule.dtype:
                dtype_mapping = {
                    'int': 'int64',
                    'float': 'float64',
                    'str': 'object',
                    'datetime': 'datetime64'
                }
                expected_dtype = dtype_mapping.get(rule.dtype, rule.dtype)

                # 嘗試轉換
                try:
                    if rule.dtype == 'int':
                        df[rule.column] = pd.to_numeric(df[rule.column], errors='coerce').astype('Int64')
                    elif rule.dtype == 'float':
                        df[rule.column] = pd.to_numeric(df[rule.column], errors='coerce')
                    elif rule.dtype == 'datetime':
                        df[rule.column] = pd.to_datetime(df[rule.column], errors='coerce')
                except Exception as e:
                    warnings.append(f"列 '{rule.column}' 類型轉換失敗: {e}")

            # 驗證範圍
            if rule.min_value is not None or rule.max_value is not None:
                numeric_col = pd.to_numeric(df[rule.column], errors='coerce')
                if rule.min_value is not None:
                    out_of_range = (numeric_col < rule.min_value).sum()
                    if out_of_range > 0:
                        col_details['issues'].append(f"{out_of_range} 個值小於最小值 {rule.min_value}")

                if rule.max_value is not None:
                    out_of_range = (numeric_col > rule.max_value).sum()
                    if out_of_range > 0:
                        col_details['issues'].append(f"{out_of_range} 個值大於最大值 {rule.max_value}")

            # 驗證允許的值
            if rule.allowed_values:
                invalid_values = df[~df[rule.column].isin(rule.allowed_values)][rule.column].unique()
                if len(invalid_values) > 0:
                    col_details['issues'].append(f"發現不允許的值: {list(invalid_values)[:5]}")

            # 驗證字符串長度
            if rule.max_length and df[rule.column].dtype == 'object':
                too_long = (df[rule.column].astype(str).str.len() > rule.max_length).sum()
                if too_long > 0:
                    col_details['issues'].append(f"{too_long} 個字符串超過最大長度 {rule.max_length}")

            details[rule.column] = col_details

        valid_rows = len(df) - len(df[df.isnull().any(axis=1)])
        invalid_rows = len(df) - valid_rows

        is_valid = len(errors) == 0

        result = ValidationResult(
            is_valid=is_valid,
            total_rows=len(df),
            valid_rows=valid_rows,
            invalid_rows=invalid_rows,
            errors=errors,
            warnings=warnings,
            details=details
        )

        logger.info(f"Schema 驗證完成 - 有效: {result.is_valid}, "
                   f"有效行數: {result.valid_rows}/{result.total_rows}")
        return result

    def detect_outliers(self, df: pd.DataFrame, columns: Optional[List[str]] = None,
                       method: str = 'iqr', threshold: float = 1.5) -> Dict[str, Any]:
        """
        檢測異常值（離群點）

        Args:
            df: 輸入 DataFrame
            columns: 要檢測的列（如為 None，則檢測所有數值列）
            method: 檢測方法 ('iqr', 'zscore')
            threshold: 閾值 (IQR: 1.5, Z-score: 3)

        Returns:
            異常值檢測結果
        """
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        outliers = {}

        for col in columns:
            if col not in df.columns:
                logger.warning(f"列 '{col}' 不存在")
                continue

            numeric_col = pd.to_numeric(df[col], errors='coerce')

            if method == 'iqr':
                Q1 = numeric_col.quantile(0.25)
                Q3 = numeric_col.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR

                outlier_mask = (numeric_col < lower_bound) | (numeric_col > upper_bound)
                outlier_indices = df[outlier_mask].index.tolist()

            elif method == 'zscore':
                mean = numeric_col.mean()
                std = numeric_col.std()
                z_scores = np.abs((numeric_col - mean) / std)
                outlier_mask = z_scores > threshold
                outlier_indices = df[outlier_mask].index.tolist()

            else:
                logger.error(f"不支持的方法: {method}")
                continue

            outliers[col] = {
                'count': len(outlier_indices),
                'percentage': (len(outlier_indices) / len(df) * 100),
                'indices': outlier_indices[:100]  # 限制輸出前 100 個
            }

        logger.info(f"異常值檢測完成 - 檢測了 {len(outliers)} 列")
        return outliers

    def check_consistency(self, df: pd.DataFrame, rules: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        檢查數據一致性

        Args:
            df: 輸入 DataFrame
            rules: 一致性檢查規則
                例如: {
                    'primary_key': ['id'],  # 主鍵（唯一性檢查）
                    'referential': {  # 外鍵檢查
                        'user_id': {'table': 'users', 'column': 'id'}
                    },
                    'conditional': {  # 條件檢查
                        'if_status_active_then_has_date': lambda r: r['status'] == 'active' and r['date'] is not None
                    }
                }

        Returns:
            一致性檢查結果
        """
        consistency_report = {
            'is_consistent': True,
            'issues': [],
            'details': {}
        }

        # 檢查主鍵唯一性
        if 'primary_key' in rules:
            pk_columns = rules['primary_key']
            duplicates = df[df.duplicated(subset=pk_columns, keep=False)]
            if len(duplicates) > 0:
                consistency_report['issues'].append(
                    f"主鍵不唯一: {pk_columns}，發現 {len(duplicates)} 個重複值"
                )
                consistency_report['is_consistent'] = False
                consistency_report['details']['duplicate_keys'] = len(duplicates)

        # 檢查條件規則
        if 'conditional' in rules:
            for rule_name, rule_func in rules['conditional'].items():
                invalid_rows = df[~df.apply(rule_func, axis=1)]
                if len(invalid_rows) > 0:
                    consistency_report['issues'].append(
                        f"條件規則 '{rule_name}' 失敗: {len(invalid_rows)} 行不符合條件"
                    )
                    consistency_report['is_consistent'] = False

        logger.info(f"一致性檢查完成 - 一致: {consistency_report['is_consistent']}")
        return consistency_report

    def validate_data_completeness(self, df: pd.DataFrame,
                                  threshold: float = 0.8) -> Dict[str, Any]:
        """
        驗證數據完整性

        Args:
            df: 輸入 DataFrame
            threshold: 接受的最小完整性比例（默認 80%）

        Returns:
            完整性檢查結果
        """
        if df.empty:
            return {'is_complete': False, 'completeness': 0.0, 'reason': '數據集為空'}

        total_cells = len(df) * len(df.columns)
        missing_cells = df.isnull().sum().sum()
        completeness = (total_cells - missing_cells) / total_cells

        completeness_report = {
            'is_complete': completeness >= threshold,
            'completeness': completeness,
            'threshold': threshold,
            'total_cells': total_cells,
            'missing_cells': missing_cells,
            'by_column': {}
        }

        # 逐列統計缺失數據
        for col in df.columns:
            col_completeness = 1 - (df[col].isnull().sum() / len(df))
            completeness_report['by_column'][col] = {
                'completeness': col_completeness,
                'missing_count': df[col].isnull().sum()
            }

        logger.info(f"數據完整性檢查完成 - 完整性: {completeness:.2%}")
        return completeness_report

    def generate_validation_report(self, df: pd.DataFrame,
                                  rules: List[ValidationRule]) -> str:
        """
        生成驗證報告

        Args:
            df: 輸入 DataFrame
            rules: 驗證規則

        Returns:
            報告字符串
        """
        report = []
        report.append("=" * 70)
        report.append("數據驗證報告")
        report.append("=" * 70)
        report.append(f"時間: {datetime.now().isoformat()}")
        report.append(f"數據行數: {len(df)}")
        report.append(f"數據列數: {len(df.columns)}")
        report.append("")

        # Schema 驗證
        schema_result = self.validate_schema(df, rules)
        report.append("Schema 驗證結果:")
        report.append(f"  是否有效: {schema_result.is_valid}")
        report.append(f"  有效行數: {schema_result.valid_rows}/{schema_result.total_rows}")
        if schema_result.errors:
            report.append("  錯誤:")
            for error in schema_result.errors:
                report.append(f"    - {error}")
        if schema_result.warnings:
            report.append("  警告:")
            for warning in schema_result.warnings:
                report.append(f"    - {warning}")
        report.append("")

        # 完整性檢查
        completeness = self.validate_data_completeness(df)
        report.append("數據完整性:")
        report.append(f"  完整性比例: {completeness['completeness']:.2%}")
        report.append(f"  缺失單元格: {completeness['missing_cells']}")
        report.append("")

        # 異常值檢測
        outliers = self.detect_outliers(df)
        if outliers:
            report.append("異常值檢測結果:")
            for col, details in outliers.items():
                if details['count'] > 0:
                    report.append(f"  列 '{col}': {details['count']} 個異常值 ({details['percentage']:.2f}%)")
        report.append("")

        report.append("=" * 70)
        return "\n".join(report)
