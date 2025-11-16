#!/usr/bin/env python3
"""
測試真實NBA資料獲取
"""

import os
import sys
import asyncio

# 設置環境變量
os.environ['GLM46_API_KEY'] = '3f3a42c3fd2e443bbd0f0825eba93cf2.UZd0cuO7lgt4tGMW'
os.environ['TELEGRAM_BOT_TOKEN'] = '7180490983:AAFbkKnDPC1MHAaOGzQA1fOs9FBwSGGonzI'

# 添加項目路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_real_nba_crawler():
    """測試真實NBA爬蟲"""
    try:
        from src.telegram.fast_nba_crawler import get_fast_nba_crawler_instance

        print("測試真實NBA資料獲取...")

        crawler = get_fast_nba_crawler_instance()

        # 清除緩存以確保獲取最新資料
        crawler.clear_cache()

        # 獲取NBA比分
        nba_data = await crawler.crawl_nba_scores()

        print(f"資料長度: {len(nba_data)} 字元")

        # 檢查是否為模擬資料
        is_mock = "模擬資料" in nba_data or "Mock data" in nba_data
        is_real = "即時資料 | 來源: ESPN" in nba_data

        print(f"是否為模擬資料: {'是' if is_mock else '否'}")
        print(f"是否為真實資料: {'是' if is_real else '否'}")

        if nba_data:
            print(f"\n資料內容:")
            print(nba_data)

        # 獲取爬蟲統計
        stats = crawler.get_statistics()
        print(f"\n爬蟲統計:")
        print(f"   緩存大小: {stats['cache_size']}")
        print(f"   狀態: {stats['crawler_status']}")

        return not is_mock and len(nba_data) > 100

    except Exception as e:
        print(f"測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_espn_access():
    """測試直接訪問ESPN"""
    try:
        import httpx
        from bs4 import BeautifulSoup

        print("測試直接訪問ESPN...")

        url = "https://www.espn.com/nba/scoreboard"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            print(f"HTTP狀態: {response.status_code}")
            print(f"內容長度: {len(response.text)} 字元")

            # 檢查是否包含NBA相關內容
            has_nba = "NBA" in response.text or "basketball" in response.text.lower()
            print(f"包含NBA內容: {'是' if has_nba else '否'}")

            # 嘗試解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()

            # 查找比分模式
            score_patterns = []
            import re
            patterns = re.findall(r'([A-Za-z][A-Za-z\s\.&\-]+?)\s+(\d+)\s*[-–]\s*(\d+)\s+([A-Za-z][A-Za-z\s\.&\-]+)', text)
            score_patterns.extend(patterns)

            print(f"找到比分模式: {len(score_patterns)} 個")
            for i, pattern in enumerate(score_patterns[:3]):
                print(f"   模式 {i+1}: {pattern}")

            return len(score_patterns) > 0

    except Exception as e:
        print(f"ESPN訪問測試失敗: {e}")
        return False

async def main():
    """主測試函數"""
    print("=" * 50)
    print("真實NBA資料測試")
    print("=" * 50)

    print("\n1. 測試直接ESPN訪問:")
    espn_ok = await test_espn_access()

    print("\n2. 測試NBA爬蟲:")
    crawler_ok = await test_real_nba_crawler()

    print("\n" + "=" * 50)
    print("測試結果:")
    print(f"   ESPN訪問: {'成功' if espn_ok else '失敗'}")
    print(f"   NBA爬蟲: {'成功' if crawler_ok else '失敗'}")

    overall_success = espn_ok and crawler_ok
    print(f"\n整體評估: {'可獲取真實資料' if overall_success else '仍需改進'}")

    return overall_success

if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n最終結果: {'成功' if success else '失敗'}")