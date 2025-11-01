#!/usr/bin/env python3
"""
診斷 Bot 版本和 NBA Scraper 狀態
"""

import sys
import os
import importlib.util
from datetime import datetime

def check_nba_scraper_version():
    """檢查 NBA Scraper 版本"""
    print("=" * 70)
    print("NBA Scraper 版本診斷")
    print("=" * 70)

    # 檢查文件是否存在
    scraper_path = "src/telegram_bot/sports_scoring/nba_scraper.py"
    if not os.path.exists(scraper_path):
        print(f"❌ 文件不存在: {scraper_path}")
        return False

    # 檢查文件時間
    mtime = os.path.getmtime(scraper_path)
    mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[1] 文件路徑: {scraper_path}")
    print(f"    修改時間: {mtime_str}")

    # 檢查文件大小
    size = os.path.getsize(scraper_path)
    print(f"    文件大小: {size} bytes")

    # 檢查關鍵代碼
    with open(scraper_path, 'r', encoding='utf-8') as f:
        content = f.read()

    checks = [
        ("import aiohttp", "✅ 已添加 aiohttp 支持"),
        ("espn_api_url", "✅ 已添加 ESPN API URL"),
        ("_fetch_from_espn", "✅ 已實現真實 API 調用"),
        ("_parse_espn_response", "✅ 已實現數據解析"),
    ]

    print("\n[2] 關鍵功能檢查:")
    all_ok = True
    for check, msg in checks:
        if check in content:
            print(f"    {msg}")
        else:
            print(f"    ❌ 缺少: {check}")
            all_ok = False

    # 檢查 ESPN API URL
    if "site/v2/sports/basketball/nba/scoreboard" in content:
        print("    ✅ 使用正確的 ESPN API 端點")
    else:
        print("    ❌ ESPN API 端點可能不正確")
        all_ok = False

    return all_ok

def test_nba_scraper_direct():
    """直接測試 NBA Scraper"""
    print("\n" + "=" * 70)
    print("直接測試 NBA Scraper")
    print("=" * 70)

    try:
        # 添加路徑
        sys.path.insert(0, os.path.dirname(__file__))

        # 清除模塊緩存
        if 'src.telegram_bot.sports_scoring.nba_scraper' in sys.modules:
            del sys.modules['src.telegram_bot.sports_scoring.nba_scraper']

        # 導入
        from src.telegram_bot.sports_scoring.nba_scraper import NBAScraper
        print("\n[1] 成功導入 NBAScraper")

        # 創建實例
        scraper = NBAScraper()
        print("[2] 成功創建 NBAScraper 實例")

        # 檢查 URL
        if hasattr(scraper, 'espn_api_url'):
            print(f"[3] ESPN API URL: {scraper.espn_api_url}")
        else:
            print("[3] ❌ 缺少 espn_api_url 屬性")
            return False

        # 測試獲取比分
        print("\n[4] 測試獲取 NBA 比分...")
        import asyncio

        async def _test():
            scores = await scraper.fetch_scores()
            return scores

        scores = asyncio.run(_test())

        if scores:
            print(f"    ✅ 成功獲取 {len(scores)} 場比賽")
            if scores:
                game = scores[0]
                print(f"\n    範例比賽:")
                print(f"      {game.get('away_team')} @ {game.get('home_team')}")
                print(f"      比分: {game.get('home_score')}-{game.get('away_score')}")
                print(f"      狀態: {game.get('status')}")
            return True
        else:
            print("    ⚠️  未獲取到比賽數據")
            return False

    except Exception as e:
        print(f"    ❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_bot_integration():
    """檢查 Bot 集成"""
    print("\n" + "=" * 70)
    print("檢查 Bot 集成")
    print("=" * 70)

    bot_file = "src/telegram_bot/telegram_quant_bot.py"
    if not os.path.exists(bot_file):
        print(f"❌ Bot 文件不存在: {bot_file}")
        return False

    with open(bot_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 檢查導入
    if "from sports_scoring import" in content:
        print("\n[1] ✅ Bot 文件包含 sports_scoring 導入")
    else:
        print("\n[1] ❌ Bot 文件缺少 sports_scoring 導入")
        return False

    if "NBAScraper" in content:
        print("[2] ✅ Bot 文件包含 NBAScraper")
    else:
        print("[2] ❌ Bot 文件缺少 NBAScraper")
        return False

    # 檢查命令實現
    if "score_cmd" in content and "/score nba" in content:
        print("[3] ✅ Bot 實現了 /score nba 命令")
    else:
        print("[3] ❌ Bot 缺少 /score nba 命令實現")
        return False

    return True

def main():
    """主診斷函數"""
    print("\n🔍 NBA Scraper 診斷工具")
    print("診斷時間:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print()

    results = []

    # 檢查 1: 文件版本
    result1 = check_nba_scraper_version()
    results.append(("文件版本", result1))

    # 檢查 2: 直接測試
    result2 = test_nba_scraper_direct()
    results.append(("直接測試", result2))

    # 檢查 3: Bot 集成
    result3 = check_bot_integration()
    results.append(("Bot 集成", result3))

    # 總結
    print("\n" + "=" * 70)
    print("診斷結果總結")
    print("=" * 70)

    for name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{name:15} {status}")

    if all(r for _, r in results):
        print("\n🎉 所有檢查通過！NBA Scraper 正常工作")
        print("\n如果 Bot 仍顯示舊數據，請重啟 Bot:")
        print("  1. 停止當前 Bot 進程")
        print("  2. 運行: python src/telegram_bot/start_telegram_bot.py")
    else:
        print("\n⚠️  部分檢查失敗，請查看上述錯誤信息")

    return all(r for _, r in results)

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1)
