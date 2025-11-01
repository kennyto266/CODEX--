@echo off
chcp 65001 > nul

echo.
echo ============================================================
echo ACTUAL TASK IMPORT - 172 Historical Tasks
echo ============================================================
echo.

echo Step 1: Parsing task list...
python scripts/import_tasks.py analyze openspec/changes/optimize-project-plan/tasks.md

echo.
echo Step 2: Starting actual import...
echo This will create SQLite database: tasks.db
echo.

python scripts/import_tasks.py import openspec/changes/optimize-project-plan/tasks.md --no-dry-run

echo.
echo ============================================================
echo IMPORT COMPLETED
echo ============================================================
echo.
echo Database location: ./tasks.db
echo Task board: http://localhost:8001/task-board-demo.html
echo.
