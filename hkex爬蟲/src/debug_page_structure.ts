import { chromium } from 'playwright';

async function debugPageStructure() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  try {
    const url = 'https://www.hkex.com.hk/chi/stat/smstat/dayquot/d251002c.htm';
    console.log(`🌐 Opening: ${url}`);
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    const pageText = await page.textContent('body');
    
    if (!pageText) {
      console.log('❌ No page content');
      return;
    }

    console.log('\n📊 === CHECKING FOR SECTION HEADERS ===');
    
    const lines = pageText.split('\n');
    console.log(`Total lines: ${lines.length}`);
    
    // Look for section headers
    console.log('\n🔍 Searching for section headers...\n');
    
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes('十大')) {
        console.log(`[Line ${i}] ${lines[i]}`);
        // Print next 15 lines
        for (let j = i + 1; j < Math.min(i + 15, lines.length); j++) {
          console.log(`[Line ${j}] ${lines[j]}`);
        }
        console.log('---');
      }
    }

    // Also check for any English headers that might be table headers
    console.log('\n\n🔍 Searching for common stock data patterns...\n');
    for (let i = 0; i < Math.min(lines.length, 500); i++) {
      if (lines[i].match(/CODE|Ticker|Product|Stock|RANK|Shares|Turnover/i)) {
        console.log(`[Line ${i}] ${lines[i]}`);
        for (let j = i + 1; j < Math.min(i + 5, lines.length); j++) {
          console.log(`[Line ${j}] ${lines[j]}`);
        }
        console.log('---');
        i += 10;
      }
    }

  } catch (error) {
    console.error('❌ Error:', error);
  } finally {
    await browser.close();
  }
}

debugPageStructure().catch(console.error);
