import { chromium } from 'playwright';

async function testHKEXScraping() {
  const browser = await chromium.launch({ headless: false });  // Show browser
  const page = await browser.newPage();

  try {
    console.log('🌐 Navigating to HKEX website...');
    await page.goto('https://www.hkex.com.hk/chi/stat/smstat/dayquot/qtn_c.asp', {
      waitUntil: 'networkidle'
    });

    console.log('⏱️ Waiting for page to load...');
    await page.waitForTimeout(3000);

    console.log('🔍 Looking for date links...');
    const dateLinks = await page.locator('table a').count();
    console.log(`Found ${dateLinks} date links`);

    if (dateLinks > 0) {
      console.log('\n📅 Clicking date "2" (October 2)...');

      // Click date 2
      await page.locator('table a').first().click();  // First link after Oct 1

      console.log('⏳ Waiting for page navigation...');
      await page.waitForTimeout(2000);

      // Check URL
      const currentUrl = page.url();
      console.log(`📍 Current URL: ${currentUrl}`);

      // Get page title
      const title = await page.title();
      console.log(`📄 Page title: ${title}`);

      // Get all text on page
      const pageText = await page.textContent('body');
      console.log('\n📋 Page content (first 500 chars):');
      console.log(pageText?.substring(0, 500) || 'No content');

      // Try to find market data keywords
      const hasMarketData = pageText?.includes('成交股份') ||
                            pageText?.includes('Trading Volume') ||
                            pageText?.includes('Sec. Traded');

      console.log(`\n🎯 Contains market data keywords: ${hasMarketData ? '✅ YES' : '❌ NO'}`);

      // Find all tables
      const tables = await page.locator('table').count();
      console.log(`📊 Found ${tables} tables on page`);

      // Get table contents
      for (let i = 0; i < Math.min(tables, 3); i++) {
        const tableText = await page.locator(`table`).nth(i).textContent();
        console.log(`\n📑 Table ${i + 1} (first 200 chars):`);
        console.log(tableText?.substring(0, 200) || 'Empty table');
      }
    }

  } catch (error) {
    console.error('❌ Error:', error);
  } finally {
    console.log('\n⏸️ Browser open for inspection - press Enter to close...');
    await new Promise(resolve => setTimeout(resolve, 10000));  // Keep open for 10 seconds
    await browser.close();
  }
}

testHKEXScraping().catch(console.error);
