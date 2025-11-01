#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Advanced Task Automation Script
Demonstrates advanced CLI task management features
"""

import requests
import json
from datetime import datetime

API_BASE = 'http://localhost:8000/tasks'

def get_all_tasks():
    """Get all tasks"""
    response = requests.get(API_BASE)
    return response.json()

def update_task_status(task_id, new_status):
    """Update task status"""
    response = requests.put(
        f'{API_BASE}/{task_id}/status',
        params={'new_status': new_status}
    )
    return response.status_code == 200

def print_header(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}\n")

def print_success(message):
    print(f"[SUCCESS] {message}")

def print_info(message):
    print(f"[INFO] {message}")

# Scenario 1: Batch update pending review tasks
def demo_batch_complete():
    """Demo: Batch complete pending review tasks"""
    print_header("Demo 1: Batch Complete Pending Review Tasks")

    tasks = get_all_tasks()
    pending_review = [t for t in tasks if t.get('status') == '待驗收']

    print(f"Found {len(pending_review)} pending review tasks")

    success_count = 0
    for task in pending_review:
        task_id = task.get('id')
        if update_task_status(task_id, '已完成'):
            success_count += 1
            print(f"  - {task_id} -> Completed")

    print_success(f"Updated {success_count}/{len(pending_review)} tasks to Completed")
    return success_count

# Scenario 2: Task Statistics Analysis
def demo_statistics():
    """Demo: Generate task statistics"""
    print_header("Demo 2: Task Statistics Analysis")

    tasks = get_all_tasks()

    status_count = {}
    priority_count = {}

    for task in tasks:
        status = task.get('status', 'Unknown')
        priority = task.get('priority', 'N/A')

        status_count[status] = status_count.get(status, 0) + 1
        priority_count[priority] = priority_count.get(priority, 0) + 1

    print("Status Distribution:")
    for status, count in sorted(status_count.items()):
        percentage = (count / len(tasks)) * 100
        print(f"  {status}: {count} ({percentage:.1f}%)")

    print("\nPriority Distribution:")
    for priority, count in sorted(priority_count.items()):
        percentage = (count / len(tasks)) * 100
        print(f"  {priority}: {count} ({percentage:.1f}%)")

    # Calculate completion rate
    completed = status_count.get('已完成', 0)
    total = len(tasks)
    completion_rate = (completed / total) * 100

    print(f"\nKey Metrics:")
    print(f"  Total Tasks: {total}")
    print(f"  Completion Rate: {completion_rate:.1f}%")
    print(f"  In Progress: {status_count.get('進行中', 0)}")
    print(f"  Pending: {status_count.get('待開始', 0)}")

    return status_count

# Scenario 3: Sprint Management
def demo_sprint_management():
    """Demo: Sprint management"""
    print_header("Demo 3: Sprint Management")

    tasks = get_all_tasks()

    # Find Sprint 1 tasks
    sprint1_tasks = [t for t in tasks if t.get('sprint') == 'Sprint 1']
    print(f"Sprint 1 Tasks: {len(sprint1_tasks)}")

    if len(sprint1_tasks) > 0:
        completed = sum(1 for t in sprint1_tasks if t.get('status') == '已完成')
        in_progress = sum(1 for t in sprint1_tasks if t.get('status') == '進行中')
        pending = sum(1 for t in sprint1_tasks if t.get('status') == '待開始')

        print(f"\n  Completed: {completed}")
        print(f"  In Progress: {in_progress}")
        print(f"  Pending: {pending}")

        sprint_completion = (completed / len(sprint1_tasks)) * 100
        print(f"\n  Sprint Completion: {sprint_completion:.1f}%")

    return len(sprint1_tasks)

# Scenario 4: Start Next Batch
def demo_start_next_batch():
    """Demo: Start next batch of tasks"""
    print_header("Demo 4: Start Next Batch of Tasks")

    tasks = get_all_tasks()
    pending_tasks = [t for t in tasks if t.get('status') == '待開始']

    # Select next 10 tasks
    batch_size = 10
    next_batch = pending_tasks[:batch_size]

    print(f"Starting next batch of {batch_size} tasks...")

    success_count = 0
    for i, task in enumerate(next_batch, 1):
        task_id = task.get('id')
        if update_task_status(task_id, '進行中'):
            success_count += 1
            print(f"  [{i:2d}/{batch_size}] {task_id} -> In Progress")

    print_success(f"Successfully started {success_count}/{batch_size} tasks")
    return success_count

# Scenario 5: Identify Blocked Tasks
def demo_identify_blocked():
    """Demo: Identify blocked tasks"""
    print_header("Demo 5: Identify Blocked Tasks")

    tasks = get_all_tasks()
    blocked_tasks = [t for t in tasks if t.get('status') == '已阻塞']

    if len(blocked_tasks) == 0:
        print("No blocked tasks found!")
        return 0

    print(f"Found {len(blocked_tasks)} blocked tasks:")
    for task in blocked_tasks:
        print(f"  - {task.get('id')}: {task.get('title', 'N/A')}")

    return len(blocked_tasks)

# Scenario 6: High Priority Tasks
def demo_high_priority():
    """Demo: Find high priority tasks"""
    print_header("Demo 6: Find High Priority Tasks")

    tasks = get_all_tasks()
    high_priority = [t for t in tasks if t.get('priority') == 'P0']

    print(f"Found {len(high_priority)} P0 priority tasks:")

    # Group by status
    p0_by_status = {}
    for task in high_priority:
        status = task.get('status', 'Unknown')
        if status not in p0_by_status:
            p0_by_status[status] = []
        p0_by_status[status].append(task.get('id'))

    for status, task_ids in p0_by_status.items():
        print(f"\n  {status} ({len(task_ids)} tasks):")
        for tid in task_ids[:5]:  # Show first 5
            print(f"    - {tid}")
        if len(task_ids) > 5:
            print(f"    ... and {len(task_ids) - 5} more")

    return len(high_priority)

# Main Program
if __name__ == '__main__':
    print(f"""
+--------------------------------------------------------+
|        Advanced Task Automation Script v1.0           |
|              {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                  |
+--------------------------------------------------------+
    """)

    try:
        # Execute all demos
        demo_batch_complete()
        demo_statistics()
        demo_sprint_management()
        demo_start_next_batch()
        demo_identify_blocked()
        demo_high_priority()

        print_header("Automation Script Complete")
        print("All demos executed successfully!\n")
        print("Available automation features:")
        print("  1. Batch Status Updates")
        print("  2. Task Search & Filter")
        print("  3. Data Analysis & Reports")
        print("  4. Sprint Management")
        print("  5. Blocked Task Handling")
        print("  6. Priority-based Operations")
        print("  7. Workflow Automation")

    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
        import traceback
        traceback.print_exc()
