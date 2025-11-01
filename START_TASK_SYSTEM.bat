@echo off
chcp 65001 > nul
title Task Management System

echo.
echo ============================================
echo  Task Management System - Quick Start
echo ============================================
echo.

echo Step 1: Verifying task import functionality...
python verify_task_import.py
if %errorlevel% neq 0 (
    echo Warning: Verification failed, but continuing...
)

echo.
echo Step 2: Running basic tests...
python -m pytest tests/dashboard/test_task_import_basic.py -v
if %errorlevel% neq 0 (
    echo Warning: Some tests failed, but continuing...
)

echo.
echo Step 3: Analyzing task list...
python scripts/import_tasks.py analyze openspec/changes/optimize-project-plan/tasks.md

echo.
echo Step 4: Opening task board in browser...
start "" "file://%cd%\src\dashboard\static\task-board-demo.html"

echo.
echo ============================================
echo  System is ready!
echo ============================================
echo.
echo Available resources:
echo   - Task Board: file://%cd%\src\dashboard\static\task-board-demo.html
echo   - Import Guide: %cd%\src\dashboard\static\TASK_IMPORT_GUIDE.md
echo   - Summary: %cd%\TASK_IMPORT_PROJECT_SUMMARY.md
echo.
echo Commands:
echo   - Analyze: python scripts\import_tasks.py analyze [file]
echo   - Import (dry run): python scripts\import_tasks.py import [file]
echo   - Import (actual): python scripts\import_tasks.py import [file] --no-dry-run
echo   - Run tests: python -m pytest tests\dashboard\test_task_import_basic.py -v
echo.
echo Opening browser in 3 seconds...
timeout /t 3 > nul

echo.
echo ============================================
echo  Task Management System started successfully!
echo ============================================
echo.
pause
