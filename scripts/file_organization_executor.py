#!/usr/bin/env python3
"""
项目文件自动整理执行器
基于文件整理方案.md的自动化脚本

功能:
1. 创建新的目录结构
2. 清理冗余文件
3. 归档历史文件
4. 重命名重复文件
5. 验证整理结果
"""

import os
import sys
import json
import shutil
import tarfile
import re
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple

class FileOrganizer:
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "operations": [],
            "errors": [],
            "stats": {}
        }

    def log_operation(self, operation: str, status: str, details: str = ""):
        """记录操作日志"""
        entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "operation": operation,
            "status": status,
            "details": details
        }
        self.report["operations"].append(entry)
        print(f"[{entry['time']}] {operation}: {status} {details}")

    def get_directory_size(self, path: Path) -> int:
        """计算目录大小（字节）"""
        total = 0
        try:
            for entry in path.rglob('*'):
                if entry.is_file():
                    total += entry.stat().st_size
        except (PermissionError, OSError):
            pass
        return total

    def format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def check_space_before_after(self, label: str) -> Tuple[int, int]:
        """检查操作前后的空间变化"""
        before = self.get_directory_size(self.project_root)
        return before, before  # Placeholder - actual after will be calculated after operations

    def create_directory_structure(self):
        """阶段1: 创建新的目录结构"""
        self.log_operation("创建目录结构", "开始")

        directories = [
            "assets/debug",
            "assets/logs/system",
            "assets/logs/trading",
            "assets/logs/performance",
            "assets/temp",
            "data/real_data",
            "data/cache",
            "data/user_data",
            "config/optimization",
            "config/deployment",
            "config/api",
            "scripts/deployment",
            "scripts/data_collection",
            "scripts/maintenance",
            "tests/unit",
            "tests/integration",
            "tests/performance",
            "tests/security",
            "docs/api",
            "docs/user-guide",
            "docs/developer-guide",
            "docs/reports",
            "archive/historical",
            "archive/deprecated",
            "archive/backup",
            "build/debug",
            "build/release",
            "build/artifacts"
        ]

        created = 0
        for dir_path in directories:
            full_path = self.project_root / dir_path
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                created += 1
            except Exception as e:
                self.report["errors"].append(f"创建目录失败: {dir_path} - {str(e)}")

        self.log_operation("创建目录结构", "完成", f"创建了 {created} 个目录")
        return created > 0

    def backup_critical_files(self):
        """备份关键文件"""
        self.log_operation("备份关键文件", "开始")

        backup_dir = self.project_root / "archive/backup"
        backup_dir.mkdir(exist_ok=True)

        # 备份Git
        git_backup = backup_dir / "git-backup"
        if (self.project_root / ".git").exists():
            try:
                shutil.copytree(self.project_root / ".git", git_backup, dirs_exist_ok=True)
                self.log_operation("备份Git", "完成")
            except Exception as e:
                self.log_operation("备份Git", "失败", str(e))

        # 备份配置
        config_backup = backup_dir / "config-backup"
        config_backup.mkdir(exist_ok=True)
        try:
            for cfg_file in self.project_root.glob("config/*.yaml"):
                shutil.copy2(cfg_file, config_backup)
            self.log_operation("备份配置", "完成")
        except Exception as e:
            self.log_operation("备份配置", "失败", str(e))

    def clean_redundant_files(self):
        """阶段2: 清理冗余文件"""
        self.log_operation("清理冗余文件", "开始")

        total_saved = 0
        operations = [
            ("node_modules", "删除Node.js依赖", 2.1),
            ("venv", "删除Python虚拟环境", 0.7),
            (".venv*", "删除其他虚拟环境", 0.3),
            ("python3.10", "删除Python安装", 0.5)
        ]

        for pattern, description, estimated_gb in operations:
            if pattern == "node_modules":
                path = self.project_root / "node_modules"
            elif pattern == "venv":
                path = self.project_root / "venv"
            elif pattern == ".venv*":
                for p in self.project_root.glob(".venv*"):
                    if p.is_dir():
                        size = self.get_directory_size(p)
                        p.unlink()
                        total_saved += size
                        self.log_operation(description, "完成", f"节省 {self.format_size(size)}")
            elif pattern == "python3.10":
                path = self.project_root / "python3.10"
            else:
                continue

            if path.exists():
                try:
                    size = self.get_directory_size(path)
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                    total_saved += size
                    self.log_operation(description, "完成", f"节省 {self.format_size(size)}")
                except Exception as e:
                    self.log_operation(description, "失败", str(e))

        # 清理Rust构建缓存
        target_deps = self.project_root / "target/debug/deps"
        if target_deps.exists():
            try:
                rlib_files = list(target_deps.glob("*.rlib"))
                for rlib in rlib_files:
                    if rlib.stat().st_size > 100 * 1024 * 1024:  # >100MB
                        size = rlib.stat().st_size
                        rlib.unlink()
                        total_saved += size
                self.log_operation("清理Rust缓存", "完成")
            except Exception as e:
                self.log_operation("清理Rust缓存", "失败", str(e))

        # 清理大型PDB文件
        pdb_count = 0
        for pdb_file in self.project_root.rglob("*.pdb"):
            if pdb_file.stat().st_size > 100 * 1024 * 1024:  # >100MB
                size = pdb_file.stat().st_size
                pdb_file.unlink()
                total_saved += size
                pdb_count += 1
        self.log_operation("清理PDB文件", "完成", f"删除了 {pdb_count} 个文件")

        # 清理过期日志
        log_count = 0
        for log_file in self.project_root.rglob("*.log"):
            if log_file.stat().st_mtime < time.time() - 30 * 24 * 3600:  # 30天前
                size = log_file.stat().st_size
                log_file.unlink()
                total_saved += size
                log_count += 1
        self.log_operation("清理过期日志", "完成", f"删除了 {log_count} 个文件")

        self.report["stats"]["space_saved_gb"] = total_saved / (1024**3)
        self.log_operation("清理冗余文件", "完成", f"总共节省 {self.format_size(total_saved)}")

    def archive_large_modules(self):
        """阶段3: 归档大型模块"""
        self.log_operation("归档大型模块", "开始")

        # 归档Chrome DevTools
        chrome_dir = self.project_root / "chrome-devtools-mcp"
        if chrome_dir.exists():
            try:
                archive_path = self.project_root / "archive/chrome-devtools-mcp.tar.gz"
                with tarfile.open(archive_path, "w:gz") as tar:
                    tar.add(chrome_dir, arcname="chrome-devtools-mcp")
                shutil.rmtree(chrome_dir)
                size = archive_path.stat().st_size
                self.log_operation("归档Chrome DevTools", "完成", f"压缩后 {self.format_size(size)}")
            except Exception as e:
                self.log_operation("归档Chrome DevTools", "失败", str(e))

        # 移动大型数据文件
        large_files_dir = self.project_root / "archive/large-files"
        large_files_dir.mkdir(exist_ok=True)
        moved_count = 0
        for file_path in self.project_root.rglob("*"):
            if file_path.is_file():
                if file_path.stat().st_size > 100 * 1024 * 1024:  # >100MB
                    # 排除src和config目录
                    if "src" in file_path.parts or "config" in file_path.parts:
                        continue
                    try:
                        shutil.move(str(file_path), str(large_files_dir))
                        moved_count += 1
                    except Exception as e:
                        self.report["errors"].append(f"移动大文件失败: {file_path} - {str(e)}")
        self.log_operation("移动大文件", "完成", f"移动了 {moved_count} 个文件")

    def reorganize_debug_files(self):
        """重新组织调试文件"""
        self.log_operation("组织调试文件", "开始")

        debug_dir = self.project_root / "assets/debug"
        moved_count = 0

        for pdb_file in self.project_root.rglob("*.pdb"):
            try:
                shutil.move(str(pdb_file), str(debug_dir))
                moved_count += 1
            except Exception as e:
                self.report["errors"].append(f"移动PDB文件失败: {pdb_file} - {str(e)}")

        self.log_operation("组织调试文件", "完成", f"移动了 {moved_count} 个文件")

    def reorganize_config_files(self):
        """重新组织配置文件"""
        self.log_operation("组织配置文件", "开始")

        config_dir = self.project_root / "config"
        optimization_dir = config_dir / "optimization"
        deployment_dir = config_dir / "deployment"

        moved_count = 0

        # 移动优化结果
        for opt_file in config_dir.glob("*optimization*.json"):
            try:
                shutil.move(str(opt_file), str(optimization_dir))
                moved_count += 1
            except Exception as e:
                self.report["errors"].append(f"移动优化文件失败: {opt_file} - {str(e)}")

        # 移动基准测试结果
        for bench_file in config_dir.glob("*benchmark*.json"):
            try:
                shutil.move(str(bench_file), str(optimization_dir))
                moved_count += 1
            except Exception as e:
                self.report["errors"].append(f"移动基准文件失败: {bench_file} - {str(e)}")

        # 移动YAML配置
        for yaml_file in config_dir.glob("*.yaml"):
            try:
                shutil.move(str(yaml_file), str(deployment_dir))
                moved_count += 1
            except Exception as e:
                self.report["errors"].append(f"移动YAML文件失败: {yaml_file} - {str(e)}")

        self.log_operation("组织配置文件", "完成", f"移动了 {moved_count} 个文件")

    def clean_duplicate_files(self):
        """阶段4: 清理重复文件"""
        self.log_operation("清理重复文件", "开始")

        cleaned_count = 0

        for root, dirs, files in os.walk(self.project_root):
            for file in files:
                # 匹配 _1, _2, _3 等后缀
                match = re.match(r'(.*)_(\d+)\.(.*)', file)
                if match:
                    file_path = Path(root) / file
                    new_name = f"{match.group(1)}.{match.group(3)}"
                    new_path = Path(root) / new_name

                    # 如果目标文件不存在，才重命名
                    if not new_path.exists():
                        try:
                            file_path.rename(new_path)
                            cleaned_count += 1
                        except Exception as e:
                            self.report["errors"].append(f"重命名文件失败: {file_path} - {str(e)}")

        self.log_operation("清理重复文件", "完成", f"清理了 {cleaned_count} 个文件")

    def validate_organization(self):
        """阶段5: 验证整理结果"""
        self.log_operation("验证整理结果", "开始")

        validation_results = {}

        # 统计当前文件数量
        total_files = sum(1 for _ in self.project_root.rglob('*') if _.is_file())
        validation_results["total_files"] = total_files

        # 统计未跟踪文件
        try:
            import subprocess
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            untracked = len([line for line in result.stdout.split('\n') if line.startswith('??')])
            validation_results["untracked_files"] = untracked
        except:
            validation_results["untracked_files"] = "无法获取"

        # 计算当前目录大小
        current_size = self.get_directory_size(self.project_root)
        validation_results["total_size"] = self.format_size(current_size)

        # 检查关键目录是否存在
        key_dirs = [
            "assets/debug",
            "config/optimization",
            "scripts/deployment",
            "tests/unit",
            "docs/api",
            "archive/historical"
        ]
        missing_dirs = [d for d in key_dirs if not (self.project_root / d).exists()]
        validation_results["missing_directories"] = missing_dirs

        self.report["stats"].update(validation_results)

        # 打印验证结果
        print("\n" + "="*60)
        print("验证结果:")
        print(f"  总文件数: {total_files}")
        print(f"  总大小: {validation_results['total_size']}")
        print(f"  未跟踪文件: {validation_results['untracked_files']}")
        if missing_dirs:
            print(f"  缺失目录: {', '.join(missing_dirs)}")
        else:
            print("  ✅ 所有关键目录已创建")
        print("="*60)

        self.log_operation("验证整理结果", "完成")

    def generate_report(self):
        """生成最终报告"""
        report_path = self.project_root / "file_organization_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)

        # 生成Markdown报告
        md_path = self.project_root / "file_organization_final_report.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write("# 文件整理最终报告\n\n")
            f.write(f"**执行时间**: {self.report['timestamp']}\n\n")
            f.write(f"**项目路径**: {self.report['project_root']}\n\n")

            f.write("## 操作统计\n\n")
            f.write(f"- 总操作数: {len(self.report['operations'])}\n")
            f.write(f"- 错误数: {len(self.report['errors'])}\n")
            f.write(f"- 节省空间: {self.report['stats'].get('space_saved_gb', 0):.2f} GB\n")

            f.write("\n## 详细信息\n\n")
            for op in self.report['operations']:
                f.write(f"- {op['time']} {op['operation']}: {op['status']} {op['details']}\n")

            if self.report['errors']:
                f.write("\n## 错误列表\n\n")
                for error in self.report['errors']:
                    f.write(f"- {error}\n")

        print(f"\n报告已生成: {report_path}")
        print(f"Markdown报告: {md_path}")

    def run(self):
        """执行完整的整理流程"""
        print("="*60)
        print("项目文件自动整理工具")
        print("="*60)

        try:
            # 阶段1: 创建目录结构
            if not self.create_directory_structure():
                print("❌ 创建目录结构失败")
                return False

            # 阶段1.5: 备份关键文件
            self.backup_critical_files()

            # 阶段2: 清理冗余文件
            self.clean_redundant_files()

            # 阶段3: 归档大型模块
            self.archive_large_modules()

            # 阶段3.5: 重新组织调试文件
            self.reorganize_debug_files()

            # 阶段3.6: 重新组织配置文件
            self.reorganize_config_files()

            # 阶段4: 清理重复文件
            self.clean_duplicate_files()

            # 阶段5: 验证结果
            self.validate_organization()

            # 生成报告
            self.generate_report()

            print("\n" + "="*60)
            print("✅ 文件整理完成!")
            print("="*60)
            return True

        except Exception as e:
            self.log_operation("整理过程", "失败", str(e))
            self.report["errors"].append(f"整理过程失败: {str(e)}")
            print(f"\n❌ 整理过程出错: {e}")
            return False

if __name__ == "__main__":
    # 解析命令行参数
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = os.getcwd()

    organizer = FileOrganizer(project_root)
    success = organizer.run()

    sys.exit(0 if success else 1)
