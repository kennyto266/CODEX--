#!/usr/bin/env python3
"""
測試真實NBA爬蟲 - 確保獲取真實ESPN數據
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
        from src.telegram.real_nba_crawler import get_real_nba_crawler_instance

        print("=" * 60)
        print("測試真實NBA爬蟲 - 絕無模擬數據")
        print("=" * 60)

        crawler = get_real_nba_crawler_instance()

        # 清除緩存確保獲取最新資料
        crawler.clear_cache()

        print("正在爬取真實ESPN數據...")

        # 獲取NBA比分
        nba_data = await crawler.crawl_nba_scores()

        print(f"\n資料長度: {len(nba_data)} 字元")

        # 檢查是否為真實資料
        is_real = "真實" in nba_data and "ESPN" in nba_data
        is_mock = "模擬" in nba_data or "Mock" in nba_data
        has_games = "第1場" in nba_data

        print(f"使用真實資料: {'是' if is_real else '否'}")
        print(f"包含模擬資料: {'是' if is_mock else '否'}")
        print(f"包含比賽場次: {'是' if has_games else '否'}")

        # 檢查場次數量
        game_count = nba_data.count("第") // 2  # 每場比賽有"第X場"
        print(f"場次數量: {game_count} 場")

        # 檢查比賽內容
        has_scores = any(char.isdigit() for char in nba_data[:500])
        print(f"包含比分數字: {'是' if has_scores else '否'}")

        if nba_data:
            print(f"\n前500字符內容:")
            print("-" * 40)
            print(nba_data[:500] + "..." if len(nba_data) > 500 else nba_data)
            print("-" * 40)

        # 獲取爬蟲統計
        stats = crawler.get_statistics()
        print(f"\n爬蟲統計:")
        print(f"   緩存大小: {stats['cache_size']}")
        print(f"   狀態: {stats['crawler_status']}")
        print(f"   方法: {stats['method']}")

        # 判斷成功標準
        success = (
            is_real and
            not is_mock and
            len(nba_data) > 200 and
            game_count >= 1 and
            has_scores
        )

        return success

    except Exception as e:
        print(f"測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_espn_direct():
    """直接測試ESPN訪問"""
    try:
        import httpx
        from bs4 import BeautifulSoup

        print("\n" + "=" * 60)
        print("直接測試ESPN網站訪問")
        print("=" * 60)

        url = "https://www.espn.com/nba/scoreboard"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }

        print(f"正在訪問: {url}")

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            print(f"HTTP狀態: {response.status_code}")
            print(f"內容長度: {len(response.text)} 字元")

            # 檢查NBA內容
            has_nba = "NBA" in response.text or "basketball" in response.text.lower()
            print(f"包含NBA內容: {'是' if has_nba else '否'}")

            # 解析並查找比分
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()

            # 查找數字比分模式
            import re
            score_patterns = re.findall(r'(\d+)\s*[-–]\s*(\d+)', text)
            print(f"找到比分模式: {len(score_patterns)} 個")

            # 查找隊伍模式
            team_patterns = []
            nba_teams = ['Lakers', 'Warriors', 'Celtics', 'Heat', 'Thunder', 'Nuggets']
            for team in nba_teams:
                if team in text:
                    team_patterns.append(team)

            print(f"找到NBA隊伍: {len(team_patterns)} 個 - {team_patterns}")

            # 顯示前幾個比分示例
            if score_patterns:
                print(f"\n比分示例:")
                for i, (s1, s2) in enumerate(score_patterns[:5]):
                    print(f"   {i+1}. {s1} - {s2}")

            return len(score_patterns) > 0

    except Exception as e:
        print(f"ESPN訪問測試失敗: {e}")
        return False

async def main():
    """主測試函數"""
    print("NBA真實數據爬蟲測試")
    print("確保獲取真實ESPN數據，拒絕任何模擬數據\n")

    # 測試1: 直接ESPN訪問
    espn_ok = await test_espn_direct()

    # 測試2: 真實NBA爬蟲
    crawler_ok = await test_real_nba_crawler()

    print("\n" + "=" * 60)
    print("測試結果總結:")
    print("=" * 60)
    print(f"   ESPN直接訪問: {'成功' if espn_ok else '失敗'}")
    print(f"   NBA爬蟲測試: {'成功' if crawler_ok else '失敗'}")

    overall_success = espn_ok and crawler_ok

    if overall_success:
        print(f"\n成功! 爬蟲能獲取真實NBA數據")
        print("無模擬數據，全部來自ESPN")
    else:
        print(f"\n失敗! 需要進一步調試")
        print("無法獲取真實NBA數據")

    return overall_success

if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n最終結果: {'成功' if success else '失敗'}")
    sys.exit(0 if success else 1)