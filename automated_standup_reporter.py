#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自動化每日站會報告生成器
一鍵生成完整的項目狀態報告
"""

import requests
import json
from datetime import datetime, timedelta

API_BASE = 'http://localhost:8000/tasks'

def get_all_tasks():
    """獲取所有任務"""
    response = requests.get(API_BASE)
    return response.json()

def generate_daily_report():
    """生成每日站會報告"""
    print(f"\n{'='*70}")
    print(f"           每日站會報告 - {datetime.now().strftime('%Y-%m-%d')}")
    print(f"{'='*70}\n")

    tasks = get_all_tasks()

    # 基本統計
    total = len(tasks)
    status_count = {}
    priority_count = {}

    for task in tasks:
        status = task.get('status', 'Unknown')
        priority = task.get('priority', 'N/A')

        status_count[status] = status_count.get(status, 0) + 1
        priority_count[priority] = priority_count.get(priority, 0) + 1

    # 打印報告
    print(f"📊 總體概況")
    print(f"{'-'*70}")
    print(f"  總任務數: {total}")
    print(f"  已完成: {status_count.get('已完成', 0)}")
    print(f"  進行中: {status_count.get('進行中', 0)}")
    print(f"  待開始: {status_count.get('待開始', 0)}")
    print(f"  已阻塞: {status_count.get('已阻塞', 0)}")

    # 完成率
    completed = status_count.get('已完成', 0)
    completion_rate = (completed / total) * 100
    print(f"  完成率: {completion_rate:.1f}%")
    print()

    print(f"📈 優先級分布")
    print(f"{'-'*70}")
    for priority in ['P0', 'P1', 'P2']:
        count = priority_count.get(priority, 0)
        pct = (count / total) * 100
        print(f"  {priority}: {count} ({pct:.1f}%)")
    print()

    print(f"🚧 需要關注的任務")
    print(f"{'-'*70}")

    # 已阻塞任務
    blocked = [t for t in tasks if t.get('status') == '已阻塞']
    if blocked:
        print(f"  已阻塞任務 ({len(blocked)} 個):")
        for task in blocked[:5]:
            print(f"    - {task.get('id')}: {task.get('title', 'N/A')}")
        if len(blocked) > 5:
            print(f"    ... 還有 {len(blocked) - 5} 個")
    else:
        print("  ✅ 沒有阻塞任務")

    # P0進行中任務
    p0_in_progress = [t for t in tasks if t.get('priority') == 'P0' and t.get('status') == '進行中']
    if p0_in_progress:
        print(f"\n  P0進行中任務 ({len(p0_in_progress)} 個):")
        for task in p0_in_progress[:5]:
            print(f"    - {task.get('id')}: {task.get('title', 'N/A')[:50]}")
        if len(p0_in_progress) > 5:
            print(f"    ... 還有 {len(p0_in_progress) - 5} 個")
    print()

    print(f"📅 今日行動項")
    print(f"{'-'*70}")

    # 今日新增任務
    # （這裡簡化處理，實際可以根據創建時間篩選）
    pending = [t for t in tasks if t.get('status') == '待開始']
    p0_pending = [t for t in pending if t.get('priority') == 'P0']

    if p0_pending:
        print(f"  1. 啟動 {len(p0_pending)} 個P0待開始任務")
        print(f"     (預估工時: {sum(t.get('estimated_hours', 0) for t in p0_pending)}h)")
    else:
        print("  1. 所有P0任務已啟動")

    # 完成率預測
    if completed > 0:
        avg_completion_rate = completion_rate / 30  # 假設30天週期
        predicted_completion = min(100, avg_completion_rate * 30)
        print(f"  2. 按當前進度，月底完成率預測: {predicted_completion:.1f}%")
    print()

    print(f"💡 建議")
    print(f"{'-'*70}")

    if blocked:
        print(f"  ⚠️  優先解決 {len(blocked)} 個阻塞任務")

    pending_count = status_count.get('待開始', 0)
    if pending_count > 20:
        print(f"  ⚡ {pending_count} 個待開始任務，建議批量啟動")

    p0_pending_count = len(p0_pending)
    if p0_pending_count > 5:
        print(f"  🎯 {p0_pending_count} 個P0待開始任務，需要分配資源")

    print()
    print(f"{'='*70}")
    print(f" 報告生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")

def generate_weekly_burndown():
    """生成週燃盡圖數據（簡化版）"""
    print(f"\n{'='*70}")
    print(f"           週燃盡圖數據")
    print(f"{'='*70}\n")

    tasks = get_all_tasks()
    total = len(tasks)
    completed = len([t for t in tasks if t.get('status') == '已完成'])

    # 假設的每日完成數據
    print("假設本週完成進度:")
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    remaining = total - completed

    for day in days:
        completed_today = max(0, min(5, remaining))  # 每天最多完成5個
        remaining -= completed_today
        print(f"  {day}: {total - remaining}/{total} 完成 (剩餘: {remaining})")

    if remaining > 0:
        print(f"\n⚠️  本週未能完成所有任務，剩餘: {remaining}")
    else:
        print(f"\n✅ 本週目標達成！")

if __name__ == '__main__':
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║            自動化項目管理工作流 v1.0                       ║
║              {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                    ║
╚═══════════════════════════════════════════════════════════╝
    """)

    # 生成每日報告
    generate_daily_report()

    # 生成週燃盡圖
    generate_weekly_burndown()

    print("\n" + "="*70)
    print(" 自動化報告生成完成")
    print("="*70 + "\n")
