#!/usr/bin/env python3
"""
更新導入路徑以匹配新架構
Update Import Paths to Match New Architecture
"""

import os
import re
from pathlib import Path
from datetime import datetime

class ImportPathUpdater:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.src_dir = self.project_root / "src"
        self.updates = []
        self.files_updated = 0

        # 導入路徑映射表 (舊路徑 -> 新路徑)
        self.path_mappings = {
            # API 路徑
            "from src.api.routes": "from src.application.services.api.routes",
            "from src.api.middleware": "from src.application.services.api.middleware",
            "from src.api.logging": "from src.application.services.api.logging",
            "from src.api.websocket": "from src.application.services.api.websocket",
            "from src.api.dependencies": "from src.application.services.api.dependencies",
            "from src.api.server": "from src.application.services.api.server",
            "from src.api import": "from src.application.services.api import",

            # Data Adapters
            "from src.data_adapters": "from src.infrastructure.data_access.adapters",
            "from src.data_adapters.": "from src.infrastructure.data_access.adapters.",

            # Database / Repositories
            "from src.database": "from src.infrastructure.data_access.repositories",
            "from src.database.": "from src.infrastructure.data_access.repositories.",

            # Performance / Monitoring
            "from src.performance": "from src.infrastructure.performance",
            "from src.performance.": "from src.infrastructure.performance.",
            "from src.observability": "from src.infrastructure.monitoring",
            "from src.observability.": "from src.infrastructure.monitoring.",

            # Security
            "from src.security": "from src.infrastructure.security",
            "from src.security.": "from src.infrastructure.security.",

            # Messaging
            "from src.signals": "from src.infrastructure.messaging",
            "from src.signals.": "from src.infrastructure.messaging.",

            # External APIs
            "from src.integration": "from src.infrastructure.external_apis",
            "from src.integration.": "from src.infrastructure.external_apis.",

            # Core / Shared
            "from src.core": "from src.shared.entities",
            "from src.utils": "from src.shared.utils",
            "from src.validators": "from src.shared.validators",
            "from src.indicators": "from src.shared.indicators",

            # Domain層
            "from src.strategies": "from src.domain.strategy",
            "from src.strategy": "from src.domain.strategy.services",
            "from src.portfolio": "from src.domain.portfolio",
        }

    def log(self, message):
        """記錄日誌"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")

    def backup_file(self, file_path):
        """備份文件"""
        backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            with open(file_path, 'r', encoding='utf-8') as src:
                with open(backup_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            self.log(f"✓ 備份文件: {backup_path}")
            return True
        except Exception as e:
            self.log(f"❌ 備份失敗 {file_path}: {e}")
            return False

    def update_file_imports(self, file_path):
        """更新單個文件的導入"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            updates_made = []

            # 應用所有映射
            for old_path, new_path in self.path_mappings.items():
                if old_path in content:
                    content = content.replace(old_path, new_path)
                    updates_made.append(f"{old_path} -> {new_path}")

            if content != original_content:
                self.backup_file(file_path)

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                self.log(f"✓ 更新: {file_path}")
                for update in updates_made:
                    self.log(f"  - {update}")

                self.files_updated += 1
                return True
            return False

        except Exception as e:
            self.log(f"❌ 更新失敗 {file_path}: {e}")
            return False

    def scan_and_update(self):
        """掃描並更新所有Python文件"""
        self.log("\n" + "="*80)
        self.log("開始掃描和更新導入路徑")
        self.log("="*80 + "\n")

        python_files = list(self.src_dir.rglob("*.py"))
        self.log(f"找到 {len(python_files)} 個Python文件\n")

        for i, file_path in enumerate(python_files, 1):
            # 跳過備份文件
            if "backup_" in str(file_path):
                continue

            self.log(f"[{i}/{len(python_files)}] 檢查: {file_path.relative_to(self.src_dir)}")

            if self.update_file_imports(file_path):
                pass  # 已在update_file_imports中記錄

        self.log("\n" + "="*80)
        self.log(f"更新完成: {self.files_updated} 個文件已更新")
        self.log("="*80 + "\n")

    def generate_report(self):
        """生成更新報告"""
        report = f"""
導入路徑更新報告
Update Import Paths Report

生成時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

✅ 更新統計:
- 更新的文件數: {self.files_updated} 個
- 應用的映射規則: {len(self.path_mappings)} 個

📋 應用的映射規則:
{chr(10).join([f"  • {old} -> {new}" for old, new in self.path_mappings.items()])}

⚠️ 注意事項:
- 所有原始文件已備份 (backup_YYYYMMDD_HHMMSS後綴)
- 請運行測試驗證更新結果
- 如有問題可以從備份恢復

🔍 下一步:
1. 運行測試驗證更新結果
2. 檢查是否有遺漏的導入路徑
3. 更新測試文件中的導入路徑

📞 恢復方法:
如需恢復，請從備份文件複製內容
"""

        report_file = self.project_root / "import_path_update_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        self.log(f"\n報告已保存到: {report_file}")
        print(report)

if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "更新導入路徑工具" + " " * 28 + "║")
    print("║" + " " * 15 + "Update Import Paths Tool" + " " * 26 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")

    updater = ImportPathUpdater()
    updater.scan_and_update()
    updater.generate_report()
