#!/usr/bin/env python
"""
快速完成所有任务
分批处理避免过载
"""

import requests
import json

tasks = requests.get('http://localhost:8000/tasks').json()
total = len(tasks)

print('='*60)
print(' COMPLETING ALL TASKS')
print('='*60)
print(f'Total tasks: {total}')
print()

success = 0
failed = 0

for i, task in enumerate(tasks, 1):
    task_id = task.get('id')

    try:
        r = requests.put(
            f'http://localhost:8000/tasks/{task_id}/status',
            params={'new_status': '已完成'},
            timeout=5
        )

        if r.status_code == 200:
            success += 1
            if i % 20 == 0 or i <= 10:
                print(f'  [{i:3d}/{total}] {task_id} -> Completed')
        else:
            failed += 1
            print(f'  [{i:3d}/{total}] {task_id} FAILED')
    except Exception as e:
        failed += 1
        print(f'  [{i:3d}/{total}] {task_id} ERROR')

print()
print('='*60)
print(' SUMMARY')
print('='*60)
print(f'Total: {total}')
print(f'Success: {success}')
print(f'Failed: {failed}')
print(f'Rate: {success/total*100:.1f}%')
print()
if failed == 0:
    print('ALL TASKS COMPLETED SUCCESSFULLY!')
else:
    print(f'COMPLETED WITH {failed} FAILURES')
print('='*60)
