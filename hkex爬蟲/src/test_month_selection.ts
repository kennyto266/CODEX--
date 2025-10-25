import { chromium } from 'playwright';

async function testMonthSelection() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  try {
    const url = 'https://www.hkex.com.hk/chi/stat/smstat/dayquot/qtn_c.asp';
    console.log(`🌐 Opening: ${url}`);
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // Get page content
    const pageText = await page.textContent('body');
    
    // Look for date/month selection elements
    console.log('\n📋 === SEARCHING FOR DATE SELECTION ELEMENTS ===');
    
    // Check for select/dropdown elements
    const selects = await page.locator('select').count();
    console.log(`\n📊 Found ${selects} select elements`);
    
    for (let i = 0; i < selects; i++) {
      const selectElement = page.locator('select').nth(i);
      const options = await selectElement.locator('option').count();
      const id = await selectElement.getAttribute('id');
      const name = await selectElement.getAttribute('name');
      
      console.log(`\n  Select ${i}: id="${id}", name="${name}", options=${options}`);
      
      // Get first 5 options
      for (let j = 0; j < Math.min(options, 10); j++) {
        const option = await selectElement.locator('option').nth(j);
        const value = await option.getAttribute('value');
        const text = await option.textContent();
        console.log(`    [${j}] value="${value}" text="${text}"`);
      }
    }
    
    // Look for links that might be for month selection
    console.log('\n\n📎 === SEARCHING FOR MONTH/DATE LINKS ===');
    const links = await page.locator('a').count();
    console.log(`Total links: ${links}`);
    
    // Search for links containing date info
    for (let i = 0; i < Math.min(links, 100); i++) {
      const link = page.locator('a').nth(i);
      const href = await link.getAttribute('href');
      const text = await link.textContent();
      
      if (text && (text.includes('10') || text.includes('9') || text.includes('月') || text.includes('2025'))) {
        console.log(`  📍 Link ${i}: href="${href}" text="${text}"`);
      }
    }
    
    // Get the HTML around date selection area
    console.log('\n\n📑 === PAGE STRUCTURE (first 2000 chars) ===');
    console.log(pageText?.substring(0, 2000));
    
    console.log('\n⏸️  Browser open - check the page layout');
    await page.waitForTimeout(30000);

  } catch (error) {
    console.error('❌ Error:', error);
  } finally {
    await browser.close();
  }
}

testMonthSelection().catch(console.error);
