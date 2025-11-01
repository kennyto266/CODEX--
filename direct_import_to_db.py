#!/usr/bin/env python3
"""
Direct Import to Database - Simplified Version
"""

import sys
import sqlite3
from pathlib import Path
import re
from datetime import datetime

def parse_tasks_from_markdown(file_path):
    """Parse tasks from markdown file"""
    tasks = []
    stages = {}
    current_stage = None
    current_section = None

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()

        # Detect stage
        if line.startswith('## 阶段') or line.startswith('## Phase'):
            current_stage = line.replace('##', '').strip()
            if '|' in current_stage:
                current_stage = current_stage.split('|')[0].strip()
            stages[current_stage] = []

        # Detect section
        if line.startswith('### '):
            current_section = line.replace('###', '').strip()

        # Parse task
        if line.startswith('- [ ]'):
            # Extract priority
            priority_match = re.search(r'\[(P[012])\]', line)
            priority = priority_match.group(1) if priority_match else 'P2'

            # Extract task title (remove task marker and priority)
            title = line.replace('- [ ]', '').strip()
            title = re.sub(r'\s*\[P[012]\]\s*$', '', title).strip()

            task = {
                'title': title,
                'description': title,
                'priority': priority,
                'status': 'TODO',
                'estimated_hours': 0,
                'stage': current_stage or 'Unknown',
                'section': current_section or '',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            tasks.append(task)
            if current_stage:
                stages[current_stage] = stages.get(current_stage, 0) + 1

    return tasks, stages

def create_database():
    """Create SQLite database and tables"""
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()

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

def generate_task_id(counter):
    """Generate task ID"""
    return f"TASK-{counter:03d}"

def generate_sprint_id(stage_name, counter):
    """Generate sprint ID"""
    # Convert stage name to sprint format
    sprint_name = stage_name.replace('阶段', 'Phase').replace('Phase', 'Sprint')
    if counter == 0:
        return sprint_name
    else:
        return f"{sprint_name}-{counter}"

def main():
    """Main function"""
    print("\n" + "="*60)
    print("DIRECT DATABASE IMPORT")
    print("="*60)
    print("\nImporting 172 tasks directly to SQLite database...")
    print()

    try:
        # Parse tasks
        print("Step 1: Parse task file...")
        task_file = Path("openspec/changes/optimize-project-plan/tasks.md")
        tasks, stages = parse_tasks_from_markdown(str(task_file))
        print(f"  [OK] Parsed {len(tasks)} tasks")
        print(f"  [OK] Found {len(stages)} stages")
        print()

        # Create database
        print("Step 2: Create database...")
        conn = create_database()
        cursor = conn.cursor()
        print(f"  [OK] Database created: tasks.db")
        print()

        # Insert tasks
        print("Step 3: Insert tasks...")
        task_counter = 100
        for task in tasks:
            task_id = generate_task_id(task_counter)
            task_counter += 1

            cursor.execute('''
                INSERT OR REPLACE INTO tasks (
                    id, title, description, priority, status,
                    estimated_hours, stage, section,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task_id,
                task['title'],
                task['description'],
                task['priority'],
                task['status'],
                task['estimated_hours'],
                task['stage'],
                task['section'],
                task['created_at'],
                task['updated_at']
            ))

        conn.commit()
        print(f"  [OK] Inserted {len(tasks)} tasks")
        print()

        # Insert sprints
        print("Step 4: Insert sprints...")
        for stage_name, count in stages.items():
            sprint_id = generate_sprint_id(stage_name, 0)

            # Get task IDs for this stage
            cursor.execute(
                'SELECT id FROM tasks WHERE stage = ?',
                (stage_name,)
            )
            task_ids = [row[0] for row in cursor.fetchall()]

            cursor.execute('''
                INSERT OR REPLACE INTO sprints (
                    id, name, status, task_ids,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                sprint_id,
                stage_name,
                'PLANNING',
                str(task_ids),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))

        conn.commit()
        print(f"  [OK] Inserted {len(stages)} sprints")
        print()

        # Show statistics
        print("="*60)
        print("IMPORT RESULTS")
        print("="*60)
        print(f"  Total tasks: {len(tasks)}")
        print(f"  Total sprints: {len(stages)}")
        print(f"  Database: tasks.db")
        print()

        # Priority statistics
        print("Priority Distribution:")
        priority_stats = {}
        for task in tasks:
            priority = task['priority']
            priority_stats[priority] = priority_stats.get(priority, 0) + 1

        for priority in ['P0', 'P1', 'P2']:
            count = priority_stats.get(priority, 0)
            percentage = (count / len(tasks) * 100) if tasks else 0
            print(f"  {priority}: {count} tasks ({percentage:.1f}%)")
        print()

        # Stage statistics
        print("Stage Distribution:")
        for stage_name, count in sorted(stages.items()):
            print(f"  {stage_name}: {count} tasks")
        print()

        # Verify data
        print("Verification:")
        cursor.execute('SELECT COUNT(*) FROM tasks')
        task_count = cursor.fetchone()[0]
        print(f"  Tasks in database: {task_count}")

        cursor.execute('SELECT COUNT(*) FROM sprints')
        sprint_count = cursor.fetchone()[0]
        print(f"  Sprints in database: {sprint_count}")
        print()

        conn.close()

        print("="*60)
        print("IMPORT COMPLETED SUCCESSFULLY!")
        print("="*60)
        print()
        print(f"Database location: {Path('tasks.db').absolute()}")
        print(f"Size: {Path('tasks.db').stat().st_size} bytes")
        print()

        return 0

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
