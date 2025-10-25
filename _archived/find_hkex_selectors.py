#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HKEX Page Structure Analysis - Find actual CSS selectors and data elements
This script analyzes the HKEX page HTML to find where market data is stored
"""

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent))

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_LIBS = True
except ImportError:
    HAS_LIBS = False

class HKEXPageAnalyzer:
    """Analyze HKEX page structure to find data elements"""

    def __init__(self):
        self.url = "https://www.hkex.com.hk/?sc_lang=zh-HK"
        self.page_content = None
        self.soup = None
        self.data_elements = []

    async def fetch_page(self):
        """Fetch the HKEX page"""
        if not HAS_LIBS:
            print("[ERROR] Missing required libraries")
            return False

        try:
            print(f"[FETCHING] {self.url}")

            # Add headers to avoid being blocked
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = requests.get(self.url, headers=headers, timeout=15)

            if response.status_code != 200:
                print(f"[ERROR] HTTP {response.status_code}")
                return False

            print(f"[OK] Successfully fetched page (HTTP 200)")
            self.page_content = response.content
            self.soup = BeautifulSoup(self.page_content, 'html.parser')
            return True

        except Exception as e:
            print(f"[ERROR] {e}")
            return False

    def analyze_structure(self):
        """Analyze page structure to find data elements"""
        if not self.soup:
            print("[ERROR] Page not fetched")
            return False

        print("\n" + "="*70)
        print("PAGE STRUCTURE ANALYSIS")
        print("="*70)

        # Find all elements containing numbers that look like prices
        results = {
            'page_title': self.soup.title.string if self.soup.title else 'N/A',
            'market_indicators': [],
            'all_numbers': [],
            'price_like_elements': []
        }

        # Search for HSI related content
        print("\n[SEARCHING] For HSI market index data...")
        hsi_elements = self._find_elements_containing('25247')
        if hsi_elements:
            print(f"[FOUND] {len(hsi_elements)} elements containing '恒生指数'")
            for elem in hsi_elements[:3]:
                results['market_indicators'].append({
                    'text': elem.get_text(strip=True)[:200],
                    'tag': elem.name,
                    'class': elem.get('class', []),
                    'id': elem.get('id', 'N/A')
                })
                print(f"  - {elem.name}: {elem.get('class')} (text: {elem.get_text(strip=True)[:100]})")

        # Search for price patterns (5-digit numbers)
        print("\n[SEARCHING] For price-like numbers (5-6 digits)...")
        price_elements = self._find_price_elements()
        print(f"[FOUND] {len(price_elements)} price-like elements")
        for elem in price_elements[:10]:
            results['price_like_elements'].append({
                'text': elem.get_text(strip=True)[:150],
                'tag': elem.name,
                'class': elem.get('class', []),
                'id': elem.get('id', 'N/A'),
                'parent_class': elem.parent.get('class', []) if elem.parent else []
            })
            print(f"  - {elem.name} [{elem.get('class')}]: {elem.get_text(strip=True)[:80]}")

        # Look for common market data container patterns
        print("\n[SEARCHING] For market data containers...")
        containers = self._find_data_containers()
        print(f"[FOUND] {len(containers)} potential data containers")

        # Save results
        return results

    def _find_elements_containing(self, text):
        """Find elements containing specific text"""
        results = []
        if not self.soup:
            return results

        for elem in self.soup.find_all(True):
            if text in elem.get_text():
                # Only return if this text is in this specific element, not inherited from parent
                if elem.string and text in elem.string:
                    results.append(elem)
                elif elem.get_text(strip=True) and len(elem.get_text(strip=True)) < 500:
                    results.append(elem)

        return results

    def _find_price_elements(self):
        """Find elements that contain price-like numbers"""
        results = []
        if not self.soup:
            return results

        # Look for numbers in range of market indices (1000-100000)
        target_numbers = ['25247', '25,247', '9011', '9,011', '5760', '5,760']

        for elem in self.soup.find_all(True):
            text = elem.get_text(strip=True)
            # Check if element contains any of our target numbers
            for num in target_numbers:
                if num in text.replace(',', ''):
                    results.append(elem)
                    break

        return results

    def _find_data_containers(self):
        """Find containers that hold market data"""
        results = []
        if not self.soup:
            return results

        # Look for common patterns: divs, sections, articles with class names suggesting market data
        patterns = ['market', 'index', 'hsi', 'price', 'data', 'quote', 'highlight', 'ticker']

        for elem in self.soup.find_all(['div', 'section', 'article', 'span']):
            classes = ' '.join(elem.get('class', []))
            id_attr = elem.get('id', '')

            # Check if element name or classes match patterns
            for pattern in patterns:
                if pattern in classes.lower() or pattern in id_attr.lower():
                    results.append({
                        'tag': elem.name,
                        'class': classes,
                        'id': id_attr,
                        'text_preview': elem.get_text(strip=True)[:100]
                    })
                    break

        return results

    def find_selectors(self):
        """Extract CSS selectors from found elements"""
        print("\n" + "="*70)
        print("CSS SELECTOR EXTRACTION")
        print("="*70)

        selectors = {
            'by_class': {},
            'by_id': {},
            'by_xpath': []
        }

        if not self.soup:
            return selectors

        # Method 1: Find elements with specific classes
        print("\n[EXTRACTING] Classes used in market data elements...")
        class_counts = {}
        for elem in self.soup.find_all(True):
            classes = elem.get('class', [])
            if classes:
                class_str = ' '.join(classes)
                class_counts[class_str] = class_counts.get(class_str, 0) + 1

        # Show most common classes
        for class_str, count in sorted(class_counts.items(), key=lambda x: x[1], reverse=True)[:15]:
            if any(kw in class_str.lower() for kw in ['price', 'index', 'market', 'data', 'quote', 'value', 'digit']):
                selectors['by_class'][class_str] = count
                print(f"  - .{class_str.replace(' ', '.')} (found {count} times)")

        # Method 2: Find elements with IDs containing market-related keywords
        print("\n[EXTRACTING] IDs used in market data elements...")
        for elem in self.soup.find_all(True):
            id_attr = elem.get('id', '')
            if id_attr and any(kw in id_attr.lower() for kw in ['hsi', 'price', 'market', 'data', 'quote']):
                selectors['by_id'][id_attr] = elem.name
                print(f"  - #{id_attr} ({elem.name})")

        return selectors

    def extract_data_mapping(self):
        """Extract the mapping between indicators and their HTML elements"""
        print("\n" + "="*70)
        print("DATA ELEMENT MAPPING")
        print("="*70)

        mapping = {}

        if not self.soup:
            return mapping

        # Define what we're looking for
        indicators = {
            'hsi': ['恒生指数', '25247', '25,247'],
            'hsi_china': ['恒生中国企业指数', '9011', '9,011'],
            'hsi_tech': ['恒生科技指数', '5760', '5,760'],
            'hsi_volatility': ['恒指波幅指数', '28.88'],
            'usd_rmb': ['美元兑人民币', '7.1246', '7.12'],
            'btc_index': ['比特币', '107428'],
            'eth_index': ['以太币', '3923.51'],
        }

        print("\n[MAPPING] Indicator locations in page HTML:")

        for indicator, search_terms in indicators.items():
            print(f"\n{indicator}:")
            found = False

            for term in search_terms:
                # Search for elements containing this term
                for elem in self.soup.find_all(True):
                    text = elem.get_text(strip=True)
                    if term in text.replace(',', '') and len(text) < 500:
                        element_info = {
                            'indicator': indicator,
                            'search_term': term,
                            'tag': elem.name,
                            'class': elem.get('class', []),
                            'id': elem.get('id', ''),
                            'parent_tag': elem.parent.name if elem.parent else None,
                            'parent_class': elem.parent.get('class', []) if elem.parent else [],
                            'text_preview': text[:150]
                        }

                        if elem.name in ['span', 'div', 'p', 'td', 'li']:
                            mapping[f"{indicator}_{term}"] = element_info
                            print(f"  Found '{term}': {elem.name}.{' '.join(elem.get('class', []))} = {text[:80]}")
                            found = True
                            break

                if found:
                    break

        return mapping


async def main():
    """Main analysis"""
    print("\n" + "="*70)
    print("HKEX PAGE STRUCTURE AND SELECTOR ANALYSIS")
    print("="*70)
    print(f"\nTarget URL: https://www.hkex.com.hk/?sc_lang=zh-HK")
    print("Objective: Find CSS selectors and HTML structure for market data extraction\n")

    analyzer = HKEXPageAnalyzer()

    # Step 1: Fetch page
    if not await analyzer.fetch_page():
        return 1

    # Step 2: Analyze structure
    analysis = analyzer.analyze_structure()

    # Step 3: Extract selectors
    selectors = analyzer.find_selectors()

    # Step 4: Extract data mapping
    mapping = analyzer.extract_data_mapping()

    # Step 5: Save results
    print("\n" + "="*70)
    print("SAVING RESULTS")
    print("="*70)

    results = {
        'page_title': analysis['page_title'] if analysis else 'N/A',
        'data_containers': analysis['market_indicators'] if analysis else [],
        'price_elements': analysis['price_like_elements'] if analysis else [],
        'selectors': selectors,
        'indicator_mapping': mapping
    }

    # Save to JSON
    output_file = 'hkex_selectors_analysis.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"[SAVED] Results to {output_file}")

    # Print summary
    print("\n" + "="*70)
    print("ANALYSIS SUMMARY")
    print("="*70)
    print(f"Page Title: {results['page_title']}")
    print(f"Market Indicators Found: {len(results['data_containers'])}")
    print(f"Price-like Elements: {len(results['price_elements'])}")
    print(f"Unique Classes: {len(results['selectors']['by_class'])}")
    print(f"Elements with IDs: {len(results['selectors']['by_id'])}")
    print(f"Indicator Mappings: {len(results['indicator_mapping'])}")

    print("\n[SUCCESS] Analysis complete!")
    print("Review 'hkex_selectors_analysis.json' for detailed results.")

    return 0


if __name__ == "__main__":
    print("\n[START] HKEX Page Structure Analysis")
    print("This will analyze the HKEX page HTML to find data element selectors\n")

    if not HAS_LIBS:
        print("[ERROR] Missing required libraries")
        print("Install with: pip install requests beautifulsoup4")
        sys.exit(1)

    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
