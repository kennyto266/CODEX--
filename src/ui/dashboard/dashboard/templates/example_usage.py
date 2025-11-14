#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告模板使用示例
==================

演示如何使用报告模板系统生成各种类型的专业报告。

作者: CODEX Trading System
版本: 1.0
日期: 2025-11-09
"""

import os
import json
from datetime import datetime
from report_generator import ReportGenerator, ReportConfig


def example_1_basic_performance_report():
    """Example 1: Generate basic performance report"""
    print("\n" + "="*60)
    print("Example 1: Basic Performance Report")
    print("="*60)

    # 创建报告生成器
    generator = ReportGenerator()

    # 配置报告
    config = ReportConfig(
        template_type='performance',
        symbol='0700.HK',
        period='2023-01-01 至 2023-12-31',
        output_dir='./output/examples'
    )

    # 生成并保存报告
    output_path = generator.save_report(config)
    print(f"Report generated: {output_path}")


def example_2_risk_assessment_report():
    """Example 2: Generate risk assessment report"""
    print("\n" + "="*60)
    print("Example 2: Risk Assessment Report")
    print("="*60)

    generator = ReportGenerator()

    config = ReportConfig(
        template_type='risk',
        symbol='0388.HK',
        period='2023-01-01 至 2023-12-31',
        output_dir='./output/examples'
    )

    output_path = generator.save_report(config)
    print(f"Report generated: {output_path}")


def example_3_strategy_comparison_report():
    """Example 3: Generate strategy comparison report"""
    print("\n" + "="*60)
    print("Example 3: Strategy Comparison Report")
    print("="*60)

    generator = ReportGenerator()

    config = ReportConfig(
        template_type='comparison',
        symbol='0939.HK',
        period='2023-01-01 至 2023-12-31',
        output_dir='./output/examples'
    )

    output_path = generator.save_report(config)
    print(f"Report generated: {output_path}")


def example_4_executive_summary_report():
    """Example 4: Generate executive summary report"""
    print("\n" + "="*60)
    print("Example 4: Executive Summary Report")
    print("="*60)

    generator = ReportGenerator()

    config = ReportConfig(
        template_type='executive_summary',
        symbol='1398.HK',
        period='2023-01-01 至 2023-12-31',
        output_dir='./output/examples'
    )

    output_path = generator.save_report(config)
    print(f"Report generated: {output_path}")


def example_5_technical_appendix_report():
    """Example 5: Generate technical appendix report"""
    print("\n" + "="*60)
    print("Example 5: Technical Appendix Report")
    print("="*60)

    generator = ReportGenerator()

    config = ReportConfig(
        template_type='technical',
        symbol='2628.HK',
        period='2023-01-01 至 2023-12-31',
        output_dir='./output/examples'
    )

    output_path = generator.save_report(config)
    print(f"Report generated: {output_path}")


def example_6_custom_data_report():
    """Example 6: Generate report with custom data"""
    print("\n" + "="*60)
    print("Example 6: Custom Data Report")
    print("="*60)

    generator = ReportGenerator()

    # 准备自定义数据
    custom_data = {
        'total_return': 35.8,
        'annual_return': 17.2,
        'sharpe_ratio': 2.3,
        'max_drawdown': -6.5,
        'volatility': 11.8,
        'win_rate': 68.5,
        'custom_field': '这是自定义字段',
        'custom_section': {
            'title': '自定义章节',
            'content': '自定义内容示例'
        }
    }

    config = ReportConfig(
        template_type='performance',
        symbol='3988.HK',
        period='2023-06-01 至 2024-06-01',
        output_dir='./output/examples'
    )

    output_path = generator.save_report(config, custom_data=custom_data)
    print(f"Report generated: {output_path}")


def example_7_batch_generation():
    """Example 7: Batch generate multiple reports"""
    print("\n" + "="*60)
    print("Example 7: Batch Generation")
    print("="*60)

    generator = ReportGenerator()

    # 准备多个配置
    configs = [
        ReportConfig('performance', '0700.HK', '2023-Q1', './output/examples'),
        ReportConfig('risk', '0700.HK', '2023-Q1', './output/examples'),
        ReportConfig('comparison', '0700.HK', '2023-Q1', './output/examples'),
        ReportConfig('executive_summary', '0700.HK', '2023-Q1', './output/examples'),
        ReportConfig('technical', '0700.HK', '2023-Q1', './output/examples')
    ]

    # 批量生成
    output_paths = generator.batch_generate(configs)
    print(f"Batch generation completed: {len(output_paths)} reports:")
    for path in output_paths:
        print(f"   - {path}")


def example_8_multiple_symbols():
    """Example 8: Multiple stocks batch analysis"""
    print("\n" + "="*60)
    print("Example 8: Multiple Symbols Analysis")
    print("="*60)

    generator = ReportGenerator()

    # 港股主要股票
    symbols = ['0700.HK', '0388.HK', '0939.HK', '1398.HK', '2628.HK', '3988.HK']

    configs = []
    for symbol in symbols:
        config = ReportConfig(
            template_type='performance',
            symbol=symbol,
            period='2023-01-01 至 2023-12-31',
            output_dir='./output/examples/multiple_symbols'
        )
        configs.append(config)

    output_paths = generator.batch_generate(configs)
    print(f"Performance reports generated for {len(symbols)} stocks:")
    for symbol, path in zip(symbols, output_paths):
        print(f"   {symbol}: {path}")


def example_9_comprehensive_analysis():
    """Example 9: Comprehensive analysis report suite"""
    print("\n" + "="*60)
    print("Example 9: Comprehensive Analysis")
    print("="*60)

    generator = ReportGenerator()

    # 为单只股票生成完整报告套件
    symbol = '0700.HK'
    period = '2023-01-01 至 2023-12-31'

    templates = [
        ('performance', '性能分析'),
        ('risk', '风险评估'),
        ('comparison', '策略对比'),
        ('executive_summary', '执行摘要'),
        ('technical', '技术附录')
    ]

    configs = [
        ReportConfig(template, symbol, period, f'./output/examples/comprehensive/{template}')
        for template, _ in templates
    ]

    output_paths = generator.batch_generate(configs)

    print(f"Comprehensive analysis reports for {symbol} completed:")
    for (template, name), path in zip(templates, output_paths):
        print(f"   {name}: {path}")

    # 生成报告索引
    index_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{symbol} - 综合分析报告</title>
</head>
<body>
    <h1>{symbol} - 综合分析报告</h1>
    <h2>报告时间: {period}</h2>
    <h2>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</h2>
    <ul>
"""

    for (template, name), path in zip(templates, output_paths):
        filename = os.path.basename(path)
        index_content += f'        <li><a href="{filename}">{name}</a></li>\n'

    index_content += """    </ul>
</body>
</html>"""

    index_path = './output/examples/comprehensive/index.html'
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)

    print(f"   Summary index: {index_path}")


def example_10_json_data_export():
    """Example 10: Export report data as JSON"""
    print("\n" + "="*60)
    print("Example 10: JSON Data Export")
    print("="*60)

    generator = ReportGenerator()

    # 生成报告（同时获取数据）
    config = ReportConfig(
        template_type='performance',
        symbol='0700.HK',
        period='2023-01-01 至 2023-12-31',
        output_dir='./output/examples'
    )

    # 手动生成数据（模拟真实场景）
    data = generator._generate_performance_data(config.symbol, config.period)

    # 保存为JSON
    json_path = './output/examples/report_data.json'
    os.makedirs(os.path.dirname(json_path), exist_ok=True)

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Report data exported: {json_path}")
    print(f"Data fields: {', '.join(data.keys())}")


def main():
    """Main function - Run all examples"""
    print("\n" + "="*60)
    print("  Report Template System Examples")
    print("="*60)
    print(f"Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # Create output directory
    os.makedirs('./output/examples', exist_ok=True)

    # Run examples
    try:
        example_1_basic_performance_report()
        example_2_risk_assessment_report()
        example_3_strategy_comparison_report()
        example_4_executive_summary_report()
        example_5_technical_appendix_report()
        example_6_custom_data_report()
        example_7_batch_generation()
        example_8_multiple_symbols()
        example_9_comprehensive_analysis()
        example_10_json_data_export()

        print("\n" + "="*60)
        print("All examples completed successfully!")
        print("="*60)
        print("\nOutput directory: ./output/examples/")
        print("Documentation: README.md")
        print("Variables guide: TEMPLATE_VARIABLES.md")
        print("="*60)

    except Exception as e:
        print(f"\nExecution failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
