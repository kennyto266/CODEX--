#!/usr/bin/env python3
"""
港股量化交易 AI Agent 系统 - 简单Web启动器

这个脚本会启动一个简化的Web仪表板，无需复杂配置。
"""

import os
import sys
import webbrowser
import time
from pathlib import Path

def check_dependencies():
    """检查依赖包"""
    try:
        import fastapi
        import uvicorn
        return True
    except ImportError:
        print("❌ 缺少必要的依赖包")
        print("请运行以下命令安装:")
        print("pip install fastapi uvicorn")
        return False

def start_web_dashboard():
    """启动Web仪表板"""
    if not check_dependencies():
        return False
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        🚀 港股量化交易 AI Agent 仪表板                       ║
║                                                              ║
║        简化Web版本 - 一键启动                                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    print("🌐 正在启动Web服务器...")
    print("📊 仪表板地址: http://localhost:8000")
    print("🔧 API状态: http://localhost:8000/api/status")
    print("")
    print("💡 提示:")
    print("   - 服务器启动后会自动打开浏览器")
    print("   - 按 Ctrl+C 停止服务")
    print("   - 如果浏览器没有自动打开，请手动访问 http://localhost:8000")
    print("=" * 60)
    
    # 延迟打开浏览器
    def open_browser():
        time.sleep(3)  # 等待服务器启动
        try:
            webbrowser.open('http://localhost:8000')
            print("✅ 浏览器已打开")
        except Exception as e:
            print(f"⚠️ 无法自动打开浏览器: {e}")
            print("请手动访问: http://localhost:8000")
    
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    try:
        # 启动Web服务器
        from simple_web_dashboard import main
        main()
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("请检查端口8000是否被占用")
        return False
    
    return True

def main():
    """主函数"""
    print("🚀 港股量化交易 AI Agent 系统 - Web启动器")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("""
使用方法:
  python start_web.py              # 启动Web仪表板
  python start_web.py --help       # 显示帮助信息

功能:
  ✅ 现代化Web界面
  ✅ 实时监控7个AI Agent
  ✅ 查看策略和绩效指标
  ✅ 远程控制Agent操作
  ✅ 无需复杂配置

访问地址:
  http://localhost:8000 - 主仪表板
  http://localhost:8000/api/status - 系统状态
  http://localhost:8000/api/agents - Agent数据
        """)
        return
    
    success = start_web_dashboard()
    
    if not success:
        print("\n❌ 启动失败")
        print("💡 解决方案:")
        print("   1. 安装依赖: pip install fastapi uvicorn")
        print("   2. 检查端口8000是否被占用")
        print("   3. 尝试运行演示模式: python demo.py")
        sys.exit(1)

if __name__ == "__main__":
    main()
