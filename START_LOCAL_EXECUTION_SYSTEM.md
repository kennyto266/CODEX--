# 🚀 本地任务执行系统 - 快速启动

**一键启动完整系统，无需额外配置！**

---

## ⚡ 30秒快速启动

### 步骤1: 启动所有服务
```bash
# 在项目根目录依次执行 (每个命令在新终端窗口):
terminal 1: python simple_task_api.py
terminal 2: python terminal_task_executor.py
terminal 3: cd src/dashboard/static && python -m http.server 8001
```

### 步骤2: 打开浏览器
```
🎯 智能任务看板: http://localhost:8001/task-board-execution.html
```

### 步骤3: 开始执行
- 查看任务列表
- 点击🚀按钮执行任务
- 观察实时结果

---

## 🎯 3种使用方式

### 方式1: Web界面 (最简单) ⭐
```
打开: http://localhost:8001/task-board-execution.html
操作: 点击🚀按钮
查看: 任务状态和执行结果
```

### 方式2: API调用 (开发用)
```bash
# 单任务执行
curl -X POST http://localhost:8002/execute/task \
  -H "Content-Type: application/json" \
  -d '{"task_id":"T1","command":"echo Hello","execution_type":"shell"}'

# 批量执行
curl -X POST http://localhost:8002/execute/batch \
  -H "Content-Type: application/json" \
  -d '{"task_ids":["T1","T2","T3"]}'
```

### 方式3: Python脚本 (自动化)
```python
import requests

# 执行任务
r = requests.post("http://localhost:8002/execute/task", json={
    "task_id": "DEMO",
    "command": "echo 'Hello from Python'",
    "execution_type": "shell"
})

result = r.json()
print(f"Success: {result['success']}")
print(f"Output: {result['stdout']}")
```

---

## ✅ 验证系统正常

### 检查服务状态
```bash
# 检查API
curl http://localhost:8000/tasks/summary
# 应返回: {"total": 11, "completed": 3, ...}

# 检查执行器
curl http://localhost:8002/
# 应返回: {"service": "Terminal Task Executor", ...}

# 检查前端
curl -I http://localhost:8001/task-board-execution.html
# 应返回: HTTP/1.0 200 OK
```

### 快速测试
```bash
# 测试本地执行
curl -X POST http://localhost:8002/execute/task \
  -H "Content-Type: application/json" \
  -d '{"task_id":"TEST","command":"echo 系统正常","execution_type":"shell"}'

# 预期结果:
# {"task_id":"TEST","success":true,"stdout":"系统正常\n",...}
```

---

## 📋 支持的任务类型

| 类型 | 示例命令 | 说明 |
|------|----------|------|
| Shell | `echo "Hello"` | 系统命令 |
| Python | `python -c "print(1)"` | Python代码 |
| 批量 | 多个任务 | 顺序执行 |

---

## 🔧 故障排除

### 端口被占用
```bash
# 查看端口占用
netstat -ano | findstr :8000

# 终止进程
taskkill /PID <进程ID> /F
```

### 服务未启动
```bash
# 检查进程
ps aux | grep python

# 重新启动
python simple_task_api.py &
python terminal_task_executor.py &
```

### 数据库问题
```bash
# 重建数据库
rm tasks.db
python -c "import sqlite3; c=sqlite3.connect('tasks.db'); c.execute('CREATE TABLE tasks (id TEXT, title TEXT, status TEXT, priority TEXT, execution_result TEXT)'); c.commit(); c.close()"
```

---

## 📊 系统状态

✅ **任务管理API** (端口8000) - 运行中
✅ **终端执行器** (端口8002) - 运行中
✅ **前端看板** (端口8001) - 运行中
✅ **SQLite数据库** - 已连接

---

## 🎉 开始使用

**现在就可以开始使用本地任务执行系统了！**

1. 访问: http://localhost:8001/task-board-execution.html
2. 体验真正的本地命令执行
3. 查看实时任务状态更新

**系统完全就绪，无需额外配置！** 🚀
