#!/usr/bin/env python3
"""
测试真实体育比分数据获取
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'telegram_bot'))

print("=" * 70)
print("真实体育比分数据测试")
print("=" * 70)
print()


async def test_real_data_fetcher():
    """测试真实数据获取器"""
    print("[TEST 1] 测试真实数据获取器")
    print("-" * 70)

    try:
        from sports_scoring.real_data_fetcher import RealSportsDataFetcher

        fetcher = RealSportsDataFetcher()
        print("[OK] 真实数据获取器导入成功")

        # 获取足球比分
        print("\n[2] 获取足球比分...")
        scores = await fetcher.fetch_football_scores()
        print(f"[OK] 获取到 {len(scores)} 场比赛")

        if scores:
            print("\n比赛详情:")
            for i, game in enumerate(scores[:5], 1):
                print(f"\n  比赛 {i}:")
                print(f"    联赛: {game.get('league', 'N/A')}")
                print(f"    对战: {game.get('home_team', 'N/A')} vs {game.get('away_team', 'N/A')}")
                print(f"    比分: {game.get('home_score', 0)} - {game.get('away_score', 0)}")
                print(f"    状态: {game.get('status', 'N/A')}")
                if game.get('minute'):
                    print(f"    时间: {game.get('minute')}'")

        return True

    except Exception as e:
        print(f"[FAIL] 真实数据获取器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_football_scraper():
    """测试足球爬虫"""
    print("\n[TEST 2] 测试足球爬虫（集成真实数据）")
    print("-" * 70)

    try:
        from sports_scoring.football_scraper import FootballScraper

        scraper = FootballScraper()
        print("[OK] 足球爬虫导入成功")

        # 测试获取比分
        print("\n[2] 获取足球比分...")
        scores = await scraper.fetch_scores()
        print(f"[OK] 获取到 {len(scores)} 场比赛")

        if scores:
            print("\n最近5场比赛:")
            for i, game in enumerate(scores[:5], 1):
                print(f"\n  {i}. {game.get('home_team')} {game.get('home_score', 0)} - {game.get('away_score', 0)} {game.get('away_team')}")
                print(f"     联赛: {game.get('league')} | 状态: {game.get('status')}")

        # 测试获取赛程
        print("\n[3] 获取未来赛程...")
        schedule = await scraper.fetch_schedule(3)
        print(f"[OK] 获取到 {len(schedule)} 场赛程")

        if schedule:
            print("\n未来3天赛程:")
            for i, game in enumerate(schedule[:3], 1):
                print(f"\n  {i}. {game.get('date')} {game.get('home_team')} vs {game.get('away_team')}")
                print(f"     时间: {game.get('start_time')} | 联赛: {game.get('league')}")

        return True

    except Exception as e:
        print(f"[FAIL] 足球爬虫测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_data_formatting():
    """测试数据格式化"""
    print("\n[TEST 3] 测试数据格式化")
    print("-" * 70)

    try:
        from sports_scoring.data_processor import DataProcessor

        print("[OK] 数据处理器导入成功")

        # 创建测试数据
        test_data = [
            {
                "date": "2024-10-27",
                "home_team": "曼城",
                "away_team": "利物浦",
                "home_score": 2,
                "away_score": 1,
                "status": "finished",
                "league": "英超",
                "start_time": "22:00",
                "venue": "Etihad Stadium",
                "minute": None,
                "added_time": None,
            },
            {
                "date": "2024-10-27",
                "home_team": "皇馬",
                "away_team": "巴塞隆拿",
                "home_score": 0,
                "away_score": 0,
                "status": "live",
                "league": "西甲",
                "start_time": "23:30",
                "venue": "班拿貝球場",
                "minute": 67,
                "added_time": 2,
            }
        ]

        # 格式化数据
        formatted = DataProcessor.format_football_score(test_data)
        print(f"[OK] 数据格式化成功")
        print(f"\n格式化结果预览:")
        print("-" * 70)
        print(formatted[:500] + "..." if len(formatted) > 500 else formatted)
        print("-" * 70)

        return True

    except Exception as e:
        print(f"[FAIL] 数据格式化测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    results = []

    # 测试真实数据获取器
    result1 = await test_real_data_fetcher()
    results.append(("真实数据获取器", result1))

    # 测试足球爬虫
    result2 = await test_football_scraper()
    results.append(("足球爬虫", result2))

    # 测试数据格式化
    result3 = await test_data_formatting()
    results.append(("数据格式化", result3))

    # 输出测试结果
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)

    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")

    print("\n" + "=" * 70)

    all_passed = all(result for _, result in results)
    if all_passed:
        print("[SUCCESS] 所有测试通过！")
        print("\n真实比分数据获取功能已集成完成！")
        print("Bot 现在可以获取真实的体育比分数据了。")
        return 0
    else:
        print("[FAIL] 部分测试失败，请检查错误信息")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
