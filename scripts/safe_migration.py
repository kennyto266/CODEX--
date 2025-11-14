#!/usr/bin/env python3
"""
安全執行架構遷移
Safe Architecture Migration Executor
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime

class SafeArchitectureMigration:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.src_dir = self.project_root / "src"
        self.migration_log = []
        self.start_time = datetime.now()
        self.success_count = 0
        self.fail_count = 0

    def log(self, message, level="INFO"):
        """記錄日誌"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.migration_log.append(log_entry)
        print(log_entry)

    def create_directory_structure(self):
        """創建新的目錄結構"""
        self.log("\n" + "="*80)
        self.log("Step 1: 創建新的目錄結構")
        self.log("="*80)

        # 創建5層架構目錄
        directories = [
            "ui/dashboard",
            "ui/telegram_bot",
            "application/services",
            "application/use_cases",
            "application/use_cases/analysis",
            "domain/trading",
            "domain/portfolio",
            "domain/strategy",
            "domain/strategy/services",
            "domain/risk",
            "infrastructure/data_access/adapters",
            "infrastructure/data_access/repositories",
            "infrastructure/security",
            "infrastructure/security/privacy",
            "infrastructure/performance",
            "infrastructure/monitoring",
            "infrastructure/external_apis",
            "infrastructure/messaging",
            "shared/entities",
            "shared/utils",
            "shared/validators",
            "shared/indicators",
        ]

        for dir_path in directories:
            full_path = self.src_dir / dir_path
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                self.log(f"✓ 創建目錄: {dir_path}")
            except Exception as e:
                self.log(f"❌ 創建失敗: {dir_path} - {e}", "ERROR")

    def migrate_directory(self, old_path, new_path, description=""):
        """遷移目錄（移動文件而不是整個目錄）"""
        old_dir = self.src_dir / old_path
        new_dir = self.src_dir / new_path

        if not old_dir.exists():
            self.log(f"⚠️  跳過 (不存在): {old_path}", "SKIP")
            return False

        if not old_dir.is_dir():
            self.log(f"⚠️  跳過 (不是目錄): {old_path}", "SKIP")
            return False

        # 檢查目標目錄是否為空
        if new_dir.exists() and any(new_dir.iterdir()):
            self.log(f"⚠️  跳過 (已存在且非空): {new_path}", "SKIP")
            return False

        try:
            self.log(f"\n遷移: {old_path} -> {new_path}")
            if description:
                self.log(f"  說明: {description}")

            # 移動目錄
            shutil.move(str(old_dir), str(new_dir))
            self.success_count += 1
            self.log(f"  ✅ 成功")
            return True
        except Exception as e:
            self.fail_count += 1
            self.log(f"  ❌ 失敗: {e}", "ERROR")
            return False

    def create_init_files(self):
        """創建__init__.py文件"""
        self.log("\n" + "="*80)
        self.log("Step 3: 創建__init__.py文件")
        self.log("="*80)

        init_dirs = [
            "ui", "ui/dashboard", "ui/telegram_bot",
            "application", "application/services", "application/use_cases", "application/use_cases/analysis",
            "domain", "domain/trading", "domain/portfolio", "domain/strategy", "domain/strategy/services", "domain/risk",
            "infrastructure", "infrastructure/data_access", "infrastructure/data_access/adapters",
            "infrastructure/data_access/repositories", "infrastructure/security", "infrastructure/security/privacy",
            "infrastructure/performance", "infrastructure/monitoring", "infrastructure/external_apis", "infrastructure/messaging",
            "shared", "shared/entities", "shared/utils", "shared/validators", "shared/indicators"
        ]

        for dir_path in init_dirs:
            init_file = self.src_dir / dir_path / "__init__.py"
            try:
                init_file.touch()
                self.log(f"✓ 創建: {dir_path}/__init__.py")
            except Exception as e:
                self.log(f"❌ 失敗: {dir_path}/__init__.py - {e}", "ERROR")

    def test_basic_import(self):
        """測試基本導入"""
        self.log("\n" + "="*80)
        self.log("Step 4: 測試基本導入")
        self.log("="*80)

        try:
            import sys
            sys.path.insert(0, str(self.project_root))
            import src
            self.log("✅ src 模組導入成功")
            return True
        except Exception as e:
            self.log(f"❌ src 模組導入失敗: {e}", "ERROR")
            return False

    def generate_report(self):
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
成功遷移: {self.success_count} 個目錄
失敗遷移: {self.fail_count} 個目錄

📁 新架構目錄結構:
src/
├── ui/              (用戶界面)
│   ├── dashboard/
│   └── telegram_bot/
├── application/     (應用服務)
│   ├── services/
│   └── use_cases/
│       └── analysis/
├── domain/          (業務邏輯)
│   ├── trading/
│   ├── portfolio/
│   ├── strategy/
│   │   └── services/
│   └── risk/
├── infrastructure/  (基礎設施)
│   ├── data_access/
│   │   ├── adapters/
│   │   └── repositories/
│   ├── security/
│   │   └── privacy/
│   ├── performance/
│   ├── monitoring/
│   ├── external_apis/
│   └── messaging/
└── shared/          (共享組件)
    ├── entities/
    ├── utils/
    ├── validators/
    └── indicators/

📋 下一步操作:
1. ✅ 創建新架構目錄
2. ✅ 遷移源碼模組
3. ✅ 創建__init__.py文件
4. ⏳ 更新導入路徑 (import statements)
5. ⏳ 運行完整測試
6. ⏳ 更新配置文件
7. ⏳ 更新文檔

⚠️ 注意事項:
- 遷移已完成，請檢查功能是否正常
- 如果有導入錯誤，需要更新Python文件的import語句
- 運行測試確保系統穩定
- 遇問題可從備份恢復
"""

        self.log(report)

        # 保存報告
        report_file = self.project_root / "safe_migration_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
            f.write("\n\n## 遷移日誌\n\n")
            f.write("\n".join(self.migration_log))

        self.log(f"\n報告已保存到: {report_file}")

    def run_migration(self):
        """執行完整遷移流程"""
        print("\n")
        print("╔" + "=" * 78 + "╗")
        print("║" + " " * 18 + "安全執行架構遷移" + " " * 27 + "║")
        print("║" + " " * 15 + "Safe Architecture Migration" + " " * 22 + "║")
        print("╚" + "=" * 78 + "╝")
        print("\n")

        # Step 1: 創建目錄結構
        self.create_directory_structure()

        # Step 2: 遷移目錄
        self.log("\n" + "="*80)
        self.log("Step 2: 遷移源碼模組")
        self.log("="*80)

        migrations = [
            ("dashboard", "ui/dashboard", "Web儀表板"),
            ("data_adapters", "infrastructure/data_access/adapters", "數據適配器"),
            ("trading", "domain/trading", "交易域"),
            ("risk", "domain/risk", "風險管理"),
            ("security", "infrastructure/security", "安全"),
            ("utils", "shared/utils", "工具"),
        ]

        for old, new, desc in migrations:
            self.migrate_directory(old, new, desc)

        # Step 3: 創建__init__.py文件
        self.create_init_files()

        # Step 4: 測試
        self.test_basic_import()

        # Step 5: 生成報告
        self.generate_report()

if __name__ == "__main__":
    migration = SafeArchitectureMigration()
    migration.run_migration()
