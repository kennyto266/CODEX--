#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自動任務狀態更新腳本
用於在CLI中自動更新任務狀態，支持單個更新和批量更新
"""

import requests
import json
import sys
from typing import List, Dict, Optional

# 設置UTF-8編碼
import codecs
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

# API基礎URL
BASE_URL = "http://localhost:8000"

class TaskUpdater:
    def __init__(self):
        self.base_url = BASE_URL

    def get_all_tasks(self) -> List[Dict]:
        """獲取所有任務"""
        response = requests.get(f"{self.base_url}/tasks")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ 獲取任務失敗: HTTP {response.status_code}")
            return []

    def get_task(self, task_id: str) -> Optional[Dict]:
        """獲取特定任務"""
        response = requests.get(f"{self.base_url}/tasks/{task_id}")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ 獲取任務 {task_id} 失敗: HTTP {response.status_code}")
            return None

    def update_task_status(self, task_id: str, new_status: str) -> bool:
        """更新任務狀態"""
        response = requests.put(
            f"{self.base_url}/tasks/{task_id}/status",
            params={"new_status": new_status}
        )

        if response.status_code == 200:
            updated_task = response.json()
            print(f"✅ 任務 {task_id} 狀態已更新為: {new_status}")
            print(f"   標題: {updated_task.get('title', 'N/A')}")
            return True
        else:
            print(f"❌ 更新任務 {task_id} 失敗: HTTP {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   錯誤: {error_detail}")
            except:
                print(f"   響應: {response.text}")
            return False

    def batch_update_by_status(self, from_status: str, to_status: str) -> int:
        """批量更新指定狀態的所有任務"""
        tasks = self.get_all_tasks()
        target_tasks = [t for t in tasks if t.get('status') == from_status]

        if not target_tasks:
            print(f"⚠️  沒有找到狀態為 '{from_status}' 的任務")
            return 0

        print(f"\n📋 找到 {len(target_tasks)} 個狀態為 '{from_status}' 的任務")
        print(f"   將更新為: '{to_status}'")

        success_count = 0
        for task in target_tasks:
            task_id = task.get('id')
            if self.update_task_status(task_id, to_status):
                success_count += 1

        print(f"\n✅ 批量更新完成: {success_count}/{len(target_tasks)} 成功")
        return success_count

    def batch_update_by_ids(self, task_ids: List[str], to_status: str) -> int:
        """批量更新指定ID的任務"""
        print(f"\n📋 將更新 {len(task_ids)} 個任務為狀態: '{to_status}'")

        success_count = 0
        for task_id in task_ids:
            if self.update_task_status(task_id, to_status):
                success_count += 1

        print(f"\n✅ 批量更新完成: {success_count}/{len(task_ids)} 成功")
        return success_count

    def show_task_stats(self):
        """顯示任務統計"""
        tasks = self.get_all_tasks()
        if not tasks:
            return

        status_counts = {}
        for task in tasks:
            status = task.get('status', 'Unknown')
            status_counts[status] = status_counts.get(status, 0) + 1

        print("\n📊 任務狀態統計:")
        print("=" * 50)
        for status, count in sorted(status_counts.items()):
            percentage = (count / len(tasks)) * 100
            print(f"  {status:12s}: {count:3d} 個 ({percentage:5.1f}%)")

        print("=" * 50)
        print(f"  {'總計':12s}: {len(tasks):3d} 個 (100.0%)")

        completed = sum(1 for t in tasks if t.get('is_completed'))
        print(f"\n🎯 完成率: {completed}/{len(tasks)} ({(completed/len(tasks)*100):.1f}%)")

def print_usage():
    """打印使用說明"""
    print("""
🤖 自動任務狀態更新工具

使用方法:
  python auto_update_tasks.py stats                    # 顯示任務統計
  python auto_update_tasks.py update <ID> <STATUS>    # 更新單個任務
  python auto_update_tasks.py batch <FROM> <TO>       # 批量更新同狀態任務
  python auto_update_tasks.py ids <ID1,ID2,...> <STATUS>  # 批量更新指定ID

示例:
  python auto_update_tasks.py stats
  python auto_update_tasks.py update TASK-100 已完成
  python auto_update_tasks.py batch 待開始 進行中
  python auto_update_tasks.py ids TASK-100,TASK-101,TASK-102 已完成

支持的狀態:
  - 待開始
  - 進行中
  - 待驗收
  - 已完成
  - 已阻塞
""")

def main():
    updater = TaskUpdater()

    if len(sys.argv) < 2:
        print_usage()
        return

    command = sys.argv[1].lower()

    if command == "stats":
        updater.show_task_stats()

    elif command == "update" and len(sys.argv) == 4:
        task_id = sys.argv[2]
        new_status = sys.argv[3]
        updater.update_task_status(task_id, new_status)

    elif command == "batch" and len(sys.argv) == 4:
        from_status = sys.argv[2]
        to_status = sys.argv[3]
        updater.batch_update_by_status(from_status, to_status)

    elif command == "ids" and len(sys.argv) == 4:
        task_ids_str = sys.argv[2]
        to_status = sys.argv[3]
        task_ids = [tid.strip() for tid in task_ids_str.split(',')]
        updater.batch_update_by_ids(task_ids, to_status)

    else:
        print("❌ 無效的命令或參數不足")
        print_usage()

if __name__ == "__main__":
    main()
