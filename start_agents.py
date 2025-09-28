#!/usr/bin/env python3
"""
港股量化交易 AI Agent 系统 - 简化启动脚本
提供多种启动方式，无需复杂配置
"""

import sys
import os
import subprocess
import webbrowser
import time
import threading
from pathlib import Path

def print_banner():
    """打印启动横幅"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        港股量化交易 AI Agent 系统                            ║
║                                                              ║
║        简化启动脚本 - 多种运行方式                            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

def check_python():
    """检查Python版本"""
    try:
        import sys
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 9):
            print("❌ Python版本过低，需要Python 3.9+")
            return False
        print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
        return True
    except Exception as e:
        print(f"❌ Python检查失败: {e}")
        return False

def install_dependencies():
    """安装必要依赖"""
    print("📦 正在安装依赖包...")
    try:
        # 检查是否在虚拟环境中
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            print("✅ 检测到虚拟环境")
        else:
            print("⚠️  建议使用虚拟环境")
        
        # 安装基础依赖
        packages = ['fastapi', 'uvicorn']
        for package in packages:
            try:
                __import__(package)
                print(f"✅ {package} 已安装")
            except ImportError:
                print(f"📦 正在安装 {package}...")
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"✅ {package} 安装完成")
        
        return True
    except Exception as e:
        print(f"❌ 依赖安装失败: {e}")
        return False

def run_demo():
    """运行演示模式"""
    print("🎬 启动演示模式...")
    try:
        if os.path.exists('demo.py'):
            subprocess.run([sys.executable, 'demo.py'])
        else:
            print("❌ demo.py 文件不存在")
            return False
    except Exception as e:
        print(f"❌ 演示模式启动失败: {e}")
        return False

def run_web_dashboard():
    """运行Web仪表板"""
    print("🌐 启动Web仪表板...")
    try:
        # 检查修复后的文件
        if os.path.exists('simple_web_dashboard_fixed.py'):
            dashboard_file = 'simple_web_dashboard_fixed.py'
        elif os.path.exists('simple_web_dashboard.py'):
            dashboard_file = 'simple_web_dashboard.py'
        elif os.path.exists('start_web.py'):
            dashboard_file = 'start_web.py'
        else:
            print("❌ 找不到Web仪表板文件")
            return False
        
        print(f"📁 使用文件: {dashboard_file}")
        
        # 延迟打开浏览器
        def open_browser():
            time.sleep(3)
            try:
                webbrowser.open("http://localhost:8000")
                print("🌐 浏览器已打开: http://localhost:8000")
            except Exception as e:
                print(f"⚠️  无法自动打开浏览器: {e}")
                print("💡 请手动访问: http://localhost:8000")
        
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # 启动服务器
        subprocess.run([sys.executable, dashboard_file])
        return True
        
    except KeyboardInterrupt:
        print("\n👋 Web服务器已停止")
        return True
    except Exception as e:
        print(f"❌ Web仪表板启动失败: {e}")
        return False

def run_full_system():
    """运行完整系统"""
    print("🚀 启动完整系统...")
    try:
        if os.path.exists('start_dashboard.py'):
            subprocess.run([sys.executable, 'start_dashboard.py', 'dashboard'])
        else:
            print("❌ start_dashboard.py 文件不存在")
            return False
    except Exception as e:
        print(f"❌ 完整系统启动失败: {e}")
        return False

def show_menu():
    """显示菜单"""
    print("""
🎯 请选择运行模式:

1. 🎬 演示模式 (推荐新手)
   - 无需依赖，快速体验
   - 展示7个AI Agent功能

2. 🌐 Web仪表板 (推荐日常使用)
   - 现代化Web界面
   - 实时监控Agent状态
   - 远程控制功能

3. 🚀 完整系统 (生产环境)
   - 需要Redis服务
   - 所有功能完整运行

4. 📦 安装依赖
   - 安装必要的Python包

5. ❓ 帮助信息
   - 查看详细使用说明

0. 🚪 退出
    """)

def show_help():
    """显示帮助信息"""
    print("""
📚 港股量化交易 AI Agent 系统使用指南

🎯 三种运行模式:

1. 演示模式 (python demo.py)
   ✅ 无需任何配置
   ✅ 展示7个AI Agent功能
   ✅ 包含绩效分析和策略展示
   ✅ 适合快速体验系统

2. Web仪表板 (python start_web.py)
   ✅ 现代化Web界面 (http://localhost:8000)
   ✅ 实时监控Agent状态
   ✅ 远程控制功能
   ✅ 自动打开浏览器

3. 完整系统 (python start_dashboard.py dashboard)
   ✅ 所有功能完整运行
   ✅ 需要Redis服务
   ✅ 适合生产环境

🔧 环境要求:
   - Python 3.9+
   - 内存: 至少4GB RAM
   - 磁盘空间: 至少2GB

📊 Agent类型:
   1. 量化分析师 - 技术分析和策略研究
   2. 量化交易员 - 执行交易决策
   3. 投资组合经理 - 资产配置优化
   4. 风险分析师 - 风险控制和监控
   5. 数据科学家 - 数据分析和建模
   6. 研究分析师 - 市场研究和预测
   7. 量化工程师 - 系统维护和优化

🌐 访问地址:
   - 主仪表板: http://localhost:8000
   - API状态: http://localhost:8000/api/status
   - Agent详情: http://localhost:8000/agent/{agent_id}

💡 故障排除:
   - 如果端口8000被占用，尝试其他端口
   - 如果依赖安装失败，使用虚拟环境
   - 如果浏览器无法打开，手动访问地址
    """)

def main():
    """主函数"""
    print_banner()
    
    if not check_python():
        return
    
    while True:
        show_menu()
        
        try:
            choice = input("请输入选择 (0-5): ").strip()
            
            if choice == '0':
                print("👋 再见！")
                break
            elif choice == '1':
                run_demo()
            elif choice == '2':
                if install_dependencies():
                    run_web_dashboard()
            elif choice == '3':
                if install_dependencies():
                    run_full_system()
            elif choice == '4':
                install_dependencies()
            elif choice == '5':
                show_help()
            else:
                print("❌ 无效选择，请重新输入")
            
            if choice in ['1', '2', '3']:
                input("\n按回车键继续...")
                
        except KeyboardInterrupt:
            print("\n👋 程序已退出")
            break
        except Exception as e:
            print(f"❌ 发生错误: {e}")

if __name__ == "__main__":
    main()