"""
啟動 LIHKG API 服務器
"""

import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('lihkg_scraper.api')

if __name__ == '__main__':
    logger.info("啟動 LIHKG 情緒分析 API 服務器...")
    logger.info("API 文檔: http://localhost:8000/docs")
    logger.info("健康檢查: http://localhost:8000/health")
    
    uvicorn.run(
        "api.__init__:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
