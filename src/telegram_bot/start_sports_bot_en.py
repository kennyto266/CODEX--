#!/usr/bin/env python3
"""
Sports Score Bot Launcher - English Version
"""

import os
import sys
import logging
from datetime import datetime

# Set environment
os.environ["TELEGRAM_BOT_TOKEN"] = "7180490983:AAFbkKnDPC1MHAaOGzQA1fOs9FBwSGGonzI"

# Configure logging (English only)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("sports_bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Check Token
token = os.getenv("TELEGRAM_BOT_TOKEN")
if not token:
    logger.error("TELEGRAM_BOT_TOKEN not set")
    sys.exit(1)

logger.info("Token configured")

# Test Bot connection
def test_bot_connection():
    """Test Bot connection"""
    import requests

    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()
        if data.get("ok"):
            bot_info = data.get("result", {})
            logger.info(f"Bot connected: @{bot_info.get('username')}")
            return True
        else:
            logger.error(f"API error: {data}")
            return False

    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False

# Start Bot
async def start_bot():
    """Start Bot"""
    from telegram.ext import Application

    try:
        # Create Application
        app = Application.builder().token(token).build()

        # Import sports scoring modules
        logger.info("Importing sports scoring modules...")
        from sports_scoring import (
            NBAScraper,
            FootballScraper,
            CacheManager,
            DataProcessor
        )
        logger.info("Sports scoring modules imported successfully")

        # Import sports score processors
        from sports_scoring.football_scraper import FootballScraper
        from sports_scoring.data_processor import DataProcessor

        # Define command handlers
        from telegram import Update
        from telegram.ext import ContextTypes, CommandHandler

        async def score_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            """Sports score query command - using real data"""
            try:
                # Get real football scores
                football_scraper = FootballScraper()
                scores = await football_scraper.fetch_scores()

                # Format data
                message = DataProcessor.format_football_score(scores)

                # Add NBA note
                message += "\n\nBasketball\nNBA scores coming soon\n\n"

                await update.message.reply_text(message)

            except Exception as e:
                error_msg = f"Failed to get scores: {e}"
                logger.error(error_msg)
                await update.message.reply_text(error_msg)

        async def schedule_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            """Schedule query command - using real data"""
            try:
                # Get real schedule
                football_scraper = FootballScraper()
                schedule = await football_scraper.fetch_schedule(3)

                # Format schedule
                message = DataProcessor.format_schedule(schedule, sport_type="soccer")

                await update.message.reply_text(message)

            except Exception as e:
                error_msg = f"Failed to get schedule: {e}"
                logger.error(error_msg)
                await update.message.reply_text(error_msg)

        async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            """Help command"""
            message = (
                "Sports Score Bot\n\n"
                "Available commands:\n"
                "/score - View scores\n"
                "/schedule - View schedule\n"
                "/help - Show help\n\n"
                "Examples:\n"
                "/score - View all scores\n"
                "/schedule - View future schedule"
            )

            await update.message.reply_text(message)

        # Register command handlers
        logger.info("Registering command handlers...")
        app.add_handler(CommandHandler("score", score_cmd))
        app.add_handler(CommandHandler("schedule", schedule_cmd))
        app.add_handler(CommandHandler("help", help_cmd))

        logger.info("Starting bot...")
        logger.info(f"Bot username: @penguinai_bot")
        logger.info("Press Ctrl+C to stop bot")

        # Start polling
        await app.initialize()
        await app.start()
        await app.updater.start_polling()

        # Keep running
        import signal
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        await asyncio.Event().wait()

    except Exception as e:
        logger.error(f"Bot start failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 70)
    print("Sports Score Bot Launcher")
    print("=" * 70)
    print()

    # Test connection
    if not test_bot_connection():
        print("Connection test failed, check network or Token")
        sys.exit(1)

    print()

    # Start Bot
    import asyncio
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped")
