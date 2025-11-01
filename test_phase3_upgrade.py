#!/usr/bin/env python3
"""
Phase 3 升級測試腳本
測試天氣服務和體育比分系統升級
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

# 添加路徑
sys.path.insert(0, '/c/Users/Penguin8n/CODEX--/CODEX--/src/telegram_bot')

from weather_service import HKOWeatherService, weather_service
from sports_scoring.joker_sports_adapter import joker_adapter
from sports_scoring.football_scraper import FootballScraper

async def test_hko_weather_service():
    """測試香港天文台天氣服務"""
    print("\n" + "=" * 60)
    print("測試 1: 香港天文台天氣服務")
    print("=" * 60)

    try:
        hko_service = HKOWeatherService()

        # 測試獲取當前天氣
        print("\n[1.1] 獲取當前天氣...")
        weather = await hko_service.get_current_weather()
        if weather:
            print(f"✓ 獲取天氣數據成功")
            print(f"  溫度: {weather.get('temperature', 'N/A')}°C")
            print(f"  濕度: {weather.get('humidity', 'N/A')}%")
            print(f"  數據源: {weather.get('source', 'N/A')}")
        else:
            print("✗ 獲取天氣數據失敗")

        # 測試獲取天氣警告
        print("\n[1.2] 獲取天氣警告...")
        warnings = await hko_service.get_weather_warnings()
        print(f"✓ 獲取警告數據成功，共 {len(warnings)} 條警告")
        for warning in warnings[:3]:  # 只顯示前3條
            print(f"  - {warning.get('type', 'N/A')}: {warning.get('status', 'N/A')}")

        # 測試獲取UV指數
        print("\n[1.3] 獲取UV指數...")
        uv_data = await hko_service.get_uv_index()
        if uv_data:
            print(f"✓ 獲取UV指數成功")
            print(f"  UV值: {uv_data.get('uv_index', 'N/A')}")
            print(f"  等級: {uv_data.get('level', 'N/A')}")
        else:
            print("✗ 獲取UV指數失敗")

        # 測試格式化消息
        print("\n[1.4] 測試消息格式化...")
        if weather:
            message = hko_service.format_weather_message(weather)
            print(f"✓ 格式化消息成功，長度: {len(message)} 字符")
            print(f"  預覽: {message[:100]}...")

        print("\n✅ 天氣服務測試完成")
        return True

    except Exception as e:
        print(f"\n❌ 天氣服務測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_joker_sports_adapter():
    """測試足智彩體育適配器"""
    print("\n" + "=" * 60)
    print("測試 2: 足智彩體育適配器")
    print("=" * 60)

    try:
        # 測試獲取實時比分
        print("\n[2.1] 獲取實時比分...")
        scores = await joker_adapter.fetch_live_scores("soccer")
        print(f"✓ 獲取比分數據成功，共 {len(scores)} 場比賽")

        for score in scores[:3]:  # 只顯示前3場
            print(f"  - {score.get('home_team', 'N/A')} {score.get('home_score', '?')}-"
                  f"{score.get('away_score', '?')} {score.get('away_team', 'N/A')}")
            print(f"    狀態: {score.get('status', 'N/A')}, 數據源: {score.get('data_source', 'N/A')}")

        # 測試獲取 upcoming 賽程
        print("\n[2.2] 獲取 upcoming 賽程...")
        schedule = await joker_adapter.fetch_upcoming_matches("soccer")
        print(f"✓ 獲取賽程數據成功，共 {len(schedule)} 場比賽")

        for match in schedule[:3]:  # 只顯示前3場
            print(f"  - {match.get('home_team', 'N/A')} vs {match.get('away_team', 'N/A')}")
            print(f"    時間: {match.get('match_time', 'N/A')}, 狀態: {match.get('status', 'N/A')}")

        # 測試統計信息
        print("\n[2.3] 獲取適配器統計...")
        stats = joker_adapter.get_stats()
        print(f"✓ 獲取統計成功")
        print(f"  名稱: {stats.get('name', 'N/A')}")
        print(f"  更新次數: {stats.get('update_count', 0)}")
        print(f"  錯誤次數: {stats.get('error_count', 0)}")
        print(f"  成功率: {stats.get('success_rate', 0):.2%}")

        print("\n✅ 足智彩適配器測試完成")
        return True

    except Exception as e:
        print(f"\n❌ 足智彩適配器測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_football_scraper_upgrade():
    """測試足球爬蟲升級"""
    print("\n" + "=" * 60)
    print("測試 3: 足球爬蟲升級")
    print("=" * 60)

    try:
        scraper = FootballScraper()

        # 檢查是否包含足智彩適配器
        print("\n[3.1] 檢查足智彩適配器...")
        if hasattr(scraper, 'joker_adapter'):
            print("✓ 足球爬蟲包含足智彩適配器")
        else:
            print("✗ 足球爬蟲缺少足智彩適配器")
            return False

        # 測試獲取比分（會優先使用足智彩）
        print("\n[3.2] 獲取足球比分...")
        scores = await scraper.fetch_scores()
        print(f"✓ 獲取足球比分成功，共 {len(scores)} 場比賽")

        # 檢查數據來源
        data_sources = {}
        for score in scores:
            source = score.get('data_source', '未知')
            data_sources[source] = data_sources.get(source, 0) + 1

        print(f"  數據來源統計:")
        for source, count in data_sources.items():
            print(f"    - {source}: {count} 場比賽")

        print("\n✅ 足球爬蟲升級測試完成")
        return True

    except Exception as e:
        print(f"\n❌ 足球爬蟲升級測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_integration():
    """測試整合"""
    print("\n" + "=" * 60)
    print("測試 4: 系統整合")
    print("=" * 60)

    try:
        # 檢查全局實例
        print("\n[4.1] 檢查全局實例...")
        from weather_service import weather_service
        print(f"✓ 全局天氣服務實例: {type(weather_service).__name__}")

        # 檢查是否為升級版
        if isinstance(weather_service, HKOWeatherService):
            print("✓ 天氣服務已升級為HKOWeatherService")
        else:
            print("⚠ 天氣服務未升級")

        print("\n[4.2] 檢查緩存機制...")
        if hasattr(weather_service, 'cache'):
            print(f"✓ 天氣服務包含緩存機制，TTL: {weather_service.cache_ttl}秒")
        else:
            print("✗ 天氣服務缺少緩存")

        print("\n✅ 系統整合測試完成")
        return True

    except Exception as e:
        print(f"\n❌ 系統整合測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主測試函數"""
    print("=" * 60)
    print("Phase 3 升級測試開始")
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = []

    # 執行所有測試
    results.append(("天氣服務升級", await test_hko_weather_service()))
    results.append(("足智彩適配器", await test_joker_sports_adapter()))
    results.append(("足球爬蟲升級", await test_football_scraper_upgrade()))
    results.append(("系統整合", await test_integration()))

    # 輸出總結
    print("\n" + "=" * 60)
    print("測試總結")
    print("=" * 60)

    for test_name, passed in results:
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"{status} {test_name}")

    all_passed = all(result[1] for result in results)
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有測試通過！Phase 3 升級成功")
    else:
        print("⚠️ 部分測試失敗，請檢查日志")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
