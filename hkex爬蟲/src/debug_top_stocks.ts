import { chromium } from 'playwright';

async function debug() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  try {
    const url = 'https://www.hkex.com.hk/chi/stat/smstat/dayquot/d251002c.htm';
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    const result = await page.evaluate(() => {
      const pageText = document.body.innerText;
      const lines = pageText.split('\n');

      let sharesLines: string[] = [];
      let foundShares = false;

      for (let i = 0; i < lines.length; i++) {
        if (lines[i].includes('十大成交股數最多股票')) {
          foundShares = true;
          console.log(`Found at line ${i}: ${lines[i]}`);
          
          // Get next 15 lines
          for (let j = i; j < Math.min(i + 15, lines.length); j++) {
            sharesLines.push(lines[j]);
            console.log(`[${j}] "${lines[j]}"`);
          }
          break;
        }
      }

      return sharesLines;
    });

    console.log('\n=== RAW LINES ===');
    result.forEach((line, idx) => {
      console.log(`${idx}: ${line}`);
    });

  } catch (error) {
    console.error('Error:', error);
  } finally {
    await browser.close();
  }
}

debug().catch(console.error);
