#!/bin/bash

echo ""
echo "================================================"
echo "  重啟 NBA 比分 Telegram Bot"
echo "================================================"
echo ""

echo "[1/3] 停止舊 Bot 進程..."
pkill -f telegram
sleep 2

echo "[2/3] 清除緩存..."
find . -name "*.pyc" -delete 2>/dev/null
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

echo "[3/3] 啟動 Bot..."
echo ""
echo "================================================"
echo "  Bot 啟動中..."
echo "  發送 /score nba 查看 NBA 比分"
echo "  按 Ctrl+C 停止"
echo "================================================"
echo ""

cd src/telegram_bot
python3 start_telegram_bot.py

echo ""
echo "Bot 已停止"
