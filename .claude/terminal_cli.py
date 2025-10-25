#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
终端CLI包装器
提供命令行接口用于创建和管理终端
自动处理重试和错误恢复
"""

import sys
import time
import argparse
import json
from pathlib import Path
from typing import Optional

# 添加.claude目录到Python路径
claude_dir = Path(__file__).parent
sys.path.insert(0, str(claude_dir))

from improved_terminal_mcp import ImprovedTerminalMCP, TerminalState


class TerminalCLI:
    """终端CLI接口"""

    def __init__(self, max_retries: int = 3, wait_time: float = 1.0):
        """初始化CLI"""
        self.wrapper = ImprovedTerminalMCP(max_retries=max_retries, wait_time=wait_time)
        self.terminal_id: Optional[str] = None

    def create_terminal(self, cwd: str = ".", shell: str = "powershell") -> bool:
        """创建新终端"""
        print(f"[*] 创建终端: shell={shell}, cwd={cwd}")

        self.terminal_id = self.wrapper.create_terminal(cwd=cwd, shell=shell)

        if self.terminal_id:
            print(f"[+] 终端创建成功: {self.terminal_id}")
            return True
        else:
            print(f"[-] 终端创建失败")
            return False

    def execute(self, command: str, wait: float = 2.0) -> bool:
        """执行命令"""
        if not self.terminal_id:
            print("[-] 错误: 没有活跃的终端，请先创建终端")
            return False

        print(f"[*] 执行命令: {command}")

        output = self.wrapper.execute_command_safe(
            self.terminal_id,
            command,
            wait_for_output=wait
        )

        if output:
            print("[+] 命令执行成功，输出:")
            print("-" * 60)
            print(output)
            print("-" * 60)
            return True
        else:
            print("[-] 无法读取输出")
            return False

    def info(self) -> bool:
        """显示终端信息"""
        if not self.terminal_id:
            print("[-] 错误: 没有活跃的终端")
            return False

        info = self.wrapper.terminals.get(self.terminal_id)
        if not info:
            print("[-] 终端信息不可用")
            return False

        print("[*] 终端信息:")
        print(f"  • ID: {self.terminal_id}")
        print(f"  • 状态: {info['state'].value}")
        print(f"  • Shell: {info['shell']}")
        print(f"  • CWD: {info['cwd']}")
        print(f"  • 正常运行时间: {time.time() - info['created_at']:.1f}秒")
        print(f"  • 操作数: {info['operation_count']}")
        print(f"  • 错误数: {info['error_count']}")

        return True

    def stats(self) -> bool:
        """显示统计信息"""
        stats = self.wrapper.get_operation_stats()

        print("[*] 操作统计:")
        print(f"  • 总操作: {stats['total_operations']}")
        print(f"  • 成功: {stats['successful']}")
        print(f"  • 失败: {stats['failed']}")
        print(f"  • 成功率: {stats['success_rate']:.1f}%")
        print(f"  • 已创建终端: {stats['terminals_created']}")

        return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="改进的终端MCP CLI包装器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  创建终端:
    python terminal_cli.py create --cwd "C:\\path\\to\\dir" --shell powershell

  执行命令:
    python terminal_cli.py execute "python --version"

  显示信息:
    python terminal_cli.py info

  显示统计:
    python terminal_cli.py stats

  完整流程:
    python terminal_cli.py create
    python terminal_cli.py execute "dir"
    python terminal_cli.py info
    python terminal_cli.py stats
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="命令")

    # create 命令
    create_parser = subparsers.add_parser("create", help="创建新终端")
    create_parser.add_argument(
        "--cwd",
        default=".",
        help="工作目录（默认: 当前目录）"
    )
    create_parser.add_argument(
        "--shell",
        default="powershell",
        help="Shell类型（默认: powershell）"
    )
    create_parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="最大重试次数（默认: 3）"
    )

    # execute 命令
    execute_parser = subparsers.add_parser("execute", help="执行命令")
    execute_parser.add_argument("command", help="要执行的命令")
    execute_parser.add_argument(
        "--wait",
        type=float,
        default=2.0,
        help="等待输出的时间（秒）（默认: 2.0）"
    )

    # info 命令
    subparsers.add_parser("info", help="显示终端信息")

    # stats 命令
    subparsers.add_parser("stats", help="显示操作统计")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # 创建CLI实例
    cli = TerminalCLI(
        max_retries=getattr(args, "retries", 3),
        wait_time=1.0
    )

    # 处理命令
    try:
        if args.command == "create":
            success = cli.create_terminal(
                cwd=args.cwd,
                shell=args.shell
            )
            return 0 if success else 1

        elif args.command == "execute":
            success = cli.execute(args.command, wait=args.wait)
            return 0 if success else 1

        elif args.command == "info":
            success = cli.info()
            return 0 if success else 1

        elif args.command == "stats":
            success = cli.stats()
            return 0 if success else 1

        else:
            print(f"[-] 未知命令: {args.command}")
            return 1

    except KeyboardInterrupt:
        print("\n[-] 被用户中断")
        return 130

    except Exception as e:
        print(f"[-] 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
