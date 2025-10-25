import { chromium } from 'playwright';

async function testDirectURL() {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // 直接访问October 2的数据页面 (你提供的URL)
    const url = 'https://www.hkex.com.hk/chi/stat/smstat/dayquot/d251002c.htm';

    console.log(`🌐 Navigating directly to: ${url}`);
    await page.goto(url, { waitUntil: 'networkidle' });

    console.log('⏱️ Page loaded, waiting for content...');
    await page.waitForTimeout(2000);

    // 获取页面内容
    const pageText = await page.textContent('body');

    // 检查市场数据
    console.log('\n📋 Searching for market data...');
    const keywords = [
      '成交股份',
      'Sec. Traded',
      '上升股份',
      'Advanced',
      '下降股份',
      'Declined',
      'Trading Volume',
      '成交金額'
    ];

    for (const keyword of keywords) {
      const found = pageText?.includes(keyword) ? '✅' : '❌';
      console.log(`  ${found} ${keyword}`);
    }

    // 获取所有表格
    const tables = await page.locator('table').count();
    console.log(`\n📊 Found ${tables} tables`);

    // 提取表格数据
    if (tables > 0) {
      console.log('\n📋 Table contents:');
      for (let i = 0; i < Math.min(tables, 3); i++) {
        const tableText = await page.locator(`table`).nth(i).textContent();
        if (tableText && tableText.trim().length > 0) {
          console.log(`\nTable ${i + 1}:`);
          console.log(tableText.substring(0, 300));
        }
      }
    }

    // 查找包含数字的行（市场数据通常包含大数字）
    console.log('\n🔍 Searching for numeric data (market statistics usually contain numbers):');
    const allText = pageText || '';
    const lines = allText.split('\n');
    let dataLinesFound = 0;

    for (const line of lines) {
      // 查找包含大数字的行
      if (/\d{6,}/.test(line) && line.length > 20) {
        console.log(`  📍 ${line.substring(0, 100)}`);
        dataLinesFound++;
        if (dataLinesFound >= 5) break;
      }
    }

    if (dataLinesFound === 0) {
      console.log('  ❌ No numeric data lines found');
    }

  } catch (error) {
    console.error('❌ Error:', error);
  } finally {
    await browser.close();
  }
}

testDirectURL().catch(console.error);
