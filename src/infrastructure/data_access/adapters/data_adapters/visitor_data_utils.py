#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
访客数据处理工具
提供访客数据的标准化、验证和模拟数据检测功能

Author: Claude Code
Version: 1.0.0
Date: 2025-11-10
"""

import logging
import re
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd


class VisitorDataNormalizer:
    """访客数据标准化器"""

    # 支持的访客指标映射
    INDICATOR_MAPPING = {
        # visitor_total
        'visitor_total': ['visitor_total', 'total_visitors', 'total', 'visitors', 'visitor_arrivals_total'],
        # visitor_mainland
        'visitor_mainland': ['visitor_mainland', 'mainland_china', 'mainland', 'china', 'visitor_arrivals_mainland'],
        # visitor_growth
        'visitor_growth': ['visitor_growth', 'growth_rate', 'yoy_growth', 'visitor_growth_rate']
    }

    # 数据源域名白名单
    VALID_DOMAINS = [
        'data.gov.hk',
        'www.discoverhongkong.com',
        'immd.gov.hk',
        'www.immd.gov.hk',
        'censtatd.gov.hk',
        'www.censtatd.gov.hk'
    ]

    def __init__(self):
        """初始化标准化器"""
        self.logger = logging.getLogger(__name__)

    def normalize_visitor_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化访客DataFrame

        Args:
            df: 原始访客数据

        Returns:
            DataFrame: 标准化后的数据
        """
        try:
            df_copy = df.copy()

            # 1. 标准化列名
            df_copy = self._standardize_columns(df_copy)

            # 2. 标准化数据类型
            df_copy = self._standardize_dtypes(df_copy)

            # 3. 标准化日期格式
            df_copy = self._standardize_dates(df_copy)

            # 4. 标准化数值
            df_copy = self._standardize_values(df_copy)

            # 5. 标准化数据源
            df_copy = self._standardize_sources(df_copy)

            # 6. 过滤无效行
            df_copy = self._filter_invalid_rows(df_copy)

            # 7. 按日期排序
            df_copy = df_copy.sort_values('date').reset_index(drop=True)

            return df_copy

        except Exception as e:
            self.logger.error(f"Error normalizing visitor dataframe: {e}")
            return df

    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名"""
        df_copy = df.copy()

        # 列名映射
        column_mapping = {
            'Indicator': 'symbol',
            'indicator': 'symbol',
            'Metric': 'symbol',
            'metric': 'symbol',
            'Date': 'date',
            'date': 'date',
            'DateTime': 'date',
            'datetime': 'date',
            'Value': 'value',
            'value': 'value',
            'Count': 'value',
            'count': 'value',
            'Source': 'source',
            'source': 'source',
            'Data_Source': 'source',
            'data_source': 'source'
        }

        # 应用列名映射
        df_copy = df_copy.rename(columns=column_mapping)

        # 检查是否包含必需列
        required_columns = ['symbol', 'date', 'value', 'source']
        missing_columns = [col for col in required_columns if col not in df_copy.columns]

        if missing_columns:
            raise ValueError(f"Missing required columns after standardization: {missing_columns}")

        return df_copy

    def _standardize_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化数据类型"""
        df_copy = df.copy()

        # 标准化日期
        if 'date' in df_copy.columns:
            df_copy['date'] = pd.to_datetime(df_copy['date'], errors='coerce').dt.date

        # 标准化数值
        if 'value' in df_copy.columns:
            df_copy['value'] = pd.to_numeric(df_copy['value'], errors='coerce')

        # 确保字符串类型
        if 'symbol' in df_copy.columns:
            df_copy['symbol'] = df_copy['symbol'].astype(str)

        if 'source' in df_copy.columns:
            df_copy['source'] = df_copy['source'].astype(str)

        return df_copy

    def _standardize_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化日期格式"""
        df_copy = df.copy()

        if 'date' not in df_copy.columns:
            return df_copy

        # 转换日期
        df_copy['date'] = pd.to_datetime(df_copy['date'], errors='coerce').dt.date

        # 验证日期范围
        valid_dates = []
        for idx, date_val in enumerate(df_copy['date']):
            if date_val and date_val <= date.today():
                valid_dates.append(idx)

        df_copy = df_copy.iloc[valid_dates].reset_index(drop=True)

        return df_copy

    def _standardize_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化数值"""
        df_copy = df.copy()

        if 'value' not in df_copy.columns:
            return df_copy

        # 清理数值字符串
        def clean_value(val):
            if pd.isna(val):
                return np.nan

            try:
                # 移除逗号、空格和百分号
                cleaned = str(val).replace(',', '').replace(' ', '').replace('%', '')
                return float(cleaned)
            except (ValueError, TypeError):
                return np.nan

        df_copy['value'] = df_copy['value'].apply(clean_value)

        return df_copy

    def _standardize_sources(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化数据源"""
        df_copy = df.copy()

        if 'source' not in df_copy.columns:
            return df_copy

        # 标准化数据源
        def clean_source(source):
            if pd.isna(source):
                return 'unknown'

            source_str = str(source).strip()

            # 检查是否在白名单中
            for domain in self.VALID_DOMAINS:
                if domain in source_str.lower():
                    return domain

            # 如果不在白名单中，保留原始值但记录警告
            self.logger.warning(f"Unknown data source domain: {source_str}")

            return source_str

        df_copy['source'] = df_copy['source'].apply(clean_source)

        return df_copy

    def _filter_invalid_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """过滤无效行"""
        df_copy = df.copy()

        # 删除包含NaN的行
        df_copy = df_copy.dropna()

        # 删除value为负数的行
        if 'value' in df_copy.columns:
            df_copy = df_copy[df_copy['value'] >= 0]

        # 删除明显异常的值
        if 'value' in df_copy.columns:
            # 使用IQR方法检测异常值
            Q1 = df_copy['value'].quantile(0.25)
            Q3 = df_copy['value'].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            # 保留合理范围内的数据
            df_copy = df_copy[
                (df_copy['value'] >= max(0, lower_bound)) &
                (df_copy['value'] <= upper_bound)
            ]

        return df_copy.reset_index(drop=True)


class VisitorDataValidator:
    """访客数据验证器"""

    def __init__(self):
        """初始化验证器"""
        self.logger = logging.getLogger(__name__)

    async def validate_visitor_data(
        self,
        df: pd.DataFrame,
        min_records: int = 50,
        max_records: int = 10000
    ) -> Tuple[bool, List[str]]:
        """
        验证访客数据

        Args:
            df: 要验证的DataFrame
            min_records: 最小记录数
            max_records: 最大记录数

        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误列表)
        """
        errors = []

        # 1. 检查数据结构
        structure_errors = self._validate_structure(df)
        errors.extend(structure_errors)

        # 2. 检查数据类型
        dtype_errors = self._validate_data_types(df)
        errors.extend(dtype_errors)

        # 3. 检查数据范围
        range_errors = self._validate_data_range(df)
        errors.extend(range_errors)

        # 4. 检查记录数量
        count_errors = self._validate_record_count(df, min_records, max_records)
        errors.extend(count_errors)

        # 5. 检查数据源
        source_errors = self._validate_data_sources(df)
        errors.extend(source_errors)

        return len(errors) == 0, errors

    def _validate_structure(self, df: pd.DataFrame) -> List[str]:
        """验证数据结构"""
        errors = []

        # 检查必需列
        required_columns = ['symbol', 'date', 'value', 'source']
        for col in required_columns:
            if col not in df.columns:
                errors.append(f"Missing required column: {col}")

        return errors

    def _validate_data_types(self, df: pd.DataFrame) -> List[str]:
        """验证数据类型"""
        errors = []

        # 检查date列
        if 'date' in df.columns:
            non_date_count = df['date'].apply(lambda x: not isinstance(x, (date, pd.Timestamp))).sum()
            if non_date_count > 0:
                errors.append(f"Found {non_date_count} invalid date values")

        # 检查value列
        if 'value' in df.columns:
            non_numeric_count = df['value'].apply(lambda x: not isinstance(x, (int, float, np.number))).sum()
            if non_numeric_count > 0:
                errors.append(f"Found {non_numeric_count} invalid numeric values")

        # 检查symbol列
        if 'symbol' in df.columns:
            empty_symbols = (df['symbol'].isna() | (df['symbol'] == '')).sum()
            if empty_symbols > 0:
                errors.append(f"Found {empty_symbols} empty symbol values")

        # 检查source列
        if 'source' in df.columns:
            empty_sources = (df['source'].isna() | (df['source'] == '')).sum()
            if empty_sources > 0:
                errors.append(f"Found {empty_sources} empty source values")

        return errors

    def _validate_data_range(self, df: pd.DataFrame) -> List[str]:
        """验证数据范围"""
        errors = []

        # 检查日期范围
        if 'date' in df.columns and len(df) > 0:
            min_date = df['date'].min()
            max_date = df['date'].max()
            today = date.today()

            if min_date < date(2000, 1, 1):
                errors.append(f"Date range starts too early: {min_date}")

            if max_date > today:
                future_days = (max_date - today).days
                if future_days > 30:
                    errors.append(f"Date range extends too far into future: {max_date} ({future_days} days)")

        # 检查数值范围
        if 'value' in df.columns and len(df) > 0:
            min_value = df['value'].min()
            max_value = df['value'].max()

            # visitor_total 应该在合理范围内
            if 'visitor_total' in df['symbol'].values:
                visitor_total_data = df[df['symbol'] == 'visitor_total']
                if len(visitor_total_data) > 0:
                    vt_min = visitor_total_data['value'].min()
                    vt_max = visitor_total_data['value'].max()

                    if vt_min < 0:
                        errors.append(f"visitor_total has negative values: {vt_min}")

                    if vt_max > 100000000:  # 1亿
                        errors.append(f"visitor_total exceeds maximum: {vt_max}")

            # visitor_growth 应该在合理范围内
            if 'visitor_growth' in df['symbol'].values:
                visitor_growth_data = df[df['symbol'] == 'visitor_growth']
                if len(visitor_growth_data) > 0:
                    vg_min = visitor_growth_data['value'].min()
                    vg_max = visitor_growth_data['value'].max()

                    if vg_min < -100:
                        errors.append(f"visitor_growth below minimum: {vg_min}")

                    if vg_max > 100:
                        errors.append(f"visitor_growth exceeds maximum: {vg_max}")

        return errors

    def _validate_record_count(self, df: pd.DataFrame, min_records: int, max_records: int) -> List[str]:
        """验证记录数量"""
        errors = []

        if len(df) < min_records:
            errors.append(f"Too few records: {len(df)} < {min_records}")

        if len(df) > max_records:
            errors.append(f"Too many records: {len(df)} > {max_records}")

        return errors

    def _validate_data_sources(self, df: pd.DataFrame) -> List[str]:
        """验证数据源"""
        errors = []

        if 'source' not in df.columns:
            return errors

        # 检查数据源域名
        for source in df['source'].unique():
            if pd.isna(source):
                errors.append("Found NaN data source")
                continue

            source_str = str(source).lower()
            is_valid = any(domain in source_str for domain in VisitorDataNormalizer.VALID_DOMAINS)

            if not is_valid:
                errors.append(f"Invalid data source domain: {source}")

        return errors

    def check_government_domain(self, source: str) -> bool:
        """
        检查是否为政府域名

        Args:
            source: 数据源

        Returns:
            bool: 是否为政府域名
        """
        if not source:
            return False

        source_lower = str(source).lower()
        return any(domain in source_lower for domain in VisitorDataNormalizer.VALID_DOMAINS)


class MockDataDetector:
    """模拟数据检测器"""

    def __init__(self):
        """初始化检测器"""
        self.logger = logging.getLogger(__name__)

    async def detect_mock_data(
        self,
        df: pd.DataFrame,
        confidence_threshold: float = 0.7
    ) -> Tuple[bool, float, List[str]]:
        """
        检测模拟数据

        Args:
            df: 要检测的DataFrame
            confidence_threshold: 置信度阈值

        Returns:
            Tuple[bool, float, List[str]]: (是否为模拟数据, 置信度, 检测到的指标)
        """
        if len(df) == 0:
            return False, 0.0, []

        mock_score = 0.0
        detected_issues = []

        # 1. 检查重复值
        repeat_result = self._check_repeating_values(df)
        mock_score += repeat_result['score']
        detected_issues.extend(repeat_result['issues'])

        # 2. 检查线性趋势
        trend_result = self._check_linear_trend(df)
        mock_score += trend_result['score']
        detected_issues.extend(trend_result['issues'])

        # 3. 检查完美周期性
        periodicity_result = self._check_periodicity(df)
        mock_score += periodicity_result['score']
        detected_issues.extend(periodicity_result['issues'])

        # 4. 检查四舍五入数字
        round_result = self._check_round_numbers(df)
        mock_score += round_result['score']
        detected_issues.extend(round_result['issues'])

        # 5. 检查低方差
        variance_result = self._check_low_variance(df)
        mock_score += variance_result['score']
        detected_issues.extend(variance_result['issues'])

        # 6. 检查数据一致性
        consistency_result = self._check_data_consistency(df)
        mock_score += consistency_result['score']
        detected_issues.extend(consistency_result['issues'])

        # 计算最终置信度
        confidence = min(mock_score, 1.0)

        # 判断是否为模拟数据
        is_mock = confidence >= confidence_threshold

        return is_mock, confidence, detected_issues

    def _check_repeating_values(self, df: pd.DataFrame) -> Dict[str, Any]:
        """检查重复值"""
        if 'value' not in df.columns:
            return {'score': 0, 'issues': []}

        values = df['value'].values
        value_counts = pd.Series(values).value_counts()
        max_repeat = value_counts.max() if len(value_counts) > 0 else 0
        repeat_ratio = max_repeat / len(values) if len(values) > 0 else 0

        if repeat_ratio > 0.5:
            return {
                'score': 0.3,
                'issues': [f"High repeat ratio: {repeat_ratio:.2%}"]
            }

        return {'score': 0, 'issues': []}

    def _check_linear_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """检查线性趋势"""
        if 'value' not in df.columns or len(df) < 2:
            return {'score': 0, 'issues': []}

        values = df['value'].values
        x = np.arange(len(values))

        try:
            # 计算与完美直线的偏差
            coeffs = np.polyfit(x, values, 1)
            predicted = np.polyval(coeffs, x)
            mae = np.mean(np.abs(values - predicted))
            max_val = np.max(values) if len(values) > 0 else 1
            linear_error = mae / max_val if max_val > 0 else 0

            if linear_error < 0.01:
                return {
                    'score': 0.3,
                    'issues': [f"Nearly perfect linear trend (error: {linear_error:.4%})"]
                }
        except Exception:
            pass

        return {'score': 0, 'issues': []}

    def _check_periodicity(self, df: pd.DataFrame) -> Dict[str, Any]:
        """检查完美周期性"""
        if 'value' not in df.columns or len(df) < 3:
            return {'score': 0, 'issues': []}

        values = df['value'].values

        # 检查所有值是否相同
        if all(v == values[0] for v in values):
            return {
                'score': 0.4,
                'issues': ['All values are identical (perfect periodicity)']
            }

        return {'score': 0, 'issues': []}

    def _check_round_numbers(self, df: pd.DataFrame) -> Dict[str, Any]:
        """检查四舍五入的数字"""
        if 'value' not in df.columns or len(df) == 0:
            return {'score': 0, 'issues': []}

        values = df['value'].values
        round_count = sum(1 for v in values if v % 10 == 0)
        round_ratio = round_count / len(values)

        if round_ratio > 0.8:
            return {
                'score': 0.1,
                'issues': [f"High round number ratio: {round_ratio:.2%}"]
            }

        return {'score': 0, 'issues': []}

    def _check_low_variance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """检查低方差"""
        if 'value' not in df.columns or len(df) < 2:
            return {'score': 0, 'issues': []}

        values = df['value'].values
        mean_val = np.mean(values)
        std_val = np.std(values)
        cv = std_val / mean_val if mean_val > 0 else 0

        if cv < 0.001:
            return {
                'score': 0.2,
                'issues': [f"Extremely low variance (CV: {cv:.6f})"]
            }

        return {'score': 0, 'issues': []}

    def _check_data_consistency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """检查数据一致性"""
        issues = []
        score = 0

        # 检查访客数量是否合理
        if 'visitor_total' in df['symbol'].values and 'visitor_mainland' in df['symbol'].values:
            total_data = df[df['symbol'] == 'visitor_total'].set_index('date')['value']
            mainland_data = df[df['symbol'] == 'visitor_mainland'].set_index('date')['value']

            # 检查内地访客是否超过总访客
            for date_val in total_data.index:
                if date_val in mainland_data.index:
                    if mainland_data[date_val] > total_data[date_val]:
                        issues.append(f"Mainland visitors exceed total on {date_val}")
                        score += 0.1

        return {'score': score, 'issues': issues}


# 便捷函数
async def normalize_visitor_data(df: pd.DataFrame) -> pd.DataFrame:
    """标准化访客数据"""
    normalizer = VisitorDataNormalizer()
    return normalizer.normalize_visitor_dataframe(df)


async def validate_visitor_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """验证访客数据"""
    validator = VisitorDataValidator()
    return await validator.validate_visitor_data(df)


async def detect_mock_visitor_data(df: pd.DataFrame) -> Tuple[bool, float, List[str]]:
    """检测模拟访客数据"""
    detector = MockDataDetector()
    return await detector.detect_mock_data(df)


if __name__ == '__main__':
    # 测试代码
    import asyncio

    async def test():
        # 创建测试数据
        data = {
            'date': ['2023-01-01', '2023-02-01', '2023-03-01'],
            'visitor_total': [500000, 520000, 480000],
            'source': ['data.gov.hk', 'data.gov.hk', 'data.gov.hk']
        }
        df = pd.DataFrame(data)

        # 标准化
        normalized = await normalize_visitor_data(df)
        print("Normalized data:")
        print(normalized)

        # 验证
        is_valid, errors = await validate_visitor_data(normalized)
        print(f"\nValid: {is_valid}")
        print(f"Errors: {errors}")

        # 检测模拟数据
        is_mock, confidence, issues = await detect_mock_visitor_data(normalized)
        print(f"\nIs mock: {is_mock}")
        print(f"Confidence: {confidence}")
        print(f"Issues: {issues}")

    asyncio.run(test())
