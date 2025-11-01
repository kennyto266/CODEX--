#!/usr/bin/env python3
"""
任務數據導入命令行工具
解析Markdown任務清單並導入到數據庫
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
import logging

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.dashboard.services.task_import_service import TaskImportService, TaskDataAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TaskImporterCLI:
    """任務導入命令行工具"""

    def __init__(self):
        self.import_service = None

    async def analyze(self, file_path: str) -> int:
        """
        分析任務清單文件

        Args:
            file_path: 文件路徑

        Returns:
            退出碼
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                return 1

            print(f"\n{'='*60}")
            print(f"[Analysis] 任務清單分析")
            print(f"{'='*60}\n")

            analyzer = TaskDataAnalyzer()
            analysis = analyzer.analyze_markdown_tasks(file_path)

            if not analysis:
                logger.error("分析失敗")
                return 1

            # 顯示基本信息
            print(f"文件: {analysis['file_path']}")
            print(f"總行數: {analysis['total_lines']}")
            print(f"任務數量: {analysis['task_count']}\n")

            # 優先級分布
            print("優先級分布:")
            for priority, count in analysis['priority_distribution'].items():
                percentage = (count / analysis['task_count'] * 100) if analysis['task_count'] > 0 else 0
                print(f"  {priority}: {count} 個 ({percentage:.1f}%)")
            print()

            # 工時統計
            hours_stats = analysis['hours_stats']
            print("工時統計:")
            print(f"  最小: {hours_stats['min']} 小時")
            print(f"  最大: {hours_stats['max']} 小時")
            print(f"  平均: {hours_stats['avg']:.1f} 小時")
            print(f"  總計: {hours_stats['total']} 小時")
            print()

            # 質量問題
            if analysis.get('issues'):
                print("⚠️ 發現的問題:")
                for issue in analysis['issues']:
                    print(f"  - {issue}")
                print()
            else:
                print("✅ 未發現質量問題\n")

            # 質量評分
            score = analysis.get('quality_score', 0)
            print(f"📈 質量評分: {score:.1f}/100")
            if score >= 80:
                print("  優秀 ✅")
            elif score >= 60:
                print("  良好 ⚠️")
            else:
                print("  需改進 ❌")

            print(f"\n{'='*60}")

            return 0

        except Exception as e:
            logger.error(f"分析失敗: {e}")
            return 1

    async def import_tasks(
        self,
        file_path: str,
        create_sprint: bool = True,
        dry_run: bool = False
    ) -> int:
        """
        導入任務

        Args:
            file_path: 文件路徑
            create_sprint: 是否創建Sprint
            dry_run: 演練模式

        Returns:
            退出碼
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                return 1

            print(f"\n{'='*60}")
            print(f"[Import] 任務數據導入")
            print(f"{'='*60}\n")

            if dry_run:
                print("⚠️ 演練模式（不會實際導入）\n")

            # 步驟1: 分析文件
            print("步驟1: 分析任務清單...")
            analyzer = TaskDataAnalyzer()
            analysis = analyzer.analyze_markdown_tasks(file_path)

            if not analysis:
                logger.error("分析失敗")
                return 1

            print(f"  ✓ 發現 {analysis['task_count']} 個任務")
            print(f"  ✓ 質量評分: {analysis['quality_score']:.1f}/100\n")

            # 步驟2: 解析任務
            print("步驟2: 解析任務...")
            self.import_service = TaskImportService(
                task_repo=None,  # 演練模式下不需要
                sprint_repo=None
            )

            tasks = await self.import_service.parse_tasks_from_markdown(file_path)

            if not tasks:
                logger.error("解析失敗，未發現任務")
                return 1

            print(f"  ✓ 成功解析 {len(tasks)} 個任務\n")

            # 步驟3: 顯示預覽
            print("步驟3: 數據預覽...")
            print("  按階段分布:")
            for stage, count in self.import_service._count_by_stage(tasks).items():
                print(f"    {stage}: {count} 個")

            print("  按優先級分布:")
            for priority, count in self.import_service._count_by_priority(tasks).items():
                print(f"    {priority}: {count} 個")

            total_hours = sum(t.estimated_hours for t in tasks)
            print(f"  總預估工時: {total_hours} 小時\n")

            # 步驟4: 確認導入
            if not dry_run:
                response = input("是否繼續導入？(y/N): ").strip().lower()
                if response not in ['y', 'yes', '是']:
                    print("\n已取消導入")
                    return 0

            # 步驟5: 執行導入
            if dry_run:
                print("\n步驟4: 演練模式完成")
                print("  如需實際導入，請使用 --no-dry-run 參數")
                print(f"\n{'='*60}")
                return 0

            print("\n步驟4: 執行導入...")

            # 這裡需要初始化Repository
            # 在實際使用時需要配置數據庫連接
            print("  ⚠️ 當前為演練模式")
            print("  要執行實際導入，請運行:")
            print("  python -m src.dashboard.services.task_import_service")
            print("  或使用API端點: POST /api/v1/import/tasks/start")

            print(f"\n{'='*60}")
            print("✅ 演練完成")
            print(f"{'='*60}")

            return 0

        except Exception as e:
            logger.error(f"導入失敗: {e}")
            import traceback
            traceback.print_exc()
            return 1

    async def validate(self) -> int:
        """
        驗證已導入的任務

        Returns:
            退出碼
        """
        try:
            print(f"\n{'='*60}")
            print(f"🔍 驗證已導入任務")
            print(f"{'='*60}\n")

            # TODO: 實現驗證邏輯
            print("⚠️ 驗證功能需要在實際數據庫環境中運行")
            print("請使用API端點: GET /api/v1/import/tasks/validate")

            print(f"\n{'='*60}")

            return 0

        except Exception as e:
            logger.error(f"驗證失敗: {e}")
            return 1

    async def show_help(self):
        """顯示幫助信息"""
        print("""
任務數據導入命令行工具

用法:
  python import_tasks.py <command> [options]

命令:
  analyze <file>     分析任務清單文件質量
  import <file>      導入任務到數據庫
  validate           驗證已導入的任務
  help               顯示此幫助信息

示例:
  # 分析任務清單
  python import_tasks.py analyze openspec/changes/optimize-project-plan/tasks.md

  # 導入任務（演練模式）
  python import_tasks.py import openspec/changes/optimize-project-plan/tasks.md

  # 實際導入
  python import_tasks.py import openspec/changes/optimize-project-plan/tasks.md --no-dry-run

  # 創建Sprint
  python import_tasks.py import openspec/changes/optimize-project-plan/tasks.md --create-sprint

更多幫助: python import_tasks.py help
        """)


async def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="任務數據導入命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'command',
        choices=['analyze', 'import', 'validate', 'help'],
        help='要執行的命令'
    )

    parser.add_argument(
        'file',
        nargs='?',
        help='任務清單文件路徑（用於analyze和import命令）'
    )

    parser.add_argument(
        '--create-sprint',
        action='store_true',
        default=True,
        help='創建Sprint（默認True）'
    )

    parser.add_argument(
        '--no-dry-run',
        action='store_true',
        help='執行實際導入（默認為演練模式）'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='詳細輸出'
    )

    args = parser.parse_args()

    # 設置日誌級別
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    cli = TaskImporterCLI()

    # 處理命令
    if args.command == 'help':
        await cli.show_help()
        return 0

    if args.command == 'analyze':
        if not args.file:
            print("❌ 錯誤: 需要指定文件路徑\n")
            await cli.show_help()
            return 1
        return await cli.analyze(args.file)

    elif args.command == 'import':
        if not args.file:
            print("❌ 錯誤: 需要指定文件路徑\n")
            await cli.show_help()
            return 1
        dry_run = not args.no_dry_run
        return await cli.import_tasks(
            args.file,
            create_sprint=args.create_sprint,
            dry_run=dry_run
        )

    elif args.command == 'validate':
        return await cli.validate()

    else:
        print(f"❌ 未知命令: {args.command}\n")
        await cli.show_help()
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
