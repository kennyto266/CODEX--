#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日常自動化腳本
每日自動執行的項目管理任務
"""

import requests
import json
from datetime import datetime

API_BASE = 'http://localhost:8000/tasks'

def get_tasks():
    """獲取所有任務"""
    response = requests.get(API_BASE)
    return response.json()

def update_task(task_id, status):
    """更新任務狀態"""
    response = requests.put(
        f'{API_BASE}/{task_id}/status',
        params={'new_status': status}
    )
    return response.status_code == 200

def daily_automation():
    """每日自動化流程"""
    print(f"\n{'='*60}")
    print(f" Daily Automation - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")

    tasks = get_tasks()

    # 1. 生成狀態報告
    print("1. GENERATING STATUS REPORT")
    print("-" * 60)

    status_count = {}
    priority_count = {}

    for task in tasks:
        status = task.get('status', 'Unknown')
        priority = task.get('priority', 'N/A')

        status_count[status] = status_count.get(status, 0) + 1
        priority_count[priority] = priority_count.get(priority, 0) + 1

    print(f"Total Tasks: {len(tasks)}")
    for status, count in sorted(status_count.items()):
        print(f"  {status}: {count}")
    print()

    # 2. 檢查阻塞任務
    print("2. CHECKING BLOCKED TASKS")
    print("-" * 60)

    blocked = [t for t in tasks if 'blocked' in t.get('status', '').lower() or 'block' in t.get('status', '').lower()]

    if blocked:
        print(f"Found {len(blocked)} blocked tasks:")
        for task in blocked[:5]:
            print(f"  - {task.get('id')}: {task.get('title', 'N/A')}")
    else:
        print("No blocked tasks found")
    print()

    # 3. 完成率計算
    print("3. COMPLETION METRICS")
    print("-" * 60)

    completed = status_count.get('已完成', 0)
    completion_rate = (completed / len(tasks)) * 100
    print(f"Completed: {completed}/{len(tasks)} ({completion_rate:.1f}%)")

    if completion_rate < 50:
        print("WARNING: Completion rate below 50%")
    elif completion_rate > 80:
        print("GREAT: Completion rate above 80%")
    print()

    # 4. P0任務狀態
    print("4. P0 TASKS STATUS")
    print("-" * 60)

    p0_tasks = [t for t in tasks if t.get('priority') == 'P0']
    p0_completed = len([t for t in p0_tasks if 'done' in t.get('status', '').lower()])
    p0_in_progress = len([t for t in p0_tasks if 'progress' in t.get('status', '').lower()])

    print(f"P0 Tasks: {len(p0_tasks)}")
    print(f"  Completed: {p0_completed}")
    print(f"  In Progress: {p0_in_progress}")
    print(f"  Pending: {len(p0_tasks) - p0_completed - p0_in_progress}")
    print()

    # 5. 自動化建議
    print("5. AUTOMATION RECOMMENDATIONS")
    print("-" * 60)

    pending_count = len(tasks) - completed
    if pending_count > 20:
        print(f"RECOMMENDATION: {pending_count} tasks pending")
        print("ACTION: Batch start high-priority tasks")

    blocked_count = len(blocked)
    if blocked_count > 0:
        print(f"RECOMMENDATION: {blocked_count} tasks blocked")
        print("ACTION: Review and resolve blockers")

    print()

    return {
        'total': len(tasks),
        'completed': completed,
        'pending': pending_count,
        'blocked': blocked_count,
        'completion_rate': completion_rate
    }

def weekly_report():
    """週報告"""
    print(f"\n{'='*60}")
    print(f" WEEKLY REPORT - {datetime.now().strftime('%Y-%m-%d')}")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    # 執行每日自動化
    stats = daily_automation()

    # 輸出總結
    print("="*60)
    print(" AUTOMATION COMPLETE")
    print("="*60)
    print(f"Tasks: {stats['total']}")
    print(f"Completed: {stats['completed']}")
    print(f"Pending: {stats['pending']}")
    print(f"Completion Rate: {stats['completion_rate']:.1f}%")
    print()
