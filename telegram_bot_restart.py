#!/usr/bin/env python3
"""
Telegram Bot that restarts on conflict
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
    level=logging.INFO
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

def main():
    """Main program with restart on conflict"""
    max_retries = 5
    retry_delay = 30

    for attempt in range(1, max_retries + 1):
        try:
            logging.info(f"=== Attempt {attempt}/{max_retries} ===")

            # Create application
            application = Application.builder().token(token).build()

            # Add handlers
            application.add_handler(CommandHandler("start", start))
            application.add_handler(CommandHandler("score", score))
            application.add_handler(CommandHandler("schedule", schedule))
            application.add_handler(CommandHandler("help", help_cmd))

            logging.info("Starting bot...")
            application.run_polling(
                allowed_updates=["message"],
                drop_pending_updates=True,
                timeout=10,
                poll_interval=1.0
            )

            # If we get here, bot is running successfully
            logging.info("Bot is running successfully!")
            while True:
                time.sleep(1)

        except Exception as e:
            error_msg = str(e)
            logging.error(f"Error: {error_msg}")

            if "Conflict" in error_msg:
                logging.warning(f"Conflict detected! Restarting in {retry_delay} seconds...")
                time.sleep(retry_delay)
                logging.info("Restarting bot...")
                continue
            elif attempt < max_retries:
                logging.warning(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logging.error("Max retries reached. Exiting.")
                sys.exit(1)

if __name__ == '__main__':
    main()
