#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任務狀態自動化示例腳本
演示如何在CLI中自動更新任務狀態

使用方法:
1. 單個更新: python task_automation_examples.py update TASK-100 已完成
2. 批量更新: python task_automation_examples.py batch 待開始 進行中
3. 檢查狀態: python task_automation_examples.py check TASK-100
"""

import requests
import sys

BASE_URL = "http://localhost:8000"

def update_single_task(task_id, new_status):
    """更新單個任務"""
    print(f"Updating {task_id} to '{new_status}'...")

    response = requests.put(
        f"{BASE_URL}/tasks/{task_id}/status",
        params={"new_status": new_status}
    )

    if response.status_code == 200:
        task = response.json()
        print(f"[SUCCESS] {task_id} -> {new_status}")
        return True
    else:
        print(f"[FAILED] HTTP {response.status_code}")
        return False

def batch_update(from_status, to_status):
    """批量更新同狀態的所有任務"""
    print(f"\\nBatch updating tasks from '{from_status}' to '{to_status}'...")

    # 獲取所有任務
    response = requests.get(f"{BASE_URL}/tasks")
    tasks = response.json()

    # 篩選目標任務
    target_tasks = [t for t in tasks if t.get('status') == from_status]

    if not target_tasks:
        print(f"[WARN] No tasks found with status '{from_status}'")
        return

    print(f"Found {len(target_tasks)} tasks to update\\n")

    success_count = 0
    for task in target_tasks:
        task_id = task.get('id')
        if update_single_task(task_id, to_status):
            success_count += 1

    print(f"\\n[COMPLETE] {success_count}/{len(target_tasks)} updated successfully")

def check_task_status(task_id):
    """檢查任務狀態"""
    response = requests.get(f"{BASE_URL}/tasks/{task_id}")

    if response.status_code == 200:
        task = response.json()
        print(f"\\nTask: {task_id}")
        print(f"Title: {task.get('title', 'N/A')}")
        print(f"Status: {task.get('status', 'N/A')}")
        print(f"Priority: {task.get('priority', 'N/A')}")
        print(f"Completed: {task.get('is_completed', False)}")
    else:
        print(f"[ERROR] Task {task_id} not found")

def show_all_tasks():
    """顯示所有任務"""
    response = requests.get(f"{BASE_URL}/tasks")
    tasks = response.json()

    print(f"\\nTotal: {len(tasks)} tasks\\n")

    # 按狀態分組
    status_groups = {}
    for task in tasks:
        status = task.get('status', 'Unknown')
        if status not in status_groups:
            status_groups[status] = []
        status_groups[status].append(task)

    # 顯示每個狀態的任務
    for status, task_list in sorted(status_groups.items()):
        print(f"\\n[{status}] ({len(task_list)} tasks):")
        for task in task_list[:5]:  # 只顯示前5個
            print(f"  - {task.get('id')}: {task.get('title', 'N/A')}")
        if len(task_list) > 5:
            print(f"  ... and {len(task_list) - 5} more")

def main():
    if len(sys.argv) < 2:
        print("""
=== Task Automation Examples ===

Commands:
  update <ID> <STATUS>    Update single task
  batch <FROM> <TO>       Batch update tasks by status
  check <ID>              Check task status
  list                    List all tasks

Examples:
  python task_automation_examples.py update TASK-100 已完成
  python task_automation_examples.py batch 待開始 進行中
  python task_automation_examples.py check TASK-100
  python task_automation_examples.py list

Status Options:
  - 待開始
  - 進行中
  - 待驗收
  - 已完成
  - 已阻塞
""")
        return

    command = sys.argv[1].lower()

    if command == "update" and len(sys.argv) == 4:
        update_single_task(sys.argv[2], sys.argv[3])

    elif command == "batch" and len(sys.argv) == 4:
        batch_update(sys.argv[2], sys.argv[3])

    elif command == "check" and len(sys.argv) == 3:
        check_task_status(sys.argv[2])

    elif command == "list":
        show_all_tasks()

    else:
        print("[ERROR] Invalid command or parameters")
        print("Run without arguments for usage help")

if __name__ == "__main__":
    main()
