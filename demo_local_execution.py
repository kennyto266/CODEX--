#!/usr/bin/env python3
"""
本地任务执行系统完整演示
展示真正的本地命令执行功能
"""

import json
import time
import requests
from datetime import datetime

def print_header(title):
    """打印标题"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_step(step, description):
    """打印步骤"""
    print(f"\n📌 步骤 {step}: {description}")
    print("-" * 70)

def demo_api_health_check():
    """演示1: API健康检查"""
    print_header("演示 1: API服务健康检查")

    # 检查任务管理API
    print_step(1, "检查任务管理API (端口8000)")
    try:
        response = requests.get("http://localhost:8000/")
        data = response.json()
        print(f"✅ 任务管理API正常: {data['message']}")
        print(f"   端点: {list(data['endpoints'].keys())}")
    except Exception as e:
        print(f"❌ 任务管理API连接失败: {e}")
        return False

    # 检查终端执行器API
    print_step(2, "检查终端执行器API (端口8002)")
    try:
        response = requests.get("http://localhost:8002/")
        data = response.json()
        print(f"✅ 终端执行器API正常: {data['service']} v{data['version']}")
        print(f"   端点: {list(data['endpoints'].keys())}")
    except Exception as e:
        print(f"❌ 终端执行器API连接失败: {e}")
        return False

    return True

def demo_task_summary():
    """演示2: 获取任务摘要"""
    print_header("演示 2: 任务统计摘要")

    print_step(1, "获取当前任务状态")
    try:
        response = requests.get("http://localhost:8000/tasks/summary")
        data = response.json()

        print(f"\n📊 任务统计:")
        print(f"   总任务数: {data['total']}")
        print(f"   ✅ 已完成: {data['completed']}")
        print(f"   🔄 进行中: {data['in_progress']}")
        print(f"   🚫 已阻塞: {data['blocked']}")
        print(f"   ⏸️  待开始: {data['todo']}")
        print(f"   📈 完成率: {data['completion_rate']:.1f}%")

        return data
    except Exception as e:
        print(f"❌ 获取任务摘要失败: {e}")
        return None

def demo_single_task_execution():
    """演示3: 单任务执行"""
    print_header("演示 3: 本地命令执行")

    task_id = f"TASK-DEMO-{int(time.time())}"
    timestamp = datetime.now().strftime("%H:%M:%S")
    command = f'echo "Executing {task_id} at {timestamp}" && echo "Local execution successful!" && date'

    print_step(1, f"执行任务 {task_id}")
    print(f"   命令: {command}")

    try:
        response = requests.post(
            "http://localhost:8002/execute/task",
            json={
                "task_id": task_id,
                "command": command,
                "execution_type": "shell"
            }
        )

        result = response.json()

        if result.get("success"):
            print(f"\n✅ 任务执行成功!")
            print(f"   执行时间: {result['execution_time']:.3f}s")
            print(f"   时间戳: {result['timestamp']}")
            print(f"\n📤 输出结果:")
            print(result['stdout'])
        else:
            print(f"\n❌ 任务执行失败!")
            print(f"   错误信息: {result.get('stderr', 'Unknown error')}")

        return result
    except Exception as e:
        print(f"❌ 任务执行请求失败: {e}")
        return None

def demo_python_execution():
    """演示4: Python代码执行"""
    print_header("演示 4: Python代码执行")

    task_id = f"TASK-PY-{int(time.time())}"
    python_code = '''
import json
import datetime

print(f"Python execution started at {datetime.datetime.now()}")
data = {
    "task": "Python Code Demo",
    "timestamp": str(datetime.datetime.now()),
    "result": "Python code executed successfully!"
}
print(f"Generated data: {json.dumps(data, indent=2)}")
print("Python execution completed!")
'''

    print_step(1, f"执行Python代码 {task_id}")

    try:
        response = requests.post(
            "http://localhost:8002/execute/task",
            json={
                "task_id": task_id,
                "command": f'python -c {json.dumps(python_code)}',
                "execution_type": "python"
            }
        )

        result = response.json()

        if result.get("success"):
            print(f"\n✅ Python代码执行成功!")
            print(f"   执行时间: {result['execution_time']:.3f}s")
            print(f"\n📤 输出结果:")
            print(result['stdout'])
        else:
            print(f"\n❌ Python代码执行失败!")
            print(f"   错误信息: {result.get('stderr', 'Unknown error')}")

        return result
    except Exception as e:
        print(f"❌ Python执行请求失败: {e}")
        return None

def demo_batch_execution():
    """演示5: 批量执行"""
    print_header("演示 5: 批量任务执行")

    tasks = [
        {"id": f"TASK-B1-{int(time.time())}", "cmd": "echo 'Batch task 1' && sleep 1 && echo 'Done 1'"},
        {"id": f"TASK-B2-{int(time.time())}", "cmd": "echo 'Batch task 2' && sleep 1 && echo 'Done 2'"},
        {"id": f"TASK-B3-{int(time.time())}", "cmd": "echo 'Batch task 3' && sleep 1 && echo 'Done 3'"},
    ]

    print_step(1, f"批量执行 {len(tasks)} 个任务")
    for task in tasks:
        print(f"   - {task['id']}: {task['cmd'][:50]}...")

    try:
        # 先执行单个任务（批量API可能不存在，使用循环代替）
        results = []
        for task in tasks:
            response = requests.post(
                "http://localhost:8002/execute/task",
                json={
                    "task_id": task["id"],
                    "command": task["cmd"],
                    "execution_type": "shell"
                }
            )
            results.append(response.json())
            time.sleep(0.5)  # 稍作延迟

        success_count = sum(1 for r in results if r.get("success"))

        print(f"\n✅ 批量执行完成!")
        print(f"   成功: {success_count}/{len(tasks)}")
        print(f"   失败: {len(tasks) - success_count}/{len(tasks)}")

        return results
    except Exception as e:
        print(f"❌ 批量执行失败: {e}")
        return None

def demo_execution_status():
    """演示6: 执行状态查询"""
    print_header("演示 6: 执行状态查询")

    task_id = f"TASK-STATUS-{int(time.time())}"
    command = f'echo "Status check for {task_id}" && echo "Status: OK"'

    print_step(1, f"执行任务并查询状态")

    # 执行任务
    print(f"   执行任务: {task_id}")
    response = requests.post(
        "http://localhost:8002/execute/task",
        json={
            "task_id": task_id,
            "command": command,
            "execution_type": "shell"
        }
    )
    execution_result = response.json()

    # 查询状态
    print_step(2, f"查询任务状态")
    time.sleep(1)
    status_response = requests.get(f"http://localhost:8002/execute/status/{task_id}")
    status_result = status_response.json()

    print(f"\n📊 执行结果:")
    print(f"   状态: {'成功' if execution_result.get('success') else '失败'}")
    print(f"   执行时间: {execution_result['execution_time']:.3f}s")

    print(f"\n📊 查询结果:")
    print(f"   任务ID: {status_result['task_id']}")
    print(f"   状态: {status_result['status']}")
    print(f"   执行结果: {status_result['execution_result'][:100]}...")

    return status_result

def print_summary():
    """打印总结"""
    print_header("🎉 本地任务执行系统演示完成")

    print("\n✅ 系统特性:")
    print("   📌 支持本地Shell命令执行")
    print("   📌 支持Python代码执行")
    print("   📌 实时执行状态反馈")
    print("   📌 任务结果持久化存储")
    print("   📌 批量任务执行")
    print("   📌 完整的错误处理")

    print("\n🌐 访问地址:")
    print("   🎯 智能任务看板: http://localhost:8001/task-board-execution.html")
    print("   📚 任务API文档: http://localhost:8000/docs")
    print("   ⚡ 执行器API文档: http://localhost:8002/docs")

    print("\n🚀 下一步:")
    print("   1. 打开浏览器访问任务看板")
    print("   2. 点击🚀按钮执行任务")
    print("   3. 观察任务状态的实时更新")

def main():
    """主函数"""
    print("\n")
    print("="*70)
    print("  🎯 本地任务执行系统 - 完整功能演示")
    print("  " + "="*66)
    print()

    # 检查API健康状态
    if not demo_api_health_check():
        print("\n❌ API服务不可用，请确保以下服务正在运行:")
        print("   - 任务管理API: python simple_task_api.py")
        print("   - 终端执行器: python terminal_task_executor.py")
        return

    # 获取任务摘要
    summary = demo_task_summary()
    if not summary:
        print("\n❌ 无法获取任务摘要")
        return

    # 演示单任务执行
    demo_single_task_execution()

    # 演示Python执行
    demo_python_execution()

    # 演示批量执行
    demo_batch_execution()

    # 演示状态查询
    demo_execution_status()

    # 打印总结
    print_summary()

if __name__ == "__main__":
    main()
