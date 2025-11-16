"""Fixed NBA crawler based on real MCP ESPN data structure.

This crawler extracts data exactly as found on ESPN using Chrome MCP analysis.
"""

import asyncio
import logging
import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import httpx
from bs4 import BeautifulSoup


class FixedNBARCrawler:
    """Fixed NBA crawler based on real ESPN data structure."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache = {}
        self.cache_expiry = {}
        self.base_url = "https://www.espn.com/nba/scoreboard"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        # Real ESPN team abbreviations mapping
        self.team_mapping = {
            'ATL': '老鷹隊', 'BOS': '塞爾提克', 'BKN': '籃網隊', 'CHA': '黃蜂隊',
            'CHI': '公牛隊', 'CLE': '騎士隊', 'DAL': '獨行俠', 'DEN': '金塊隊',
            'DET': '活塞隊', 'GSW': '勇士隊', 'HOU': '火箭隊', 'IND': '溜馬隊',
            'LAC': '快艇隊', 'LAL': '湖人隊', 'MEM': '灰熊隊', 'MIA': '熱火隊',
            'MIL': '公鹿隊', 'MIN': '灰狼隊', 'NOP': '鵜鶘隊', 'NYK': '尼克斯隊',
            'OKC': '雷霆隊', 'ORL': '魔術隊', 'PHI': '76人隊', 'PHX': '太陽隊',
            'POR': '拓荒者隊', 'SAC': '國王隊', 'SAS': '馬刺隊', 'TOR': '暴龍隊',
            'UTA': '爵士隊', 'WAS': '巫師隊'
        }

    def _is_cache_valid(self, key: str, ttl_minutes: int = 1) -> bool:
        """Check if cached data is still valid."""
        if key not in self.cache or key not in self.cache_expiry:
            return False
        return datetime.now() < self.cache_expiry[key]

    def _set_cache(self, key: str, data: Any, ttl_minutes: int = 1):
        """Set cached data with expiry."""
        self.cache[key] = data
        self.cache_expiry[key] = datetime.now() + timedelta(minutes=ttl_minutes)

    async def crawl_nba_scores(self) -> str:
        """Get NBA scores using fixed parsing logic."""
        try:
            cache_key = "fixed_nba_scores"

            # Check cache first
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]

            print("正在獲取真實ESPN NBA數據 (修復版)...")

            # Fetch from ESPN
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.get(self.base_url, headers=self.headers)
                response.raise_for_status()

                print(f"ESPN響應長度: {len(response.text)} 字符")

                # Parse HTML using fixed logic
                soup = BeautifulSoup(response.text, 'html.parser')
                games = self._parse_espn_html_fixed(soup)

                print(f"解析到 {len(games)} 場比賽")

                # Format response
                if games:
                    formatted_scores = self._format_fixed_nba_scores(games)
                    self._set_cache(cache_key, formatted_scores, ttl_minutes=2)
                    return formatted_scores
                else:
                    return self._get_no_data_message()

        except Exception as e:
            self.logger.error(f"Fixed NBA crawl error: {e}")
            print(f"爬取錯誤: {e}")
            return self._get_no_data_message()

    def _parse_espn_html_fixed(self, soup) -> List[Dict]:
        """Parse ESPN HTML using the structure discovered via MCP."""
        games = []

        try:
            # Get all text from the page
            all_text = soup.get_text()

            print("開始解析真實ESPN數據 (修復版)...")

            # Pattern 1: Look for ESPN game links and scores
            # Based on MCP analysis, games have structure like:
            # "MEM 100 CLE 108" or "DEN 111 MIN 103"

            # Find game score patterns like "TEAM_A SCORE TEAM_B SCORE"
            score_pattern = r'([A-Z]{2,3})\s+(\d{1,3})\s+([A-Z]{2,3})\s+(\d{1,3})'
            matches = re.findall(score_pattern, all_text)

            print(f"找到比分模式: {len(matches)} 個")

            for match in matches:
                team1_abbr, score1, team2_abbr, score2 = match

                # Only process if both are valid NBA teams
                if (team1_abbr in self.team_mapping and team2_abbr in self.team_mapping):
                    games.append({
                        'away_team': self.team_mapping.get(team1_abbr, team1_abbr),
                        'away_score': int(score1),
                        'home_team': self.team_mapping.get(team2_abbr, team2_abbr),
                        'home_score': int(score2),
                        'status': self._extract_game_status_fixed(all_text, team1_abbr, team2_abbr)
                    })

            # Pattern 2: Look for individual team scores with context
            # Search for patterns like "DEN 111" followed by "MIN 103"
            for team_abbr in self.team_mapping.keys():
                # Look for team followed by score
                team_score_pattern = rf'{team_abbr}\s+(\d{{1,3}})'
                team_matches = list(re.finditer(team_score_pattern, all_text))

                for match in team_matches:
                    team_score = int(match.group(1))
                    start_pos = match.end()

                    # Look for another team score within 200 characters
                    context = all_text[start_pos:start_pos + 200]
                    next_match = re.search(r'([A-Z]{2,3})\s+(\d{1,3})', context)

                    if next_match:
                        next_team_abbr = next_match.group(1)
                        next_score = int(next_match.group(2))

                        if (next_team_abbr in self.team_mapping and
                            next_team_abbr != team_abbr and
                            not any(g['away_team'] == self.team_mapping.get(team_abbr) and
                                   g['home_team'] == self.team_mapping.get(next_team_abbr) for g in games)):

                            games.append({
                                'away_team': self.team_mapping.get(team_abbr, team_abbr),
                                'away_score': team_score,
                                'home_team': self.team_mapping.get(next_team_abbr, next_team_abbr),
                                'home_score': next_score,
                                'status': self._extract_game_status_fixed(all_text, team_abbr, next_team_abbr)
                            })

            # Remove duplicates
            unique_games = []
            seen = set()
            for game in games:
                game_key = (game['away_team'], game['home_team'], game['away_score'], game['home_score'])
                if game_key not in seen:
                    seen.add(game_key)
                    unique_games.append(game)

            print(f"去重後有 {len(unique_games)} 場比賽")
            return unique_games

        except Exception as e:
            self.logger.error(f"Error parsing fixed ESPN HTML: {e}")
            print(f"解析錯誤: {e}")
            return []

    def _extract_game_status_fixed(self, text: str, team1: str, team2: str) -> str:
        """Extract game status based on real ESPN patterns."""
        try:
            # Look for time patterns like "3:34 - 4th"
            time_pattern = r'(\d{1,2}):(\d{2})\s*-\s*(\d+)(?:st|nd|rd|th)?'
            time_matches = re.findall(time_pattern, text)

            if time_matches:
                minutes, seconds, quarter = time_matches[0]
                return f"第{quarter}節 | 剩餘{minutes}:{seconds}"

            # Check if game is final
            if re.search(r'final|end|完場|已結束', text, re.IGNORECASE):
                return "已結束"

            return "進行中"

        except Exception as e:
            self.logger.error(f"Error extracting fixed game status: {e}")
            return "進行中"

    def _format_fixed_nba_scores(self, games: List[Dict]) -> str:
        """Format NBA scores using corrected data."""
        try:
            if not games:
                return self._get_no_data_message()

            text = f"NBA真實即時比分 ({datetime.now().strftime('%m/%d %H:%M')})\n\n"

            for i, game in enumerate(games[:10], 1):
                status_icon = "LIVE" if game.get('status') != '已結束' else "END"

                text += f"{status_icon} 第{i}場\n"
                text += f"{game['away_team']} {game['away_score']} - {game['home_score']} {game['home_team']}\n"
                text += f"狀態: {game.get('status', '進行中')}\n\n"

            text += f"真實賽事資料 | 來源: ESPN (修復版)\n"
            text += f"更新: {datetime.now().strftime('%H:%M:%S')}\n"
            text += f"場次: {len(games)}場比賽"

            return text

        except Exception as e:
            self.logger.error(f"Error formatting fixed NBA scores: {e}")
            return self._get_no_data_message()

    def _get_no_data_message(self) -> str:
        """Get message when no data is available."""
        return f"""無法獲取NBA數據

ESPN網站可能更新中或暫時無法訪問
請稍後再試或直接訪問: https://www.espn.com/nba/scoreboard

查詢時間: {datetime.now().strftime('%H:%M:%S')}
狀態: 數據爬取失敗"""

    def get_statistics(self) -> Dict[str, Any]:
        """Get fixed NBA crawler statistics."""
        return {
            'cache_size': len(self.cache),
            'cache_keys': list(self.cache.keys()),
            'crawler_status': 'active',
            'base_url': self.base_url,
            'method': 'Fixed HTTP parsing based on MCP analysis',
            'last_update': datetime.now().isoformat()
        }

    def clear_cache(self):
        """Clear all cached data."""
        self.cache.clear()
        self.cache_expiry.clear()


# Global instance
_fixed_nba_crawler_instance: Optional[FixedNBARCrawler] = None


def get_fixed_nba_crawler_instance() -> FixedNBARCrawler:
    """Get or create fixed NBA crawler instance."""
    global _fixed_nba_crawler_instance
    if _fixed_nba_crawler_instance is None:
        _fixed_nba_crawler_instance = FixedNBARCrawler()
    return _fixed_nba_crawler_instance