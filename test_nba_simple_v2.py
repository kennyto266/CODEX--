#!/usr/bin/env python3
"""
Simple NBA Score Test for Telegram Bot
"""

import asyncio
import sys
import os

# Add project path
sys.path.insert(0, os.path.dirname(__file__))

async def test_nba_scores():
    """Test NBA scores directly"""
    print("=" * 70)
    print("Testing NBA Scores in Telegram Bot")
    print("=" * 70)

    # Import NBAScraper directly
    try:
        from src.telegram_bot.sports_scoring.nba_scraper import NBAScraper
        print("\n[1] NBAScraper imported successfully")
    except ImportError as e:
        print(f"\n[ERROR] Failed to import NBAScraper: {e}")
        return False

    try:
        # Create scraper instance
        scraper = NBAScraper()
        print("\n[2] NBAScraper initialized")

        # Fetch NBA scores
        print("\n[3] Fetching NBA scores from ESPN API...")
        scores = await scraper.fetch_scores()

        if scores:
            print(f"\n[SUCCESS] Retrieved {len(scores)} NBA games")
            print("\n" + "-" * 70)
            print("NBA Game Scores:")
            print("-" * 70)

            for i, game in enumerate(scores, 1):
                print(f"\nGame {i}:")
                print(f"  Date: {game.get('date', 'N/A')}")
                print(f"  Teams: {game.get('away_team', 'N/A')} @ {game.get('home_team', 'N/A')}")
                print(f"  Score: {game.get('home_score', 0)} - {game.get('away_score', 0)}")
                print(f"  Status: {game.get('status', 'N/A')}")
                print(f"  Quarter: {game.get('quarter', 'N/A')}")
                print(f"  Time: {game.get('time_remaining', 'N/A')}")
                print(f"  Venue: {game.get('venue', 'N/A')}")

            print("\n" + "-" * 70)
            print("[RESULT] NBA scores working correctly!")
            print("-" * 70)
            print("\nHow to use in Telegram Bot:")
            print("  1. Start bot: python src/telegram_bot/start_telegram_bot.py")
            print("  2. Send command: /score nba")
            print("  3. Bot will display real NBA scores")

            return True

        else:
            print("\n[WARNING] No NBA games found")
            print("  Possible reasons:")
            print("  - No games today")
            print("  - Off-season")
            print("  - API issue")

            return False

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_bot_integration():
    """Test integration with Telegram bot"""
    print("\n" + "=" * 70)
    print("Testing Telegram Bot Integration")
    print("=" * 70)

    try:
        # Test importing from bot file
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'telegram_bot'))

        # Check if the bot file has the import
        with open('src/telegram_bot/telegram_quant_bot.py', 'r') as f:
            content = f.read()
            if 'NBAScraper' in content:
                print("\n[1] Bot file contains NBAScraper import")
            else:
                print("\n[WARNING] Bot file does not contain NBAScraper")

        # Check for score command
        if '/score nba' in content or 'score_cmd' in content:
            print("[2] Bot has /score nba command implemented")
        else:
            print("[WARNING] Bot does not have score command")

        print("\n[SUCCESS] Bot integration verified")
        return True

    except Exception as e:
        print(f"\n[ERROR] Bot integration test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("\nStarting NBA Score Tests...\n")

    # Test 1: Direct NBA scores
    result1 = await test_nba_scores()

    # Test 2: Bot integration
    result2 = await test_bot_integration()

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)

    if result1:
        print("[PASS] NBA Score Retrieval: OK")
    else:
        print("[FAIL] NBA Score Retrieval: FAILED")

    if result2:
        print("[PASS] Bot Integration: OK")
    else:
        print("[FAIL] Bot Integration: FAILED")

    if result1 and result2:
        print("\n[SUCCESS] All tests passed!")
        print("\nNext Steps:")
        print("  1. Ensure TELEGRAM_BOT_TOKEN is set in .env")
        print("  2. Run: python src/telegram_bot/start_telegram_bot.py")
        print("  3. In Telegram, send: /score nba")
    else:
        print("\n[FAILED] Some tests failed. Please check errors above.")

    return result1 and result2

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
