#!/usr/bin/env python3
"""
港股量化交易 AI Agent 系统 - 仪表板快速访问

这个脚本会帮您快速访问Web仪表板。
"""

import webbrowser
import requests
import time

def check_ports():
    """检查可用端口"""
    ports = [8000, 8001, 8002, 8080, 8081]
    available_ports = []
    
    for port in ports:
        try:
            response = requests.get(f"http://localhost:{port}/api/status", timeout=2)
            if response.status_code == 200:
                available_ports.append(port)
        except:
            continue
    
    return available_ports

def open_dashboard():
    """打开仪表板"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        🚀 港股量化交易 AI Agent 仪表板访问器                  ║
║                                                              ║
║        快速访问Web界面                                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    print("🔍 正在检测可用的仪表板...")
    
    available_ports = check_ports()
    
    if not available_ports:
        print("❌ 没有检测到运行中的仪表板")
        print("")
        print("💡 请先启动仪表板:")
        print("   python demo.py                    # 演示模式")
        print("   python start_web_port.py 8001     # Web模式")
        print("   python simple_web_dashboard.py    # 简单模式")
        return False
    
    print(f"✅ 检测到 {len(available_ports)} 个可用的仪表板:")
    
    for i, port in enumerate(available_ports, 1):
        try:
            response = requests.get(f"http://localhost:{port}/api/status", timeout=2)
            data = response.json()
            print(f"   {i}. http://localhost:{port} - {data.get('active_agents', '?')}个活跃Agent")
        except:
            print(f"   {i}. http://localhost:{port} - 状态未知")
    
    print("")
    
    # 自动打开第一个可用的仪表板
    if available_ports:
        port = available_ports[0]
        url = f"http://localhost:{port}"
        
        print(f"🌐 正在打开仪表板: {url}")
        
        try:
            webbrowser.open(url)
            print("✅ 浏览器已打开")
            print("")
            print("📊 仪表板功能:")
            print("   - 实时监控7个AI Agent状态")
            print("   - 查看策略信息和绩效指标")
            print("   - 远程控制Agent操作")
            print("   - 夏普比率和风险分析")
            print("")
            print("🔧 其他可用地址:")
            for port in available_ports:
                print(f"   http://localhost:{port}")
            
            return True
            
        except Exception as e:
            print(f"❌ 无法自动打开浏览器: {e}")
            print(f"请手动访问: {url}")
            return False
    
    return False

def main():
    """主函数"""
    try:
        open_dashboard()
    except KeyboardInterrupt:
        print("\n👋 操作已取消")
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        print("💡 请尝试手动访问: http://localhost:8000 或 http://localhost:8001")

if __name__ == "__main__":
    main()
