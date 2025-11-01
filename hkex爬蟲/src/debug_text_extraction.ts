import { chromium } from 'playwright';

async function debugTextExtraction() {
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

    const lines = pageText.split('\n');
    
    // Find lines containing the keywords
    console.log('\n🔍 === Searching for section headers ===\n');
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      if (line.includes('MOST ACTIVES')) {
        console.log(`\n[Line ${i}] HEADER: "${line}"`);
        
        // Print next 20 lines
        for (let j = i + 1; j < Math.min(i + 20, lines.length); j++) {
          console.log(`[Line ${j}] "${lines[j]}"`);
        }
        console.log('\n---\n');
        i += 20;
      }
    }

  } catch (error) {
    console.error('❌ Error:', error);
  } finally {
    await browser.close();
  }
}

debugTextExtraction().catch(console.error);
