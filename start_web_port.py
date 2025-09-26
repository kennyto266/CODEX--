#!/usr/bin/env python3
"""
港股量化交易 AI Agent 系统 - 多端口Web启动器

这个脚本会自动检测可用端口并启动Web仪表板。
"""

import os
import sys
import webbrowser
import time
import socket
from pathlib import Path

def find_free_port(start_port=8000, max_port=8010):
    """查找可用端口"""
    for port in range(start_port, max_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return None

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

def start_web_dashboard_on_port(port):
    """在指定端口启动Web仪表板"""
    if not check_dependencies():
        return False
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        🚀 港股量化交易 AI Agent 仪表板                       ║
║                                                              ║
║        简化Web版本 - 端口 {port}                              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    print(f"🌐 正在启动Web服务器 (端口 {port})...")
    print(f"📊 仪表板地址: http://localhost:{port}")
    print(f"🔧 API状态: http://localhost:{port}/api/status")
    print("")
    print("💡 提示:")
    print("   - 服务器启动后会自动打开浏览器")
    print("   - 按 Ctrl+C 停止服务")
    print(f"   - 如果浏览器没有自动打开，请手动访问 http://localhost:{port}")
    print("=" * 60)
    
    # 延迟打开浏览器
    def open_browser():
        time.sleep(3)  # 等待服务器启动
        try:
            webbrowser.open(f'http://localhost:{port}')
            print("✅ 浏览器已打开")
        except Exception as e:
            print(f"⚠️ 无法自动打开浏览器: {e}")
            print(f"请手动访问: http://localhost:{port}")
    
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    try:
        # 启动Web服务器
        import uvicorn
        from simple_web_dashboard import app
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("🚀 港股量化交易 AI Agent 系统 - 智能端口启动器")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("""
使用方法:
  python start_web_port.py              # 自动检测端口并启动
  python start_web_port.py 8080         # 指定端口启动
  python start_web_port.py --help       # 显示帮助信息

功能:
  ✅ 自动检测可用端口
  ✅ 避免端口冲突
  ✅ 现代化Web界面
  ✅ 实时监控7个AI Agent
  ✅ 自动打开浏览器

端口范围: 8000-8010 (自动检测)
        """)
        return
    
    # 获取端口
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("❌ 无效的端口号")
            return
    else:
        port = find_free_port()
        if port is None:
            print("❌ 无法找到可用端口 (8000-8010)")
            print("💡 请手动指定端口: python start_web_port.py 8080")
            return
    
    print(f"🔍 使用端口: {port}")
    
    success = start_web_dashboard_on_port(port)
    
    if not success:
        print("\n❌ 启动失败")
        print("💡 解决方案:")
        print("   1. 安装依赖: pip install fastapi uvicorn")
        print("   2. 尝试不同端口: python start_web_port.py 8080")
        print("   3. 使用演示模式: python demo.py")
        sys.exit(1)

if __name__ == "__main__":
    main()
