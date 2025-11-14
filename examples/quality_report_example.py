"""
数据质量报告生成器 (T354) - 使用示例
演示如何使用 QualityReporter 生成专业的数据质量报告

Author: Claude Code
Date: 2025-11-09
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data import (
    QualityReporter,
    QualityReport,
    QualityScoreCalculator,
    ReportFormatter,
    TrendAnalyzer,
    generate_quality_report
)


async def example_1_basic_usage():
    """示例1: 基本使用 - 快速生成质量报告"""
    print("\n" + "="*80)
    print("示例1: 基本使用 - 快速生成质量报告")
    print("="*80)

    # 模拟数据质量检查结果
    validation_results = [
        {
            'is_valid': True,
            'overall_score': 0.92,
            'stages': {
                'structure': {
                    'is_passed': True,
                    'score': 0.95,
                    'errors': []
                },
                'data_type': {
                    'is_passed': True,
                    'score': 0.93,
                    'errors': []
                },
                'business_logic': {
                    'is_passed': True,
                    'score': 0.88,
                    'errors': []
                }
            }
        }
    ]

    anomaly_results = [
        {
            'summary': {
                'total_anomalies': 5,
                'high_severity': 1,
                'medium_severity': 2,
                'low_severity': 2
            },
            'anomalies': [
                {
                    'type': 'statistical',
                    'severity': 'high',
                    'description': 'Z-Score异常 (3.2σ)',
                    'count': 1
                },
                {
                    'type': 'value',
                    'severity': 'medium',
                    'description': '负值异常',
                    'count': 2
                },
                {
                    'type': 'outlier',
                    'severity': 'low',
                    'description': '离群值',
                    'count': 2
                }
            ]
        }
    ]

    verification_results = [
        {
            'status': 'consistent',
            'consistency_score': 0.88,
            'differences': [
                {
                    'type': 'field_inconsistency',
                    'description': '收盘价字段存在轻微差异',
                    'impact': 'low'
                }
            ]
        }
    ]

    freshness_results = [
        {
            'status': 'up_to_date',
            'freshness_score': 0.95,
            'age_hours': 0.5,
            'last_update': datetime.now().isoformat()
        }
    ]

    # 使用便捷函数生成报告
    print("生成数据质量报告...")
    report = await generate_quality_report(
        symbol='0700.HK',
        validation_results=validation_results,
        anomaly_results=anomaly_results,
        verification_results=verification_results,
        freshness_results=freshness_results
    )

    # 显示报告摘要
    print(f"\n=== 数据质量报告摘要 ===")
    print(f"股票代码: {report.symbol}")
    print(f"报告时间: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"总体分数: {report.overall_score:.2f}/1.00")
    print(f"质量等级: {report.grade}")
    print(f"质量水平: {report.summary.get('quality_level', 'N/A')}")

    print(f"\n各维度分数:")
    for dimension, score in report.dimensions.items():
        print(f"  {dimension:15s}: {score:.2f}")

    print(f"\n主要问题:")
    if report.anomaly_results:
        total_anomalies = report.anomaly_results[0]['summary']['total_anomalies']
        print(f"  - 检测到 {total_anomalies} 个异常")
    if report.verification_results:
        if report.verification_results[0]['differences']:
            print(f"  - 发现 {len(report.verification_results[0]['differences'])} 个一致性差异")

    print(f"\n改进建议 (前5条):")
    for i, rec in enumerate(report.recommendations[:5], 1):
        print(f"  {i}. {rec}")

    return report


async def example_2_advanced_configuration():
    """示例2: 高级配置 - 自定义权重和参数"""
    print("\n" + "="*80)
    print("示例2: 高级配置 - 自定义权重和参数")
    print("="*80)

    # 创建自定义配置
    config = {
        'score_calculator': {
            'weights': {
                'completeness': 0.30,  # 强调完整性
                'accuracy': 0.30,      # 强调准确性
                'consistency': 0.20,
                'timeliness': 0.10,
                'validity': 0.05,
                'uniqueness': 0.05
            },
            'grade_thresholds': {
                'A': 0.95,
                'B': 0.85,
                'C': 0.75,
                'D': 0.65,
                'F': 0.0
            }
        },
        'formatter': {
            'output_dir': 'reports',
            'template': 'detailed.html',
            'include_charts': True
        },
        'trend_analyzer': {
            'min_reports': 5,
            'trend_threshold': 0.05
        }
    }

    # 使用自定义配置创建报告生成器
    reporter = QualityReporter(config)

    # 模拟数据
    validation_results = [{
        'is_valid': True,
        'overall_score': 0.90,
        'stages': {
            'completeness': {'is_passed': True, 'score': 0.95},
            'accuracy': {'is_passed': True, 'score': 0.88}
        }
    }]

    anomaly_results = [{
        'summary': {'total_anomalies': 3},
        'anomalies': [{'type': 'value', 'severity': 'low'}]
    }]

    verification_results = [{
        'status': 'consistent',
        'consistency_score': 0.92
    }]

    freshness_results = [{
        'status': 'up_to_date',
        'freshness_score': 0.90
    }]

    # 生成报告
    print("使用自定义配置生成报告...")
    report = await reporter.generate_report(
        '0939.HK',
        validation_results,
        anomaly_results,
        verification_results,
        freshness_results
    )

    print(f"\n自定义配置报告:")
    print(f"  总体分数: {report.overall_score:.2f}")
    print(f"  质量等级: {report.grade}")
    print(f"  完整性权重: 30%")
    print(f"  准确性权重: 30%")

    return reporter, report


async def example_3_html_report_generation():
    """示例3: HTML 报告生成 - 保存可视化报告"""
    print("\n" + "="*80)
    print("示例3: HTML 报告生成 - 保存可视化报告")
    print("="*80)

    reporter = QualityReporter()

    # 模拟数据
    validation_results = [{
        'is_valid': True,
        'overall_score': 0.88,
        'stages': {
            'structure': {'is_passed': True, 'score': 0.92},
            'data_type': {'is_passed': True, 'score': 0.89},
            'business_logic': {'is_passed': True, 'score': 0.85},
            'completeness': {'is_passed': True, 'score': 0.86}
        }
    }]

    anomaly_results = [{
        'summary': {'total_anomalies': 7},
        'anomalies': [
            {'type': 'statistical', 'severity': 'high', 'count': 2},
            {'type': 'value', 'severity': 'medium', 'count': 3},
            {'type': 'outlier', 'severity': 'low', 'count': 2}
        ]
    }]

    verification_results = [{
        'status': 'inconsistent',
        'consistency_score': 0.78,
        'differences': [
            {'type': 'field_inconsistency', 'description': '价格数据差异', 'impact': 'medium'},
            {'type': 'timestamp_mismatch', 'description': '时间戳不匹配', 'impact': 'high'}
        ]
    }]

    freshness_results = [{
        'status': 'stale',
        'freshness_score': 0.65,
        'age_hours': 48.0
    }]

    # 生成报告
    print("生成包含图表的 HTML 报告...")
    report = await reporter.generate_report(
        '1398.HK',
        validation_results,
        anomaly_results,
        verification_results,
        freshness_results
    )

    # 保存 HTML 报告
    print("保存 HTML 报告...")
    filepath = reporter.save_html_report(report)
    print(f"\n✅ 报告已保存到: {filepath}")

    # 显示报告统计
    stats = reporter.get_stats()
    print(f"\n报告统计:")
    print(f"  报告数量: {stats.get('total_reports', 0)}")
    print(f"  平均分数: {stats.get('avg_score', 0):.2f}")
    print(f"  最佳分数: {stats.get('best_score', 0):.2f}")
    print(f"  最差分数: {stats.get('worst_score', 0):.2f}")

    return report


async def example_4_trend_analysis():
    """示例4: 趋势分析 - 历史报告对比"""
    print("\n" + "="*80)
    print("示例4: 趋势分析 - 历史报告对比")
    print("="*80)

    # 模拟历史报告数据
    historical_reports = []
    base_score = 0.75
    for i in range(10):
        report = {
            'timestamp': (datetime.now() - timedelta(days=i*7)).isoformat(),
            'overall_score': base_score + (i * 0.02) + np.random.normal(0, 0.01),
            'dimensions': {
                'completeness': 0.80 + (i * 0.015),
                'accuracy': 0.78 + (i * 0.018),
                'consistency': 0.75 + (i * 0.012),
                'timeliness': 0.70 + (i * 0.020),
                'validity': 0.82 + (i * 0.010),
                'uniqueness': 0.85 + (i * 0.005)
            }
        }
        historical_reports.append(report)

    # 创建趋势分析器
    trend_analyzer = TrendAnalyzer()

    # 分析趋势
    print("分析历史数据趋势...")
    trends = trend_analyzer.analyze_trends(historical_reports)

    # 显示趋势结果
    print(f"\n=== 趋势分析结果 ===")
    print(f"分析期间: {trends['period']['start']} 至 {trends['period']['end']}")
    print(f"报告数量: {trends['summary']['total_reports']}")

    if 'overall' in trends:
        overall_trend = trends['overall']
        print(f"\n总体趋势:")
        print(f"  方向: {overall_trend['direction']}")
        print(f"  斜率: {overall_trend['slope']:.4f}")
        print(f"  R²: {overall_trend['r_squared']:.3f}")
        print(f"  描述: {overall_trend['description']}")

    if 'dimensions' in trends:
        print(f"\n各维度趋势:")
        for dimension, trend_data in trends['dimensions'].items():
            if 'slope' in trend_data:
                direction = trend_data.get('direction', 'stable')
                slope = trend_data.get('slope', 0)
                r2 = trend_data.get('r_squared', 0)
                print(f"  {dimension:15s}: {direction:8s} (斜率: {slope:+.4f}, R²: {r2:.3f})")

    if 'recommendations' in trends:
        print(f"\n趋势建议:")
        for i, rec in enumerate(trends['recommendations'][:3], 1):
            print(f"  {i}. {rec}")

    return trends


async def example_5_complete_workflow():
    """示例5: 完整工作流 - 端到端数据质量评估"""
    print("\n" + "="*80)
    print("示例5: 完整工作流 - 端到端数据质量评估")
    print("="*80)

    # 创建完整的质量报告系统
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
        'formatter': {
            'output_dir': 'reports',
            'template': 'detailed.html'
        }
    })

    # 步骤1: 收集所有质量检查数据
    print("\n步骤1: 收集质量检查数据...")

    # 模拟多种数据源的质量检查
    data_sources = [
        {'name': '主数据源', 'data': {...}},
        {'name': '备用数据源', 'data': {...}}
    ]

    validation_results = []
    anomaly_results = []
    verification_results = []
    freshness_results = []

    for source in data_sources:
        # 模拟验证结果
        validation_results.append({
            'is_valid': True,
            'overall_score': 0.90,
            'stages': {
                'structure': {'is_passed': True, 'score': 0.95},
                'data_type': {'is_passed': True, 'score': 0.92},
                'business_logic': {'is_passed': True, 'score': 0.88}
            },
            'source': source['name']
        })

        # 模拟异常检测结果
        anomaly_results.append({
            'summary': {'total_anomalies': 4},
            'anomalies': [
                {'type': 'statistical', 'severity': 'medium', 'count': 2},
                {'type': 'value', 'severity': 'low', 'count': 2}
            ],
            'source': source['name']
        })

    # 模拟跨源验证
    verification_results.append({
        'status': 'mostly_consistent',
        'consistency_score': 0.85,
        'differences': [
            {'type': 'value_difference', 'description': '价格差异 < 0.1%', 'impact': 'low'}
        ]
    })

    # 模拟新鲜度检查
    freshness_results.append({
        'status': 'up_to_date',
        'freshness_score': 0.92,
        'age_hours': 2.0
    })

    # 步骤2: 生成综合质量报告
    print("步骤2: 生成综合质量报告...")
    report = await reporter.generate_report(
        symbol='0700.HK',
        validation_results=validation_results,
        anomaly_results=anomaly_results,
        verification_results=verification_results,
        freshness_results=freshness_results
    )

    # 步骤3: 保存报告
    print("步骤3: 保存报告...")
    filepath = reporter.save_html_report(report)
    print(f"✅ 报告已保存: {filepath}")

    # 步骤4: 分析和展示结果
    print("\n步骤4: 质量分析结果")
    print("="*60)

    print(f"\n📊 总体质量评估:")
    print(f"  分数: {report.overall_score:.2f}/1.00")
    print(f"  等级: {report.grade}")
    print(f"  状态: {report.summary.get('quality_level', 'N/A')}")

    print(f"\n📈 维度分析:")
    sorted_dims = sorted(report.dimensions.items(), key=lambda x: x[1], reverse=True)
    for dim, score in sorted_dims:
        status = "✓" if score >= 0.8 else "⚠" if score >= 0.6 else "✗"
        print(f"  {status} {dim:15s}: {score:.2f}")

    print(f"\n🔍 问题总结:")
    total_issues = (
        sum(r['summary'].get('total_anomalies', 0) for r in anomaly_results) +
        sum(len(r.get('differences', [])) for r in verification_results)
    )
    print(f"  总问题数: {total_issues}")

    if report.recommendations:
        print(f"\n💡 优先改进建议:")
        for i, rec in enumerate(report.recommendations[:3], 1):
            print(f"  {i}. {rec}")

    print(f"\n📄 报告文件:")
    print(f"  HTML报告: {filepath}")

    return report


async def main():
    """主函数 - 运行所有示例"""
    print("\n" + "="*80)
    print("数据质量报告生成器 (T354) - 使用示例")
    print("="*80)
    print("\n本示例演示如何使用 QualityReporter 生成专业的数据质量报告")

    try:
        # 运行所有示例
        report1 = await example_1_basic_usage()
        reporter2, report2 = await example_2_advanced_configuration()
        report3 = await example_3_html_report_generation()
        trends = await example_4_trend_analysis()
        report5 = await example_5_complete_workflow()

        print("\n" + "="*80)
        print("✅ 所有示例运行完成！")
        print("="*80)
        print("\n📚 更多资源:")
        print("  - 核心实现: src/data/quality_reporter.py")
        print("  - 测试用例: tests/test_data_quality_validation_system.py")
        print("  - 完整报告: T354_COMPLETION_REPORT.md")
        print("\n🚀 立即开始使用:")
        print("  from data import QualityReporter, generate_quality_report")

    except Exception as e:
        print(f"\n❌ 运行示例时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
