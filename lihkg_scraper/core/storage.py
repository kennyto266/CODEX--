"""
LIHKG 數據存儲管理器
使用 SQLite 存儲爬取的數據
"""

import sqlite3
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger('lihkg_scraper.storage')

class LIHKGDataStore:
    """
    LIHKG 數據存儲管理器
    使用 SQLite 存儲爬取的數據
    """
    
    def __init__(self, db_path: str = 'data/lihkg.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化資料庫"""
        logger.info(f"初始化資料庫: {self.db_path}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 創建 posts 表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                post_id TEXT PRIMARY KEY,
                category INTEGER,
                title TEXT,
                content TEXT,
                author TEXT,
                replies INTEGER,
                views INTEGER,
                likes INTEGER,
                post_time TIMESTAMP,
                tags TEXT,
                sentiment_score REAL,
                sentiment_label TEXT,
                stock_mentions TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info("資料庫初始化完成")
    
    async def save_post(self, post: Dict, sentiment: Dict):
        """保存帖子數據"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO posts (
                    post_id, category, title, content, author,
                    replies, views, likes, post_time, tags,
                    sentiment_score, sentiment_label,
                    stock_mentions, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                post['post_id'], 
                post.get('category', 0),
                post['title'],
                post['content'],
                post['author'],
                post['replies'],
                post['views'],
                post['likes'],
                post['post_time'],
                json.dumps(post.get('tags', [])),
                sentiment.get('sentiment_score', 0),
                sentiment.get('sentiment_label', 'neutral'),
                json.dumps(post.get('stock_mentions', [])),
                post.get('created_at', datetime.now().isoformat()),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            logger.debug(f"保存帖子: {post['post_id']}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"保存帖子失敗: {e}")
            raise
        finally:
            conn.close()
    
    async def get_recent_posts(self, category=None, limit=100):
        """獲取最近的帖子"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if category is not None:
                cursor.execute('''
                    SELECT * FROM posts 
                    WHERE category = ? 
                    ORDER BY post_time DESC 
                    LIMIT ?
                ''', (category, limit))
            else:
                cursor.execute('''
                    SELECT * FROM posts 
                    ORDER BY post_time DESC 
                    LIMIT ?
                ''', (limit,))
            
            rows = cursor.fetchall()
            posts = [self._row_to_dict(row) for row in rows]
            return posts
        except Exception as e:
            logger.error(f"獲取帖子失敗: {e}")
            return []
        finally:
            conn.close()
    
    async def get_stock_sentiment(self, stock_code, days=7):
        """獲取特定股票的情緒分析"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT * FROM posts 
                WHERE stock_mentions LIKE ? 
                AND post_time > datetime('now', '-{} days')
                ORDER BY post_time DESC
            '''.format(days), (f'%{stock_code}%',))
            
            rows = cursor.fetchall()
            posts = [self._row_to_dict(row) for row in rows]
            return posts
        except Exception as e:
            logger.error(f"獲取股票情緒失敗: {e}")
            return []
        finally:
            conn.close()
    
    async def get_trending_stocks(self, category=None, days=7, limit=20):
        """獲取熱門討論股票"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            from collections import Counter
            
            if category is not None:
                cursor.execute('''
                    SELECT stock_mentions, sentiment_score 
                    FROM posts 
                    WHERE category = ?
                    AND post_time > datetime('now', '-{} days')
                '''.format(days), (category,))
            else:
                cursor.execute('''
                    SELECT stock_mentions, sentiment_score 
                    FROM posts 
                    WHERE post_time > datetime('now', '-{} days')
                '''.format(days))
            
            rows = cursor.fetchall()
            
            stock_mentions = Counter()
            stock_sentiment = {}
            
            for row in rows:
                mentions_json = row[0]
                sentiment_score = row[1] if row[1] else 0
                
                try:
                    mentions = json.loads(mentions_json)
                    for stock in mentions:
                        stock_mentions[stock] += 1
                        if stock not in stock_sentiment:
                            stock_sentiment[stock] = []
                        stock_sentiment[stock].append(sentiment_score)
                except:
                    continue
            
            trending_stocks = []
            for stock, mentions in stock_mentions.most_common(limit):
                avg_sentiment = sum(stock_sentiment[stock]) / len(stock_sentiment[stock])
                trending_stocks.append({
                    'stock_code': stock,
                    'mentions': mentions,
                    'avg_sentiment': round(avg_sentiment, 3),
                    'sentiment_count': len(stock_sentiment[stock])
                })
            
            return trending_stocks
        except Exception as e:
            logger.error(f"獲取熱門股票失敗: {e}")
            return []
        finally:
            conn.close()
    
    async def get_statistics(self):
        """獲取數據統計"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 總帖子數
            cursor.execute('SELECT COUNT(*) FROM posts')
            total_posts = cursor.fetchone()[0]
            
            # 各板塊帖子數
            cursor.execute('''
                SELECT category, COUNT(*) 
                FROM posts 
                GROUP BY category
            ''')
            category_stats = dict(cursor.fetchall())
            
            # 情緒分佈
            cursor.execute('''
                SELECT sentiment_label, COUNT(*) 
                FROM posts 
                GROUP BY sentiment_label
            ''')
            sentiment_stats = dict(cursor.fetchall())
            
            # 平均情緒分數
            cursor.execute('SELECT AVG(sentiment_score) FROM posts')
            avg_sentiment = cursor.fetchone()[0] or 0
            
            stats = {
                'total_posts': total_posts,
                'category_distribution': category_stats,
                'sentiment_distribution': sentiment_stats,
                'average_sentiment': round(avg_sentiment, 3),
                'last_updated': datetime.now().isoformat()
            }
            
            return stats
        except Exception as e:
            logger.error(f"獲取統計失敗: {e}")
            return {}
        finally:
            conn.close()
    
    def _row_to_dict(self, row):
        """將資料庫行轉換為字典"""
        if len(row) < 15:
            return {}
        return {
            'post_id': row[0],
            'category': row[1],
            'title': row[2],
            'content': row[3],
            'author': row[4],
            'replies': row[5],
            'views': row[6],
            'likes': row[7],
            'post_time': row[8],
            'tags': json.loads(row[9]) if row[9] else [],
            'sentiment_score': row[10],
            'sentiment_label': row[11],
            'stock_mentions': json.loads(row[12]) if row[12] else [],
            'created_at': row[13],
            'updated_at': row[14]
        }
