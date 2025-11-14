"""
Phase 8b - T350: 综合数据验证管道
实现多层次自动化数据验证流程
"""

__all__ = [
    "ValidationPipeline",
    "ValidationStage",
    "ValidationResult",
    "ValidationError",
    "StructureValidator",
    "BusinessLogicValidator",
    "DataTypeValidator",
    "CompletenessValidator"
]

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union, Callable, Set
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
import json
import re

from .validator import DataValidationResult

logger = logging.getLogger('quant_system.data.validation_pipeline')


class ValidationStage(Enum):
    """验证阶段枚举"""
    STRUCTURE = "structure"
    DATA_TYPE = "data_type"
    BUSINESS_LOGIC = "business_logic"
    COMPLETENESS = "completeness"
    CONSISTENCY = "consistency"
    QUALITY = "quality"


class ValidationError(Exception):
    """验证错误异常"""
    pass


@dataclass
class ValidationResult:
    """验证结果"""
    stage: ValidationStage
    is_passed: bool
    score: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'stage': self.stage.value,
            'is_passed': self.is_passed,
            'score': self.score,
            'errors': self.errors,
            'warnings': self.warnings,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }


class StructureValidator:
    """结构验证器"""

    def __init__(self):
        self.required_columns = {
            'ohlcv': ['open', 'high', 'low', 'close', 'volume'],
            'timeseries': ['date', 'value'],
            'market_data': ['symbol', 'timestamp', 'price', 'volume']
        }

    def validate(self, data: Union[pd.DataFrame, Dict], schema: str) -> ValidationResult:
        """验证数据结构"""
        errors = []
        warnings = []
        details = {}

        try:
            if isinstance(data, dict):
                data = pd.DataFrame(data)

            if data.empty:
                errors.append("数据为空")
                return ValidationResult(
                    stage=ValidationStage.STRUCTURE,
                    is_passed=False,
                    score=0.0,
                    errors=errors,
                    warnings=warnings,
                    details=details
                )

            # 检查必要列
            required_cols = self.required_columns.get(schema, [])
            if required_cols:
                missing_cols = [col for col in required_cols if col not in data.columns]
                if missing_cols:
                    errors.append(f"缺少必要列: {missing_cols}")

            # 检查列名
            invalid_cols = [col for col in data.columns if not self._is_valid_column_name(col)]
            if invalid_cols:
                warnings.append(f"无效列名: {invalid_cols}")

            # 检查数据类型
            details['row_count'] = len(data)
            details['column_count'] = len(data.columns)
            details['columns'] = list(data.columns)

            # 计算完整性
            if not data.empty:
                completeness = (1 - data.isnull().sum().sum() / (len(data) * len(data.columns))) * 100
                details['completeness'] = completeness

            is_passed = len(errors) == 0
            score = 1.0 if is_passed else max(0.0, 1.0 - len(errors) * 0.2)

        except Exception as e:
            errors.append(f"结构验证异常: {str(e)}")
            is_passed = False
            score = 0.0

        return ValidationResult(
            stage=ValidationStage.STRUCTURE,
            is_passed=is_passed,
            score=score,
            errors=errors,
            warnings=warnings,
            details=details
        )

    def _is_valid_column_name(self, col: str) -> bool:
        """检查列名是否有效"""
        if not isinstance(col, str):
            return False
        if not col.strip():
            return False
        # 列名只允许字母、数字、下划线
        return re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col) is not None


class DataTypeValidator:
    """数据类型验证器"""

    def __init__(self):
        self.type_rules = {
            'price': (float, int),
            'volume': (int,),
            'date': (str, pd.Timestamp, datetime),
            'timestamp': (int, float, str, datetime)
        }

    def validate(self, data: pd.DataFrame, schema: str) -> ValidationResult:
        """验证数据类型"""
        errors = []
        warnings = []
        details = {'type_checks': {}}

        try:
            for column in data.columns:
                column_data = data[column]
                col_check = self._check_column_type(column, column_data)
                details['type_checks'][column] = col_check

                if not col_check['is_valid']:
                    errors.extend(col_check.get('errors', []))
                if col_check.get('warnings'):
                    warnings.extend(col_check['warnings'])

            # 特殊检查
            details.update(self._special_checks(data))

            is_passed = len(errors) == 0
            score = 1.0 if is_passed else max(0.0, 1.0 - len(errors) * 0.1)

        except Exception as e:
            errors.append(f"数据类型验证异常: {str(e)}")
            is_passed = False
            score = 0.0

        return ValidationResult(
            stage=ValidationStage.DATA_TYPE,
            is_passed=is_passed,
            score=score,
            errors=errors,
            warnings=warnings,
            details=details
        )

    def _check_column_type(self, column: str, data: pd.Series) -> Dict[str, Any]:
        """检查列数据类型"""
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }

        # 数值列检查
        if any(keyword in column.lower() for keyword in ['price', 'open', 'high', 'low', 'close']):
            numeric_count = pd.to_numeric(data, errors='coerce').notna().sum()
            if numeric_count < len(data) * 0.8:
                result['is_valid'] = False
                result['errors'].append(f"{column}: 数值格式错误比例过高")

        # 日期列检查
        elif 'date' in column.lower() or 'time' in column.lower():
            try:
                pd.to_datetime(data, errors='raise')
            except:
                result['warnings'].append(f"{column}: 部分日期格式异常")

        return result

    def _special_checks(self, data: pd.DataFrame) -> Dict[str, Any]:
        """特殊检查"""
        checks = {}

        # 检查重复行
        if not data.empty:
            duplicates = data.duplicated().sum()
            checks['duplicate_rows'] = duplicates

        # 检查索引
        if hasattr(data.index, 'duplicated'):
            index_duplicates = data.index.duplicated().sum()
            checks['duplicate_index'] = index_duplicates

        return checks


class BusinessLogicValidator:
    """业务逻辑验证器"""

    def __init__(self):
        self.rules = {
            'ohlcv': [
                self._check_ohlc_logic,
                self._check_volume_logic,
                self._check_price_logic
            ],
            'timeseries': [
                self._check_time_order
            ]
        }

    def validate(self, data: pd.DataFrame, schema: str) -> ValidationResult:
        """验证业务逻辑"""
        errors = []
        warnings = []
        details = {'rule_checks': {}}

        try:
            rules = self.rules.get(schema, [])
            for rule in rules:
                rule_name = rule.__name__
                try:
                    rule_result = rule(data)
                    details['rule_checks'][rule_name] = rule_result

                    if not rule_result.get('is_valid', True):
                        errors.extend(rule_result.get('errors', []))
                    if rule_result.get('warnings'):
                        warnings.extend(rule_result['warnings'])
                except Exception as e:
                    errors.append(f"规则 {rule_name} 执行失败: {str(e)}")

            is_passed = len(errors) == 0
            score = 1.0 if is_passed else max(0.0, 1.0 - len(errors) * 0.15)

        except Exception as e:
            errors.append(f"业务逻辑验证异常: {str(e)}")
            is_passed = False
            score = 0.0

        return ValidationResult(
            stage=ValidationStage.BUSINESS_LOGIC,
            is_passed=is_passed,
            score=score,
            errors=errors,
            warnings=warnings,
            details=details
        )

    def _check_ohlc_logic(self, data: pd.DataFrame) -> Dict[str, Any]:
        """检查OHLC逻辑"""
        errors = []
        warnings = []

        required_cols = ['open', 'high', 'low', 'close']
        if not all(col in data.columns for col in required_cols):
            return {'is_valid': False, 'errors': ['缺少OHLC列'], 'warnings': []}

        # 检查高低价逻辑
        high_low_violations = (data['high'] < data['low']).sum()
        if high_low_violations > 0:
            errors.append(f"高低价逻辑错误: {high_low_violations} 条记录")

        # 检查开收价逻辑
        if 'open' in data.columns and 'close' in data.columns:
            # 开收价可以在高低价之间
            out_of_range = ((data['open'] < data['low']) | (data['open'] > data['high'])).sum()
            if out_of_range > 0:
                warnings.append(f"开盘价越界: {out_of_range} 条记录")

        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def _check_volume_logic(self, data: pd.DataFrame) -> Dict[str, Any]:
        """检查成交量逻辑"""
        errors = []
        warnings = []

        if 'volume' not in data.columns:
            return {'is_valid': True, 'errors': [], 'warnings': []}

        # 检查负成交量
        negative_volume = (data['volume'] < 0).sum()
        if negative_volume > 0:
            errors.append(f"负成交量错误: {negative_volume} 条记录")

        # 检查极值
        if not data.empty:
            q99 = data['volume'].quantile(0.99)
            extreme_volume = (data['volume'] > q99 * 10).sum()
            if extreme_volume > 0:
                warnings.append(f"极值成交量: {extreme_volume} 条记录")

        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def _check_price_logic(self, data: pd.DataFrame) -> Dict[str, Any]:
        """检查价格逻辑"""
        errors = []
        warnings = []

        price_cols = ['open', 'high', 'low', 'close']
        price_cols = [col for col in price_cols if col in data.columns]

        for col in price_cols:
            if not data.empty:
                # 检查负价格
                negative_prices = (data[col] < 0).sum()
                if negative_prices > 0:
                    errors.append(f"{col} 负价格错误: {negative_prices} 条记录")

                # 检查极值
                q01 = data[col].quantile(0.01)
                q99 = data[col].quantile(0.99)
                extreme_prices = ((data[col] < q01 * 0.5) | (data[col] > q99 * 5)).sum()
                if extreme_prices > 0:
                    warnings.append(f"{col} 极值价格: {extreme_prices} 条记录")

        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def _check_time_order(self, data: pd.DataFrame) -> Dict[str, Any]:
        """检查时间序列顺序"""
        errors = []
        warnings = []

        if 'date' not in data.columns:
            return {'is_valid': True, 'errors': [], 'warnings': []}

        try:
            dates = pd.to_datetime(data['date'])
            if not dates.is_monotonic_increasing:
                descending_count = (dates.diff() < 0).sum()
                warnings.append(f"时间序列非单调递增: {descending_count} 条记录")
        except:
            errors.append("时间序列格式错误")

        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }


class CompletenessValidator:
    """完整性验证器"""

    def validate(self, data: pd.DataFrame, schema: str) -> ValidationResult:
        """验证数据完整性"""
        errors = []
        warnings = []
        details = {'completeness': {}}

        try:
            if data.empty:
                errors.append("数据为空")
                return ValidationResult(
                    stage=ValidationStage.COMPLETENESS,
                    is_passed=False,
                    score=0.0,
                    errors=errors,
                    warnings=warnings,
                    details=details
                )

            # 计算各列完整性
            for column in data.columns:
                missing_count = data[column].isnull().sum()
                completeness_pct = (1 - missing_count / len(data)) * 100
                details['completeness'][column] = {
                    'missing_count': missing_count,
                    'completeness_pct': completeness_pct
                }

                if completeness_pct < 50:
                    errors.append(f"{column} 完整性过低: {completeness_pct:.1f}%")
                elif completeness_pct < 90:
                    warnings.append(f"{column} 完整性较低: {completeness_pct:.1f}%")

            # 检查关键列
            key_columns = self._get_key_columns(schema)
            for col in key_columns:
                if col in data.columns:
                    missing_pct = details['completeness'][col]['completeness_pct']
                    if missing_pct < 95:
                        errors.append(f"关键列 {col} 完整性不足: {missing_pct:.1f}%")

            is_passed = len(errors) == 0
            score = max(0.0, min(1.0, 1.0 - len(errors) * 0.2 - len(warnings) * 0.05))

        except Exception as e:
            errors.append(f"完整性验证异常: {str(e)}")
            is_passed = False
            score = 0.0

        return ValidationResult(
            stage=ValidationStage.COMPLETENESS,
            is_passed=is_passed,
            score=score,
            errors=errors,
            warnings=warnings,
            details=details
        )

    def _get_key_columns(self, schema: str) -> List[str]:
        """获取关键列"""
        key_columns_map = {
            'ohlcv': ['close', 'volume'],
            'timeseries': ['date', 'value'],
            'market_data': ['symbol', 'timestamp', 'price']
        }
        return key_columns_map.get(schema, [])


class ValidationPipeline:
    """综合数据验证管道"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化验证管道

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.stages = {
            ValidationStage.STRUCTURE: StructureValidator(),
            ValidationStage.DATA_TYPE: DataTypeValidator(),
            ValidationStage.BUSINESS_LOGIC: BusinessLogicValidator(),
            ValidationStage.COMPLETENESS: CompletenessValidator()
        }

        # 启用/禁用特定阶段
        self.enabled_stages = self.config.get('enabled_stages', list(self.stages.keys()))

        # 并行执行
        self.parallel = self.config.get('parallel', True)
        self.max_workers = self.config.get('max_workers', 4)

        # 统计信息
        self.stats = {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'stage_stats': {stage.value: {'passed': 0, 'failed': 0} for stage in self.stages.keys()}
        }

        logger.info(f"验证管道初始化完成，启用阶段: {[s.value for s in self.enabled_stages]}")

    async def validate(self, data: Union[pd.DataFrame, Dict], schema: str,
                      symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        执行数据验证

        Args:
            data: 待验证数据
            schema: 数据模式 (ohlcv, timeseries, market_data)
            symbol: 股票代码

        Returns:
            验证结果字典
        """
        self.stats['total_runs'] += 1

        if isinstance(data, dict):
            data = pd.DataFrame(data)

        results = {
            'symbol': symbol,
            'schema': schema,
            'timestamp': datetime.utcnow().isoformat(),
            'overall_score': 0.0,
            'is_valid': False,
            'stages': {},
            'summary': {
                'total_stages': len(self.enabled_stages),
                'passed_stages': 0,
                'failed_stages': 0,
                'total_errors': 0,
                'total_warnings': 0
            }
        }

        stage_results = []

        try:
            if self.parallel and len(self.enabled_stages) > 1:
                # 并行执行验证阶段
                tasks = []
                for stage in self.enabled_stages:
                    if stage in self.stages:
                        validator = self.stages[stage]
                        task = asyncio.create_task(
                            self._run_stage_async(validator, data, schema)
                        )
                        tasks.append((stage, task))

                for stage, task in tasks:
                    result = await task
                    stage_results.append(result)
            else:
                # 串行执行
                for stage in self.enabled_stages:
                    if stage in self.stages:
                        validator = self.stages[stage]
                        result = await self._run_stage_async(validator, data, schema)
                        stage_results.append(result)

            # 汇总结果
            self._aggregate_results(results, stage_results)

            self.stats['successful_runs'] += 1
            for stage in self.enabled_stages:
                if stage in self.stages:
                    result = next((r for r in stage_results if r.stage == stage), None)
                    if result:
                        if result.is_passed:
                            self.stats['stage_stats'][stage.value]['passed'] += 1
                        else:
                            self.stats['stage_stats'][stage.value]['failed'] += 1

        except Exception as e:
            logger.error(f"验证管道执行异常: {str(e)}", exc_info=True)
            self.stats['failed_runs'] += 1
            results['error'] = str(e)

        return results

    async def _run_stage_async(self, validator: Any, data: pd.DataFrame,
                               schema: str) -> ValidationResult:
        """异步执行单个验证阶段"""
        loop = asyncio.get_event_loop()

        if hasattr(validator, 'validate') and asyncio.iscoroutinefunction(validator.validate):
            return await validator.validate(data, schema)
        else:
            # 在线程池中执行同步验证
            with ThreadPoolExecutor(max_workers=1) as executor:
                result = await loop.run_in_executor(
                    executor,
                    lambda: validator.validate(data, schema)
                )
                return result

    def _aggregate_results(self, results: Dict, stage_results: List[ValidationResult]):
        """汇总验证结果"""
        total_score = 0.0
        passed_stages = 0
        all_errors = []
        all_warnings = []

        for result in stage_results:
            results['stages'][result.stage.value] = result.to_dict()

            if result.is_passed:
                passed_stages += 1

            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
            total_score += result.score

        # 计算总体分数
        if stage_results:
            results['overall_score'] = total_score / len(stage_results)

        # 确定整体是否有效
        results['is_valid'] = passed_stages == len(stage_results) and len(all_errors) == 0

        # 更新摘要
        results['summary'] = {
            'total_stages': len(stage_results),
            'passed_stages': passed_stages,
            'failed_stages': len(stage_results) - passed_stages,
            'total_errors': len(all_errors),
            'total_warnings': len(all_warnings),
            'errors': all_errors,
            'warnings': all_warnings
        }

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()

    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'stage_stats': {stage.value: {'passed': 0, 'failed': 0} for stage in self.stages.keys()}
        }

    def add_stage(self, stage: ValidationStage, validator: Any):
        """添加自定义验证阶段"""
        self.stages[stage] = validator
        if stage not in self.enabled_stages:
            self.enabled_stages.append(stage)
        self.stats['stage_stats'][stage.value] = {'passed': 0, 'failed': 0}

    def remove_stage(self, stage: ValidationStage):
        """移除验证阶段"""
        if stage in self.stages:
            del self.stages[stage]
        if stage in self.enabled_stages:
            self.enabled_stages.remove(stage)
        if stage.value in self.stats['stage_stats']:
            del self.stats['stage_stats'][stage.value]


# 便捷函数
async def validate_data_pipeline(data: Union[pd.DataFrame, Dict], schema: str,
                                symbol: Optional[str] = None,
                                config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    便捷的数据验证函数

    Args:
        data: 待验证数据
        schema: 数据模式
        symbol: 股票代码
        config: 配置选项

    Returns:
        验证结果
    """
    pipeline = ValidationPipeline(config)
    return await pipeline.validate(data, schema, symbol)


def create_validation_pipeline(config: Optional[Dict[str, Any]] = None) -> ValidationPipeline:
    """
    创建验证管道实例

    Args:
        config: 配置字典

    Returns:
        验证管道实例
    """
    return ValidationPipeline(config)


# 使用示例
if __name__ == "__main__":
    import asyncio

    async def test_pipeline():
        # 创建测试数据
        test_data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=10),
            'open': [100, 101, 102, np.nan, 104, 105, 106, 107, 108, 109],
            'high': [102, 103, 104, 105, 106, 107, 108, 109, 110, 111],
            'low': [99, 100, 101, 102, 103, 104, 105, 106, 107, 108],
            'close': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
            'volume': [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900]
        })

        # 创建验证管道
        config = {
            'enabled_stages': [ValidationStage.STRUCTURE, ValidationStage.DATA_TYPE,
                             ValidationStage.BUSINESS_LOGIC, ValidationStage.COMPLETENESS],
            'parallel': True,
            'max_workers': 4
        }

        pipeline = ValidationPipeline(config)

        # 执行验证
        result = await pipeline.validate(test_data, 'ohlcv', '0700.HK')

        # 打印结果
        print("\n=== 数据验证结果 ===")
        print(f"总体分数: {result['overall_score']:.2f}")
        print(f"是否有效: {result['is_valid']}")
        print(f"通过阶段: {result['summary']['passed_stages']}/{result['summary']['total_stages']}")
        print(f"错误数量: {result['summary']['total_errors']}")
        print(f"警告数量: {result['summary']['total_warnings']}")

        if result['summary']['errors']:
            print("\n错误详情:")
            for error in result['summary']['errors']:
                print(f"  - {error}")

        if result['summary']['warnings']:
            print("\n警告详情:")
            for warning in result['summary']['warnings']:
                print(f"  - {warning}")

        # 获取统计信息
        stats = pipeline.get_stats()
        print(f"\n验证统计: {stats}")

    # 运行测试
    asyncio.run(test_pipeline())
