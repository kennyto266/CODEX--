"""
LIHKG 爬蟲核心引擎
整合 Chrome MCP 控制進行自動化數據採集
"""

import asyncio
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime

from .chrome_controller import LIHKGChromeController
from .parser import PostParser
from .sentiment import SentimentAnalyzer
from .storage import LIHKGDataStore

logger = logging.getLogger('lihkg_scraper.scraper')

class LIHKGScraper:
    """
    LIHKG 爬蟲核心引擎
    整合 Chrome MCP 控制進行自動化數據採集
    """
    
    def __init__(self, db_path: str = 'data/lihkg.db'):
        self.chrome_controller = LIHKGChromeController()
        self.parser = PostParser()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.data_store = LIHKGDataStore(db_path)
        self.rate_limiter = RateLimiter()
        
    async def initialize(self):
        """初始化爬蟲"""
        logger.info("初始化 LIHKG 爬蟲")
        
        # 初始化 Chrome 瀏覽器
        await self.chrome_controller.initialize()
        
        logger.info("爬蟲初始化完成")
    
    async def scrape_category(self, 
                              category_id: int, 
                              max_pages: int = 10) -> List[Dict]:
        """
        爬取指定板塊的所有帖子
        
        Args:
            category_id: 板塊 ID (2=股票, 15=期貨)
            max_pages: 最大頁數
            
        Returns:
            list: 爬取的帖子數據
        """
        logger.info(f"開始爬取板塊 {category_id}, 最多 {max_pages} 頁")
        
        all_posts = []
        
        try:
            # 導航到板塊首頁
            await self.chrome_controller.navigate_to_category(category_id)
            await self.chrome_controller.wait_for_page_load()
            
            for page in range(1, max_pages + 1):
                try:
                    logger.info(f"爬取第 {page}/{max_pages} 頁")
                    
                    # 提取帖子列表
                    raw_posts = await self.chrome_controller.extract_post_list()
                    
                    if not raw_posts:
                        logger.warning(f"第 {page} 頁無數據")
                        break
                    
                    # 解析和處理每個帖子
                    for raw_post in raw_posts:
                        try:
                            post = await self.parser.parse(raw_post)
                            post['category'] = category_id
                            
                            if self.parser.validate_post(post):
                                all_posts.append(post)
                            else:
                                logger.warning(f"帖子驗證失敗: {post.get('post_id', 'N/A')}")
                                
                        except Exception as e:
                            logger.error(f"解析帖子失敗: {e}")
                    
                    # 速率限制
                    await self.rate_limiter.wait()
                    
                except Exception as e:
                    logger.error(f"爬取第 {page} 頁失敗: {e}")
                    await asyncio.sleep(5)  # 錯誤後等待
                    continue
            
            logger.info(f"爬取完成，共獲取 {len(all_posts)} 個帖子")
            return all_posts
            
        except Exception as e:
            logger.error(f"爬取板塊失敗: {e}")
            raise
    
    async def scrape_post_details(self, post_id: str) -> Dict:
        """
        獲取帖子詳細內容
        
        Args:
            post_id: 帖子 ID
            
        Returns:
            dict: 帖子詳細數據
        """
        return await self.chrome_controller.get_post_details(post_id)
    
    async def process_posts(self, posts: List[Dict]) -> List[Dict]:
        """
        處理帖子列表 (情緒分析)
        
        Args:
            posts: 帖子列表
            
        Returns:
            list: 處理後的帖子列表
        """
        logger.info(f"開始處理 {len(posts)} 個帖子")
        
        # 批量情緒分析
        sentiments = await self.sentiment_analyzer.batch_analyze(posts)
        
        # 保存到資料庫
        await self.data_store.save_posts(posts, sentiments)
        
        # 合併結果
        processed_posts = []
        for post, sentiment in zip(posts, sentiments):
            post['sentiment'] = sentiment
            processed_posts.append(post)
        
        logger.info(f"處理完成")
        return processed_posts
    
    async def close(self):
        """關閉爬蟲"""
        logger.info("關閉 LIHKG 爬蟲")
        await self.chrome_controller.close()

class RateLimiter:
    """速率限制器"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.min_interval = 60 / requests_per_minute
        self.last_request = 0
    
    async def wait(self):
        """等待以符合速率限制"""
        now = time.time()
        elapsed = now - self.last_request
        
        if elapsed < self.min_interval:
            await asyncio.sleep(self.min_interval - elapsed)
        
        self.last_request = time.time()
