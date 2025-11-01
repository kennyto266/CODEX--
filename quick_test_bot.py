#!/usr/bin/env python3
"""
快速測試 Bot - 簡化版
"""

import os
import sys
import requests

os.environ["TELEGRAM_BOT_TOKEN"] = "7180490983:AAFbkKnDPC1MHAaOGzQA1fOs9FBwSGGonzI"

token = os.getenv("TELEGRAM_BOT_TOKEN")

print("=" * 70)
print("Bot 連接測試")
print("=" * 70)

# 測試 1: 獲取 Bot 信息
print("\n[1] 獲取 Bot 信息...")
url = f"https://api.telegram.org/bot{token}/getMe"
response = requests.get(url)
data = response.json()

if data.get("ok"):
    bot = data.get("result", {})
    print(f"   用戶名: @{bot.get('username')}")
    print(f"   名字: {bot.get('first_name')}")
    print("   [OK] Bot 信息獲取成功")
else:
    print(f"   [FAIL] {data}")
    sys.exit(1)

# 測試 2: 發送測試消息
print("\n[2] 發送測試消息...")
chat_id = "1005293427"  # 管理員 Chat ID

message = (
    "🎉 體育比分 Bot 測試\n\n"
    "Bot 已經成功啟動！\n"
    "可以使用的命令：\n"
    "/score - 查看比分\n"
    "/schedule - 查看賽程\n"
    "/help - 幫助"
)

url = f"https://api.telegram.org/bot{token}/sendMessage"
data = {
    "chat_id": chat_id,
    "text": message
}

try:
    response = requests.post(url, data=data, timeout=5)
    if response.status_code == 200:
        result = response.json()
        if result.get("ok"):
            print("   [OK] 測試消息已發送")
        else:
            print(f"   [FAIL] {result}")
    else:
        print(f"   [FAIL] HTTP {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"   [FAIL] {e}")

print("\n" + "=" * 70)
print("[DONE] 測試完成")
print("=" * 70)
print("\nBot 已經可以工作了！")
print("請在 Telegram 中發送 /help 給 @penguinai_bot 查看所有命令")
