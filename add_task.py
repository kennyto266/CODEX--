#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加新任务到待执行列表
"""

import sqlite3
import sys
from datetime import datetime

def add_task(task_id, title, description="", status="TODO", priority="P2", estimated_hours=8):
    """添加新任务"""
    try:
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()

        # 检查任务ID是否已存在
        cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
        if cursor.fetchone():
            print(f"ERROR: Task {task_id} already exists!")
            conn.close()
            return False

        # 插入新任务
        cursor.execute("""
            INSERT INTO tasks (
                id, title, description, status, priority,
                estimated_hours, actual_hours, stage, section,
                assignee, reporter, sprint, story_points,
                progress_percentage, is_blocked, is_completed,
                created_at, updated_at, execution_result
            ) VALUES (?, ?, ?, ?, ?, ?, 0, NULL, NULL, NULL, NULL, NULL, 1, 0.0, 0, 0, ?, ?, NULL)
        """, (
            task_id, title, description, status, priority,
            estimated_hours, datetime.now().isoformat(), datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

        print(f"SUCCESS: Task {task_id} added to {status}")
        return True

    except Exception as e:
        print(f"ERROR: Failed to add task: {e}")
        return False

def list_tasks(status=None):
    """列出任务"""
    try:
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()

        if status:
            cursor.execute("""
                SELECT id, title, status, priority, estimated_hours
                FROM tasks WHERE status = ? ORDER BY id
            """, (status,))
        else:
            cursor.execute("""
                SELECT id, title, status, priority, estimated_hours
                FROM tasks ORDER BY status, id
            """)

        print("\nTask List:")
        print("-" * 80)
        for row in cursor.fetchall():
            print(f"{row[0]:<15} {row[1]:<30} {row[2]:<15} {row[3]:<8} {row[4]}h")

        conn.close()
        return True

    except Exception as e:
        print(f"ERROR: Failed to list tasks: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("\n=== Task Management ===\n")
        print("Usage:")
        print("  python add_task.py list [STATUS]     # List all or filtered tasks")
        print("  python add_task.py add <ID> <TITLE>  # Add new task to TODO")
        print("\nExamples:")
        print("  python add_task.py list")
        print("  python add_task.py list TODO")
        print("  python add_task.py add TASK-300 'New Feature Development'")
        print("  python add_task.py add TASK-301 'Bug Fix' 'Fix critical bug' P1 16")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "list":
        status = sys.argv[2] if len(sys.argv) > 2 else None
        list_tasks(status)

    elif command == "add":
        if len(sys.argv) < 4:
            print("ERROR: Missing task ID or title")
            print("Usage: python add_task.py add <ID> <TITLE> [DESCRIPTION] [PRIORITY] [HOURS]")
            sys.exit(1)

        task_id = sys.argv[2]
        title = sys.argv[3]
        description = sys.argv[4] if len(sys.argv) > 4 else ""
        priority = sys.argv[5] if len(sys.argv) > 5 else "P2"
        hours = int(sys.argv[6]) if len(sys.argv) > 6 else 8

        add_task(task_id, title, description, "TODO", priority, hours)

    else:
        print(f"ERROR: Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
