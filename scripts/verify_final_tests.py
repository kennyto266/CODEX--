#!/usr/bin/env python
"""
快速验证最终测试套件

检查所有测试文件是否存在且可导入
"""

import os
import sys
import importlib.util
from pathlib import Path


def check_test_file(test_path: str) -> dict:
    """检查测试文件"""
    result = {
        'path': test_path,
        'exists': False,
        'importable': False,
        'has_tests': False,
        'error': None
    }

    if not os.path.exists(test_path):
        result['error'] = "文件不存在"
        return result

    result['exists'] = True

    # 尝试导入
    try:
        spec = importlib.util.spec_from_file_location("test_module", test_path)
        if spec and spec.loader:
            result['importable'] = True
        else:
            result['error'] = "无法创建模块规范"
    except Exception as e:
        result['error'] = f"导入失败: {e}"
        return result

    # 检查是否包含pytest测试
    try:
        with open(test_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 查找pytest标记
        if '@pytest.mark.' in content or 'def test_' in content:
            result['has_tests'] = True
        else:
            result['error'] = "未找到测试函数"
    except Exception as e:
        result['error'] = f"读取文件失败: {e}"

    return result


def main():
    """主函数"""
    print("=" * 80)
    print("最终测试套件快速验证")
    print("=" * 80)
    print()

    # 测试文件列表
    test_files = {
        'T240': 'tests/regression/test_full_regression.py',
        'T241': 'tests/performance/test_final_benchmarks.py',
        'T242': 'tests/security/test_security_audit.py',
        'T243': 'tests/acceptance/test_user_acceptance.py',
        'T244': 'scripts/docs_review.py'
    }

    all_passed = True

    for test_name, test_path in test_files.items():
        print(f"检查 {test_name}: {test_path}")
        result = check_test_file(test_path)

        if result['exists'] and result['importable'] and result['has_tests']:
            print(f"  ✓ 验证通过")
        else:
            print(f"  ✗ 验证失败")
            all_passed = False

            if result['error']:
                print(f"    错误: {result['error']}")

        if not result['exists']:
            print(f"    文件不存在")

        if not result['importable']:
            print(f"    无法导入")

        if not result['has_tests']:
            print(f"    未包含测试")

        print()

    # 检查目录结构
    print("=" * 80)
    print("检查目录结构")
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
            print(f"✓ {directory} 目录存在")
        else:
            print(f"✗ {directory} 目录不存在")
            all_passed = False

    print()

    # 检查__init__.py文件
    print("=" * 80)
    print("检查__init__.py文件")
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
            print(f"✓ {init_file} 存在")
        else:
            print(f"✗ {init_file} 不存在")
            all_passed = False

    print()

    # 总结
    print("=" * 80)
    print("验证总结")
    print("=" * 80)
    print()

    if all_passed:
        print("✓ 所有检查通过")
        print("\n可以运行测试:")
        print("  python scripts/run_final_tests.py")
        print("\n或运行单个测试:")
        for test_name, test_path in test_files.items():
            print(f"  pytest {test_path} -v")
        return 0
    else:
        print("✗ 存在未通过检查的项目")
        print("\n请修复上述问题后再运行测试")
        return 1


if __name__ == '__main__':
    sys.exit(main())
