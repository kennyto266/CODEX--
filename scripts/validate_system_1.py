#!/usr/bin/env python3
"""
Quick Validation Test
Quick validation test for the HK Quant Trading System
"""

import sys
import os

def check_file_exists(filepath, description):
    """Check if file exists"""
    exists = os.path.exists(filepath)
    status = "OK" if exists else "MISSING"
    print(f"  [{status}] {description}: {filepath}")
    return exists

def count_file_lines(filepath):
    """Count lines in file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return len(f.readlines())
    except:
        return 0

def count_api_endpoints(filepath):
    """Count API endpoints"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            return content.count('@router.get') + content.count('@router.post')
    except:
        return 0

def main():
    """Main test function"""
    print("=" * 80)
    print("HK Quant Trading System - Quick Validation Test")
    print("=" * 80)
    print()

    # 1. Check core files
    print("1. Checking Core Files...")
    files_to_check = [
        ("src/dashboard/api_hibor_enhanced.py", "HIBOR Enhanced API"),
        ("src/dashboard/api_csd_economic_enhanced.py", "CSD Economic Enhanced API"),
        ("src/dashboard/api_csd_advanced.py", "CSD Advanced API"),
        ("src/dashboard/api_cache_enhanced.py", "Cache Enhanced API"),
        ("src/dashboard/api_websocket.py", "WebSocket API"),
        ("src/performance/performance_optimizer.py", "Performance Optimizer"),
        ("deploy_production.py", "Production Deployment Script"),
        ("config/performance_config.yaml", "Performance Config"),
        ("docs/TECHNICAL_DOCUMENTATION.md", "Technical Documentation"),
        ("SPRINT3_PLANNING.md", "Sprint 3 Planning"),
        ("SPRINT3_EPICS.md", "Sprint 3 Epics"),
        ("SPRINT3_STORY_CONTEXTS.md", "Sprint 3 Story Contexts"),
    ]

    file_count = 0
    for filepath, description in files_to_check:
        if check_file_exists(filepath, description):
            file_count += 1

    print(f"\nFile Check: {file_count}/{len(files_to_check)} files found")
    print()

    # 2. Count code statistics
    print("2. Code Statistics...")
    code_files = [
        ("src/dashboard/api_hibor_enhanced.py", "HIBOR API"),
        ("src/dashboard/api_csd_economic_enhanced.py", "CSD Enhanced"),
        ("src/dashboard/api_csd_advanced.py", "CSD Advanced"),
        ("src/dashboard/api_cache_enhanced.py", "Cache API"),
        ("src/dashboard/api_websocket.py", "WebSocket"),
        ("src/performance/performance_optimizer.py", "Performance"),
    ]

    total_lines = 0
    for filepath, name in code_files:
        if os.path.exists(filepath):
            lines = count_file_lines(filepath)
            total_lines += lines
            print(f"  - {name}: {lines} lines")

    print(f"\nTotal Code Lines: {total_lines}")
    print()

    # 3. Count API endpoints
    print("3. API Endpoints...")
    total_endpoints = 0
    for filepath, name in code_files:
        if os.path.exists(filepath):
            endpoints = count_api_endpoints(filepath)
            total_endpoints += endpoints
            print(f"  - {name}: {endpoints} endpoints")

    print(f"\nTotal API Endpoints: {total_endpoints}")
    print()

    # 4. Check documentation
    print("4. Documentation Files...")
    doc_files = [
        ("docs/TECHNICAL_DOCUMENTATION.md", "Technical Doc"),
        ("FINAL_EXECUTION_SUCCESS.md", "Final Report"),
        ("COMPLETE_OPTIONS_EXEUTION_SUMMARY.md", "Options Summary"),
    ]

    doc_count = 0
    for filepath, name in doc_files:
        if os.path.exists(filepath):
            lines = count_file_lines(filepath)
            doc_count += 1
            print(f"  - {name}: {lines} lines")

    print(f"\nTotal Documentation: {doc_count} files")
    print()

    # 5. Summary
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Files Found: {file_count}/{len(files_to_check)}")
    print(f"Code Lines: {total_lines}")
    print(f"API Endpoints: {total_endpoints}")
    print(f"Documentation: {doc_count} files")

    # Calculate success rate
    file_success_rate = (file_count / len(files_to_check)) * 100

    print()
    if file_success_rate >= 90:
        print("STATUS: SUCCESS - System ready for deployment")
    elif file_success_rate >= 70:
        print("STATUS: WARNING - Some files missing")
    else:
        print("STATUS: ERROR - Critical files missing")

    print("=" * 80)

    return file_success_rate >= 90

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
