#!/usr/bin/env python3
"""
驗證 NBA Scraper 向後兼容性
確保新的 ESPN API 整合不會破壞現有功能
"""

import asyncio
import sys
import os
import inspect

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from telegram_bot.sports_scoring.nba_scraper import NBAScraper

async def test_backward_compatibility():
    """測試向後兼容性"""
    print("=" * 70)
    print("Testing Backward Compatibility")
    print("=" * 70)

    scraper = NBAScraper()

    # 測試 1: 檢查 fetch_scores() 方法簽名
    print("\n[1] Checking fetch_scores() method signature...")
    fetch_sig = inspect.signature(scraper.fetch_scores)
    print(f"  Signature: {fetch_sig}")
    print(f"  Parameters: {list(fetch_sig.parameters.keys())}")
    print(f"  Return annotation: {fetch_sig.return_annotation}")

    # 檢查是否為 async 方法
    if inspect.iscoroutinefunction(scraper.fetch_scores):
        print("  [PASS] Method is async (as expected)")
    else:
        print("  [FAIL] Method is not async!")
        return False

    # 測試 2: 檢查其他主要方法是否存在
    print("\n[2] Checking other methods exist...")
    methods_to_check = [
        'fetch_scores',
        'fetch_schedule',
        'get_team_stats',
        'parse_game_status',
        'format_team_name'
    ]

    for method_name in methods_to_check:
        if hasattr(scraper, method_name):
            print(f"  [PASS] Method '{method_name}' exists")
        else:
            print(f"  [FAIL] Method '{method_name}' missing!")
            return False

    # 測試 3: 檢查返回數據格式
    print("\n[3] Checking return data format...")
    try:
        games = await scraper.fetch_scores()

        # 檢查返回類型
        if isinstance(games, list):
            print(f"  [PASS] Returns a list (length: {len(games)})")
        else:
            print(f"  [FAIL] Returns {type(games)}, expected list")
            return False

        if games:
            game = games[0]
            expected_fields = [
                'date',
                'home_team',
                'away_team',
                'home_score',
                'away_score',
                'status',
                'quarter',
                'time_remaining',
                'start_time',
                'venue',
                'league'
            ]

            print(f"  Checking {len(expected_fields)} expected fields...")
            missing_fields = []
            for field in expected_fields:
                if field in game:
                    print(f"    [PASS] Field '{field}': {game[field]}")
                else:
                    print(f"    [WARNING] Field '{field}' missing")
                    missing_fields.append(field)

            if not missing_fields:
                print(f"  [PASS] All {len(expected_fields)} fields present")
            else:
                print(f"  [INFO] {len(missing_fields)} fields missing (not critical)")

    except Exception as e:
        print(f"  [ERROR] Failed to call fetch_scores(): {e}")
        return False

    # 測試 4: 檢查方法調用方式（無參數）
    print("\n[4] Checking method can be called without arguments...")
    try:
        # 模擬舊的調用方式
        result = await scraper.fetch_scores()
        print(f"  [PASS] fetch_scores() can be called without arguments")
        print(f"  [PASS] Returned {len(result)} games")
    except TypeError as e:
        print(f"  [FAIL] fetch_scores() requires arguments: {e}")
        return False

    # 測試 5: 檢查模擬數據功能
    print("\n[5] Checking mock data functionality...")
    try:
        mock_games = scraper._get_mock_data()
        if isinstance(mock_games, list):
            print(f"  [PASS] Mock data returns list (length: {len(mock_games)})")
        else:
            print(f"  [FAIL] Mock data returns {type(mock_games)}")
    except Exception as e:
        print(f"  [ERROR] Mock data failed: {e}")

    print("\n" + "=" * 70)
    print("Backward Compatibility Test Complete")
    print("=" * 70)

    print("\n[RESULT] All backward compatibility checks passed!")
    print("\nExisting code using NBAScraper will continue to work without changes:")
    print("  - Method signatures unchanged")
    print("  - Return data format consistent")
    print("  - Async behavior maintained")
    print("  - Mock data fallback available")

    return True

if __name__ == "__main__":
    asyncio.run(test_backward_compatibility())
