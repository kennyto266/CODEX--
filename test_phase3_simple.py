#!/usr/bin/env python3
import sys
import asyncio

sys.path.insert(0, '/c/Users/Penguin8n/CODEX--/CODEX--/src')
sys.path.insert(0, '/c/Users/Penguin8n/CODEX--/CODEX--/src/telegram_bot')

print("Phase 3 升級測試")
print("=" * 60)

# 測試1: 天氣服務升級
print("\n測試 1: 檢查天氣服務升級...")
try:
    from weather_service import HKOWeatherService, weather_service
    print(f"[PASS] 天氣服務類: {type(weather_service).__name__}")
    print(f"[PASS] HKOWeatherService 存在: {HKOWeatherService is not None}")
    
    # 測試緩存
    if hasattr(weather_service, 'cache'):
        print(f"[PASS] 緩存機制存在，TTL: {weather_service.cache_ttl}秒")
except Exception as e:
    print(f"[FAIL] 天氣服務錯誤: {e}")

# 測試2: 足智彩適配器
print("\n測試 2: 檢查足智彩適配器...")
try:
    from sports_scoring.joker_sports_adapter import joker_adapter
    print(f"[PASS] 足智彩適配器: {type(joker_adapter).__name__}")
    print(f"[PASS] 適配器名稱: {joker_adapter.name}")
except Exception as e:
    print(f"[FAIL] 足智彩適配器錯誤: {e}")

# 測試3: 足球爬蟲升級
print("\n測試 3: 檢查足球爬蟲升級...")
try:
    from sports_scoring.football_scraper import FootballScraper
    scraper = FootballScraper()
    print(f"[PASS] FootballScraper 存在")
    print(f"[PASS] 包含joker_adapter: {hasattr(scraper, 'joker_adapter')}")
except Exception as e:
    print(f"[FAIL] 足球爬蟲錯誤: {e}")

print("\n" + "=" * 60)
print("Phase 3 檢查完成")
print("=" * 60)
