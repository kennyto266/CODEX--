# 📝 如何添加任务到"待执行"列表

**系统已就绪！现在有3种方式添加任务**

---

## 方法1: 使用Python脚本 (推荐) ⭐

### 创建单个任务
```bash
python add_demo_task.py
```
这会创建一个示例任务：`TASK-DEMO-1761784763`

### 创建自定义任务
创建一个新文件 `my_task.py`:
```python
import sqlite3
import time

conn = sqlite3.connect('tasks.db')
cursor = conn.cursor()

# 自定义任务信息
task_id = "TASK-MY-001"
title = "My Custom Task"
description = "Task description here"
status = "TODO"
priority = "P1"
hours = 16

cursor.execute("""
INSERT INTO tasks (
    id, title, description, status, priority,
    estimated_hours, actual_hours, stage, section,
    assignee, reporter, sprint, story_points,
    progress_percentage, is_blocked, is_completed,
    created_at, updated_at
) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, 1, 0.0, 0, 0, datetime('now'), datetime('now'))
""", (
    task_id, title, description, status, priority,
    hours, "Custom", "MyModule", "User A", "Admin", "SPRINT-1"
))

conn.commit()
conn.close()

print(f"Task {task_id} added successfully!")
```

运行:
```bash
python my_task.py
```

---

## 方法2: 通过API调用

### 步骤1: 直接操作数据库 (临时方案)
由于当前API没有创建任务的端点，我们通过SQLite添加:

```python
import requests
import json

# 这里需要先通过Python脚本添加任务到数据库
# 然后可以通过API更新状态
```

### 步骤2: 更新任务状态
```bash
# 将任务移到"进行中"
curl -X PUT "http://localhost:8000/tasks/TASK-DEMO-1761784763/status?new_status=进行中"

# 将任务标记为已完成
curl -X PUT "http://localhost:8000/tasks/TASK-DEMO-1761784763/status?new_status=已完成"
```

---

## 方法3: 通过Web界面

### 手动添加任务
1. 打开: http://localhost:8001/task-board-execution.html
2. 右键点击页面 → "检查元素"
3. 在Console中执行:
```javascript
// 注意：当前界面没有直接的"添加任务"按钮
// 需要先通过方法1或2添加任务
```

---

## 📋 完整示例：添加并执行任务

### 步骤1: 添加任务
```bash
python add_demo_task.py
```
输出:
```
SUCCESS: Task added!
  ID: TASK-DEMO-1761784763
  Title: Demo Task - Local Execution Feature
  Status: TODO
Total tasks in database: 13
```

### 步骤2: 在看板中查看
1. 打开: http://localhost:8001/task-board-execution.html
2. 点击"🔄 刷新"按钮
3. 找到新添加的任务 (在"待开始"列)

### 步骤3: 执行任务
点击任务旁的🚀按钮，执行本地命令:
```bash
echo "Executing TASK-DEMO-1761784763: Demo Task - Local Execution Feature"
echo "Task completed successfully!"
```

### 步骤4: 查看结果
- 任务状态变为"✅ 已完成"
- 执行结果显示在任务卡片中
- 数据库更新执行时间和输出

---

## 🎯 批量添加任务

创建 `batch_add_tasks.py`:
```python
import sqlite3

tasks = [
    ("TASK-BATCH-001", "Batch Task 1", "First batch task", "TODO", "P2", 8),
    ("TASK-BATCH-002", "Batch Task 2", "Second batch task", "TODO", "P1", 12),
    ("TASK-BATCH-003", "Batch Task 3", "Third batch task", "TODO", "P2", 6),
]

conn = sqlite3.connect('tasks.db')
cursor = conn.cursor()

for task_id, title, desc, status, priority, hours in tasks:
    cursor.execute("""
        INSERT INTO tasks (
            id, title, description, status, priority,
            estimated_hours, actual_hours, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, 0, datetime('now'), datetime('now'))
    """, (task_id, title, desc, status, priority, hours))
    print(f"Added: {task_id}")

conn.commit()
conn.close()
print(f"\nTotal {len(tasks)} tasks added!")
```

运行:
```bash
python batch_add_tasks.py
```

---

## 🔧 API端点参考

### 当前可用的端点
```bash
# 获取所有任务
GET http://localhost:8000/tasks

# 获取任务摘要
GET http://localhost:8000/tasks/summary

# 获取单个任务
GET http://localhost:8000/tasks/{task_id}

# 更新任务状态
PUT http://localhost:8000/tasks/{task_id}/status?new_status={status}

# 执行任务
POST http://localhost:8002/execute/task

# 批量执行
POST http://localhost:8002/execute/batch

# 查询执行状态
GET http://localhost:8002/execute/status/{task_id}
```

### 缺失的端点 (TODO)
```bash
# 创建任务 (尚未实现)
POST http://localhost:8000/tasks

# 删除任务 (尚未实现)
DELETE http://localhost:8000/tasks/{task_id}

# 更新任务 (尚未实现)
PUT http://localhost:8000/tasks/{task_id}
```

---

## 💡 任务状态说明

| 状态 | 显示名称 | 含义 |
|------|----------|------|
| `TODO` | ⏸️ 待开始 | 新任务，默认状态 |
| `进行中` | 🔄 进行中 | 正在执行 |
| `待验收` | 👀 待验收 | 等待验收 |
| `已完成` | ✅ 已完成 | 执行完成 |
| `已阻塞` | 🚫 已阻塞 | 无法执行 |

---

## 🎉 实际演示

### 当前数据库状态
```
✅ 任务总数: 13
✅ 最新添加: TASK-DEMO-1761784763
✅ 状态: TODO (在待执行列表中)
```

### 立即体验
1. 打开看板: http://localhost:8001/task-board-execution.html
2. 刷新页面查看新任务
3. 点击🚀执行任务
4. 观察状态变化

---

## 📌 总结

**添加任务有3种方式:**

1. **Python脚本** (最灵活) - 直接操作数据库
2. **API调用** (开发用) - 需要扩展API
3. **Web界面** (未来功能) - 需要添加前端按钮

**推荐**: 使用Python脚本快速添加任务，然后通过Web界面执行！

---

**现在就开始添加你的任务吧！** 🚀
