"""
足球比分爬蟲
從英超官網、ESPN 等多個數據源獲取足球比分數據
支持英超官網作為主要數據源
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
import re


logger = logging.getLogger(__name__)


from .real_data_fetcher import RealSportsDataFetcher


class FootballScraper:
    """足球比分爬蟲"""

    def __init__(self):
        self.hkjc_url = "https://football.hkjc.com/"
        self.espn_url = "https://www.espn.com/soccer/scoreboard"
        self.premier_league_url = "https://www.premierleague.com/en/matches"
        self.real_fetcher = RealSportsDataFetcher()
        logger.info("初始化足球爬蟲 (支持英超官網數據源)")

    async def fetch_scores(self) -> List[Dict[str, Any]]:
        """
        獲取足球當日比分 - 使用多層數據源

        優先級順序：
        1. 英超官網 (premierleague.com) - 最高優先級
        2. ESPN API - 備用數據源
        3. 模擬數據 - 最後回退

        Returns:
            List[Dict[str, Any]]: 比賽數據列表
        """
        logger.info("開始獲取足球比分 (多層數據源)...")

        # 使用更新後的真實數據獲取器
        try:
            games = await self.real_fetcher.fetch_football_scores()
            logger.info(f"成功獲取 {len(games)} 場比賽")
            return games
        except Exception as e:
            logger.error(f"獲取真實數據失敗: {e}")
            logger.info("回退到模擬數據...")
            return self._get_mock_data()

    async def _fetch_from_hkjc(self) -> List[Dict[str, Any]]:
        """
        從香港馬會獲取數據
        注意：這裡使用模擬數據，因為實際爬取需要 Chrome MCP

        Returns:
            List[Dict[str, Any]]: 香港比賽數據
        """
        # 模擬網頁請求延遲
        await asyncio.sleep(0.1)

        # 模擬馬會頁面結構
        return self._get_mock_hk_data()

    async def _fetch_from_espn(self) -> List[Dict[str, Any]]:
        """
        從 ESPN 獲取數據
        注意：這裡使用模擬數據

        Returns:
            List[Dict[str, Any]]: 國際比賽數據
        """
        # 模擬網頁請求延遲
        await asyncio.sleep(0.1)

        return self._get_mock_intl_data()

    def _get_mock_hk_data(self) -> List[Dict[str, Any]]:
        """
        獲取模擬香港比賽數據

        Returns:
            List[Dict[str, Any]]: 模擬數據
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # 模擬香港比賽
        mock_games = [
            {
                "date": today,
                "home_team": "港足",
                "away_team": "傑志",
                "home_score": 2,
                "away_score": 1,
                "status": "finished",
                "league": "香港超級聯賽",
                "start_time": "19:30",
                "venue": "香港大球場",
                "minute": None,
                "added_time": None,
            },
            {
                "date": today,
                "home_team": "東方龍獅",
                "away_team": "標準流浪",
                "home_score": 1,
                "away_score": 0,
                "status": "live",
                "league": "香港超級聯賽",
                "start_time": "19:30",
                "venue": "旺角大球場",
                "minute": 67,
                "added_time": 2,
            }
        ]

        return mock_games

    def _get_mock_intl_data(self) -> List[Dict[str, Any]]:
        """
        獲取模擬國際比賽數據

        Returns:
            List[Dict[str, Any]]: 模擬數據
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # 模擬國際比賽
        mock_games = [
            {
                "date": today,
                "home_team": "曼城",
                "away_team": "利物浦",
                "home_score": 3,
                "away_score": 1,
                "status": "finished",
                "league": "英超",
                "start_time": "22:00",
                "venue": "Etihad Stadium",
                "minute": None,
                "added_time": None,
            },
            {
                "date": today,
                "home_team": "皇馬",
                "away_team": "巴塞隆拿",
                "home_score": 2,
                "away_score": 1,
                "status": "live",
                "league": "西甲",
                "start_time": "23:30",
                "venue": "班拿貝球場",
                "minute": 43,
                "added_time": 1,
            }
        ]

        return mock_games

    def _get_mock_data(self) -> List[Dict[str, Any]]:
        """
        獲取完整的模擬數據

        Returns:
            List[Dict[str, Any]]: 完整的模擬數據
        """
        hk_data = self._get_mock_hk_data()
        intl_data = self._get_mock_intl_data()
        return hk_data + intl_data

    async def fetch_schedule(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        獲取足球賽程 - 使用多層數據源

        優先級順序：
        1. 英超官網 (premierleague.com) - 最高優先級
        2. 備用數據源 - 備用賽程
        3. 模擬賽程 - 最後回退

        Args:
            days: 天數

        Returns:
            List[Dict[str, Any]]: 賽程數據列表
        """
        logger.info(f"獲取未來 {days} 天的足球賽程 (多層數據源)...")

        # 使用更新後的真實數據獲取器
        try:
            schedule = await self.real_fetcher.fetch_schedule(days)
            logger.info(f"成功獲取 {len(schedule)} 場賽程")
            return schedule
        except Exception as e:
            logger.error(f"獲取真實賽程失敗: {e}")
            logger.info("回退到模擬賽程...")
            return self._get_mock_schedule(days)

    def _get_mock_schedule(self, days: int) -> List[Dict[str, Any]]:
        """
        獲取模擬賽程數據

        Args:
            days: 天數

        Returns:
            List[Dict[str, Any]]: 模擬賽程數據
        """
        schedule = []
        today = datetime.now()

        # 模擬未來幾天的賽程
        for i in range(1, min(days + 1, 8)):
            game_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
            game_date = game_date.replace(day=today.day + i)

            # 每天添加 1-2 場比賽
            schedule.append({
                "date": game_date.strftime("%Y-%m-%d"),
                "home_team": "港足",
                "away_team": "東方龍獅",
                "start_time": "19:30",
                "venue": "香港大球場",
                "competition": "香港超級聯賽",
                "league": "香港超級聯賽",
            })

            if i % 2 == 0:
                schedule.append({
                    "date": game_date.strftime("%Y-%m-%d"),
                    "home_team": "曼聯",
                    "away_team": "阿仙奴",
                    "start_time": "21:00",
                    "venue": "Old Trafford",
                    "competition": "英超",
                    "league": "英超",
                })

        return schedule

    def parse_match_time(self, time_text: str) -> Dict[str, Any]:
        """
        解析比賽時間

        Args:
            time_text: 時間文本 (例如: "67'+3", "半場", "90")

        Returns:
            Dict[str, Any]: 解析後的時間信息
        """
        if "半場" in time_text or "halftime" in time_text.lower():
            return {"status": "halftime", "minute": 45, "is_live": True}

        # 匹配補時時間 (例如: "67'+3")
        added_time_match = re.search(r"(\d+)'\+(\d+)", time_text)
        if added_time_match:
            minute = int(added_time_match.group(1))
            added_time = int(added_time_match.group(2))
            return {
                "status": "live",
                "minute": minute,
                "added_time": added_time,
                "is_live": True
            }

        # 匹配常規時間 (例如: "67'")
        time_match = re.search(r"(\d+)'", time_text)
        if time_match:
            minute = int(time_match.group(1))
            return {
                "status": "live",
                "minute": minute,
                "added_time": 0,
                "is_live": minute < 90
            }

        # 匹配 "90" 或 "90+"
        if time_text in ["90", "90+"] or "補時" in time_text:
            return {"status": "finished", "minute": 90, "is_live": False}

        return {"status": "unknown", "minute": 0, "is_live": False}

    def format_team_name(self, team_name: str) -> str:
        """
        格式化球隊名稱

        Args:
            team_name: 原始球隊名稱

        Returns:
            str: 格式化後的名稱
        """
        # 名稱映射
        name_mappings = {
            "Manchester United": "曼聯",
            "Arsenal": "阿仙奴",
            "Liverpool": "利物浦",
            "Manchester City": "曼城",
            "Real Madrid": "皇馬",
            "Barcelona": "巴塞隆拿",
            "Hong Kong": "港足",
            "Kitchee": "傑志",
            "Eastern": "東方龍獅",
            "South China": "南華",
            "Rangers": "流浪",
        }

        return name_mappings.get(team_name, team_name)

    def get_competition_emoji(self, league: str) -> str:
        """
        獲取聯賽表情符號

        Args:
            league: 聯賽名稱

        Returns:
            str: 表情符號
        """
        emoji_map = {
            "香港超級聯賽": "🏆",
            "英超": "🥇",
            "西甲": "🥇",
            "德甲": "🥇",
            "意甲": "🥇",
            "法甲": "🥇",
            "世界杯": "🏆",
            "歐洲盃": "🏆",
            "亞洲杯": "🏆",
        }

        return emoji_map.get(league, "⚽")
