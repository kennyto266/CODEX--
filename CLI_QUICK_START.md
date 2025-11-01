# CLI 任務自動化 - 快速開始

## 🚀 立即開始

### 1. 更新單個任務
```bash
python -c "import requests; requests.put('http://localhost:8000/tasks/TASK-100/status', params={'new_status': '進行中'})"
```

### 2. 檢查任務狀態
```bash
curl -s "http://localhost:8000/tasks/TASK-100" | python -c "import sys,json; print(json.load(sys.stdin)['status'])"
```

### 3. 批量更新
```bash
python -c "
import requests
tasks = requests.get('http://localhost:8000/tasks').json()
for task in tasks:
    if task.get('status') == '待開始':
        requests.put(f'http://localhost:8000/tasks/{task[\"id\"]}/status', params={'new_status': '進行中'})
print('批量更新完成')
"
```

## 📋 支持的狀態

- `待開始`
- `進行中`
- `待驗收`
- `已完成`
- `已阻塞`

## 🔧 常用命令

### 開始任務
```bash
python -c "import requests; requests.put('http://localhost:8000/tasks/TASK-XXX/status', params={'new_status': '進行中'})"
```

### 完成任務
```bash
python -c "import requests; requests.put('http://localhost:8000/tasks/TASK-XXX/status', params={'new_status': '已完成'})"
```

### 需要驗收
```bash
python -c "import requests; requests.put('http://localhost:8000/tasks/TASK-XXX/status', params={'new_status': '待驗收'})"
```

### 任務被阻塞
```bash
python -c "import requests; requests.put('http://localhost:8000/tasks/TASK-XXX/status', params={'new_status': '已阻塞'})"
```

## 📊 查看統計

```bash
curl -s "http://localhost:8000/tasks" | python -c "
import sys, json
tasks = json.load(sys.stdin)
status = {}
for t in tasks:
    s = t.get('status', 'Unknown')
    status[s] = status.get(s, 0) + 1
print('Total:', len(tasks))
for s, c in status.items():
    print(f'  {s}: {c}')
"
```

## 🎯 完整工作流

```bash
# 1. 開始任務
python -c "import requests; requests.put('http://localhost:8000/tasks/TASK-100/status', params={'new_status': '進行中'})"

# 2. 開發中...

# 3. 提交前標記為待驗收
python -c "import requests; requests.put('http://localhost:8000/tasks/TASK-100/status', params={'new_status': '待驗收'})"

# 4. 驗收後標記為已完成
python -c "import requests; requests.put('http://localhost:8000/tasks/TASK-100/status', params={'new_status': '已完成'})"
```

## 📁 文件

- `auto_update_tasks.py` - 完整自動化腳本
- `task_automation_examples.py` - 使用示例
- `CLI_TASK_AUTOMATION_GUIDE.md` - 詳細指南
- `CLI_AUTOMATION_SUCCESS_REPORT.md` - 成功報告

---

**✅ 任務看板CLI自動化已就緒！**
