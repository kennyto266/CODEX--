#!/usr/bin/env python3
"""
Telegram Bot that handles conflicts gracefully
"""

import os
import sys
import logging
import time
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()
token = os.getenv('TELEGRAM_BOT_TOKEN')

if not token:
    logging.error("TELEGRAM_BOT_TOKEN not found")
    sys.exit(1)

logging.info(f"Bot token: {token[:10]}...")

async def start(update: Update, context):
    """Handle /start command"""
    await update.message.reply_text(
        'Bot is running!\n\n'
        'Available commands:\n'
        '/score - View football scores\n'
        '/schedule - View football schedule\n'
        '/help - Show help'
    )

async def score(update: Update, context):
    """Handle /score command"""
    await update.message.reply_text('Getting football scores...')

async def schedule(update: Update, context):
    """Handle /schedule command"""
    await update.message.reply_text('Getting football schedule...')

async def help_cmd(update: Update, context):
    """Handle /help command"""
    help_text = (
        'Available Commands:\n\n'
        '/start - Start the bot\n'
        '/score - Get football scores\n'
        '/schedule - Get football schedule\n'
        '/help - Show this help message\n\n'
        'Bot Features:\n'
        '- Premier League data integration\n'
        '- Multi-layer data sources\n'
        '- Real-time performance monitoring'
    )
    await update.message.reply_text(help_text)

async def error_handler(update: Update, context):
    """Handle errors"""
    logging.error(f"Exception while handling an update: {context.error}")

    # Check if it's a conflict error
    if "Conflict" in str(context.error):
        logging.warning("Conflict detected! This means another bot instance is running.")
        logging.warning("Stopping this instance...")

        # Stop the application
        await context.application.stop()

def main():
    """Main program with proper error handling"""
    max_restarts = 5
    restart_delay = 60

    for attempt in range(1, max_restarts + 1):
        try:
            logging.info(f"=== Starting bot (attempt {attempt}/{max_restarts}) ===")

            # Create application
            application = Application.builder().token(token).build()

            # Add handlers
            application.add_handler(CommandHandler("start", start))
            application.add_handler(CommandHandler("score", score))
            application.add_handler(CommandHandler("schedule", schedule))
            application.add_handler(CommandHandler("help", help_cmd))

            # Add error handler
            application.add_error_handler(error_handler)

            logging.info("Bot is running...")
            logging.info("Send /start to the bot to test it!")

            # Start polling
            application.run_polling(
                allowed_updates=["message"],
                drop_pending_updates=True,
                timeout=10,
                poll_interval=1.0
            )

            # If we get here, bot stopped normally
            logging.info("Bot stopped normally")
            break

        except Exception as e:
            error_msg = str(e)
            logging.error(f"Bot crashed: {error_msg}")

            if "Conflict" in error_msg:
                logging.warning(f"Conflict detected. Waiting {restart_delay} seconds before restart...")
                time.sleep(restart_delay)
                continue
            elif attempt < max_restarts:
                logging.warning(f"Retrying in {restart_delay} seconds...")
                time.sleep(restart_delay)
            else:
                logging.error("Max restarts reached. Exiting.")
                sys.exit(1)

if __name__ == '__main__':
    main()
