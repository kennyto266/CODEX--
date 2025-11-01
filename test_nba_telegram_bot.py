#!/usr/bin/env python3
"""
測試 Telegram Bot 中的 NBA 比分功能
模擬真實的 Telegram bot 環境
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# 添加項目路徑
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 導入體育比分系統
try:
    from src.telegram_bot.sports_scoring import (
        NBAScraper,
        FootballScraper,
        CacheManager,
        DataProcessor
    )
    SPORTS_SCORING_OK = True
    logger.info("✅ 體育比分系統加載成功")
except ImportError as e:
    logger.error(f"❌ 體育比分系統加載失敗: {e}")
    SPORTS_SCORING_OK = False

async def test_nba_score_command():
    """測試 /score nba 命令功能"""
    print("=" * 70)
    print("測試 Telegram Bot NBA 比分功能")
    print("=" * 70)

    if not SPORTS_SCORING_OK:
        print("❌ 體育比分系統未加載，無法測試")
        return False

    try:
        # 模擬 /score nba 命令
        print("\n[1] 模擬執行 /score nba 命令...")

        # 創建 scraper
        nba_scraper = NBAScraper()
        logger.info("✅ NBAScraper 初始化成功")

        # 獲取 NBA 比分
        print("\n[2] 獲取 NBA 比分數據...")
        nba_scores = await nba_scraper.fetch_scores()

        if nba_scores:
            print(f"✅ 成功獲取 {len(nba_scores)} 場 NBA 比賽\n")

            # 格式化輸出（模擬 Telegram 消息）
            print("📊 NBA 比分:")
            print("-" * 70)

            for i, game in enumerate(nba_scores, 1):
                date = game.get('date', 'N/A')
                home = game.get('home_team', 'N/A')
                away = game.get('away_team', 'N/A')
                home_score = game.get('home_score', 0)
                away_score = game.get('away_score', 0)
                status = game.get('status', 'N/A')
                quarter = game.get('quarter', 'N/A')
                time_remaining = game.get('time_remaining', 'N/A')
                venue = game.get('venue', 'N/A')

                print(f"\n🏀 比賽 {i}: {date}")
                print(f"   {away} @ {home}")
                print(f"   比分: {home_score} - {away_score}")
                print(f"   狀態: {status}")

                if status == 'live' and quarter != 'N/A':
                    print(f"   {quarter} ({time_remaining})")

                if venue and venue != 'N/A':
                    print(f"   球場: {venue}")

            # 測試數據處理器
            print("\n[3] 測試數據處理器...")
            data_processor = DataProcessor()
            formatted = data_processor.format_nba_score(nba_scores)
            print("✅ 數據格式化成功")
            print("\n格式化後的 Telegram 消息預覽:")
            print("-" * 70)
            print(formatted[:500] + "..." if len(formatted) > 500 else formatted)

        else:
            print("\n⚠️  未找到 NBA 比賽數據")
            print("   可能原因:")
            print("   - 今天沒有 NBA 比賽")
            print("   - NBA 休賽期間")

        # 測試賽程功能
        print("\n[4] 測試 NBA 賽程功能...")
        schedule = await nba_scraper.fetch_schedule(days=7)
        if schedule:
            print(f"✅ 獲取到 {len(schedule)} 場未來比賽")

        return True

    except Exception as e:
        logger.error(f"❌ 測試失敗: {e}", exc_info=True)
        print(f"\n❌ 測試過程中發生錯誤: {e}")
        return False

async def test_nba_data_integration():
    """測試 NBA 數據與 Telegram Bot 集成"""
    print("\n" + "=" * 70)
    print("測試 NBA 數據與 Telegram Bot 集成")
    print("=" * 70)

    # 測試從 Telegram bot 導入
    print("\n[1] 測試從 telegram_quant_bot.py 導入 NBAScraper...")
    try:
        from src.telegram_bot.telegram_quant_bot import NBAScraper as BotNBAScraper
        scraper = BotNBAScraper()
        scores = await scraper.fetch_scores()

        if scores:
            print(f"✅ 從 bot 中成功獲取 {len(scores)} 場比賽")
            print("   數據來源: ESPN NBA API")
            print("   時間:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

            # 顯示第一場比賽
            if scores:
                game = scores[0]
                print(f"\n   示例比賽: {game['away_team']} @ {game['home_team']}")
                print(f"   比分: {game['home_score']}-{game['away_score']}")
                print(f"   狀態: {game['status']}")

        return True
    except Exception as e:
        logger.error(f"❌ 導入失敗: {e}")
        print(f"❌ 無法從 bot 導入: {e}")
        return False

async def main():
    """主測試函數"""
    print("🚀 開始 NBA 比分功能測試\n")

    # 測試 1: 獨立 NBA 比分
    result1 = await test_nba_score_command()

    # 測試 2: Bot 集成
    result2 = await test_nba_data_integration()

    # 總結
    print("\n" + "=" * 70)
    print("測試結果總結")
    print("=" * 70)

    if result1:
        print("✅ 獨立 NBA 比分測試: 通過")
    else:
        print("❌ 獨立 NBA 比分測試: 失敗")

    if result2:
        print("✅ Telegram Bot 集成測試: 通過")
    else:
        print("❌ Telegram Bot 集成測試: 失敗")

    if result1 and result2:
        print("\n🎉 所有測試通過！NBA 比分功能正常工作")
        print("\n使用方法:")
        print("  1. 啟動 Telegram Bot: python src/telegram_bot/start_telegram_bot.py")
        print("  2. 在 Telegram 中發送: /score nba")
        print("  3. 查看實時 NBA 比分數據")
    else:
        print("\n⚠️  部分測試失敗，請檢查錯誤信息")

    return result1 and result2

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
