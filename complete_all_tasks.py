#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量完成所有任务脚本
将所有100个任务的状态更新为"已完成"
"""

import requests
import json
import sys
from datetime import datetime

API_BASE = 'http://localhost:8000/tasks'

def get_all_tasks():
    """获取所有任务"""
    try:
        response = requests.get(API_BASE, timeout=10)
        return response.json()
    except Exception as e:
        print(f"ERROR: Failed to fetch tasks: {e}")
        return []

def update_task_status(task_id, new_status):
    """更新任务状态"""
    try:
        response = requests.put(
            f'{API_BASE}/{task_id}/status',
            params={'new_status': new_status},
            timeout=5
        )
        return response.status_code == 200, response.status_code
    except Exception as e:
        print(f"ERROR updating {task_id}: {e}")
        return False, 500

def complete_all_tasks():
    """完成所有任务"""
    print(f"\n{'='*70}")
    print(f" COMPLETE ALL TASKS AUTOMATION")
    print(f" Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")

    # 获取所有任务
    print("[1/3] Fetching all tasks...")
    tasks = get_all_tasks()

    if not tasks:
        print("FATAL: No tasks found or API connection failed")
        return False

    print(f"    Total tasks found: {len(tasks)}")

    # 分析当前状态
    print("\n[2/3] Analyzing current status...")
    status_count = {}
    for task in tasks:
        status = task.get('status', 'Unknown')
        status_count[status] = status_count.get(status, 0) + 1

    print("    Current status distribution:")
    for status, count in sorted(status_count.items()):
        print(f"      {status}: {count}")

    # 开始批量完成
    print("\n[3/3] Completing all tasks...")
    print("    This will update ALL tasks to '已完成' status")
    print("    Progress: ")

    success_count = 0
    failed_count = 0
    total = len(tasks)

    # 分批处理以显示进度
    batch_size = 10
    for i in range(0, total, batch_size):
        batch = tasks[i:i+batch_size]

        for j, task in enumerate(batch, i + 1):
            task_id = task.get('id')
            current_status = task.get('status')

            success, status_code = update_task_status(task_id, '已完成')

            if success:
                success_count += 1
                if j % 10 == 0 or j <= 5:
                    print(f"      [{j:3d}/{total}] {task_id} ({current_status}) -> 已完成")
            else:
                failed_count += 1
                print(f"      [{j:3d}/{total}] {task_id} FAILED (status: {status_code})")

    # 生成完成报告
    print(f"\n{'='*70}")
    print(f" COMPLETION SUMMARY")
    print(f" End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")
    print(f" Total Tasks: {total}")
    print(f" Successfully Completed: {success_count}")
    print(f" Failed: {failed_count}")
    print(f" Success Rate: {(success_count/total*100):.1f}%")

    if failed_count == 0:
        print(f"\n✅ ALL TASKS COMPLETED SUCCESSFULLY!")
    else:
        print(f"\n⚠️  Completed with {failed_count} failures")

    # 保存完成报告
    report = f"""
COMPLETE ALL TASKS REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Tasks: {total}
Successfully Completed: {success_count}
Failed: {failed_count}
Success Rate: {(success_count/total*100):.1f}%

Status Distribution (After Completion):
  已完成: {success_count} (expected: {total})
  Failed: {failed_count}
"""

    with open(f'complete_all_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt', 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\nReport saved to: complete_all_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    print(f"{'='*70}\n")

    return success_count == total

if __name__ == '__main__':
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║        BATCH COMPLETE ALL TASKS AUTOMATION v1.0              ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

⚠️  WARNING: This will mark ALL tasks as completed!
   Press Ctrl+C to cancel or wait 3 seconds to continue...
    """)

    import time
    time.sleep(3)

    success = complete_all_tasks()

    if success:
        print("🎉 Mission Accomplished: All tasks completed!")
        sys.exit(0)
    else:
        print("❌ Some tasks failed to complete")
        sys.exit(1)
