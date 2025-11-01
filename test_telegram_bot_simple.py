#!/usr/bin/env python3
"""
簡單的 Telegram Bot 測試
"""

import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# 設置日誌
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /start 命令"""
    await update.message.reply_text('Bot is running!\n\nCommands:\n/score - View scores\n/schedule - View schedule')

async def score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /score command"""
    await update.message.reply_text('Getting scores...')

async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /schedule command"""
    await update.message.reply_text('Getting schedule...')

def main():
    """主程序"""
    # 載入環境變量
    load_dotenv()

    # 獲取 Bot Token
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN not found")
        return

    print(f"Bot Token: {token[:10]}...")

    # 創建應用
    application = Application.builder().token(token).build()

    # 添加處理程序
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("score", score))
    application.add_handler(CommandHandler("schedule", schedule))

    # Start bot
    print("Starting Telegram Bot...")
    application.run_polling()

if __name__ == '__main__':
    main()
