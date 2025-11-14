#!/usr/bin/env python3
"""
執行架構遷移
Execute Architecture Migration
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

class ArchitectureMigration:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.src_dir = self.project_root / "src"
        self.migration_log = []
        self.start_time = datetime.now()
        self.migration_count = 0

    def log(self, message, level="INFO"):
        """記錄日誌"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.migration_log.append(log_entry)
        print(log_entry)

    def migrate_directory(self, old_path, new_path, description=""):
        """遷移目錄"""
        old_dir = self.src_dir / old_path
        new_dir = self.src_dir / new_path

        if not old_dir.exists():
            self.log(f"⚠️  跳過 (不存在): {old_path}", "SKIP")
            return False

        if new_dir.exists():
            self.log(f"⚠️  跳過 (已存在): {new_path}", "SKIP")
            return False

        try:
            self.log(f"遷移: {old_path} -> {new_path}")
            if description:
                self.log(f"  說明: {description}")
            shutil.move(str(old_dir), str(new_dir))
            self.migration_count += 1
            self.log(f"  ✅ 成功")
            return True
        except Exception as e:
            self.log(f"  ❌ 失敗: {e}", "ERROR")
            return False

    def test_basic_import(self):
        """測試基本導入"""
        self.log("\n" + "="*80)
        self.log("測試基本導入")
        self.log("="*80 + "\n")

        try:
            import sys
            sys.path.insert(0, str(self.project_root))
            import src
            self.log("✅ src 模組導入成功")
        except Exception as e:
            self.log(f"❌ src 模組導入失敗: {e}", "ERROR")

    def run_migration(self):
        """執行遷移"""
        print("\n")
        print("╔" + "=" * 78 + "╗")
        print("║" + " " * 20 + "執行架構遷移" + " " * 28 + "║")
        print("║" + " " * 15 + "Execute Architecture Migration" + " " * 22 + "║")
        print("╚" + "=" * 78 + "╝")
        print("\n")

        # 遷移映射表
        migrations = [
            # UI Layer
            ("dashboard", "ui/dashboard", "Web儀表板"),
            ("telegram_bot", "ui/telegram_bot", "Telegram機器人"),
            ("telegram_local", "ui/telegram_bot/local", "Telegram本地版"),

            # Application Layer
            ("api", "application/services", "API服務"),
            ("analysis", "application/use_cases", "分析用例"),

            # Domain Layer
            ("trading", "domain/trading", "交易域"),
            ("portfolio", "domain/portfolio", "投資組合域"),
            ("strategies", "domain/strategy", "策略域"),
            ("strategy", "domain/strategy/services", "策略服務"),
            ("risk", "domain/risk", "風險管理"),
            ("risk_management", "domain/risk", "風險管理"),

            # Infrastructure Layer
            ("data_adapters", "infrastructure/data_access/adapters", "數據適配器"),
            ("database", "infrastructure/data_access/repositories", "數據庫"),
            ("db", "infrastructure/data_access", "DB"),
            ("encryption", "infrastructure/security", "加密"),
            ("security", "infrastructure/security", "安全"),
            ("privacy", "infrastructure/security/privacy", "隱私"),
            ("performance", "infrastructure/performance", "性能"),
            ("observability", "infrastructure/monitoring", "監控"),
            ("monitoring", "infrastructure/monitoring", "監控"),
            ("integration", "infrastructure/external_apis", "集成"),
            ("signals", "infrastructure/messaging", "信號"),

            # Shared Layer
            ("data", "shared/entities", "共享實體"),
            ("utils", "shared/utils", "工具"),
            ("validators", "shared/validators", "驗證器"),
            ("indicators", "shared/indicators", "技術指標"),
        ]

        self.log("="*80)
        self.log("開始執行遷移")
        self.log("="*80 + "\n")

        success_count = 0
        for old, new, desc in migrations:
            if self.migrate_directory(old, new, desc):
                success_count += 1

        # 測試
        self.test_basic_import()

        # 生成報告
        self.generate_report(success_count)

    def generate_report(self, success_count):
        """生成遷移報告"""
        self.log("\n" + "="*80)
        self.log("遷移完成報告")
        self.log("="*80)

        end_time = datetime.now()
        duration = end_time - self.start_time

        report = f"""
架構遷移完成

開始時間: {self.start_time.strftime("%Y-%m-%d %H:%M:%S")}
結束時間: {end_time.strftime("%Y-%m-%d %H:%M:%S")}
執行時長: {duration}

✅ 遷移統計:
總遷移項: {len(self.migration_log)}
成功遷移: {success_count} 個目錄
失敗遷移: {len(self.migration_log) - success_count} 個目錄

📁 成功遷移的目錄:
{chr(10).join([log for log in self.migration_log if "✅ 成功" in log])}

⚠️ 跳過或失敗的目錄:
{chr(10).join([log for log in self.migration_log if "⚠️" in log or "❌" in log])}

📋 下一步操作:
1. 更新導入路徑 (import statements)
2. 運行完整測試
3. 更新配置文件
4. 更新文檔

⚠️ 注意事項:
- 部分目錄可能已存在，跳過了遷移
- 請檢查並手動處理失敗的遷移
- 運行測試確保功能正常
- 如有問題可從備份恢復

📞 如需幫助:
查看 architecture_refactor_report.md 獲取詳情
"""

        self.log(report)

        # 保存報告
        report_file = self.project_root / "migration_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
            f.write("\n\n## 遷移日誌\n\n")
            f.write("\n".join(self.migration_log))

        self.log(f"\n報告已保存到: {report_file}")
        self.log("\n" + "="*80)

if __name__ == "__main__":
    migration = ArchitectureMigration()
    migration.run_migration()
