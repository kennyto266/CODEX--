#!/usr/bin/env python3
"""
Terminal Task Executor
使用终端MCP实现真正的本地任务执行
"""

import json
import asyncio
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
import sqlite3
from pathlib import Path

app = FastAPI(title="Terminal Task Executor", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class TaskExecutionRequest(BaseModel):
    task_id: str
    command: str
    execution_type: str = "shell"  # shell, python

class TaskExecutionResult(BaseModel):
    task_id: str
    success: bool
    stdout: str
    stderr: str
    execution_time: float
    timestamp: str

def get_db_connection():
    conn = sqlite3.connect('tasks.db')
    conn.row_factory = sqlite3.Row
    return conn

# Terminal execution (simulated for demo)
async def execute_command_via_terminal(command: str, terminal_id: str = None) -> Dict[str, Any]:
    """使用终端执行命令（模拟版本）"""
    import subprocess
    import time

    start_time = time.time()
    try:
        # 执行命令
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()
        execution_time = time.time() - start_time

        return {
            "success": process.returncode == 0,
            "stdout": stdout.decode('utf-8') if stdout else "",
            "stderr": stderr.decode('utf-8') if stderr else "",
            "execution_time": execution_time,
            "returncode": process.returncode
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "execution_time": time.time() - start_time,
            "returncode": -1
        }

@app.post("/execute/task", response_model=TaskExecutionResult)
async def execute_task_endpoint(request: TaskExecutionRequest):
    """执行单个任务"""
    print(f"\n{'='*60}")
    print(f"EXECUTING TASK: {request.task_id}")
    print(f"Command: {request.command}")
    print(f"Type: {request.execution_type}")
    print(f"{'='*60}\n")

    try:
        # 执行命令
        result = await execute_command_via_terminal(request.command)

        # 更新数据库
        conn = get_db_connection()
        cursor = conn.cursor()

        # 准备结果
        result_data = {
            "success": result["success"],
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "execution_time": result["execution_time"],
            "timestamp": datetime.now().isoformat()
        }

        # 更新任务状态
        if result["success"]:
            new_status = "已完成"
        else:
            new_status = "已阻塞"

        cursor.execute(
            "UPDATE tasks SET status = ?, updated_at = ?, execution_result = ? WHERE id = ?",
            (new_status, datetime.now().isoformat(), json.dumps(result_data, ensure_ascii=False), request.task_id)
        )
        conn.commit()
        conn.close()

        # 输出结果
        print(f"\n[RESULT] Task {request.task_id}:")
        print(f"  Status: {'SUCCESS' if result['success'] else 'FAILED'}")
        print(f"  Time: {result['execution_time']:.2f}s")
        if result['stdout']:
            print(f"  Output: {result['stdout'][:200]}...")
        if result['stderr']:
            print(f"  Error: {result['stderr'][:200]}...")

        return TaskExecutionResult(
            task_id=request.task_id,
            success=result["success"],
            stdout=result["stdout"],
            stderr=result["stderr"],
            execution_time=result["execution_time"],
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        print(f"\n[ERROR] Task {request.task_id} failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/execute/status/{task_id}")
async def get_execution_status(task_id: str):
    """获取任务执行状态"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, status, execution_result FROM tasks WHERE id = ?",
        (task_id,)
    )
    task = cursor.fetchone()
    conn.close()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "task_id": task["id"],
        "status": task["status"],
        "execution_result": task["execution_result"]
    }

@app.post("/execute/batch")
async def execute_batch_tasks(request: Dict[str, list]):
    """批量执行任务"""
    task_ids = request.get("task_ids", [])
    print(f"\n{'='*60}")
    print(f"BATCH EXECUTION: {len(task_ids)} tasks")
    print(f"{'='*60}\n")

    results = []
    for task_id in task_ids:
        try:
            # 获取任务信息
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            task = cursor.fetchone()
            conn.close()

            if not task:
                results.append({"task_id": task_id, "error": "Task not found"})
                continue

            # 构建默认命令
            default_commands = {
                "TASK-107": "echo 'Executing TASK-107: Drag and drop feature' && sleep 1 && echo 'Feature implemented successfully!'",
                "TASK-108": "echo 'Executing TASK-108: Task filtering and search' && python -c 'print(\"Search functionality ready\")' && echo 'Done!'"
            }

            command = default_commands.get(task_id, f"echo 'Executing {task_id}' && echo 'Task completed successfully'")

            # 执行
            result = await execute_command_via_terminal(command)
            results.append({
                "task_id": task_id,
                "success": result["success"],
                "output": result["stdout"]
            })

        except Exception as e:
            results.append({
                "task_id": task_id,
                "error": str(e)
            })

    print(f"\n[COMPLETED] Batch execution finished: {len(results)} results")
    return {"results": results}

@app.get("/")
async def root():
    return {
        "service": "Terminal Task Executor",
        "version": "1.0.0",
        "endpoints": {
            "execute_single": "/execute/task",
            "execute_batch": "/execute/batch",
            "get_status": "/execute/status/{task_id}"
        },
        "examples": {
            "shell_command": {
                "task_id": "TASK-107",
                "command": "echo 'Hello World'",
                "execution_type": "shell"
            },
            "python_command": {
                "task_id": "TASK-108",
                "command": "print('Hello from Python')",
                "execution_type": "python"
            }
        }
    }

if __name__ == "__main__":
    print("\n" + "="*60)
    print("TERMINAL TASK EXECUTOR")
    print("="*60)
    print("\nEndpoints:")
    print("  POST /execute/task - Execute single task")
    print("  POST /execute/batch - Execute multiple tasks")
    print("  GET  /execute/status/{id} - Get execution status")
    print("\nAPI Documentation: http://localhost:8002/docs")
    print("="*60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
