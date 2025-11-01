#!/usr/bin/env python3
"""
体育比分 Bot 启动脚本 - 简化版（无emoji）
"""

import os
import sys
import logging
from datetime import datetime

# 设置环境变量
os.environ["TELEGRAM_BOT_TOKEN"] = "7180490983:AAFbkKnDPC1MHAaOGzQA1fOs9FBwSGGonzI"

# 配置日志（无emoji）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("sports_bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 添加路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 检查 Token
token = os.getenv("TELEGRAM_BOT_TOKEN")
if not token:
    logger.error("Token 未设置")
    sys.exit(1)

logger.info("Token 已设置")

# 测试 Bot 连接
def test_bot_connection():
    """测试 Bot 连接"""
    import requests

    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()
        if data.get("ok"):
            bot_info = data.get("result", {})
            logger.info(f"Bot 连接成功: @{bot_info.get('username')}")
            return True
        else:
            logger.error(f"API 错误: {data}")
            return False

    except Exception as e:
        logger.error(f"连接测试失败: {e}")
        return False

# 启动 Bot
async def start_bot():
    """启动 Bot"""
    from telegram.ext import Application

    try:
        # 创建 Application
        app = Application.builder().token(token).build()

        # 导入体育比分模块
        logger.info("导入体育比分模块...")
        from sports_scoring import (
            NBAScraper,
            FootballScraper,
            CacheManager,
            DataProcessor
        )
        logger.info("体育比分模块导入成功")

        # 导入体育比分处理器
        from sports_scoring.football_scraper import FootballScraper
        from sports_scoring.data_processor import DataProcessor

        # 定义命令处理器
        from telegram import Update
        from telegram.ext import ContextTypes, CommandHandler

        async def score_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            """体育比分查询命令 - 使用真实数据"""
            from telegram.ext import reply_long

            try:
                # 获取真实足球比分
                football_scraper = FootballScraper()
                scores = await football_scraper.fetch_scores()

                # 格式化数据
                message = DataProcessor.format_football_score(scores)

                # 添加NBA说明（简化版）
                message += "\n\n篮球\n篮球比分功能即将推出\n\n"

                await reply_long(update, message)

            except Exception as e:
                error_msg = f"获取比分失败: {e}"
                logger.error(error_msg)
                await reply_long(update, error_msg)

        async def schedule_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            """赛程查询命令 - 使用真实数据"""
            from telegram.ext import reply_long

            try:
                # 获取真实赛程
                football_scraper = FootballScraper()
                schedule = await football_scraper.fetch_schedule(3)

                # 格式化赛程
                message = DataProcessor.format_schedule(schedule, sport_type="soccer")

                await reply_long(update, message)

            except Exception as e:
                error_msg = f"获取赛程失败: {e}"
                logger.error(error_msg)
                await reply_long(update, error_msg)

        async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            """帮助命令"""
            from telegram.ext import reply_long

            message = (
                "体育比分 Bot\n\n"
                "可用命令：\n"
                "/score - 查看比分\n"
                "/schedule - 查看赛程\n"
                "/help - 显示此帮助\n\n"
                "示例：\n"
                "/score - 查看所有比分\n"
                "/schedule - 查看未来赛程"
            )

            await reply_long(update, message)

        # 注册命令处理器
        logger.info("注册命令处理器...")
        app.add_handler(CommandHandler("score", score_cmd))
        app.add_handler(CommandHandler("schedule", schedule_cmd))
        app.add_handler(CommandHandler("help", help_cmd))

        logger.info("Bot 启动中...")
        logger.info(f"Bot 用户名: @penguinai_bot")
        logger.info("按 Ctrl+C 停止 Bot")

        # 启动轮询
        await app.initialize()
        await app.start()
        await app.updater.start_polling()

        # 保持运行
        import signal
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        await asyncio.Event().wait()

    except Exception as e:
        logger.error(f"Bot 启动失败: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 70)
    print("体育比分 Bot 启动器")
    print("=" * 70)
    print()

    # 测试连接
    if not test_bot_connection():
        print("连接测试失败，请检查网络或 Token")
        sys.exit(1)

    print()

    # 启动 Bot
    import asyncio
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        logger.info("Bot 已停止")
