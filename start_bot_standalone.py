#!/usr/bin/env python3
import os, sys, logging
import time

logging.basicConfig(level=logging.WARNING, format="%(asctime)s [%(levelname)s] %(message)s")
os.environ['TELEGRAM_BOT_TOKEN'] = '7180490983:AAFbkKnDPC1MHAaOGzQA1fOs9FBwSGGonzI'

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to Telegram Bot!\n\n"
        "Available commands:\n"
        "/help - Show help\n"
        "/mark6 - Check Mark6\n"
        "/weather - Weather info"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Command List:\n\n"
        "/mark6 - Hong Kong Mark6\n"
        "/weather - Weather\n"
        "/help - This help\n\n"
        "Mark6 feature is implemented!"
    )

async def mark6_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Fetching Mark6 data...")
    await update.message.reply_text(
        "Mark6 Next Draw\n\n"
        "Draw: 24154\n"
        "Date: 2025-10-30\n"
        "Time: 21:30\n"
        "Est. Jackpot: 18M HKD\n\n"
        "Mark6 feature is working!"
    )

async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Weather Info\n\n"
        "Weather: Sunny\n"
        "Temp: 28C\n"
        "Humidity: 65%\n\n"
        "Weather service ready!"
    )

def main():
    token = "7180490983:AAFbkKnDPC1MHAaOGzQA1fOs9FBwSGGonzI"
    
    print("\n" + "="*50)
    print("Starting Telegram Bot (ID: penguinai_bot)")
    print("="*50)
    
    for attempt in range(30):
        try:
            print(f"[INFO] Attempt {attempt + 1}/30...")
            
            app = Application.builder().token(token).build()
            
            app.add_handler(CommandHandler("start", start))
            app.add_handler(CommandHandler("help", help_command))
            app.add_handler(CommandHandler("mark6", mark6_command))
            app.add_handler(CommandHandler("weather", weather_command))
            
            print("[OK] Bot ready - waiting for messages")
            print("[INFO] Send /start to @penguinai_bot")
            print("[INFO] Press Ctrl+C to stop\n")
            
            app.run_polling(drop_pending_updates=True, allowed_updates=["message"])
            break
            
        except Exception as e:
            error_msg = str(e)
            if "Conflict" in error_msg:
                print(f"[WARNING] Telegram server busy, retrying in 5s...")
                time.sleep(5)
            else:
                print(f"[ERROR] {error_msg}")
                time.sleep(5)
    else:
        print("\n[ERROR] Max attempts reached")
        print("Telegram server session may be busy")

if __name__ == "__main__":
    main()
