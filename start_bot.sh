#!/bin/bash
# Telegram Bot启动脚本

echo "============================================================"
echo "Telegram 量化交易系统 Bot 启动器"
echo "============================================================"
echo ""

# 检查虚拟环境
if [ -d ".venv310" ]; then
    echo "[INFO] 激活虚拟环境..."
    source .venv310/bin/activate
else
    echo "[WARNING] 未找到虚拟环境 .venv310"
fi

# 检查依赖
echo "[INFO] 检查依赖..."
python -c "import telegram; print('[OK] python-telegram-bot installed')" 2>/dev/null || echo "[FAIL] 请安装: pip install python-telegram-bot"
python -c "import playwright; print('[OK] playwright installed')" 2>/dev/null || echo "[FAIL] 请安装: pip install playwright"
python -c "import matplotlib; print('[OK] matplotlib installed')" 2>/dev/null || echo "[FAIL] 请安装: pip install matplotlib"

echo ""

# 检查环境变量
if [ -f ".env" ]; then
    echo "[OK] 找到 .env 文件"
else
    echo "[WARNING] 未找到 .env 文件，请复制 .env.example 并配置"
fi

echo ""
echo "============================================================"
echo "启动 Bot..."
echo "============================================================"
echo ""

# 启动Bot
python src/telegram_bot/telegram_quant_bot.py
