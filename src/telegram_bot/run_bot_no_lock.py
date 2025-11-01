#!/usr/bin/env python3
"""
啟動Telegram Bot（跳過單實例鎖）
"""

import os
import sys
import logging

# 設置環境變量
os.environ['TELEGRAM_BOT_TOKEN'] = '7180490983:AAFbkKnDPC1MHAaOGzQA1fOs9FBwSGGonzI'
os.environ['BOT_SINGLETON_PORT'] = '39230'

# 添加當前目錄到路徑
sys.path.insert(0, os.path.dirname(__file__))

# 導入並直接調用run_polling
import asyncio
from telegram_quant_bot import build_app

async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("❌ 未設置 TELEGRAM_BOT_TOKEN")
        return

    print(f"🚀 啟動Telegram Bot (Token: {token[:20]}...)")
    print("✅ 跳過單實例鎖檢查")

    app = build_app(token)

    print("✅ Bot應用已構建")
    print("✅ 開始輪詢...")

    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=["message"])
    print("\n🤖 Bot已成功啟動並運行！")
    print("📱 可以發送消息給Bot進行測試")
    print("⏹️  按 Ctrl+C 停止\n")

    try:
        await asyncio.Event().wait()  # 永遠等待
    except KeyboardInterrupt:
        print("\n👋 正在停止Bot...")
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        print("✅ Bot已停止")

if __name__ == "__main__":
    # 配置日誌
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # 運行
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
