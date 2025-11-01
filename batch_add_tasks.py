#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import time

# 定义要添加的任务列表
tasks = [
    ("TASK-BATCH-001", "Data Processing Script", "Process daily data files", "TODO", "P1", 8),
    ("TASK-BATCH-002", "API Integration", "Connect to external API", "TODO", "P2", 12),
    ("TASK-BATCH-003", "User Interface Update", "Improve dashboard design", "TODO", "P1", 16),
    ("TASK-BATCH-004", "Database Optimization", "Optimize query performance", "TODO", "P2", 10),
    ("TASK-BATCH-005", "Unit Tests", "Write comprehensive tests", "TODO", "P1", 6),
]

print("\n" + "="*70)
print("  BATCH TASK CREATION")
print("="*70)

# 连接数据库
conn = sqlite3.connect('tasks.db')
cursor = conn.cursor()

added_count = 0
failed_count = 0

# 逐个添加任务
for task_id, title, desc, status, priority, hours in tasks:
    try:
        cursor.execute("""
            INSERT INTO tasks (
                id, title, description, status, priority,
                estimated_hours, actual_hours, stage, section,
                assignee, reporter, sprint, story_points,
                progress_percentage, is_blocked, is_completed,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, 1, 0.0, 0, 0, datetime('now'), datetime('now'))
        """, (
            task_id, title, desc, status, priority,
            hours, "Batch", "BatchModule", "User A", "Admin", "BATCH-2025"
        ))
        print(f"[OK] Added: {task_id} - {title}")
        added_count += 1
    except Exception as e:
        print(f"[FAIL] {task_id}: {str(e)}")
        failed_count += 1

# 提交更改
conn.commit()

# 验证总数
cursor.execute("SELECT COUNT(*) FROM tasks")
total_count = cursor.fetchone()[0]

# 统计各状态任务
cursor.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status")
status_counts = cursor.fetchall()

print("\n" + "="*70)
print("  CREATION SUMMARY")
print("="*70)
print(f"\nSuccessfully added: {added_count} tasks")
print(f"Failed: {failed_count} tasks")
print(f"Total tasks in database: {total_count}")

print("\nTask Status Breakdown:")
for status, count in status_counts:
    print(f"  {status}: {count}")

print("\n" + "="*70)
print("  NEXT STEPS")
print("="*70)
print("\n1. Open the task board:")
print("   http://localhost:8001/task-board-execution.html")
print("\n2. Click the 'Refresh' button to see new tasks")
print("\n3. Execute tasks by clicking the 🚀 button")
print("\n4. Use batch execution for multiple tasks")
print("\n" + "="*70)

conn.close()
