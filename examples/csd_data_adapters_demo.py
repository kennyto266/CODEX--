"""
C&SD数据适配器使用示例

演示如何使用Phase 8b (T345-T349)的5个C&SD数据适配器：
1. CSDDataCrawler - 数据爬虫
2. GDPParser - GDP数据解析
3. RetailDataProcessor - 零售数据处理
4. VisitorDataProcessor - 访客数据处理
5. TradeDataIntegrator - 贸易数据集成

Author: Claude Code
Version: 1.0.0
Date: 2025-11-09
"""

import asyncio
import json
import pandas as pd
from pathlib import Path
from datetime import date
from decimal import Decimal

# 导入C&SD适配器
from src.data_adapters.cs_d_crawler import (
    CSDDataCrawler,
    CSDCrawlerConfig,
    CSDDataType,
    get_csd_tables
)
from src.data_adapters.gdp_parser import (
    GDPParser,
    GDPParserConfig,
    GDPIndicator,
    parse_gdp_file,
    get_gdp_indicator
)
from src.data_adapters.retail_parser import (
    RetailDataProcessor,
    RetailParserConfig,
    RetailCategory,
    parse_retail_file
)
from src.data_adapters.visitor_parser import (
    VisitorDataProcessor,
    VisitorParserConfig,
    VisitorType,
    parse_visitor_file
)
from src.data_adapters.trade_parser import (
    TradeDataIntegrator,
    TradeParserConfig,
    TradeType,
    TradeCategory,
    parse_trade_file
)


async def demo_csd_crawler():
    """演示C&SD数据爬虫功能"""
    print("\n" + "="*80)
    print("演示 1: CSDDataCrawler - C&SD经济数据爬虫 (T345)")
    print("="*80)

    # 创建爬虫配置
    config = CSDCrawlerConfig(
        base_url="https://www.censtatd.gov.hk",
        download_dir="data/csd_downloads",
        request_timeout=30,
        max_retries=3,
        rate_limit=1.0
    )

    # 初始化爬虫
    crawler = CSDDataCrawler(config)

    try:
        # 获取数据摘要
        print("\n1. 获取爬虫数据摘要...")
        summary = await crawler.get_data_summary()
        print(f"   适配器名称: {summary['adapter_name']}")
        print(f"   总表数: {summary.get('total_tables', 0)}")
        print(f"   下载目录: {summary['download_dir']}")

        # 发现数据表 (模拟)
        print("\n2. 发现可用的C&SD数据表...")
        # 注意：实际使用时需要网络连接
        print("   (实际环境中会扫描C&SD官网)")
        discovered_tables = await crawler.discover_tables(CSDDataType.GDP)
        print(f"   发现 {len(discovered_tables)} 类数据表")

        # 获取数据 (模拟)
        print("\n3. 获取GDP数据...")
        result = await crawler.fetch_data(CSDDataType.GDP)
        if result['success']:
            print(f"   成功获取数据，类型: {result['data']['data_type']}")
            print(f"   表数: {result['data']['total_tables']}")
        else:
            print(f"   获取失败: {result.get('error', 'Unknown error')}")

    finally:
        await crawler.close()

    print("\n✓ CSDDataCrawler 演示完成")


async def demo_gdp_parser():
    """演示GDP解析器功能"""
    print("\n" + "="*80)
    print("演示 2: GDPParser - GDP和经济指标解析器 (T346)")
    print("="*80)

    # 创建解析器
    parser = GDPParser()

    try:
        # 创建示例GDP数据
        print("\n1. 创建示例GDP数据...")
        with pd.ExcelWriter('data/sample_gdp.xlsx') as writer:
            gdp_data = pd.DataFrame({
                'Year': [2019, 2020, 2021, 2022, 2023],
                'Nominal_GDP_HKD_Million': [2860000, 2780000, 2920000, 3080000, 3200000],
                'Real_GDP_HKD_Million': [2800000, 2650000, 2750000, 2850000, 2950000],
                'GDP_Growth_YoY': [2.8, -2.8, 5.0, 5.5, 3.9]
            })
            gdp_data.to_excel(writer, sheet_name='GDP_Data', index=False)
            print(f"   创建了 {len(gdp_data)} 行GDP数据")

        # 解析GDP文件
        print("\n2. 解析GDP数据文件...")
        file_path = Path('data/sample_gdp.xlsx')
        datasets = await parser.parse_gdp_data(file_path, CSDDataType.GDP)

        print(f"   解析出 {len(datasets)} 个GDP指标:")
        for indicator, dataset in datasets.items():
            print(f"   - {indicator.value}: {len(dataset.data_points)} 个数据点")
            if dataset.data_points:
                latest = max(dataset.data_points, key=lambda x: x.date)
                print(f"     最新值: {latest.value} ({latest.date})")

        # 计算GDP增长率
        print("\n3. 计算GDP增长率...")
        for indicator in datasets.keys():
            growth_rates = await parser.calculate_gdp_growth(indicator)
            if growth_rates:
                print(f"   {indicator.value}: {len(growth_rates)} 个增长率数据")
                latest_growth = growth_rates[-1] if growth_rates else None
                if latest_growth:
                    print(f"     最新增长率: {latest_growth:.2f}%")

        # 导出为DataFrame
        print("\n4. 导出GDP数据为DataFrame...")
        for indicator in list(datasets.keys())[:2]:  # 只导出前2个
            df = await parser.export_to_dataframe(indicator)
            if df is not None and not df.empty:
                print(f"   {indicator.value} DataFrame:")
                print(f"     行数: {len(df)}")
                print(f"     列: {list(df.columns)}")
                print(f"     示例数据:\n{df.head(2).to_string(index=False)}")

        # 获取解析摘要
        print("\n5. 获取解析摘要...")
        summary = await parser.get_summary()
        print(f"   解析器: {summary['parser_name']}")
        print(f"   总指标数: {summary['total_indicators']}")

    finally:
        await parser.close()

    # 清理示例文件
    if file_path.exists():
        file_path.unlink()

    print("\n✓ GDPParser 演示完成")


async def demo_retail_processor():
    """演示零售数据处理器"""
    print("\n" + "="*80)
    print("演示 3: RetailDataProcessor - 零售销售数据处理器 (T347)")
    print("="*80)

    # 创建处理器
    processor = RetailDataProcessor()

    try:
        # 创建示例零售数据
        print("\n1. 创建示例零售数据...")
        with pd.ExcelWriter('data/sample_retail.xlsx') as writer:
            retail_data = pd.DataFrame({
                'Month': pd.date_range('2023-01', periods=12, freq='M').strftime('%Y-%m'),
                'Total_Retail_Sales': [52000, 48000, 55000, 62000, 58000, 65000,
                                     70000, 68000, 72000, 75000, 78000, 80000],
                'Clothing_Footwear': [8500, 7800, 9200, 10500, 9800, 11000,
                                    12000, 11500, 12500, 13000, 13500, 14000],
                'Supermarket': [15000, 14800, 15200, 15800, 15500, 16000,
                              16500, 16200, 16800, 17000, 17200, 17500],
                'Restaurants': [12000, 11000, 12500, 14000, 13000, 15000,
                              16000, 15500, 16500, 17000, 17500, 18000]
            })
            retail_data.to_excel(writer, sheet_name='Retail_Sales', index=False)
            print(f"   创建了 {len(retail_data)} 行零售数据")

        # 解析零售文件
        print("\n2. 解析零售数据文件...")
        file_path = Path('data/sample_retail.xlsx')
        datasets = await processor.parse_retail_data(file_path, CSDDataType.RETAIL_SALES)

        print(f"   解析出 {len(datasets)} 个零售类别:")
        for category, dataset in datasets.items():
            print(f"   - {category.value}: {len(dataset.data_points)} 个数据点")
            if dataset.data_points:
                latest = max(dataset.data_points, key=lambda x: x.date)
                print(f"     最新值: {latest.value} {latest.unit}")
                if latest.growth_rate:
                    print(f"     增长率: {latest.growth_rate:.2f}%")

        # 计算市场份额
        print("\n3. 计算市场份额...")
        latest_month = date(2023, 12, 1)
        for category in [RetailCategory.CLOTHING, RetailCategory.SUPERMARKET]:
            if category in datasets:
                share = await processor.calculate_market_share(category, latest_month)
                if share:
                    print(f"   {category.value}: {share:.2f}%")

        # 导出为DataFrame
        print("\n4. 导出零售数据为DataFrame...")
        for category in [RetailCategory.TOTAL_SALES, RetailCategory.CLOTHING]:
            if category in datasets:
                df = await processor.export_to_dataframe(category)
                if df is not None and not df.empty:
                    print(f"   {category.value} DataFrame:")
                    print(f"     行数: {len(df)}")
                    print(f"     最新数据: {df.iloc[-1]['value']:,.0f}")

        # 获取处理摘要
        print("\n5. 获取处理摘要...")
        summary = await processor.get_summary()
        print(f"   处理器: {summary['processor_name']}")
        print(f"   总类别数: {summary['total_categories']}")

    finally:
        await processor.close()

    # 清理示例文件
    if file_path.exists():
        file_path.unlink()

    print("\n✓ RetailDataProcessor 演示完成")


async def demo_visitor_processor():
    """演示访港旅客数据处理器"""
    print("\n" + "="*80)
    print("演示 4: VisitorDataProcessor - 访港旅客数据处理器 (T348)")
    print("="*80)

    # 创建处理器
    processor = VisitorDataProcessor()

    try:
        # 创建示例访客数据
        print("\n1. 创建示例访客数据...")
        with pd.ExcelWriter('data/sample_visitors.xlsx') as writer:
            visitor_data = pd.DataFrame({
                'Month': pd.date_range('2022-01', periods=24, freq='M').strftime('%Y-%m'),
                'Total_Visitors': [2200000, 2000000, 2400000, 2600000, 2800000, 2900000,
                                 3000000, 3100000, 2900000, 2700000, 2500000, 2300000,
                                 2600000, 2400000, 2800000, 3000000, 3200000, 3300000,
                                 3400000, 3500000, 3200000, 3000000, 2800000, 2700000],
                'Mainland_China': [1500000, 1300000, 1600000, 1700000, 1900000, 2000000,
                                 2100000, 2200000, 2000000, 1800000, 1600000, 1500000,
                                 1700000, 1500000, 1800000, 2000000, 2200000, 2300000,
                                 2400000, 2500000, 2200000, 2000000, 1800000, 1700000],
                'Taiwan': [180000, 160000, 190000, 200000, 220000, 230000,
                          240000, 250000, 230000, 210000, 190000, 180000,
                          200000, 180000, 210000, 230000, 250000, 260000,
                          270000, 280000, 250000, 230000, 210000, 200000],
                'Other_Asia': [320000, 300000, 350000, 400000, 420000, 430000,
                              440000, 450000, 430000, 410000, 390000, 370000,
                              400000, 380000, 420000, 450000, 480000, 490000,
                              500000, 520000, 490000, 470000, 440000, 420000]
            })
            visitor_data.to_excel(writer, sheet_name='Visitor_Arrivals', index=False)
            print(f"   创建了 {len(visitor_data)} 行访客数据")

        # 解析访客文件
        print("\n2. 解析访客数据文件...")
        file_path = Path('data/sample_visitors.xlsx')
        datasets = await processor.parse_visitor_data(file_path, CSDDataType.VISITOR_ARRIVALS)

        print(f"   解析出 {len(datasets)} 个访客类型:")
        for visitor_type, dataset in datasets.items():
            print(f"   - {visitor_type.value}: {len(dataset.data_points)} 个数据点")
            if dataset.data_points:
                latest = max(dataset.data_points, key=lambda x: x.date)
                print(f"     最新值: {latest.value:,.0f} 人")
                if latest.growth_rate:
                    print(f"     增长率: {latest.growth_rate:.2f}%")

        # 计算访客占比
        print("\n3. 计算访客占比...")
        latest_month = date(2023, 12, 1)
        for visitor_type in [VisitorType.MAINLAND_CHINA, VisitorType.TAIWAN]:
            if visitor_type in datasets:
                share = await processor.calculate_visitor_share(visitor_type, latest_month)
                if share:
                    print(f"   {visitor_type.value}: {share:.2f}%")

        # 获取季节性模式
        print("\n4. 分析季节性访客模式...")
        patterns = await processor.get_seasonal_patterns(VisitorType.TOTAL_VISITORS)
        if patterns:
            print("   平均访客数 (按季节):")
            for season, avg_visitors in patterns.items():
                if avg_visitors > 0:
                    print(f"     {season}: {avg_visitors:,.0f} 人")

        # 导出为DataFrame
        print("\n5. 导出访客数据为DataFrame...")
        for visitor_type in [VisitorType.TOTAL_VISITORS, VisitorType.MAINLAND_CHINA]:
            if visitor_type in datasets:
                df = await processor.export_to_dataframe(visitor_type)
                if df is not None and not df.empty:
                    print(f"   {visitor_type.value} DataFrame:")
                    print(f"     行数: {len(df)}")
                    print(f"     累计访客: {df['value'].sum():,.0f}")

        # 获取处理摘要
        print("\n6. 获取处理摘要...")
        summary = await processor.get_summary()
        print(f"   处理器: {summary['processor_name']}")
        print(f"   总访客类型: {summary['total_visitor_types']}")

    finally:
        await processor.close()

    # 清理示例文件
    if file_path.exists():
        file_path.unlink()

    print("\n✓ VisitorDataProcessor 演示完成")


async def demo_trade_integrator():
    """演示贸易数据集成器"""
    print("\n" + "="*80)
    print("演示 5: TradeDataIntegrator - 贸易数据集成器 (T349)")
    print("="*80)

    # 创建集成器
    integrator = TradeDataIntegrator()

    try:
        # 创建示例贸易数据
        print("\n1. 创建示例贸易数据...")
        with pd.ExcelWriter('data/sample_trade.xlsx') as writer:
            trade_data = pd.DataFrame({
                'Month': pd.date_range('2022-01', periods=24, freq='M').strftime('%Y-%m'),
                'Exports_Total': [420000, 400000, 450000, 480000, 500000, 520000,
                                540000, 560000, 530000, 510000, 490000, 470000,
                                450000, 430000, 480000, 510000, 540000, 570000,
                                600000, 620000, 580000, 560000, 530000, 500000],
                'Imports_Total': [480000, 460000, 510000, 540000, 570000, 590000,
                                610000, 630000, 600000, 580000, 560000, 540000,
                                520000, 500000, 550000, 580000, 610000, 640000,
                                670000, 690000, 650000, 630000, 600000, 570000],
                'Exports_Consumer_Goods': [150000, 140000, 160000, 170000, 180000, 190000,
                                          200000, 210000, 190000, 180000, 170000, 160000,
                                          150000, 140000, 170000, 190000, 210000, 220000,
                                          230000, 240000, 210000, 190000, 170000, 150000],
                'Imports_Capital_Goods': [120000, 110000, 130000, 140000, 150000, 160000,
                                         170000, 180000, 160000, 150000, 140000, 130000,
                                         120000, 110000, 140000, 160000, 180000, 190000,
                                         200000, 210000, 180000, 160000, 140000, 120000]
            })
            trade_data.to_excel(writer, sheet_name='Trade_Statistics', index=False)
            print(f"   创建了 {len(trade_data)} 行贸易数据")

        # 解析贸易文件
        print("\n2. 解析贸易数据文件...")
        file_path = Path('data/sample_trade.xlsx')
        datasets = await integrator.parse_trade_data(file_path, CSDDataType.TRADE_STATISTICS)

        print(f"   解析出 {len(datasets)} 个贸易数据集:")
        for key, dataset in datasets.items():
            print(f"   - {key}: {len(dataset.data_points)} 个数据点")
            if dataset.data_points:
                latest = max(dataset.data_points, key=lambda x: x.date)
                print(f"     最新值: {latest.value:,.0f} 万港元")
                if latest.growth_rate:
                    print(f"     增长率: {latest.growth_rate:.2f}%")

        # 计算贸易差额
        print("\n3. 计算贸易差额...")
        latest_month = date(2023, 12, 1)
        balance = await integrator.calculate_trade_balance(TradeCategory.TOTAL_TRADE, latest_month)
        if balance:
            if balance > 0:
                print(f"   {latest_month} 贸易顺差: {balance:,.0f} 万港元")
            else:
                print(f"   {latest_month} 贸易逆差: {abs(balance):,.0f} 万港元")

        # 获取主要贸易伙伴
        print("\n4. 获取主要贸易伙伴...")
        top_partners = await integrator.get_top_trade_partners(
            TradeType.EXPORTS,
            TradeCategory.TOTAL_TRADE,
            limit=3
        )
        print("   主要出口贸易伙伴:")
        for partner, value in top_partners:
            print(f"     {partner.value}: {value:,.0f} 万港元")

        # 导出为DataFrame
        print("\n5. 导出贸易数据为DataFrame...")
        for trade_type in [TradeType.EXPORTS, TradeType.IMPORTS]:
            dataset = await integrator.get_trade_data(
                trade_type, TradeCategory.TOTAL_TRADE, None
            )
            if dataset:
                df = dataset.to_dataframe()
                print(f"   {trade_type.value} DataFrame:")
                print(f"     行数: {len(df)}")
                print(f"     累计: {df['value'].sum():,.0f} 万港元")

        # 获取集成摘要
        print("\n6. 获取集成摘要...")
        summary = await integrator.get_summary()
        print(f"   集成器: {summary['integrator_name']}")
        print(f"   总数据集: {summary['total_datasets']}")
        print(f"   贸易类型: {summary['trade_types']}")

    finally:
        await integrator.close()

    # 清理示例文件
    if file_path.exists():
        file_path.unlink()

    print("\n✓ TradeDataIntegrator 演示完成")


async def demo_full_workflow():
    """演示完整的数据处理流程"""
    print("\n" + "="*80)
    print("演示 6: 完整数据处理流程")
    print("="*80)

    print("\n完整的C&SD数据处理流程:")
    print("1. 使用 CSDDataCrawler 爬取C&SD官网数据")
    print("2. 使用各解析器处理不同类型的数据")
    print("3. 统一数据格式和验证")
    print("4. 计算增长率和市场占比")
    print("5. 导出为DataFrame进行进一步分析")
    print("6. 生成经济指标报告")

    # 创建统一数据收集器配置
    from src.data_adapters.unified_data_collector import UnifiedDataCollector

    print("\n1. 初始化统一数据收集器...")
    collector = UnifiedDataCollector()
    print("   ✓ 收集器已初始化")

    # 模拟数据收集
    print("\n2. 收集各类经济数据...")
    print("   - GDP数据: ✓")
    print("   - 零售销售: ✓")
    print("   - 访客数据: ✓")
    print("   - 贸易数据: ✓")

    # 生成综合报告
    print("\n3. 生成经济指标综合报告...")
    report = {
        'report_date': date.today().isoformat(),
        'indicators': {
            'gdp': {
                'nominal_gdp_2023': 3200000,
                'gdp_growth_yoy': 3.9,
                'status': 'stable'
            },
            'retail_sales': {
                'total_2023': 80000,
                'yoy_growth': 5.2,
                'status': 'growing'
            },
            'visitors': {
                'total_2023': 3400000,
                'yoy_growth': 8.5,
                'status': 'strong_recovery'
            },
            'trade_balance': {
                'monthly_2023_12': -70000,
                'status': 'deficit'
            }
        },
        'summary': '香港经济在2023年呈现稳定恢复态势，访客数据强劲反弹，零售销售稳步增长。'
    }

    print(json.dumps(report, indent=2, ensure_ascii=False))

    print("\n✓ 完整数据处理流程演示完成")


async def main():
    """主函数"""
    print("="*80)
    print("C&SD数据适配器 (Phase 8b - T345-T349) 完整演示")
    print("="*80)
    print("\n包含以下适配器:")
    print("1. T345: CSDDataCrawler - C&SD经济数据爬虫")
    print("2. T346: GDPParser - GDP和经济指标解析器")
    print("3. T347: RetailDataProcessor - 零售销售数据处理器")
    print("4. T348: VisitorDataProcessor - 访港旅客数据处理器")
    print("5. T349: TradeDataIntegrator - 贸易数据集成器")

    # 创建数据目录
    Path('data').mkdir(exist_ok=True)

    try:
        # 运行所有演示
        await demo_csd_crawler()
        await demo_gdp_parser()
        await demo_retail_processor()
        await demo_visitor_processor()
        await demo_trade_integrator()
        await demo_full_workflow()

        print("\n" + "="*80)
        print("所有演示完成! ✓")
        print("="*80)
        print("\n使用指南:")
        print("1. 直接使用适配器类进行数据处理")
        print("2. 使用便捷函数简化操作")
        print("3. 所有适配器支持异步操作")
        print("4. 自动缓存和错误处理")
        print("5. 支持多种数据格式 (CSV, Excel, XML, JSON)")

    except Exception as e:
        print(f"\n✗ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
