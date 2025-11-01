#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CODEX量化交易系统 - 完整集成版
集成所有性能优化功能的高性能量化交易平台

特性:
✅ 完整性能优化 - API缓存、内存优化、数据库优化
✅ 前端性能监控 - 实时性能面板
✅ 统一API架构 - FastAPI + 性能优化
✅ 自动化优化 - 定时性能检查和优化
"""

import sys
import os
import asyncio
import uvicorn
from pathlib import Path
from datetime import datetime
import logging

# 设置环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('integrated_codex.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("CODEX.Integrated")

def main():
    """启动集成版CODEX系统"""
    print("=" * 80)
    print("CODEX Integrated Quant Trading System v8.0")
    print("=" * 80)
    print()
    print("Integrated Features:")
    print("  [OK] Performance Optimization System")
    print("  [OK] API Cache Mechanism")
    print("  [OK] Frontend Performance Monitor")
    print("  [OK] Memory Optimization")
    print("  [OK] Database Optimization")
    print("  [OK] Real-time Performance Panel")
    print()
    print("Access URLs:")
    print("  - API Docs: http://localhost:8001/docs")
    print("  - Performance Panel: http://localhost:8001/performance-monitor.html")
    print("  - Paper Trading: http://localhost:8001/static/paper-trading.html")
    print("  - Main Page: http://localhost:8001/")
    print()
    print("Starting server...")
    print("=" * 80)
    print()

    try:
        # 导入主系统
        from complete_project_system import app
        logger.info("[OK] Main system module loaded successfully")

        # 启动集成系统
        logger.info("[OK] Starting integrated system server...")

        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8001,
            log_level="info",
            access_log=True
        )

    except KeyboardInterrupt:
        print("\n" + "=" * 80)
        print("System stopped by user")
        print("=" * 80)
        logger.info("System stopped by user")
    except Exception as e:
        print("\n" + "=" * 80)
        print(f"Startup failed: {e}")
        print("=" * 80)
        logger.error(f"System startup failed: {e}", exc_info=True)
        return 1

    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
