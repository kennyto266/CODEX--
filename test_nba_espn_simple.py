#!/usr/bin/env python3
"""
簡化版 NBA Scraper ESPN API 測試
避免編碼問題，專注於功能測試
"""

import asyncio
import json
import sys
import os

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from telegram_bot.sports_scoring.nba_scraper import NBAScraper

async def test_nba_scraper():
    """測試 NBA Scraper"""
    print("=" * 70)
    print("Testing ESPN NBA Scraper Integration")
    print("=" * 70)

    scraper = NBAScraper()

    print("\n[1] Testing ESPN NBA API call...")
    try:
        games = await scraper.fetch_scores()

        print(f"\n[SUCCESS] Retrieved {len(games)} games")

        if games:
            print("\n[2] Game Data:")
            print("-" * 70)

            for i, game in enumerate(games, 1):
                print(f"\nGame {i}:")
                print(f"  Date: {game.get('date', 'N/A')}")
                print(f"  Home: {game.get('home_team', 'N/A')}")
                print(f"  Away: {game.get('away_team', 'N/A')}")
                print(f"  Score: {game.get('home_score', 0)} - {game.get('away_score', 0)}")
                print(f"  Status: {game.get('status', 'N/A')}")
                print(f"  Quarter: {game.get('quarter', 'N/A')}")
                print(f"  Time: {game.get('time_remaining', 'N/A')}")
                print(f"  Venue: {game.get('venue', 'N/A')}")

            print("\n[3] Full JSON Output:")
            print(json.dumps(games, indent=2, ensure_ascii=False))

            # 驗證數據格式
            print("\n[4] Data Format Validation:")
            required_fields = ['date', 'home_team', 'away_team', 'home_score',
                             'away_score', 'status', 'league']

            all_valid = True
            for game in games:
                missing = [f for f in required_fields if f not in game]
                if missing:
                    print(f"  [WARNING] Game missing fields: {missing}")
                    all_valid = False

            if all_valid:
                print(f"  [SUCCESS] All {len(games)} games have valid format")

        else:
            print("\n[INFO] No games found")
            print("  Possible reasons:")
            print("  - No NBA games today")
            print("  - Off-season")
            print("  - ESPN API returned empty data")

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        print("\n  This may be due to:")
        print("  - Network connection issue")
        print("  - ESPN API unavailable")
        print("  - API endpoint changed")
        print("\n  System will fallback to mock data")

        # 測試備用數據
        print("\n[5] Testing fallback mock data...")
        mock_data = scraper._get_mock_data()
        if mock_data:
            print(f"  [SUCCESS] Fallback data working, {len(mock_data)} mock games")
        else:
            print("  [WARNING] Fallback data empty")

    print("\n" + "=" * 70)
    print("Test Complete")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_nba_scraper())
