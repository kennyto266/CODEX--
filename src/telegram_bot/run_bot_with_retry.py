#!/usr/bin/env python3
"""
Run Telegram Bot with automatic retry
"""

import os
import sys
import asyncio
import time

sys.path.insert(0, os.path.dirname(__file__))

# Set environment
os.environ['TELEGRAM_BOT_TOKEN'] = '7180490983:AAFbkKnDPC1MHAaOGzQA1fOs9FBwSGGonzI'

# Patch single instance lock
import telegram_quant_bot
telegram_quant_bot._acquire_single_instance_lock = lambda: None

# Import and run
from telegram_quant_bot import build_app

async def run_bot():
    max_retries = 30  # Try for about 5 minutes
    retry_delay = 10  # seconds

    for attempt in range(max_retries):
        try:
            print(f"Starting bot (attempt {attempt + 1}/{max_retries})...")
            app = build_app('7180490983:AAFbkKnDPC1MHAaOGzQA1fOs9FBwSGGonzI')

            await app.initialize()
            await app.start()
            await app.updater.start_polling(allowed_updates=['message'])

            print("\n" + "="*50)
            print(" Bot is RUNNING successfully!")
            print("="*50)
            print("\nSend these commands to test:")
            print("  /help    - View all commands")
            print("  /mark6   - Test new Mark6 feature")
            print("  /weather - Test weather service")
            print("\nPress Ctrl+C to stop")
            print("="*50 + "\n")

            # Run forever
            await asyncio.Event().wait()

        except Exception as e:
            error_msg = str(e)
            if "Conflict" in error_msg:
                print(f"⚠️  Telegram conflict detected (attempt {attempt + 1})")
                print(f"   Waiting {retry_delay}s for server session to timeout...")
                await asyncio.sleep(retry_delay)
            else:
                print(f"❌ Error: {e}")
                await asyncio.sleep(retry_delay)

    print("\n❌ Max retries reached. Please try again later.")

if __name__ == "__main__":
    asyncio.run(run_bot())
