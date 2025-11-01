@echo off
chcp 65001 >nul
echo ============================================================
echo Telegram 量化交易系统 Bot 启动器
echo ============================================================
echo.

REM 检查虚拟环境
if exist .venv310 (
    echo [INFO] 激活虚拟环境...
    call .venv310\Scripts\activate.bat
) else (
    echo [WARNING] 未找到虚拟环境 .venv310
)

REM 检查依赖
echo [INFO] 检查依赖...
python -c "import telegram" >nul 2>&1 && echo [OK] python-telegram-bot installed || echo [FAIL] 请安装: pip install python-telegram-bot
python -c "import playwright" >nul 2>&1 && echo [OK] playwright installed || echo [FAIL] 请安装: pip install playwright
python -c "import matplotlib" >nul 2>&1 && echo [OK] matplotlib installed || echo [FAIL] 请安装: pip install matplotlib

echo.
echo ============================================================
echo 启动 Bot...
echo ============================================================
echo.

REM 启动独立Bot（无量化系统依赖）
python start_bot_standalone.py
