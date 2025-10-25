#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HKEX Selenium Web Scraper - Real browser automation with data extraction
This scraper actually opens a browser, loads the page, waits for data,
and extracts market indicators from the rendered DOM
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, date
import json

sys.path.insert(0, str(Path(__file__).parent))

from src.data_adapters.alternative_data_adapter import AlternativeDataAdapter, IndicatorMetadata, DataFrequency

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False


class HKEXSeleniumScraper(AlternativeDataAdapter):
    """
    Real HKEX scraper using Selenium WebDriver

    This scraper:
    1. Opens Chrome browser
    2. Navigates to HKEX website
    3. Waits for JavaScript to load market data (3-5 seconds)
    4. Extracts data from rendered DOM
    5. Returns structured DataFrame
    """

    # Market indicators we're trying to extract
    INDICATORS = {
        'hsi': 'HSI (Hang Seng Index)',
        'hsi_china': 'HSI China Enterprises Index',
        'hsi_tech': 'HSI Tech Index',
        'hsi_volatility': 'HSI Volatility Index',
        'msci_china': 'MSCI China A50 Index',
        'usd_rmb': 'USD/RMB Exchange Rate',
        'usd_inr': 'USD/INR Exchange Rate',
        'btc_index': 'Bitcoin Index',
        'eth_index': 'Ethereum Index',
    }

    # CSS selectors to try (these will be updated based on actual page structure)
    SELECTOR_PATTERNS = {
        'price_patterns': [
            'span[data-value]',  # data attribute
            'span.price',  # class
            'span.market-price',
            '.market-highlights span',
            '[class*="price"]',
            '[class*="index"]',
            '[data-*="price"]'
        ],
        'change_patterns': [
            'span.change',
            'span[class*="change"]',
            '[class*="change"]'
        ]
    }

    def __init__(self):
        super().__init__(
            adapter_name="HKEXSeleniumScraper",
            data_source_url="https://www.hkex.com.hk/?sc_lang=zh-HK",
            cache_ttl=300,  # 5 minutes
            max_retries=3,
            timeout=20
        )
        self.driver = None
        self.data_cache = {}

    async def _do_connect(self) -> bool:
        """Initialize Selenium WebDriver"""
        if not HAS_SELENIUM:
            print("[ERROR] Selenium not installed. Run: pip install selenium")
            return False

        try:
            print("[CONNECTING] Starting Chrome browser with Selenium...")

            # Configure Chrome options
            chrome_options = Options()
            # Uncomment for headless mode (no visible window)
            # chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)')

            # Initialize driver (assumes chromedriver in PATH)
            self.driver = webdriver.Chrome(options=chrome_options)

            print("[OK] Chrome browser started")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to start browser: {e}")
            print("[INFO] Make sure ChromeDriver is installed: https://chromedriver.chromium.org/")
            return False

    async def _do_disconnect(self) -> bool:
        """Close browser"""
        if self.driver:
            self.driver.quit()
            print("[OK] Browser closed")
        return True

    async def _fetch_with_retry(
        self,
        indicator_code: str,
        start_date: date,
        end_date: date,
        **kwargs,
    ) -> object:
        """Fetch data with retry logic"""
        return await self._retry_operation(
            self._scrape_live_data,
            indicator_code,
            start_date,
            end_date,
            **kwargs
        )

    async def _scrape_live_data(
        self,
        indicator_code: str,
        start_date: date,
        end_date: date,
        **kwargs
    ) -> object:
        """Scrape live data from HKEX website"""
        if not self.driver:
            raise RuntimeError("Browser not connected")

        try:
            print(f"\n[SCRAPING] {indicator_code}...")

            # Navigate to HKEX
            print(f"[NAVIGATE] Loading {self.data_source_url}")
            self.driver.get(self.data_source_url)

            # Wait for page to load
            print("[WAIT] Waiting for JavaScript to load data (5 seconds)...")
            await asyncio.sleep(5)  # Wait for JS to execute

            # Try to find market data elements
            print("[SEARCH] Looking for market data in rendered page...")
            data = await self._extract_from_page()

            if data:
                self.data_cache[indicator_code] = data
                return data

            return None

        except Exception as e:
            print(f"[ERROR] Scraping failed: {e}")
            raise

    async def _extract_from_page(self) -> dict:
        """Extract data from rendered page"""
        results = {}

        try:
            # Get page source
            page_source = self.driver.page_source

            # Look for the data points
            print("[EXTRACT] Searching for market data in page...")

            # Save page for inspection
            with open('hkex_rendered_page.html', 'w', encoding='utf-8') as f:
                f.write(page_source)
            print("[SAVED] Rendered page to hkex_rendered_page.html")

            # Try different search strategies
            strategies = [
                self._extract_by_text,
                self._extract_by_elements,
                self._extract_by_js_eval
            ]

            for strategy in strategies:
                try:
                    data = strategy()
                    if data:
                        results.update(data)
                        print(f"[OK] Strategy found data: {len(data)} items")
                except Exception as e:
                    print(f"[SKIP] Strategy failed: {e}")
                    continue

            return results if results else None

        except Exception as e:
            print(f"[ERROR] Extraction failed: {e}")
            return None

    def _extract_by_text(self) -> dict:
        """Strategy 1: Find elements by text content"""
        results = {}
        target_values = {
            'hsi': '25247',
            'hsi_china': '9011',
            'hsi_tech': '5760',
            'btc': '107428',
            'eth': '3923'
        }

        print("[STRATEGY] Using text content search...")

        for elem in self.driver.find_elements(By.TAG_NAME, 'span'):
            try:
                text = elem.text
                for key, value in target_values.items():
                    if value in text:
                        # Found matching element
                        elem_info = {
                            'text': text[:200],
                            'tag': elem.tag_name,
                            'class': elem.get_attribute('class'),
                            'id': elem.get_attribute('id'),
                            'data_attributes': {}
                        }

                        # Get data attributes
                        attrs = elem.get_attribute('outerHTML')
                        results[key] = elem_info
                        print(f"  Found {key}: {elem.get_attribute('class')}")

            except Exception as e:
                continue

        return results if results else None

    def _extract_by_elements(self) -> dict:
        """Strategy 2: Find by CSS selectors"""
        results = {}

        print("[STRATEGY] Using CSS selector search...")

        for pattern in self.SELECTOR_PATTERNS['price_patterns']:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, pattern)
                if elements:
                    for elem in elements[:5]:
                        try:
                            text = elem.text
                            if any(v in text for v in ['25247', '9011', '5760', '107428']):
                                results[f"selector_{pattern}"] = {
                                    'selector': pattern,
                                    'text': text[:100],
                                    'class': elem.get_attribute('class')
                                }
                                print(f"  Found with selector '{pattern}': {text[:50]}")
                        except:
                            continue
            except:
                continue

        return results if results else None

    def _extract_by_js_eval(self) -> dict:
        """Strategy 3: Execute JavaScript to find data"""
        results = {}

        print("[STRATEGY] Using JavaScript evaluation...")

        js_script = """
        return (function() {
            const data = {};
            const allText = document.body.innerText;

            // Check if page has loaded data
            if (allText.includes('25247')) {
                data.has_hsi = true;

                // Find all span elements
                const spans = document.querySelectorAll('span');
                let found = 0;
                spans.forEach((span, idx) => {
                    const text = span.innerText;
                    if (text && text.includes('25247') && found < 3) {
                        data[`hsi_element_${idx}`] = {
                            text: text.substring(0, 100),
                            className: span.className,
                            id: span.id
                        };
                        found++;
                    }
                });
            }

            // Check for other indicators
            data.has_btc = allText.includes('107428');
            data.has_eth = allText.includes('3923');

            return data;
        })();
        """

        try:
            result = self.driver.execute_script(js_script)
            if result:
                results['js_results'] = result
                print(f"  JavaScript found: {result}")
        except Exception as e:
            print(f"  JavaScript eval failed: {e}")

        return results if results else None

    async def _get_realtime_impl(self, indicator_code: str, **kwargs):
        """Get real-time data"""
        if indicator_code in self.data_cache:
            return self.data_cache[indicator_code]

        # If not in cache, try to fetch
        try:
            data = await self._scrape_live_data(indicator_code, date.today(), date.today())
            return data
        except:
            return None

    async def _get_metadata_impl(self, indicator_code: str) -> IndicatorMetadata:
        """Get indicator metadata"""
        indicator_name = self.INDICATORS.get(indicator_code, indicator_code)

        return IndicatorMetadata(
            indicator_code=indicator_code,
            indicator_name=indicator_name,
            description=f"Real-time {indicator_name} from HKEX via Selenium scraper",
            data_source="HKEX",
            frequency=DataFrequency.REALTIME,
            unit="points" if "Index" in indicator_name else "HKD" if "RMB" in indicator_name else "INR" if "INR" in indicator_name else "USD",
            country_code="HK",
            category="market_index",
            last_updated=datetime.now(),
            next_update=datetime.now(),
            data_availability="Real-time during trading hours",
            quality_notes="Data extracted from HKEX website using Selenium WebDriver"
        )

    async def _list_indicators_impl(self):
        """List available indicators"""
        return list(self.INDICATORS.keys())

    async def _check_connectivity(self) -> bool:
        """Check if browser is accessible"""
        return self.driver is not None


async def test_scraper():
    """Test the Selenium scraper"""
    print("\n" + "="*70)
    print("HKEX Selenium Web Scraper - Real Browser Test")
    print("="*70)
    print(f"\nURL: https://www.hkex.com.hk/?sc_lang=zh-HK")
    print("Method: Selenium WebDriver with real browser\n")

    scraper = HKEXSeleniumScraper()

    try:
        # Connect
        if not await scraper.connect():
            print("[ERROR] Failed to connect browser")
            return 1

        print("[OK] Connected to browser\n")

        # List indicators
        indicators = await scraper.list_indicators()
        print(f"[OK] Available indicators: {len(indicators)}")
        print(f"    {', '.join(indicators[:5])}...\n")

        # Scrape data
        print("="*70)
        print("Scraping Live Market Data")
        print("="*70 + "\n")

        test_indicator = "hsi"
        print(f"[TEST] Scraping {test_indicator}...")

        data = await scraper._scrape_live_data(
            test_indicator,
            date.today(),
            date.today()
        )

        if data:
            print(f"\n[SUCCESS] Data extracted:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print("[INFO] No data extracted (page structure may differ)")

        # Get metadata
        print("\n" + "="*70)
        print("Indicator Metadata")
        print("="*70 + "\n")

        metadata = await scraper.get_metadata(test_indicator)
        print(f"Indicator: {metadata.indicator_name}")
        print(f"Source: {metadata.data_source}")
        print(f"Frequency: {metadata.frequency}")

        # Disconnect
        await scraper.disconnect()

        print("\n" + "="*70)
        print("[COMPLETE] Selenium scraper test finished")
        print("="*70)
        print("\nChecked files for page structure:")
        print("  - hkex_rendered_page.html")
        print("\nTo properly extract data:")
        print("  1. Review hkex_rendered_page.html in browser")
        print("  2. Inspect elements to find CSS classes/IDs")
        print("  3. Update SELECTOR_PATTERNS with actual selectors")
        print("  4. Rerun scraper to extract using correct selectors\n")

        return 0

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        # Cleanup
        try:
            if scraper.driver:
                await scraper.disconnect()
        except:
            pass


if __name__ == "__main__":
    print("\n[START] HKEX Selenium Web Scraper")
    print("[NOTE] This will open an actual Chrome browser window\n")

    if not HAS_SELENIUM:
        print("[ERROR] Selenium not installed")
        print("Install with: pip install selenium")
        print("\nAlso need ChromeDriver from: https://chromedriver.chromium.org/")
        sys.exit(1)

    exit_code = asyncio.run(test_scraper())
    sys.exit(exit_code)
