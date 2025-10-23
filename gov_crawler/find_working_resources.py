#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Find working resource IDs for Hong Kong government data
"""

import requests
import json
import sys
import os

# Set encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "https://data.gov.hk/tc-data/api/3/action"

# Search for specific datasets we need
search_queries = [
    ("property", "Property Market"),
    ("censtatd", "Government Statistics"),
]

print("Searching for working resources...")
print("=" * 70)

working_resources = []

for query, label in search_queries:
    print(f"\nSearching: {label} (query: {query})")
    print("-" * 70)

    try:
        response = requests.get(
            f"{BASE_URL}/package_search",
            params={'q': query, 'rows': 20},
            timeout=10
        )
        data = response.json()

        if not data.get('success'):
            print(f"  API returned error: {data.get('error')}")
            continue

        results = data['result']['results']
        print(f"  Found {len(results)} packages")

        for pkg in results[:3]:  # Show first 3
            pkg_title = pkg.get('title', 'N/A')
            pkg_id = pkg.get('id', '')

            print(f"\n  Package: {pkg_title[:60]}")
            print(f"    ID: {pkg_id}")
            print(f"    Resources: {len(pkg.get('resources', []))}")

            # Try to find working resources
            for resource in pkg.get('resources', [])[:5]:
                res_id = resource.get('id', '')
                res_name = resource.get('name', 'N/A')
                res_format = resource.get('format', '')

                try:
                    # Test access
                    test_resp = requests.get(
                        f"{BASE_URL}/datastore_search",
                        params={'resource_id': res_id, 'limit': 1},
                        timeout=5
                    )

                    test_data = test_resp.json()
                    success = test_data.get('success', False)
                    status = "OK" if success else "FAIL"

                    print(f"      [{status}] {res_format:6s} | {res_name[:40]}")
                    print(f"             {res_id}")

                    if success:
                        working_resources.append({
                            'query': query,
                            'package_title': pkg_title,
                            'package_id': pkg_id,
                            'resource_id': res_id,
                            'resource_name': res_name,
                            'format': res_format
                        })

                except Exception as e:
                    print(f"      [ERR] Error testing: {str(e)[:40]}")

    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "=" * 70)
print(f"Found {len(working_resources)} working resources")
print("=" * 70)

# Save results
output_file = "working_resources.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(working_resources, f, ensure_ascii=False, indent=2)

print(f"\nResults saved to: {output_file}")

# Print a sample of working resources
if working_resources:
    print("\nWorking Resource IDs:")
    for res in working_resources[:5]:
        print(f"  - {res['format']:6s}: {res['resource_id']}")
