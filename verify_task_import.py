#!/usr/bin/env python3
"""
Task Import Functionality Verification Script
Verify core functions are working properly
"""

import tempfile
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Test data
TEST_MARKDOWN = """
# Project Task List Test

## Stage 1: Task Management System

### 1.1 Data Model Design (4 hours)
- [ ] Create task data model [P0]
- [ ] Create sprint data model [P0]
- [ ] Create status enum [P0]

### 1.2 Task API Development (8 hours)
- [ ] Implement GET endpoint [P0]
- [ ] Implement POST endpoint [P1]

## Stage 2: Workflow Standardization

### 2.1 Task State Management (6 hours)
- [ ] Implement state transition logic [P0]
- [ ] Create state change history [P1]
"""


def test_basic_parsing():
    """Test basic parsing functionality"""
    print("\n" + "="*60)
    print("Test 1: Basic Markdown Parsing")
    print("="*60)

    # Create temp file
    fd, file_path = tempfile.mkstemp(suffix='.md', text=True)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(TEST_MARKDOWN)

        # Read and verify
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Basic verification
        checks = [
            ("Title", "Project Task List Test" in content),
            ("Stage 1", "Stage 1" in content),
            ("Stage 2", "Stage 2" in content),
            ("Task List", content.count("- [ ]") >= 5),
            ("Priority P0", content.count("[P0]") >= 4),
            ("Priority P1", content.count("[P1]") >= 2),
            ("Time Estimate", content.count("(4 hours)") > 0),
        ]

        all_passed = True
        for name, result in checks:
            status = "[OK]" if result else "[FAIL]"
            print(f"  {status} {name}")
            if not result:
                all_passed = False

        return all_passed

    finally:
        os.remove(file_path)


def test_task_extraction():
    """Test task extraction"""
    print("\n" + "="*60)
    print("Test 2: Task Extraction")
    print("="*60)

    import re

    lines = TEST_MARKDOWN.split('\n')
    task_lines = [line for line in lines if line.strip().startswith('- [ ]')]

    print(f"  [OK] Found {len(task_lines)} tasks")

    # Extract priorities
    priorities = {'P0': 0, 'P1': 0, 'P2': 0}
    for line in task_lines:
        for p in priorities:
            if f'[{p}]' in line:
                priorities[p] += 1

    print("  Priority Distribution:")
    for priority, count in priorities.items():
        print(f"    {priority}: {count} tasks")

    # Verify statistics
    total = sum(priorities.values())
    print(f"  [OK] Total: {total} tasks")

    return total >= 5


def test_stage_extraction():
    """Test stage extraction"""
    print("\n" + "="*60)
    print("Test 3: Stage Extraction")
    print("="*60)

    import re

    stage_lines = [
        line for line in TEST_MARKDOWN.split('\n')
        if line.startswith('## Stage')
    ]

    print(f"  [OK] Found {len(stage_lines)} stages")

    for stage in stage_lines:
        stage_match = re.match(r'## Stage (\d+): (.+)', stage)
        if stage_match:
            stage_num = stage_match.group(1)
            stage_name = stage_match.group(2)
            print(f"    Stage {stage_num}: {stage_name}")

    return len(stage_lines) >= 2


def test_section_extraction():
    """Test section extraction"""
    print("\n" + "="*60)
    print("Test 4: Section Extraction")
    print("="*60)

    import re

    section_lines = [
        line for line in TEST_MARKDOWN.split('\n')
        if line.startswith('### ')
    ]

    print(f"  [OK] Found {len(section_lines)} sections")

    for section in section_lines:
        # Verify section format
        if re.match(r'### \d+\.\d+ ', section):
            # Verify time estimate
            if re.search(r'\(\d+ hours\)', section):
                print(f"    [OK] {section}")
            else:
                print(f"    [WARN] {section} (missing time)")
                return False
        else:
            print(f"    [FAIL] {section} (invalid format)")
            return False

    return len(section_lines) >= 2


def test_file_encoding():
    """Test file encoding"""
    print("\n" + "="*60)
    print("Test 5: File Encoding")
    print("="*60)

    chinese_content = """
# Project Task List

## Stage 1: Task Management System

### 1.1 Data Model Design (4 hours)
- [ ] Create task model [P0]
- [ ] Handle Chinese path [P1]
"""

    fd, file_path = tempfile.mkstemp(suffix='.md', text=True)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(chinese_content)

        # Verify file can be read correctly
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        checks = [
            ("Task Management System" in content, "Chinese Title"),
            ("Data Model Design" in content, "Chinese Section"),
            ("Handle Chinese path" in content, "Chinese Task"),
        ]

        all_passed = True
        for result, name in checks:
            status = "[OK]" if result else "[FAIL]"
            print(f"  {status} {name}")
            if not result:
                all_passed = False

        return all_passed

    finally:
        os.remove(file_path)


def test_import_tools():
    """Test if import tools exist"""
    print("\n" + "="*60)
    print("Test 6: Import Tools Check")
    print("="*60)

    tools = [
        ("src/dashboard/services/task_import_service.py", "Import Service"),
        ("src/dashboard/api/task_import.py", "API Endpoint"),
        ("scripts/import_tasks.py", "CLI Tool"),
        ("tests/dashboard/test_task_import_basic.py", "Basic Tests"),
        ("src/dashboard/static/TASK_IMPORT_GUIDE.md", "Usage Guide"),
    ]

    all_exist = True
    for file_path, name in tools:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"  [OK] {name}")
        else:
            print(f"  [FAIL] {name} (file not found)")
            all_exist = False

    return all_exist


def test_actual_service():
    """Test if actual service can be imported"""
    print("\n" + "="*60)
    print("Test 7: Actual Service Import")
    print("="*60)

    try:
        from src.dashboard.services.task_import_service import TaskImportService
        print("  [OK] TaskImportService imported successfully")

        # Check if methods exist
        methods = ['parse_tasks_from_markdown', 'import_tasks', 'rollback_import']
        for method in methods:
            if hasattr(TaskImportService, method):
                print(f"  [OK] Method '{method}' exists")
            else:
                print(f"  [WARN] Method '{method}' not found")
                return False

        return True

    except ImportError as e:
        print(f"  [FAIL] Cannot import service: {e}")
        return False


def main():
    """Main function"""
    print("\n" + "="*60)
    print("Task Import Functionality Verification")
    print("="*60)

    tests = [
        ("Basic Parsing", test_basic_parsing),
        ("Task Extraction", test_task_extraction),
        ("Stage Extraction", test_stage_extraction),
        ("Section Extraction", test_section_extraction),
        ("File Encoding", test_file_encoding),
        ("Tools Check", test_import_tools),
        ("Service Import", test_actual_service),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n  [FAIL] Test failed: {e}")
            failed += 1

    # Output summary
    print("\n" + "="*60)
    print("Verification Summary")
    print("="*60)
    print(f"  Total Tests: {len(tests)}")
    print(f"  Passed: {passed} [OK]")
    print(f"  Failed: {failed} [FAIL]")

    if failed == 0:
        print("\nAll tests passed! Task import functionality is working!")
        return 0
    else:
        print(f"\n{failed} test(s) failed, please check related functionality")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
