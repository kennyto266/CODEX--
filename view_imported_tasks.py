#!/usr/bin/env python3
"""
View Imported Tasks
Display tasks from the imported database
"""

import sqlite3
import sys
from pathlib import Path

def view_tasks(limit=20):
    """View imported tasks"""
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()

    print("\n" + "="*80)
    print("IMPORTED TASKS FROM DATABASE")
    print("="*80)
    print()

    # Total count
    cursor.execute('SELECT COUNT(*) FROM tasks')
    total = cursor.fetchone()[0]
    print(f"Total tasks: {total}")
    print()

    # Priority distribution
    print("Priority Distribution:")
    cursor.execute('SELECT priority, COUNT(*) FROM tasks GROUP BY priority ORDER BY priority')
    for priority, count in cursor.fetchall():
        percentage = (count / total * 100) if total > 0 else 0
        print(f"  {priority}: {count} tasks ({percentage:.1f}%)")
    print()

    # Status distribution
    print("Status Distribution:")
    cursor.execute('SELECT status, COUNT(*) FROM tasks GROUP BY status ORDER BY status')
    for status, count in cursor.fetchall():
        percentage = (count / total * 100) if total > 0 else 0
        print(f"  {status}: {count} tasks ({percentage:.1f}%)")
    print()

    # Sample tasks
    print(f"Sample Tasks (showing {min(limit, total)} of {total}):")
    print("-"*80)
    cursor.execute('SELECT id, title, priority, status FROM tasks LIMIT ?', (limit,))
    for i, (task_id, title, priority, status) in enumerate(cursor.fetchall(), 1):
        # Truncate long titles
        if len(title) > 60:
            title = title[:57] + "..."

        # Priority badge
        priority_badge = {
            'P0': '[P0-CRITICAL]',
            'P1': '[P1-IMPORTANT]',
            'P2': '[P2-NORMAL]'
        }.get(priority, f'[{priority}]')

        print(f"\n{i}. {task_id}")
        print(f"   Title: {title}")
        print(f"   {priority_badge} Status: {status}")

    conn.close()

    print()
    print("="*80)
    print(f"Database file: {Path('tasks.db').absolute()}")
    print("="*80)

if __name__ == '__main__':
    limit = 20
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            pass

    view_tasks(limit)
