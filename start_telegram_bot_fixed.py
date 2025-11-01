#!/usr/bin/env python3
"""
Telegram Bot with single-instance lock
"""

import os
import sys
import logging
import socket
import time
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Acquire single instance lock
LOCK_PORT = 39217
lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lock_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    lock_socket.bind(('127.0.0.1', LOCK_PORT))
    lock_socket.listen(1)
    logging.info(f"Single instance lock acquired on port {LOCK_PORT}")
except OSError:
    logging.error(f"Another bot instance is already running on port {LOCK_PORT}")
    sys.exit(1)

# Load environment variables
load_dotenv()

# Get bot token
token = os.getenv('TELEGRAM_BOT_TOKEN')
if not token:
    logging.error("TELEGRAM_BOT_TOKEN not found in environment")
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

def main():
    """Main program"""
    logging.info("Starting Telegram Bot...")

    # Create application
    application = Application.builder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("score", score))
    application.add_handler(CommandHandler("schedule", schedule))
    application.add_handler(CommandHandler("help", help_cmd))

    # Start bot with error handling
    try:
        logging.info("Bot is running. Press Ctrl+C to stop.")
        application.run_polling(
            allowed_updates=["message"],
            drop_pending_updates=True
        )
    except Exception as e:
        logging.error(f"Bot error: {e}")
    finally:
        logging.info("Bot stopped")

if __name__ == '__main__':
    main()
