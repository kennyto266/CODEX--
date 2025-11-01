import re
import json

def extract_tasks_fixed():
    with open('openspec/changes/optimize-api-architecture/tasks.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    task_pattern = r'- \[ \] (.+?)(?=\n- \[ \]|\n\n|\Z)'
    matches = re.findall(task_pattern, content, re.DOTALL)
    
    tasks = []
    for i, match in enumerate(matches, 1):
        task_desc = match.strip()
        if task_desc.startswith('#') or task_desc.startswith('##'):
            continue
        
        # 智能分配優先級和估時
        priority = 'P2'
        estimated = 2
        
        if any(kw in task_desc for kw in ['創建', '實現', '重構', '統一API']):
            priority = 'P1'
            estimated = 3
        if any(kw in task_desc for kw in ['認證', '安全', '監控', '速率限制']):
            priority = 'P0'
        if '測試' in task_desc:
            estimated = 1
        elif '文檔' in task_desc:
            estimated = 1
        
        task_info = {
            'id': f'TASK-H-{i:03d}',
            'title': task_desc,
            'description': f'從optimize-api-architecture提案導入的歷史任務 #{i}',
            'priority': priority,
            'estimated_hours': estimated,
            'status': 'TODO',
            'source': 'optimize-api-architecture'
        }
        tasks.append(task_info)
    
    return tasks

tasks = extract_tasks_fixed()

# 保存為JSON
with open('sprints/SPRINT-2025-10/artifacts/historical-tasks-fixed.json', 'w', encoding='utf-8') as f:
    json.dump(tasks, f, ensure_ascii=False, indent=2)

# 統計信息
p0 = sum(1 for t in tasks if t['priority'] == 'P0')
p1 = sum(1 for t in tasks if t['priority'] == 'P1')
p2 = sum(1 for t in tasks if t['priority'] == 'P2')
total_hours = sum(t['estimated_hours'] for t in tasks)

print(f"任務修復完成!")
print(f"總任務數: {len(tasks)}")
print(f"P0: {p0} 個")
print(f"P1: {p1} 個")
print(f"P2: {p2} 個")
print(f"總估時: {total_hours} 小時")
print(f"保存至: historical-tasks-fixed.json")
