# Phase 8b: T350-T354 数据质量与验证系统

## 概述

Phase 8b实现了一套完整的数据质量与验证监控系统，包含5个核心模块，提供自动化数据验证、异常检测、跨源验证、新鲜度检查和质量报告生成功能。

## 模块架构

```
Phase 8b 数据质量与验证系统
├── T350: validation_pipeline.py     - 综合数据验证管道
├── T351: anomaly_detector.py         - 数据异常检测系统
├── T352: cross_source_verification.py - 跨源数据验证
├── T353: freshness_checker.py        - 数据新鲜度检查
├── T354: quality_reporter.py         - 数据质量报告生成
└── test_data_quality_validation_system.py - 综合测试
```

## 核心功能

### 1. T350: 数据验证管道 (validation_pipeline.py)

**功能**: 多层次自动化数据验证流程

**主要特性**:
- **4个验证阶段**:
  - `STRUCTURE`: 结构验证（列名、数据完整性）
  - `DATA_TYPE`: 数据类型验证（数值、日期格式）
  - `BUSINESS_LOGIC`: 业务逻辑验证（OHLC规则、价格逻辑）
  - `COMPLETENESS`: 完整性验证（缺失值检查）
- **并行/串行执行**: 支持多线程并行验证
- **可配置规则**: 灵活的验证规则配置
- **详细报告**: 提供验证结果和错误信息

**使用示例**:
```python
from data.validation_pipeline import ValidationPipeline, ValidationStage

# 创建验证管道
config = {
    'enabled_stages': [ValidationStage.STRUCTURE, ValidationStage.DATA_TYPE,
                     ValidationStage.BUSINESS_LOGIC, ValidationStage.COMPLETENESS],
    'parallel': True,
    'max_workers': 4
}
pipeline = ValidationPipeline(config)

# 执行验证
result = await pipeline.validate(data, 'ohlcv', '0700.HK')

print(f"总体分数: {result['overall_score']:.2f}")
print(f"是否有效: {result['is_valid']}")
print(f"错误: {result['summary']['errors']}")
```

### 2. T351: 异常检测系统 (anomaly_detector.py)

**功能**: 统计、机器学习和规则基异常检测

**主要特性**:
- **统计异常检测**:
  - Z-Score异常检测
  - IQR异常检测
  - MAD异常检测
  - 季节性异常检测
- **机器学习异常检测**:
  - Isolation Forest
  - DBSCAN聚类
  - PCA重构异常检测
- **规则基异常检测**:
  - 负值检查
  - 零值检查
  - 极端变化检查
  - 重复值检查
  - 缺失值检查
  - 值边界检查
- **实时监控**: 支持滑动窗口实时异常检测

**使用示例**:
```python
from data.anomaly_detector import AnomalyDetector

# 创建异常检测器
config = {
    'detection_modes': ['statistical', 'rule_based'],
    'statistical': {'z_threshold': 2.5},
    'parallel': True
}
detector = AnomalyDetector(config)

# 执行检测
result = await detector.detect(data, 'timeseries')

print(f"检测到 {result['summary']['total_anomalies']} 个异常")
for anomaly in result['anomalies']:
    print(f"  {anomaly['type']}: {anomaly['description']}")
```

### 3. T352: 跨源数据验证 (cross_source_verification.py)

**功能**: 多数据源对比和一致性检查

**主要特性**:
- **一致性检查**: OHLCV数据一致性验证
- **元数据对比**: 数据源元数据一致性验证
- **差异分析**: 详细的差异分析和分类
- **优先级解决**: 基于优先级的冲突解决
- **并行比较**: 多数据源并行比较

**使用示例**:
```python
from data.cross_source_verification import CrossSourceVerification

# 创建数据源
data_sources = {
    'yahoo': yahoo_data,
    'alpha_vantage': alpha_vantage_data,
    'bloomberg': bloomberg_data
}

# 创建验证器
verifier = CrossSourceVerification({
    'min_sources': 2,
    'parallel_comparison': True,
    'consistency': {
        'tolerance': {'price': 0.01},
        'minimum_matches': 0.7
    }
})

# 执行验证
result = await verifier.verify('0700.HK', data_sources)

print(f"状态: {result.status.value}")
print(f"一致性分数: {result.consistency_score:.2f}")
print(f"差异: {result.differences}")
```

### 4. T353: 数据新鲜度检查 (freshness_checker.py)

**功能**: 数据更新时间检查、延迟监控和缺失数据检测

**主要特性**:
- **延迟监控**: 实时监控数据更新延迟
- **更新频率分析**: 分析数据更新模式和频率
- **缺失数据检测**: 检测数据缺口和缺失期间
- **告警管理**: 自动告警机制
- **多源监控**: 同时监控多个数据源

**使用示例**:
```python
from data.freshness_checker import FreshnessChecker, UpdateStatus

# 创建检查器
checker = FreshnessChecker({
    'latency': {'thresholds': {'daily': 4.0}},
    'alert': {
        'alert_rules': {
            'stale': {'enabled': True, 'channels': ['log']}
        }
    }
})

# 执行检查
result = await checker.check('0700.HK', data, last_update)

print(f"状态: {result.status.value}")
print(f"新鲜度分数: {result.freshness_score:.2f}")
print(f"数据年龄: {result.age_hours:.1f}小时")
```

### 5. T354: 数据质量报告生成 (quality_reporter.py)

**功能**: 综合质量评分、报告生成和趋势分析

**主要特性**:
- **质量评分算法**: 6维度质量评分
  - 完整性 (Completeness): 25%
  - 准确性 (Accuracy): 25%
  - 一致性 (Consistency): 20%
  - 及时性 (Timeliness): 15%
  - 有效性 (Validity): 10%
  - 唯一性 (Uniqueness): 5%
- **HTML报告生成**: 美观的HTML报告
- **趋势分析**: 历史数据质量趋势分析
- **图表生成**: 雷达图、趋势图、异常分布图
- **改进建议**: 自动生成改进建议

**使用示例**:
```python
from data.quality_reporter import QualityReporter

# 创建报告生成器
reporter = QualityReporter({
    'score_calculator': {
        'weights': {
            'completeness': 0.25,
            'accuracy': 0.25,
            'consistency': 0.20,
            'timeliness': 0.15,
            'validity': 0.10,
            'uniqueness': 0.05
        }
    },
    'formatter': {'output_dir': 'reports'}
})

# 生成报告
report = await reporter.generate_report(
    '0700.HK',
    validation_results,
    anomaly_results,
    verification_results,
    freshness_results
)

print(f"总体分数: {report.overall_score:.2f}")
print(f"等级: {report.grade}")
print(f"各维度: {report.dimensions}")

# 保存HTML报告
filepath = reporter.save_html_report(report)
print(f"报告已保存到: {filepath}")
```

## 完整工作流示例

```python
import asyncio
from data.validation_pipeline import ValidationPipeline
from data.anomaly_detector import AnomalyDetector
from data.cross_source_verification import CrossSourceVerification
from data.freshness_checker import FreshnessChecker
from data.quality_reporter import QualityReporter

async def full_data_quality_check(symbol, data, data_sources):
    """完整的数据质量检查流程"""

    # 步骤1: 数据验证
    pipeline = ValidationPipeline()
    validation_result = await pipeline.validate(data, 'ohlcv', symbol)

    # 步骤2: 异常检测
    detector = AnomalyDetector()
    anomaly_result = await detector.detect(data, 'ohlcv')

    # 步骤3: 跨源验证
    verifier = CrossSourceVerification()
    verification_result = await verifier.verify(symbol, data_sources)

    # 步骤4: 新鲜度检查
    checker = FreshnessChecker()
    freshness_result = await checker.check(symbol, data, datetime.utcnow())

    # 步骤5: 生成质量报告
    reporter = QualityReporter()
    quality_report = await reporter.generate_report(
        symbol,
        [validation_result],
        [anomaly_result],
        [verification_result],
        [freshness_result]
    )

    return quality_report

# 运行检查
report = await full_data_quality_check('0700.HK', stock_data, sources)
print(f"质量分数: {report.overall_score:.2f}, 等级: {report.grade}")
```

## 配置选项

### 验证管道配置
```python
config = {
    'enabled_stages': [ValidationStage.STRUCTURE, ValidationStage.COMPLETENESS],
    'parallel': True,
    'max_workers': 4
}
```

### 异常检测配置
```python
config = {
    'detection_modes': ['statistical', 'rule_based', 'ml'],
    'statistical': {
        'z_threshold': 2.5,
        'iqr_multiplier': 1.5,
        'mad_multiplier': 3.5
    },
    'ml': {
        'contamination': 0.1,
        'random_state': 42
    },
    'rule_based': {}
}
```

### 跨源验证配置
```python
config = {
    'min_sources': 2,
    'parallel_comparison': True,
    'consistency': {
        'tolerance': {
            'price': 0.01,  # 1%
            'volume': 0.05  # 5%
        },
        'minimum_matches': 0.7
    },
    'priority': {
        'source_priorities': {
            'bloomberg': 10,
            'yahoo_finance': 7,
            'alpha_vantage': 6
        }
    }
}
```

### 新鲜度检查配置
```python
config = {
    'latency': {
        'thresholds': {
            'real_time': 0.5,  # 30分钟
            'daily': 4.0,      # 4小时
            'weekly': 48.0,    # 48小时
            'monthly': 168.0   # 1周
        }
    },
    'alert': {
        'alert_rules': {
            'stale': {'enabled': True, 'channels': ['log']},
            'very_stale': {'enabled': True, 'channels': ['log', 'email']}
        },
        'alert_cooldown': 3600  # 1小时
    }
}
```

### 质量报告配置
```python
config = {
    'score_calculator': {
        'weights': {
            'completeness': 0.25,
            'accuracy': 0.25,
            'consistency': 0.20,
            'timeliness': 0.15,
            'validity': 0.10,
            'uniqueness': 0.05
        },
        'grade_thresholds': {
            'A': 0.9,
            'B': 0.8,
            'C': 0.7,
            'D': 0.6,
            'F': 0.0
        }
    },
    'formatter': {
        'output_dir': 'reports'
    }
}
```

## 运行测试

### 运行综合测试
```bash
# 运行所有测试
python -m pytest tests/test_data_quality_validation_system.py -v

# 运行特定测试
python -m pytest tests/test_data_quality_validation_system.py::TestValidationPipeline -v
python -m pytest tests/test_data_quality_validation_system.py::TestAnomalyDetector -v
```

### 运行演示
```bash
# 运行完整演示
python examples/data_quality_validation_demo.py
```

## 依赖库

主要依赖库:
- `pandas`: 数据处理
- `numpy`: 数值计算
- `scikit-learn`: 机器学习算法
- `scipy`: 统计分析
- `matplotlib`: 图表生成
- `seaborn`: 图表美化
- `jinja2`: HTML模板
- `asyncio`: 异步编程

安装依赖:
```bash
pip install pandas numpy scikit-learn scipy matplotlib seaborn jinja2
```

## 输出文件

### 质量报告
- 位置: `reports/` 目录
- 格式: HTML
- 内容: 包含质量评分、维度分析、异常详情、趋势图表

### 测试报告
- 位置: 测试输出
- 格式: 控制台输出
- 内容: 测试通过/失败情况

## 最佳实践

### 1. 数据验证
- 在数据入库前进行验证
- 定期重新验证历史数据
- 根据业务需求调整验证规则

### 2. 异常检测
- 结合多种检测方法提高准确性
- 定期更新异常检测阈值
- 建立异常分类和处置流程

### 3. 跨源验证
- 使用至少2-3个数据源
- 设置合理的容忍度范围
- 定期检查数据源质量

### 4. 新鲜度监控
- 根据数据特性设置阈值
- 配置告警机制
- 监控多数据源更新状态

### 5. 质量报告
- 定期生成质量报告
- 跟踪质量趋势
- 根据建议改进数据质量

## 故障排除

### 常见问题

**Q: 验证过程缓慢**
A: 启用并行处理 (`parallel: True`) 并调整 `max_workers`

**Q: 异常检测误报**
A: 调整检测阈值 (z_threshold, iqr_multiplier)

**Q: 跨源验证不一致**
A: 检查数据源质量，调整容忍度范围

**Q: 新鲜度告警频繁**
A: 增加告警冷却时间 (alert_cooldown)

### 日志记录

系统使用标准Python logging:
```python
import logging
logging.basicConfig(level=logging.INFO)

# 查看日志
logger = logging.getLogger('quant_system.data.validation_pipeline')
logger.info("验证信息")
```

## 性能优化

1. **并行处理**: 启用多线程并行执行
2. **缓存结果**: 缓存验证结果避免重复计算
3. **增量验证**: 仅验证新增或修改的数据
4. **批处理**: 批量处理多个数据源
5. **资源管理**: 适当限制并发数量

## 扩展开发

### 添加自定义验证规则

```python
from data.validation_pipeline import ValidationStage

class CustomValidator:
    def validate(self, data):
        # 自定义验证逻辑
        return ValidationResult(
            stage=ValidationStage.STRUCTURE,
            is_passed=True,
            score=1.0
        )

# 添加到管道
pipeline = ValidationPipeline()
pipeline.add_stage(ValidationStage.STRUCTURE, CustomValidator())
```

### 添加自定义异常检测方法

```python
from data.anomaly_detector import AnomalyType

class CustomAnomalyDetector:
    def detect(self, data):
        # 自定义检测逻辑
        return [AnomalyResult(
            type=AnomalyType.VALUE,
            score=1.0,
            confidence=1.0,
            index=data.index[0]
        )]

# 添加到检测器
detector = AnomalyDetector()
detector.add_detector('custom', CustomAnomalyDetector())
```

## 总结

Phase 8b数据质量与验证系统提供了完整的数据质量管理解决方案，包括:

1. **全面验证**: 多层次数据验证确保数据质量
2. **智能检测**: 多种异常检测方法发现数据问题
3. **跨源对比**: 多数据源一致性验证
4. **实时监控**: 数据新鲜度和延迟监控
5. **自动报告**: 质量评分和趋势分析报告

该系统可集成到数据管道中，提供持续的数据质量监控和改进建议。
