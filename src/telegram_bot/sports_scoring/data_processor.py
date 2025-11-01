"""
數據處理器
負責格式化體育比分數據
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


logger = logging.getLogger(__name__)


class MatchStatus(Enum):
    """比賽狀態"""
    SCHEDULED = "scheduled"
    LIVE = "live"
    HALFTIME = "halftime"
    FINISHED = "finished"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"


class DataProcessor:
    """數據處理器"""

    @staticmethod
    def format_nba_score(teams_data: List[Dict[str, Any]]) -> str:
        """
        格式化 NBA 比分消息

        Args:
            teams_data: NBA 球隊比分數據列表

        Returns:
            str: 格式化的消息
        """
        if not teams_data:
            return "🏀 今日沒有 NBA 比賽"

        # 獲取今日日期
        today = datetime.now().strftime("%Y-%m-%d")

        # 按狀態分組
        finished = []
        live = []
        scheduled = []

        for game in teams_data:
            status = game.get("status", "").lower()
            if "final" in status or status == "finished":
                finished.append(game)
            elif status == "live" or "q" in status.lower():
                live.append(game)
            else:
                scheduled.append(game)

        # 構建消息
        message = f"🏀 NBA 今日比分 ({today})\n\n"

        # 已結束的比賽
        if finished:
            message += f"✅ 已結束 ({len(finished)}場)\n"
            for game in finished:
                home = game.get("home_team", "")
                away = game.get("away_team", "")
                home_score = game.get("home_score", 0)
                away_score = game.get("away_score", 0)

                message += f"🏆 {away} {away_score} - {home_score} {home}\n"

                # 添加勝率（如果可用）
                home_odds = game.get("home_odds")
                away_odds = game.get("away_odds")
                if home_odds and away_odds:
                    message += f"   📊 勝率: {away_odds}% vs {home_odds}%\n"

            message += "\n"

        # 進行中的比賽
        if live:
            message += f"🔴 進行中 ({len(live)}場)\n"
            for game in live:
                home = game.get("home_team", "")
                away = game.get("away_team", "")
                home_score = game.get("home_score", 0)
                away_score = game.get("away_score", 0)
                quarter = game.get("quarter", "")
                time_remaining = game.get("time_remaining", "")

                message += f"⚡ {away} vs {home} ({quarter})\n"
                message += f"   💯 比分: {away_score} - {home_score}\n"
                if time_remaining:
                    message += f"   ⏱️ 剩餘: {time_remaining}\n"

            message += "\n"

        # 即將開始的比賽
        if scheduled:
            message += f"⏸️ 即將開始 ({len(scheduled)}場)\n"
            for game in scheduled:
                home = game.get("home_team", "")
                away = game.get("away_team", "")
                start_time = game.get("start_time", "")
                venue = game.get("venue", "")

                if start_time:
                    message += f"🕖 {start_time} {away} vs {home}\n"
                else:
                    message += f"⏰ {away} vs {home}\n"

                if venue:
                    message += f"   📍 {venue}\n"

            message += "\n"

        return message

    @staticmethod
    def format_football_score(teams_data: List[Dict[str, Any]]) -> str:
        """
        格式化足球比分消息

        Args:
            teams_data: 足球比賽數據列表

        Returns:
            str: 格式化的消息
        """
        if not teams_data:
            return "⚽ 今日沒有足球比賽"

        # 獲取今日日期
        today = datetime.now().strftime("%Y-%m-%d")

        # 按聯賽分組
        leagues = {}
        for game in teams_data:
            league = game.get("league", "其他")
            if league not in leagues:
                leagues[league] = {
                    "finished": [],
                    "live": [],
                    "scheduled": []
                }

            status = game.get("status", "").lower()
            if status == "finished":
                leagues[league]["finished"].append(game)
            elif status == "live" or status == "halftime":
                leagues[league]["live"].append(game)
            else:
                leagues[league]["scheduled"].append(game)

        # 構建消息
        message = f"⚽ 足球比分 ({today})\n\n"

        for league, games in leagues.items():
            if not any(games.values()):
                continue

            # 聯賽標題
            if league == "香港超級聯賽":
                message += "🏆 香港超級聯賽\n"
            elif league == "英超":
                message += "🌍 英超聯賽\n"
            else:
                message += f"⚽ {league}\n"

            # 已結束
            if games["finished"]:
                message += "✅ 已結束\n"
                for game in games["finished"]:
                    home = game.get("home_team", "")
                    away = game.get("away_team", "")
                    home_score = game.get("home_score", 0)
                    away_score = game.get("away_score", 0)
                    start_time = game.get("start_time", "")
                    venue = game.get("venue", "")

                    message += f"🥅 {away} {away_score} - {home_score} {home}\n"

                    if start_time:
                        message += f"   📅 {start_time} |"
                    if venue:
                        message += f" 現場: {venue}\n"

                message += "\n"

            # 進行中
            if games["live"]:
                message += "🔴 進行中\n"
                for game in games["live"]:
                    home = game.get("home_team", "")
                    away = game.get("away_team", "")
                    home_score = game.get("home_score", 0)
                    away_score = game.get("away_score", 0)
                    minute = game.get("minute", 0)
                    added_time = game.get("added_time", 0)

                    time_str = f"{minute}'" + (f"+{added_time}" if added_time else "")
                    status = game.get("status", "")
                    if status == "halftime":
                        time_str = "中場休息"

                    message += f"⚡ {away} vs {home} ({time_str})\n"
                    message += f"   💯 比分: {away_score} - {home_score}\n"

                message += "\n"

            # 即將開始
            if games["scheduled"]:
                message += "⏸️ 即將開始\n"
                for game in games["scheduled"]:
                    home = game.get("home_team", "")
                    away = game.get("away_team", "")
                    start_time = game.get("start_time", "")
                    venue = game.get("venue", "")

                    if start_time:
                        message += f"🕖 {start_time} {away} vs {home}\n"
                    else:
                        message += f"⏰ {away} vs {home}\n"

                    if venue:
                        message += f"   🏟️ {venue}\n"

                message += "\n"

        return message

    @staticmethod
    def format_schedule(schedule_data: List[Dict[str, Any]], sport_type: str) -> str:
        """
        格式化賽程消息

        Args:
            schedule_data: 賽程數據列表
            sport_type: 運動類型 (nba, soccer)

        Returns:
            str: 格式化的消息
        """
        if not schedule_data:
            sport_emoji = "🏀" if sport_type == "nba" else "⚽"
            return f"{sport_emoji} 未來7天沒有賽程"

        # 按日期分組
        by_date = {}
        for game in schedule_data:
            date = game.get("date", datetime.now().strftime("%Y-%m-%d"))
            if date not in by_date:
                by_date[date] = []
            by_date[date].append(game)

        # 構建消息
        sport_emoji = "🏀" if sport_type == "nba" else "⚽"
        sport_name = "NBA" if sport_type == "nba" else "足球"
        message = f"{sport_emoji} {sport_name} 未來賽程\n\n"

        # 顯示未來 7 天
        for date, games in sorted(by_date.items())[:7]:
            # 格式化日期
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            day_name = date_obj.strftime("%A")
            date_str = date_obj.strftime("%Y-%m-%d")
            today = datetime.now().date()
            game_date = date_obj.date()

            if game_date == today:
                date_display = f"今天 ({date_str})"
            elif game_date == today.replace(day=today.day + 1):
                date_display = f"明天 ({date_str})"
            else:
                date_display = f"{day_name} ({date_str})"

            message += f"📅 {date_display}\n"

            for game in games:
                home = game.get("home_team", "")
                away = game.get("away_team", "")
                start_time = game.get("start_time", "")
                venue = game.get("venue", "")
                competition = game.get("competition", "")

                if start_time:
                    message += f"🕖 {start_time} {away} vs {home}\n"
                else:
                    message += f"⏰ {away} vs {home}\n"

                if venue:
                    message += f"   📍 {venue}\n"

                if competition and competition not in [home, away]:
                    message += f"   🏆 {competition}\n"

            message += "\n"

        return message

    @staticmethod
    def validate_match_data(data: Dict[str, Any]) -> bool:
        """
        驗證比賽數據

        Args:
            data: 比賽數據

        Returns:
            bool: 是否有效
        """
        # 檢查必要字段
        required_fields = ["home_team", "away_team"]
        for field in required_fields:
            if field not in data or not data[field]:
                logger.warning(f"缺少必要字段: {field}")
                return False

        # 檢查比分（如果比賽已開始或結束）
        status = data.get("status", "").lower()
        if status in ["live", "finished", "halftime"]:
            if "home_score" not in data or "away_score" not in data:
                logger.warning("進行中或已結束的比賽缺少比分")
                return False

        return True

    @staticmethod
    def normalize_team_name(team_name: str) -> str:
        """
        標準化球隊名稱

        Args:
            team_name: 原始球隊名稱

        Returns:
            str: 標準化後的名稱
        """
        # 移除多餘的空格和特殊字符
        normalized = team_name.strip()

        # 常見的標準化映射
        name_mappings = {
            "Los Angeles Lakers": "Lakers",
            "Boston Celtics": "Celtics",
            "Golden State Warriors": "Warriors",
            "Miami Heat": "Heat",
            "Hong Kong": "港足",
            "Kitchee": "傑志",
            "Eastern": "東方龍獅",
            "Wong Chuk Hang": "黃竹坑",
        }

        return name_mappings.get(normalized, normalized)
