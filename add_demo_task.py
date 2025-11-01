#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import time

# Connect to database
conn = sqlite3.connect('tasks.db')
cursor = conn.cursor()

# Generate new task ID
task_id = f"TASK-DEMO-{int(time.time())}"

# Insert new task (using English to avoid encoding issues)
cursor.execute("""
INSERT INTO tasks (
    id, title, description, status, priority,
    estimated_hours, actual_hours, stage, section,
    assignee, reporter, sprint, story_points,
    progress_percentage, is_blocked, is_completed,
    created_at, updated_at
) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, 1, 0.0, 0, 0, datetime('now'), datetime('now'))
""", (
    task_id,
    "Demo Task - Local Execution Feature",
    "This task demonstrates adding new tasks to the system",
    "TODO",  # Using English status
    "P2",
    8,
    "Demo",
    "Feature",
    "User A",
    "Admin",
    "SPRINT-DEMO",
))

conn.commit()

# Verify
cursor.execute("SELECT id, title, status FROM tasks WHERE id = ?", (task_id,))
result = cursor.fetchone()

print("\n" + "="*60)
if result:
    print("SUCCESS: Task added!")
    print(f"  ID: {result[0]}")
    print(f"  Title: {result[1]}")
    print(f"  Status: {result[2]}")
else:
    print("ERROR: Failed to add task")

# Show current task count
cursor.execute("SELECT COUNT(*) FROM tasks")
count = cursor.fetchone()[0]
print(f"\nTotal tasks in database: {count}")
print("="*60)

conn.close()
