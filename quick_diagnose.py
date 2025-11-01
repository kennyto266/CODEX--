#!/usr/bin/env python3
"""
Quick Bot Version Diagnose
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(__file__))

def main():
    print("=" * 70)
    print("NBA Scraper Quick Diagnose")
    print("=" * 70)

    # Check file
    scraper_path = "src/telegram_bot/sports_scoring/nba_scraper.py"
    print(f"\n[1] Checking file: {scraper_path}")

    if not os.path.exists(scraper_path):
        print("    [ERROR] File not found!")
        return False

    with open(scraper_path, 'r') as f:
        content = f.read()

    checks = [
        ("import aiohttp", "aiohttp support"),
        ("site/v2/sports/basketball/nba/scoreboard", "ESPN API URL"),
        ("_fetch_from_espn", "Real API call"),
        ("_parse_espn_response", "Data parsing"),
    ]

    all_ok = True
    for check, desc in checks:
        if check in content:
            print(f"    [OK] {desc}")
        else:
            print(f"    [FAIL] {desc}")
            all_ok = False

    # Test import
    print("\n[2] Testing import...")
    try:
        from src.telegram_bot.sports_scoring.nba_scraper import NBAScraper
        print("    [OK] Import successful")

        # Test instance
        scraper = NBAScraper()
        print("    [OK] Instance created")

        # Test fetch
        print("\n[3] Testing fetch_scores...")
        async def test():
            scores = await scraper.fetch_scores()
            return scores

        scores = asyncio.run(test())

        if scores:
            print(f"    [OK] Got {len(scores)} games")
            print("\n    Sample game:")
            game = scores[0]
            print(f"      {game.get('away_team')} @ {game.get('home_team')}")
            print(f"      Score: {game.get('home_score')}-{game.get('away_score')}")
            print(f"      Status: {game.get('status')}")
        else:
            print("    [WARN] No games returned")
            all_ok = False

    except Exception as e:
        print(f"    [ERROR] {e}")
        all_ok = False

    print("\n" + "=" * 70)
    if all_ok:
        print("[SUCCESS] All checks passed!")
        print("\nIf bot still shows old data, RESTART the bot:")
        print("  1. Kill bot process: pkill -f telegram")
        print("  2. Start bot: python src/telegram_bot/start_telegram_bot.py")
    else:
        print("[FAIL] Some checks failed")
    print("=" * 70)

    return all_ok

if __name__ == "__main__":
    main()
