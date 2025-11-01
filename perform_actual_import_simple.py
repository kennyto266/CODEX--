#!/usr/bin/env python3
"""
Execute Actual Task Import - Simplified Version
"""

import sys
import asyncio
from pathlib import Path

async def main():
    print("\n" + "="*60)
    print("TASK IMPORT EXECUTION")
    print("="*60)
    print()

    try:
        # Import dependencies
        from src.dashboard.repositories.dependency_injection import (
            initialize_database,
            get_db,
            RepositoryManager
        )

        print("Step 1: Initialize database...")
        database_url = "sqlite:///./tasks.db"
        initialize_database(database_url)
        print(f"  [OK] Database: {database_url}")
        print()

        print("Step 2: Create repositories...")
        db = get_db()
        repo_manager = RepositoryManager(db)
        print(f"  [OK] RepositoryManager created")
        print()

        print("Step 3: Import service...")
        from src.dashboard.services.task_import_service import TaskImportService
        task_import_service = TaskImportService(
            repo_manager.task_repo,
            repo_manager.sprint_repo
        )
        print(f"  [OK] TaskImportService created")
        print()

        print("Step 4: Parse tasks...")
        task_file = project_root = Path(__file__).parent / "openspec/changes/optimize-project-plan/tasks.md"
        parsed_tasks = await task_import_service.parse_tasks_from_markdown(str(task_file))
        print(f"  [OK] Parsed {len(parsed_tasks)} tasks")
        print()

        print("Step 5: Create database tables...")
        from src.dashboard.models.task import Base
        from src.dashboard.repositories.dependency_injection import _db_manager
        Base.metadata.create_all(_db_manager._engine)
        print(f"  [OK] Tables created")
        print()

        print("Step 6: Execute import...")
        import_result = await task_import_service.import_tasks(str(task_file))
        print(f"  [OK] Import completed")
        print()

        print("="*60)
        print("IMPORT COMPLETE")
        print("="*60)
        print(f"Database: ./tasks.db")
        print(f"Tasks: {len(parsed_tasks)} imported")
        print()

        return 0

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
