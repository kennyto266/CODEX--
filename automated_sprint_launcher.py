#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自動化Sprint啟動腳本
一鍵啟動整個Sprint的所有任務
"""

import requests
import json
from datetime import datetime, timedelta

API_BASE = 'http://localhost:8000/tasks'

def get_all_tasks():
    """獲取所有任務"""
    response = requests.get(API_BASE)
    return response.json()

def update_task_status(task_id, new_status):
    """更新任務狀態"""
    response = requests.put(
        f'{API_BASE}/{task_id}/status',
        params={'new_status': new_status}
    )
    return response.status_code == 200

def launch_sprint(sprint_name):
    """啟動指定Sprint"""
    print(f"\n{'='*60}")
    print(f" 自動化 Sprint 啟動器")
    print(f" Sprint: {sprint_name}")
    print(f"{'='*60}\n")

    tasks = get_all_tasks()
    sprint_tasks = [t for t in tasks if t.get('sprint') == sprint_name]

    if not sprint_tasks:
        print(f"未找到Sprint '{sprint_name}'的任務")
        return

    print(f"找到 {len(sprint_tasks)} 個Sprint任務")
    print()

    # 分組統計
    status_groups = {}
    for task in sprint_tasks:
        status = task.get('status')
        if status not in status_groups:
            status_groups[status] = []
        status_groups[status].append(task)

    print("當前狀態分布:")
    for status, task_list in status_groups.items():
        print(f"  {status}: {len(task_list)} 個")
    print()

    # 啟動所有待開始的任務
    pending = [t for t in sprint_tasks if t.get('status') == '待開始']
    if not pending:
        print("所有任務已經啟動")
        return

    print(f"啟動 {len(pending)} 個待開始任務...")
    success_count = 0

    for i, task in enumerate(pending, 1):
        task_id = task.get('id')
        if update_task_status(task_id, '進行中'):
            success_count += 1
            print(f"  [{i:2d}/{len(pending)}] {task_id} -> 進行中")

    print()
    print(f"[成功] Sprint '{sprint_name}' 已啟動 {success_count}/{len(pending)} 任務")

    # 啟動後統計
    remaining = len(sprint_tasks) - success_count
    print(f"\nSprint進度:")
    print(f"  總任務: {len(sprint_tasks)}")
    print(f"  已啟動: {success_count}")
    print(f"  剩餘: {remaining}")

def generate_sprint_report(sprint_name):
    """生成Sprint報告"""
    print(f"\n{'='*60}")
    print(f" Sprint 報告: {sprint_name}")
    print(f"{'='*60}\n")

    tasks = get_all_tasks()
    sprint_tasks = [t for t in tasks if t.get('sprint') == sprint_name]

    if not sprint_tasks:
        print(f"未找到Sprint '{sprint_name}'的任務")
        return

    # 統計
    status_count = {}
    priority_count = {}
    total_estimated = 0
    total_actual = 0

    for task in sprint_tasks:
        status = task.get('status')
        priority = task.get('priority')
        estimated = task.get('estimated_hours', 0)
        actual = task.get('actual_hours', 0)

        status_count[status] = status_count.get(status, 0) + 1
        priority_count[priority] = priority_count.get(priority, 0) + 1
        total_estimated += estimated
        total_actual += actual

    print(f"總任務數: {len(sprint_tasks)}")
    print(f"預估工時: {total_estimated}h")
    print(f"實際工時: {total_actual}h")
    print()

    print("狀態分布:")
    for status, count in sorted(status_count.items()):
        pct = (count / len(sprint_tasks)) * 100
        print(f"  {status}: {count} ({pct:.1f}%)")
    print()

    print("優先級分布:")
    for priority, count in sorted(priority_count.items()):
        pct = (count / len(sprint_tasks)) * 100
        print(f"  {priority}: {count} ({pct:.1f}%)")

    # 計算完成率
    completed = status_count.get('已完成', 0)
    completion_rate = (completed / len(sprint_tasks)) * 100
    print(f"\n完成率: {completion_rate:.1f}%")

    # 估算剩餘時間
    if completed > 0 and total_actual > 0:
        avg_per_task = total_actual / completed
        remaining_tasks = len(sprint_tasks) - completed
        estimated_remaining = remaining_tasks * avg_per_task
        print(f"預估剩餘時間: {estimated_remaining:.1f}h")

if __name__ == '__main__':
    print(f"""
╔════════════════════════════════════════════════════╗
║          自動化 Sprint 管理工具 v1.0               ║
║              {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                  ║
╚════════════════════════════════════════════════════╝
    """)

    # 啟動Sprint
    sprint_name = "SPRINT-2025-10"
    launch_sprint(sprint_name)

    # 生成報告
    generate_sprint_report(sprint_name)

    print(f"\n{'='*60}")
    print(" 自動化Sprint管理完成")
    print(f"{'='*60}\n")
