"""
NBA 比分爬蟲
從 ESPN 獲取 NBA 比分數據
"""

import asyncio
import logging
import re
from typing import Dict, Any, List
from datetime import datetime
import json
import aiohttp


logger = logging.getLogger(__name__)


class NBAScraper:
    """NBA 比分爬蟲"""

    def __init__(self):
        self.base_url = "https://www.espn.com/nba/scoreboard"
        self.espn_api_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
        self.backup_url = "https://www.nba.com/games"

    async def fetch_scores(self) -> List[Dict[str, Any]]:
        """
        獲取 NBA 當日比分

        Returns:
            List[Dict[str, Any]]: 比賽數據列表
        """
        logger.info("開始獲取 NBA 比分...")

        # 嘗試從 ESPN 獲取
        try:
            games = await self._fetch_from_espn()
            if games:
                logger.info(f"從 ESPN 成功獲取 {len(games)} 場比賽")
                return games
        except Exception as e:
            logger.error(f"從 ESPN 獲取失敗: {e}")

        # 備用方案：返回模擬數據
        logger.warning("使用備用模擬數據")
        return self._get_mock_data()

    async def _fetch_from_espn(self) -> List[Dict[str, Any]]:
        """
        從 ESPN NBA API 獲取真實數據

        Returns:
            List[Dict[str, Any]]: 比賽數據列表

        Raises:
            Exception: 當 API 調用失敗時
        """
        logger.info("正在從 ESPN NBA API 獲取數據...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.espn_api_url, timeout=10) as response:
                    if response.status != 200:
                        logger.error(f"ESPN API 返回狀態碼: {response.status}")
                        raise Exception(f"API 請求失敗，狀態碼: {response.status}")

                    data = await response.json()
                    logger.info("成功獲取 ESPN NBA API 響應")

                    # 解析響應數據
                    games = self._parse_espn_response(data)

                    if not games:
                        logger.warning("ESPN API 響應中未找到比賽數據")
                        raise Exception("未找到比賽數據")

                    logger.info(f"成功解析 {len(games)} 場比賽")
                    return games

        except asyncio.TimeoutError:
            logger.error("ESPN NBA API 請求超時（10秒）")
            raise
        except aiohttp.ClientError as e:
            logger.error(f"ESPN NBA API 客戶端錯誤: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"ESPN NBA API JSON 解析錯誤: {e}")
            raise
        except Exception as e:
            logger.error(f"獲取 ESPN NBA 數據時發生未知錯誤: {e}")
            raise

    def _parse_espn_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        解析 ESPN API 響應數據（site/v2 格式）

        Args:
            data: ESPN API 響應的 JSON 數據

        Returns:
            List[Dict[str, Any]]: 解析後的比賽數據列表
        """
        games = []

        try:
            # ESPN site/v2 API 響應結構：data['events']
            events = data.get('events', [])

            if not events:
                logger.warning("ESPN 響應中未找到 'events' 字段")
                return games

            for event in events:
                try:
                    # 獲取比賽基本信息
                    competitions = event.get('competitions', [])
                    if not competitions:
                        logger.warning("事件中未找到 'competitions' 字段，跳過")
                        continue

                    competition = competitions[0]
                    competitors = competition.get('competitors', [])

                    if len(competitors) < 2:
                        logger.warning("比賽中競爭者不足，跳過")
                        continue

                    # 提取主隊和客隊信息
                    home_team = None
                    away_team = None
                    home_score = 0
                    away_score = 0

                    for competitor in competitors:
                        team = competitor.get('team', {})
                        # 獲取球隊名稱（優先使用 displayName）
                        team_name = team.get('displayName', team.get('shortDisplayName', ''))

                        if competitor.get('homeAway') == 'home':
                            home_team = self.format_team_name(team_name)
                            # 獲取比分
                            try:
                                home_score = int(competitor.get('score', 0))
                            except (ValueError, TypeError):
                                home_score = 0
                        elif competitor.get('homeAway') == 'away':
                            away_team = self.format_team_name(team_name)
                            # 獲取比分
                            try:
                                away_score = int(competitor.get('score', 0))
                            except (ValueError, TypeError):
                                away_score = 0

                    # 如果無法獲取球隊信息，跳過該比賽
                    if not home_team or not away_team:
                        logger.warning(f"跳過缺少球隊信息的比賽: {home_team} vs {away_team}")
                        continue

                    # 獲取比賽狀態
                    status = event.get('status', {})
                    status_type = status.get('type', {})
                    # 從狀態中獲取描述
                    competition_status = status_type.get('description', 'Scheduled')

                    # 解析比賽狀態
                    parsed_status = self.parse_game_status(competition_status)
                    status_text = parsed_status['status']

                    # 提取時間信息（NBA API 可能包含 clock 和 period）
                    quarter = None
                    time_remaining = None

                    # 從狀態中提取時間
                    clock = status.get('clock')
                    period = status.get('period')

                    if clock and isinstance(clock, (int, float)):
                        # NBA 時鐘以秒為單位，轉換為 MM:SS 格式
                        minutes = int(clock) // 60
                        seconds = int(clock) % 60
                        time_remaining = f"{minutes}:{seconds:02d}"

                    if period:
                        if period < 5:
                            quarter = f"Q{period}"
                        else:
                            quarter = f"OT{period - 4}"

                    # 獲取比赛日期和時間
                    event_date = event.get('date', '')
                    start_time = ''
                    if event_date:
                        try:
                            # ESPN API 提供的日期是 ISO 格式
                            dt = datetime.fromisoformat(event_date.replace('Z', '+00:00'))
                            start_time = dt.strftime('%H:%M')
                            date_str = dt.strftime('%Y-%m-%d')
                        except Exception:
                            date_str = datetime.now().strftime('%Y-%m-%d')
                    else:
                        # 從 day 字段獲取日期（site/v2 API 可能使用 day 字段）
                        day = data.get('day', {})
                        day_date = day.get('date', '')
                        if day_date:
                            date_str = day_date
                        else:
                            date_str = datetime.now().strftime('%Y-%m-%d')

                    # 獲取球場信息
                    venue = ''
                    venue_info = competition.get('venue', {})
                    if venue_info:
                        venue = venue_info.get('fullName', '')

                    # 構建比賽數據
                    game_data = {
                        'date': date_str,
                        'home_team': home_team,
                        'away_team': away_team,
                        'home_score': home_score,
                        'away_score': away_score,
                        'status': status_text,
                        'quarter': quarter,
                        'time_remaining': time_remaining,
                        'start_time': start_time,
                        'venue': venue,
                        'league': 'NBA'
                    }

                    games.append(game_data)

                except Exception as e:
                    logger.warning(f"解析單個比賽數據時發生錯誤: {e}")
                    continue

        except Exception as e:
            logger.error(f"解析 ESPN API 響應時發生錯誤: {e}")

        return games

    def _get_mock_data(self) -> List[Dict[str, Any]]:
        """
        獲取模擬數據（用於測試和演示）

        Returns:
            List[Dict[str, Any]]: 模擬的 NBA 比賽數據
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # 檢查是否是比賽日（週末通常是比賽日）
        today_obj = datetime.strptime(today, "%Y-%m-%d")
        is_weekend = today_obj.weekday() >= 5

        if not is_weekend:
            # 工作日通常沒有 NBA 比赛
            return []

        # 返回一些模擬的比賽數據
        mock_games = [
            {
                "date": today,
                "home_team": "Lakers",
                "away_team": "Celtics",
                "home_score": 118,
                "away_score": 102,
                "status": "finished",
                "quarter": "Final",
                "time_remaining": "0:00",
                "start_time": "10:30",
                "venue": "Crypto.com Arena",
                "league": "NBA",
                "home_odds": 52.3,
                "away_odds": 49.1,
            },
            {
                "date": today,
                "home_team": "Warriors",
                "away_team": "Suns",
                "home_score": 108,
                "away_score": 95,
                "status": "finished",
                "quarter": "Final",
                "time_remaining": "0:00",
                "start_time": "08:00",
                "venue": "Chase Center",
                "league": "NBA",
                "home_odds": 48.7,
                "away_odds": 45.2,
            },
            {
                "date": today,
                "home_team": "Bucks",
                "away_team": "Heat",
                "home_score": 89,
                "away_score": 87,
                "status": "live",
                "quarter": "Q3",
                "time_remaining": "5:32",
                "start_time": "07:00",
                "venue": "Fiserv Forum",
                "league": "NBA",
            },
            {
                "date": today,
                "home_team": "Nuggets",
                "away_team": "Clippers",
                "home_score": 0,
                "away_score": 0,
                "status": "scheduled",
                "quarter": None,
                "time_remaining": None,
                "start_time": "10:30",
                "venue": "Ball Arena",
                "league": "NBA",
            }
        ]

        return mock_games

    async def fetch_schedule(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        獲取 NBA 賽程

        Args:
            days: 天數

        Returns:
            List[Dict[str, Any]]: 賽程數據列表
        """
        logger.info(f"獲取未來 {days} 天的 NBA 賽程...")

        # 返回模擬的賽程數據
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

            # 只在週末添加比賽
            if game_date.weekday() in [5, 6]:  # 週六和週日
                schedule.append({
                    "date": game_date.strftime("%Y-%m-%d"),
                    "home_team": "Lakers" if i % 2 == 0 else "Warriors",
                    "away_team": "Celtics" if i % 2 == 0 else "Suns",
                    "start_time": "10:30" if i % 2 == 0 else "08:00",
                    "venue": "Crypto.com Arena" if i % 2 == 0 else "Chase Center",
                    "competition": "NBA",
                })

        return schedule

    async def get_team_stats(self, team_name: str) -> Dict[str, Any]:
        """
        獲取球隊統計信息

        Args:
            team_name: 球隊名稱

        Returns:
            Dict[str, Any]: 球隊統計
        """
        # 模擬球隊統計數據
        mock_stats = {
            "team_name": team_name,
            "wins": 42,
            "losses": 30,
            "win_rate": 58.3,
            "home_record": "25-11",
            "away_record": "17-19",
            "conference_rank": "西部第 5",
            "last_10": "7-3",
            "points_per_game": 115.2,
            "points_allowed": 112.8,
        }

        return mock_stats

    def parse_game_status(self, status_text: str) -> Dict[str, Any]:
        """
        解析比賽狀態

        Args:
            status_text: ESPN API 提供的狀態文本

        Returns:
            Dict[str, Any]: 解析後的狀態
        """
        status_lower = status_text.lower()

        # ESPN API 常見狀態: "Final", "In Progress", "Scheduled", "Pre-Game"
        if "final" in status_lower or "complete" in status_lower:
            return {
                "status": "finished",
                "is_live": False,
                "quarter": "Final",
                "time_remaining": "0:00"
            }

        if "in progress" in status_lower or "halftime" in status_lower:
            # 嘗試從狀態文本中提取節次和時間
            quarter = None
            time_remaining = None

            # 提取節次
            quarter_match = re.search(r'(q\d|first|second|third|fourth|ot)', status_lower)
            if quarter_match:
                quarter_raw = quarter_match.group(1).upper()
                if quarter_raw == "FIRST":
                    quarter = "Q1"
                elif quarter_raw == "SECOND":
                    quarter = "Q2"
                elif quarter_raw == "THIRD":
                    quarter = "Q3"
                elif quarter_raw == "FOURTH":
                    quarter = "Q4"
                elif quarter_raw.startswith("Q"):
                    quarter = quarter_raw
                elif "OT" in quarter_raw:
                    quarter = "OT"

            # 提取時間 (NBA 用 MM:SS 格式)
            time_match = re.search(r'(\d{1,2}):(\d{2})', status_text)
            if time_match:
                time_remaining = f"{time_match.group(1)}:{time_match.group(2)}"

            # 如果是中场休息
            if "halftime" in status_lower:
                quarter = "Half"
                time_remaining = "0:00"

            return {
                "status": "live",
                "is_live": True,
                "quarter": quarter,
                "time_remaining": time_remaining
            }

        if "scheduled" in status_lower or "pre-game" in status_lower or "scheduled" in status_lower:
            return {
                "status": "scheduled",
                "is_live": False,
                "quarter": None,
                "time_remaining": None
            }

        # 其他未知狀態
        return {
            "status": "unknown",
            "is_live": False,
            "quarter": None,
            "time_remaining": None
        }

    def format_team_name(self, team_name: str) -> str:
        """
        格式化球隊名稱

        Args:
            team_name: 原始球隊名稱（來自 ESPN API）

        Returns:
            str: 簡化後的球隊名稱
        """
        # 名稱映射 - ESPN API 完整名稱 -> 簡化名稱
        name_mappings = {
            # 西部球隊
            "Los Angeles Lakers": "Lakers",
            "Los Angeles Clippers": "Clippers",
            "Golden State Warriors": "Warriors",
            "Phoenix Suns": "Suns",
            "Denver Nuggets": "Nuggets",
            "Minnesota Timberwolves": "Timberwolves",
            "Oklahoma City Thunder": "Thunder",
            "Utah Jazz": "Jazz",
            "Portland Trail Blazers": "Trail Blazers",
            "Sacramento Kings": "Kings",
            "Dallas Mavericks": "Mavericks",
            "Houston Rockets": "Rockets",
            "Memphis Grizzlies": "Grizzlies",
            "New Orleans Pelicans": "Pelicans",
            "San Antonio Spurs": "Spurs",

            # 東部球隊
            "Boston Celtics": "Celtics",
            "Brooklyn Nets": "Nets",
            "New York Knicks": "Knicks",
            "Philadelphia 76ers": "76ers",
            "Toronto Raptors": "Raptors",
            "Chicago Bulls": "Bulls",
            "Cleveland Cavaliers": "Cavaliers",
            "Detroit Pistons": "Pistons",
            "Indiana Pacers": "Pacers",
            "Milwaukee Bucks": "Bucks",
            "Atlanta Hawks": "Hawks",
            "Charlotte Hornets": "Hornets",
            "Miami Heat": "Heat",
            "Orlando Magic": "Magic",
            "Washington Wizards": "Wizards",

            # 可能的簡稱
            "Lakers": "Lakers",
            "Clippers": "Clippers",
            "Warriors": "Warriors",
            "Suns": "Suns",
            "Nuggets": "Nuggets",
            "Timberwolves": "Timberwolves",
            "Thunder": "Thunder",
            "Jazz": "Jazz",
            "Trail Blazers": "Trail Blazers",
            "Kings": "Kings",
            "Mavericks": "Mavericks",
            "Rockets": "Rockets",
            "Grizzlies": "Grizzlies",
            "Pelicans": "Pelicans",
            "Spurs": "Spurs",
            "Celtics": "Celtics",
            "Nets": "Nets",
            "Knicks": "Knicks",
            "76ers": "76ers",
            "Raptors": "Raptors",
            "Bulls": "Bulls",
            "Cavaliers": "Cavaliers",
            "Pistons": "Pistons",
            "Pacers": "Pacers",
            "Bucks": "Bucks",
            "Hawks": "Hawks",
            "Hornets": "Hornets",
            "Heat": "Heat",
            "Magic": "Magic",
            "Wizards": "Wizards",
        }

        return name_mappings.get(team_name, team_name)
