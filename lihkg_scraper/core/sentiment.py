"""
LIHKG 散戶情緒分析模塊
整合現有的 sentiment_analyzer.py 進行情緒分析
"""

import logging
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger('lihkg_scraper.sentiment')

class SentimentAnalyzer:
    """
    散戶情緒分析器
    分析帖子情緒傾向、計算情緒分數
    """
    
    def __init__(self):
        """初始化情緒分析器"""
        self.analyzer = None
        self._load_analyzer()
    
    def _load_analyzer(self):
        """載入基礎情緒分析器"""
        try:
            # 嘗試載入現有的 sentiment_analyzer
            import sys
            import os
            
            # 添加路徑
            sys.path.append(os.path.join(os.path.dirname(__file__), '../../data_downloader'))
            
            from sentiment_analyzer import SentimentAnalyzer as BaseAnalyzer
            self.analyzer = BaseAnalyzer()
            logger.info("成功載入基礎情緒分析器")
            
        except ImportError as e:
            logger.warning(f"無法載入基礎情緒分析器: {e}")
            logger.info("使用簡化版情緒分析")
            self.analyzer = None
    
    async def analyze_post(self, post: Dict) -> Dict:
        """
        分析帖子情緒
        
        Args:
            post: 帖子數據
            
        Returns:
            dict: 情緒分析結果
        """
        try:
            text = f"{post['title']} {post['content'][:500]}"
            
            # 進行情緒分析
            sentiment = await self._analyze_text(text)
            
            # 計算情緒強度
            intensity = self._calculate_intensity(post)
            
            # 綜合情緒分數 (-1 到 1)
            sentiment_score = sentiment['score'] * intensity
            
            result = {
                'sentiment_score': sentiment_score,
                'sentiment_label': sentiment['label'],
                'confidence': sentiment['confidence'],
                'intensity': intensity,
                'positive_words': sentiment.get('positive_words', []),
                'negative_words': sentiment.get('negative_words', []),
                'analyzed_at': datetime.now().isoformat()
            }
            
            logger.debug(f"情緒分析完成: {post['post_id']}, 分數: {sentiment_score:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"情緒分析失敗: {e}")
            return self._default_sentiment()
    
    async def _analyze_text(self, text: str) -> Dict:
        """
        分析文本情緒
        
        Args:
            text: 待分析文本
            
        Returns:
            dict: 情緒分析結果
        """
        if self.analyzer:
            try:
                # 使用基礎情緒分析器
                result = await self.analyzer.analyze(text)
                return result
            except Exception as e:
                logger.warning(f"基礎分析器分析失敗: {e}")
        
        # 使用簡化版分析
        return self._simple_sentiment_analysis(text)
    
    def _simple_sentiment_analysis(self, text: str) -> Dict:
        """
        簡化版情緒分析
        
        Args:
            text: 待分析文本
            
        Returns:
            dict: 情緒分析結果
        """
        # 簡單的關鍵詞匹配
        positive_words = [
            '好', '漲', '升', '賺', '贏', '正', '看漲', '買入',
            '突破', '利好', '上漲', '牛', '升溫', '復甦'
        ]
        
        negative_words = [
            '跌', '賠', '輸', '負', '看跌', '賣出', '崩',
            '跌幅', '下跌', '熊', '恐慌', '危機', '憂慮'
        ]
        
        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        total = pos_count + neg_count
        if total == 0:
            return {
                'score': 0,
                'label': 'neutral',
                'confidence': 0.5,
                'positive_words': [],
                'negative_words': []
            }
        
        score = (pos_count - neg_count) / total
        label = 'positive' if score > 0 else 'negative' if score < 0 else 'neutral'
        confidence = abs(score)
        
        return {
            'score': score,
            'label': label,
            'confidence': confidence,
            'positive_words': [w for w in positive_words if w in text_lower],
            'negative_words': [w for w in negative_words if w in text_lower]
        }
    
    def _calculate_intensity(self, post: Dict) -> float:
        """
        計算情緒強度
        
        Args:
            post: 帖子數據
            
        Returns:
            float: 情緒強度 (0-1)
        """
        # 基於回復數、查看數、點贊數計算
        metrics = {
            'replies': min(post.get('replies', 0) / 100, 1.0),
            'views': min(post.get('views', 0) / 10000, 1.0),
            'likes': min(post.get('likes', 0) / 50, 1.0)
        }
        
        intensity = sum(metrics.values()) / len(metrics)
        return min(max(intensity, 0.0), 1.0)
    
    def _default_sentiment(self) -> Dict:
        """
        默認情緒分析結果
        
        Returns:
            dict: 默認結果
        """
        return {
            'sentiment_score': 0,
            'sentiment_label': 'neutral',
            'confidence': 0.5,
            'intensity': 0.5,
            'positive_words': [],
            'negative_words': [],
            'analyzed_at': datetime.now().isoformat()
        }
    
    async def batch_analyze(self, posts: List[Dict]) -> List[Dict]:
        """
        批量情緒分析
        
        Args:
            posts: 帖子列表
            
        Returns:
            list: 情緒分析結果列表
        """
        logger.info(f"開始批量情緒分析: {len(posts)} 個帖子")
        
        results = []
        for post in posts:
            result = await self.analyze_post(post)
            results.append(result)
        
        logger.info(f"批量情緒分析完成")
        return results
