#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Fixed Dashboard API Implementation
"""

import sys
import os
import asyncio
import json
from pathlib import Path

# Setup paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))
os.environ.setdefault("PYTHONPATH", str(project_root))

from fixed_dashboard import create_app, DashboardDataService


async def test_dashboard():
    """Test all dashboard API endpoints"""
    print("=" * 70)
    print("[TEST] CODEX Dashboard Implementation Test")
    print("=" * 70)

    tests_passed = 0
    tests_failed = 0

    # Test 1: Create app
    print("\n[1] Creating FastAPI application...")
    try:
        app = create_app()
        print("    OK - FastAPI app created")
        print("    Routes registered: " + str(len(app.routes)))
        tests_passed += 1
    except Exception as e:
        print("    FAILED: " + str(e))
        tests_failed += 1
        return False

    # Test 2: Data service
    print("\n[2] Creating DashboardDataService...")
    try:
        service = DashboardDataService()
        print("    OK - Data service created")
        tests_passed += 1
    except Exception as e:
        print("    FAILED: " + str(e))
        tests_failed += 1
        return False

    # Test 3: Health check
    print("\n[3] Testing /api/health endpoint...")
    try:
        result = await service.get_health()
        assert result["status"] == "ok", "status should be 'ok'"
        assert "timestamp" in result, "missing timestamp"
        print("    OK - Health check endpoint works")
        tests_passed += 1
    except Exception as e:
        print("    FAILED: " + str(e))
        tests_failed += 1

    # Test 4: Portfolio
    print("\n[4] Testing /api/trading/portfolio endpoint...")
    try:
        result = await service.get_portfolio()
        assert "portfolio_value" in result
        assert "initial_capital" in result
        print("    OK - Portfolio endpoint: Value=$" + str(result['portfolio_value']))
        tests_passed += 1
    except Exception as e:
        print("    FAILED: " + str(e))
        tests_failed += 1

    # Test 5: Performance
    print("\n[5] Testing /api/trading/performance endpoint...")
    try:
        result = await service.get_performance()
        assert "sharpe_ratio" in result
        assert "max_drawdown" in result
        print("    OK - Performance endpoint works")
        tests_passed += 1
    except Exception as e:
        print("    FAILED: " + str(e))
        tests_failed += 1

    # Test 6: System status
    print("\n[6] Testing /api/system/status endpoint...")
    try:
        result = await service.get_system_status()
        assert result["status"] == "operational"
        assert result["agents"]["total"] == 7
        print("    OK - System status: operational")
        tests_passed += 1
    except Exception as e:
        print("    FAILED: " + str(e))
        tests_failed += 1

    # Test 7: System refresh
    print("\n[7] Testing /api/system/refresh endpoint...")
    try:
        result = await service.refresh_system(hard_refresh=False)
        assert result["status"] == "success"
        print("    OK - System refresh endpoint works")
        tests_passed += 1
    except Exception as e:
        print("    FAILED: " + str(e))
        tests_failed += 1

    # Test 8: Response format
    print("\n[8] Validating response formats...")
    try:
        endpoints = {
            "/api/health": await service.get_health(),
            "/api/trading/portfolio": await service.get_portfolio(),
            "/api/trading/performance": await service.get_performance(),
            "/api/system/status": await service.get_system_status(),
        }
        for endpoint, data in endpoints.items():
            json.dumps(data)  # Validate JSON serializable
            assert isinstance(data, dict)
            assert len(data) > 0
        print("    OK - All responses are valid JSON")
        tests_passed += 1
    except Exception as e:
        print("    FAILED: " + str(e))
        tests_failed += 1

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print("Passed: " + str(tests_passed))
    print("Failed: " + str(tests_failed))

    if tests_failed == 0:
        print("\nOK - All tests passed!")
        print("Dashboard implementation is ready for deployment")
        return True
    else:
        print("\nFAILED - Some tests failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_dashboard())
    sys.exit(0 if success else 1)
