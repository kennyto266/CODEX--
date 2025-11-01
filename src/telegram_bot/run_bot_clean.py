#!/usr/bin/env python3
"""
Launch Telegram Bot (skip single instance lock)
"""

import os
import sys
import logging
import asyncio

# Change to project root directory
project_root = os.path.dirname(os.path.dirname(__file__))
os.chdir(project_root)
sys.path.insert(0, project_root)  # Add project root to path
sys.path.insert(0, os.path.join(project_root, 'src', 'telegram_bot'))  # Add telegram_bot to path

# Set environment variables
os.environ['TELEGRAM_BOT_TOKEN'] = '7180490983:AAFbkKnDPC1MHAaOGzQA1fOs9FBwSGGonzI'

# Import and run polling directly
from telegram_quant_bot import build_app

async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN not set")
        return

    print(f"Starting Telegram Bot (Token: {token[:20]}...)")
    print("Skipping single instance lock check")

    # Remove single instance lock check
    import telegram_quant_bot
    if hasattr(telegram_quant_bot, '_acquire_single_instance_lock'):
        # Patch to always return None
        telegram_quant_bot._acquire_single_instance_lock = lambda: None
        print("Patched single instance lock check")

    app = build_app(token)

    print("Bot application built successfully")
    print("Starting polling...")

    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=["message"])

    print("\n========================================")
    print(" Bot is running successfully!")
    print(" Send /mark6 command to test new feature")
    print(" Press Ctrl+C to stop")
    print("========================================\n")

    try:
        await asyncio.Event().wait()  # Wait forever
    except KeyboardInterrupt:
        print("\nStopping bot...")
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        print("Bot stopped")

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

    try:
        asyncio.run(main())
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
