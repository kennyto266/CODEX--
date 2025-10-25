#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HKEX Page Data Extraction - Find actual data elements and selectors
This script analyzes HKEX page HTML to identify where market data is stored
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


class HKEXDataExtractor:
    """Extract actual data elements from HKEX page"""

    def __init__(self):
        self.url = "https://www.hkex.com.hk/?sc_lang=zh-HK"
        self.page_content = None
        self.soup = None

    async def fetch_page(self):
        """Fetch HKEX page"""
        if not HAS_LIBS:
            print("[ERROR] Missing requests/beautifulsoup4")
            return False

        try:
            print(f"[FETCHING] {self.url}")

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(self.url, headers=headers, timeout=15)

            if response.status_code != 200:
                print(f"[ERROR] HTTP {response.status_code}")
                return False

            print(f"[OK] Page fetched successfully")
            self.page_content = response.content
            self.soup = BeautifulSoup(self.page_content, 'html.parser')

            # Save raw HTML for inspection
            with open('hkex_raw_page.html', 'w', encoding='utf-8') as f:
                f.write(str(self.soup.prettify()))
            print("[SAVED] Raw HTML to hkex_raw_page.html")

            return True

        except Exception as e:
            print(f"[ERROR] {str(e)}")
            return False

    def analyze_structure(self):
        """Analyze and extract data elements"""
        if not self.soup:
            print("[ERROR] Page not loaded")
            return None

        print("\n[ANALYZING] Page structure...")

        # Target data points we know exist
        data_points = {
            'HSI': '25247',
            'HSI_China': '9011',
            'HSI_Tech': '5760',
            'Change_HSI': '641.41',
            'HSI_Pct': '2.48',
            'BTC': '107428',
            'ETH': '3923'
        }

        results = {
            'data_elements': [],
            'class_names': {},
            'id_names': {},
            'parent_hierarchy': {}
        }

        print("\n[SEARCHING] For data elements in page...")

        # Search for each data point
        for label, search_value in data_points.items():
            print(f"\nSearching for {label} ({search_value})...")

            for elem in self.soup.find_all(True):
                text = elem.get_text(strip=True)

                # Normalize text (remove spaces and commas)
                normalized_text = text.replace(' ', '').replace(',', '')

                if search_value in normalized_text:
                    elem_info = {
                        'label': label,
                        'search_value': search_value,
                        'found_text': text[:200],
                        'tag': elem.name,
                        'class': ' '.join(elem.get('class', [])) if elem.get('class') else 'NO_CLASS',
                        'id': elem.get('id', 'NO_ID'),
                        'data_attrs': {k: v for k, v in elem.attrs.items() if k.startswith('data-')}
                    }

                    # Get parent hierarchy
                    parents = []
                    current = elem.parent
                    depth = 0
                    while current and depth < 5:
                        parent_info = {
                            'tag': current.name,
                            'class': ' '.join(current.get('class', [])) if current.get('class') else 'NO_CLASS',
                            'id': current.get('id', 'NO_ID')
                        }
                        parents.append(parent_info)
                        current = current.parent
                        depth += 1

                    elem_info['parents'] = parents

                    results['data_elements'].append(elem_info)

                    # Track class and ID names
                    if elem.get('class'):
                        class_str = ' '.join(elem.get('class'))
                        results['class_names'][class_str] = results['class_names'].get(class_str, 0) + 1

                    if elem.get('id'):
                        id_str = elem.get('id')
                        results['id_names'][id_str] = results['id_names'].get(id_str, 0) + 1

                    print(f"  FOUND: <{elem.name} class='{elem.get('class', ['NO_CLASS'])[0] if elem.get('class') else 'NO_CLASS'}'> = {text[:80]}")

        return results

    def extract_selectors(self, analysis):
        """Extract CSS selectors from analysis"""
        if not analysis:
            return None

        selectors = {
            'by_class': [],
            'by_id': [],
            'xpath_patterns': [],
            'combined_selectors': []
        }

        # Sort classes by frequency
        sorted_classes = sorted(analysis['class_names'].items(), key=lambda x: x[1], reverse=True)
        selectors['by_class'] = [
            {'selector': f".{cls.replace(' ', '.')}", 'count': count}
            for cls, count in sorted_classes[:10]
        ]

        # Sort IDs
        sorted_ids = sorted(analysis['id_names'].items(), key=lambda x: x[1], reverse=True)
        selectors['by_id'] = [
            {'selector': f"#{id_str}", 'count': count}
            for id_str, count in sorted_ids[:10]
        ]

        # Analyze elements to create combined selectors
        for elem in analysis['data_elements'][:5]:
            combined = []
            if elem['tag']:
                combined.append(elem['tag'])
            if elem['class'] and elem['class'] != 'NO_CLASS':
                combined.append(f".{elem['class'].split()[0]}")

            if combined:
                selector = ' > '.join(combined)
                selectors['combined_selectors'].append({
                    'selector': selector,
                    'label': elem['label'],
                    'found_text': elem['found_text']
                })

        return selectors


async def main():
    """Main execution"""
    print("\n" + "="*70)
    print("HKEX PAGE DATA EXTRACTION")
    print("="*70)
    print("Goal: Find actual HTML elements containing market data\n")

    extractor = HKEXDataExtractor()

    # Fetch page
    if not await extractor.fetch_page():
        return 1

    # Analyze structure
    analysis = extractor.analyze_structure()

    if not analysis:
        print("\n[ERROR] Analysis failed")
        return 1

    # Extract selectors
    selectors = extractor.extract_selectors(analysis)

    # Save results
    results = {
        'url': extractor.url,
        'data_elements_found': len(analysis['data_elements']),
        'unique_classes': len(analysis['class_names']),
        'unique_ids': len(analysis['id_names']),
        'analysis': analysis,
        'selectors': selectors
    }

    with open('hkex_data_extraction.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n[SAVED] Analysis to hkex_data_extraction.json")
    print("[SAVED] Raw HTML to hkex_raw_page.html")

    # Print summary
    print("\n" + "="*70)
    print("EXTRACTION SUMMARY")
    print("="*70)
    print(f"Data elements found: {len(analysis['data_elements'])}")
    print(f"Unique CSS classes: {len(analysis['class_names'])}")
    print(f"Unique IDs: {len(analysis['id_names'])}")

    print("\nTop CSS Classes:")
    for class_name, count in sorted(analysis['class_names'].items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  .{class_name}: {count} elements")

    print("\nTop IDs:")
    for id_name, count in sorted(analysis['id_names'].items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  #{id_name}: {count} elements")

    print("\n[SUCCESS] Data extraction complete!")

    return 0


if __name__ == "__main__":
    print("\n[START] Analyzing HKEX page structure...")

    if not HAS_LIBS:
        print("[ERROR] Missing libraries: pip install requests beautifulsoup4")
        sys.exit(1)

    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
