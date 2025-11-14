"""
数据验证器
检测和验证非价格数据，识别模拟数据
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Set
from datetime import datetime, date
import re
import logging
from collections import Counter
import statistics


class DataValidator:
    """
    数据验证器
    负责数据质量检查和模拟数据检测
    """

    # 模拟数据检测规则
    MOCK_PATTERNS = {
        'repeating_values': 0.7,  # 重复值比例阈值
        'linear_trend': 0.9,  # 线性趋势阈值
        'perfect_periodicity': 0.95,  # 完美周期性阈值
        'round_numbers': 0.6,  # 整数或整十数比例阈值
        'low_variance': 0.1,  # 低方差阈值
    }

    # 数据源置信度
    SOURCE_CONFIDENCE = {
        'DEMO': 0.0,  # 演示数据
        'SIMULATED': 0.1,  # 模拟数据
        'HKMA_REALISTIC_SIMULATION': 0.3,  # 真实模拟
        'MOCK': 0.0,  # 模拟
        'FAKE': 0.0,  # 虚假数据
        'TEST': 0.0,  # 测试数据
        'SYNTHETIC': 0.2,  # 合成数据
    }

    def __init__(self):
        self.logger = logging.getLogger('nonprice_data.validator')

    async def validate_dataframe(
        self,
        df: pd.DataFrame,
        data_source: str
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        验证DataFrame

        Args:
            df: 要验证的DataFrame
            data_source: 数据源名称

        Returns:
            Tuple[bool, List[str], Dict[str, Any]]: (是否有效, 错误列表, 警告列表)
        """
        errors = []
        warnings = []

        # 1. 检查空值
        null_counts = df.isnull().sum()
        if null_counts.any():
            errors.append(f"Null values found: {null_counts[null_counts > 0].to_dict()}")

        # 2. 检查重复行
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            warnings.append(f"Found {duplicates} duplicate rows")

        # 3. 检查数据类型
        if 'value' in df.columns:
            non_numeric = df[~pd.to_numeric(df['value'], errors='coerce').notna()]
            if len(non_numeric) > 0:
                errors.append(f"Found {len(non_numeric)} non-numeric values in 'value' column")

        # 4. 检查日期范围
        if 'date' in df.columns:
            dates = pd.to_datetime(df['date'], errors='coerce')
            if dates.isnull().any():
                errors.append("Found invalid date formats")
            else:
                date_range = (dates.max() - dates.min()).days
                if date_range > 365 * 5:  # 超过5年
                    warnings.append(f"Data spans {date_range} days (>5 years)")

        # 5. 检查值范围
        if 'value' in df.columns:
            values = pd.to_numeric(df['value'], errors='coerce')
            if values.min() < 0:
                warnings.append(f"Found negative values: min={values.min()}")

            if values.max() > 1e10:
                warnings.append(f"Found extremely large values: max={values.max()}")

        # 6. 检查数据源字段
        if 'source' in df.columns:
            sources = df['source'].unique()
            for source in sources:
                if source in self.SOURCE_CONFIDENCE and self.SOURCE_CONFIDENCE[source] < 0.5:
                    warnings.append(f"Low confidence source detected: {source}")

        # 7. 检查数据点数量
        if len(df) < 10:
            warnings.append(f"Very few data points: {len(df)}")

        return len(errors) == 0, errors, warnings

    async def detect_mock_data(
        self,
        df: pd.DataFrame,
        data_source: str = "unknown"
    ) -> Tuple[bool, float, List[str]]:
        """
        检测模拟数据

        Args:
            df: 要检测的DataFrame
            data_source: 数据源名称

        Returns:
            Tuple[bool, float, List[str]]: (是否为模拟数据, 置信度, 检测到的特征)
        """
        mock_features = []
        confidence_score = 0.0
        total_checks = 0

        if 'value' not in df.columns:
            return False, 0.0, []

        values = pd.to_numeric(df['value'], errors='coerce').dropna()

        # 1. 检查重复值
        total_checks += 1
        value_counts = Counter(values)
        most_common_ratio = value_counts.most_common(1)[0][1] / len(values)
        if most_common_ratio > self.MOCK_PATTERNS['repeating_values']:
            mock_features.append(f"High repetition: {most_common_ratio:.2%} of values are identical")
            confidence_score += 0.3

        # 2. 检查线性趋势
        total_checks += 1
        if len(values) > 10:
            x = np.arange(len(values))
            correlation = np.corrcoef(x, values)[0, 1]
            if not np.isnan(correlation) and abs(correlation) > self.MOCK_PATTERNS['linear_trend']:
                mock_features.append(f"Strong linear trend: correlation={correlation:.3f}")
                confidence_score += 0.2

        # 3. 检查周期性模式
        total_checks += 1
        if len(values) > 30:
            # 计算自相关
            autocorr = self._calculate_autocorrelation(values, lag=7)
            if autocorr > self.MOCK_PATTERNS['perfect_periodicity']:
                mock_features.append(f"Strong periodicity: autocorr={autocorr:.3f}")
                confidence_score += 0.2

        # 4. 检查整数比例
        total_checks += 1
        integer_ratio = sum(1 for v in values if v == int(v)) / len(values)
        round_ratio = sum(1 for v in values if v % 10 == 0) / len(values)
        if integer_ratio > self.MOCK_PATTERNS['round_numbers']:
            mock_features.append(f"High integer ratio: {integer_ratio:.2%}")
            confidence_score += 0.1
        if round_ratio > 0.3:
            mock_features.append(f"Many round numbers: {round_ratio:.2%}")
            confidence_score += 0.1

        # 5. 检查方差
        total_checks += 1
        if len(values) > 1:
            cv = statistics.stdev(values) / abs(statistics.mean(values)) if statistics.mean(values) != 0 else 0
            if cv < self.MOCK_PATTERNS['low_variance']:
                mock_features.append(f"Low coefficient of variation: {cv:.4f}")
                confidence_score += 0.2

        # 6. 检查数据源
        total_checks += 1
        if 'source' in df.columns:
            source = df['source'].iloc[0] if len(df) > 0 else "unknown"
            if source in self.SOURCE_CONFIDENCE:
                if self.SOURCE_CONFIDENCE[source] < 0.5:
                    confidence_score += (1.0 - self.SOURCE_CONFIDENCE[source]) * 0.5
                    mock_features.append(f"Low confidence source: {source}")

        # 7. 检查数据格式特征
        total_checks += 1
        if self._has_synthetic_patterns(df):
            mock_features.append("Synthetic data patterns detected")
            confidence_score += 0.2

        # 计算最终置信度
        final_confidence = min(confidence_score, 1.0)

        # 判断是否为模拟数据
        is_mock = final_confidence > 0.5

        self.logger.info(
            f"Mock data detection: is_mock={is_mock}, confidence={final_confidence:.2%}, "
            f"features={len(mock_features)}"
        )

        return is_mock, final_confidence, mock_features

    def _calculate_autocorrelation(self, values: pd.Series, lag: int) -> float:
        """计算自相关"""
        if len(values) <= lag:
            return 0.0

        mean_val = values.mean()
        numerator = sum((values.iloc[i] - mean_val) * (values.iloc[i - lag] - mean_val)
                       for i in range(lag, len(values)))
        denominator = sum((v - mean_val) ** 2 for v in values)

        return numerator / denominator if denominator != 0 else 0.0

    def _has_synthetic_patterns(self, df: pd.DataFrame) -> bool:
        """检查合成数据模式"""
        # 检查是否包含明显的模拟标识符
        mock_identifiers = [
            'DEMO', 'MOCK', 'SIMULATED', 'FAKE', 'TEST', 'SYNTHETIC',
            'demo', 'mock', 'simulated', 'fake', 'test', 'synthetic'
        ]

        if 'source' in df.columns:
            source = str(df['source'].iloc[0]) if len(df) > 0 else ""
            if any(identifier in source for identifier in mock_identifiers):
                return True

        # 检查值是否过于规整
        if 'value' in df.columns:
            values = pd.to_numeric(df['value'], errors='coerce').dropna()
            if len(values) > 10:
                # 检查是否所有值都是某个基础值的整数倍
                base_value = values.iloc[0] if values.iloc[0] != 0 else 1
                if all(abs(v / base_value - round(v / base_value)) < 0.01 for v in values if v != 0):
                    return True

        return False

    async def get_data_quality_report(
        self,
        df: pd.DataFrame,
        data_source: str
    ) -> Dict[str, Any]:
        """
        生成数据质量报告

        Args:
            df: 要分析的DataFrame
            data_source: 数据源名称

        Returns:
            Dict[str, Any]: 质量报告
        """
        report = {
            'data_source': data_source,
            'total_records': len(df),
            'date_range': {},
            'value_statistics': {},
            'data_quality': {},
            'mock_detection': {}
        }

        # 日期范围
        if 'date' in df.columns:
            dates = pd.to_datetime(df['date'], errors='coerce')
            report['date_range'] = {
                'start': dates.min().isoformat() if not dates.isnull().all() else None,
                'end': dates.max().isoformat() if not dates.isnull().all() else None,
                'span_days': (dates.max() - dates.min()).days if not dates.isnull().all() else 0
            }

        # 值统计
        if 'value' in df.columns:
            values = pd.to_numeric(df['value'], errors='coerce')
            report['value_statistics'] = {
                'min': float(values.min()) if not values.empty else None,
                'max': float(values.max()) if not values.empty else None,
                'mean': float(values.mean()) if not values.empty else None,
                'std': float(values.std()) if not values.empty else None,
                'null_count': int(values.isnull().sum())
            }

        # 数据质量
        is_valid, errors, warnings = await self.validate_dataframe(df, data_source)
        report['data_quality'] = {
            'is_valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'quality_score': max(0, 1.0 - len(errors) * 0.2 - len(warnings) * 0.05)
        }

        # 模拟数据检测
        is_mock, confidence, features = await self.detect_mock_data(df, data_source)
        report['mock_detection'] = {
            'is_mock': is_mock,
            'confidence': confidence,
            'features': features
        }

        return report
