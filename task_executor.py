#!/usr/bin/env python3
"""
Task Executor - 任务执行引擎
支持在本地执行Python脚本、Shell命令、API调用等
"""

import asyncio
import subprocess
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, List
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskExecutor:
    """任务执行引擎"""

    def __init__(self, db_path: str = "tasks.db"):
        self.db_path = db_path
        self.running_tasks = {}  # 正在运行的任务

    def get_db_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    async def execute_task(self, task_id: str, execution_type: str, command: str):
        """
        执行任务
        :param task_id: 任务ID
        :param execution_type: 执行类型 (python/shell/api)
        :param command: 执行命令或代码
        """
        try:
            logger.info(f"开始执行任务 {task_id} ({execution_type})")

            # 更新任务状态为"进行中"
            await self.update_task_status(task_id, "进行中")

            # 根据类型执行
            if execution_type == "python":
                result = await self._execute_python(task_id, command)
            elif execution_type == "shell":
                result = await self._execute_shell(task_id, command)
            elif execution_type == "api":
                result = await self._execute_api(task_id, command)
            else:
                raise ValueError(f"不支持的执行类型: {execution_type}")

            # 更新任务为已完成
            await self.update_task_status(task_id, "已完成", result)

            logger.info(f"任务 {task_id} 执行完成")
            return result

        except Exception as e:
            logger.error(f"任务 {task_id} 执行失败: {str(e)}")
            await self.update_task_status(task_id, "已阻塞", {"error": str(e)})
            raise

    async def _execute_python(self, task_id: str, code: str) -> Dict[str, Any]:
        """执行Python代码"""
        try:
            # 创建临时Python文件
            temp_file = Path(f"temp_task_{task_id}.py")
            temp_file.write_text(code, encoding='utf-8')

            # 执行Python脚本
            process = await asyncio.create_subprocess_exec(
                "python", str(temp_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            # 清理临时文件
            temp_file.unlink()

            result = {
                "type": "python",
                "returncode": process.returncode,
                "stdout": stdout.decode('utf-8'),
                "stderr": stderr.decode('utf-8'),
                "timestamp": datetime.now().isoformat()
            }

            if process.returncode != 0:
                raise Exception(f"Python脚本执行失败: {stderr.decode('utf-8')}")

            return result

        except Exception as e:
            raise Exception(f"Python执行错误: {str(e)}")

    async def _execute_shell(self, task_id: str, command: str) -> Dict[str, Any]:
        """执行Shell命令"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            result = {
                "type": "shell",
                "returncode": process.returncode,
                "stdout": stdout.decode('utf-8'),
                "stderr": stderr.decode('utf-8'),
                "timestamp": datetime.now().isoformat()
            }

            if process.returncode != 0:
                raise Exception(f"Shell命令执行失败: {stderr.decode('utf-8')}")

            return result

        except Exception as e:
            raise Exception(f"Shell执行错误: {str(e)}")

    async def _execute_api(self, task_id: str, api_config: str) -> Dict[str, Any]:
        """执行API调用"""
        try:
            # 解析API配置
            config = json.loads(api_config)
            url = config.get("url")
            method = config.get("method", "GET")
            data = config.get("data", {})

            # 使用curl执行API调用
            cmd = ["curl", "-s", "-X", method, url]
            if data:
                cmd.extend(["-H", "Content-Type: application/json"])
                cmd.extend(["-d", json.dumps(data)])

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            result = {
                "type": "api",
                "url": url,
                "method": method,
                "returncode": process.returncode,
                "stdout": stdout.decode('utf-8'),
                "stderr": stderr.decode('utf-8'),
                "timestamp": datetime.now().isoformat()
            }

            if process.returncode != 0:
                raise Exception(f"API调用失败: {stderr.decode('utf-8')}")

            return result

        except Exception as e:
            raise Exception(f"API执行错误: {str(e)}")

    async def update_task_status(self, task_id: str, status: str, result: Dict = None):
        """更新任务状态"""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        # 获取当前任务
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        task = cursor.fetchone()

        if not task:
            raise Exception(f"任务 {task_id} 不存在")

        # 更新状态和结果
        if result:
            result_json = json.dumps(result, ensure_ascii=False)
            cursor.execute(
                "UPDATE tasks SET status = ?, updated_at = ?, execution_result = ? WHERE id = ?",
                (status, datetime.now().isoformat(), result_json, task_id)
            )
        else:
            cursor.execute(
                "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
                (status, datetime.now().isoformat(), task_id)
            )

        conn.commit()
        conn.close()

    async def run_demo_tasks(self):
        """Run demo tasks"""
        print("\n" + "="*60)
        print("TASK EXECUTOR DEMO")
        print("="*60)

        demo_tasks = [
            {
                "id": "TASK-200",
                "title": "Execute Python Data Processing",
                "execution_type": "python",
                "command": """
print("Starting data processing...")
import json
data = {"name": "Demo Task", "value": 100}
print(f"Processing data: {data}")
print("Data processing complete!")
result = {"processed": True, "count": 100}
print(f"Result: {result}")
""",
                "expected_status": "已完成"
            },
            {
                "id": "TASK-201",
                "title": "Execute Shell System Check",
                "execution_type": "shell",
                "command": "echo 'System check start' && python --version && echo 'System check complete'",
                "expected_status": "已完成"
            },
            {
                "id": "TASK-202",
                "title": "Call Local API for Data",
                "execution_type": "api",
                "command": json.dumps({
                    "url": "http://localhost:8000/tasks/summary",
                    "method": "GET"
                }),
                "expected_status": "已完成"
            }
        ]

        for task in demo_tasks:
            print(f"\nExecuting: {task['title']}")
            print(f"Type: {task['execution_type']}")
            try:
                result = await self.execute_task(
                    task['id'],
                    task['execution_type'],
                    task['command']
                )
                print(f"[OK] Execution successful")
                if result.get('stdout'):
                    print(f"Output:\n{result['stdout']}")
            except Exception as e:
                print(f"[ERROR] Execution failed: {str(e)}")
            print("-" * 60)

        print("\n" + "="*60)
        print("DEMO COMPLETED!")
        print("="*60)

if __name__ == "__main__":
    executor = TaskExecutor()
    asyncio.run(executor.run_demo_tasks())
