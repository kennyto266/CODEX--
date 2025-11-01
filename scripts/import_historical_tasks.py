import re, json
from datetime import datetime

def extract_tasks():
    with open('openspec/changes/optimize-api-architecture/tasks.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    task_pattern = r'- \[ \] (.+?)(?=\n- \[ \]|\n\n|\Z)'
    matches = re.findall(task_pattern, content, re.DOTALL)
    
    tasks = []
    for i, match in enumerate(matches, 1):
        task_desc = match.strip()
        if task_desc.startswith('#') or task_desc.startswith('##'):
            continue
        
        task_info = {
            'id': f'TASK-H-{i:03d}',
            'title': task_desc,
            'priority': 'P2',
            'estimated_hours': 2,
            'status': 'TODO'
        }
        tasks.append(task_info)
    
    return tasks

tasks = extract_tasks()
with open('sprints/SPRINT-2025-10/artifacts/historical-tasks.json', 'w') as f:
    json.dump(tasks, f, ensure_ascii=False, indent=2)

print(f"Extracted {len(tasks)} tasks")
print("First 5 tasks:")
for i, task in enumerate(tasks[:5]):
    print(f"{i+1}. {task['title'][:50]}...")
