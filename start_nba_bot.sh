#!/bin/bash

echo ""
echo "================================================"
echo "  NBA 比分 Telegram Bot 啟動器"
echo "================================================"
echo ""

# 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 未安裝"
    exit 1
fi
echo "[OK] Python3 已安裝"

# 檢查環境變量文件
if [ ! -f ".env" ]; then
    echo "[WARNING] .env 文件不存在"
    echo "請確保 TELEGRAM_BOT_TOKEN 已設置"
    echo ""
fi

# 檢查 TELEGRAM_BOT_TOKEN
TOKEN=$(grep "TELEGRAM_BOT_TOKEN" .env 2>/dev/null | cut -d'=' -f2)
if [ -z "$TOKEN" ]; then
    echo "[WARNING] TELEGRAM_BOT_TOKEN 未設置"
    echo "請在 .env 文件中設置您的 Bot Token"
    echo ""
fi

echo "[1/3] 檢查依賴..."
python3 -c "import aiohttp, telegram" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[ERROR] 缺少必要依賴，請運行:"
    echo "pip3 install -r requirements.txt"
    exit 1
fi
echo "[OK] 依賴檢查通過"

echo ""
echo "[2/3] 測試 NBA 比分功能..."
python3 test_nba_simple_v2.py
if [ $? -ne 0 ]; then
    echo ""
    echo "[WARNING] NBA 比分測試失敗，但將繼續啟動 Bot..."
    echo ""
fi

echo ""
echo "[3/3] 啟動 Telegram Bot..."
echo ""
echo "================================================"
echo "  Bot 啟動中..."
echo "  發送 /score nba 查看 NBA 比分"
echo "  按 Ctrl+C 停止 Bot"
echo "================================================"
echo ""

cd src/telegram_bot
python3 start_telegram_bot.py

echo ""
echo "Bot 已停止"
