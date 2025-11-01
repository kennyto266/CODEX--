import { chromium } from 'playwright';

async function testTopStocks() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1600, height: 900 });

  try {
    const url = 'https://www.hkex.com.hk/chi/stat/smstat/dayquot/d251002c.htm';
    console.log(`🌐 Opening: ${url}`);
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    const pageText = await page.textContent('body');

    console.log('\n📊 === SEARCHING FOR TOP 10 STOCKS TABLE ===');

    // Search for the section
    if (pageText?.includes('十大成交股數最多股票')) {
      console.log('✅ Found: 十大成交股數最多股票');

      // Get the section content
      const lines = pageText.split('\n');
      let foundHeader = false;
      let tableData: string[] = [];

      for (let i = 0; i < lines.length; i++) {
        if (lines[i].includes('十大成交股數最多股票')) {
          foundHeader = true;
          console.log(`\n📌 Found at line ${i}`);
          // Print next 100 lines to see the structure
          for (let j = i; j < Math.min(i + 100, lines.length); j++) {
            console.log(`[${j}] ${lines[j]}`);
            tableData.push(lines[j]);
          }
          break;
        }
      }
    } else {
      console.log('❌ Not found: 十大成交股數最多股票');
    }

    console.log('\n\n🔍 === CHECKING FOR TABLES ===');
    const tables = await page.locator('table').count();
    console.log(`Found ${tables} tables total`);

    // Try to find the top 10 stocks table by looking for keywords
    for (let i = 0; i < Math.min(tables, 15); i++) {
      const tableText = await page.locator('table').nth(i).textContent();
      if (tableText && (
        tableText.includes('十大成交股數') ||
        tableText.includes('CODE') ||
        tableText.includes('股份編號') ||
        tableText.includes('SHARES TRADED')
      )) {
        console.log(`\n✅ Table ${i} might be top stocks:`);
        console.log(tableText.substring(0, 500));
        console.log('...');
      }
    }

    console.log('\n\n⏸️  Browser open for 60 seconds - Inspect the page');
    await page.waitForTimeout(60000);

  } catch (error) {
    console.error('❌ Error:', error);
  } finally {
    await browser.close();
  }
}

testTopStocks().catch(console.error);
