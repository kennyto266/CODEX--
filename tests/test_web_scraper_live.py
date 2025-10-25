#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Real Web Scraper Test - Actually connects to live websites
Uses requests and BeautifulSoup to scrape real data
"""

import asyncio
import sys
from pathlib import Path
from datetime import date, datetime

sys.path.insert(0, str(Path(__file__).parent))

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_LIBS = True
except ImportError:
    HAS_LIBS = False


class HKEXLiveScraper:
    """HKEX Live Web Scraper"""

    async def test_connection(self):
        """Test if we can connect to HKEX"""
        if not HAS_LIBS:
            return False, "Missing libraries"

        try:
            url = "https://www.hkex.com.hk/Market-Data/Market-Highlights"
            print(f"[Connecting] {url}")

            response = requests.get(url, timeout=10)
            success = response.status_code == 200

            if success:
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.title.string if soup.title else "No title"
                return True, f"HTTP {response.status_code} - {title}"
            else:
                return False, f"HTTP {response.status_code}"

        except requests.exceptions.Timeout:
            return False, "Connection timeout"
        except requests.exceptions.ConnectionError:
            return False, "Connection refused"
        except Exception as e:
            return False, str(e)


class GovernmentLiveScraper:
    """Government Data Live Web Scraper"""

    async def test_connection(self):
        """Test if we can connect to government website"""
        if not HAS_LIBS:
            return False, "Missing libraries"

        try:
            url = "https://www.hkma.gov.hk/eng/key-information/market-data/daily-monetary-data/"
            print(f"[Connecting] {url}")

            response = requests.get(url, timeout=10)
            success = response.status_code == 200

            if success:
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.title.string if soup.title else "No title"
                return True, f"HTTP {response.status_code} - {title}"
            else:
                return False, f"HTTP {response.status_code}"

        except requests.exceptions.Timeout:
            return False, "Connection timeout"
        except requests.exceptions.ConnectionError:
            return False, "Connection refused"
        except Exception as e:
            return False, str(e)


class YahooFinanceLiveScraper:
    """Yahoo Finance Live Web Scraper"""

    async def test_connection(self):
        """Test if we can connect to Yahoo Finance"""
        if not HAS_LIBS:
            return False, "Missing libraries"

        try:
            url = "https://finance.yahoo.com/quote/%5EHSI"
            print(f"[Connecting] {url}")

            response = requests.get(url, timeout=10)
            success = response.status_code == 200

            if success:
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.title.string if soup.title else "No title"
                return True, f"HTTP {response.status_code} - {title}"
            else:
                return False, f"HTTP {response.status_code}"

        except requests.exceptions.Timeout:
            return False, "Connection timeout"
        except requests.exceptions.ConnectionError:
            return False, "Connection refused"
        except Exception as e:
            return False, str(e)


async def main():
    """Main test"""
    print("="*70)
    print("Real Web Scraper Test - Connecting to live websites")
    print("="*70)

    results = {}

    # Test HKEX
    print("\n[TEST 1] HKEX Website Connection")
    print("-"*70)
    hkex = HKEXLiveScraper()
    success, message = await hkex.test_connection()
    results["HKEX"] = (success, message)
    print(f"[{'OK' if success else 'FAIL'}] {message}\n")

    # Test Government
    print("[TEST 2] Hong Kong Monetary Authority Website")
    print("-"*70)
    gov = GovernmentLiveScraper()
    success, message = await gov.test_connection()
    results["Government"] = (success, message)
    print(f"[{'OK' if success else 'FAIL'}] {message}\n")

    # Test Yahoo Finance
    print("[TEST 3] Yahoo Finance Website")
    print("-"*70)
    yahoo = YahooFinanceLiveScraper()
    success, message = await yahoo.test_connection()
    results["Yahoo Finance"] = (success, message)
    print(f"[{'OK' if success else 'FAIL'}] {message}\n")

    # Summary
    print("="*70)
    print("Test Summary")
    print("="*70)

    passed = 0
    for name, (success, message) in results.items():
        status = "PASS" if success else "FAIL"
        print(f"{name:.<40} [{status}]")
        if success:
            passed += 1

    total = len(results)
    print(f"\nResults: {passed}/{total} websites accessible")

    if passed > 0:
        print("\n[SUCCESS] Real web scraper successfully connected to live websites!")
        print("\nNext steps:")
        print("1. Extract specific data elements using CSS selectors")
        print("2. Parse HTML tables and lists")
        print("3. Update collectors to use live mode")
        return 0
    else:
        print("\n[INFO] Could not connect to websites")
        if not HAS_LIBS:
            print("Need to install: pip install requests beautifulsoup4")
        return 1


if __name__ == "__main__":
    print("\n[START] Real Web Scraper Test")
    print("This script will connect to actual websites\n")

    if not HAS_LIBS:
        print("[WARNING] Missing required libraries!")
        print("Install with: pip install requests beautifulsoup4")
        print()

    exit_code = asyncio.run(main())
    sys.exit(exit_code)
