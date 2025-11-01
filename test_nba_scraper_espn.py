#!/usr/bin/env python3
"""
測試 NBA Scraper ESPN API 整合
驗證是否能夠從 ESPN 獲取真實 NBA 比分數據
"""

import asyncio
import json
import sys
import os

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from telegram_bot.sports_scoring.nba_scraper import NBAScraper

async def test_fetch_scores():
    """測試獲取 NBA 比分功能"""
    print("=" * 70)
    print("測試 ESPN NBA Scraper")
    print("=" * 70)

    scraper = NBAScraper()

    print("\n1. 測試 ESPN NBA API 調用...")
    try:
        games = await scraper.fetch_scores()

        print(f"\n✅ 成功獲取 {len(games)} 場比賽")

        if games:
            print("\n2. 顯示比賽數據:")
            print("-" * 70)

            for i, game in enumerate(games, 1):
                print(f"\n比賽 {i}:")
                print(f"  日期: {game.get('date', 'N/A')}")
                print(f"  主隊: {game.get('home_team', 'N/A')}")
                print(f"  客隊: {game.get('away_team', 'N/A')}")
                print(f"  比分: {game.get('home_score', 0)} - {game.get('away_score', 0)}")
                print(f"  狀態: {game.get('status', 'N/A')}")
                print(f"  節次: {game.get('quarter', 'N/A')}")
                print(f"  剩餘時間: {game.get('time_remaining', 'N/A')}")
                print(f"  開始時間: {game.get('start_time', 'N/A')}")
                print(f"  球場: {game.get('venue', 'N/A')}")
                print(f"  聯賽: {game.get('league', 'N/A')}")

            # 驗證數據格式
            print("\n3. 驗證數據格式...")
            required_fields = ['date', 'home_team', 'away_team', 'home_score',
                             'away_score', 'status', 'league']

            for game in games:
                missing_fields = [field for field in required_fields if field not in game]
                if missing_fields:
                    print(f"  ⚠️  比賽缺少字段: {missing_fields}")
                else:
                    print(f"  ✅ 比賽數據格式正確: {game['home_team']} vs {game['away_team']}")

            print("\n4. 完整 JSON 輸出:")
            print(json.dumps(games, indent=2, ensure_ascii=False))

        else:
            print("\n⚠️  未找到任何比賽")
            print("   可能原因:")
            print("   - 今天沒有 NBA 比賽")
            print("   - NBA 休賽期間")
            print("   - ESPN API 返回空數據")

    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        print("\n   這可能是因為:")
        print("   - 網絡連接問題")
        print("   - ESPN API 不可用")
        print("   - API 端點變更")
        print("\n   系統將自動使用備用模擬數據")

        # 測試備用數據
        print("\n5. 測試備用模擬數據...")
        mock_data = scraper._get_mock_data()
        if mock_data:
            print(f"✅ 備用數據正常，提供 {len(mock_data)} 場模擬比賽")
        else:
            print("⚠️  備用數據為空")

    print("\n" + "=" * 70)
    print("測試完成")
    print("=" * 70)

async def test_game_status_parsing():
    """測試比賽狀態解析"""
    print("\n\n測試比賽狀態解析...")

    scraper = NBAScraper()

    test_cases = [
        "Final",
        "In Progress - Q1",
        "In Progress - Q2",
        "In Progress - Q3",
        "In Progress - Q4",
        "In Progress - OT",
        "Halftime",
        "Scheduled",
        "Pre-Game",
    ]

    for status in test_cases:
        parsed = scraper.parse_game_status(status)
        print(f"  {status:25} -> {parsed}")

async def test_team_name_formatting():
    """測試球隊名稱格式化"""
    print("\n\n測試球隊名稱格式化...")

    scraper = NBAScraper()

    test_names = [
        "Los Angeles Lakers",
        "Golden State Warriors",
        "Boston Celtics",
        "Miami Heat",
        "Milwaukee Bucks",
        "Phoenix Suns",
        "Los Angeles Clippers",
        "Denver Nuggets",
        "Philadelphia 76ers",
        "Brooklyn Nets",
    ]

    for name in test_names:
        formatted = scraper.format_team_name(name)
        print(f"  {name:30} -> {formatted}")

async def main():
    """主測試函數"""
    await test_fetch_scores()
    await test_game_status_parsing()
    await test_team_name_formatting()

if __name__ == "__main__":
    asyncio.run(main())
