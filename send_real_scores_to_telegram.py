#!/usr/bin/env python3
"""
通过真实API获取比分并发送到Telegram Bot
"""

import asyncio
import os
import sys
import requests
from datetime import datetime

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'telegram_bot'))

# 设置Token
os.environ["TELEGRAM_BOT_TOKEN"] = "7180490983:AAFbkKnDPC1MHAaOGzQA1fOs9FBwSGGonzI"

# 管理员Chat ID
ADMIN_CHAT_ID = "1005293427"


async def get_real_scores():
    """获取真实比分"""
    try:
        from sports_scoring.football_scraper import FootballScraper

        scraper = FootballScraper()
        scores = await scraper.fetch_scores()

        return scores

    except Exception as e:
        print(f"获取比分失败: {e}")
        import traceback
        traceback.print_exc()
        return []


def format_scores_for_telegram(scores):
    """格式化比分消息"""
    if not scores:
        return "⚽ 暂无比分数据"

    # 按联赛分组
    leagues = {}
    for game in scores:
        league = game.get('league', '其他')
        if league not in leagues:
            leagues[league] = []
        leagues[league].append(game)

    # 生成消息
    message = f"📊 实时体育比分 (真实数据)\n"
    message += f"🕒 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

    for league, games in leagues.items():
        message += f"🏆 {league}\n"

        finished_games = [g for g in games if g.get('status') == 'finished']
        live_games = [g for g in games if g.get('status') == 'live']
        scheduled_games = [g for g in games if g.get('status') == 'scheduled']

        if finished_games:
            message += "✅ 已结束\n"
            for game in finished_games:
                home = game.get('home_team', 'N/A')
                away = game.get('away_team', 'N/A')
                home_score = game.get('home_score', 0)
                away_score = game.get('away_score', 0)
                time = game.get('start_time', '')
                venue = game.get('venue', '')
                message += f"🥅 {home} {home_score} - {away_score} {away}\n"
                if venue:
                    message += f"   📅 {time} | 📍 {venue}\n"
            message += "\n"

        if live_games:
            message += "🔴 进行中\n"
            for game in live_games:
                home = game.get('home_team', 'N/A')
                away = game.get('away_team', 'N/A')
                home_score = game.get('home_score', 0)
                away_score = game.get('away_score', 0)
                minute = game.get('minute')
                added = game.get('added_time')
                time_str = f"{minute}'" + (f"+{added}" if added else "")
                message += f"⚡ {home} {home_score} - {away_score} {away} ({time_str})\n"
            message += "\n"

        if scheduled_games:
            message += "⏸️ 即将开始\n"
            for game in scheduled_games:
                home = game.get('home_team', 'N/A')
                away = game.get('away_team', 'N/A')
                time = game.get('start_time', '')
                venue = game.get('venue', '')
                message += f"🕖 {time} {home} vs {away}\n"
                if venue:
                    message += f"   📍 {venue}\n"
            message += "\n"

    # 添加说明
    message += "=" * 40 + "\n"
    message += "📱 使用 Bot 命令：\n"
    message += "/score - 查看所有比分\n"
    message += "/score soccer - 查看足球比分\n"
    message += "/schedule - 查看赛程\n"
    message += "/help - 显示帮助\n"

    return message


async def get_schedule():
    """获取赛程"""
    try:
        from sports_scoring.football_scraper import FootballScraper

        scraper = FootballScraper()
        schedule = await scraper.fetch_schedule(3)

        return schedule

    except Exception as e:
        print(f"获取赛程失败: {e}")
        return []


def format_schedule_for_telegram(schedule):
    """格式化赛程消息"""
    if not schedule:
        return "📅 暂无赛程数据"

    message = f"📅 未来3天赛程\n"
    message += f"🕒 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

    # 按日期分组
    dates = {}
    for game in schedule:
        date = game.get('date', '未知日期')
        if date not in dates:
            dates[date] = []
        dates[date].append(game)

    for date, games in dates.items():
        message += f"📆 {date}\n"
        for game in games:
            home = game.get('home_team', 'N/A')
            away = game.get('away_team', 'N/A')
            time = game.get('start_time', '')
            league = game.get('league', '')
            venue = game.get('venue', '')
            message += f"🕖 {time} {home} vs {away}\n"
            message += f"   🏆 {league}"
            if venue:
                message += f" | 📍 {venue}"
            message += "\n"
        message += "\n"

    return message


def send_to_telegram(message, chat_id):
    """发送到Telegram"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        response = requests.post(
            url,
            data={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            },
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                return True, "消息发送成功"
            else:
                return False, f"API错误: {result}"
        else:
            return False, f"HTTP错误: {response.status_code}"

    except Exception as e:
        return False, f"发送失败: {e}"


async def main():
    """主函数"""
    print("=" * 70)
    print("获取真实比分并发送到Telegram")
    print("=" * 70)
    print()

    # 获取比分
    print("[1] 获取真实比分数据...")
    scores = await get_real_scores()
    print(f"   获取到 {len(scores)} 场比赛")

    if scores:
        print("\n比分预览:")
        for game in scores[:3]:
            home = game.get('home_team', 'N/A')
            away = game.get('away_team', 'N/A')
            home_score = game.get('home_score', 0)
            away_score = game.get('away_score', 0)
            status = game.get('status', 'N/A')
            print(f"   {home} {home_score} - {away_score} {away} ({status})")

    # 格式化比分消息
    print("\n[2] 格式化比分消息...")
    score_message = format_scores_for_telegram(scores)
    print(f"   消息长度: {len(score_message)} 字符")

    # 发送比分
    print("\n[3] 发送到Telegram...")
    success, msg = send_to_telegram(score_message, ADMIN_CHAT_ID)

    if success:
        print("   ✅ 比分消息发送成功")
    else:
        print(f"   ❌ 发送失败: {msg}")

    # 获取赛程
    print("\n[4] 获取赛程数据...")
    schedule = await get_schedule()
    print(f"   获取到 {len(schedule)} 场比赛")

    # 格式化赛程消息
    print("\n[5] 格式化赛程消息...")
    schedule_message = format_schedule_for_telegram(schedule)
    print(f"   消息长度: {len(schedule_message)} 字符")

    # 发送赛程
    print("\n[6] 发送赛程到Telegram...")
    success2, msg2 = send_to_telegram(schedule_message, ADMIN_CHAT_ID)

    if success2:
        print("   ✅ 赛程消息发送成功")
    else:
        print(f"   ❌ 发送失败: {msg2}")

    print("\n" + "=" * 70)
    if success and success2:
        print("✅ 所有消息发送成功！")
        print("请在Telegram中查看 @penguinai_bot 的消息")
        print("\n现在Bot命令将返回真实的比分数据！")
    else:
        print("⚠️ 部分消息发送失败，请检查网络连接")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
