#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試英超聯賽官網數據適配器
驗證 PremierLeagueAdapter 的基本功能
"""

import asyncio
import logging
from typing import List, Dict, Any
import sys

# 設置控制台輸出編碼
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_premier_league_adapter():
    """測試 PremierLeagueAdapter"""
    print("=" * 60)
    print("測試英超聯賽官網數據適配器")
    print("=" * 60)

    try:
        # 導入 PremierLeagueAdapter
        from src.telegram_bot.sports_scoring.premier_league_adapter import (
            PremierLeagueAdapter,
            PremierLeagueMatch,
            MatchStatus
        )
        print("✓ 成功導入 PremierLeagueAdapter")

        # 創建適配器實例
        adapter = PremierLeagueAdapter()
        print("✓ 創建適配器實例")

        # 初始化適配器
        await adapter.initialize()
        print("✓ 初始化適配器")

        # 測試健康檢查
        health = await adapter.health_check()
        print(f"\n📊 健康檢查結果:")
        print(f"   狀態: {health['status']}")
        print(f"   Chrome MCP: {health['chrome_mcp_available']}")
        print(f"   當前輪次: {health['current_matchweek']}")
        print(f"   當前月份: {health['current_month']}")
        print(f"   緩存大小: {health['cache_size']}")
        print(f"   更新次數: {health['stats']['update_count']}")
        print(f"   錯誤次數: {health['stats']['error_count']}")

        # 測試獲取比分
        print("\n" + "=" * 60)
        print("測試獲取英超比分")
        print("=" * 60)

        try:
            scores = await adapter.fetch_premier_league_scores()
            print(f"\n✓ 成功獲取 {len(scores)} 場比賽比分:")

            for i, score in enumerate(scores[:5], 1):  # 只顯示前5場
                print(f"\n  比賽 {i}:")
                print(f"    日期: {score['date']}")
                print(f"    對戰: {score['home_team']} vs {score['away_team']}")
                print(f"    比分: {score['home_score']} - {score['away_score']}")
                print(f"    狀態: {score['status']}")
                if score['status'] == 'live':
                    print(f"    時間: {score['display_time']}")
                print(f"    球場: {score['venue']}")
                print(f"    聯賽: {score['league']}")

        except Exception as e:
            print(f"❌ 獲取比分失敗: {e}")

        # 測試獲取賽程
        print("\n" + "=" * 60)
        print("測試獲取英超賽程")
        print("=" * 60)

        try:
            schedule = await adapter.fetch_premier_league_schedule(days=7)
            print(f"\n✓ 成功獲取 {len(schedule)} 場賽程:")

            for i, game in enumerate(schedule[:5], 1):  # 只顯示前5場
                print(f"\n  賽程 {i}:")
                print(f"    日期: {game['date']}")
                print(f"    對戰: {game['home_team']} vs {game['away_team']}")
                print(f"    時間: {game['start_time']}")
                print(f"    球場: {game['venue']}")
                print(f"    聯賽: {game['league']}")

        except Exception as e:
            print(f"❌ 獲取賽程失敗: {e}")

        # 測試時區轉換
        print("\n" + "=" * 60)
        print("測試時區轉換")
        print("=" * 60)

        test_times = [
            "2025-10-31T19:30:00Z",
            "2025-10-31T22:00:00Z",
            "2025-11-01T00:30:00Z",
        ]

        for gmt_time in test_times:
            hkt_time = await adapter._convert_timezone(gmt_time)
            print(f"  GMT: {gmt_time} → HKT: {hkt_time}")

        # 測試球隊名稱映射
        print("\n" + "=" * 60)
        print("測試球隊名稱映射")
        print("=" * 60)

        test_teams = [
            "Arsenal",
            "Manchester City",
            "Liverpool",
            "Chelsea",
            "Tottenham Hotspur",
            "Manchester United",
            "Unknown Team",
        ]

        for team_en in test_teams:
            team_zh = adapter.team_name_mapping.get(team_en, team_en)
            print(f"  {team_en:25} → {team_zh}")

        # 測試數據驗證
        print("\n" + "=" * 60)
        print("測試數據驗證")
        print("=" * 60)

        # 創建測試比賽數據
        test_matches = [
            PremierLeagueMatch(
                match_id="test_1",
                home_team="曼城",
                away_team="利物浦",
                home_score=2,
                away_score=1,
                status=MatchStatus.FINISHED,
                venue="Etihad Stadium",
            ),
            PremierLeagueMatch(
                match_id="test_2",
                home_team="",
                away_team="阿仙奴",
                home_score=1,
                away_score=0,
                status=MatchStatus.LIVE,
                venue="酋長球場",
            ),
        ]

        valid_matches = await adapter.validate_data(test_matches)
        print(f"  原始數據: {len(test_matches)} 場")
        print(f"  驗證後: {len(valid_matches)} 場")

        # 測試緩存功能
        print("\n" + "=" * 60)
        print("測試緩存功能")
        print("=" * 60)

        # 第一次獲取
        print("\n  第一次獲取 (無緩存):")
        scores1 = await adapter.fetch_premier_league_scores(force_refresh=True)
        print(f"    獲取到 {len(scores1)} 場比賽")

        # 第二次獲取 (有緩存)
        print("\n  第二次獲取 (有緩存):")
        scores2 = await adapter.fetch_premier_league_scores()
        print(f"    獲取到 {len(scores2)} 場比賽")

        # 檢查緩存狀態
        health = await adapter.health_check()
        print(f"\n  緩存狀態: {health['cache_size']} 項")

        print("\n" + "=" * 60)
        print("✅ 所有測試完成！")
        print("=" * 60)

    except ImportError as e:
        print(f"❌ 導入錯誤: {e}")
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()


async def test_basic_functionality():
    """測試基本功能"""
    print("\n" + "=" * 60)
    print("測試 PremierLeagueMatch 數據類")
    print("=" * 60)

    from src.telegram_bot.sports_scoring.premier_league_adapter import (
        PremierLeagueMatch,
        MatchStatus
    )

    # 創建比賽對象
    match = PremierLeagueMatch(
        match_id="test_001",
        home_team="曼城",
        away_team="利物浦",
        home_score=2,
        away_score=1,
        status=MatchStatus.LIVE,
        minute=67,
        added_time=2,
        start_time_gmt="2025-10-31T19:30:00Z",
        start_time_hkt="2025-11-01T03:30:00",
        venue="Etihad Stadium",
        matchweek=10,
    )

    print(f"\n  比賽ID: {match.match_id}")
    print(f"  對戰: {match.home_team} vs {match.away_team}")
    print(f"  比分: {match.home_score} - {match.away_score}")
    print(f"  狀態: {match.status}")
    print(f"  是否進行中: {match.is_live}")
    print(f"  顯示時間: {match.display_time}")
    print(f"  球場: {match.venue}")
    print(f"  輪次: {match.matchweek}")

    # 轉換為字典
    match_dict = match.to_dict()
    print(f"\n  字典格式:")
    for key, value in match_dict.items():
        print(f"    {key}: {value}")


if __name__ == "__main__":
    # 運行基本功能測試
    asyncio.run(test_basic_functionality())

    # 運行主要測試
    asyncio.run(test_premier_league_adapter())
