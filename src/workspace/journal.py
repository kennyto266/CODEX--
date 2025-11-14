"""
交易日志和笔记
记录交易思考、市场观察和策略反思
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class MarketObservation:
    """市场观察"""
    id: str
    timestamp: str
    market: str  # 市场名称
    mood: str  # 市场情绪 (bullish, bearish, neutral)
    key_events: List[str]  # 关键事件
    observations: str  # 观察内容
    tags: List[str] = None
    symbol_specific: Optional[str] = None  # 特定股票

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class TradeNote:
    """交易笔记"""
    id: str
    timestamp: str
    trade_id: Optional[str]  # 关联交易ID
    symbol: str
    note_type: str  # entry, exit, review, reflection
    content: str
    strategy: str = ""
    tags: List[str] = None
    emotion: str = ""  # 交易时情绪

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class StrategyReflection:
    """策略反思"""
    id: str
    timestamp: str
    strategy_name: str
    period_start: str
    period_end: str
    performance: float  # 期间表现
    what_worked: List[str] = None  # 有效的部分
    what_didnt_work: List[str] = None  # 无效的部分
    improvements: List[str] = None  # 改进建议
    overall_rating: int = 0  # 1-10评分

    def __post_init__(self):
        if self.what_worked is None:
            self.what_worked = []
        if self.what_didnt_work is None:
            self.what_didnt_work = []
        if self.improvements is None:
            self.improvements = []


@dataclass
class JournalEntry:
    """完整日志条目"""
    id: str
    timestamp: str
    entry_type: str  # trade_note, market_obs, strategy_reflection
    content: Dict[str, Any]  # 实际内容
    tags: List[str] = None
    priority: str = "normal"  # low, normal, high

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class TradingJournal:
    """交易日志管理器"""

    def __init__(self, data_dir: str = "workspace_data/journal"):
        self.data_dir = data_dir
        self.journal_entries: List[JournalEntry] = []
        self.trade_notes: Dict[str, List[TradeNote]] = {}  # user_id -> notes
        self.market_observations: Dict[str, List[MarketObservation]] = {}  # user_id -> observations
        self.strategy_reflections: Dict[str, List[StrategyReflection]] = {}  # user_id -> reflections
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """确保数据目录存在"""
        import os
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def add_trade_note(
        self,
        user_id: str,
        symbol: str,
        note_type: str,
        content: str,
        trade_id: Optional[str] = None,
        strategy: str = "",
        emotion: str = "",
        tags: Optional[List[str]] = None
    ) -> TradeNote:
        """
        添加交易笔记

        Args:
            user_id: 用户ID
            symbol: 股票代码
            note_type: 笔记类型 (entry, exit, review, reflection)
            content: 内容
            trade_id: 关联交易ID
            strategy: 策略名称
            emotion: 情绪
            tags: 标签

        Returns:
            新交易笔记
        """
        import uuid

        note = TradeNote(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            trade_id=trade_id,
            symbol=symbol,
            note_type=note_type,
            content=content,
            strategy=strategy,
            emotion=emotion,
            tags=tags or []
        )

        if user_id not in self.trade_notes:
            self.trade_notes[user_id] = []

        self.trade_notes[user_id].append(note)

        # 保存
        self._save_trade_notes(user_id)

        logger.info(f"Added trade note for {symbol}")
        return note

    def add_market_observation(
        self,
        user_id: str,
        market: str,
        mood: str,
        observations: str,
        key_events: Optional[List[str]] = None,
        symbol_specific: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> MarketObservation:
        """
        添加市场观察

        Args:
            user_id: 用户ID
            market: 市场名称
            mood: 市场情绪
            observations: 观察内容
            key_events: 关键事件
            symbol_specific: 特定股票
            tags: 标签

        Returns:
            新市场观察
        """
        import uuid

        obs = MarketObservation(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            market=market,
            mood=mood,
            key_events=key_events or [],
            observations=observations,
            tags=tags or [],
            symbol_specific=symbol_specific
        )

        if user_id not in self.market_observations:
            self.market_observations[user_id] = []

        self.market_observations[user_id].append(obs)

        # 保存
        self._save_market_observations(user_id)

        logger.info(f"Added market observation for {market}")
        return obs

    def add_strategy_reflection(
        self,
        user_id: str,
        strategy_name: str,
        period_start: str,
        period_end: str,
        performance: float,
        what_worked: Optional[List[str]] = None,
        what_didnt_work: Optional[List[str]] = None,
        improvements: Optional[List[str]] = None,
        overall_rating: int = 5
    ) -> StrategyReflection:
        """
        添加策略反思

        Args:
            user_id: 用户ID
            strategy_name: 策略名称
            period_start: 期间开始
            period_end: 期间结束
            performance: 期间表现
            what_worked: 有效部分
            what_didnt_work: 无效部分
            improvements: 改进建议
            overall_rating: 总体评分 (1-10)

        Returns:
            新策略反思
        """
        import uuid

        reflection = StrategyReflection(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            strategy_name=strategy_name,
            period_start=period_start,
            period_end=period_end,
            performance=performance,
            what_worked=what_worked or [],
            what_didnt_work=what_didnt_work or [],
            improvements=improvements or [],
            overall_rating=overall_rating
        )

        if user_id not in self.strategy_reflections:
            self.strategy_reflections[user_id] = []

        self.strategy_reflections[user_id].append(reflection)

        # 保存
        self._save_strategy_reflections(user_id)

        logger.info(f"Added strategy reflection for {strategy_name}")
        return reflection

    def get_trade_notes(
        self,
        user_id: str,
        symbol: Optional[str] = None,
        note_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[TradeNote]:
        """
        获取交易笔记

        Args:
            user_id: 用户ID
            symbol: 股票代码
            note_type: 笔记类型
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            交易笔记列表
        """
        if user_id not in self.trade_notes:
            return []

        notes = self.trade_notes[user_id]

        # 筛选
        if symbol:
            notes = [n for n in notes if n.symbol == symbol]

        if note_type:
            notes = [n for n in notes if n.note_type == note_type]

        if start_date:
            notes = [n for n in notes if n.timestamp >= start_date]

        if end_date:
            notes = [n for n in notes if n.timestamp <= end_date]

        return notes

    def get_market_observations(
        self,
        user_id: str,
        market: Optional[str] = None,
        mood: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[MarketObservation]:
        """
        获取市场观察

        Args:
            user_id: 用户ID
            market: 市场名称
            mood: 市场情绪
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            市场观察列表
        """
        if user_id not in self.market_observations:
            return []

        observations = self.market_observations[user_id]

        # 筛选
        if market:
            observations = [o for o in observations if o.market == market]

        if mood:
            observations = [o for o in observations if o.mood == mood]

        if start_date:
            observations = [o for o in observations if o.timestamp >= start_date]

        if end_date:
            observations = [o for o in observations if o.timestamp <= end_date]

        return observations

    def get_strategy_reflections(
        self,
        user_id: str,
        strategy_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[StrategyReflection]:
        """
        获取策略反思

        Args:
            user_id: 用户ID
            strategy_name: 策略名称
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            策略反思列表
        """
        if user_id not in self.strategy_reflections:
            return []

        reflections = self.strategy_reflections[user_id]

        # 筛选
        if strategy_name:
            reflections = [r for r in reflections if r.strategy_name == strategy_name]

        if start_date:
            reflections = [r for r in reflections if r.timestamp >= start_date]

        if end_date:
            reflections = [r for r in reflections if r.timestamp <= end_date]

        return reflections

    def search_journal(self, user_id: str, query: str) -> Dict[str, List]:
        """
        搜索日志

        Args:
            user_id: 用户ID
            query: 搜索关键词

        Returns:
            搜索结果
        """
        query_lower = query.lower()
        results = {
            'trade_notes': [],
            'market_observations': [],
            'strategy_reflections': []
        }

        # 搜索交易笔记
        for note in self.trade_notes.get(user_id, []):
            if (query_lower in note.content.lower() or
                query_lower in note.symbol.lower() or
                any(query_lower in tag.lower() for tag in note.tags)):
                results['trade_notes'].append(note)

        # 搜索市场观察
        for obs in self.market_observations.get(user_id, []):
            if (query_lower in obs.observations.lower() or
                query_lower in obs.market.lower() or
                any(query_lower in event.lower() for event in obs.key_events) or
                any(query_lower in tag.lower() for tag in obs.tags)):
                results['market_observations'].append(obs)

        # 搜索策略反思
        for ref in self.strategy_reflections.get(user_id, []):
            if (query_lower in ref.strategy_name.lower() or
                any(query_lower in item.lower() for item in ref.what_worked) or
                any(query_lower in item.lower() for item in ref.what_didnt_work) or
                any(query_lower in item.lower() for item in ref.improvements)):
                results['strategy_reflections'].append(ref)

        return results

    def get_emotion_analysis(self, user_id: str) -> Dict[str, Any]:
        """
        获取情绪分析

        Args:
            user_id: 用户ID

        Returns:
            情绪分析
        """
        if user_id not in self.trade_notes:
            return {
                'total_notes': 0,
                'emotion_distribution': {},
                'emotion_by_pnl': {}
            }

        notes = self.trade_notes[user_id]
        emotions = [n.emotion for n in notes if n.emotion]
        emotion_dist = {}
        for emotion in emotions:
            emotion_dist[emotion] = emotion_dist.get(emotion, 0) + 1

        # 按盈亏分组分析情绪
        # 这里简化处理，实际应该关联交易记录
        emotion_by_pnl = {
            'positive_trades': {},
            'negative_trades': {}
        }

        return {
            'total_notes': len(notes),
            'emotion_distribution': emotion_dist,
            'emotion_by_pnl': emotion_by_pnl
        }

    def get_market_sentiment_timeline(self, user_id: str, days: int = 30) -> pd.DataFrame:
        """
        获取市场情绪时间线

        Args:
            user_id: 用户ID
            days: 天数

        Returns:
            情绪时间线DataFrame
        """
        if user_id not in self.market_observations:
            return pd.DataFrame(columns=['date', 'sentiment', 'count'])

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        observations = self.get_market_observations(
            user_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )

        if not observations:
            return pd.DataFrame(columns=['date', 'sentiment', 'count'])

        # 按日期和情绪分组
        daily_sentiment = {}
        for obs in observations:
            date = obs.timestamp[:10]
            if date not in daily_sentiment:
                daily_sentiment[date] = {'bullish': 0, 'bearish': 0, 'neutral': 0}
            daily_sentiment[date][obs.mood] = daily_sentiment[date].get(obs.mood, 0) + 1

        # 转换为DataFrame
        data = []
        for date, sentiments in sorted(daily_sentiment.items()):
            for sentiment, count in sentiments.items():
                data.append({
                    'date': date,
                    'sentiment': sentiment,
                    'count': count
                })

        return pd.DataFrame(data)

    def get_most_active_tags(self, user_id: str) -> List[Dict[str, int]]:
        """
        获取最活跃标签

        Args:
            user_id: 用户ID

        Returns:
            标签统计列表
        """
        tag_counts = {}

        # 统计交易笔记标签
        for note in self.trade_notes.get(user_id, []):
            for tag in note.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # 统计市场观察标签
        for obs in self.market_observations.get(user_id, []):
            for tag in obs.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # 转换为列表并排序
        return sorted(
            [{'tag': tag, 'count': count} for tag, count in tag_counts.items()],
            key=lambda x: x['count'],
            reverse=True
        )

    def export_journal(self, user_id: str, format: str = 'json') -> str:
        """
        导出日志

        Args:
            user_id: 用户ID
            format: 格式 (json, csv)

        Returns:
            导出的数据
        """
        data = {
            'trade_notes': [asdict(n) for n in self.trade_notes.get(user_id, [])],
            'market_observations': [asdict(o) for o in self.market_observations.get(user_id, [])],
            'strategy_reflections': [asdict(r) for r in self.strategy_reflections.get(user_id, [])]
        }

        if format == 'json':
            return json.dumps(data, indent=2, ensure_ascii=False)
        elif format == 'csv':
            # 简化为CSV格式
            all_entries = []
            for note in data['trade_notes']:
                all_entries.append({
                    'timestamp': note['timestamp'],
                    'type': 'trade_note',
                    'content': note['content'],
                    'symbol': note['symbol']
                })
            for obs in data['market_observations']:
                all_entries.append({
                    'timestamp': obs['timestamp'],
                    'type': 'market_observation',
                    'content': obs['observations'],
                    'symbol': obs.get('symbol_specific', '')
                })

            df = pd.DataFrame(all_entries)
            return df.to_csv(index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _save_trade_notes(self, user_id: str):
        """保存交易笔记"""
        import os
        file_path = os.path.join(self.data_dir, f"{user_id}_notes.json")
        notes = self.trade_notes.get(user_id, [])
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([asdict(n) for n in notes], f, indent=2, ensure_ascii=False)

    def _save_market_observations(self, user_id: str):
        """保存市场观察"""
        import os
        file_path = os.path.join(self.data_dir, f"{user_id}_observations.json")
        observations = self.market_observations.get(user_id, [])
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([asdict(o) for o in observations], f, indent=2, ensure_ascii=False)

    def _save_strategy_reflections(self, user_id: str):
        """保存策略反思"""
        import os
        file_path = os.path.join(self.data_dir, f"{user_id}_reflections.json")
        reflections = self.strategy_reflections.get(user_id, [])
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([asdict(r) for r in reflections], f, indent=2, ensure_ascii=False)

    def delete_entry(self, user_id: str, entry_id: str, entry_type: str) -> bool:
        """
        删除日志条目

        Args:
            user_id: 用户ID
            entry_id: 条目ID
            entry_type: 条目类型 (trade_note, market_observation, strategy_reflection)

        Returns:
            是否成功删除
        """
        try:
            if entry_type == 'trade_note':
                notes = self.trade_notes.get(user_id, [])
                self.trade_notes[user_id] = [n for n in notes if n.id != entry_id]
                self._save_trade_notes(user_id)
            elif entry_type == 'market_observation':
                obs = self.market_observations.get(user_id, [])
                self.market_observations[user_id] = [o for o in obs if o.id != entry_id]
                self._save_market_observations(user_id)
            elif entry_type == 'strategy_reflection':
                refs = self.strategy_reflections.get(user_id, [])
                self.strategy_reflections[user_id] = [r for r in refs if r.id != entry_id]
                self._save_strategy_reflections(user_id)
            else:
                return False

            logger.info(f"Deleted {entry_type} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete entry: {e}")
            return False


# 导出
__all__ = [
    'TradingJournal',
    'TradeNote',
    'MarketObservation',
    'StrategyReflection',
    'JournalEntry',
]
