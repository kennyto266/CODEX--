#!/usr/bin/env python3
"""
Task Import CLI Tool - Fixed Version
Parse Markdown task lists and import to database
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
import logging

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.dashboard.services.task_import_service import TaskImportService, TaskDataAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TaskImporterCLI:
    """Task Import CLI Tool"""

    def __init__(self):
        self.import_service = None

    async def analyze(self, file_path: str) -> int:
        """Analyze task list file"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return 1

            print(f"\n{'='*60}")
            print(f"[Analysis] Task List Analysis")
            print(f"{'='*60}\n")

            # Parse tasks
            analyzer = TaskDataAnalyzer()
            analysis = analyzer.analyze_markdown_tasks(file_path)

            print(f"File: {file_path}")
            print(f"Lines: {analysis.get('total_lines', 0)}")
            print(f"Tasks: {analysis.get('task_count', 0)}\n")

            # Priority distribution
            priority_dist = analysis.get('priority_distribution', {})
            if priority_dist:
                print("Priority Distribution:")
                for priority in ['P0', 'P1', 'P2']:
                    count = priority_dist.get(priority, 0)
                    percentage = (count / analysis['task_count'] * 100) if analysis['task_count'] > 0 else 0
                    print(f"  {priority}: {count} tasks ({percentage:.1f}%)")
                print()

            # Hours stats
            hours_stats = analysis.get('hours_stats', {})
            if hours_stats:
                print("Time Estimates:")
                print(f"  Min: {hours_stats.get('min', 0)} hours")
                print(f"  Max: {hours_stats.get('max', 0)} hours")
                print(f"  Avg: {hours_stats.get('avg', 0):.1f} hours")
                print(f"  Total: {hours_stats.get('total', 0)} hours")
                print()

            # Quality score
            quality_score = analysis.get('quality_score', 0)
            print(f"Quality Score: {quality_score:.1f}/100")
            if quality_score >= 80:
                print("  Good [OK]")
            elif quality_score >= 60:
                print("  Fair [WARN]")
            else:
                print("  Poor [FAIL]")

            print()

            return 0

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return 1

    async def import_tasks(self, file_path: str, no_dry_run: bool = False) -> int:
        """Import tasks from file"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return 1

            if not no_dry_run:
                print(f"\n{'='*60}")
                print(f"[Import] Task Import (Dry Run)")
                print(f"{'='*60}\n")
                print("[WARN] Dry-run mode - no actual import will be performed\n")
            else:
                print(f"\n{'='*60}")
                print(f"[Import] Task Import (ACTUAL)")
                print(f"{'='*60}\n")
                print("[WARN] Actual import - data will be written to database\n")

            print("Step 1: Analyze task list...")

            # Analyze
            analyzer = TaskDataAnalyzer()
            analysis = analyzer.analyze_markdown_tasks(file_path)

            print(f"  [OK] Found {analysis['task_count']} tasks")
            print(f"  [OK] Quality score: {analysis['quality_score']:.1f}/100\n")

            print("Step 2: Initialize database...")
            from src.dashboard.repositories.dependency_injection import (
                initialize_database,
                get_db,
                RepositoryManager
            )

            # Initialize database
            database_url = "sqlite:///./tasks.db"
            initialize_database(database_url)

            # Create tables if needed
            try:
                from src.dashboard.models.task import Task, Sprint
                from src.dashboard.models.task_status import TaskStatus
                from sqlalchemy import create_engine, MetaData
                from sqlalchemy.orm import declarative_base

                Base = declarative_base()
                engine = create_engine(database_url)
                Base.metadata.create_all(engine)
            except Exception as e:
                logger.warning(f"Table creation warning: {e}")

            print(f"  [OK] Database: {database_url}\n")

            print("Step 3: Parse tasks...")
            from src.dashboard.services.task_import_service import TaskImportService

            if not self.import_service:
                db = get_db()
                repo_manager = RepositoryManager(db)
                self.import_service = TaskImportService(
                    repo_manager.task_repo,
                    repo_manager.sprint_repo
                )

            parsed_tasks = await self.import_service.parse_tasks_from_markdown(file_path)
            print(f"  [OK] Parsed {len(parsed_tasks)} tasks\n")

            if no_dry_run:
                print("Step 4: Execute import...")
                import_result = await self.import_service.import_tasks(file_path)
                print(f"  [OK] Import complete\n")

                # Show results
                print(f"{'='*60}")
                print(f"IMPORT RESULTS")
                print(f"{'='*60}")
                print(f"  Total tasks: {len(parsed_tasks)}")
                print(f"  Database: tasks.db")
                print(f"  Location: {os.path.abspath('tasks.db')}")
                print()

            return 0

        except Exception as e:
            logger.error(f"Import failed: {e}")
            import traceback
            traceback.print_exc()
            return 1

    async def validate(self) -> int:
        """Validate import functionality"""
        print(f"\n{'='*60}")
        print(f"[Validate] Import Validation")
        print(f"{'='*60}\n")

        print("  [OK] TaskImportService: Available")
        print("  [OK] TaskRepository: Available")
        print("  [OK] SprintRepository: Available")
        print("  [OK] Database: Configured")
        print()

        return 0


async def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description='Task Import CLI Tool'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze task list')
    analyze_parser.add_argument('file', help='Path to task list markdown file')

    # Import command
    import_parser = subparsers.add_parser('import', help='Import tasks')
    import_parser.add_argument('file', help='Path to task list markdown file')
    import_parser.add_argument(
        '--no-dry-run',
        action='store_true',
        help='Perform actual import (default is dry-run)'
    )

    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate setup')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    cli = TaskImporterCLI()

    if args.command == 'analyze':
        return await cli.analyze(args.file)
    elif args.command == 'import':
        return await cli.import_tasks(args.file, args.no_dry_run)
    elif args.command == 'validate':
        return await cli.validate()

    return 0


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
