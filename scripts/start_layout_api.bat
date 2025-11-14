@echo off
REM LayoutConfig API Windows启动脚本
REM Phase 8a: Frontend Testing Framework

echo ==========================================
echo LayoutConfig API 启动脚本
echo Phase 8a: Frontend Testing Framework
echo ==========================================
echo.

REM 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ 错误: Python未安装
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✓ %PYTHON_VERSION%

REM 激活虚拟环境（如果存在）
if exist ".venv310\Scripts\activate.bat" (
    call .venv310\Scripts\activate.bat
    echo ✓ 虚拟环境已激活
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✓ 虚拟环境已激活
) else (
    echo ⚠ 警告: 未检测到虚拟环境
    echo   建议创建: python -m venv .venv310
)

REM 安装依赖
echo.
echo 检查依赖包...
python -c "import fastapi, sqlalchemy, pydantic" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠ 正在安装依赖包...
    pip install fastapi uvicorn sqlalchemy pydantic structlog python-multipart
    echo ✓ 依赖包安装完成
) else (
    echo ✓ 依赖包已安装
)

REM 初始化数据库
echo.
echo 初始化数据库...
set DATABASE_URL=sqlite:///./layout_config.db
echo 数据库URL: %DATABASE_URL%

python -c "
import sys
sys.path.append(r'C:\Users\Penguin8n\CODEX--\CODEX--')

try:
    from src.database.base import Base
    from src.database.models.layout import LayoutConfigModel, LayoutComponentModel
    from src.api.dependencies.database import db_manager

    db_manager.create_tables()
    print('✓ 数据库表创建成功')
except Exception as e:
    print(f'✗ 数据库初始化失败: {e}')
    import traceback
    traceback.print_exc()
"

REM 启动API服务器
echo.
echo ==========================================
echo 启动API服务器...
echo ==========================================
echo.
echo API地址: http://localhost:8001
echo API文档: http://localhost:8001/api/docs
echo ReDoc文档: http://localhost:8001/api/redoc
echo.
echo 按 Ctrl+C 停止服务器
echo.

cd /c/Users/Penguin8n/CODEX--/CODEX--
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8001 --reload

pause
