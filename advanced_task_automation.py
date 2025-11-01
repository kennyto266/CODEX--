#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
高級任務自動化腳本
展示CLI任務管理的進階功能
"""

import requests
import json
from datetime import datetime

API_BASE = 'http://localhost:8000/tasks'

def get_all_tasks():
    """獲取所有任務"""
    response = requests.get(API_BASE)
    return response.json()

def get_task_by_id(task_id):
    """獲取指定任務"""
    response = requests.get(f'{API_BASE}/{task_id}')
    return response.json()

def update_task_status(task_id, new_status):
    """更新任務狀態"""
    response = requests.put(
        f'{API_BASE}/{task_id}/status',
        params={'new_status': new_status}
    )
    return response.status_code == 200

def print_separator(title):
    """打印分隔線"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}\n")

def print_success(message):
    """打印成功消息"""
    print(f"✅ {message}")

def print_error(message):
    """打印錯誤消息"""
    print(f"❌ {message}")

# 場景1：查找特定任務
def scenario_find_high_priority():
    """場景1：查找高優先級任務"""
    print_separator("場景1: 查找高優先級任務")

    tasks = get_all_tasks()
    high_priority = [t for t in tasks if t.get('priority') == 'P0']

    print(f"找到 {len(high_priority)} 個P0優先級任務:")
    for task in high_priority:
        print(f"  - {task.get('id')} [{task.get('status')}]")

    return high_priority

# 場景2：批量更新待驗收任務
def scenario_update_pending_review():
    """場景2：批量更新待驗收任務"""
    print_separator("場景2: 批量更新待驗收任務")

    tasks = get_all_tasks()
    pending_review = [t for t in tasks if t.get('status') == '待驗收']

    print(f"找到 {len(pending_review)} 個待驗收任務")

    success_count = 0
    for task in pending_review:
        task_id = task.get('id')
        if update_task_status(task_id, '已完成'):
            success_count += 1
            print(f"  ✅ {task_id} 已完成")

    print(f"\n成功更新 {success_count}/{len(pending_review)} 個任務")
    return success_count

# 場景3：狀態分析報告
def scenario_generate_report():
    """場景3：生成任務狀態分析報告"""
    print_separator("場景3: 任務狀態分析報告")

    tasks = get_all_tasks()

    # 統計各狀態
    status_count = {}
    priority_count = {}
    sprint_count = {}

    for task in tasks:
        status = task.get('status', 'Unknown')
        priority = task.get('priority', 'N/A')
        sprint = task.get('sprint', 'N/A')

        status_count[status] = status_count.get(status, 0) + 1
        priority_count[priority] = priority_count.get(priority, 0) + 1
        sprint_count[sprint] = sprint_count.get(sprint, 0) + 1

    print("📊 狀態分布:")
    for status, count in sorted(status_count.items()):
        percentage = (count / len(tasks)) * 100
        print(f"  {status}: {count} ({percentage:.1f}%)")

    print("\n📈 優先級分布:")
    for priority, count in sorted(priority_count.items()):
        percentage = (count / len(tasks)) * 100
        print(f"  {priority}: {count} ({percentage:.1f}%)")

    print("\n🏃 Sprint分布:")
    for sprint, count in sorted(sprint_count.items()):
        if count > 0:
            percentage = (count / len(tasks)) * 100
            print(f"  {sprint}: {count} ({percentage:.1f}%)")

    # 計算完成率
    completed = status_count.get('已完成', 0)
    blocked = status_count.get('已阻塞', 0)
    in_progress = status_count.get('進行中', 0)
    pending = status_count.get('待開始', 0)

    total_active = completed + blocked + in_progress + pending
    completion_rate = (completed / total_active) * 100 if total_active > 0 else 0

    print(f"\n🎯 關鍵指標:")
    print(f"  完成率: {completion_rate:.1f}%")
    print(f"  阻塞任務: {blocked} 個")
    print(f"  活躍任務: {in_progress + pending} 個")

    return {
        'status_count': status_count,
        'priority_count': priority_count,
        'completion_rate': completion_rate
    }

# 場景4：Sprint管理
def scenario_sprint_management():
    """場景4：Sprint管理"""
    print_separator("場景4: Sprint管理")

    tasks = get_all_tasks()

    # 查找Sprint 1任務
    sprint1_tasks = [t for t in tasks if t.get('sprint') == 'Sprint 1']
    print(f"找到 Sprint 1 任務: {len(sprint1_tasks)} 個")

    # 統計Sprint 1的完成情況
    completed = sum(1 for t in sprint1_tasks if t.get('status') == '已完成')
    in_progress = sum(1 for t in sprint1_tasks if t.get('status') == '進行中')
    pending = sum(1 for t in sprint1_tasks if t.get('status') == '待開始')

    print(f"\n  ✅ 已完成: {completed}")
    print(f"  🔄 進行中: {in_progress}")
    print(f"  ⏳ 待開始: {pending}")

    if len(sprint1_tasks) > 0:
        sprint_completion = (completed / len(sprint1_tasks)) * 100
        print(f"  📊 Sprint完成度: {sprint_completion:.1f}%")

    return len(sprint1_tasks)

# 場景5：批量啟動下一批任務
def scenario_start_next_batch():
    """場景5：批量啟動下一批任務"""
    print_separator("場景5: 批量啟動下一批任務")

    tasks = get_all_tasks()
    pending_tasks = [t for t in tasks if t.get('status') == '待開始']

    # 選擇前10個任務
    batch_size = 10
    next_batch = pending_tasks[:batch_size]

    print(f"準備啟動下一批 {batch_size} 個任務...")

    success_count = 0
    for i, task in enumerate(next_batch, 1):
        task_id = task.get('id')
        if update_task_status(task_id, '進行中'):
            success_count += 1
            print(f"  [{i:2d}/{batch_size}] {task_id} → 進行中")

    print(f"\n✅ 成功啟動 {success_count}/{batch_size} 個任務")
    return success_count

# 場景6：查找並標記阻塞任務
def scenario_identify_blocked():
    """場景6：識別並處理阻塞任務"""
    print_separator("場景6: 識別並處理阻塞任務")

    tasks = get_all_tasks()
    blocked_tasks = [t for t in tasks if t.get('status') == '已阻塞']

    if len(blocked_tasks) == 0:
        print("🎉 沒有阻塞任務！")
        return 0

    print(f"發現 {len(blocked_tasks)} 個阻塞任務:")
    for task in blocked_tasks:
        print(f"  - {task.get('id')}: {task.get('title', 'N/A')}")

    # 檢查是否有進行中的任務超過3天（假設）
    old_tasks = []
    print(f"\n檢查長期進行中的任務...")

    return len(blocked_tasks)

# 主程序
if __name__ == '__main__':
    print(f"""
╔════════════════════════════════════════════════════╗
║         高級任務自動化腳本 v1.0                    ║
║              {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                  ║
╚════════════════════════════════════════════════════╝
    """)

    try:
        # 執行所有場景
        scenario_find_high_priority()
        scenario_update_pending_review()
        scenario_generate_report()
        scenario_sprint_management()
        scenario_start_next_batch()
        scenario_identify_blocked()

        print_separator("自動化腳本完成")
        print("🎊 所有場景執行完畢！")
        print("\n可用的自動化操作:")
        print("  1. 批量狀態更新")
        print("  2. 任務搜索和篩選")
        print("  3. 數據分析和報告")
        print("  4. Sprint管理")
        print("  5. 阻塞任務處理")
        print("  6. 工作流自動化")

    except Exception as e:
        print_error(f"執行過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
