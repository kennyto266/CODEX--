#!/usr/bin/env python3
"""
港股量化交易 AI Agent 系统 - 自动安装脚本

这个脚本会自动检查环境、安装依赖、配置系统，让您可以快速开始使用。
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path


def print_banner():
    """打印欢迎横幅"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        🚀 港股量化交易 AI Agent 系统 自动安装程序              ║
║                                                              ║
║        7个专业AI Agent + 实时监控仪表板                      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)


def check_python_version():
    """检查Python版本"""
    print("🔍 检查Python版本...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"❌ Python版本过低: {version.major}.{version.minor}")
        print("   需要Python 3.9或更高版本")
        return False
    
    print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
    return True


def check_pip():
    """检查pip是否可用"""
    print("🔍 检查pip...")
    
    try:
        import pip
        print("✅ pip已安装")
        return True
    except ImportError:
        print("❌ pip未安装")
        return False


def install_requirements():
    """安装Python依赖"""
    print("📦 安装Python依赖包...")
    
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ requirements.txt文件不存在")
        return False
    
    try:
        # 升级pip
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        print("✅ pip已升级")
        
        # 安装依赖
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                               check=True, capture_output=True, text=True)
        print("✅ 依赖包安装完成")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖包安装失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False


def create_directories():
    """创建必要的目录"""
    print("📁 创建项目目录...")
    
    directories = [
        "logs",
        "data",
        "cache",
        "config"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ 创建目录: {directory}")


def create_env_file():
    """创建环境配置文件"""
    print("⚙️ 创建环境配置...")
    
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if env_file.exists():
        print("✅ .env文件已存在")
        return True
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ 从env.example创建.env文件")
        return True
    else:
        # 创建默认的.env文件
        default_env = """# 港股量化交易 AI Agent 系统配置文件

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# 数据库配置（可选）
DATABASE_URL=sqlite:///./data/hk_quant.db

# 系统配置
DEBUG=false
LOG_LEVEL=INFO
PORT=8000

# 交易配置
TRADING_ENABLED=false
MAX_POSITION_SIZE=0.1

# 风险控制
RISK_LIMIT=0.05
MAX_DAILY_LOSS=0.02

# 监控配置
ENABLE_MONITORING=true
ENABLE_ALERTS=true
"""
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(default_env)
        print("✅ 创建默认.env文件")
        return True


def check_redis():
    """检查Redis服务"""
    print("🔍 检查Redis服务...")
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        print("✅ Redis服务正在运行")
        return True
    except Exception as e:
        print("⚠️ Redis服务未运行或不可访问")
        print("   提示: 可以使用Docker启动Redis:")
        print("   docker run -d -p 6379:6379 redis:latest")
        return False


def run_tests():
    """运行基本测试"""
    print("🧪 运行基本测试...")
    
    try:
        # 测试导入
        sys.path.insert(0, str(Path.cwd()))
        
        # 测试核心模块
        from src.core import SystemConfig
        config = SystemConfig()
        print("✅ 核心模块测试通过")
        
        # 测试数据模型
        from src.models.agent_dashboard import AgentDashboardData
        print("✅ 数据模型测试通过")
        
        # 测试仪表板组件
        from src.dashboard.components import AgentCardComponent
        print("✅ 仪表板组件测试通过")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def print_next_steps():
    """打印后续步骤"""
    print("""
🎉 安装完成！接下来您可以：

1. 启动演示模式（推荐首次使用）:
   python start_dashboard.py demo

2. 启动完整仪表板:
   python start_dashboard.py dashboard

3. 查看使用指南:
   cat USAGE_GUIDE.md

4. 访问仪表板:
   http://localhost:8000

📚 更多信息:
   - 用户指南: USAGE_GUIDE.md
   - API文档: docs/api_reference.md
   - 开发指南: docs/developer_guide.md

💡 提示: 如果遇到问题，请查看日志文件 logs/dashboard.log
    """)


def main():
    """主安装流程"""
    print_banner()
    
    # 检查系统环境
    if not check_python_version():
        sys.exit(1)
    
    if not check_pip():
        sys.exit(1)
    
    # 安装依赖
    if not install_requirements():
        print("❌ 安装失败，请检查错误信息")
        sys.exit(1)
    
    # 创建目录和配置文件
    create_directories()
    create_env_file()
    
    # 检查Redis（可选）
    check_redis()
    
    # 运行测试
    if not run_tests():
        print("⚠️ 测试失败，但系统可能仍可运行")
    
    print_next_steps()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 安装被用户中断")
    except Exception as e:
        print(f"❌ 安装过程中发生错误: {e}")
        sys.exit(1)
