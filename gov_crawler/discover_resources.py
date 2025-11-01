#!/usr/bin/env python3
"""
GOV 爬蟲系統 - 資源發現工具
用於發現香港政府開放數據的實際資源 ID
"""

import requests
import json
from typing import Dict, List, Any, Optional
import sys

BASE_URL = "https://data.gov.hk/tc-data/api/3/action"


def search_packages(query: str = "", fq: str = "", limit: int = 100) -> List[Dict[str, Any]]:
    """Search for packages/datasets"""
    try:
        params = {'rows': limit}
        if query:
            params['q'] = query
        if fq:
            params['fq'] = fq

        response = requests.get(f"{BASE_URL}/package_search", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('success'):
            return data['result']['results']
        return []
    except Exception as e:
        print(f"Error searching packages: {e}")
        return []


def get_package_details(package_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed information about a package"""
    try:
        response = requests.get(f"{BASE_URL}/package_show?id={package_id}", timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('success'):
            return data['result']
        return None
    except Exception as e:
        print(f"Error getting package details: {e}")
        return None


def search_resources_in_category(category_name: str, limit: int = 50) -> Dict[str, Any]:
    """Search for resources in a specific category"""
    print(f"\n{'='*60}")
    print(f"Searching category: {category_name}")
    print(f"{'='*60}")

    fq = f"groups:{category_name}"
    packages = search_packages(fq=fq, limit=limit)

    print(f"Found {len(packages)} packages in category '{category_name}'")

    resources = {}
    for package in packages:
        pkg_name = package.get('name', 'Unknown')
        pkg_title = package.get('title', 'No Title')
        pkg_id = package.get('id', '')

        print(f"\nPackage: {pkg_title}")
        print(f"  Name: {pkg_name}")
        print(f"  ID: {pkg_id}")
        print(f"  Resources: {len(package.get('resources', []))}")

        for resource in package.get('resources', []):
            res_id = resource.get('id', 'Unknown')
            res_name = resource.get('name', 'Unknown')
            res_format = resource.get('format', 'Unknown')
            res_url = resource.get('url', '')
            is_api = resource.get('is_api', 'N')

            key = f"{pkg_name}#{res_id}"
            resources[key] = {
                'package_name': pkg_name,
                'package_title': pkg_title,
                'package_id': pkg_id,
                'resource_id': res_id,
                'resource_name': res_name,
                'resource_format': res_format,
                'resource_url': res_url,
                'is_api': is_api
            }

            print(f"    - {res_name} ({res_format}) [API: {is_api}]")
            print(f"      ID: {res_id}")
            if res_url:
                print(f"      URL: {res_url}")

    return resources


def test_resource_access(resource_id: str, limit: int = 5) -> bool:
    """Test if we can access a resource via datastore_search"""
    try:
        params = {
            'resource_id': resource_id,
            'limit': limit
        }
        response = requests.get(f"{BASE_URL}/datastore_search", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('success'):
            records = data['result'].get('records', [])
            print(f"  ✓ Accessible - Found {len(records)} records")
            return True
        else:
            error = data.get('error', 'Unknown error')
            print(f"  ✗ Error: {error}")
            return False
    except Exception as e:
        print(f"  ✗ Exception: {e}")
        return False


def main():
    """Main discovery process"""

    # Categories to explore
    categories = [
        'finance',
        'housing',
        'transport',
        'business-and-trade',
        'health'
    ]

    all_resources = {}

    # Discover resources in each category
    for category in categories:
        resources = search_resources_in_category(category, limit=50)
        all_resources.update(resources)

    # Try to access some resources
    print(f"\n{'='*60}")
    print("Testing resource access via datastore_search")
    print(f"{'='*60}")

    accessible = {}
    for key, resource in list(all_resources.items())[:20]:  # Test first 20
        print(f"\nTesting: {resource['resource_name']}")
        if test_resource_access(resource['resource_id']):
            accessible[key] = resource

    # Save results
    output_file = "discovered_resources.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'all_resources': all_resources,
            'accessible_resources': accessible
        }, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"Discovery complete!")
    print(f"Total resources found: {len(all_resources)}")
    print(f"Accessible resources: {len(accessible)}")
    print(f"Results saved to: {output_file}")
    print(f"{'='*60}")

    # Print summary of accessible resources
    print("\nAccessible resources summary:")
    for key, resource in accessible.items():
        print(f"\n{resource['resource_name']}")
        print(f"  Resource ID: {resource['resource_id']}")
        print(f"  Format: {resource['resource_format']}")
        print(f"  Package: {resource['package_name']}")


if __name__ == '__main__':
    main()
