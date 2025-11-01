#!/bin/bash

echo ""
echo "============================================"
echo " Task Management System - Quick Start"
echo "============================================"
echo ""

echo "Step 1: Verifying task import functionality..."
python3 verify_task_import.py
if [ $? -ne 0 ]; then
    echo "Warning: Verification failed, but continuing..."
fi

echo ""
echo "Step 2: Running basic tests..."
python3 -m pytest tests/dashboard/test_task_import_basic.py -v
if [ $? -ne 0 ]; then
    echo "Warning: Some tests failed, but continuing..."
fi

echo ""
echo "Step 3: Analyzing task list..."
python3 scripts/import_tasks.py analyze openspec/changes/optimize-project-plan/tasks.md

echo ""
echo "Step 4: Opening task board in browser..."
open "file://$(pwd)/src/dashboard/static/task-board-demo.html" 2>/dev/null || \
xdg-open "file://$(pwd)/src/dashboard/static/task-board-demo.html" 2>/dev/null

echo ""
echo "============================================"
echo " System is ready!"
echo "============================================"
echo ""
echo "Available resources:"
echo "  - Task Board: file://$(pwd)/src/dashboard/static/task-board-demo.html"
echo "  - Import Guide: $(pwd)/src/dashboard/static/TASK_IMPORT_GUIDE.md"
echo "  - Summary: $(pwd)/TASK_IMPORT_PROJECT_SUMMARY.md"
echo ""
echo "Commands:"
echo "  - Analyze: python3 scripts/import_tasks.py analyze [file]"
echo "  - Import (dry run): python3 scripts/import_tasks.py import [file]"
echo "  - Import (actual): python3 scripts/import_tasks.py import [file] --no-dry-run"
echo "  - Run tests: python3 -m pytest tests/dashboard/test_task_import_basic.py -v"
echo ""
echo "Opening browser in 3 seconds..."
sleep 3

echo ""
echo "============================================"
echo " Task Management System started successfully!"
echo "============================================"
echo ""
