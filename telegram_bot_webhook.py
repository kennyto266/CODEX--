#!/usr/bin/env python3
"""
Telegram Bot using webhook instead of polling
"""

import os
import sys
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)

# Load environment variables
load_dotenv()
token = os.getenv('TELEGRAM_BOT_TOKEN')

if not token:
    logging.error("TELEGRAM_BOT_TOKEN not found")
    sys.exit(1)

logging.info(f"Bot token: {token[:10]}...")

# Create application
application = Application.builder().token(token).build()

# Add handlers
@application.route("/")
async def webhook(update: Update):
    """Handle webhook updates"""
    return jsonify({"status": "ok"})

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

# Register handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("score", score))
application.add_handler(CommandHandler("schedule", schedule))
application.add_handler(CommandHandler("help", help_cmd))

@app.route('/webhook', methods=['POST'])
async def webhook():
    """Webhook endpoint"""
    update = Update.de_json(request.get_json(), application.bot)
    await application.process_update(update)
    return 'ok'

if __name__ == '__main__':
    # Set webhook
    WEBHOOK_URL = f"https://api.telegram.org/bot{token}/setWebhook"
    webhook_url = "https://your-domain.com/webhook"  # Replace with actual URL

    # For testing, we'll use polling instead
    logging.info("Starting bot with polling...")
    try:
        application.run_polling(
            allowed_updates=["message"],
            drop_pending_updates=True
        )
    except Exception as e:
        logging.error(f"Bot error: {e}")
