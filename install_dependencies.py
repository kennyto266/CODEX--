"""
安装港股AI代理系统所需的依赖包
"""

import subprocess
import sys

def install_package(package):
    """安装Python包"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {package} 安装失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始安装港股AI代理系统依赖...")
    print("="*50)
    
    # 必需的包列表
    required_packages = [
        "aiohttp",      # 异步HTTP客户端
        "pandas",       # 数据处理
        "numpy",        # 数值计算
        "openai",       # OpenAI API客户端
        "asyncio",      # 异步编程（Python内置）
    ]
    
    success_count = 0
    total_count = len(required_packages)
    
    for package in required_packages:
        print(f"📦 正在安装 {package}...")
        if install_package(package):
            success_count += 1
        print()
    
    print("="*50)
    print(f"安装完成: {success_count}/{total_count} 个包安装成功")
    
    if success_count == total_count:
        print("🎉 所有依赖安装成功！现在可以运行 hk_real_example.py 了")
    else:
        print("⚠️ 部分依赖安装失败，请手动安装失败的包")
    
    print("\n📝 使用方法:")
    print("python hk_real_example.py")

if __name__ == "__main__":
    main()
