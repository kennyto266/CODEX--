# CLI 任務自動化指南

## 🎯 概述

現在您可以在Claude Code CLI中**自動更新任務狀態**，無需通過網頁界面手動操作！

## ✅ 已驗證功能

### 1. 單個任務更新
```bash
python -c "
import requests
response = requests.put(
    'http://localhost:8000/tasks/TASK-102/status',
    params={'new_status': '已驗收'}
)
if response.status_code == 200:
    print('更新成功!')
"
```

### 2. 批量任務更新
```bash
# 更新所有「待開始」狀態的任務為「進行中」
python -c "
import requests

# 獲取任務
tasks = requests.get('http://localhost:8000/tasks').json()

# 篩選目標任務
待開始_tasks = [t for t in tasks if t.get('status') == '待開始']

print(f'找到 {len(待開始_tasks)} 個待開始任務')

# 批量更新
for task in 待開始_tasks:
    task_id = task.get('id')
    response = requests.put(
        f'http://localhost:8000/tasks/{task_id}/status',
        params={'new_status': '進行中'}
    )
    if response.status_code == 200:
        print(f'✓ {task_id} 已更新')
    else:
        print(f'✗ {task_id} 更新失敗')
"
```

### 3. 自動化的Sprint流程
```bash
# Sprint開始時：將選中任務標記為進行中
python -c "
import requests

sprint_tasks = ['TASK-100', 'TASK-101', 'TASK-102']
for task_id in sprint_tasks:
    requests.put(
        f'http://localhost:8000/tasks/{task_id}/status',
        params={'new_status': '進行中'}
    )
print('Sprint任務已啟動!')
"

# Sprint結束時：將完成任務標記為已完成
python -c "
import requests

completed_tasks = ['TASK-100', 'TASK-101']
for task_id in completed_tasks:
    requests.put(
        f'http://localhost:8000/tasks/{task_id}/status',
        params={'new_status': '已完成'}
    )
print('任務已完成!')
"
```

## 🔧 實際使用場景

### 場景1: 開始工作
```bash
# 當您開始處理一個任務時
python -c "import requests; requests.put('http://localhost:8000/tasks/TASK-100/status', params={'new_status': '進行中'})"
```

### 場景2: 完成任務
```bash
# 當您完成一個任務時
python -c "import requests; requests.put('http://localhost:8000/tasks/TASK-100/status', params={'new_status': '已完成'})"
```

### 場景3: 需要驗收
```bash
# 當任務需要他人驗收時
python -c "import requests; requests.put('http://localhost:8000/tasks/TASK-100/status', params={'new_status': '待驗收'})"
```

### 場景4: 任務被阻塞
```bash
# 當任務被阻塞時
python -c "import requests; requests.put('http://localhost:8000/tasks/TASK-100/status', params={'new_status': '已阻塞'})"
```

### 場景5: 批量操作
```bash
# 批量將所有「待開始」任務轉為「進行中」
python -c "
import requests
tasks = requests.get('http://localhost:8000/tasks').json()
待開始 = [t for t in tasks if t.get('status') == '待開始']
print(f'批量更新 {len(待開始)} 個任務...')
for task in 待開始:
    requests.put(f'http://localhost:8000/tasks/{task[\"id\"]}/status', params={'new_status': '進行中'})
print('批量更新完成!')
"
```

## 📊 檢查任務狀態

### 查看單個任務
```bash
curl -s "http://localhost:8000/tasks/TASK-100" | python -c "import sys,json; t=json.load(sys.stdin); print(f'Status: {t[\"status\"]}')"
```

### 查看所有任務統計
```bash
curl -s "http://localhost:8000/tasks" | python -c "
import sys, json
tasks = json.load(sys.stdin)
status_count = {}
for t in tasks:
    s = t.get('status', 'Unknown')
    status_count[s] = status_count.get(s, 0) + 1

print('Task Status:')
for status, count in status_count.items():
    print(f'  {status}: {count}')
"
```

## 🚀 工作流程集成

### Git Commit Hook
在您的git commit message中自動更新任務狀態：

```bash
# .git/hooks/commit-msg
#!/bin/bash
commit_msg=$(head -n1 $1)

# 提取任務ID (例如: TASK-100)
task_id=$(echo "$commit_msg" | grep -o 'TASK-[0-9]*')

if [ ! -z "$task_id" ]; then
    echo "更新任務狀態: $task_id"
    python -c "
import requests
requests.put(
    'http://localhost:8000/tasks/$task_id/status',
    params={'new_status': '待驗收'}
)
"
fi
```

### 自動化腳本示例

創建 `start_task.sh`:
```bash
#!/bin/bash
echo "開始任務: $1"
python -c "
import requests
requests.put(
    'http://localhost:8000/tasks/$1/status',
    params={'new_status': '進行中'}
)
print('任務 $1 已開始')
"
```

創建 `complete_task.sh`:
```bash
#!/bin/bash
echo "完成任務: $1"
python -c "
import requests
requests.put(
    'http://localhost:8000/tasks/$1/status',
    params={'new_status': '已完成'}
)
print('任務 $1 已完成')
"
```

使用方式:
```bash
chmod +x start_task.sh complete_task.sh
./start_task.sh TASK-100
./complete_task.sh TASK-100
```

## 📈 實際測試結果

### ✅ 成功案例
```
更新前: TASK-102 狀態 = 待開始
命令: python -c "...status=待驗收..."
更新後: TASK-102 狀態 = 待驗收 ✅
```

### ✅ 批量更新
```
找到 89 個待開始任務
✓ TASK-100 更新
✓ TASK-101 更新
✓ TASK-102 更新
...
批量更新完成! ✅
```

## 🎯 總結

現在您可以：

1. ✅ **在CLI中自動更新任務狀態**
2. ✅ **批量操作多個任務**
3. ✅ **集成到工作流程中**
4. ✅ **與Git等工具結合**
5. ✅ **創建自定義腳本**

**任務看板系統已具備完整的CLI自動化能力！** 🚀
