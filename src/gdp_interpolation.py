"""
GDP数据插值和验证模块

提供GDP数据的季度到日度插值功能，以及数据验证和标准化

Author: Claude Code
Version: 1.0.0
Date: 2025-11-10
"""

import logging
import numpy as np
import pandas as pd
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from src.data_adapters.gdp_adapter import GDPDataSet, GDPDataPoint, GDPIndicator, GDPFrequency


class GDPDataInterpolator:
    """
    GDP数据插值器

    将季度或年度GDP数据插值为日度数据，用于回测
    """

    def __init__(self, interpolation_method: str = "linear"):
        """
        初始化插值器

        Args:
            interpolation_method: 插值方法 ("linear", "spline", "cubic")
        """
        self.interpolation_method = interpolation_method
        self.logger = logging.getLogger("hk_quant_system.gdp_interpolation")

    def interpolate_to_daily(
        self,
        dataset: GDPDataSet,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        fill_forward: bool = True
    ) -> pd.DataFrame:
        """
        将季度数据插值为日度数据

        Args:
            dataset: GDP数据集
            start_date: 开始日期
            end_date: 结束日期
            fill_forward: 是否向前填充

        Returns:
            插值后的日度DataFrame
        """
        if not dataset.data_points:
            self.logger.warning("Empty dataset, returning empty DataFrame")
            return pd.DataFrame()

        # 转换为DataFrame
        df = self._dataset_to_dataframe(dataset)

        # 设置日期索引
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)

        # 过滤日期范围
        if start_date:
            df = df[df.index >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df.index <= pd.to_datetime(end_date)]

        # 重新采样到日度
        df_daily = df.resample('D').asfreq()

        # 插值填充
        if fill_forward:
            df_daily = df_daily.ffill()

        # 应用插值方法
        df_interpolated = self._apply_interpolation(df_daily)

        # 重置索引
        df_interpolated.reset_index(inplace=True)
        df_interpolated['date'] = df_interpolated['date'].dt.date

        return df_interpolated

    def _dataset_to_dataframe(self, dataset: GDPDataSet) -> pd.DataFrame:
        """将数据集转换为DataFrame"""
        data = []
        for dp in dataset.data_points:
            data.append({
                'date': dp.date,
                'value': float(dp.value),
                'unit': dp.unit,
                'currency': dp.currency,
                'real_adjusted': dp.real_adj,
                'source': dp.source,
                'is_mock': dp.is_mock
            })

        df = pd.DataFrame(data)
        df.sort_values('date', inplace=True)
        return df

    def _apply_interpolation(self, df: pd.DataFrame) -> pd.DataFrame:
        """应用插值方法"""
        if df.empty:
            return df

        # 获取数值列（排除日期）
        value_columns = ['value']

        for col in value_columns:
            if col in df.columns:
                if self.interpolation_method == "linear":
                    df[col] = df[col].interpolate(method='linear')
                elif self.interpolation_method == "spline":
                    df[col] = df[col].interpolate(method='spline', order=3)
                elif self.interpolation_method == "cubic":
                    df[col] = df[col].interpolate(method='cubic')
                else:
                    # 默认使用线性插值
                    df[col] = df[col].interpolate(method='linear')

        return df

    def interpolate_multiple_indicators(
        self,
        datasets: Dict[GDPIndicator, GDPDataSet],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """
        插值多个GDP指标

        Args:
            datasets: 指标数据集字典
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            合并后的日度DataFrame
        """
        if not datasets:
            return pd.DataFrame()

        interpolated_dfs = []

        for indicator, dataset in datasets.items():
            df = self.interpolate_to_daily(dataset, start_date, end_date)
            if not df.empty:
                df['indicator'] = indicator.value
                interpolated_dfs.append(df)

        if not interpolated_dfs:
            return pd.DataFrame()

        # 合并所有指标
        result = pd.concat(interpolated_dfs, ignore_index=True)
        result.sort_values(['date', 'indicator'], inplace=True)

        return result

    def validate_interpolation_quality(
        self,
        original_df: pd.DataFrame,
        interpolated_df: pd.DataFrame,
        threshold: float = 0.05
    ) -> Dict[str, float]:
        """
        验证插值质量

        Args:
            original_df: 原始数据
            interpolated_df: 插值后数据
            threshold: 质量阈值

        Returns:
            质量指标
        """
        if original_df.empty or interpolated_df.empty:
            return {"quality_score": 0.0}

        # 计算原始数据点保留率
        original_dates = set(pd.to_datetime(original_df['date']))
        interpolated_dates = set(pd.to_datetime(interpolated_df['date']))

        # 原始日期应该在插值后数据中存在
        retention_rate = len(original_dates & interpolated_dates) / len(original_dates)

        # 计算数值差异
        value_changes = []
        original_df_sorted = original_df.sort_values('date')
        interpolated_df_sorted = interpolated_df.sort_values('date')

        for _, row in original_df_sorted.iterrows():
            # 找到插值后数据中对应的日期
            matching_rows = interpolated_df_sorted[
                interpolated_df_sorted['date'] == row['date']
            ]
            if not matching_rows.empty:
                original_value = row['value']
                interpolated_value = matching_rows.iloc[0]['value']
                if original_value != 0:
                    change_rate = abs(interpolated_value - original_value) / abs(original_value)
                    value_changes.append(change_rate)

        avg_change_rate = np.mean(value_changes) if value_changes else 0.0

        # 质量评分
        quality_score = 1.0
        if retention_rate < 1.0:
            quality_score -= 0.3 * (1.0 - retention_rate)
        if avg_change_rate > threshold:
            quality_score -= 0.4 * (avg_change_rate / threshold)

        quality_score = max(0.0, min(1.0, quality_score))

        return {
            "retention_rate": retention_rate,
            "avg_change_rate": avg_change_rate,
            "quality_score": quality_score,
            "threshold": threshold
        }


class GDPDataValidator:
    """
    GDP数据验证器

    验证GDP数据的真实性和质量
    """

    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.gdp_validator")
        # 允许的政府域名
        self.allowed_domains = [
            "censtatd.gov.hk",
            "gov.hk",
            "hkma.gov.hk"
        ]
        # 模拟数据检测关键词
        self.mock_indicators = [
            "mock",
            "sample",
            "test",
            "example",
            "demo"
        ]

    def validate_government_domain(self, source: str) -> Tuple[bool, str]:
        """
        验证数据源是否为政府域名

        Args:
            source: 数据源

        Returns:
            (是否有效, 错误信息)
        """
        if not source:
            return False, "Empty source"

        source_lower = source.lower()

        # 检查是否包含允许的域名
        for domain in self.allowed_domains:
            if domain in source_lower:
                return True, "Valid government domain"

        return False, f"Source not from verified government domain: {source}"

    def detect_mock_data(self, data_point: Dict) -> Tuple[bool, str]:
        """
        检测是否为模拟数据

        Args:
            data_point: 数据点

        Returns:
            (是否为模拟, 检测信息)
        """
        # 检查数据源
        source = data_point.get('source', '')
        source_lower = source.lower()

        for mock_word in self.mock_indicators:
            if mock_word in source_lower:
                return True, f"Mock data detected in source: {mock_word}"

        # 检查is_mock标志
        if data_point.get('is_mock', False):
            return True, "Marked as mock data"

        # 检查数值模式（太完美或太规律）
        value = data_point.get('value', 0)
        if isinstance(value, (int, float)):
            if self._is_suspiciously_perfect(value):
                return True, "Suspiciously perfect values"

        return False, "No mock data detected"

    def _is_suspiciously_perfect(self, value: float) -> bool:
        """检测是否过于完美（可能是模拟数据）"""
        # 检查是否全是整数（可能表明是模拟数据）
        if value == int(value):
            # 如果值太大且是整数，可能可疑
            if value > 1000000 and value % 1000 == 0:
                return True

        return False

    def validate_data_ranges(self, data_point: Dict) -> Tuple[bool, List[str]]:
        """
        验证数据范围

        Args:
            data_point: 数据点

        Returns:
            (是否有效, 错误列表)
        """
        errors = []
        value = data_point.get('value')
        indicator = data_point.get('indicator', '')

        if value is None:
            errors.append("Missing value")
            return False, errors

        # 转换为数值
        if isinstance(value, str):
            try:
                value = float(value)
            except (ValueError, TypeError):
                errors.append(f"Invalid value format: {value}")
                return False, errors

        # 验证不同指标的范围
        if indicator == 'gdp_nominal' or indicator == 'gdp_real':
            # GDP应该为正数
            if value <= 0:
                errors.append(f"GDP value must be positive: {value}")
            # GDP应该在合理范围内（0.1万亿美元到10万亿美元）
            if value > 10000000:  # 100万亿
                errors.append(f"GDP value too large: {value}")

        elif 'growth' in indicator:
            # 增长率应该在-20%到30%之间
            if value < -20 or value > 30:
                errors.append(f"Growth rate out of range: {value}%")

        elif 'sector' in indicator:
            # 部门占比应该在0到100之间
            if value < 0 or value > 100:
                errors.append(f"Sector percentage out of range: {value}%")

        elif 'per_capita' in indicator:
            # 人均GDP应该为正
            if value <= 0:
                errors.append(f"Per capita GDP must be positive: {value}")

        is_valid = len(errors) == 0
        return is_valid, errors

    def validate_sector_sums(self, data_points: List[Dict]) -> Tuple[bool, List[str]]:
        """
        验证部门GDP总和

        Args:
            data_points: 数据点列表

        Returns:
            (是否有效, 错误列表)
        """
        errors = []

        # 找到同一日期的部门数据
        sector_indicators = {
            'gdp_primary': None,
            'gdp_secondary': None,
            'gdp_tertiary': None
        }

        # 按日期分组
        by_date = {}
        for dp in data_points:
            if 'sector' in dp.get('indicator', ''):
                date_str = str(dp.get('date'))
                if date_str not in by_date:
                    by_date[date_str] = []
                by_date[date_str].append(dp)

        # 验证每日的部门总和
        for date_str, dps in by_date.items():
            sector_sum = 0.0
            found_sectors = []

            for dp in dps:
                indicator = dp.get('indicator')
                if indicator in sector_indicators:
                    try:
                        value = float(dp.get('value', 0))
                        sector_sum += value
                        found_sectors.append(indicator)
                    except (ValueError, TypeError):
                        continue

            # 检查总和是否接近100%
            if len(found_sectors) > 1:
                if sector_sum < 95 or sector_sum > 105:
                    errors.append(
                        f"Date {date_str}: Sector sum ({sector_sum:.1f}%) not close to 100% "
                        f"for sectors: {found_sectors}"
                    )

        is_valid = len(errors) == 0
        return is_valid, errors

    def validate_data_freshness(
        self,
        data_point: Dict,
        max_age_days: int = 90
    ) -> Tuple[bool, str]:
        """
        验证数据新鲜度

        Args:
            data_point: 数据点
            max_age_days: 最大数据年龄（天）

        Returns:
            (是否新鲜, 消息)
        """
        date_str = data_point.get('date')
        if not date_str:
            return False, "Missing date"

        try:
            if isinstance(date_str, str):
                parsed_date = pd.to_datetime(date_str).date()
            else:
                parsed_date = date_str

            today = date.today()
            age_days = (today - parsed_date).days

            if age_days > max_age_days:
                return False, f"Data is {age_days} days old, exceeds max age of {max_age_days} days"

            return True, f"Data is fresh (age: {age_days} days)"

        except Exception as e:
            return False, f"Error parsing date: {e}"

    def validate_comprehensive(
        self,
        data_points: List[Dict],
        max_age_days: int = 90
    ) -> Dict[str, any]:
        """
        综合验证

        Args:
            data_points: 数据点列表
            max_age_days: 最大数据年龄

        Returns:
            验证结果
        """
        results = {
            "is_valid": True,
            "total_records": len(data_points),
            "errors": [],
            "warnings": [],
            "summary": {}
        }

        if not data_points:
            results["is_valid"] = False
            results["errors"].append("No data points to validate")
            return results

        # 统计信息
        mock_count = 0
        invalid_domain_count = 0
        out_of_range_count = 0
        stale_data_count = 0

        # 验证每个数据点
        for idx, dp in enumerate(data_points):
            # 验证政府域名
            is_valid_domain, domain_msg = self.validate_government_domain(dp.get('source', ''))
            if not is_valid_domain:
                invalid_domain_count += 1
                results["errors"].append(f"Record {idx}: {domain_msg}")

            # 检测模拟数据
            is_mock, mock_msg = self.detect_mock_data(dp)
            if is_mock:
                mock_count += 1
                results["warnings"].append(f"Record {idx}: {mock_msg}")

            # 验证数据范围
            is_valid_range, range_errors = self.validate_data_ranges(dp)
            if not is_valid_range:
                out_of_range_count += 1
                results["errors"].extend([f"Record {idx}: {err}" for err in range_errors])

            # 验证数据新鲜度
            is_fresh, freshness_msg = self.validate_data_freshness(dp, max_age_days)
            if not is_fresh:
                stale_data_count += 1
                results["warnings"].append(f"Record {idx}: {freshness_msg}")

        # 验证部门总和
        is_valid_sum, sum_errors = self.validate_sector_sums(data_points)
        if not is_valid_sum:
            results["errors"].extend(sum_errors)

        # 总结
        results["summary"] = {
            "mock_data_count": mock_count,
            "invalid_domain_count": invalid_domain_count,
            "out_of_range_count": out_of_range_count,
            "stale_data_count": stale_data_count,
            "valid_percentage": (
                (len(data_points) - len(results["errors"])) / len(data_points) * 100
            )
        }

        # 总体有效性
        if results["errors"]:
            results["is_valid"] = False

        return results


# 便捷函数
def interpolate_gdp_data(
    dataset: GDPDataSet,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    method: str = "linear"
) -> pd.DataFrame:
    """
    便捷函数：插值GDP数据

    Args:
        dataset: GDP数据集
        start_date: 开始日期
        end_date: 结束日期
        method: 插值方法

    Returns:
        插值后的DataFrame
    """
    interpolator = GDPDataInterpolator(method)
    return interpolator.interpolate_to_daily(dataset, start_date, end_date)


def validate_gdp_data(
    data_points: List[Dict],
    max_age_days: int = 90
) -> Dict[str, any]:
    """
    便捷函数：验证GDP数据

    Args:
        data_points: 数据点列表
        max_age_days: 最大数据年龄

    Returns:
        验证结果
    """
    validator = GDPDataValidator()
    return validator.validate_comprehensive(data_points, max_age_days)


def normalize_gdp_data(
    dataset: GDPDataSet
) -> GDPDataSet:
    """
    便捷函数：标准化GDP数据

    Args:
        dataset: 原始数据集

    Returns:
        标准化后的数据集
    """
    from src.data_adapters.gdp_adapter import GDPAdapter

    adapter = GDPAdapter()
    try:
        loop = adapter.get_event_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # 如果在事件循环中，使用异步
        import asyncio
        return loop.run_until_complete(adapter.normalize_gdp_data(dataset))
    else:
        # 否则同步执行
        import asyncio
        return asyncio.run(adapter.normalize_gdp_data(dataset))
