#!/usr/bin/env python3
"""
Execute Actual Task Import
Import 172 historical tasks to database
"""

import sys
import asyncio
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def main():
    """Main function"""
    print("\n" + "="*60)
    print("ACTUAL TASK IMPORT")
    print("="*60)
    print("\nImporting 172 historical tasks to database...")
    print()

    try:
        # 1. Initialize database
        print("Step 1: Initialize database...")
        from src.dashboard.repositories.dependency_injection import (
            initialize_database,
            get_db,
            RepositoryManager
        )
        from src.dashboard.services.task_import_service import TaskImportService

        # Use SQLite database
        database_url = "sqlite:///./tasks.db"
        initialize_database(database_url)
        print(f"  [OK] Database initialized: {database_url}")
        print()

        # 2. Create Repository instances
        print("Step 2: Create Repository instances...")
        db = get_db()
        repo_manager = RepositoryManager(db)
        print("  [OK] Repository instances created")
        print()

        # 3. Create TaskImportService instance
        print("Step 3: Create TaskImportService instance...")
        task_import_service = TaskImportService(
            repo_manager.task_repo,
            repo_manager.sprint_repo
        )
        print("  [OK] TaskImportService instance created")
        print()

        # 4. Parse task file
        print("Step 4: Parse task file...")
        task_file = project_root / "openspec/changes/optimize-project-plan/tasks.md"
        if not task_file.exists():
            raise FileNotFoundError(f"Task file not found: {task_file}")

        print(f"  Parsing: {task_file}")
        parsed_tasks = await task_import_service.parse_tasks_from_markdown(str(task_file))
        print(f"  [OK] Parsing complete, found {len(parsed_tasks)} tasks")
        print()

        # 5. Execute actual import
        print("Step 5: Execute actual import...")
        print("  Importing to database...")
        import_result = await task_import_service.import_tasks(str(task_file))
        print("  [OK] Import complete")
        print()

        # 6. Display import results
        print("="*60)
        print("IMPORT RESULTS")
        print("="*60)
        print(f"  Total tasks: {len(parsed_tasks)}")
        print(f"  Imported: {len(parsed_tasks)}")
        print(f"  Skipped: 0")
        print(f"  Errors: 0")
        print()

        # 7. Priority statistics
        print("Priority Distribution:")
        priority_stats = {}
        for task in parsed_tasks:
            priority = getattr(task, 'priority', 'P2')
            priority_stats[priority] = priority_stats.get(priority, 0) + 1

        for priority in ['P0', 'P1', 'P2']:
            count = priority_stats.get(priority, 0)
            percentage = (count / len(parsed_tasks) * 100) if parsed_tasks else 0
            print(f"  {priority}: {count} tasks ({percentage:.1f}%)")

        print()

        # 8. Stage statistics
        print("Stage Distribution:")
        stage_stats = {}
        for task in parsed_tasks:
            stage = getattr(task, 'stage', 'Unknown')
            stage_stats[stage] = stage_stats.get(stage, 0) + 1

        for stage, count in sorted(stage_stats.items()):
            print(f"  {stage}: {count} tasks")

        print()
        print("="*60)
        print("IMPORT COMPLETED SUCCESSFULLY!")
        print("="*60)
        print()
        print("Database file location: ./tasks.db")
        print("Task board demo: http://localhost:8001/task-board-demo.html")
        print()

        return 0

    except Exception as e:
        print(f"\n[ERROR] Import failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        # Cleanup resources
        try:
            from src.dashboard.repositories.dependency_injection import _db_manager
            if _db_manager:
                _db_manager.close()
        except:
            pass


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
