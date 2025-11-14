#!/bin/bash

# LayoutConfig API快速启动脚本
# Phase 8a - T214-T218

set -e

echo "=========================================="
echo "LayoutConfig API 启动脚本"
echo "Phase 8a: Frontend Testing Framework"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Python
if ! command -v python &> /dev/null; then
    echo -e "${RED}✗ 错误: Python未安装${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python已安装: $(python --version)"

# 检查虚拟环境
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠ 警告: 未检测到虚拟环境${NC}"
    read -p "是否激活虚拟环境? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -f ".venv310/bin/activate" ]; then
            source .venv310/bin/activate
            echo -e "${GREEN}✓${NC} 已激活虚拟环境"
        elif [ -f "venv/bin/activate" ]; then
            source venv/bin/activate
            echo -e "${GREEN}✓${NC} 已激活虚拟环境"
        else
            echo -e "${YELLOW}⚠ 建议创建虚拟环境: python -m venv .venv310${NC}"
        fi
    fi
else
    echo -e "${GREEN}✓${NC} 虚拟环境已激活"
fi

# 安装依赖
echo ""
echo "检查依赖包..."
python -c "import fastapi, sqlalchemy, pydantic" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠ 正在安装依赖包...${NC}"
    pip install fastapi uvicorn sqlalchemy pydantic structlog python-multipart
    echo -e "${GREEN}✓${NC} 依赖包安装完成"
else
    echo -e "${GREEN}✓${NC} 依赖包已安装"
fi

# 初始化数据库
echo ""
echo "初始化数据库..."
export DATABASE_URL="${DATABASE_URL:-sqlite:///./layout_config.db}"
echo "数据库URL: $DATABASE_URL"

python -c "
import sys
sys.path.append('/c/Users/Penguin8n/CODEX--/CODEX--')

from src.database.base import Base
from src.database.models.layout import LayoutConfigModel, LayoutComponentModel
from src.api.dependencies.database import db_manager

# 创建表
db_manager.create_tables()
print('✓ 数据库表创建成功')
"

# 启动API服务器
echo ""
echo "=========================================="
echo "启动API服务器..."
echo "=========================================="
echo ""
echo "API地址: http://localhost:8001"
echo "API文档: http://localhost:8001/api/docs"
echo "ReDoc文档: http://localhost:8001/api/redoc"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

cd /c/Users/Penguin8n/CODEX--/CODEX--
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8001 --reload
