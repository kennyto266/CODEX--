import { chromium } from 'playwright';

async function seePageContent() {
  const browser = await chromium.launch({ headless: false });  // Show browser
  const page = await browser.newPage();

  // Set viewport size
  await page.setViewportSize({ width: 1280, height: 800 });

  try {
    const url = 'https://www.hkex.com.hk/chi/stat/smstat/dayquot/d251002c.htm';
    console.log(`🌐 Opening: ${url}`);
    console.log('\n📌 Browser will stay open for 30 seconds for you to inspect\n');

    await page.goto(url, { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);

    // Get page content
    const pageText = await page.textContent('body');

    console.log('📋 === PAGE CONTENT ===');
    console.log(pageText?.substring(0, 2000) || 'No content');
    console.log('\n... (truncated) ...\n');

    // Try to find where the data is
    console.log('🔍 === SEARCHING FOR MARKET DATA ===');

    // Look for common patterns
    const patterns = [
      { name: '成交股份', regex: /成交股份[：:]+\s*([0-9,]+)/g },
      { name: 'Sec. Traded', regex: /Sec\.\s*Traded[：:]+\s*([0-9,]+)/g },
      { name: '上升股份', regex: /上升股份[：:]+\s*([0-9,]+)/g },
      { name: 'Advanced', regex: /Advanced[：:]+\s*([0-9,]+)/g },
      { name: '下降股份', regex: /下降股份[：:]+\s*([0-9,]+)/g },
      { name: 'Declined', regex: /Declined[：:]+\s*([0-9,]+)/g },
    ];

    for (const pattern of patterns) {
      const matches = pageText?.match(pattern.regex);
      if (matches) {
        console.log(`✅ ${pattern.name}: Found ${matches.length} occurrences`);
        console.log(`   Sample: ${matches[0]}`);
      } else {
        console.log(`❌ ${pattern.name}: Not found`);
      }
    }

    // Get all text with line breaks to see structure
    console.log('\n📑 === FULL PAGE STRUCTURE (first 3000 chars) ===');
    console.log(pageText?.substring(0, 3000) || 'No content');

    console.log('\n⏸️  Browser open - you have 30 seconds to inspect the page');
    console.log('📍 Look for the market data tables and values\n');

    await page.waitForTimeout(30000);

  } catch (error) {
    console.error('❌ Error:', error);
  } finally {
    await browser.close();
  }
}

seePageContent().catch(console.error);
