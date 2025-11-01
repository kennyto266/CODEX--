@echo off
echo.
echo ================================================
echo   NBA 比分 Telegram Bot 啟動器
echo ================================================
echo.

REM 檢查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 未安裝或未添加到 PATH
    pause
    exit /b 1
)

REM 檢查環境變量文件
if not exist ".env" (
    echo [WARNING] .env 文件不存在
    echo 請確保 TELEGRAM_BOT_TOKEN 已設置
    echo.
)

REM 檢查 TELEGRAM_BOT_TOKEN
for /f "tokens=2 delims==" %%i in ('findstr "TELEGRAM_BOT_TOKEN" .env 2^>nul') do set TOKEN=%%i
if "%TOKEN%"=="" (
    echo [WARNING] TELEGRAM_BOT_TOKEN 未設置
    echo 請在 .env 文件中設置您的 Bot Token
    echo.
)

echo [1/3] 檢查依賴...
python -c "import aiohttp, telegram" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 缺少必要依賴，請運行:
    echo pip install -r requirements.txt
    pause
    exit /b 1
)
echo [OK] 依賴檢查通過

echo.
echo [2/3] 測試 NBA 比分功能...
python test_nba_simple_v2.py
if errorlevel 1 (
    echo.
    echo [WARNING] NBA 比分測試失敗，但將繼續啟動 Bot...
    echo.
)

echo.
echo [3/3] 啟動 Telegram Bot...
echo.
echo ================================================
echo   Bot 啟動中...
echo   發送 /score nba 查看 NBA 比分
echo   按 Ctrl+C 停止 Bot
echo ================================================
echo.

cd src\telegram_bot
python start_telegram_bot.py

echo.
echo Bot 已停止
pause
