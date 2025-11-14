#!/usr/bin/env python3
"""
项目文件整理工具
Project File Organization Tool
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime
import subprocess

class ProjectOrganizer:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.stats = {
            'deleted': 0,
            'moved': 0,
            'archived': 0,
            'errors': []
        }
        self.backup_dir = self.project_root / "archive" / "archive_20251111"

    def analyze_project(self):
        """分析项目文件结构"""
        print("="*80)
        print("项目文件分析 | Project File Analysis")
        print("="*80)
        print()

        # 获取所有文件
        all_files = list(self.project_root.rglob('*'))
        all_files = [f for f in all_files if f.is_file()]

        # 按目录统计
        dir_stats = {}
        type_stats = {}

        for f in all_files:
            # 目录统计
            rel_path = f.relative_to(self.project_root)
            parts = rel_path.parts
            if len(parts) > 0:
                top_dir = parts[0]
                if top_dir not in dir_stats:
                    dir_stats[top_dir] = 0
                dir_stats[top_dir] += 1

            # 类型统计
            ext = f.suffix.lower()
            if ext not in type_stats:
                type_stats[ext] = 0
            type_stats[ext] += 1

        print(f"总文件数 | Total Files: {len(all_files)}")
        print()

        print("按目录分组 | Files by Directory:")
        for dir_name, count in sorted(dir_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"  {dir_name}/: {count} files")
        print()

        print("按类型分组 | Files by Type:")
        for ext, count in sorted(type_stats.items(), key=lambda x: x[1], reverse=True):
            if ext:  # Skip empty extensions
                print(f"  {ext}: {count} files")
        print()

        return all_files, dir_stats, type_stats

    def find_cleanup_candidates(self, all_files):
        """查找可清理的文件"""
        print("="*80)
        print("清理建议 | Cleanup Candidates")
        print("="*80)
        print()

        cleanup_candidates = {
            'temp_files': [],
            'duplicate_files': {},
            'old_backups': [],
            'log_files': [],
            'test_outputs': [],
            'duplicates': []
        }

        # 临时文件
        temp_patterns = ['*.tmp', '*.log', '*.bak', '*~', '.DS_Store', 'Thumbs.db']
        for file in all_files:
            if any(file.match(pattern) for pattern in temp_patterns):
                cleanup_candidates['temp_files'].append(file)

        # 测试输出文件
        for file in all_files:
            if 'test_' in file.name and file.suffix in ['.json', '.csv', '.txt']:
                cleanup_candidates['test_outputs'].append(file)

        # 检查重复文件
        name_groups = {}
        for file in all_files:
            name = file.name
            if name not in name_groups:
                name_groups[name] = []
            name_groups[name].append(file)

        for name, files in name_groups.items():
            if len(files) > 1:
                # 按修改时间排序，保留最新的
                files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                cleanup_candidates['duplicates'].append({
                    'name': name,
                    'files': files,
                    'keep': files[0],
                    'remove': files[1:]
                })

        # 输出清理建议
        print("1. 临时文件 | Temp Files:")
        if cleanup_candidates['temp_files']:
            for f in cleanup_candidates['temp_files'][:10]:
                print(f"   - {f.relative_to(self.project_root)}")
            if len(cleanup_candidates['temp_files']) > 10:
                print(f"   ... and {len(cleanup_candidates['temp_files']) - 10} more")
        else:
            print("   ✅ No temp files found")
        print()

        print("2. 重复文件 | Duplicate Files:")
        if cleanup_candidates['duplicates']:
            for dup in cleanup_candidates['duplicates'][:5]:
                print(f"   {dup['name']}:")
                print(f"     Keep: {dup['keep'].relative_to(self.project_root)}")
                print(f"     Remove: {len(dup['remove'])} copies")
        else:
            print("   ✅ No duplicates found")
        print()

        print("3. 测试输出 | Test Outputs:")
        if cleanup_candidates['test_outputs']:
            for f in cleanup_candidates['test_outputs'][:10]:
                print(f"   - {f.relative_to(self.project_root)}")
        else:
            print("   ✅ No test outputs found")
        print()

        return cleanup_candidates

    def organize_data_directory(self):
        """整理data目录"""
        print("="*80)
        print("整理 Data 目录 | Organizing Data Directory")
        print("="*80)
        print()

        data_dir = self.project_root / "data"
        if not data_dir.exists():
            print("❌ data目录不存在 | data directory not found")
            return

        # 建议的新结构
        new_structure = {
            'market_data': ['*.csv'],  # 股票数据
            'economic_indicators': ['*gdp*', '*cpi*', '*hibor*', '*unemployment*', '*retail*', '*visitor*'],
            'government_data': ['*gov*', 'real_gov_data'],
            'property_data': ['*property*', '*centaline*', '*cia*', '*rental*', '*transaction*'],
            'system_cache': ['*.json', '*.db', 'cache'],
            'temp': ['*demo*', '*_demo_*', '*demo_*']
        }

        print("建议的新结构 | Proposed Structure:")
        for new_dir, patterns in new_structure.items():
            print(f"  data/{new_dir}/")
            for pattern in patterns:
                print(f"    - {pattern}")
        print()

        # 统计当前文件
        current_files = list(data_dir.rglob('*'))
        current_files = [f for f in current_files if f.is_file()]

        print(f"当前文件数: {len(current_files)}")
        print("文件大小 | File Sizes:")

        for f in current_files:
            try:
                size_kb = f.stat().st_size / 1024
                if size_kb > 1024:
                    size_str = f"{size_kb/1024:.1f} MB"
                else:
                    size_str = f"{size_kb:.1f} KB"
                print(f"  {f.name}: {size_str}")
            except:
                pass
        print()

        return new_structure

    def create_organization_report(self, all_files, dir_stats, cleanup_candidates):
        """生成整理报告"""
        print("="*80)
        print("文件整理报告 | Organization Report")
        print("="*80)
        print()

        # 生成报告文件
        report = {
            'analysis_date': datetime.now().isoformat(),
            'total_files': len(all_files),
            'directory_stats': dict(sorted(dir_stats.items(), key=lambda x: x[1], reverse=True)),
            'cleanup_suggestions': {
                'temp_files': len(cleanup_candidates['temp_files']),
                'duplicate_groups': len(cleanup_candidates['duplicates']),
                'test_outputs': len(cleanup_candidates['test_outputs'])
            },
            'recommendations': []
        }

        # 添加建议
        if cleanup_candidates['temp_files']:
            report['recommendations'].append(f"删除 {len(cleanup_candidates['temp_files'])} 个临时文件")

        if cleanup_candidates['duplicates']:
            total_dups = sum(len(dup['remove']) for dup in cleanup_candidates['duplicates'])
            report['recommendations'].append(f"删除 {total_dups} 个重复文件")

        if cleanup_candidates['test_outputs']:
            report['recommendations'].append(f"清理 {len(cleanup_candidates['test_outputs'])} 个测试输出文件")

        # 保存报告
        report_file = self.project_root / "file_organization_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"报告已保存 | Report saved: {report_file}")
        print()

        return report

    def run_organization(self, dry_run=True):
        """执行整理"""
        print("="*80)
        print(f"执行整理 | Running Organization (DRY RUN: {dry_run})")
        print("="*80)
        print()

        # 分析项目
        all_files, dir_stats, type_stats = self.analyze_project()

        # 查找清理候选
        cleanup_candidates = self.find_cleanup_candidates(all_files)

        # 整理data目录
        self.organize_data_directory()

        # 生成报告
        report = self.create_organization_report(all_files, dir_stats, cleanup_candidates)

        print("="*80)
        print("整理总结 | Organization Summary")
        print("="*80)
        print()
        print(f"总文件数 | Total Files: {report['total_files']}")
        print()
        print("建议操作 | Recommended Actions:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
        print()
        print("="*80)
        print()
        print("执行步骤 | Next Steps:")
        print("1. 审查上述建议 | Review the recommendations above")
        print("2. 创建备份 | Create a backup before making changes")
        print("3. 设置 dry_run=False 执行实际整理 | Set dry_run=False to actually organize")
        print("4. 验证系统功能 | Verify system functionality after reorganization")
        print()

def main():
    print()
    print("╔" + "="*78 + "╗")
    print("║" + " "*15 + "PROJECT FILE ORGANIZER v1.0" + " "*24 + "║")
    print("║" + " "*10 + "项目文件整理工具 - 2025-11-11" + " "*28 + "║")
    print("╚" + "="*78 + "╝")
    print()

    organizer = ProjectOrganizer()
    organizer.run_organization(dry_run=True)

    print("按 Ctrl+C 退出 | Press Ctrl+C to exit")

if __name__ == "__main__":
    main()
