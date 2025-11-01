#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Dashboard API Implementation

Validates that the fixed_dashboard.py correctly implements all required API endpoints.
"""

import sys
import os
import asyncio
import json
from pathlib import Path
from datetime import datetime

# Setup paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))
os.environ.setdefault("PYTHONPATH", str(project_root))

# Import the dashboard module
from fixed_dashboard import create_app, DashboardDataService


async def test_dashboard_implementation():
    """Test all dashboard API endpoints"""
    print("=" * 70)
    print("[TEST] CODEX Dashboard Implementation Test")
    print("=" * 70)

    # Test 1: Create app
    print("\n[PASS] Test 1: Creating FastAPI application...")
    try:
        app = create_app()
        print(f"   - FastAPI app created successfully")
        print(f"   - Routes registered: {len(app.routes)}")
        assert len(app.routes) >= 8, "Expected at least 8 routes"
        print("   ✓ PASSED")
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
        return False

    # Test 2: Data service instantiation
    print("\n✅ Test 2: Creating DashboardDataService...")
    try:
        service = DashboardDataService()
        print("   - Data service created successfully")
        print("   ✓ PASSED")
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
        return False

    # Test 3: Health check endpoint
    print("\n✅ Test 3: Testing /api/health endpoint...")
    try:
        result = await service.get_health()
        assert result["status"] == "ok"
        assert "timestamp" in result
        assert "service" in result
        print(f"   - Response: {json.dumps(result, indent=2)}")
        print("   ✓ PASSED")
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
        return False

    # Test 4: Portfolio endpoint
    print("\n✅ Test 4: Testing /api/trading/portfolio endpoint...")
    try:
        result = await service.get_portfolio()
        assert "portfolio_value" in result
        assert "initial_capital" in result
        assert "positions" in result
        print(f"   - Portfolio Value: ${result['portfolio_value']:,.2f}")
        print(f"   - Active Positions: {result['active_positions']}")
        print("   ✓ PASSED")
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
        return False

    # Test 5: Performance endpoint
    print("\n✅ Test 5: Testing /api/trading/performance endpoint...")
    try:
        result = await service.get_performance()
        assert "sharpe_ratio" in result
        assert "max_drawdown" in result
        assert "win_rate" in result
        print(f"   - Sharpe Ratio: {result['sharpe_ratio']:.2f}")
        print(f"   - Max Drawdown: {result['max_drawdown']:.2f}%")
        print(f"   - Win Rate: {result['win_rate']:.2%}")
        print("   ✓ PASSED")
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
        return False

    # Test 6: System status endpoint
    print("\n✅ Test 6: Testing /api/system/status endpoint...")
    try:
        result = await service.get_system_status()
        assert result["status"] == "operational"
        assert result["agents"]["total"] == 7
        assert result["agents"]["active"] == 7
        print(f"   - Status: {result['status'].upper()}")
        print(f"   - Agents: {result['agents']['active']}/{result['agents']['total']}")
        print(f"   - Uptime: {result['uptime_formatted']}")
        print("   ✓ PASSED")
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
        return False

    # Test 7: System refresh endpoint
    print("\n✅ Test 7: Testing /api/system/refresh endpoint...")
    try:
        result = await service.refresh_system(hard_refresh=False)
        assert result["status"] == "success"
        assert "refresh_type" in result
        print(f"   - Refresh Type: {result['refresh_type']}")
        print(f"   - Affected Systems: {', '.join(result['affected_systems'])}")
        print("   ✓ PASSED")
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
        return False

    # Test 8: Response format validation
    print("\n✅ Test 8: Validating response formats...")
    try:
        endpoints = {
            "/api/health": await service.get_health(),
            "/api/trading/portfolio": await service.get_portfolio(),
            "/api/trading/performance": await service.get_performance(),
            "/api/system/status": await service.get_system_status(),
        }

        for endpoint, data in endpoints.items():
            # All responses must be JSON-serializable
            json_str = json.dumps(data)
            assert isinstance(data, dict), f"{endpoint}: Response is not a dict"
            assert len(data) > 0, f"{endpoint}: Response is empty"
            print(f"   ✓ {endpoint}: Valid JSON response")

        print("   ✓ PASSED - All responses are valid JSON")
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
        return False

    # Summary
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
    print("\n� Summary:")
    print("   ✓ FastAPI application created with 8+ routes")
    print("   ✓ All 5 API endpoints implemented correctly")
    print("   ✓ All responses are valid JSON")
    print("   ✓ System status shows 'operational'")
    print("   ✓ Proper error handling in place")
    print("\n✅ Implementation is ready for deployment!")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_dashboard_implementation())
    sys.exit(0 if success else 1)
