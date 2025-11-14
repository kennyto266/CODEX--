#!/usr/bin/env python3
"""
Simple File Check - Verify our created files
简单文件检查 - 验证创建的文件
"""

import os
import re

def check_file(filepath, expected_patterns):
    """Check if file exists and contains expected patterns"""
    print(f"\nChecking: {filepath}")

    if not os.path.exists(filepath):
        print(f"  [MISSING] File not found")
        return False

    # Get file size
    size = os.path.getsize(filepath)
    print(f"  [OK] File exists, size: {size} bytes")

    # Read and check patterns
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Count lines
        lines = len(content.splitlines())
        print(f"  [OK] Lines: {lines}")

        # Check patterns
        found = 0
        for pattern in expected_patterns:
            if pattern in content:
                found += 1
                print(f"  [OK] Pattern found: {pattern}")
            else:
                print(f"  [MISSING] Pattern not found: {pattern}")

        print(f"  Result: {found}/{len(expected_patterns)} patterns found")
        return found == len(expected_patterns)

    except Exception as e:
        print(f"  [ERROR] Failed to read file: {e}")
        return False

def main():
    """Main check function"""
    print("=" * 80)
    print("Checking Created Files")
    print("=" * 80)

    # List of files to check
    files_to_check = [
        {
            "path": "src/dashboard/api_hibor_enhanced.py",
            "patterns": ["router = APIRouter", "@router.get", "class HiborResponse"]
        },
        {
            "path": "src/dashboard/api_csd_advanced.py",
            "patterns": ["router = APIRouter", "class UnemploymentData", "class RetailSalesData"]
        },
        {
            "path": "src/dashboard/api_websocket.py",
            "patterns": ["router = APIRouter", "ConnectionManager", "WebSocketDisconnect"]
        },
        {
            "path": "src/performance/performance_optimizer.py",
            "patterns": ["DatabaseOptimizer", "MemoryOptimizer", "PerformanceMonitor"]
        },
        {
            "path": "deploy_production.py",
            "patterns": ["ProductionDeployment", "check_environment", "run_tests"]
        },
        {
            "path": "docs/TECHNICAL_DOCUMENTATION.md",
            "patterns": ["# API文档", "# 系统概述", "## 架构设计"]
        },
    ]

    success_count = 0
    for file_info in files_to_check:
        if check_file(file_info["path"], file_info["patterns"]):
            success_count += 1

    # Summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Files checked: {len(files_to_check)}")
    print(f"Files passed: {success_count}")
    print(f"Pass rate: {success_count/len(files_to_check)*100:.1f}%")
    print()

    if success_count == len(files_to_check):
        print("All files are correctly created!")
    elif success_count > len(files_to_check) // 2:
        print("Most files are correct, some need attention")
    else:
        print("Many files have issues")

    print("=" * 80)

    return success_count == len(files_to_check)

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
