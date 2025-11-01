#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI Task Status Updater
Auto update task status from command line
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def get_all_tasks():
    """Get all tasks"""
    response = requests.get(f"{BASE_URL}/tasks")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"[ERROR] Failed to get tasks: HTTP {response.status_code}")
        return []

def update_task_status(task_id, new_status):
    """Update task status"""
    response = requests.put(
        f"{BASE_URL}/tasks/{task_id}/status",
        params={"new_status": new_status}
    )

    if response.status_code == 200:
        updated_task = response.json()
        print(f"[OK] Task {task_id} status updated to: {new_status}")
        print(f"     Title: {updated_task.get('title', 'N/A')}")
        return True
    else:
        print(f"[ERROR] Failed to update task {task_id}: HTTP {response.status_code}")
        try:
            error_detail = response.json()
            print(f"     Error: {error_detail}")
        except:
            print(f"     Response: {response.text}")
        return False

def batch_update_by_status(from_status, to_status):
    """Batch update tasks by status"""
    tasks = get_all_tasks()
    target_tasks = [t for t in tasks if t.get('status') == from_status]

    if not target_tasks:
        print(f"[WARN] No tasks found with status '{from_status}'")
        return 0

    print(f"\n[INFO] Found {len(target_tasks)} tasks with status '{from_status}'")
    print(f"       Will update to: '{to_status}'")

    success_count = 0
    for task in target_tasks:
        task_id = task.get('id')
        if update_task_status(task_id, to_status):
            success_count += 1

    print(f"\n[OK] Batch update completed: {success_count}/{len(target_tasks)} successful")
    return success_count

def show_stats():
    """Show task statistics"""
    tasks = get_all_tasks()
    if not tasks:
        return

    status_counts = {}
    for task in tasks:
        status = task.get('status', 'Unknown')
        status_counts[status] = status_counts.get(status, 0) + 1

    print("\n=== Task Status Statistics ===")
    for status, count in sorted(status_counts.items()):
        percentage = (count / len(tasks)) * 100
        print(f"  {status:12s}: {count:3d} ({percentage:5.1f}%)")

    print("=" * 30)
    print(f"  {'TOTAL':12s}: {len(tasks):3d}")

    completed = sum(1 for t in tasks if t.get('is_completed'))
    print(f"\nCompletion Rate: {completed}/{len(tasks)} ({(completed/len(tasks)*100):.1f}%)")

def main():
    if len(sys.argv) < 2:
        print("""
=== CLI Task Status Updater ===

Usage:
  python cli_task_updater.py stats                    # Show statistics
  python cli_task_updater.py update <ID> <STATUS>    # Update single task
  python cli_task_updater.py batch <FROM> <TO>       # Batch update by status

Examples:
  python cli_task_updater.py stats
  python cli_task_updater.py update TASK-100 "已完成"
  python cli_task_updater.py batch "待開始" "進行中"

Supported Status:
  - 待開始
  - 進行中
  - 待驗收
  - 已完成
  - 已阻塞
""")
        return

    command = sys.argv[1].lower()

    if command == "stats":
        show_stats()

    elif command == "update" and len(sys.argv) == 4:
        task_id = sys.argv[2]
        new_status = sys.argv[3]
        update_task_status(task_id, new_status)

    elif command == "batch" and len(sys.argv) == 4:
        from_status = sys.argv[2]
        to_status = sys.argv[3]
        batch_update_by_status(from_status, to_status)

    else:
        print("[ERROR] Invalid command or insufficient parameters")
        print("Type 'python cli_task_updater.py' for usage help")

if __name__ == "__main__":
    main()
