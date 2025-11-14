#!/usr/bin/env python3
"""
項目架構重構腳本
Project Architecture Refactor Script
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

class ArchitectureRefactor:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.src_dir = self.project_root / "src"
        self.refactor_log = []
        self.start_time = datetime.now()

    def log(self, message, level="INFO"):
        """記錄日誌"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.refactor_log.append(log_entry)
        print(log_entry)

    def create_backup(self):
        """創建備份"""
        self.log("=" * 80)
        self.log("創建架構重構備份")
        self.log("=" * 80)

        backup_dir = self.project_root / "archive" / "refactor_backup"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # 備份src目錄
        src_backup = backup_dir / "src_backup"
        if self.src_dir.exists():
            self.log(f"備份 src/ 到 {src_backup}")
            if src_backup.exists():
                shutil.rmtree(src_backup)
            shutil.copytree(self.src_dir, src_backup)

        # 備份配置文件
        config_files = [
            "requirements.txt",
            "pyproject.toml",
            "pytest.ini",
            ".gitignore"
        ]
        for file in config_files:
            file_path = self.project_root / file
            if file_path.exists():
                self.log(f"備份 {file}")
                shutil.copy2(file_path, backup_dir / file)

        self.log("備份完成")
        self.log("")

    def create_git_branch(self):
        """創建Git分支"""
        self.log("創建 Git 分支 'architecture-refactor'")
        os.system("git checkout -b architecture-refactor > /dev/null 2>&1")
        self.log("Git 分支創建完成")
        self.log("")

    def create_new_structure(self):
        """創建新的目錄結構"""
        self.log("=" * 80)
        self.log("創建新的項目架構")
        self.log("=" * 80)

        # 源碼目錄結構
        src_structure = {
            "ui": {
                "dashboard": ["api", "static", "templates", "websocket"],
                "telegram_bot": ["local"],
                "cli": []
            },
            "application": {
                "services": [],
                "use_cases": [],
                "facades": [],
                "handlers": []
            },
            "domain": {
                "market": ["entities", "repositories", "services", "events"],
                "trading": ["entities", "repositories", "services", "events"],
                "portfolio": ["entities", "repositories", "services"],
                "risk": ["entities", "repositories", "services"],
                "strategy": ["entities", "repositories", "services"]
            },
            "infrastructure": {
                "data_access": ["adapters", "cache", "repositories"],
                "external_apis": ["alpha_vantage", "hkma", "yahoo", "futu"],
                "messaging": [],
                "logging": [],
                "security": ["privacy"],
                "performance": [],
                "monitoring": []
            },
            "shared": {
                "entities": [],
                "value_objects": [],
                "exceptions": [],
                "utils": [],
                "constants": [],
                "decorators": []
            }
        }

        # 數據目錄結構
        data_structure = {
            "raw": {
                "market": ["hkex", "us"],
                "economic": ["hkma", "census", "property"],
                "external": ["alpha_vantage", "yahoo"]
            },
            "processed": {
                "market": [],
                "economic": [],
                "indicators": [],
                "optimization": [],
                "results": []
            },
            "cache": {
                "market_cache": [],
                "api_cache": [],
                "temp": []
            },
            "datasets": {
                "training": [],
                "validation": [],
                "test": []
            }
        }

        # 創建src目錄
        self.log("創建源碼目錄結構...")
        for module, submodules in src_structure.items():
            module_path = self.src_dir / module
            module_path.mkdir(exist_ok=True)
            for submod, subdirs in submodules.items():
                submod_path = module_path / submod
                submod_path.mkdir(exist_ok=True)
                for subdir in subdirs:
                    subdir_path = submod_path / subdir
                    subdir_path.mkdir(exist_ok=True)
            self.log(f"✓ 創建 {module}/")

        # 創建data目錄
        self.log("創建數據目錄結構...")
        data_dir = self.project_root / "data"
        for category, subcategories in data_structure.items():
            category_path = data_dir / category
            category_path.mkdir(exist_ok=True)
            for subcat, subdirs in subcategories.items():
                subcat_path = category_path / subcat
                subcat_path.mkdir(exist_ok=True)
                for subdir in subdirs:
                    subdir_path = subcat_path / subdir
                    subdir_path.mkdir(exist_ok=True)
            self.log(f"✓ 創建 data/{category}/")

        # 創建其他目錄
        other_dirs = {
            "scripts": ["deployment", "data_collection", "maintenance", "development", "backtest", "utils"],
            "tests": ["unit", "integration", "e2e", "performance", "security", "fixtures", "helpers"],
            "docs": ["api", "user_guide", "developer_guide", "architecture"],
            "config": ["development", "production", "testing"],
            "assets": ["images", "styles", "templates", "debug"],
            "build": ["debug", "release"],
            "tools": ["analysis", "migration", "monitoring"]
        }

        for parent, subdirs in other_dirs.items():
            parent_path = self.project_root / parent
            for subdir in subdirs:
                subdir_path = parent_path / subdir
                subdir_path.mkdir(parents=True, exist_ok=True)

        self.log("目錄結構創建完成")
        self.log("")

    def analyze_current_structure(self):
        """分析當前結構"""
        self.log("=" * 80)
        self.log("分析當前項目結構")
        self.log("=" * 80)

        analysis = {
            "src_dirs": [],
            "data_files": [],
            "scripts": [],
            "tests": []
        }

        # 分析src目錄
        for item in self.src_dir.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                analysis["src_dirs"].append({
                    "name": item.name,
                    "path": item,
                    "size": sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                })

        # 分析data目錄
        data_dir = self.project_root / "data"
        for item in data_dir.rglob('*'):
            if item.is_file():
                analysis["data_files"].append({
                    "name": item.name,
                    "path": item,
                    "size": item.stat().st_size
                })

        # 統計信息
        self.log(f"源碼目錄數量: {len(analysis['src_dirs'])}")
        self.log(f"數據文件數量: {len(analysis['data_files'])}")
        self.log("")

        return analysis

    def generate_migration_map(self):
        """生成遷移映射表"""
        self.log("=" * 80)
        self.log("生成遷移映射表")
        self.log("=" * 80)

        migration_map = {
            "src": {
                "dashboard": "ui/dashboard",
                "telegram_bot": "ui/telegram_bot",
                "telegram_local": "ui/telegram_bot/local",
                "api": "application/services",
                "analysis": "application/use_cases",
                "trading": "domain/trading",
                "portfolio": "domain/portfolio",
                "strategies": "domain/strategy",
                "strategy": "domain/strategy/services",
                "risk": "domain/risk",
                "risk_management": "domain/risk",
                "data_adapters": "infrastructure/data_access/adapters",
                "database": "infrastructure/data_access/repositories",
                "db": "infrastructure/data_access",
                "encryption": "infrastructure/security",
                "security": "infrastructure/security",
                "privacy": "infrastructure/security/privacy",
                "performance": "infrastructure/performance",
                "observability": "infrastructure/monitoring",
                "monitoring": "infrastructure/monitoring",
                "integration": "infrastructure/external_apis",
                "signals": "infrastructure/messaging",
                "data": "shared/entities",
                "utils": "shared/utils",
                "validators": "shared",
                "indicators": "shared"
            },
            "data": {
                "*.csv": "raw/market/hkex",
                "real_*.csv": "processed/economic",
                "real_gov_data": "raw/economic",
                "property": "raw/economic/property",
                "retail": "raw/economic",
                "tourism": "raw/economic",
                "cache": "cache",
                "optimization": "processed/optimization",
                "results": "processed/results",
                "temp": "cache/temp",
                "user_data": "user_data"
            }
        }

        self.log("遷移映射表:")
        for category, mappings in migration_map.items():
            self.log(f"  {category}:")
            for old, new in mappings.items():
                self.log(f"    {old} -> {new}")
        self.log("")

        return migration_map

    def generate_summary_report(self):
        """生成總結報告"""
        self.log("=" * 80)
        self.log("架構重構總結")
        self.log("=" * 80)

        end_time = datetime.now()
        duration = end_time - self.start_time

        report = f"""
架構重構準備完成

開始時間: {self.start_time.strftime("%Y-%m-%d %H:%M:%S")}
結束時間: {end_time.strftime("%Y-%m-%d %H:%M:%S")}
執行時長: {duration}

✅ 已完成的操作:
1. 創建Git分支 'architecture-refactor'
2. 備份所有關鍵文件到 archive/refactor_backup/
3. 創建新的目錄結構
4. 生成遷移映射表
5. 分析當前項目結構

📁 新目錄結構:
src/
├── ui/              (用戶界面)
├── application/     (應用服務)
├── domain/          (業務邏輯)
├── infrastructure/  (基礎設施)
└── shared/          (共享組件)

data/
├── raw/             (原始數據)
├── processed/       (處理後數據)
├── cache/           (緩存)
└── datasets/        (數據集)

scripts/
├── deployment/      (部署)
├── data_collection/ (數據收集)
├── maintenance/     (維護)
└── development/     (開發)

tests/
├── unit/            (單元測試)
├── integration/     (集成測試)
├── e2e/            (端到端)
└── performance/     (性能測試)

📋 下一步操作:
1. 開始遷移源碼模組 (按遷移映射表)
2. 更新導入路徑
3. 運行測試驗證
4. 更新文檔

⚠️ 注意事項:
- 當前僅完成結構創建，未遷移文件
- 請按照遷移映射表逐步移動文件
- 每步操作後請測試功能
- 遇到問題可回滾到備份

📞 如需幫助:
查看 PROJECT_ARCHITECTURE_CLASSIFICATION.md 獲取詳細方案
"""

        self.log(report)

        # 保存報告到文件
        report_file = self.project_root / "architecture_refactor_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
            f.write("\n\n## 執行日誌\n\n")
            f.write("\n".join(self.refactor_log))

        self.log(f"報告已保存到: {report_file}")
        self.log("")
        self.log("=" * 80)

    def run(self):
        """執行架構重構準備"""
        try:
            print("\n")
            print("╔" + "=" * 78 + "╗")
            print("║" + " " * 20 + "項目架構重構腳本" + " " * 26 + "║")
            print("║" + " " * 15 + "Project Architecture Refactor" + " " * 22 + "║")
            print("╚" + "=" * 78 + "╝")
            print("\n")

            self.create_git_branch()
            self.create_backup()
            self.create_new_structure()
            self.analyze_current_structure()
            self.generate_migration_map()
            self.generate_summary_report()

            print("\n✅ 架構重構準備完成！")
            print("📖 查看 'architecture_refactor_report.md' 了解詳情")
            print("📚 參考 'PROJECT_ARCHITECTURE_CLASSIFICATION.md' 獲取完整方案")
            print("\n")

        except Exception as e:
            self.log(f"錯誤: {e}", "ERROR")
            raise

if __name__ == "__main__":
    import sys

    refactor = ArchitectureRefactor()
    refactor.run()
