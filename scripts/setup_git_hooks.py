#!/usr/bin/env python3
"""
Git Hook自動設置腳本
自動在Git倉庫中設置Hooks以支持任務自動化
"""

import os
import sys
import subprocess
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitHooksSetup:
    """Git Hook設置工具"""

    def __init__(self, repo_path: str = "."):
        """
        初始化

        Args:
            repo_path: Git倉庫路徑
        """
        self.repo_path = Path(repo_path).resolve()
        self.hooks_dir = self.repo_path / ".git" / "hooks"

    def setup_pre_commit_hook(self) -> bool:
        """設置pre-commit hook"""
        try:
            hook_content = self._generate_pre_commit_hook()
            hook_path = self.hooks_dir / "pre-commit"

            # 創建hooks目錄
            self.hooks_dir.mkdir(parents=True, exist_ok=True)

            # 寫入hook文件
            with open(hook_path, "w", encoding="utf-8") as f:
                f.write(hook_content)

            # 設置可執行權限
            os.chmod(hook_path, 0o755)

            logger.info(f"✅ Pre-commit hook 已設置: {hook_path}")

            # 添加commit-msg hook
            self.setup_commit_msg_hook()

            return True

        except Exception as e:
            logger.error(f"❌ 設置pre-commit hook失敗: {e}")
            return False

    def setup_commit_msg_hook(self) -> bool:
        """設置commit-msg hook"""
        try:
            hook_content = self._generate_commit_msg_hook()
            hook_path = self.hooks_dir / "commit-msg"

            with open(hook_path, "w", encoding="utf-8") as f:
                f.write(hook_content)

            os.chmod(hook_path, 0o755)

            logger.info(f"✅ Commit-msg hook 已設置: {hook_path}")
            return True

        except Exception as e:
            logger.error(f"❌ 設置commit-msg hook失敗: {e}")
            return False

    def _generate_pre_commit_hook(self) -> str:
        """生成pre-commit hook內容"""
        return """#!/bin/bash
# Git Pre-Commit Hook for CODEX Task Management
# 自動檢查提交信息格式

# 獲取commit message
commit_msg_file=$1
commit_msg=$(cat "$commit_msg_file")

# 檢查是否包含任務ID
if echo "$commit_msg" | grep -qE "TASK-[0-9]{3}"; then
    echo "✅ 檢測到任務ID"
else
    echo "⚠️  警告: 提交信息中未找到任務ID"
    echo "   建議格式: feat: TASK-001 your commit message"
fi

# 檢查提交信息格式
if echo "$commit_msg" | grep -qE "^(feat|fix|docs|style|perf|chore|test|refactor)\s*:"; then
    echo "✅ 使用標準提交格式"
else
    echo "⚠️  建議使用標準格式: feat: 或 fix: 等"
fi

# 檢查是否包含關閉關鍵字
if echo "$commit_msg" | grep -qE "(close|fix|resolve)"; then
    echo "ℹ️  檢測到關閉關鍵字，任務將自動標記為已完成"
fi

exit 0
"""

    def _generate_commit_msg_hook(self) -> str:
        """生成commit-msg hook內容"""
        return """#!/bin/bash
# Git Commit-Msg Hook for CODEX Task Management
# 處理提交信息並通知任務管理系統

commit_msg_file=$1
commit_msg=$(cat "$commit_msg_file")
commit_hash=$(git rev-parse HEAD)

echo "📋 Processing commit: ${commit_hash:0:8}"

# 提取任務ID
task_ids=$(echo "$commit_msg" | grep -oE "TASK-[0-9]{3}" | sort -u)

if [ -n "$task_ids" ]; then
    echo "📌 Found tasks: $task_ids"

    # TODO: 調用任務管理API
    # curl -X POST http://localhost:8001/api/v1/automation/commit/process \\
    #   -H "Content-Type: application/json" \\
    #   -d "{\"repo_path\": \"$PWD\", \"commit\": {...}}"
else
    echo "ℹ️  No task IDs found in commit message"
fi

exit 0
"""

    def setup_post_receive_hook(self) -> bool:
        """設置post-receive hook（用於bare倉庫）"""
        try:
            hook_content = self._generate_post_receive_hook()
            hook_path = self.hooks_dir / "post-receive"

            with open(hook_path, "w", encoding="utf-8") as f:
                f.write(hook_content)

            os.chmod(hook_path, 0o755)

            logger.info(f"✅ Post-receive hook 已設置: {hook_path}")
            return True

        except Exception as e:
            logger.error(f"❌ 設置post-receive hook失敗: {e}")
            return False

    def _generate_post_receive_hook(self) -> str:
        """生成post-receive hook內容"""
        return """#!/bin/bash
# Git Post-Receive Hook for CODEX Task Management
# 接收推送並通知任務管理系統

while read oldrev newrev refname; do
    echo "📨 Received push: ${oldrev:0:8} -> ${newrev:0:8}"

    # TODO: 調用Webhook API
    # curl -X POST http://localhost:8001/api/v1/automation/webhook/git \\
    #   -H "Content-Type: application/json" \\
    #   -d '{...}'
done

exit 0
"""

    def create_sample_commit(self) -> bool:
        """創建示例提交"""
        try:
            # 創建示例文件
            sample_file = self.repo_path / "TASK_EXAMPLE.md"
            sample_file.write_text("""# 任務自動化示例

## 提交格式示例

### 功能開發
```
feat: TASK-001 實現用戶認證功能
```

### Bug修復
```
fix: TASK-002 修復登錄頁面bug
```

### 關閉任務
```
feat: TASK-003 完成API設計
Closes TASK-003
```

### 測試
```
test: TASK-004 添加單元測試
```

## 自動化規則

1. 包含TASK-XXX的提交會自動更新任務狀態
2. 包含關閉關鍵字（close, fix, resolve）的提交會自動完成任務
3. 文檔提交會自動完成文檔任務
4. 測試提交會自動完成測試任務

更多信息請訪問：/tasks
""")

            # 提交示例文件
            subprocess.run(
                ["git", "add", "TASK_EXAMPLE.md"],
                cwd=self.repo_path,
                check=True
            )

            subprocess.run(
                ["git", "commit", "-m", "feat: TASK-000 添加任務自動化示例\n\nCloses TASK-000"],
                cwd=self.repo_path,
                check=True
            )

            logger.info("✅ 創建示例提交成功")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 創建示例提交失敗: {e}")
            return False

    def setup(self) -> bool:
        """執行完整的hook設置"""
        logger.info("🚀 開始設置Git Hook...")

        # 檢查是否為Git倉庫
        if not (self.repo_path / ".git").exists():
            logger.error(f"❌ {self.repo_path} 不是Git倉庫")
            return False

        # 設置hooks
        success = True
        success &= self.setup_pre_commit_hook()
        success &= self.setup_commit_msg_hook()

        # 創建示例
        if success:
            logger.info("📝 是否創建示例文件？(y/n)", end=" ")
            try:
                response = input().strip().lower()
                if response in ["y", "yes", "是"]:
                    self.create_sample_commit()
            except (EOFError, KeyboardInterrupt):
                pass

        if success:
            logger.info("✅ Git Hook設置完成！")
            logger.info("")
            logger.info("📚 使用指南:")
            logger.info("1. 提交信息格式: feat: TASK-001 your message")
            logger.info("2. 關閉任務: feat: TASK-002 complete feature\nCloses TASK-002")
            logger.info("3. 查看任務看板: 訪問 /tasks")
            logger.info("")
            logger.info("💡 提示: 查看 TASK_EXAMPLE.md 了解更多示例")
        else:
            logger.error("❌ Git Hook設置部分失敗，請檢查錯誤信息")

        return success


def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description="Git Hook自動設置工具")
    parser.add_argument(
        "repo_path",
        nargs="?",
        default=".",
        help="Git倉庫路徑（默認：當前目錄）"
    )

    args = parser.parse_args()

    setup = GitHooksSetup(args.repo_path)
    success = setup.setup()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
