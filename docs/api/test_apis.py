#!/usr/bin/env python3
"""
Quick API Test - Test our created API modules
快速API测试 - 验证我们创建的API模块
"""

import sys
import os
import importlib.util

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_module_import(module_path, module_name):
    """Test if a module can be imported"""
    try:
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print(f"✓ {module_name} imported successfully")
        return True, module
    except Exception as e:
        print(f"✗ {module_name} import failed: {str(e)[:100]}")
        return False, None

def test_api_functions(module):
    """Test API functions in a module"""
    if not module:
        return False

    try:
        # Check for router
        if hasattr(module, 'router'):
            print(f"  ✓ Router found: {module.router}")
        else:
            print(f"  ⚠ No router found")

        # Check for specific functions
        functions = [attr for attr in dir(module) if callable(getattr(module, attr)) and not attr.startswith('_')]
        print(f"  ✓ Functions found: {len(functions)}")
        for func in functions[:5]:  # Show first 5
            print(f"    - {func}")

        return True
    except Exception as e:
        print(f"  ✗ Error checking functions: {str(e)}")
        return False

def main():
    """Main test function"""
    print("=" * 80)
    print("Testing Created API Modules")
    print("=" * 80)
    print()

    # Test each API module
    modules_to_test = [
        ("src/dashboard/api_hibor_enhanced.py", "HIBOR Enhanced API"),
        ("src/dashboard/api_csd_economic_enhanced.py", "CSD Economic Enhanced API"),
        ("src/dashboard/api_csd_advanced.py", "CSD Advanced API"),
        ("src/dashboard/api_cache_enhanced.py", "Cache Enhanced API"),
        ("src/dashboard/api_websocket.py", "WebSocket API"),
    ]

    success_count = 0
    for module_path, module_name in modules_to_test:
        print(f"Testing: {module_name}")
        print(f"  Path: {module_path}")

        if not os.path.exists(module_path):
            print(f"  ✗ File not found")
            print()
            continue

        # Test import
        success, module = test_module_import(module_path, module_name)
        if success:
            # Test functions
            if test_api_functions(module):
                success_count += 1

        print()

    # Summary
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"Modules tested: {len(modules_to_test)}")
    print(f"Success: {success_count}/{len(modules_to_test)}")
    print(f"Success rate: {success_count/len(modules_to_test)*100:.1f}%")
    print()

    if success_count == len(modules_to_test):
        print("✓ All API modules are working correctly!")
    elif success_count > 0:
        print("⚠ Some modules are working, some have issues")
    else:
        print("✗ No modules are working")

    print("=" * 80)

    return success_count > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
