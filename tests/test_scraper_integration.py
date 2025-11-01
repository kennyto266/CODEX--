"""
爬虫集成测试脚本

测试替代数据收集器的爬虫功能是否能成功工作
"""

import asyncio
from datetime import date
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.data_adapters.alternative_data_service import AlternativeDataService
from src.data_adapters.hkex_data_collector import HKEXDataCollector
from src.data_adapters.gov_data_collector import GovDataCollector
from src.data_adapters.kaggle_data_collector import KaggleDataCollector


async def test_hkex_scraper():
    """测试HKEX爬虫"""
    print("\n" + "="*60)
    print("测试 HKEX 数据收集器")
    print("="*60)

    collector = HKEXDataCollector(mode="mock")

    try:
        # 连接
        connected = await collector.connect()
        print(f"✅ 连接状态: {connected}")

        # 列出指标
        indicators = await collector.list_indicators()
        print(f"✅ 支持指标数: {len(indicators)}")
        for ind in indicators[:3]:
            print(f"   - {ind}")

        # 获取数据
        print("\n[获取数据]")
        data = await collector.fetch_data(
            "hsi_futures_volume", date(2024, 1, 1), date(2024, 1, 31)
        )
        print(f"✅ 数据行数: {len(data)}")
        print(f"✅ 数据列: {list(data.columns)}")
        print(f"✅ 首行数据:")
        print(data.head(1).to_string())

        # 获取实时数据
        print("\n[实时数据]")
        realtime = await collector.get_realtime_data("hsi_implied_volatility")
        print(f"✅ 隐含波动率: {realtime['value']:.2f}%")
        print(f"✅ 时间戳: {realtime['timestamp']}")

        # 健康检查
        print("\n[健康检查]")
        health = await collector.health_check()
        print(f"✅ 状态: {health['status']}")
        print(f"✅ 已连接: {health['is_connected']}")
        print(f"✅ 缓存大小: {health['cache_size']}")

        await collector.disconnect()
        return True

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_gov_scraper():
    """测试政府数据爬虫"""
    print("\n" + "="*60)
    print("测试 政府数据 收集器")
    print("="*60)

    collector = GovDataCollector(mode="mock")

    try:
        # 连接
        connected = await collector.connect()
        print(f"✅ 连接状态: {connected}")

        # 列出指标
        indicators = await collector.list_indicators()
        print(f"✅ 支持指标数: {len(indicators)}")
        for ind in indicators[:3]:
            print(f"   - {ind}")

        # 获取HIBOR数据
        print("\n[HIBOR 数据]")
        hibor_data = await collector.fetch_data(
            "hibor_3m", date(2024, 1, 1), date(2024, 1, 31)
        )
        print(f"✅ 数据行数: {len(hibor_data)}")
        print(f"✅ 平均利率: {hibor_data['value'].mean():.3f}%")

        # 获取访客数据
        print("\n[访客数据]")
        visitor_data = await collector.fetch_data(
            "visitor_arrivals_total", date(2024, 1, 1), date(2024, 12, 31)
        )
        print(f"✅ 数据行数: {len(visitor_data)}")
        print(f"✅ 总访客数: {visitor_data['value'].sum():,.0f}")

        # 实时数据
        print("\n[实时数据]")
        realtime = await collector.get_realtime_data("unemployment_rate")
        print(f"✅ 失业率: {realtime['value']:.1f}%")

        await collector.disconnect()
        return True

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_kaggle_scraper():
    """测试Kaggle爬虫"""
    print("\n" + "="*60)
    print("测试 Kaggle 数据 收集器")
    print("="*60)

    collector = KaggleDataCollector(mode="mock")

    try:
        # 连接
        connected = await collector.connect()
        print(f"✅ 连接状态: {connected}")

        # 列出指标
        indicators = await collector.list_indicators()
        print(f"✅ 支持指标数: {len(indicators)}")
        for ind in indicators[:3]:
            print(f"   - {ind}")

        # 获取GDP数据
        print("\n[GDP 数据]")
        gdp_data = await collector.fetch_data(
            "hong_kong_gdp", date(2024, 1, 1), date(2024, 12, 31)
        )
        print(f"✅ 数据行数: {len(gdp_data)}")
        print(f"✅ 平均GDP: HKD {gdp_data['value'].mean():,.0f}")

        # 获取股票数据
        print("\n[股票数据]")
        hsi_data = await collector.fetch_data(
            "hsi_historical", date(2024, 1, 1), date(2024, 12, 31)
        )
        print(f"✅ 数据行数: {len(hsi_data)}")
        print(f"✅ 平均指数: {hsi_data['value'].mean():.0f}")

        await collector.disconnect()
        return True

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_service():
    """测试服务整合"""
    print("\n" + "="*60)
    print("测试 替代数据 服务")
    print("="*60)

    service = AlternativeDataService()

    try:
        # 初始化
        print("[初始化服务]")
        initialized = await service.initialize(mode="mock")
        print(f"✅ 初始化: {initialized}")

        # 列出适配器
        print("\n[适配器列表]")
        adapters = await service.list_adapters()
        print(f"✅ 可用适配器: {adapters}")

        # 从多个适配器获取数据
        print("\n[跨适配器数据获取]")

        # HKEX 数据
        hkex_data = await service.get_data(
            "hkex", "hsi_futures_volume", date(2024, 1, 1), date(2024, 1, 31)
        )
        print(f"✅ HKEX 数据行数: {len(hkex_data)}")

        # 政府数据
        gov_data = await service.get_data(
            "government", "hibor_overnight", date(2024, 1, 1), date(2024, 1, 31)
        )
        print(f"✅ 政府 数据行数: {len(gov_data)}")

        # Kaggle 数据
        kg_data = await service.get_data(
            "kaggle", "hong_kong_gdp", date(2024, 1, 1), date(2024, 12, 31)
        )
        print(f"✅ Kaggle 数据行数: {len(kg_data)}")

        # 健康检查
        print("\n[整体健康检查]")
        health = await service.health_check()
        print(f"✅ 总体状态: {health['overall_status']}")
        print(f"✅ 活跃适配器: {len(health['adapters'])}")

        for adapter_name, status in health['adapters'].items():
            print(f"   - {adapter_name}: {status.get('status', 'unknown')}")

        # 清理
        await service.cleanup()
        print(f"\n✅ 服务清理完成")
        return True

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("替代数据收集器 爬虫集成测试")
    print("="*60)

    results = {
        "HKEX 收集器": await test_hkex_scraper(),
        "政府数据 收集器": await test_gov_scraper(),
        "Kaggle 收集器": await test_kaggle_scraper(),
        "数据服务": await test_service(),
    }

    # 汇总结果
    print("\n" + "="*60)
    print("测试汇总")
    print("="*60)

    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name:.<40} {status}")

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"\n总体: {passed}/{total} 通过")

    if passed == total:
        print("\n[SUCCESS] 所有测试通过！爬虫功能可以正常工作。")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
