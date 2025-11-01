#!/usr/bin/env python3
"""
Telegram Bot with persistent retry and error handling
"""

import os
import sys
import logging
import asyncio
import time
from datetime import datetime
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        'Bot is running!\n\n'
        'Available commands:\n'
        '/score - View football scores\n'
        '/schedule - View football schedule\n'
        '/help - Show help'
    )

async def score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /score command"""
    await update.message.reply_text('Getting football scores...')

async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /schedule command"""
    await update.message.reply_text('Getting football schedule...')

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logging.error(f"Update {update} caused error {context.error}")

def main():
    """Main program with retry logic"""
    max_retries = 10
    retry_delay = 10

    for attempt in range(1, max_retries + 1):
        try:
            logging.info(f"Attempt {attempt}/{max_retries} to start bot...")

            # Create application
            application = Application.builder().token(token).build()

            # Add handlers
            application.add_handler(CommandHandler("start", start))
            application.add_handler(CommandHandler("score", score))
            application.add_handler(CommandHandler("schedule", schedule))
            application.add_handler(CommandHandler("help", help_cmd))

            # Add error handler
            application.add_error_handler(error_handler)

            logging.info("Starting bot with polling...")
            application.run_polling(
                allowed_updates=["message"],
                drop_pending_updates=True,
                timeout=30
            )
            break  # Success, exit loop

        except Exception as e:
            logging.error(f"Attempt {attempt} failed: {e}")

            if "Conflict" in str(e):
                logging.warning("Conflict detected. Waiting 60 seconds before retry...")
                time.sleep(60)
            elif attempt < max_retries:
                logging.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logging.error("Max retries reached. Exiting.")
                sys.exit(1)

if __name__ == '__main__':
    main()
