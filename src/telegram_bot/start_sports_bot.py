#!/usr/bin/env python3
"""
體育比分 Bot 啟動腳本
修復版 - 解決網絡連接問題
"""

import os
import sys
import logging
from datetime import datetime

# 設置環境變量
os.environ["TELEGRAM_BOT_TOKEN"] = "7180490983:AAFbkKnDPC1MHAaOGzQA1fOs9FBwSGGonzI"

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("sports_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 添加路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 檢查 Token
token = os.getenv("TELEGRAM_BOT_TOKEN")
if not token:
    logger.error("❌ 未設置 TELEGRAM_BOT_TOKEN")
    sys.exit(1)

logger.info("✅ Token 已設置")

# 測試 Bot 連接
def test_bot_connection():
    """測試 Bot 連接"""
    import requests

    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()
        if data.get("ok"):
            bot_info = data.get("result", {})
            logger.info(f"✅ Bot 連接成功: @{bot_info.get('username')}")
            return True
        else:
            logger.error(f"❌ API 錯誤: {data}")
            return False

    except Exception as e:
        logger.error(f"❌ 連接測試失敗: {e}")
        return False

# 啟動 Bot
async def start_bot():
    """啟動 Bot"""
    from telegram.ext import Application

    try:
        # 創建 Application
        app = Application.builder().token(token).build()

        # 導入並註冊處理器
        logger.info("📦 導入體育比分模塊...")
        from sports_scoring import (
            NBAScraper,
            FootballScraper,
            CacheManager,
            DataProcessor
        )
        logger.info("✅ 體育比分模塊導入成功")

        # 導入體育比分處理器
        from sports_scoring.football_scraper import FootballScraper
        from sports_scoring.data_processor import DataProcessor

        # 定義命令處理器
        from telegram import Update
        from telegram.ext import ContextTypes, CommandHandler

        async def score_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            """體育比分查詢命令 - 使用真實數據"""
            from telegram.ext import reply_long

            try:
                # 獲取真實足球比分
                football_scraper = FootballScraper()
                scores = await football_scraper.fetch_scores()

                # 格式化數據
                message = DataProcessor.format_football_score(scores)

                # 添加NBA說明（簡化版）
                message += "\n\n🏀 NBA\n⚡ NBA比分功能即將推出\n\n"

                await reply_long(update, message)

            except Exception as e:
                error_msg = f"❌ 獲取比分失敗: {e}"
                logger.error(error_msg)
                await reply_long(update, error_msg)

        async def schedule_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            """賽程查詢命令 - 使用真實數據"""
            from telegram.ext import reply_long

            try:
                # 獲取真實賽程
                football_scraper = FootballScraper()
                schedule = await football_scraper.fetch_schedule(3)

                # 格式化賽程
                message = DataProcessor.format_schedule(schedule, sport_type="soccer")

                await reply_long(update, message)

            except Exception as e:
                error_msg = f"❌ 獲取賽程失敗: {e}"
                logger.error(error_msg)
                await reply_long(update, error_msg)

        async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            """幫助命令"""
            from telegram.ext import reply_long

            message = (
                "🤖 體育比分 Bot\n\n"
                "可用命令：\n"
                "/score - 查看比分\n"
                "/schedule - 查看賽程\n"
                "/help - 顯示此幫助\n\n"
                "示例：\n"
                "/score nba - 查看 NBA 比分\n"
                "/score soccer - 查看足球比分"
            )

            await reply_long(update, message)

        # 註冊命令處理器
        logger.info("📝 註冊命令處理器...")
        app.add_handler(CommandHandler("score", score_cmd))
        app.add_handler(CommandHandler("schedule", schedule_cmd))
        app.add_handler(CommandHandler("help", help_cmd))

        logger.info("🚀 Bot 啟動中...")
        logger.info(f"🤖 Bot 用戶名: @penguinai_bot")
        logger.info("⏰ 按 Ctrl+C 停止 Bot")

        # 啟動輪詢
        await app.initialize()
        await app.start()
        await app.updater.start_polling()

        # 保持運行
        import signal
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        await asyncio.Event().wait()

    except Exception as e:
        logger.error(f"❌ Bot 啟動失敗: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 70)
    print("體育比分 Bot 啟動器")
    print("=" * 70)
    print()

    # 測試連接
    if not test_bot_connection():
        print("❌ 連接測試失敗，請檢查網絡或 Token")
        sys.exit(1)

    print()

    # 啟動 Bot
    import asyncio
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        logger.info("👋 Bot 已停止")
