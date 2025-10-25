import { chromium } from 'playwright';

async function inspectMonthPage() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1400, height: 900 });

  try {
    const url = 'https://www.hkex.com.hk/chi/stat/smstat/dayquot/qtn_c.asp';
    console.log(`🌐 Opening: ${url}`);
    await page.goto(url, { waitUntil: 'networkidle' });

    console.log('⏱️  Page loaded, taking 5 seconds to stabilize...');
    await page.waitForTimeout(5000);

    // Get page text to search for month information
    const pageText = await page.textContent('body');

    console.log('\n📊 === MONTH/DATE ELEMENTS ===');

    // Check for all select elements
    const selects = await page.locator('select').count();
    console.log(`\n📌 Found ${selects} <select> elements`);

    for (let i = 0; i < selects; i++) {
      const selectElement = page.locator('select').nth(i);
      const name = await selectElement.getAttribute('name');
      const id = await selectElement.getAttribute('id');
      const value = await selectElement.inputValue();
      const options = await selectElement.locator('option').count();

      console.log(`\n  [${i}] <select id="${id}" name="${name}" value="${value}" options=${options}>`);

      // Show options
      for (let j = 0; j < Math.min(options, 15); j++) {
        const option = selectElement.locator('option').nth(j);
        const optValue = await option.getAttribute('value');
        const optText = await option.textContent();
        console.log(`      [${j}] value="${optValue}" → "${optText}"`);
      }
    }

    // Check for any clickable month/date links
    console.log('\n\n📎 === LOOKING FOR MONTH LINKS ===');
    const links = await page.locator('a').count();
    let monthLinkCount = 0;

    for (let i = 0; i < links && monthLinkCount < 30; i++) {
      const link = page.locator('a').nth(i);
      const href = await link.getAttribute('href');
      const text = await link.textContent();
      const ariaLabel = await link.getAttribute('aria-label');

      // Look for month/date related links
      if (text && (
        text.includes('2025') ||
        text.includes('月') ||
        text.includes('9月') ||
        text.includes('10月') ||
        /202[0-9]-[01][0-9]/.test(text) ||
        /\d{1,2}月/.test(text)
      )) {
        monthLinkCount++;
        console.log(`  [${i}] href="${href}" text="${text}" aria="${ariaLabel}"`);
      }
    }

    if (monthLinkCount === 0) {
      console.log('  ❌ No month-related links found');
    }

    // Search for month text in page
    console.log('\n\n🔍 === SEARCHING FOR TEXT PATTERNS ===');
    const lines = pageText?.split('\n') || [];
    let foundMonths = 0;

    for (const line of lines) {
      if (line.includes('2025-09') || line.includes('2025-10') ||
          line.includes('9月') || line.includes('10月') ||
          (line.includes('月') && line.length < 100)) {
        console.log(`  📍 "${line.trim().substring(0, 80)}"`);
        foundMonths++;
        if (foundMonths >= 20) break;
      }
    }

    console.log('\n\n⏸️  BROWSER OPEN FOR 60 SECONDS - INSPECT THE PAGE');
    console.log('📍 Look for:');
    console.log('   - Month selection controls (dropdown, buttons, links)');
    console.log('   - How to navigate between 9月 and 10月');
    console.log('   - Navigation buttons or date pickers\n');

    await page.waitForTimeout(60000);

  } catch (error) {
    console.error('❌ Error:', error);
  } finally {
    await browser.close();
  }
}

inspectMonthPage().catch(console.error);
