#!/usr/bin/env python3
"""
Simple Task Execution Demo
"""

import subprocess
import json

def demo_python_execution():
    """Demo Python code execution"""
    print("\n" + "="*60)
    print("DEMO 1: Execute Python Code")
    print("="*60)

    code = """
print("Starting data processing...")
import json
data = {"name": "Demo Task", "value": 100}
print(f"Processing data: {data}")
print("Data processing complete!")
result = {"processed": True, "count": 100}
print(f"Result: {result}")
"""

    print("Executing Python code...")
    result = subprocess.run(["python", "-c", code], capture_output=True, text=True)

    if result.returncode == 0:
        print("[OK] Python execution successful!")
        print("Output:")
        print(result.stdout)
    else:
        print("[ERROR] Python execution failed!")
        print(result.stderr)

def demo_shell_execution():
    """Demo Shell command execution"""
    print("\n" + "="*60)
    print("DEMO 2: Execute Shell Command")
    print("="*60)

    command = "echo 'System check start' && python --version && echo 'System check complete'"

    print(f"Executing: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        print("[OK] Shell execution successful!")
        print("Output:")
        print(result.stdout)
    else:
        print("[ERROR] Shell execution failed!")
        print(result.stderr)

def demo_api_execution():
    """Demo API call execution"""
    print("\n" + "="*60)
    print("DEMO 3: Execute API Call")
    print("="*60)

    print("Calling local API: http://localhost:8000/tasks/summary")
    result = subprocess.run(
        ["curl", "-s", "http://localhost:8000/tasks/summary"],
        capture_output=True, text=True
    )

    if result.returncode == 0:
        print("[OK] API call successful!")
        print("Response:")
        try:
            data = json.loads(result.stdout)
            print(json.dumps(data, indent=2))
        except:
            print(result.stdout)
    else:
        print("[ERROR] API call failed!")
        print(result.stderr)

if __name__ == "__main__":
    print("="*60)
    print("TASK EXECUTION DEMO")
    print("="*60)
    print("\nThis demo shows REAL local task execution:")
    print("- Execute Python code")
    print("- Run Shell commands")
    print("- Make API calls")

    demo_python_execution()
    demo_shell_execution()
    demo_api_execution()

    print("\n" + "="*60)
    print("DEMO COMPLETED!")
    print("="*60)
    print("\nAll tasks executed LOCALLY on this machine!")
