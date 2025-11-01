@echo off
chcp 65001 >nul
title Telegram Bot Quick Start

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║          Telegram 量化交易系统 Bot 快速启动                ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

:: 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到Python
    echo 请先安装Python 3.8+
    pause
    exit /b 1
)

:: 检查Bot Token
if "%TELEGRAM_BOT_TOKEN%"=="" (
    echo ⚠️  警告: 未设置TELEGRAM_BOT_TOKEN环境变量
    echo.
    echo 正在使用内置Token: 7180490983:AAFbkKnDPC1MHAaOGzQA1fOs9FBwSGGonzI
    echo.
    set TELEGRAM_BOT_TOKEN=7180490983:AAFbkKnDPC1MHAaOGzQA1fOs9FBwSGGonzI
)

echo ✅ 环境检查完成
echo.
echo 选择启动模式:
echo.
echo [1] 独立模式 (推荐) - 包含基础功能和体育比分
echo [2] 完整模式 - 包含所有量化交易功能
echo [3] 测试模式 - 仅测试连接不启动
echo.
set /p choice="请输入选择 (1-3): "

if "%choice%"=="1" (
    echo.
    echo 🚀 启动独立模式Bot...
    python start_bot_standalone.py
) else if "%choice%"=="2" (
    echo.
    echo 🚀 启动完整模式Bot...
    python src/telegram_bot/telegram_quant_bot.py
) else if "%choice%"=="3" (
    echo.
    echo 🧪 运行连接测试...
    python test_bot_simple.py
) else (
    echo.
    echo ❌ 无效选择
    pause
    exit /b 1
)

if %errorlevel% neq 0 (
    echo.
    echo ❌ 启动失败
    pause
)
