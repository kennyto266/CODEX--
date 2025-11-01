#!/bin/bash

# Telegram 量化交易系统 Bot 快速启动脚本

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║          Telegram 量化交易系统 Bot 快速启动                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3"
    echo "请先安装Python 3.8+"
    exit 1
fi

# 检查Bot Token
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "⚠️  警告: 未设置TELEGRAM_BOT_TOKEN环境变量"
    echo ""
    echo "正在使用内置Token: 7180490983:AAFbkKnDPC1MHAaOGzQA1fOs9FBwSGGonzI"
    echo ""
    export TELEGRAM_BOT_TOKEN="7180490983:AAFbkKnDPC1MHAaOGzQA1fOs9FBwSGGonzI"
fi

echo "✅ 环境检查完成"
echo ""
echo "选择启动模式:"
echo ""
echo "[1] 独立模式 (推荐) - 包含基础功能和体育比分"
echo "[2] 完整模式 - 包含所有量化交易功能"
echo "[3] 测试模式 - 仅测试连接不启动"
echo ""
read -p "请输入选择 (1-3): " choice

case $choice in
    1)
        echo ""
        echo "🚀 启动独立模式Bot..."
        python3 start_bot_standalone.py
        ;;
    2)
        echo ""
        echo "🚀 启动完整模式Bot..."
        python3 src/telegram_bot/telegram_quant_bot.py
        ;;
    3)
        echo ""
        echo "🧪 运行连接测试..."
        python3 test_bot_simple.py
        ;;
    *)
        echo ""
        echo "❌ 无效选择"
        exit 1
        ;;
esac

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 启动失败"
    read -p "按Enter键退出..."
fi
