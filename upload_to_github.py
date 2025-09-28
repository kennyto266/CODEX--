"""
自动上传项目到GitHub的脚本
"""

import subprocess
import sys
import os
from datetime import datetime

def run_command(command, description):
    """运行命令并显示结果"""
    print(f"🔧 {description}...")
    print(f"📝 执行命令: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print(f"✅ {description} 成功")
            if result.stdout:
                print(f"📊 输出: {result.stdout}")
        else:
            print(f"❌ {description} 失败")
            print(f"📊 错误: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ {description} 出错: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("🚀 自动上传项目到GitHub")
    print("="*50)
    
    # 检查是否在Git仓库中
    if not os.path.exists('.git'):
        print("❌ 当前目录不是Git仓库")
        print("💡 请先运行: git init")
        return
    
    # 步骤1: 检查Git状态
    print("🔍 步骤1: 检查Git状态")
    if not run_command("git status", "检查Git状态"):
        return
    
    print()
    
    # 步骤2: 添加所有文件
    print("🔍 步骤2: 添加所有文件")
    if not run_command("git add .", "添加所有文件"):
        return
    
    print()
    
    # 步骤3: 提交更改
    print("🔍 步骤3: 提交更改")
    commit_message = f"""港股AI代理量化交易系统 - 7个专业代理协作

- 添加7个专业AI代理：基本面、技术、情绪、新闻、研究辩论、交易、风险管理
- 集成真实股票数据API
- 支持Cursor API集成
- 添加完整的文档和示例
- 优化系统性能和稳定性
- 上传时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
    
    if not run_command(f'git commit -m "{commit_message}"', "提交更改"):
        return
    
    print()
    
    # 步骤4: 推送到GitHub
    print("🔍 步骤4: 推送到GitHub")
    if not run_command("git push origin main", "推送到GitHub"):
        return
    
    print()
    print("🎉 项目上传成功！")
    print("📊 你现在可以:")
    print("  1. 在GitHub上查看你的代码")
    print("  2. 安装Cursor GitHub App")
    print("  3. 启动7个AI代理的真实系统")
    print()
    print("🔗 GitHub仓库: https://github.com/kennyto266/CODEX--")
    print("🔗 Cursor GitHub App: https://cursor.com/api/auth/connect-github")

if __name__ == "__main__":
    main()
