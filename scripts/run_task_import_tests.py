#!/usr/bin/env python3
"""
任务导入功能测试运行脚本
执行所有任务导入相关的测试用例
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """执行命令并输出结果"""
    print(f"\n{'='*60}")
    print(f"[RUNNING] {description}")
    print(f"{'='*60}\n")

    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    return result.returncode


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="任务导入功能测试运行器"
    )

    parser.add_argument(
        '--test-type',
        choices=['parser', 'service', 'api', 'integration', 'all'],
        default='all',
        help='测试类型 (默认: all)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='详细输出'
    )

    parser.add_argument(
        '--coverage',
        action='store_true',
        help='生成覆盖率报告'
    )

    parser.add_argument(
        '--output',
        type=str,
        help='输出文件路径'
    )

    args = parser.parse_args()

    # 设置Python路径
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

    # 构建pytest命令
    test_path = "tests/dashboard/"

    if args.test_type == 'parser':
        test_pattern = "test_task_parser.py"
    elif args.test_type == 'service':
        test_pattern = "test_task_import_service.py"
    elif args.test_type == 'api':
        test_pattern = "test_task_import_api.py"
    elif args.test_type == 'integration':
        test_pattern = "test_task_import_integration.py"
    else:
        test_pattern = "test_task_*.py"

    # 构建命令
    cmd = f"python -m pytest {test_path}{test_pattern}"

    if args.verbose:
        cmd += " -v"

    if args.coverage:
        cmd += " --cov=src.dashboard.services.task_import_service"
        cmd += " --cov=src.dashboard.api.task_import"
        cmd += " --cov-report=html"

    if args.output:
        cmd += f" --junit-xml={args.output}"

    # 执行测试
    returncode = run_command(cmd, f"运行{args.test_type}测试")

    # 输出总结
    print(f"\n{'='*60}")
    if returncode == 0:
        print("✅ 所有测试通过!")
    else:
        print("❌ 部分测试失败")
    print(f"{'='*60}\n")

    return returncode


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
