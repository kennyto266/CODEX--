#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Test - Verify data.gov.hk Crawler Connection
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("[TEST] data.gov.hk Crawler Connectivity")
print("=" * 70)

try:
    print("\n[STEP 1] Loading configuration...")
    from src.utils import load_config
    config = load_config("gov_crawler/config.yaml")
    print("[OK] Configuration loaded")

    print("\n[STEP 2] Initializing API Handler...")
    from src.api_handler import DataGovHKAPI
    api = DataGovHKAPI(config)
    print("[OK] API Handler initialized")

    print("\n[STEP 3] Checking API connectivity...")
    is_healthy = api.check_connectivity()

    if is_healthy:
        print("[OK] API connection successful!")
        print("  - Base URL: https://data.gov.hk/tc-data")
        print("  - API Status: Healthy")

        stats = api.get_api_statistics()
        print(f"  - Total Requests: {stats['total_requests']}")
        print(f"  - Connection Status: {'Healthy' if stats['is_healthy'] else 'Unhealthy'}")
    else:
        print("[FAIL] API connection failed")
        print("  Possible causes:")
        print("  - Network connection issue")
        print("  - data.gov.hk service unavailable")
        print("  - Firewall blocking")

    print("\n[STEP 4] Discovering data resources...")
    from src.data_registry import DataRegistry
    registry = DataRegistry()

    # Quick test: discover only first 10 resources
    print("  Scanning data.gov.hk...")
    discovered = registry.discover_all_datasets(max_rows=10)
    print(f"[OK] Discovered {discovered} resources")

    stats = registry.get_registry_statistics()
    print(f"\nResource Statistics:")
    print(f"  - Total Resources: {stats['total_resources']}")
    print(f"  - Total Packages: {stats['total_packages']}")
    print(f"  - Accessible Resources: {stats['accessible_resources']}")
    if stats['formats']:
        print(f"  - Data Formats: {stats['formats']}")

    print("\n" + "=" * 70)
    print("[SUCCESS] Test passed - Crawler can connect to data.gov.hk!")
    print("=" * 70)

except Exception as e:
    print(f"\n[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()
    print("\n" + "=" * 70)
    print("[FAIL] Connection failed - Please check:")
    print("  1. Network connection")
    print("  2. config.yaml configuration")
    print("  3. data.gov.hk service status")
    print("=" * 70)
    sys.exit(1)
