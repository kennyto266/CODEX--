#!/usr/bin/env python3
"""
快速啟動任務管理系統
導入任務並展示系統功能
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
                'status': 'TODO',
                'priority': priority,
                'estimated_hours': estimated_hours,
                'assignee': None,
                'reporter': '系統管理員',
                'stage': stage,
                'created_at': datetime.utcnow().isoformat()
            })

            task_id += 1

    return tasks

def init_database():
    """初始化SQLite數據庫"""
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()

    # 創建任務表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL,
            priority TEXT NOT NULL,
            estimated_hours INTEGER,
            actual_hours INTEGER,
            assignee TEXT,
            reporter TEXT NOT NULL,
            sprint TEXT,
            story_points INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT,
            completed_at TEXT,
            metadata TEXT
        )
    ''')

    # 創建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON tasks(assignee)')

    conn.commit()
    return conn

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

            # 插入任務
            cursor.execute('''
                INSERT INTO tasks (
                    id, title, description, status, priority,
                    estimated_hours, assignee, reporter,
                    created_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task['id'],
                task['title'],
                task['description'],
                task['status'],
                task['priority'],
                task['estimated_hours'],
                task['assignee'],
                task['reporter'],
                task['created_at'],
                json.dumps({'stage': task['stage']})
            ))

            imported += 1

        except Exception as e:
            print(f"導入任務 {task['id']} 失敗: {e}")
            skipped += 1

    conn.commit()
    return imported, skipped

def generate_summary(tasks, imported, skipped):
    """生成導入摘要"""
    total = len(tasks)
    p0_count = sum(1 for t in tasks if t['priority'] == 'P0')
    p1_count = sum(1 for t in tasks if t['priority'] == 'P1')
    p2_count = sum(1 for t in tasks if t['priority'] == 'P2')

    summary = f"""
============================================================
[導入完成] 任務數據
============================================================

總任務數: {total}
成功導入: {imported}
跳過/已存在: {skipped}

優先級分布:
  P0 (關鍵路徑): {p0_count} 個 ({p0_count/total*100:.1f}%)
  P1 (重要): {p1_count} 個 ({p1_count/total*100:.1f}%)
  P2 (一般): {p2_count} 個 ({p2_count/total*100:.1f}%)

階段分布:
"""

    stages = {}
    for task in tasks:
        stage = task.get('stage', '未知')
        stages[stage] = stages.get(stage, 0) + 1

    for stage, count in stages.items():
        summary += f"  {stage}: {count} 個\n"

    summary += f"""
============================================================
[系統信息]
============================================================

數據庫: tasks.db
任務看板: http://localhost:8001/task-board-demo.html
API文檔: http://localhost:8001/docs

下一步:
1. 訪問任務看板查看任務
2. 使用API創建、分配、轉換任務
3. 開始管理實際項目任務
"""

    return summary

def main():
    """主函數"""
    print("="*60)
    print("[啟動] 任務管理系統")
    print("="*60)

    # 解析任務
    print("\n1. 解析任務清單...")
    tasks = parse_tasks_from_md('openspec/changes/optimize-project-plan/tasks.md')
    print(f"   找到 {len(tasks)} 個任務")

    # 初始化數據庫
    print("\n2. 初始化數據庫...")
    conn = init_database()
    print("   數據庫已準備: tasks.db")

    # 導入任務
    print("\n3. 導入任務到數據庫...")
    imported, skipped = import_tasks_to_db(tasks, conn)
    print(f"   成功導入: {imported} 個")
    print(f"   跳過: {skipped} 個")

    # 生成摘要
    print("\n4. 生成導入摘要...")
    summary = generate_summary(tasks, imported, skipped)
    print(summary)

    # 保存摘要到文件
    with open('TASK_IMPORT_SUMMARY.txt', 'w', encoding='utf-8') as f:
        f.write(summary)

    print("\n[完成] 任務導入完成！")
    print("="*60)
    
    conn.close()
    return True

if __name__ == '__main__':
    main()
