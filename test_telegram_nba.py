#!/usr/bin/env python3
"""
Telegram Bot NBA 測試腳本
模擬 /score nba 命令
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

async def test_bot_nba_command():
    """模擬 Bot 中的 /score nba 命令"""
    print("=" * 70)
    print("模擬 Telegram Bot /score nba 命令")
    print("=" * 70)

    # 清除緩存
    if 'src.telegram_bot.sports_scoring.nba_scraper' in sys.modules:
        del sys.modules['src.telegram_bot.sports_scoring.nba_scraper']

    try:
        from src.telegram_bot.sports_scoring import (
            NBAScraper,
            DataProcessor
        )

        print("\n[步驟 1] 初始化...")
        nba_scraper = NBAScraper()
        data_processor = DataProcessor()
        print("✓ 完成")

        print("\n[步驟 2] 獲取 NBA 比分...")
        nba_scores = await nba_scraper.fetch_scores()
        print(f"✓ 獲取到 {len(nba_scores)} 場比賽")

        if not nba_scores:
            print("\n⚠️  未找到比賽數據")
            return False

        print("\n[步驟 3] 格式化數據...")
        formatted_message = data_processor.format_nba_score(nba_scores)
        print("✓ 完成")

        print("\n" + "=" * 70)
        print("Bot 將顯示的內容:")
        print("=" * 70)
        print(formatted_message)
        print("=" * 70)

        print("\n✅ /score nba 命令測試成功！")
        print("\n💡 如果您在 Telegram 中發送 /score nba，")
        print("   會看到與上面相同的內容。")

        return True

    except ImportError as e:
        print(f"\n❌ 導入失敗: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("\n🚀 測試 Bot 的 NBA 比分功能...\n")

    success = await test_bot_nba_command()

    if success:
        print("\n🎉 所有測試通過！")
        print("\n現在請在 Telegram 中:")
        print("  1. 找到您的 Bot")
        print("  2. 發送: /score nba")
        print("  3. 查看真實的 NBA 比分")
    else:
        print("\n⚠️  測試失敗，請檢查錯誤信息")

    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
