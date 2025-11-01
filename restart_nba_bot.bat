@echo off
echo.
echo ================================================
echo   重啟 NBA 比分 Telegram Bot
echo ================================================
echo.

echo [1/3] 停止舊 Bot 進程...
taskkill /f /im python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo [2/3] 清除緩存...
python -c "import os; [os.remove(f) for f in os.listdir('.') if f.endswith('.pyc')]" >nul 2>&1
rmdir /s /q __pycache__ >nul 2>&1
rmdir /s /q src\__pycache__ >nul 2>&1

echo [3/3] 啟動 Bot...
echo.
echo ================================================
echo   Bot 啟動中...
echo   發送 /score nba 查看 NBA 比分
echo   按 Ctrl+C 停止
echo ================================================
echo.

cd src\telegram_bot
python start_telegram_bot.py

echo.
echo Bot 已停止
pause
