"""
Phase 8b: T350-T354 数据质量与验证系统 - 使用示例
演示如何使用数据质量验证和监控系统的所有功能
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data.validation_pipeline import (
    ValidationPipeline, ValidationStage, create_validation_pipeline
)
from data.anomaly_detector import (
    AnomalyDetector, create_anomaly_detector
)
from data.cross_source_verification import (
    CrossSourceVerification, create_cross_source_verifier
)
from data.freshness_checker import (
    FreshnessChecker, create_freshness_checker
)
from data.quality_reporter import (
    QualityReporter, generate_quality_report
)


async def demo_validation_pipeline():
    """演示数据验证管道"""
    print("\n" + "="*80)
    print("演示 1: 数据验证管道 (T350)")
    print("="*80)

    # 创建测试数据
    np.random.seed(42)
    test_data = pd.DataFrame({
        'date': pd.date_range('2023-01-01', periods=100, freq='D'),
        'open': 100 + np.random.normal(0, 2, 100),
        'high': 102 + np.random.normal(0, 2, 100),
        'low': 98 + np.random.normal(0, 2, 100),
        'close': 101 + np.random.normal(0, 2, 100),
        'volume': 1000 + np.random.randint(0, 500, 100)
    })

    # 注入一些问题
    test_data.loc[20, 'high'] = 90  # 违反高低价逻辑
    test_data.loc[30:32, 'close'] = np.nan  # 缺失数据

    # 创建验证管道
    config = {
        'enabled_stages': [ValidationStage.STRUCTURE, ValidationStage.DATA_TYPE,
                         ValidationStage.BUSINESS_LOGIC, ValidationStage.COMPLETENESS],
        'parallel': True,
        'max_workers': 4
    }

    pipeline = ValidationPipeline(config)

    # 执行验证
    print("\n正在执行数据验证...")
    result = await pipeline.validate(test_data, 'ohlcv', '0700.HK')

    # 打印结果
    print(f"\n✓ 验证完成")
    print(f"  总体分数: {result['overall_score']:.2f}")
    print(f"  是否有效: {result['is_valid']}")
    print(f"  通过阶段: {result['summary']['passed_stages']}/{result['summary']['total_stages']}")
    print(f"  错误数量: {result['summary']['total_errors']}")
    print(f"  警告数量: {result['summary']['total_warnings']}")

    if result['summary']['errors']:
        print("\n  错误详情:")
        for error in result['summary']['errors'][:5]:
            print(f"    - {error}")

    if result['summary']['warnings']:
        print("\n  警告详情:")
        for warning in result['summary']['warnings'][:5]:
            print(f"    - {warning}")

    # 获取统计信息
    stats = pipeline.get_stats()
    print(f"\n  验证统计: 已验证 {stats['total_runs']} 次")

    return result


async def demo_anomaly_detector():
    """演示异常检测系统"""
    print("\n" + "="*80)
    print("演示 2: 异常检测系统 (T351)")
    print("="*80)

    # 创建包含异常的数据
    np.random.seed(42)
    test_data = pd.Series(
        np.random.normal(100, 5, 100),
        index=pd.date_range('2023-01-01', periods=100, freq='D'),
        name='price'
    )

    # 注入异常
    test_data[20] = 150  # 极端值
    test_data[30:32] = [200, 200]  # 连续极端值
    test_data[50] = -10  # 负值异常
    test_data[60:62] = [101, 101]  # 重复值

    # 创建异常检测器
    config = {
        'detection_modes': ['statistical', 'rule_based'],
        'statistical': {
            'z_threshold': 2.5,
            'iqr_multiplier': 1.5
        },
        'rule_based': {},
        'parallel': True
    }

    detector = AnomalyDetector(config)

    # 执行检测
    print("\n正在执行异常检测...")
    result = await detector.detect(test_data, 'timeseries')

    # 打印结果
    print(f"\n✓ 异常检测完成")
    print(f"  检测到 {result['summary']['total_anomalies']} 个异常")

    print(f"\n  异常类型分布:")
    for type_name, count in result['summary']['by_type'].items():
        print(f"    {type_name}: {count}")

    print(f"\n  严重程度分布:")
    for severity, count in result['summary']['by_severity'].items():
        print(f"    {severity}: {count}")

    # 打印前5个异常
    if result['anomalies']:
        print(f"\n  前5个异常:")
        for i, anomaly in enumerate(result['anomalies'][:5], 1):
            print(f"    {i}. {anomaly['description']}")
            print(f"       类型: {anomaly['type']}, 严重程度: {anomaly['severity']}")

    # 获取统计信息
    stats = detector.get_stats()
    print(f"\n  检测统计: 共执行 {stats['total_detections']} 次检测")

    return result


async def demo_cross_source_verification():
    """演示跨源数据验证"""
    print("\n" + "="*80)
    print("演示 3: 跨源数据验证 (T352)")
    print("="*80)

    # 创建多个数据源
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=50, freq='D')

    # 数据源1 - Yahoo Finance
    source1 = pd.DataFrame({
        'open': 100 + np.random.normal(0, 2, 50),
        'high': 102 + np.random.normal(0, 2, 50),
        'low': 98 + np.random.normal(0, 2, 50),
        'close': 101 + np.random.normal(0, 2, 50),
        'volume': 1000 + np.random.randint(0, 500, 50)
    }, index=dates)

    # 数据源2 - Alpha Vantage (有细微差异)
    source2 = source1.copy()
    source2['close'] = source1['close'] * 1.002  # 0.2%偏差
    source2.loc[15:17, 'volume'] = np.nan  # 缺失数据

    # 数据源3 - Bloomberg (更高质量)
    source3 = source1.copy() * 0.999  # 0.1%偏差

    data_sources = {
        'yahoo_finance': source1,
        'alpha_vantage': source2,
        'bloomberg': source3
    }

    # 创建跨源验证器
    config = {
        'min_sources': 2,
        'parallel_comparison': True,
        'consistency': {
            'tolerance': {
                'price': 0.005,  # 0.5%
                'volume': 0.05
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

    verifier = CrossSourceVerification(config)

    # 执行验证
    print("\n正在执行跨源验证...")
    result = await verifier.verify('0700.HK', data_sources)

    # 打印结果
    print(f"\n✓ 跨源验证完成")
    print(f"  状态: {result.status.value}")
    print(f"  一致性分数: {result.consistency_score:.2f}")
    print(f"  数据源: {', '.join(result.sources_compared)}")

    print(f"\n  差异数量: {len(result.differences)}")
    for i, diff in enumerate(result.differences[:5], 1):
        print(f"    {i}. {diff['description']} (严重程度: {diff.get('severity', 'unknown')})")

    print(f"\n  建议:")
    for i, rec in enumerate(result.recommendations, 1):
        print(f"    {i}. {rec}")

    # 测试冲突解决
    print(f"\n  冲突解决:")
    resolution = verifier.priority_resolver.resolve_conflict(
        '0700.HK', data_sources
    )
    print(f"    策略: {resolution['resolution_strategy']}")
    print(f"    置信度: {resolution['confidence']:.2f}")

    # 获取统计信息
    stats = verifier.get_stats()
    print(f"\n  验证统计: 共执行 {stats['total_verifications']} 次验证")

    return result


async def demo_freshness_checker():
    """演示数据新鲜度检查"""
    print("\n" + "="*80)
    print("演示 4: 数据新鲜度检查 (T353)")
    print("="*80)

    # 创建测试数据
    test_data = pd.DataFrame({
        'date': pd.date_range('2023-01-01', periods=50, freq='D'),
        'open': 100 + np.random.normal(0, 2, 50),
        'high': 102 + np.random.normal(0, 2, 50),
        'low': 98 + np.random.normal(0, 2, 50),
        'close': 101 + np.random.normal(0, 2, 50),
        'volume': 1000 + np.random.randint(0, 500, 50)
    })

    # 缺失一些数据
    missing_dates = test_data['date'].iloc[5:8]
    test_data = test_data[~test_data['date'].isin(missing_dates)]

    # 设置最后更新时间
    last_update = datetime.utcnow() - timedelta(hours=1)

    # 创建新鲜度检查器
    config = {
        'latency': {
            'thresholds': {
                'daily': 4.0
            }
        },
        'alert': {
            'alert_rules': {
                'stale': {'enabled': True, 'channels': ['log']},
                'very_stale': {'enabled': True, 'channels': ['log', 'email']}
            }
        },
        'default_frequencies': {
            '0700.HK': 'daily',
            'default': 'daily'
        }
    }

    checker = FreshnessChecker(config)

    # 执行检查
    print("\n正在执行数据新鲜度检查...")
    result = await checker.check('0700.HK', test_data, last_update)

    # 打印结果
    print(f"\n✓ 新鲜度检查完成")
    print(f"  状态: {result.status.value}")
    print(f"  新鲜度分数: {result.freshness_score:.2f}")
    print(f"  数据年龄: {result.age_hours:.1f}小时")
    print(f"  预期频率: {result.expected_frequency}")

    print(f"\n  检测到的异常: {len(result.anomalies)}")
    for i, anomaly in enumerate(result.anomalies, 1):
        print(f"    {i}. {anomaly['description']} (严重程度: {anomaly.get('severity', 'unknown')})")

    print(f"\n  建议:")
    for i, rec in enumerate(result.recommendations, 1):
        print(f"    {i}. {rec}")

    # 测试多源监控
    print(f"\n  多源延迟监控:")
    sources = {
        'yahoo': datetime.utcnow() - timedelta(hours=1),
        'alpha_vantage': datetime.utcnow() - timedelta(hours=2),
        'bloomberg': datetime.utcnow() - timedelta(minutes=30)
    }
    monitor_result = checker.latency_monitor.monitor_multiple_sources(sources, 'daily')
    print(f"    整体状态: {monitor_result['overall_status'].value}")
    print(f"    陈旧源: {', '.join(monitor_result['stale_sources'])}")

    # 获取统计信息
    stats = checker.get_stats()
    print(f"\n  检查统计: 共执行 {stats['total_checks']} 次检查")

    return result


async def demo_quality_reporter():
    """演示质量报告生成"""
    print("\n" + "="*80)
    print("演示 5: 数据质量报告生成 (T354)")
    print("="*80)

    # 创建测试结果数据
    validation_results = [
        {
            'is_valid': True,
            'overall_score': 0.9,
            'stages': {
                'structure': {'is_passed': True, 'score': 0.95, 'errors': []},
                'data_type': {'is_passed': True, 'score': 0.92, 'errors': []},
                'business_logic': {'is_passed': True, 'score': 0.88, 'errors': []}
            }
        }
    ]

    anomaly_results = [
        {
            'summary': {'total_anomalies': 5},
            'anomalies': [
                {'type': 'statistical', 'severity': 'high', 'description': 'Z-Score异常'},
                {'type': 'value', 'severity': 'medium', 'description': '负值异常'},
            ]
        }
    ]

    verification_results = [
        {
            'status': 'consistent',
            'consistency_score': 0.85,
            'differences': [{'type': 'field_inconsistency', 'description': '字段不一致'}]
        }
    ]

    freshness_results = [
        {
            'status': 'up_to_date',
            'freshness_score': 0.9,
            'age_hours': 1.5
        }
    ]

    # 创建质量报告生成器
    config = {
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
        'formatter': {
            'output_dir': 'reports'
        }
    }

    reporter = QualityReporter(config)

    # 生成报告
    print("\n正在生成数据质量报告...")
    report = await reporter.generate_report(
        '0700.HK',
        validation_results,
        anomaly_results,
        verification_results,
        freshness_results
    )

    # 打印结果
    print(f"\n✓ 质量报告生成完成")
    print(f"  股票代码: {report.symbol}")
    print(f"  总体分数: {report.overall_score:.2f}")
    print(f"  等级: {report.grade}")
    print(f"  质量水平: {report.summary['quality_level']}")

    print(f"\n  各维度分数:")
    for dimension, score in report.dimensions.items():
        print(f"    {dimension}: {score:.2f}")

    print(f"\n  总结:")
    print(f"    验证成功率: {report.summary['validation_success_rate']:.1%}")
    print(f"    异常数量: {report.summary['total_anomalies']}")
    print(f"    最佳维度: {report.summary['best_dimension'][0]} ({report.summary['best_dimension'][1]:.2f})")
    print(f"    最差维度: {report.summary['worst_dimension'][0]} ({report.summary['worst_dimension'][1]:.2f})")

    print(f"\n  改进建议:")
    for i, rec in enumerate(report.recommendations, 1):
        print(f"    {i}. {rec}")

    # 尝试保存HTML报告
    try:
        print(f"\n  正在保存HTML报告...")
        filepath = reporter.save_html_report(report)
        print(f"    ✓ 报告已保存到: {filepath}")
    except Exception as e:
        print(f"    ✗ 报告保存失败: {e}")

    # 获取统计信息
    stats = reporter.get_stats()
    print(f"\n  报告统计: 已生成 {stats['reports_generated']} 份报告")
    if stats['reports_generated'] > 0:
        print(f"    平均质量分数: {stats['average_score']:.2f}")

    return report


async def demo_full_pipeline():
    """演示完整的数据质量管道"""
    print("\n" + "="*80)
    print("演示 6: 完整数据质量管道")
    print("="*80)
    print("将所有模块整合到一个完整的流程中")

    # 步骤1: 创建测试数据
    print("\n步骤 1: 创建测试数据...")
    np.random.seed(42)
    test_data = pd.DataFrame({
        'date': pd.date_range('2023-01-01', periods=100, freq='D'),
        'open': 100 + np.random.normal(0, 2, 100),
        'high': 102 + np.random.normal(0, 2, 100),
        'low': 98 + np.random.normal(0, 2, 100),
        'close': 101 + np.random.normal(0, 2, 100),
        'volume': 1000 + np.random.randint(0, 500, 100)
    })

    # 注入一些问题
    test_data.loc[20, 'high'] = 90  # 违反高低价逻辑
    test_data.loc[30:32, 'close'] = np.nan  # 缺失数据
    test_data.loc[40] = 150  # 异常值
    test_data.loc[50] = -5  # 负值

    # 创建多个数据源
    source1 = test_data.copy()
    source2 = test_data.copy() * 1.002  # 轻微差异
    data_sources = {'source1': source1, 'source2': source2}

    # 步骤2: 数据验证
    print("步骤 2: 执行数据验证...")
    pipeline = ValidationPipeline({
        'enabled_stages': [ValidationStage.STRUCTURE, ValidationStage.DATA_TYPE,
                         ValidationStage.BUSINESS_LOGIC, ValidationStage.COMPLETENESS],
        'parallel': True
    })
    validation_result = await pipeline.validate(test_data, 'ohlcv', '0700.HK')
    print(f"  ✓ 验证完成，分数: {validation_result['overall_score']:.2f}")

    # 步骤3: 异常检测
    print("步骤 3: 执行异常检测...")
    detector = AnomalyDetector({
        'detection_modes': ['statistical', 'rule_based'],
        'parallel': True
    })
    anomaly_result = await detector.detect(test_data, 'ohlcv')
    print(f"  ✓ 异常检测完成，发现 {anomaly_result['summary']['total_anomalies']} 个异常")

    # 步骤4: 跨源验证
    print("步骤 4: 执行跨源验证...")
    verifier = CrossSourceVerification({
        'min_sources': 2,
        'parallel_comparison': True
    })
    verification_result = await verifier.verify('0700.HK', data_sources)
    print(f"  ✓ 跨源验证完成，一致性分数: {verification_result.consistency_score:.2f}")

    # 步骤5: 新鲜度检查
    print("步骤 5: 执行新鲜度检查...")
    checker = FreshnessChecker({
        'latency': {'thresholds': {'daily': 4.0}}
    })
    freshness_result = await checker.check('0700.HK', test_data, datetime.utcnow() - timedelta(hours=1))
    print(f"  ✓ 新鲜度检查完成，状态: {freshness_result.status.value}")

    # 步骤6: 生成质量报告
    print("步骤 6: 生成质量报告...")
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

    quality_report = await reporter.generate_report(
        '0700.HK',
        [validation_result],
        [anomaly_result],
        [verification_result],
        [freshness_result]
    )
    print(f"  ✓ 质量报告生成完成，总体分数: {quality_report.overall_score:.2f}，等级: {quality_report.grade}")

    # 最终总结
    print("\n" + "="*80)
    print("数据质量验证完成总结")
    print("="*80)
    print(f"✓ 数据验证: {validation_result['overall_score']:.2f}")
    print(f"✓ 异常检测: {anomaly_result['summary']['total_anomalies']} 个异常")
    print(f"✓ 跨源验证: {verification_result.consistency_score:.2f}")
    print(f"✓ 新鲜度检查: {freshness_result.status.value}")
    print(f"✓ 质量报告: {quality_report.overall_score:.2f} (等级: {quality_report.grade})")

    return quality_report


async def main():
    """主函数 - 运行所有演示"""
    print("\n" + "="*80)
    print("Phase 8b: T350-T354 数据质量与验证系统 - 完整演示")
    print("="*80)
    print("本演示将展示数据质量验证和监控系统的所有功能")
    print("包括:")
    print("  1. 数据验证管道 - 多层次自动化验证")
    print("  2. 异常检测系统 - 统计、ML和规则基检测")
    print("  3. 跨源数据验证 - 多数据源对比和一致性检查")
    print("  4. 数据新鲜度检查 - 更新延迟和缺失数据检测")
    print("  5. 质量报告生成 - HTML报告和趋势分析")
    print("  6. 完整管道演示 - 端到端数据质量监控")

    try:
        # 运行各个演示
        await demo_validation_pipeline()
        await demo_anomaly_detector()
        await demo_cross_source_verification()
        await demo_freshness_checker()
        await demo_quality_reporter()
        await demo_full_pipeline()

        print("\n" + "="*80)
        print("✓ 所有演示完成！")
        print("="*80)
        print("\n数据质量验证系统已成功演示所有功能。")
        print("您可以在生产环境中使用这些模块来确保数据质量。")

    except Exception as e:
        print(f"\n✗ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行演示
    asyncio.run(main())
