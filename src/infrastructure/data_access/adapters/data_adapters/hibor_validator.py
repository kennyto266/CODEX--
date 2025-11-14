"""
HIBOR数据验证器
验证HIBOR利率数据的准确性、完整性和一致性

功能:
- 数值范围验证
- 日期有效性检查
- 数据完整性验证
- 异常值检测
- 数据一致性验证
- 趋势合理性检查
"""

import logging
import numpy as np
import pandas as pd
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """验证结果严重级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """验证问题数据类"""
    severity: ValidationSeverity
    field: str
    message: str
    value: Any
    expected: Optional[Any] = None
    row_index: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'severity': self.severity.value,
            'field': self.field,
            'message': self.message,
            'value': str(self.value),
            'expected': str(self.expected) if self.expected else None,
            'row_index': self.row_index
        }


@dataclass
class ValidationResult:
    """验证结果数据类"""
    is_valid: bool
    total_issues: int
    issues: List[ValidationIssue]
    valid_count: int
    invalid_count: int
    warning_count: int

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'is_valid': self.is_valid,
            'total_issues': self.total_issues,
            'valid_count': self.valid_count,
            'invalid_count': self.invalid_count,
            'warning_count': self.warning_count,
            'issues': [issue.to_dict() for issue in self.issues]
        }


class HibiorDataValidator:
    """HIBOR数据验证器"""

    # HIBOR利率合理范围 (百分比)
    HIBOR_RANGES = {
        'overnight': {'min': 0.0, 'max': 50.0, 'typical': (0.1, 5.0)},
        '1w': {'min': 0.0, 'max': 50.0, 'typical': (0.1, 5.0)},
        '1m': {'min': 0.0, 'max': 50.0, 'typical': (0.1, 6.0)},
        '3m': {'min': 0.0, 'max': 50.0, 'typical': (0.2, 7.0)},
        '6m': {'min': 0.0, 'max': 50.0, 'typical': (0.3, 8.0)},
        '12m': {'min': 0.0, 'max': 50.0, 'typical': (0.5, 10.0)}
    }

    # 单日最大变化范围 (百分点)
    MAX_DAILY_CHANGE = {
        'overnight': 5.0,
        '1w': 3.0,
        '1m': 2.0,
        '3m': 1.5,
        '6m': 1.0,
        '12m': 0.8
    }

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化HIBOR数据验证器

        Args:
            config: 配置字典，包含验证规则参数
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # 从配置中读取参数
        self.strict_mode = self.config.get('strict_mode', False)
        self.check_trends = self.config.get('check_trends', True)
        self.outlier_threshold = self.config.get('outlier_threshold', 3.0)  # 标准差倍数

    def validate_hibor_data(
        self,
        data: Union[pd.DataFrame, Dict, List],
        term: Optional[str] = None
    ) -> ValidationResult:
        """
        验证HIBOR数据

        Args:
            data: 要验证的数据
            term: HIBOR期限（'overnight', '1m', '3m', '6m', '12m'）

        Returns:
            ValidationResult验证结果
        """
        self.logger.info(f"开始验证HIBOR数据，期限: {term}")

        # 转换为DataFrame
        df = self._to_dataframe(data)

        if df is None or df.empty:
            return ValidationResult(
                is_valid=False,
                total_issues=1,
                issues=[
                    ValidationIssue(
                        severity=ValidationSeverity.CRITICAL,
                        field="data",
                        message="数据为空或无法解析",
                        value=None
                    )
                ],
                valid_count=0,
                invalid_count=0,
                warning_count=0
            )

        issues: List[ValidationIssue] = []
        invalid_count = 0
        warning_count = 0

        # 1. 验证日期字段
        date_issues = self._validate_dates(df)
        issues.extend(date_issues)
        warning_count += sum(1 for i in date_issues if i.severity == ValidationSeverity.WARNING)
        invalid_count += sum(1 for i in date_issues if i.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL])

        # 2. 验证数值字段
        rate_issues = self._validate_rates(df, term)
        issues.extend(rate_issues)
        warning_count += sum(1 for i in rate_issues if i.severity == ValidationSeverity.WARNING)
        invalid_count += sum(1 for i in rate_issues if i.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL])

        # 3. 验证数据完整性
        completeness_issues = self._validate_completeness(df)
        issues.extend(completeness_issues)
        warning_count += sum(1 for i in completeness_issues if i.severity == ValidationSeverity.WARNING)
        invalid_count += sum(1 for i in completeness_issues if i.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL])

        # 4. 验证异常值
        outlier_issues = self._validate_outliers(df, term)
        issues.extend(outlier_issues)
        warning_count += sum(1 for i in outlier_issues if i.severity == ValidationSeverity.WARNING)
        invalid_count += sum(1 for i in outlier_issues if i.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL])

        # 5. 验证趋势合理性
        if self.check_trends and len(df) > 1:
            trend_issues = self._validate_trends(df, term)
            issues.extend(trend_issues)
            warning_count += sum(1 for i in trend_issues if i.severity == ValidationSeverity.WARNING)
            invalid_count += sum(1 for i in trend_issues if i.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL])

        # 6. 验证数据顺序
        order_issues = self._validate_data_order(df)
        issues.extend(order_issues)
        warning_count += sum(1 for i in order_issues if i.severity == ValidationSeverity.WARNING)
        invalid_count += sum(1 for i in order_issues if i.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL])

        # 统计结果
        total_issues = len(issues)
        is_valid = invalid_count == 0 and (not self.strict_mode or warning_count == 0)

        result = ValidationResult(
            is_valid=is_valid,
            total_issues=total_issues,
            issues=issues,
            valid_count=len(df) - invalid_count,
            invalid_count=invalid_count,
            warning_count=warning_count
        )

        self.logger.info(
            f"验证完成: 有效={result.valid_count}, "
            f"无效={result.invalid_count}, "
            f"警告={result.warning_count}"
        )

        return result

    def _to_dataframe(self, data: Union[pd.DataFrame, Dict, List]) -> Optional[pd.DataFrame]:
        """将数据转换为DataFrame"""
        try:
            if isinstance(data, pd.DataFrame):
                return data.copy()
            elif isinstance(data, dict):
                if 'data' in data:
                    return pd.DataFrame(data['data'])
                else:
                    return pd.DataFrame([data])
            elif isinstance(data, list):
                return pd.DataFrame(data)
            else:
                self.logger.error(f"不支持的数据类型: {type(data)}")
                return None
        except Exception as e:
            self.logger.error(f"数据转换错误: {e}")
            return None

    def _validate_dates(self, df: pd.DataFrame) -> List[ValidationIssue]:
        """验证日期字段"""
        issues: List[ValidationIssue] = []

        # 查找日期列
        date_columns = [col for col in df.columns if 'date' in col.lower()]

        if not date_columns:
            return [
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    field="date",
                    message="未找到日期列",
                    value=None
                )
            ]

        date_col = date_columns[0]

        for idx, row in df.iterrows():
            date_val = row.get(date_col)

            if pd.isna(date_val):
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.CRITICAL,
                        field=date_col,
                        message="日期值缺失",
                        value=None,
                        row_index=idx
                    )
                )
                continue

            try:
                # 转换为日期对象
                if isinstance(date_val, str):
                    date_obj = pd.to_datetime(date_val).date()
                elif isinstance(date_val, (date, datetime)):
                    date_obj = date_val.date() if isinstance(date_val, datetime) else date_val
                else:
                    raise ValueError(f"不支持的日期类型: {type(date_val)}")

                # 检查日期是否合理
                if date_obj > date.today() + timedelta(days=1):
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            field=date_col,
                            message="日期在未来",
                            value=date_obj,
                            expected=f"<= {date.today()}",
                            row_index=idx
                        )
                    )

                if date_obj < date(1980, 1, 1):
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            field=date_col,
                            message="日期过早",
                            value=date_obj,
                            expected=">= 1980-01-01",
                            row_index=idx
                        )
                    )

            except (ValueError, TypeError) as e:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.CRITICAL,
                        field=date_col,
                        message=f"日期解析错误: {e}",
                        value=date_val,
                        row_index=idx
                    )
                )

        return issues

    def _validate_rates(self, df: pd.DataFrame, term: Optional[str]) -> List[ValidationIssue]:
        """验证利率数值"""
        issues: List[ValidationIssue] = []

        # 查找利率列
        rate_columns = [col for col in df.columns if 'rate' in col.lower() or 'hibor' in col.lower()]

        if not rate_columns:
            return [
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    field="rate",
                    message="未找到利率列",
                    value=None
                )
            ]

        rate_col = rate_columns[0]
        valid_range = self.HIBOR_RANGES.get(term, self.HIBOR_RANGES['overnight'])

        for idx, row in df.iterrows():
            rate_val = row.get(rate_col)

            if pd.isna(rate_val):
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.CRITICAL,
                        field=rate_col,
                        message="利率值缺失",
                        value=None,
                        row_index=idx
                    )
                )
                continue

            try:
                # 转换为浮点数
                if isinstance(rate_val, str):
                    rate_num = float(rate_val.replace('%', '').strip())
                else:
                    rate_num = float(rate_val)

                # 检查是否在绝对范围内
                if rate_num < valid_range['min'] or rate_num > valid_range['max']:
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            field=rate_col,
                            message=f"利率超出绝对范围 [{valid_range['min']}%, {valid_range['max']}%]",
                            value=rate_num,
                            expected=f"[{valid_range['min']}, {valid_range['max']}]",
                            row_index=idx
                        )
                    )

                # 检查是否在典型范围内
                if self.strict_mode:
                    typical_min, typical_max = valid_range['typical']
                    if rate_num < typical_min or rate_num > typical_max:
                        issues.append(
                            ValidationIssue(
                                severity=ValidationSeverity.WARNING,
                                field=rate_col,
                                message=f"利率超出典型范围 [{typical_min}%, {typical_max}%]",
                                value=rate_num,
                                expected=f"[{typical_min}, {typical_max}]",
                                row_index=idx
                            )
                        )

            except (ValueError, TypeError) as e:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.CRITICAL,
                        field=rate_col,
                        message=f"利率解析错误: {e}",
                        value=rate_val,
                        row_index=idx
                    )
                )

        return issues

    def _validate_completeness(self, df: pd.DataFrame) -> List[ValidationIssue]:
        """验证数据完整性"""
        issues: List[ValidationIssue] = []

        # 检查是否有重复日期
        if 'date' in df.columns:
            duplicates = df['date'].duplicated().sum()
            if duplicates > 0:
                severity = ValidationSeverity.ERROR if self.strict_mode else ValidationSeverity.WARNING
                issues.append(
                    ValidationIssue(
                        severity=severity,
                        field="date",
                        message=f"发现 {duplicates} 个重复日期",
                        value=duplicates,
                        expected=0
                    )
                )

        # 检查数据连续性（工作日）
        if len(df) > 1 and 'date' in df.columns:
            df_sorted = df.sort_values('date')
            date_gaps = df_sorted['date'].diff().dt.days

            # 找出超过5天的跳跃
            large_gaps = date_gaps[date_gaps > 5]
            if len(large_gaps) > 0:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        field="date",
                        message=f"发现 {len(large_gaps)} 个超过5天的数据跳跃",
                        value=len(large_gaps),
                        expected="<= 5天"
                    )
                )

        return issues

    def _validate_outliers(self, df: pd.DataFrame, term: Optional[str]) -> List[ValidationIssue]:
        """验证异常值"""
        issues: List[ValidationIssue] = []

        # 查找利率列
        rate_columns = [col for col in df.columns if 'rate' in col.lower()]

        if not rate_columns:
            return []

        rate_col = rate_columns[0]
        rates = df[rate_col].dropna()

        if len(rates) < 3:
            return []  # 数据点太少，无法检测异常值

        # 使用Z-Score检测异常值
        mean_rate = rates.mean()
        std_rate = rates.std()

        if std_rate == 0:
            return []  # 所有值相同，不是异常

        z_scores = np.abs((rates - mean_rate) / std_rate)
        outliers = df[z_scores > self.outlier_threshold]

        for idx, row in outliers.iterrows():
            rate_val = row[rate_col]
            z_score = z_scores.loc[idx]

            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field=rate_col,
                    message=f"检测到异常值 (Z-Score: {z_score:.2f})",
                    value=rate_val,
                    expected=f"±{self.outlier_threshold}标准差内",
                    row_index=idx
                )
            )

        return issues

    def _validate_trends(self, df: pd.DataFrame, term: Optional[str]) -> List[ValidationIssue]:
        """验证趋势合理性"""
        issues: List[ValidationIssue] = []

        if len(df) < 2:
            return []

        # 查找利率列
        rate_columns = [col for col in df.columns if 'rate' in col.lower()]

        if not rate_columns:
            return []

        rate_col = rate_columns[0]
        df_sorted = df.sort_values('date')

        # 检查日变化是否过大
        max_change = self.MAX_DAILY_CHANGE.get(term, self.MAX_DAILY_CHANGE['overnight'])
        rates = pd.to_numeric(df_sorted[rate_col], errors='coerce').dropna()
        dates = df_sorted.loc[rates.index, 'date']

        daily_changes = rates.diff().abs()
        excessive_changes = daily_changes[daily_changes > max_change]

        for idx, change in excessive_changes.items():
            row_idx = df_sorted.index.get_loc(idx)
            if row_idx > 0:
                prev_rate = df_sorted[rate_col].iloc[row_idx - 1]
                curr_rate = df_sorted[rate_col].iloc[row_idx]
                change_pct = (curr_rate - prev_rate) / prev_rate * 100 if prev_rate != 0 else 0

                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        field=rate_col,
                        message=f"日变化过大: {change_pct:.2f}%",
                        value=change,
                        expected=f"<= {max_change}%",
                        row_index=idx
                    )
                )

        return issues

    def _validate_data_order(self, df: pd.DataFrame) -> List[ValidationIssue]:
        """验证数据顺序"""
        issues: List[ValidationIssue] = []

        if len(df) < 2:
            return []

        # 检查日期是否按升序排列
        if 'date' in df.columns:
            date_col = pd.to_datetime(df['date'], errors='coerce')
            if not date_col.is_monotonic_increasing:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        field="date",
                        message="日期未按升序排列",
                        value="无序",
                        expected="升序"
                    )
                )

        return issues

    def validate_single_value(
        self,
        rate: float,
        term: Optional[str] = None,
        check_range: bool = True
    ) -> bool:
        """
        验证单个HIBOR值

        Args:
            rate: HIBOR利率值
            term: HIBOR期限
            check_range: 是否检查数值范围

        Returns:
            是否有效
        """
        if pd.isna(rate) or rate is None:
            return False

        try:
            rate_num = float(rate)

            if check_range:
                valid_range = self.HIBOR_RANGES.get(term, self.HIBOR_RANGES['overnight'])
                return valid_range['min'] <= rate_num <= valid_range['max']

            return True
        except (ValueError, TypeError):
            return False

    def get_validation_report(self, result: ValidationResult) -> str:
        """
        生成验证报告

        Args:
            result: 验证结果

        Returns:
            格式化的验证报告
        """
        report = []
        report.append("=" * 60)
        report.append("HIBOR数据验证报告")
        report.append("=" * 60)
        report.append(f"验证状态: {'✓ 通过' if result.is_valid else '✗ 失败'}")
        report.append(f"有效记录: {result.valid_count}")
        report.append(f"无效记录: {result.invalid_count}")
        report.append(f"警告数量: {result.warning_count}")
        report.append(f"总问题数: {result.total_issues}")
        report.append("")

        if result.issues:
            report.append("详细问题:")
            report.append("-" * 60)

            for issue in result.issues:
                report.append(
                    f"[{issue.severity.value.upper()}] {issue.field}: {issue.message}"
                )
                if issue.value is not None:
                    report.append(f"  实际值: {issue.value}")
                if issue.expected is not None:
                    report.append(f"  期望值: {issue.expected}")
                if issue.row_index is not None:
                    report.append(f"  行号: {issue.row_index}")
                report.append("")

        return "\n".join(report)


# 便捷函数
def validate_hibor(
    data: Union[pd.DataFrame, Dict, List],
    term: Optional[str] = None,
    config: Optional[Dict] = None
) -> ValidationResult:
    """
    验证HIBOR数据的便捷函数

    Args:
        data: 要验证的数据
        term: HIBOR期限
        config: 配置参数

    Returns:
        ValidationResult验证结果
    """
    validator = HibiorDataValidator(config)
    return validator.validate_hibor_data(data, term)


if __name__ == "__main__":
    # 测试代码
    import asyncio

    # 创建测试数据
    test_data = pd.DataFrame({
        'date': pd.date_range('2023-01-01', periods=10, freq='D'),
        'rate': [0.5, 0.55, 0.6, 0.65, 0.7, 100.0, 0.75, 0.8, 0.85, 0.9]  # 包含异常值
    })

    # 验证数据
    result = validate_hibor(test_data, term='1m', config={'strict_mode': True})

    # 生成报告
    validator = HibiorDataValidator()
    print(validator.get_validation_report(result))
