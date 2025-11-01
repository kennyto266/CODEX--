#!/usr/bin/env python3
"""
发送更新的实时比分到Telegram
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


async def get_updated_scores():
    """获取更新的实时比分"""
    try:
        from sports_scoring.real_data_fetcher import RealSportsDataFetcher

        fetcher = RealSportsDataFetcher()
        scores = await fetcher.fetch_football_scores()

        return scores

    except Exception as e:
        print(f"获取比分失败: {e}")
        import traceback
        traceback.print_exc()
        return []


def format_updated_scores(scores):
    """格式化更新的比分消息"""
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
    now = datetime.now()
    message = f"📊 实时体育比分 (更新版)\n"
    message += f"🕒 更新时间: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
    message += f"⏰ 当前时间: {now.strftime('%H:%M')}\n\n"

    for league, games in leagues.items():
        message += f"🏆 {league}\n"

        finished_games = [g for g in games if g.get('status') == 'finished']
        live_games = [g for g in games if g.get('status') == 'live']
        halftime_games = [g for g in games if g.get('status') == 'halftime']
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

        if halftime_games:
            message += "⏸️ 中场休息\n"
            for game in halftime_games:
                home = game.get('home_team', 'N/A')
                away = game.get('away_team', 'N/A')
                home_score = game.get('home_score', 0)
                away_score = game.get('away_score', 0)
                minute = game.get('minute', 45)
                message += f"⚡ {home} {home_score} - {away_score} {away} (HT)\n"
                message += f"   ⏱️ 中场休息\n"
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
                message += f"🔥 {home} {home_score} - {away_score} {away}\n"
                message += f"   ⏱️ {time_str}\n"
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
    message += "✨ 实时比分已更新！\n"
    message += "🔄 每次查询都会获取最新状态\n\n"
    message += "📱 使用 Bot 命令：\n"
    message += "/score - 查看实时比分\n"
    message += "/schedule - 查看赛程\n"
    message += "/help - 显示帮助\n"

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
    print("获取更新的实时比分并发送到Telegram")
    print("=" * 70)
    print()

    # 获取比分
    print("[1] 获取更新的实时比分...")
    scores = await get_updated_scores()
    print(f"   获取到 {len(scores)} 场比赛")

    if scores:
        print("\n比分预览:")
        for game in scores:
            home = game.get('home_team', 'N/A')
            away = game.get('away_team', 'N/A')
            home_score = game.get('home_score', 0)
            away_score = game.get('away_score', 0)
            status = game.get('status', 'N/A')
            minute = game.get('minute')
            time_info = f" ({minute}')" if minute else ""
            print(f"   {home} {home_score} - {away_score} {away} ({status}){time_info}")

    # 格式化消息
    print("\n[2] 格式化消息...")
    message = format_updated_scores(scores)
    print(f"   消息长度: {len(message)} 字符")

    # 发送到Telegram
    print("\n[3] 发送到Telegram...")
    success, msg = send_to_telegram(message, ADMIN_CHAT_ID)

    if success:
        print("   ✅ 实时比分消息发送成功")
        print("\n" + "=" * 70)
        print("✅ 更新版实时比分已发送！")
        print("比分会根据当前时间动态更新")
        print("=" * 70)
    else:
        print(f"   ❌ 发送失败: {msg}")
        print("\n" + "=" * 70)
        print("⚠️ 发送失败，请检查网络连接")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
