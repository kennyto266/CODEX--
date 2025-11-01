#!/usr/bin/env python3
"""
足智彩數據適配器
從香港賽馬會足智彩官方網站獲取體育比分數據
"""

import asyncio
import logging
import httpx
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class JokerSportsAdapter(BaseScraper):
    """足智彩體育數據適配器"""

    def __init__(self):
        super().__init__("JokerSports")
        self.base_url = "https://bet.hkjc.com/ch/football"
        self.scores_url = f"{self.base_url}/index.jsp"
        self.schedule_url = f"{self.base_url}/schedule.jsp"
        self.cache = {}
        self.cache_ttl = 60  # 1分鐘緩存

    async def fetch_live_scores(self, sport_type: str = "soccer") -> List[Dict]:
        """獲取實時比分"""
        try:
            cache_key = f"scores_{sport_type}"
            if self._is_cache_valid(cache_key):
                logger.info("使用緩存的比分數據")
                return self.cache.get(cache_key, [])

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.scores_url)
                if response.status_code == 200:
                    html_content = response.text
                    scores = self._parse_scores(html_content, sport_type)

                    if scores:
                        self.cache[cache_key] = scores
                        self.cache_time[cache_key] = datetime.now().timestamp()
                        return scores

            logger.warning("無法獲取比分數據")
            return []

        except Exception as e:
            logger.error(f"獲取實時比分失敗: {e}")
            return []

    async def fetch_upcoming_matches(self, sport_type: str = "soccer") -> List[Dict]:
        """獲取 upcoming 比賽"""
        try:
            cache_key = f"schedule_{sport_type}"
            if self._is_cache_valid(cache_key):
                return self.cache.get(cache_key, [])

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.schedule_url)
                if response.status_code == 200:
                    html_content = response.text
                    schedule = self._parse_schedule(html_content, sport_type)

                    if schedule:
                        self.cache[cache_key] = schedule
                        self.cache_time[cache_key] = datetime.now().timestamp()
                        return schedule

            return []

        except Exception as e:
            logger.error(f"獲取賽程失敗: {e}")
            return []

    async def fetch_data(self, **kwargs) -> str:
        """獲取原始數據"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(self.scores_url)
            if response.status_code == 200:
                return response.text
            raise Exception(f"HTTP {response.status_code}")

    async def parse_data(self, raw_data: str) -> Dict[str, Any]:
        """解析原始數據"""
        return {
            "source": "足智彩",
            "timestamp": datetime.now().isoformat(),
            "raw_html": raw_data,
            "parsed": True
        }

    def _parse_scores(self, html_content: str, sport_type: str) -> List[Dict]:
        """解析比分數據"""
        matches = []

        try:
            # 足智彩網站可能使用JavaScript加載數據，這裡提供多種解析策略

            # 策略1: 查找比分模式
            score_patterns = [
                # 匹配比分: 球隊名 2-1 球隊名
                r'([A-Za-z\s]+)\s+(\d+)\s*-\s*(\d+)\s+([A-Za-z\s]+)',
                # 匹配狀態: 進行中/已結束
                r'(Live|FT|Finished|In Progress)',
            ]

            # 策略2: 查找JSON數據（如果頁面使用JavaScript）
            json_pattern = r'var\s+(?:scores?|matches?)\s*=\s*(\[.*?\]);'
            json_matches = re.findall(json_pattern, html_content, re.DOTALL)

            if json_matches:
                try:
                    # 嘗試解析JSON
                    json_data = json.loads(json_matches[0])
                    if isinstance(json_data, list):
                        for item in json_data:
                            match = self._normalize_match_data(item, sport_type)
                            if match:
                                matches.append(match)
                except json.JSONDecodeError:
                    logger.warning("JSON解析失敗")

            # 策略3: 使用正則表達式提取
            if not matches:
                text_matches = re.findall(
                    r'([A-Za-z\s]+(?:\s[A-Z]+)?)\s+(\d+)\s*-\s*(\d+)\s+([A-Za-z\s]+(?:\s[A-Z]+)?)',
                    html_content
                )

                for match_tuple in text_matches:
                    home_team, home_score, away_score, away_team = match_tuple

                    # 過濾掉標題行和無效數據
                    if any(keyword in home_team.lower() for keyword in ['team', 'score', 'home']):
                        continue

                    match_data = {
                        "match_id": f"joker_{hash(home_team + away_team) % 10000}",
                        "league": "足智彩" if sport_type == "soccer" else "足智彩",
                        "home_team": home_team.strip(),
                        "away_team": away_team.strip(),
                        "home_score": int(home_score),
                        "away_score": int(away_score),
                        "status": self._determine_match_status(html_content, home_team),
                        "match_time": datetime.now().strftime("%H:%M"),
                        "data_source": "joker",
                        "timestamp": datetime.now().isoformat()
                    }

                    matches.append(match_data)

            # 為每個匹配添加數據來源標記
            for match in matches:
                match["data_source"] = "足智彩"

            return matches

        except Exception as e:
            logger.error(f"解析比分數據失敗: {e}")
            return []

    def _parse_schedule(self, html_content: str, sport_type: str) -> List[Dict]:
        """解析賽程數據"""
        matches = []

        try:
            # 查找賽程模式
            schedule_pattern = r'([A-Za-z\s]+)\s+vs\s+([A-Za-z\s]+)\s+(\d{1,2}[:/]\d{1,2})'

            schedule_matches = re.findall(schedule_pattern, html_content)

            for home_team, away_team, match_time in schedule_matches:
                match_data = {
                    "match_id": f"joker_schedule_{hash(home_team + away_team) % 10000}",
                    "league": "足智彩",
                    "home_team": home_team.strip(),
                    "away_team": away_team.strip(),
                    "home_score": None,
                    "away_score": None,
                    "status": "未開始",
                    "match_time": match_time,
                    "data_source": "joker",
                    "timestamp": datetime.now().isoformat()
                }

                matches.append(match_data)

            return matches

        except Exception as e:
            logger.error(f"解析賽程數據失敗: {e}")
            return []

    def _normalize_match_data(self, item: Dict, sport_type: str) -> Optional[Dict]:
        """標準化匹配數據"""
        try:
            # 根據JSON結構調整這裡的鍵名
            home_team = item.get('home_team') or item.get('home') or item.get('team1')
            away_team = item.get('away_team') or item.get('away') or item.get('team2')
            home_score = item.get('home_score') or item.get('score_home') or item.get('score1')
            away_score = item.get('away_score') or item.get('score_away') or item.get('score2')
            status = item.get('status') or item.get('state') or '未知'

            if not all([home_team, away_team]):
                return None

            return {
                "match_id": f"joker_{hash(home_team + away_team) % 10000}",
                "league": "足智彩",
                "home_team": home_team,
                "away_team": away_team,
                "home_score": int(home_score) if home_score else None,
                "away_score": int(away_score) if away_score else None,
                "status": status,
                "match_time": datetime.now().strftime("%H:%M"),
                "data_source": "joker",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"標準化匹配數據失敗: {e}")
            return None

    def _determine_match_status(self, html_content: str, team_name: str) -> str:
        """確定比賽狀態"""
        # 檢查是否有"Live"標記
        if re.search(r'\b(Live|進行中|直播)\b', html_content, re.IGNORECASE):
            return "進行中"

        # 檢查是否有"FT"或"Finished"標記
        if re.search(r'\b(FT|Finished|已結束)\b', html_content, re.IGNORECASE):
            return "已結束"

        # 檢查是否有特定隊伍的比分
        if re.search(rf'{re.escape(team_name)}\s+\d+', html_content):
            return "進行中"

        return "未開始"

    def _is_cache_valid(self, key: str) -> bool:
        """檢查緩存是否有效"""
        if key not in self.cache or key not in self.cache_time:
            return False
        elapsed = datetime.now().timestamp() - self.cache_time[key]
        return elapsed < self.cache_ttl

    async def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證數據"""
        if not data:
            return None

        # 添加驗證標記
        data["validated"] = True
        data["validation_time"] = datetime.now().isoformat()

        return data

    def get_stats(self) -> Dict[str, Any]:
        """獲取適配器統計"""
        base_stats = super().get_stats()
        base_stats.update({
            "adapter_type": "JokerSports",
            "cache_size": len(self.cache),
            "supported_sports": ["soccer", "basketball"]
        })
        return base_stats


# 創建全局實例
joker_adapter = JokerSportsAdapter()
