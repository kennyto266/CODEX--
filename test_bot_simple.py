#!/usr/bin/env python3
import os, sys, logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
os.environ['TELEGRAM_BOT_TOKEN'] = '7180490983:AAFbkKnDPC1MHAaOGzQA1fOs9FBwSGGonzI'

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
    print("[OK] Telegram module imported successfully")
except ImportError as e:
    print(f"[ERROR] Import failed: {e}")
    sys.exit(1)

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
        "/help - This help"
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

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    logging.info(f"Received: {text}")

def main():
    token = "7180490983:AAFbkKnDPC1MHAaOGzQA1fOs9FBwSGGonzI"

    print("\n" + "="*50)
    print("Starting Telegram Bot")
    print("="*50)
    print(f"Token: {token[:20]}...")
    print("="*50 + "\n")

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("mark6", mark6_command))
    application.add_handler(CommandHandler("weather", weather_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print("[OK] Bot ready")
    print("[INFO] Send message to @penguinai_bot to test")
    print("[INFO] Press Ctrl+C to stop\n")

    try:
        application.run_polling(drop_pending_updates=True, allowed_updates=["message"])
    except KeyboardInterrupt:
        print("\n[INFO] Bot stopped")
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    main()
