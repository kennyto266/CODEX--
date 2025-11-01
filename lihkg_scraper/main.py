"""
LIHKG 爬蟲主程序
"""

import asyncio
import logging
import sys
from pathlib import Path

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/lihkg_scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('lihkg_scraper')

async def main():
    """主程序"""
    from core.scraper import LIHKGScraper
    
    # 確保目錄存在
    Path('data').mkdir(exist_ok=True)
    Path('logs').mkdir(exist_ok=True)
    
    logger.info("="*60)
    logger.info("LIHKG 財經台爬蟲啟動")
    logger.info("="*60)
    
    scraper = LIHKGScraper()
    
    try:
        # 初始化
        await scraper.initialize()
        
        # 爬取股票板塊 (category/2)
        logger.info("\n開始爬取股票板塊...")
        stock_posts = await scraper.scrape_category(category_id=2, max_pages=5)
        if stock_posts:
            processed_stock = await scraper.process_posts(stock_posts)
            logger.info(f"股票板塊: 獲取 {len(stock_posts)} 個帖子")
        
        # 爬取期貨板塊 (category/15)
        logger.info("\n開始爬取期貨板塊...")
        futures_posts = await scraper.scrape_category(category_id=15, max_pages=5)
        if futures_posts:
            processed_futures = await scraper.process_posts(futures_posts)
            logger.info(f"期貨板塊: 獲取 {len(futures_posts)} 個帖子")
        
        # 統計結果
        total = len(stock_posts) + len(futures_posts)
        logger.info("\n" + "="*60)
        logger.info(f"爬取完成！總計: {total} 個帖子")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"爬取失敗: {e}", exc_info=True)
    finally:
        await scraper.close()

if __name__ == '__main__':
    asyncio.run(main())
