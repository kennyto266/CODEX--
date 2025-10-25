"""
Test script to verify the new frontend dashboard implementation
"""

import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

def test_template_exists():
    """Test if the HTML template file exists"""
    template_path = os.path.join('src', 'dashboard', 'templates', 'index.html')
    if os.path.exists(template_path):
        print(f"✅ Template file exists: {template_path}")
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"✅ Template file size: {len(content)} bytes")
            return True
    else:
        print(f"❌ Template file not found: {template_path}")
        return False

def test_application_import():
    """Test if application.py can be imported"""
    try:
        from src.application import app
        print("✅ Application imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import application: {e}")
        return False

def test_root_endpoint():
    """Test the root endpoint configuration"""
    try:
        from src.application import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/")

        if response.status_code == 200:
            print(f"✅ Root endpoint responded with status 200")
            if "CODEX Trading System" in response.text:
                print("✅ Response contains expected content")
                return True
            else:
                print("❌ Response missing expected content")
                return False
        else:
            print(f"❌ Root endpoint responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to test root endpoint: {e}")
        return False

def test_api_info_endpoint():
    """Test the new /api/info endpoint"""
    try:
        from src.application import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/api/info")

        if response.status_code == 200:
            print(f"✅ /api/info endpoint responded with status 200")
            data = response.json()
            if "message" in data and "endpoints" in data:
                print("✅ /api/info response has expected structure")
                return True
            else:
                print("❌ /api/info response missing expected fields")
                return False
        else:
            print(f"❌ /api/info endpoint responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to test /api/info endpoint: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("CODEX Trading System - Frontend Dashboard Tests")
    print("=" * 60 + "\n")

    tests = [
        ("Template File Exists", test_template_exists),
        ("Application Import", test_application_import),
        ("Root Endpoint", test_root_endpoint),
        ("API Info Endpoint", test_api_info_endpoint),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running test: {test_name}")
        print("-" * 60)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))

    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Frontend dashboard is ready.")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
