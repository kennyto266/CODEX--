#!/usr/bin/env python3
"""
T351: 数据异常检测系统 - 使用示例
演示如何使用异常检测器进行各种类型的数据异常检测
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import json

# 导入异常检测模块
from src.data.anomaly_detector import (
    AnomalyDetector,
    StatisticalAnomalyDetector,
    MLAnomalyDetector,
    RuleBasedAnomalyDetector,
    RealtimeAnomalyMonitor,
    AnomalyVisualizer,
    detect_anomalies,
    create_anomaly_detector,
    AnomalyType
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_sample_data():
    """生成示例数据（股票价格）"""
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=365, freq='D')

    # 模拟股票价格走势
    price = 100
    prices = []
    for i in range(365):
        # 添加趋势、季节性和随机波动
        trend = 0.05 * i  # 上升趋势
        seasonal = 5 * np.sin(2 * np.pi * i / 365)  # 季节性
        noise = np.random.normal(0, 2)  # 随机噪声
        price = price + 0.02 + 0.5 * np.random.normal(0, 1)  # 随机游走
        prices.append(price + trend + seasonal + noise)

    # 注入异常
    prices[50] = price + 50  # 单点异常
    prices[100:105] = [price - 30] * 5  # 连续下跌
    prices[200] = np.nan  # 缺失值
    prices[250] = -10  # 负值（异常）
    prices[300] = 0  # 零值（异常）

    return pd.Series(prices, index=dates, name='stock_price')


async def example_1_basic_detection():
    """示例1: 基本异常检测"""
    print("\n" + "="*60)
    print("示例1: 基本异常检测")
    print("="*60)

    # 生成示例数据
    data = generate_sample_data()
    print(f"数据概况: {len(data)} 个数据点")
    print(f"数据范围: {data.min():.2f} - {data.max():.2f}")

    # 创建检测器
    detector = AnomalyDetector({
        'detection_modes': ['statistical', 'rule_based'],
        'statistical': {
            'z_threshold': 2.5,
            'iqr_multiplier': 1.5
        },
        'parallel': True
    })

    # 执行检测
    result = await detector.detect(data, 'timeseries')

    # 打印结果
    print(f"\n检测结果:")
    print(f"  总异常数: {result['summary']['total_anomalies']}")
    print(f"  异常类型分布: {result['summary']['by_type']}")
    print(f"  严重程度分布: {result['summary']['by_severity']}")

    # 显示前5个异常
    if result['anomalies']:
        print(f"\n前5个异常:")
        for i, anomaly in enumerate(result['anomalies'][:5]):
            print(f"  {i+1}. {anomaly['description']}")
            print(f"     索引: {anomaly['index']}, 值: {anomaly['value']:.2f}")
            print(f"     分数: {anomaly['score']:.2f}, 严重程度: {anomaly['severity']}")

    return data, result


async def example_2_statistical_detection():
    """示例2: 统计方法异常检测"""
    print("\n" + "="*60)
    print("示例2: 统计方法异常检测")
    print("="*60)

    data = generate_sample_data()

    # 统计检测器
    detector = StatisticalAnomalyDetector({
        'z_threshold': 2.0,
        'iqr_multiplier': 1.5,
        'mad_multiplier': 3.0
    })

    # Z-Score检测
    print("\nZ-Score异常检测:")
    zscore_anomalies = detector.detect_zscore_anomalies(data, window=30)
    print(f"  检测到 {len(zscore_anomalies)} 个异常")
    for anomaly in zscore_anomalies[:3]:
        print(f"    - 索引 {anomaly.index}: 值 {anomaly.value:.2f}, Z-Score {anomaly.score:.2f}")

    # IQR检测
    print("\nIQR异常检测:")
    iqr_anomalies = detector.detect_iqr_anomalies(data)
    print(f"  检测到 {len(iqr_anomalies)} 个异常")

    # 季节性检测
    print("\n季节性异常检测:")
    seasonal_anomalies = detector.detect_seasonal_anomalies(data, period=30)
    print(f"  检测到 {len(seasonal_anomalies)} 个异常")

    # 综合统计检测
    print("\n综合统计检测:")
    all_anomalies = detector.detect_all(data)
    print(f"  总计检测到 {len(all_anomalies)} 个异常")


async def example_3_ml_detection():
    """示例3: 机器学习异常检测"""
    print("\n" + "="*60)
    print("示例3: 机器学习异常检测")
    print("="*60)

    data = generate_sample_data()

    # ML检测器
    detector = MLAnomalyDetector({
        'contamination': 0.05,
        'random_state': 42
    })

    # Isolation Forest
    print("\nIsolation Forest检测:")
    if_anomalies = detector.detect_isolation_forest(data)
    print(f"  检测到 {len(if_anomalies)} 个异常")
    for anomaly in if_anomalies[:3]:
        print(f"    - 索引 {anomaly.index}: 值 {anomaly.value:.2f}, 分数 {anomaly.score:.2f}")

    # LOF
    print("\nLocal Outlier Factor (LOF)检测:")
    lof_anomalies = detector.detect_lof(data, n_neighbors=20)
    print(f"  检测到 {len(lof_anomalies)} 个异常")

    # DBSCAN
    print("\nDBSCAN聚类检测:")
    dbscan_anomalies = detector.detect_dbscan(data, eps=0.5, min_samples=5)
    print(f"  检测到 {len(dbscan_anomalies)} 个异常")

    # PCA重构
    print("\nPCA重构异常检测:")
    pca_anomalies = detector.detect_pca_reconstruction(data, n_components=0.95)
    print(f"  检测到 {len(pca_anomalies)} 个异常")


async def example_4_rule_based_detection():
    """示例4: 规则基异常检测"""
    print("\n" + "="*60)
    print("示例4: 规则基异常检测")
    print("="*60)

    data = generate_sample_data()

    # 规则检测器
    detector = RuleBasedAnomalyDetector()

    # 负值检测
    print("\n负值检测:")
    negative_anomalies = detector._check_negative_values(data)
    print(f"  检测到 {len(negative_anomalies)} 个负值异常")

    # 零值检测
    print("\n零值检测:")
    zero_anomalies = detector._check_zero_values(data, threshold=0.0)
    print(f"  检测到 {len(zero_anomalies)} 个零值异常")

    # 极端变化检测
    print("\n极端变化检测:")
    change_anomalies = detector._check_extreme_changes(data, threshold=0.1)
    print(f"  检测到 {len(change_anomalies)} 个极端变化异常")

    # 缺失值检测
    print("\n缺失值检测:")
    missing_anomalies = detector._check_missing_values(data)
    print(f"  检测到 {len(missing_anomalies)} 个缺失值异常")

    # 综合规则检测
    print("\n综合规则检测:")
    all_rule_anomalies = detector.detect_all(data, extreme_change_threshold=0.1)
    print(f"  总计检测到 {len(all_rule_anomalies)} 个规则异常")


async def example_5_realtime_monitoring():
    """示例5: 实时异常监控"""
    print("\n" + "="*60)
    print("示例5: 实时异常监控")
    print("="*60)

    # 创建检测器和监控器
    detector = AnomalyDetector({'detection_modes': ['statistical']})
    monitor = RealtimeAnomalyMonitor(detector, window_size=50)

    print("\n模拟实时数据流:")
    alert_count = 0

    # 模拟100个时间点的数据
    for i in range(100):
        # 模拟正常波动
        if i < 50:
            value = 100 + np.random.normal(0, 2)
        # 模拟异常波动
        elif i == 50:
            value = 200  # 突然跳跃
        elif 50 < i < 55:
            value = 90 + np.random.normal(0, 1)  # 连续下跌
        else:
            value = 100 + np.random.normal(0, 2)

        # 更新监控器
        anomalies = await monitor.update(value)

        # 检查告警
        if anomalies:
            alert_count += 1
            if alert_count <= 5:  # 只显示前5个告警
                for anomaly in anomalies:
                    print(f"  时间点 {i}: 检测到异常 - {anomaly.description}")

    print(f"\n实时监控完成，总计触发 {alert_count} 次告警")

    # 获取告警统计
    all_alerts = monitor.get_alerts()
    high_alerts = monitor.get_alerts(severity='high')
    print(f"  高优先级告警: {len(high_alerts)}")


def example_6_visualization():
    """示例6: 异常可视化"""
    print("\n" + "="*60)
    print("示例6: 异常可视化")
    print("="*60)

    # 生成数据并执行检测
    async def run_detection():
        data = generate_sample_data()
        detector = AnomalyDetector({'detection_modes': ['statistical', 'rule_based']})
        result = await detector.detect(data)
        return data, result

    # 同步运行异步函数
    data, result = asyncio.run(run_detection())

    # 创建可视化器
    visualizer = AnomalyVisualizer(figsize=(12, 8))

    # 提取异常列表
    anomalies = []
    for anomaly_dict in result['anomalies']:
        from src.data.anomaly_detector import AnomalyResult
        anomaly = AnomalyResult(
            type=AnomalyType(anomaly_dict['type']),
            score=anomaly_dict['score'],
            confidence=anomaly_dict['confidence'],
            index=anomaly_dict['index'],
            value=anomaly_dict['value'],
            severity=anomaly_dict['severity'],
            description=anomaly_dict['description']
        )
        anomalies.append(anomaly)

    # 保存图表到文件（不显示）
    print("\n生成可视化图表:")
    print("  1. 异常点时间序列图...")
    visualizer.plot_anomalies(
        data, anomalies,
        title='股票价格异常检测结果',
        save_path='examples/anomaly_timeseries.png'
    )

    print("  2. 异常分数分布图...")
    if anomalies:
        visualizer.plot_anomaly_scores(
            data, anomalies,
            title='异常分数分析',
            save_path='examples/anomaly_scores.png'
        )

    print("  3. 检测摘要图...")
    visualizer.plot_detection_summary(
        result,
        save_path='examples/anomaly_summary.png'
    )

    print("\n图表已保存到 examples/ 目录")


async def example_7_comprehensive_analysis():
    """示例7: 综合分析"""
    print("\n" + "="*60)
    print("示例7: 综合分析")
    print("="*60)

    data = generate_sample_data()

    # 使用便捷函数
    print("\n使用便捷函数进行检测...")
    result = await detect_anomalies(
        data,
        schema='financial_timeseries',
        config={
            'detection_modes': ['statistical', 'ml', 'rule_based'],
            'statistical': {'z_threshold': 2.0},
            'ml': {'contamination': 0.05},
            'parallel': True
        }
    )

    # 详细分析结果
    print(f"\n详细分析结果:")
    print(f"  检测时间: {result['timestamp']}")
    print(f"  数据模式: {result.get('schema', 'N/A')}")
    print(f"  总异常数: {result['summary']['total_anomalies']}")

    print(f"\n异常类型分析:")
    for type_name, count in result['summary']['by_type'].items():
        percentage = (count / result['summary']['total_anomalies']) * 100
        print(f"  {type_name}: {count} ({percentage:.1f}%)")

    print(f"\n严重程度分析:")
    for severity, count in result['summary']['by_severity'].items():
        percentage = (count / result['summary']['total_anomalies']) * 100
        print(f"  {severity}: {count} ({percentage:.1f}%)")

    # 分析异常的时间分布
    if result['anomalies']:
        timestamps = [datetime.fromisoformat(a['timestamp'].replace('Z', '+00:00'))
                     for a in result['anomalies']]
        dates = [ts.date() for ts in timestamps]
        unique_dates = list(set(dates))
        print(f"\n时间分布:")
        print(f"  异常出现在 {len(unique_dates)} 个不同日期")
        print(f"  最早异常: {min(dates)}")
        print(f"  最晚异常: {max(dates)}")

        # 按星期几分组
        weekdays = [ts.weekday() for ts in timestamps]
        weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        weekday_counts = {name: weekdays.count(i) for i, name in enumerate(weekday_names)}
        print(f"\n按星期几分组:")
        for day, count in weekday_counts.items():
            if count > 0:
                print(f"  {day}: {count} 个异常")

    # 保存结果到文件
    with open('examples/anomaly_report.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n详细报告已保存到: examples/anomaly_report.json")

    return result


async def example_8_custom_configuration():
    """示例8: 自定义配置"""
    print("\n" + "="*60)
    print("示例8: 自定义配置")
    print("="*60)

    data = generate_sample_data()

    # 不同的配置
    configs = [
        {
            'name': '宽松检测',
            'config': {
                'detection_modes': ['statistical'],
                'statistical': {
                    'z_threshold': 3.5,  # 更宽松的阈值
                    'iqr_multiplier': 2.0
                }
            }
        },
        {
            'name': '严格检测',
            'config': {
                'detection_modes': ['statistical', 'rule_based'],
                'statistical': {
                    'z_threshold': 1.5,  # 更严格的阈值
                    'iqr_multiplier': 1.0
                }
            }
        },
        {
            'name': 'ML检测',
            'config': {
                'detection_modes': ['ml'],
                'ml': {
                    'contamination': 0.02,  # 2%异常率
                    'random_state': 42
                }
            }
        }
    ]

    print("\n不同配置下的检测结果:")
    for cfg in configs:
        detector = AnomalyDetector(cfg['config'])
        result = await detector.detect(data)

        print(f"\n  {cfg['name']}:")
        print(f"    异常数量: {result['summary']['total_anomalies']}")
        print(f"    高优先级: {result['summary']['by_severity'].get('high', 0)}")


async def main():
    """主函数 - 运行所有示例"""
    print("="*60)
    print("T351: 数据异常检测系统 - 使用示例")
    print("="*60)

    try:
        # 示例1: 基本检测
        await example_1_basic_detection()

        # 示例2: 统计检测
        await example_2_statistical_detection()

        # 示例3: ML检测
        await example_3_ml_detection()

        # 示例4: 规则检测
        await example_4_rule_based_detection()

        # 示例5: 实时监控
        await example_5_realtime_monitoring()

        # 示例6: 可视化
        example_6_visualization()

        # 示例7: 综合分析
        await example_7_comprehensive_analysis()

        # 示例8: 自定义配置
        await example_8_custom_configuration()

        print("\n" + "="*60)
        print("所有示例运行完成!")
        print("="*60)
        print("\n生成的输出文件:")
        print("  - examples/anomaly_timeseries.png")
        print("  - examples/anomaly_scores.png")
        print("  - examples/anomaly_summary.png")
        print("  - examples/anomaly_report.json")

    except Exception as e:
        logger.error(f"运行示例时发生错误: {str(e)}", exc_info=True)
        raise


if __name__ == '__main__':
    # 运行主函数
    asyncio.run(main())
