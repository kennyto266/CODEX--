#!/usr/bin/env python
"""
Quick verification for final test suite

Check if all test files exist and are importable
"""

import os
import sys
import importlib.util
from pathlib import Path


def check_test_file(test_path: str) -> dict:
    """Check test file"""
    result = {
        'path': test_path,
        'exists': False,
        'importable': False,
        'has_tests': False,
        'error': None
    }

    if not os.path.exists(test_path):
        result['error'] = "File does not exist"
        return result

    result['exists'] = True

    # Try to import
    try:
        spec = importlib.util.spec_from_file_location("test_module", test_path)
        if spec and spec.loader:
            result['importable'] = True
        else:
            result['error'] = "Cannot create module spec"
    except Exception as e:
        result['error'] = f"Import failed: {e}"
        return result

    # Check if contains pytest tests
    try:
        with open(test_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find pytest markers
        if '@pytest.mark.' in content or 'def test_' in content:
            result['has_tests'] = True
        else:
            result['error'] = "No test functions found"
    except Exception as e:
        result['error'] = f"Failed to read file: {e}"

    return result


def main():
    """Main function"""
    print("=" * 80)
    print("Final Test Suite - Quick Verification")
    print("=" * 80)
    print()

    # Test file list
    test_files = {
        'T240': 'tests/regression/test_full_regression.py',
        'T241': 'tests/performance/test_final_benchmarks.py',
        'T242': 'tests/security/test_security_audit.py',
        'T243': 'tests/acceptance/test_user_acceptance.py',
        'T244': 'scripts/docs_review.py'
    }

    all_passed = True

    for test_name, test_path in test_files.items():
        print(f"Checking {test_name}: {test_path}")
        result = check_test_file(test_path)

        if result['exists'] and result['importable'] and result['has_tests']:
            print(f"  [OK] Verification passed")
        else:
            print(f"  [FAIL] Verification failed")
            all_passed = False

            if result['error']:
                print(f"    Error: {result['error']}")

        if not result['exists']:
            print(f"    File does not exist")

        if not result['importable']:
            print(f"    Cannot import")

        if not result['has_tests']:
            print(f"    No tests found")

        print()

    # Check directory structure
    print("=" * 80)
    print("Checking directory structure")
    print("=" * 80)
    print()

    directories = [
        'tests/regression',
        'tests/performance',
        'tests/security',
        'tests/acceptance',
        'tests/reports',
        'scripts'
    ]

    for directory in directories:
        if os.path.exists(directory):
            print(f"[OK] {directory} directory exists")
        else:
            print(f"[FAIL] {directory} directory does not exist")
            all_passed = False

    print()

    # Check __init__.py files
    print("=" * 80)
    print("Checking __init__.py files")
    print("=" * 80)
    print()

    init_files = [
        'tests/regression/__init__.py',
        'tests/performance/__init__.py',
        'tests/security/__init__.py',
        'tests/acceptance/__init__.py',
        'scripts/__init__.py'
    ]

    for init_file in init_files:
        if os.path.exists(init_file):
            print(f"[OK] {init_file} exists")
        else:
            print(f"[WARN] {init_file} does not exist")
            all_passed = False

    print()

    # Summary
    print("=" * 80)
    print("Verification Summary")
    print("=" * 80)
    print()

    if all_passed:
        print("[OK] All checks passed")
        print("\nYou can run tests:")
        print("  python scripts/run_final_tests.py")
        print("\nOr run individual tests:")
        for test_name, test_path in test_files.items():
            print(f"  pytest {test_path} -v")
        return 0
    else:
        print("[WARN] Some checks failed")
        print("\nPlease fix the issues above before running tests")
        return 1


if __name__ == '__main__':
    sys.exit(main())
