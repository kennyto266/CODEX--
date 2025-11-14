#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速数据工具 - 港股数据生态系统命令行工具
Quick Data Tool - HK Stock Data Ecosystem CLI

功能：
1. 一键获取HKEX数据
2. 验证数据质量
3. 监控系统状态
4. 生成数据报告

作者: Claude Code
日期: 2025-11-02
"""

import os
import sys
import argparse
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def quick_fetch_hkex():
    """快速获取HKEX数据"""
    print("\n=== 快速获取HKEX数据 ===\n")

    os.system('python3 hkex_real_data_fetcher.py --auto-update')

    print("\n✓ 数据获取完成!")
    print("  数据位置: data/ 目录")
    print("  日志位置: hkex_fetcher.log")

def quick_validate():
    """快速验证数据质量"""
    print("\n=== 快速数据验证 ===\n")

    os.system('python3 data_validation_tool.py --check')

    print("\n✓ 数据验证完成!")
    print("  报告位置: data_validation_report.json")

def quick_monitor():
    """快速监控系统"""
    print("\n=== 系统状态监控 ===\n")

    os.system('python3 data_quality_monitor.py --check')

    print("\n✓ 监控完成!")
    print("  报告位置: data_quality_report.json")

def quick_verify():
    """快速系统验证"""
    print("\n=== 系统完整性验证 ===\n")

    os.system('PYTHONIOENCODING=utf-8 python3 system_verification.py')

    print("\n✓ 系统验证完成!")
    print("  报告位置: final_verification_report.json")

def show_status():
    """显示系统状态"""
    print("\n" + "="*60)
    print("港股数据生态系统 - 系统状态")
    print("="*60)

    # 检查数据文件
    data_dir = Path("data")
    if data_dir.exists():
        json_files = list(data_dir.glob("*.json"))
        csv_files = list(data_dir.glob("*.csv"))
        print(f"\n📊 数据文件: {len(json_files)} JSON + {len(csv_files)} CSV")

        # 显示最新文件
        if json_files:
            latest = max(json_files, key=lambda x: x.stat().st_mtime)
            print(f"  最新: {latest.name}")

    # 检查日志文件
    log_files = ['hkex_fetcher.log', 'data_validation.log', 'data_quality_monitor.log']
    print("\n📝 日志文件:")
    for log in log_files:
        if os.path.exists(log):
            size = os.path.getsize(log)
            print(f"  ✓ {log}: {size:,} 字节")
        else:
            print(f"  - {log}: 不存在")

    # 检查报告文件
    report_files = ['data_validation_report.json', 'data_quality_report.json']
    print("\n📄 报告文件:")
    for report in report_files:
        if os.path.exists(report):
            print(f"  ✓ {report}")
        else:
            print(f"  - {report}: 不存在")

    print("\n" + "="*60)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='快速数据工具 - 港股数据生态系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
可用命令:
  fetch   快速获取HKEX数据 (等价于 --auto-update)
  validate 验证数据质量
  monitor  监控系统状态
  verify  系统完整性验证
  status  显示系统状态

示例:
  python3 quick_data_tool.py fetch
  python3 quick_data_tool.py validate
  python3 quick_data_tool.py status
        """)

    parser.add_argument('command', nargs='?',
                       choices=['fetch', 'validate', 'monitor', 'verify', 'status'],
                       default='status',
                       help='要执行的命令')

    args = parser.parse_args()

    # 设置UTF-8编码
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore') if hasattr(sys.stdout, 'reconfigure') else None

    if args.command == 'fetch':
        quick_fetch_hkex()
    elif args.command == 'validate':
        quick_validate()
    elif args.command == 'monitor':
        quick_monitor()
    elif args.command == 'verify':
        quick_verify()
    elif args.command == 'status':
        show_status()

if __name__ == "__main__":
    main()
