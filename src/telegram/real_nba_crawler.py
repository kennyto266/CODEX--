"""Real ESPN NBA crawler - extracts actual live NBA data.

This module provides REAL NBA scores from ESPN, no mock data.
"""

import asyncio
import logging
import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import httpx
from bs4 import BeautifulSoup


class RealNBARCrawler:
    """Real ESPN NBA crawler for live game data."""

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
        """Get REAL NBA scores from ESPN - no mock data fallback."""
        try:
            cache_key = "real_nba_scores"

            # Check cache first
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]

            print("正在獲取真實ESPN NBA數據...")

            # Fetch from ESPN with longer timeout
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.get(self.base_url, headers=self.headers)
                response.raise_for_status()

                print(f"ESPN響應長度: {len(response.text)} 字符")

                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract NBA game data
                games = self._parse_espn_html_real(soup)

                print(f"解析到 {len(games)} 場比賽")

                # Format response
                if games:
                    formatted_scores = self._format_real_nba_scores(games)
                    self._set_cache(cache_key, formatted_scores, ttl_minutes=2)
                    return formatted_scores
                else:
                    # Return error message instead of mock data
                    return self._get_no_data_message()

        except Exception as e:
            self.logger.error(f"Real NBA crawl error: {e}")
            print(f"爬取錯誤: {e}")
            return self._get_no_data_message()

    def _parse_espn_html_real(self, soup) -> List[Dict]:
        """Parse ESPN HTML to extract REAL game data."""
        games = []

        try:
            # Get all text from the page
            all_text = soup.get_text()

            print("開始解析真實NBA數據...")

            # Complete NBA team mapping
            team_mapping = {
                'Lakers': '湖人隊', 'Warriors': '勇士隊', 'Celtics': '塞爾提克',
                'Heat': '熱火隊', 'Suns': '太陽隊', 'Mavericks': '獨行俠',
                'Nets': '籃網隊', 'Knicks': '尼克斯隊', 'Bucks': '公鹿隊',
                'Sixers': '76人隊', 'Raptors': '暴龍隊', 'Bulls': '公牛隊',
                'Cavaliers': '騎士隊', 'Pacers': '溜馬隊', 'Pistons': '活塞隊',
                'Hornets': '黃蜂隊', 'Magic': '魔術隊', 'Hawks': '老鷹隊',
                'Thunder': '雷霆隊', 'Nuggets': '金塊隊', 'Clippers': '快艇隊',
                'Trail Blazers': '拓荒者隊', 'Grizzlies': '灰熊隊', 'Spurs': '馬刺隊',
                'Pelicans': '鵜鶘隊', 'Kings': '國王隊', 'Jazz': '爵士隊',
                'Timberwolves': '灰狼隊', 'Wizards': '巫師隊', 'Rockets': '火箭隊'
            }

            all_teams = list(team_mapping.keys())

            # Method 1: Look for specific score patterns around team names
            for team in all_teams:
                # Find all occurrences of the team name followed by numbers
                team_score_pattern = rf'{team}\s+(\d+)'
                team_matches = re.finditer(team_score_pattern, all_text, re.IGNORECASE)

                for match in team_matches:
                    team_score = int(match.group(1))
                    start_pos = match.start()
                    end_pos = match.end()

                    # Look for opponent score within 100 characters
                    context_start = max(0, start_pos - 50)
                    context_end = min(len(all_text), end_pos + 100)
                    context = all_text[context_start:context_end]

                    # Look for opponent score pattern
                    opp_pattern = r'(\d+)\s*[-–]\s*(\d+)'
                    opp_matches = list(re.finditer(opp_pattern, context))

                    for opp_match in opp_matches:
                        score1, score2 = opp_match.groups()

                        # Determine which score belongs to our team
                        if team_score == int(score1):
                            opp_score = int(score2)
                            # Find opponent team name
                            opp_context_start = max(0, start_pos - 100)
                            opp_context_end = min(len(all_text), end_pos + 200)
                            opp_context = all_text[opp_context_start:opp_context_end]

                            # Look for any NBA team name in opponent context
                            for opp_team in all_teams:
                                if opp_team.lower() in opp_context.lower() and opp_team.lower() != team.lower():
                                    games.append({
                                        'home_team': team_mapping.get(team, team),
                                        'home_score': team_score,
                                        'away_team': team_mapping.get(opp_team, opp_team),
                                        'away_score': opp_score,
                                        'status': self._extract_game_status_real(opp_context)
                                    })
                                    break

            # Method 2: General score extraction with team context
            score_patterns = re.findall(r'(\d+)\s*[-–]\s*(\d+)', all_text)

            for score1, score2 in score_patterns[:20]:  # Check first 20 scores
                score_index = all_text.find(f"{score1} - {score2}")
                if score_index > 0:
                    # Get larger context around the score
                    context_start = max(0, score_index - 300)
                    context_end = min(len(all_text), score_index + 300)
                    context = all_text[context_start:context_end]

                    # Find NBA teams in this context
                    found_teams = []
                    for team in all_teams:
                        if team.lower() in context.lower():
                            found_teams.append(team)

                    # If we found at least 2 NBA teams, this is likely a real game
                    if len(found_teams) >= 2:
                        # Use the first two teams found
                        team1, team2 = found_teams[0], found_teams[1]
                        games.append({
                            'home_team': team_mapping.get(team1, team1),
                            'home_score': int(score1),
                            'away_team': team_mapping.get(team2, team2),
                            'away_score': int(score2),
                            'status': self._extract_game_status_real(context)
                        })

            # Remove duplicates
            unique_games = []
            seen = set()
            for game in games:
                game_key = (game['home_team'], game['away_team'], game['home_score'], game['away_score'])
                if game_key not in seen and game_key not in seen:
                    seen.add(game_key)
                    unique_games.append(game)

            print(f"去重後有 {len(unique_games)} 場比賽")
            return unique_games[:10]  # Return up to 10 games

        except Exception as e:
            self.logger.error(f"Error parsing real ESPN HTML: {e}")
            print(f"解析錯誤: {e}")
            return []

    def _extract_game_status_real(self, text: str) -> str:
        """Extract real game status from text."""
        try:
            # Check if game is final
            if re.search(r'final|end|完場|已結束', text, re.IGNORECASE):
                return "已結束"

            # Look for quarter information
            quarter_patterns = [
                (r'1st.*?quarter|第1節|Q1', '第1節'),
                (r'2nd.*?quarter|第2節|Q2', '第2節'),
                (r'3rd.*?quarter|第3節|Q3', '第3節'),
                (r'4th.*?quarter|第4節|Q4', '第4節'),
                (r'overtime|OT|延長賽', '延長賽'),
                (r'halftime|中場休息', '中場休息')
            ]

            for pattern, status in quarter_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    # Look for time remaining
                    time_pattern = r'(\d{1,2}):(\d{2})'
                    time_match = re.search(time_pattern, text)
                    if time_match:
                        minutes = int(time_match.group(1))
                        seconds = int(time_match.group(2))
                        if minutes <= 12 and seconds < 60:  # Valid game time
                            return f"{status} | 剩餘{minutes}:{seconds:02d}"
                    return status

            # Default status
            return "進行中"

        except Exception as e:
            self.logger.error(f"Error extracting real game status: {e}")
            return "進行中"

    def _format_real_nba_scores(self, games: List[Dict]) -> str:
        """Format REAL NBA scores data."""
        try:
            if not games:
                return self._get_no_data_message()

            text = f"NBA真實即時比分 ({datetime.now().strftime('%m/%d %H:%M')})\n\n"

            for i, game in enumerate(games[:10], 1):
                status_icon = "LIVE" if game.get('status') != '已結束' else "END"

                text += f"{status_icon} 第{i}場\n"
                text += f"{game['home_team']} {game['home_score']} - {game['away_score']} {game['away_team']}\n"
                text += f"狀態: {game.get('status', '進行中')}\n\n"

            text += f"真實賽事資料 | 來源: ESPN\n"
            text += f"更新: {datetime.now().strftime('%H:%M:%S')}\n"
            text += f"場次: {len(games)}場比賽"

            return text

        except Exception as e:
            self.logger.error(f"Error formatting real NBA scores: {e}")
            return self._get_no_data_message()

    def _get_no_data_message(self) -> str:
        """Get message when no real data is available."""
        return f"""無法獲取真實NBA數據

ESPN網站可能更新中或暫時無法訪問
請稍後再試或直接訪問: https://www.espn.com/nba/scoreboard

查詢時間: {datetime.now().strftime('%H:%M:%S')}
狀態: 真實數據爬取失敗"""

    def get_statistics(self) -> Dict[str, Any]:
        """Get real NBA crawler statistics."""
        return {
            'cache_size': len(self.cache),
            'cache_keys': list(self.cache.keys()),
            'crawler_status': 'active',
            'base_url': self.base_url,
            'method': 'Real HTTP requests',
            'last_update': datetime.now().isoformat()
        }

    def clear_cache(self):
        """Clear all cached data."""
        self.cache.clear()
        self.cache_expiry.clear()


# Global instance
_real_nba_crawler_instance: Optional[RealNBARCrawler] = None


def get_real_nba_crawler_instance() -> RealNBARCrawler:
    """Get or create real NBA crawler instance."""
    global _real_nba_crawler_instance
    if _real_nba_crawler_instance is None:
        _real_nba_crawler_instance = RealNBARCrawler()
    return _real_nba_crawler_instance