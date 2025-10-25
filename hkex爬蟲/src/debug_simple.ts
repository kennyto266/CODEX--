import { chromium } from 'playwright';

async function debugSimple() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  try {
    const url = 'https://www.hkex.com.hk/chi/stat/smstat/dayquot/d251002c.htm';
    console.log(`打开URL: ${url}`);
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    const pageText = await page.textContent('body');
    
    if (!pageText) {
      console.log('❌ 获取不到页面内容');
      return;
    }

    const lines = pageText.split('\n');
    console.log(`\n总共 ${lines.length} 行\n`);

    // 寻找包含数字和股票代码的行
    console.log('🔍 寻找 "MOST ACTIVES" 附近的内容:\n');
    
    let found = false;
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      // 检查是否包含 ACTIVES 或相关关键字
      if (line.includes('ACTIVES') || line.includes('成交')) {
        console.log(`[第${i}行] "${line}"`);
        
        // 打印前后5行
        for (let j = Math.max(0, i - 2); j < Math.min(i + 10, lines.length); j++) {
          console.log(`  [${j}] "${lines[j]}"`);
        }
        console.log('\n---\n');
        found = true;
      }
    }
    
    if (!found) {
      console.log('❌ 没有找到 ACTIVES 相关内容');
      console.log('\n查看前100行的内容:\n');
      for (let i = 0; i < Math.min(100, lines.length); i++) {
        if (lines[i].trim()) {
          console.log(`[${i}] ${lines[i]}`);
        }
      }
    }

  } catch (error) {
    console.error('❌ 错误:', error);
  } finally {
    await browser.close();
  }
}

debugSimple().catch(console.error);
