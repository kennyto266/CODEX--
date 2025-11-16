#!/usr/bin/env python3
"""
最終測試 - 驗證真實NBA數據爬蟲
"""

import os
import sys
import asyncio

# 設置環境變量
os.environ['GLM46_API_KEY'] = '3f3a42c3fd2e443bbd0f0825eba93cf2.UZd0cuO7lgt4tGMW'
os.environ['TELEGRAM_BOT_TOKEN'] = '7180490983:AAFbkKnDPC1MHAaOGzQA1fOs9FBwSGGonzI'

# 添加項目路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_final_nba_crawler():
    """最終測試真實NBA爬蟲"""
    try:
        from src.telegram.real_nba_crawler import get_real_nba_crawler_instance

        print("=" * 60)
        print("最終測試 - 真實NBA數據爬蟲")
        print("=" * 60)

        crawler = get_real_nba_crawler_instance()

        # 清除緩存
        crawler.clear_cache()

        print("正在爬取真實ESPN NBA數據...")

        # 獲取數據
        nba_data = await crawler.crawl_nba_scores()

        print(f"\n數據結果:")
        print("-" * 40)
        print(nba_data)
        print("-" * 40)

        # 檢查結果
        is_real = "真實" in nba_data and "ESPN" in nba_data
        has_games = "第1場" in nba_data
        no_mock_data = "模擬" not in nba_data and "Mock" not in nba_data

        print(f"\n檢查結果:")
        print(f"   使用真實數據: {'是' if is_real else '否'}")
        print(f"   無模擬數據: {'是' if no_mock_data else '否'}")
        print(f"   包含比賽: {'是' if has_games else '否'}")
        print(f"   數據長度: {len(nba_data)} 字符")

        # 成功標準
        success = is_real and no_mock_data and len(nba_data) > 100

        if success:
            print(f"\n成功! 獲得真實NBA數據")
            print("✅ 拒絕模擬數據，使用真實ESPN爬蟲")
        else:
            print(f"\n失敗! 需要進一步調試")

        return success

    except Exception as e:
        print(f"測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("NBA真實數據爬蟲最終測試")
    success = asyncio.run(test_final_nba_crawler())
    print(f"\n最終結果: {'成功' if success else '失敗'}")
    sys.exit(0 if success else 1)