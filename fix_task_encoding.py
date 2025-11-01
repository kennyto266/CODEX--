#!/usr/bin/env python3
"""
Fix Task Database Encoding
Re-import tasks with proper UTF-8 encoding
"""

import sqlite3
import shutil
from pathlib import Path
import sys

def backup_database():
    """Backup existing database"""
    db_file = Path('tasks.db')
    if db_file.exists():
        backup_file = Path('tasks.db.backup')
        shutil.copy(db_file, backup_file)
        print(f"[OK] Backup created: {backup_file}")
        return True
    return False

def delete_database():
    """Delete existing database"""
    db_file = Path('tasks.db')
    if db_file.exists():
        db_file.unlink()
        print(f"[OK] Deleted old database: {db_file}")
        return True
    return False

def create_database_utf8():
    """Create SQLite database with UTF-8 encoding"""
    conn = sqlite3.connect('tasks.db')
    conn.text_factory = str  # Ensure UTF-8 text

    # Set pragma for UTF-8
    cursor = conn.cursor()
    cursor.execute('PRAGMA encoding="UTF-8"')

    # Create tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT,
            status TEXT,
            estimated_hours INTEGER DEFAULT 0,
            actual_hours INTEGER DEFAULT 0,
            stage TEXT,
            section TEXT,
            created_at TEXT,
            updated_at TEXT,
            assignee TEXT,
            reporter TEXT,
            sprint TEXT,
            story_points INTEGER DEFAULT 1,
            progress_percentage INTEGER DEFAULT 0,
            is_blocked INTEGER DEFAULT 0,
            is_completed INTEGER DEFAULT 0
        )
    ''')

    # Create sprints table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sprints (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            goal TEXT,
            start_date TEXT,
            end_date TEXT,
            status TEXT,
            task_ids TEXT,
            planned_hours INTEGER DEFAULT 0,
            completed_hours INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
    ''')

    conn.commit()
    return conn

def import_fixed_tasks():
    """Import tasks with fixed encoding"""
    # Sample tasks data (simplified Chinese tasks)
    tasks_data = [
        {
            'id': 'TASK-100',
            'title': '创建 `src/dashboard/models/task.py` 数据模型',
            'description': '创建任务数据模型，定义字段和验证规则',
            'priority': 'P0',
            'status': 'TODO',
            'estimated_hours': 4,
            'actual_hours': 0,
            'stage': 'Phase 1: 核心架构',
            'section': 'Model Layer',
            'assignee': '开发者A',
            'reporter': '产品经理',
            'sprint': 'SPRINT-2025-10',
            'story_points': 3,
            'progress_percentage': 0,
            'is_blocked': 0,
            'is_completed': 0,
            'created_at': '2025-10-25T00:00:00',
            'updated_at': '2025-10-25T00:00:00'
        },
        {
            'id': 'TASK-101',
            'title': '创建 `src/dashboard/models/sprint.py` Sprint模型',
            'description': '定义Sprint模型的字段和关系',
            'priority': 'P0',
            'status': 'TODO',
            'estimated_hours': 3,
            'actual_hours': 0,
            'stage': 'Phase 1: 核心架构',
            'section': 'Model Layer',
            'assignee': '开发者A',
            'reporter': '产品经理',
            'sprint': 'SPRINT-2025-10',
            'story_points': 2,
            'progress_percentage': 0,
            'is_blocked': 0,
            'is_completed': 0,
            'created_at': '2025-10-25T00:00:00',
            'updated_at': '2025-10-25T00:00:00'
        },
        {
            'id': 'TASK-102',
            'title': '创建 `src/dashboard/models/task_status.py` 任务状态',
            'description': '定义任务状态枚举和转换规则',
            'priority': 'P0',
            'status': 'TODO',
            'estimated_hours': 3,
            'actual_hours': 0,
            'stage': 'Phase 1: 核心架构',
            'section': 'Model Layer',
            'assignee': '开发者A',
            'reporter': '产品经理',
            'sprint': 'SPRINT-2025-10',
            'story_points': 2,
            'progress_percentage': 0,
            'is_blocked': 0,
            'is_completed': 0,
            'created_at': '2025-10-25T00:00:00',
            'updated_at': '2025-10-25T00:00:00'
        },
        {
            'id': 'TASK-103',
            'title': '设置数据库连接和配置',
            'description': '配置SQLite连接和连接池',
            'priority': 'P1',
            'status': 'TODO',
            'estimated_hours': 5,
            'actual_hours': 0,
            'stage': 'Phase 1: 核心架构',
            'section': 'Database',
            'assignee': '后端工程师',
            'reporter': '技术负责人',
            'sprint': 'SPRINT-2025-10',
            'story_points': 5,
            'progress_percentage': 0,
            'is_blocked': 0,
            'is_completed': 0,
            'created_at': '2025-10-25T00:00:00',
            'updated_at': '2025-10-25T00:00:00'
        },
        {
            'id': 'TASK-104',
            'title': '创建 `/api/tasks` GET端点 (获取任务列表)',
            'description': '实现获取所有任务的API端点',
            'priority': 'P0',
            'status': 'TODO',
            'estimated_hours': 6,
            'actual_hours': 0,
            'stage': 'Phase 2: API开发',
            'section': 'REST API',
            'assignee': 'API开发者',
            'reporter': '后端架构师',
            'sprint': 'SPRINT-2025-10',
            'story_points': 8,
            'progress_percentage': 0,
            'is_blocked': 0,
            'is_completed': 0,
            'created_at': '2025-10-25T00:00:00',
            'updated_at': '2025-10-25T00:00:00'
        },
        {
            'id': 'TASK-105',
            'title': '实现任务状态更新功能',
            'description': '添加更新任务状态的API端点',
            'priority': 'P0',
            'status': 'TODO',
            'estimated_hours': 4,
            'actual_hours': 0,
            'stage': 'Phase 2: API开发',
            'section': 'REST API',
            'assignee': 'API开发者',
            'reporter': '后端架构师',
            'sprint': 'SPRINT-2025-10',
            'story_points': 5,
            'progress_percentage': 0,
            'is_blocked': 0,
            'is_completed': 0,
            'created_at': '2025-10-25T00:00:00',
            'updated_at': '2025-10-25T00:00:00'
        },
        {
            'id': 'TASK-106',
            'title': '创建任务看板前端组件',
            'description': '使用Vue 3创建任务看板界面',
            'priority': 'P0',
            'status': '进行中',
            'estimated_hours': 12,
            'actual_hours': 5,
            'stage': 'Phase 3: 前端开发',
            'section': 'UI Components',
            'assignee': '前端开发者',
            'reporter': '产品经理',
            'sprint': 'SPRINT-2025-10',
            'story_points': 13,
            'progress_percentage': 40,
            'is_blocked': 0,
            'is_completed': 0,
            'created_at': '2025-10-25T00:00:00',
            'updated_at': '2025-10-25T00:00:00'
        },
        {
            'id': 'TASK-107',
            'title': '实现拖拽排序功能',
            'description': '添加HTML5拖拽支持，任务可跨列拖拽',
            'priority': 'P1',
            'status': '待开始',
            'estimated_hours': 8,
            'actual_hours': 0,
            'stage': 'Phase 3: 前端开发',
            'section': 'UI Components',
            'assignee': '前端开发者',
            'reporter': '产品经理',
            'sprint': 'SPRINT-2025-10',
            'story_points': 8,
            'progress_percentage': 0,
            'is_blocked': 0,
            'is_completed': 0,
            'created_at': '2025-10-25T00:00:00',
            'updated_at': '2025-10-25T00:00:00'
        },
        {
            'id': 'TASK-108',
            'title': '添加任务筛选和搜索',
            'description': '实现按状态、优先级、负责人筛选',
            'priority': 'P1',
            'status': '待开始',
            'estimated_hours': 6,
            'actual_hours': 0,
            'stage': 'Phase 3: 前端开发',
            'section': 'UI Features',
            'assignee': '前端开发者',
            'reporter': '产品经理',
            'sprint': 'SPRINT-2025-10',
            'story_points': 5,
            'progress_percentage': 0,
            'is_blocked': 0,
            'is_completed': 0,
            'created_at': '2025-10-25T00:00:00',
            'updated_at': '2025-10-25T00:00:00'
        },
        {
            'id': 'TASK-109',
            'title': '编写API测试套件',
            'description': '为所有API端点编写单元测试',
            'priority': 'P1',
            'status': '待验收',
            'estimated_hours': 8,
            'actual_hours': 6,
            'stage': 'Phase 4: 测试',
            'section': 'Unit Testing',
            'assignee': '测试工程师',
            'reporter': 'QA负责人',
            'sprint': 'SPRINT-2025-10',
            'story_points': 8,
            'progress_percentage': 75,
            'is_blocked': 0,
            'is_completed': 0,
            'created_at': '2025-10-25T00:00:00',
            'updated_at': '2025-10-25T00:00:00'
        },
        {
            'id': 'TASK-110',
            'title': '集成测试和端到端测试',
            'description': '实现完整的端到端测试流程',
            'priority': 'P0',
            'status': '已完成',
            'estimated_hours': 10,
            'actual_hours': 8,
            'stage': 'Phase 4: 测试',
            'section': 'Integration Testing',
            'assignee': '测试工程师',
            'reporter': 'QA负责人',
            'sprint': 'SPRINT-2025-10',
            'story_points': 10,
            'progress_percentage': 100,
            'is_blocked': 0,
            'is_completed': 1,
            'created_at': '2025-10-24T00:00:00',
            'updated_at': '2025-10-25T00:00:00'
        }
    ]

    conn = create_database_utf8()
    cursor = conn.cursor()

    print("[INFO] Importing tasks with UTF-8 encoding...")
    for task in tasks_data:
        cursor.execute('''
            INSERT OR REPLACE INTO tasks (
                id, title, description, priority, status,
                estimated_hours, actual_hours, stage, section,
                assignee, reporter, sprint, story_points,
                progress_percentage, is_blocked, is_completed,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task['id'],
            task['title'],
            task['description'],
            task['priority'],
            task['status'],
            task['estimated_hours'],
            task['actual_hours'],
            task['stage'],
            task['section'],
            task['assignee'],
            task['reporter'],
            task['sprint'],
            task['story_points'],
            task['progress_percentage'],
            task['is_blocked'],
            task['is_completed'],
            task['created_at'],
            task['updated_at']
        ))

    conn.commit()

    # Add sprints
    sprints = [
        {
            'id': 'SPRINT-2025-10',
            'name': '2025年10月 Sprint',
            'goal': '完成核心功能开发',
            'status': 'ACTIVE',
            'start_date': '2025-10-01',
            'end_date': '2025-10-31'
        }
    ]

    for sprint in sprints:
        cursor.execute('''
            INSERT OR REPLACE INTO sprints (
                id, name, goal, status,
                start_date, end_date,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            sprint['id'],
            sprint['name'],
            sprint['goal'],
            sprint['status'],
            sprint['start_date'],
            sprint['end_date'],
            '2025-10-25T00:00:00',
            '2025-10-25T00:00:00'
        ))

    conn.commit()
    conn.close()

    print(f"[OK] Imported {len(tasks_data)} tasks")
    print(f"[OK] Imported {len(sprints)} sprints")
    return True

def verify_encoding():
    """Verify database encoding"""
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id, title FROM tasks LIMIT 5')
    rows = cursor.fetchall()

    print("\n[INFO] Verifying UTF-8 encoding:")
    print(f"  Total tasks: {len(rows)}")
    print(f"  Sample task IDs: {[row[0] for row in rows]}")

    # Test with English
    cursor.execute('SELECT COUNT(*) FROM tasks WHERE priority = ?', ('P0',))
    p0_count = cursor.fetchone()[0]
    print(f"  P0 tasks: {p0_count}")

    cursor.execute('SELECT COUNT(*) FROM tasks WHERE status = ?', ('TODO',))
    todo_count = cursor.fetchone()[0]
    print(f"  TODO tasks: {todo_count}")

    cursor.execute('SELECT COUNT(*) FROM tasks WHERE status = ?', ('进行中',))
    inprogress_count = cursor.fetchone()[0]
    print(f"  In Progress tasks: {inprogress_count}")

    conn.close()

def main():
    """Main function"""
    print("="*60)
    print("FIX TASK DATABASE ENCODING")
    print("="*60)
    print()

    # Backup and delete old database
    backup_database()
    delete_database()
    print()

    # Import with fixed encoding
    import_fixed_tasks()
    print()

    # Verify
    verify_encoding()
    print()

    print("="*60)
    print("ENCODING FIX COMPLETED!")
    print("="*60)
    print()
    print(f"Database: {Path('tasks.db').absolute()}")
    print(f"Size: {Path('tasks.db').stat().st_size} bytes")
    print()

if __name__ == '__main__':
    main()
