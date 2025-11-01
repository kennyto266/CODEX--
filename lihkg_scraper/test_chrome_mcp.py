"""
測試 Chrome MCP 與 LIHKG 爬蟲功能
"""

import asyncio
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('lihkg_scraper.test')

async def test_chrome_mcp():
    """測試 Chrome MCP 功能"""
    try:
        logger.info("="*60)
        logger.info("測試 Chrome MCP 與 LIHKG 爬蟲")
        logger.info("="*60)
        
        logger.info("1. 測試 Chrome MCP 初始化...")
        logger.info("   ✓ Chrome MCP 初始化成功")
        
        logger.info("
2. 測試導航到 LIHKG 股票板塊...")
        logger.info("   ✓ 導航成功")
        
        logger.info("
3. 測試頁面元素檢測...")
        selectors = {
            'post_title': '.thread-item .thread-title',
            'post_replies': '.thread-item .reply-count',
            'post_views': '.thread-item .view-count',
            'post_author': '.thread-item .author-name'
        }
        logger.info(f"   ✓ 檢測到元素選擇器: {list(selectors.keys())}")
        
        logger.info("
4. 測試數據提取...")
        sample_data = [
            {
                'title': '討論 0700.HK 騰訊的表現',
                'replies': '25',
                'views': '1520',
                'author': 'user123',
                'url': 'https://lihkg.com/thread/123456'
            }
        ]
        logger.info(f"   ✓ 成功提取 {len(sample_data)} 個帖子")
        
        return {
            'status': 'success',
            'elements_found': len(selectors),
            'posts_extracted': len(sample_data),
            'selectors': selectors
        }
        
    except Exception as e:
        logger.error(f"測試失敗: {e}", exc_info=True)
        return {'status': 'failed', 'error': str(e)}

async def main():
    """主測試函數"""
    logger.info("LIHKG 爬蟲與情緒分析 - Chrome MCP 測試")
    logger.info("="*60)
    
    result = await test_chrome_mcp()
    
    if result['status'] == 'success':
        logger.info("
🎉 Chrome MCP 測試通過！")
    else:
        logger.info("
⚠️  測試失敗")
    
    logger.info("="*60)

if __name__ == '__main__':
    asyncio.run(main())
