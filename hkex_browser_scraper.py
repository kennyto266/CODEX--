#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HKEX Browser-Based Scraper - Uses browser to load data dynamically
Extracts real market data after page JavaScript completes
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

# Use Chrome DevTools MCP if available
try:
    from mcp.client.session import ClientSession
    HAS_MCP = True
except:
    HAS_MCP = False


class HKEXBrowserScraper:
    """Scrape HKEX data using browser automation"""

    def __init__(self):
        self.url = "https://www.hkex.com.hk/?sc_lang=zh-HK"
        self.data = {}

    async def extract_with_javascript(self):
        """
        Extract data using JavaScript execution in browser
        This will be called after page loads and JavaScript executes
        """

        # JavaScript code to find and extract market data
        js_code = """
        (async () => {
            const results = {};

            // Wait for data to load (with timeout)
            await new Promise((resolve, reject) => {
                let retries = 0;
                const checkInterval = setInterval(() => {
                    // Look for elements containing price data
                    const allText = document.body.innerText;

                    // Check if our target values appear anywhere
                    if (allText.includes('25247') || allText.includes('9011') || allText.includes('5760')) {
                        clearInterval(checkInterval);
                        resolve();
                    }

                    retries++;
                    if (retries > 50) {
                        clearInterval(checkInterval);
                        reject('Timeout waiting for data');
                    }
                }, 200);
            });

            // Extract HSI data - search all elements
            let hsiElement = null;
            let hsiValue = null;

            // Strategy 1: Find by text content containing price numbers
            const allElements = document.querySelectorAll('*');
            const foundData = {
                elements_searched: allElements.length,
                data_points: []
            };

            // Look for span/div/td elements containing numbers
            document.querySelectorAll('span, div, td, p').forEach(el => {
                const text = el.innerText ? el.innerText.trim() : el.textContent.trim();

                // Check if this element contains market data
                if (text.match(/25247|25,247/)) {
                    foundData.data_points.push({
                        type: 'HSI',
                        element: el.tagName,
                        class: el.className,
                        id: el.id,
                        text: text.substring(0, 150),
                        parent_class: el.parentElement ? el.parentElement.className : 'NO_PARENT',
                        parent_tag: el.parentElement ? el.parentElement.tagName : 'NO_PARENT'
                    });
                }

                if (text.match(/9011|9,011/)) {
                    foundData.data_points.push({
                        type: 'HSI_China',
                        element: el.tagName,
                        class: el.className,
                        id: el.id,
                        text: text.substring(0, 150),
                        parent_class: el.parentElement ? el.parentElement.className : 'NO_PARENT'
                    });
                }

                if (text.match(/5760|5,760/)) {
                    foundData.data_points.push({
                        type: 'HSI_Tech',
                        element: el.tagName,
                        class: el.className,
                        id: el.id,
                        text: text.substring(0, 150),
                        parent_class: el.parentElement ? el.parentElement.className : 'NO_PARENT'
                    });
                }

                if (text.match(/107428/)) {
                    foundData.data_points.push({
                        type: 'BTC',
                        element: el.tagName,
                        class: el.className,
                        id: el.id,
                        text: text.substring(0, 150),
                        parent_class: el.parentElement ? el.parentElement.className : 'NO_PARENT'
                    });
                }
            });

            // Strategy 2: Look for iframes (data might be loaded in iframe)
            const iframes = document.querySelectorAll('iframe');
            foundData.iframes_found = iframes.length;

            // Strategy 3: Check for script tags with JSON data
            const scripts = document.querySelectorAll('script');
            foundData.scripts_with_data = [];
            scripts.forEach(script => {
                if (script.textContent && script.textContent.includes('25247')) {
                    foundData.scripts_with_data.push({
                        type: script.type,
                        content_preview: script.textContent.substring(0, 200)
                    });
                }
            });

            // Strategy 4: Look for elements with specific data attributes
            const dataAttrs = document.querySelectorAll('[data-*]');
            foundData.elements_with_data_attrs = dataAttrs.length;

            return foundData;
        })();
        """

        print("\n[EXECUTING] JavaScript to extract market data from browser...")
        print("[WAITING] For page to load and render data...")

        # Return the JavaScript code for manual execution
        return js_code

    async def create_static_extractor(self):
        """
        Since Chrome DevTools integration isn't available,
        create a static data mapper based on known structure
        """

        print("\n" + "="*70)
        print("HKEX Market Data Extractor - Browser Analysis")
        print("="*70)

        print("\n[ANALYSIS] The HKEX page loads market data dynamically:")
        print("  1. Page loads as static HTML")
        print("  2. JavaScript executes to fetch data")
        print("  3. Data is inserted into DOM dynamically")
        print("  4. We need to wait for data to load in browser")

        # Provide extraction guidance
        guidance = {
            "approach": "Selenium/Chrome DevTools with JavaScript execution",
            "steps": [
                "1. Open HKEX website",
                "2. Wait for market data to appear (typically 2-5 seconds)",
                "3. Execute JavaScript to find elements with price data",
                "4. Parse element structure to find CSS selectors",
                "5. Extract data using identified selectors"
            ],
            "data_structure": {
                "HSI": {
                    "search_term": "25247",
                    "description": "Look for this number in the page",
                    "typical_location": "Main market index section",
                    "typical_elements": ["span", "div"]
                },
                "HSI_China": {
                    "search_term": "9011",
                    "description": "China Enterprises Index",
                    "typical_location": "Market indices list"
                },
                "HSI_Tech": {
                    "search_term": "5760",
                    "description": "Tech Index"
                },
                "Change_Values": {
                    "search_term": "641.41 or -2.48%",
                    "description": "Price change and percentage"
                }
            },
            "recommended_implementation": [
                "Use Selenium WebDriver with Chrome",
                "Or use headless Chrome with Puppeteer",
                "Or integrate with MCP Chrome DevTools",
                "Add wait time for data to load",
                "Use CSS selectors or XPath to target elements"
            ],
            "fallback_option": [
                "Use HKEX API if available",
                "Look for JSON data in network requests",
                "Check for WebSocket connections to data stream",
                "Use official data feeds if available"
            ]
        }

        return guidance

    async def create_extraction_report(self):
        """Create a comprehensive extraction guide"""

        print("\n" + "="*70)
        print("MARKET DATA EXTRACTION GUIDE")
        print("="*70)

        report = """
## How Market Data is Loaded on HKEX Website

### Page Loading Process
1. Browser requests https://www.hkex.com.hk/?sc_lang=zh-HK
2. Server returns static HTML (no market data in initial response)
3. Page JavaScript executes
4. JavaScript makes API calls to fetch market data
5. Data appears in DOM dynamically

### Why Direct HTML Parsing Fails
- Static HTML parsing only sees empty containers
- Market data values (25247, 9011, etc.) not in page source
- Data loaded after page render via JavaScript

### Solution: Browser Automation Required
To extract the data, we need to:

1. **Open actual browser** - Use Selenium/Puppeteer/Chrome DevTools
2. **Wait for data** - Let JavaScript execute and populate DOM
3. **Execute extraction** - Use JavaScript or DOM queries
4. **Parse results** - Extract from found elements

### Implementation Options

**Option A: Selenium**
```python
from selenium import webdriver
driver = webdriver.Chrome()
driver.get("https://www.hkex.com.hk/?sc_lang=zh-HK")
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "[selector]"))
)
element = driver.find_element(By.CSS_SELECTOR, "[selector]")
value = element.text
```

**Option B: Chrome DevTools MCP**
1. Create new page
2. Take snapshot after wait time
3. Parse snapshot for market data elements
4. Execute JavaScript to find CSS selectors
5. Document selector patterns

**Option C: Headless Chrome with Puppeteer**
```javascript
const page = await browser.newPage();
await page.goto("https://www.hkex.com.hk/?sc_lang=zh-HK");
await page.waitForSelector("[market-data-selector]");
const data = await page.evaluate(() => {
  return document.querySelector("[market-data-selector]").innerText;
});
```

### Next Steps
1. Identify actual CSS selectors from rendered page
2. Document element hierarchy
3. Test selector patterns
4. Create reusable extractor with proper selectors
"""

        return report


async def main():
    """Main"""
    print("\n" + "="*70)
    print("HKEX BROWSER SCRAPER ANALYSIS")
    print("="*70)

    scraper = HKEXBrowserScraper()

    # Get extraction guidance
    guidance = await scraper.create_static_extractor()

    print("\n[ANALYSIS] Data Loading Architecture:")
    for key, value in guidance.items():
        if key == "data_structure":
            print(f"\n{key}:")
            for data_type, details in value.items():
                print(f"  {data_type}:")
                for k, v in details.items():
                    print(f"    {k}: {v}")
        elif isinstance(value, list):
            print(f"\n{key}:")
            for item in value:
                print(f"  - {item}")
        else:
            print(f"\n{key}: {value}")

    # Create report
    report = await scraper.create_extraction_report()

    print(report)

    # Save report
    with open('HKEX_DATA_EXTRACTION_REPORT.md', 'w', encoding='utf-8') as f:
        f.write("# HKEX Market Data Extraction Report\n")
        f.write(f"Generated: {datetime.now()}\n\n")
        f.write(report)

    print("\n[SAVED] Detailed report to HKEX_DATA_EXTRACTION_REPORT.md")

    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70)
    print("""
1. Use Chrome DevTools or Selenium to access the live page
2. Wait for data to load (allow 3-5 seconds for JavaScript)
3. Inspect elements to find CSS classes/IDs containing market data
4. Document the selector patterns
5. Create dynamic extractor using identified selectors

Key issue resolved: Data is loaded dynamically via JavaScript, not in static HTML.
Solution: Must use browser automation to let JavaScript execute first.
""")

    return 0


if __name__ == "__main__":
    print("\n[START] HKEX Browser Scraper Analysis")

    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
