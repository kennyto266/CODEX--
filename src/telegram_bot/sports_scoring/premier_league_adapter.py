"""
英超聯賽官網數據適配器
使用 Chrome DevTools MCP 從英超官網獲取比分和賽程數據
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
import json
import re
import time
from dataclasses import dataclass

from .base_scraper import BaseScraper
from .premier_league_monitor import get_monitor, measure_performance

logger = logging.getLogger(__name__)


@dataclass
class MatchStatus:
    """比賽狀態枚舉"""
    SCHEDULED = "scheduled"
    LIVE = "live"
    HALFTIME = "halftime"
    FINISHED = "finished"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"


@dataclass
class PremierLeagueMatch:
    """英超比賽數據結構"""
    match_id: str
    home_team: str
    away_team: str
    home_score: int = 0
    away_score: int = 0
    status: str = MatchStatus.SCHEDULED
    minute: Optional[int] = None
    added_time: Optional[int] = None
    start_time_gmt: str = ""
    start_time_hkt: str = ""
    date: str = ""
    competition: str = "英超"
    venue: Optional[str] = None
    matchweek: Optional[int] = None
    last_update: Optional[datetime] = None
    data_source: str = "premierleague.com"

    @property
    def is_live(self) -> bool:
        """檢查比賽是否進行中"""
        return self.status == MatchStatus.LIVE

    @property
    def display_time(self) -> str:
        """返回顯示用時間"""
        if self.status == MatchStatus.LIVE:
            if self.added_time:
                return f"{self.minute}'+{self.added_time}"
            return f"{self.minute}'"
        return self.start_time_hkt

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "date": self.date,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "home_score": self.home_score,
            "away_score": self.away_score,
            "status": self.status,
            "league": self.competition,
            "start_time": self.start_time_hkt,
            "venue": self.venue,
            "minute": self.minute,
            "added_time": self.added_time,
            "matchweek": self.matchweek,
            "display_time": self.display_time,
        }


class PremierLeagueAdapter(BaseScraper):
    """英超聯賽官網數據適配器"""

    def __init__(self):
        super().__init__("PremierLeagueAdapter")
        self.base_url = "https://www.premierleague.com/en/matches"
        self.current_season = 2025
        self.current_matchweek = None
        self.current_month = None
        self._chrome_mcp_available = False
        self._cache = {}
        self._cache_timeout = 300  # 5分鐘緩存
        self.monitor = get_monitor()

        # 球隊名稱映射 (英文 -> 中文)
        self.team_name_mapping = {
            "Arsenal": "阿仙奴",
            "Aston Villa": "阿士東維拉",
            "Brighton & Hove Albion": "白禮頓",
            "Burnley": "般尼",
            "Chelsea": "車路士",
            "Crystal Palace": "水晶宮",
            "Everton": "愛華頓",
            "Fulham": "富咸",
            "Liverpool": "利物浦",
            "Luton Town": "盧頓",
            "Manchester City": "曼城",
            "Manchester United": "曼聯",
            "Newcastle United": "紐卡素",
            "Norwich City": "諾域治",
            "Nottingham Forest": "諾定咸森林",
            "Sheffield United": "錫菲聯",
            "Tottenham Hotspur": "熱刺",
            "West Ham United": "韋斯咸",
            "Wolverhampton Wanderers": "狼隊",
            "Brentford": "賓福特",
            "Leicester City": "李斯特城",
            "Leeds United": "列斯聯",
            "Southampton": "修咸頓",
            "West Bromwich Albion": "西布朗",
            "Watford": "屈福特",
            "Bournemouth": "般尼茅夫",
            "Huddersfield Town": "哈特斯菲爾德",
        }

        # CSS 選擇器
        self.selectors = {
            "matches": 'div[data-match-status]',
            "home_team": 'span[data-testid="home-team"]',
            "away_team": 'span[data-testid="away-team"]',
            "home_score": 'span[data-testid="home-score"]',
            "away_score": 'span[data-testid="away-score"]',
            "status": 'span[data-testid="match-status"]',
            "minute": 'span[data-testid="match-minute"]',
            "venue": 'span[data-testid="match-venue"]',
            "date": 'span[data-testid="match-date"]',
            "matchweek": 'div[data-testid="matchweek"]',
        }

    async def initialize(self):
        """初始化適配器"""
        logger.info("初始化英超適配器...")
        try:
            # 檢查 Chrome MCP 可用性
            self._chrome_mcp_available = await self._check_chrome_mcp()
            if self._chrome_mcp_available:
                logger.info("✓ Chrome MCP 可用")
            else:
                logger.warning("⚠ Chrome MCP 不可用，將使用備用方案")

            # 自動檢測當前輪次和月份
            await self._detect_current_matchweek()
            return True
        except Exception as e:
            logger.error(f"初始化失敗: {e}")
            return False

    async def _check_chrome_mcp(self) -> bool:
        """檢查 Chrome MCP 是否可用"""
        try:
            # 嘗試創建一個簡單的頁面來測試 MCP
            # 實際實現中，這裡會使用 mcp__chrome-devtools 相關工具
            return True
        except Exception as e:
            logger.warning(f"Chrome MCP 檢查失敗: {e}")
            return False

    async def _detect_current_matchweek(self):
        """自動檢測當前輪次和月份"""
        now = datetime.now()
        # 根據當前日期估算輪次 (英超賽季從8月開始)
        month = now.month
        self.current_month = month

        # 簡單估算：每輪比賽間隔約一週
        # 實際實現中應該從官網獲取
        if month >= 8 and month <= 12:
            self.current_matchweek = min((month - 8) * 4 + 1, 38)
        elif month >= 1 and month <= 5:
            self.current_matchweek = min((month + 4) * 4 + 1, 38)
        else:
            self.current_matchweek = 1

        logger.info(f"當前輪次: {self.current_matchweek}, 月份: {self.current_month}")

    @measure_performance("premier_league_adapter")
    async def fetch_data(self, **kwargs) -> Dict[str, Any]:
        """
        從英超官網獲取原始數據

        Args:
            **kwargs: 可選參數
                - matchweek: 特定輪次
                - month: 特定月份
                - force_refresh: 強制刷新緩存

        Returns:
            Dict[str, Any]: 原始數據
        """
        matchweek = kwargs.get('matchweek', self.current_matchweek)
        month = kwargs.get('month', self.current_month)
        force_refresh = kwargs.get('force_refresh', False)

        cache_hit = False

        # 檢查緩存
        cache_key = f"pl_scores_{matchweek}_{month}"
        if not force_refresh and cache_key in self._cache:
            cache_time, cache_data = self._cache[cache_key]
            if datetime.now().timestamp() - cache_time < self._cache_timeout:
                logger.info(f"✓ 返回緩存數據 (緩存時間: {cache_time})")
                cache_hit = True
                # 記錄緩存命中
                self.monitor.record_request(
                    response_time=0.001,
                    success=True,
                    data_source="premier_league_cache",
                    cache_hit=True
                )
                return cache_data

        logger.info(f"從英超官網獲取數據 - 輪次: {matchweek}, 月份: {month}")

        try:
            # 構建 URL
            url = f"{self.base_url}?competition=8&season={self.current_season}&matchweek={matchweek}&month={month}"

            # 嘗試使用 Chrome MCP 獲取數據
            if self._chrome_mcp_available:
                raw_data = await self._fetch_via_chrome_mcp(url)
            else:
                # 備用方案：使用 requests
                raw_data = await self._fetch_via_requests(url)

            if not raw_data:
                raise ValueError("未獲取到任何數據")

            # 緩存數據
            self._cache[cache_key] = (datetime.now().timestamp(), raw_data)

            return raw_data

        except Exception as e:
            logger.error(f"獲取數據失敗: {e}")
            raise

    async def _fetch_via_chrome_mcp(self, url: str) -> Dict[str, Any]:
        """
        通過 Chrome MCP 獲取數據

        Args:
            url: 目標 URL

        Returns:
            Dict[str, Any]: 獲取的數據
        """
        logger.info(f"使用 Chrome MCP 導航到: {url}")

        try:
            # 導航到頁面
            # await mcp__chrome-devtools__navigate_page(url=url)

            # 等待頁面加載
            # await asyncio.sleep(3)

            # 獲取頁面快照
            # snapshot = await mcp__chrome-devtools__take_snapshot(verbose=True)

            # 解析頁面數據
            # matches_data = await self._extract_matches_from_snapshot(snapshot)

            # 暫時返回模擬數據，實際實現中會使用上述 MCP 工具
            return await self._get_mock_data_for_development()

        except Exception as e:
            logger.error(f"Chrome MCP 獲取失敗: {e}")
            raise

    async def _fetch_via_requests(self, url: str) -> Dict[str, Any]:
        """
        通過 requests 獲取數據（備用方案）

        Args:
            url: 目標 URL

        Returns:
            Dict[str, Any]: 獲取的數據
        """
        logger.info(f"使用 requests 獲取: {url}")

        import aiohttp

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        return {"html": html, "url": url}
                    else:
                        raise ValueError(f"HTTP {response.status}: {response.reason}")
        except Exception as e:
            logger.error(f"Requests 獲取失敗: {e}")
            raise

    async def _extract_matches_from_snapshot(self, snapshot: Dict) -> List[Dict]:
        """
        從頁面快照中提取比賽數據

        Args:
            snapshot: 頁面快照數據

        Returns:
            List[Dict]: 比賽數據列表
        """
        # 實現頁面數據解析邏輯
        # 這裡會根據實際的 DOM 結構來提取數據
        matches = []

        try:
            # 解析快照數據
            # elements = snapshot.get('elements', [])

            # 遍歷元素並提取比賽信息
            # for element in elements:
            #     if self._is_match_element(element):
            #         match_data = self._parse_match_element(element)
            #         matches.append(match_data)

            pass
        except Exception as e:
            logger.error(f"解析快照數據失敗: {e}")

        return matches

    def _is_match_element(self, element: Dict) -> bool:
        """判斷元素是否為比賽元素"""
        # 實現比賽元素判斷邏輯
        return False

    def _parse_match_element(self, element: Dict) -> Dict:
        """解析單個比賽元素"""
        # 實現比賽元素解析邏輯
        return {}

    async def _get_mock_data_for_development(self) -> Dict[str, Any]:
        """
        開發階段使用的模擬數據
        實際部署時將移除此方法
        """
        logger.warning("⚠ 使用模擬數據 (開發階段)")

        today = datetime.now()
        current_hour = today.hour
        current_minute = today.minute

        # 根據當前時間生成動態數據
        if 12 <= current_hour <= 23:
            # 比赛进行中
            game_minute = (current_hour * 60 + current_minute - 19 * 60) % 90
            if game_minute < 0:
                game_minute = 0

            if game_minute < 45:
                status = "live"
                minute = game_minute
            elif 45 <= game_minute < 60:
                status = "halftime"
                minute = 45
            else:
                status = "live"
                minute = min(game_minute - 15, 90)

            if current_hour >= 22:
                status = "finished"
                minute = None

            return {
                "matches": [
                    {
                        "home_team": "曼城",
                        "away_team": "利物浦",
                        "home_score": 1 if status == "finished" else 1,
                        "away_score": 0 if status == "finished" else 0,
                        "status": status,
                        "minute": minute,
                        "added_time": 2 if minute and minute > 85 else None,
                        "venue": "Etihad Stadium",
                        "matchweek": self.current_matchweek,
                    },
                    {
                        "home_team": "阿仙奴",
                        "away_team": "車路士",
                        "home_score": 2 if status == "finished" else 0,
                        "away_score": 1 if status == "finished" else 0,
                        "status": status,
                        "minute": minute,
                        "added_time": 1 if minute and minute > 85 else None,
                        "venue": "酋長球場",
                        "matchweek": self.current_matchweek,
                    },
                ],
                "source": "mock_data",
                "timestamp": datetime.now().isoformat(),
            }
        else:
            # 比赛已结束或还未开始
            return {
                "matches": [
                    {
                        "home_team": "曼城",
                        "away_team": "利物浦",
                        "home_score": 2,
                        "away_score": 1,
                        "status": "finished",
                        "venue": "Etihad Stadium",
                        "matchweek": self.current_matchweek,
                    },
                    {
                        "home_team": "阿仙奴",
                        "away_team": "車路士",
                        "home_score": 1,
                        "away_score": 0,
                        "status": "finished",
                        "venue": "酋長球場",
                        "matchweek": self.current_matchweek,
                    },
                ],
                "source": "mock_data",
                "timestamp": datetime.now().isoformat(),
            }

    async def parse_data(self, raw_data: Dict[str, Any]) -> List[PremierLeagueMatch]:
        """
        解析原始數據為 PremierLeagueMatch 對象列表

        Args:
            raw_data: 原始數據

        Returns:
            List[PremierLeagueMatch]: 解析後的比賽列表
        """
        logger.info("開始解析英超數據...")

        try:
            matches_data = raw_data.get("matches", [])
            matches = []

            for match_data in matches_data:
                try:
                    match = await self._parse_single_match(match_data)
                    if match:
                        matches.append(match)
                except Exception as e:
                    logger.warning(f"解析單場比賽失敗: {e}")
                    continue

            logger.info(f"✓ 成功解析 {len(matches)} 場比賽")
            return matches

        except Exception as e:
            logger.error(f"解析數據失敗: {e}")
            raise

    async def _parse_single_match(self, match_data: Dict[str, Any]) -> Optional[PremierLeagueMatch]:
        """
        解析單場比賽數據

        Args:
            match_data: 單場比賽原始數據

        Returns:
            PremierLeagueMatch: 解析後的比賽對象
        """
        try:
            # 提取基本信息
            home_team_en = match_data.get("home_team", "")
            away_team_en = match_data.get("away_team", "")

            # 轉換為中文名稱
            home_team = self.team_name_mapping.get(home_team_en, home_team_en)
            away_team = self.team_name_mapping.get(away_team_en, away_team_en)

            # 處理比分
            home_score = int(match_data.get("home_score", 0))
            away_score = int(match_data.get("away_score", 0))

            # 處理狀態
            status = match_data.get("status", MatchStatus.SCHEDULED)

            # 處理時間
            minute = match_data.get("minute")
            if minute is not None:
                minute = int(minute)

            added_time = match_data.get("added_time")
            if added_time is not None:
                added_time = int(added_time)

            # 處理時區轉換
            start_time_gmt = match_data.get("start_time", "")
            start_time_hkt = await self._convert_timezone(start_time_gmt)

            # 創建比賽對象
            match = PremierLeagueMatch(
                match_id=f"pl_{self.current_matchweek}_{hash(f'{home_team}_{away_team}')}",
                home_team=home_team,
                away_team=away_team,
                home_score=home_score,
                away_score=away_score,
                status=status,
                minute=minute,
                added_time=added_time,
                start_time_gmt=start_time_gmt,
                start_time_hkt=start_time_hkt,
                date=datetime.now().strftime("%Y-%m-%d"),
                competition="英超",
                venue=match_data.get("venue"),
                matchweek=match_data.get("matchweek", self.current_matchweek),
                last_update=datetime.now(),
            )

            return match

        except Exception as e:
            logger.error(f"解析比賽數據失敗: {e}")
            return None

    async def _convert_timezone(self, gmt_time: str) -> str:
        """
        將 GMT 時間轉換為 HKT 時間

        Args:
            gmt_time: GMT 時間字符串

        Returns:
            str: HKT 時間字符串
        """
        try:
            if not gmt_time:
                return ""

            # 解析 GMT 時間
            # 格式示例: "2025-10-31T19:30:00Z"
            if gmt_time.endswith("Z"):
                gmt_time = gmt_time[:-1]

            dt_gmt = datetime.fromisoformat(gmt_time).replace(tzinfo=timezone.utc)

            # 轉換為 HKT (UTC+8)
            hkt_timezone = timezone(timedelta(hours=8))
            dt_hkt = dt_gmt.astimezone(hkt_timezone)

            return dt_hkt.strftime("%H:%M")

        except Exception as e:
            logger.warning(f"時區轉換失敗: {e}")
            return gmt_time

    async def validate_data(self, data: List[PremierLeagueMatch]) -> List[PremierLeagueMatch]:
        """
        驗證比賽數據完整性

        Args:
            data: 待驗證的比賽列表

        Returns:
            List[PremierLeagueMatch]: 驗證後的比賽列表
        """
        if not data:
            logger.warning("沒有數據需要驗證")
            return []

        valid_matches = []
        for match in data:
            # 基本驗證
            if not match.home_team or not match.away_team:
                logger.warning(f"跳過無效比賽: 缺少隊伍信息")
                continue

            # 比分驗證
            if match.home_score < 0 or match.away_score < 0:
                logger.warning(f"跳過無效比賽: 負比分 - {match.home_team} vs {match.away_team}")
                continue

            # 狀態驗證
            valid_statuses = [
                MatchStatus.SCHEDULED,
                MatchStatus.LIVE,
                MatchStatus.HALFTIME,
                MatchStatus.FINISHED,
                MatchStatus.POSTPONED,
                MatchStatus.CANCELLED,
            ]
            if match.status not in valid_statuses:
                logger.warning(f"未知比賽狀態: {match.status}")
                match.status = MatchStatus.SCHEDULED

            valid_matches.append(match)

        logger.info(f"✓ 驗證完成: {len(valid_matches)}/{len(data)} 場比賽有效")
        return valid_matches

    async def fetch_premier_league_scores(self, **kwargs) -> List[Dict[str, Any]]:
        """
        獲取英超比分 (對外接口)

        Args:
            **kwargs: 參數

        Returns:
            List[Dict[str, Any]]: 比分列表
        """
        try:
            logger.info("開始獲取英超比分...")

            # 獲取原始數據
            raw_data = await self.fetch_data(**kwargs)

            # 解析數據
            matches = await self.parse_data(raw_data)

            # 驗證數據
            valid_matches = await self.validate_data(matches)

            # 轉換為字典格式
            return [match.to_dict() for match in valid_matches]

        except Exception as e:
            logger.error(f"獲取英超比分失敗: {e}")
            raise

    async def fetch_premier_league_schedule(self, days: int = 7, **kwargs) -> List[Dict[str, Any]]:
        """
        獲取英超賽程 (對外接口)

        Args:
            days: 天數
            **kwargs: 參數

        Returns:
            List[Dict[str, Any]]: 賽程列表
        """
        logger.info(f"獲取未來 {days} 天的英超賽程...")

        # 目前返回模擬數據
        # 實際實現中會從英超官網獲取未來賽程
        schedule = []
        today = datetime.now()

        from dateutil.relativedelta import relativedelta

        for i in range(1, min(days + 1, 8)):
            # 使用 relativedelta 來正確處理月份變化
            game_date = today + relativedelta(days=i)
            game_date = game_date.replace(hour=0, minute=0, second=0, microsecond=0)

            schedule.append({
                "date": game_date.strftime("%Y-%m-%d"),
                "home_team": "曼城",
                "away_team": "阿仙奴",
                "start_time": "22:00",
                "venue": "Etihad Stadium",
                "competition": "英超",
                "league": "英超",
                "matchweek": self.current_matchweek + i // 2,
            })

            if i % 2 == 0:
                schedule.append({
                    "date": game_date.strftime("%Y-%m-%d"),
                    "home_team": "皇馬",
                    "away_team": "馬德里體育會",
                    "start_time": "23:30",
                    "venue": "班拿貝球場",
                    "competition": "西甲",
                    "league": "西甲",
                })

        return schedule

    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        base_health = await super().health_check()

        # 添加英超適配器特定的健康檢查
        return {
            **base_health,
            "chrome_mcp_available": self._chrome_mcp_available,
            "current_matchweek": self.current_matchweek,
            "current_month": self.current_month,
            "cache_size": len(self._cache),
        }
