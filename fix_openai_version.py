"""
修复OpenAI版本兼容性问题
"""

import subprocess
import sys

def fix_openai_version():
    """修复OpenAI版本"""
    print("🔧 修复OpenAI版本兼容性问题...")
    
    try:
        # 卸载当前版本
        print("📦 卸载当前OpenAI版本...")
        subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "openai", "-y"])
        
        # 安装兼容版本
        print("📦 安装兼容的OpenAI版本...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "openai==0.28.1"])
        
        print("✅ OpenAI版本修复完成！")
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        return False

if __name__ == "__main__":
    fix_openai_version()
