#!/usr/bin/env python3
"""
修復版任務導入腳本
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime

def parse_tasks_from_md(file_path):
    """解析Markdown文件中的任務"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    tasks = []
    lines = content.split('\n')
    task_id = 100

    for line in lines:
        # 檢查是否為任務行: - [ ] 或 - [x]
        if '- [' in line and ('創建' in line or '重構' in line or '實現' in line or '添加' in line or '更新' in line or '測試' in line or '配置' in line):
            # 提取優先級
            priority = 'P2'
            if '[P0]' in line:
                priority = 'P0'
            elif '[P1]' in line:
                priority = 'P1'

            # 提取任務標題（去掉 - [ ] 和優先級標記）
            title = line.split('] ', 1)[-1].split(' [P')[0].strip()

            # 提取階段
            stage = '階段1'
            if '### 2.' in line or '階段2' in line:
                stage = '階段2'
            elif '### 3.' in line or '階段3' in line:
                stage = '階段3'
            elif '### 4.' in line or '階段4' in line:
                stage = '階段4'
            elif '### 5.' in line or '階段5' in line:
                stage = '階段5'

            # 提取預估時間
            estimated_hours = 3
            if '6小時' in line or '8小時' in line:
                estimated_hours = 6
            elif '4小時' in line or '3小時' in line:
                estimated_hours = 3

            tasks.append({
                'id': f'TASK-{task_id:03d}',
                'title': title,
                'description': f'{stage} - {title}',
                'status': '待開始',
                'priority': priority,
                'estimated_hours': estimated_hours,
                'assignee': None,
                'reporter': '系統管理員',
                'stage': stage,
                'section': '總任務',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'story_points': 1,
                'progress_percentage': 0,
                'is_blocked': 0,
                'is_completed': 0
            })

            task_id += 1

    return tasks

def import_tasks_to_db(tasks, conn):
    """將任務導入數據庫"""
    cursor = conn.cursor()

    imported = 0
    skipped = 0

    for task in tasks:
        try:
            # 檢查是否已存在
            cursor.execute('SELECT id FROM tasks WHERE id = ?', (task['id'],))
            if cursor.fetchone():
                skipped += 1
                continue

            # 插入任務 - 使用正確的列名
            cursor.execute('''
                INSERT INTO tasks (
                    id, title, description, status, priority,
                    estimated_hours, assignee, reporter,
                    stage, section, created_at, updated_at,
                    story_points, progress_percentage, is_blocked, is_completed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task['id'],
                task['title'],
                task['description'],
                task['status'],
                task['priority'],
                task['estimated_hours'],
                task['assignee'],
                task['reporter'],
                task['stage'],
                task['section'],
                task['created_at'],
                task['updated_at'],
                task['story_points'],
                task['progress_percentage'],
                task['is_blocked'],
                task['is_completed']
            ))

            imported += 1

        except Exception as e:
            print(f"導入任務 {task['id']} 失敗: {e}")
            skipped += 1

    conn.commit()
    return imported, skipped

def verify_import(conn):
    """驗證導入結果"""
    cursor = conn.cursor()
    
    # 統計各狀態任務數
    cursor.execute('SELECT status, COUNT(*) FROM tasks GROUP BY status')
    status_counts = dict(cursor.fetchall())
    
    # 統計優先級
    cursor.execute('SELECT priority, COUNT(*) FROM tasks GROUP BY priority')
    priority_counts = dict(cursor.fetchall())
    
    # 統計階段
    cursor.execute('SELECT stage, COUNT(*) FROM tasks GROUP BY stage')
    stage_counts = dict(cursor.fetchall())
    
    return {
        'status': status_counts,
        'priority': priority_counts,
        'stage': stage_counts
    }

def main():
    """主函數"""
    print("="*60)
    print("[修復版] 任務導入系統")
    print("="*60)

    # 解析任務
    print("\n1. 解析任務清單...")
    tasks = parse_tasks_from_md('openspec/changes/optimize-project-plan/tasks.md')
    print(f"   找到 {len(tasks)} 個任務")

    # 連接數據庫
    print("\n2. 連接數據庫...")
    conn = sqlite3.connect('tasks.db')
    print("   數據庫已連接: tasks.db")

    # 導入任務
    print("\n3. 導入任務到數據庫...")
    imported, skipped = import_tasks_to_db(tasks, conn)
    print(f"   成功導入: {imported} 個")
    print(f"   跳過: {skipped} 個")

    # 驗證導入
    print("\n4. 驗證導入結果...")
    stats = verify_import(conn)
    
    print("\n狀態分布:")
    for status, count in stats['status'].items():
        print(f"  {status}: {count} 個")
    
    print("\n優先級分布:")
    for priority, count in stats['priority'].items():
        print(f"  {priority}: {count} 個")
    
    print("\n階段分布:")
    for stage, count in stats['stage'].items():
        print(f"  {stage}: {count} 個")

    print("\n" + "="*60)
    print("[完成] 任務導入成功！")
    print("="*60)
    
    print("\n可用的任務查看方式:")
    print("1. 數據庫查詢:")
    print("   sqlite3 tasks.db 'SELECT id, title, status, priority FROM tasks LIMIT 10;'")
    print("\n2. 前端看板:")
    print("   http://localhost:8001/task-board-demo.html")
    print("\n3. API接口:")
    print("   http://localhost:8001/docs")
    
    conn.close()
    return True

if __name__ == '__main__':
    main()
