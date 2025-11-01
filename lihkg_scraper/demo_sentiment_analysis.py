"""
LIHKG 散戶情緒分析演示
展示完整的爬取和情緒分析流程
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('sentiment_demo')

class SentimentDemo:
    """情緒分析演示類"""
    
    def __init__(self):
        self.posts = []
        self.sentiments = []
    
    async def simulate_scraping(self):
        """模擬爬取 LIHKG 帖子"""
        logger.info("="*70)
        logger.info("模擬 LIHKG 財經台爬取")
        logger.info("="*70)
        
        # 模擬爬取的帖子數據
        self.posts = [
            {
                'post_id': '001',
                'category': 2,
                'title': '討論 0700.HK 騰訊的表現',
                'content': '騰訊股價今日大漲，突破歷史新高，建議持續看好，未來還有上漲空間',
                'author': '投資達人',
                'replies': 45,
                'views': 2850,
                'likes': 28,
                'post_time': '2025-10-27T19:30:00',
                'tags': ['討論', '熱門']
            },
            {
                'post_id': '002',
                'category': 2,
                'title': '0388.HK 港交所 最新消息',
                'content': '港交所宣佈新政策，短期內可能影響股價，建議謹慎操作',
                'author': '市場觀察者',
                'replies': 32,
                'views': 1650,
                'likes': 15,
                'post_time': '2025-10-27T19:25:00',
                'tags': ['新聞', '分析']
            },
            {
                'post_id': '003',
                'category': 2,
                'title': '0939.HK 建設銀行 分析',
                'content': '建行股價持續下跌，市場情緒低迷，可能需要止損，建議觀望',
                'author': '風險管理員',
                'replies': 28,
                'views': 1200,
                'likes': 8,
                'post_time': '2025-10-27T19:20:00',
                'tags': ['風險', '下跌']
            },
            {
                'post_id': '004',
                'category': 15,
                'title': 'HSI 期貨 技術分析',
                'content': '恆生指數期貨技術面向好，多頭力量強勁，建議逢低買入',
                'author': '期貨高手',
                'replies': 38,
                'views': 2100,
                'likes': 22,
                'post_time': '2025-10-27T19:15:00',
                'tags': ['期貨', '技術分析']
            },
            {
                'post_id': '005',
                'category': 2,
                'title': '1398.HK 工商銀行 討論',
                'content': '工行股價穩定，股息率不錯，適合長期持有投資',
                'author': '價值投資者',
                'replies': 22,
                'views': 980,
                'likes': 18,
                'post_time': '2025-10-27T19:10:00',
                'tags': ['價值投資', '股息']
            }
        ]
        
        logger.info(f"✓ 成功爬取 {len(self.posts)} 個帖子")
        
        for i, post in enumerate(self.posts, 1):
            logger.info(f"  {i}. {post['title']} (回復: {post['replies']})")
    
    async def analyze_sentiments(self):
        """進行情緒分析"""
        logger.info("\n" + "="*70)
        logger.info("進行情緒分析")
        logger.info("="*70)
        
        # 模擬情緒分析
        for post in self.posts:
            sentiment = await self._analyze_post_sentiment(post)
            self.sentiments.append({
                'post_id': post['post_id'],
                'sentiment': sentiment
            })
            logger.info(f"帖子 {post['post_id']}: {sentiment['label']} ({sentiment['score']:.3f})")
    
    async def _analyze_post_sentiment(self, post):
        """分析單個帖子的情緒"""
        text = f"{post['title']} {post['content']}"
        
        # 情緒關鍵詞
        positive_keywords = [
            '漲', '大漲', '看好', '上漲', '突破', '新高', '建議',
            '向好', '強勁', '買入', '穩定', '不錯', '適合'
        ]
        
        negative_keywords = [
            '跌', '下跌', '下跌', '低迷', '謹慎', '止損', '觀望',
            '風險', '影響'
        ]
        
        # 計算情緒分數
        pos_count = sum(1 for word in positive_keywords if word in text)
        neg_count = sum(1 for word in negative_keywords if word in text)
        
        total = pos_count + neg_count
        if total == 0:
            score = 0
            label = 'neutral'
        else:
            score = (pos_count - neg_count) / total
            label = 'positive' if score > 0 else 'negative' if score < 0 else 'neutral'
        
        # 計算情緒強度
        intensity = min((post['replies'] + post['views']/100 + post['likes']) / 100, 1.0)
        
        return {
            'score': round(score, 3),
            'label': label,
            'intensity': round(intensity, 3),
            'positive_count': pos_count,
            'negative_count': neg_count
        }
    
    def generate_report(self):
        """生成情緒分析報告"""
        logger.info("\n" + "="*70)
        logger.info("散戶情緒分析報告")
        logger.info("="*70)
        
        # 統計情緒分佈
        total = len(self.posts)
        positive = sum(1 for s in self.sentiments if s['sentiment']['label'] == 'positive')
        negative = sum(1 for s in self.sentiments if s['sentiment']['label'] == 'negative')
        neutral = total - positive - negative
        
        # 平均情緒分數
        avg_score = sum(s['sentiment']['score'] for s in self.sentiments) / total
        
        logger.info(f"總帖子數: {total}")
        logger.info(f"正面情緒: {positive} ({positive/total*100:.1f}%)")
        logger.info(f"負面情緒: {negative} ({negative/total*100:.1f}%)")
        logger.info(f"中性情緒: {neutral} ({neutral/total*100:.1f}%)")
        logger.info(f"平均情緒分數: {avg_score:.3f}")
        
        # 熱門股票
        logger.info("\n熱門討論股票:")
        stock_mentions = {}
        for post in self.posts:
            # 提取股票代碼
            import re
            stocks = re.findall(r'\b\d{4}\.HK\b', post['title'] + ' ' + post['content'])
            for stock in stocks:
                if stock not in stock_mentions:
                    stock_mentions[stock] = {'count': 0, 'sentiments': []}
                stock_mentions[stock]['count'] += 1
                # 找到對應的情緒
                sent = next((s for s in self.sentiments if s['post_id'] == post['post_id']), None)
                if sent:
                    stock_mentions[stock]['sentiments'].append(sent['sentiment']['score'])
        
        for stock, data in sorted(stock_mentions.items(), key=lambda x: x[1]['count'], reverse=True):
            avg_sent = sum(data['sentiments']) / len(data['sentiments'])
            logger.info(f"  {stock}: 提及 {data['count']} 次, 平均情緒 {avg_sent:.3f}")
        
        # 情緒極端帖子
        logger.info("\n情緒極端帖子:")
        sorted_by_sentiment = sorted(self.sentiments, key=lambda x: x['sentiment']['score'])
        
        logger.info("  最負面:")
        for item in sorted_by_sentiment[:2]:
            post = next(p for p in self.posts if p['post_id'] == item['post_id'])
            logger.info(f"    - {post['title']} (分數: {item['sentiment
