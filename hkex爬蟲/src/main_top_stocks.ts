import { PlaywrightCrawler } from 'crawlee';
import fs from 'fs';
import path from 'path';

// Configuration
const DATA_DIR = 'data/top_stocks';

// Trading days for September and October 2025
const TRADING_DAYS_CONFIG: { [key: string]: number[] } = {
  '2025-09': [1, 2, 3, 4, 5, 8, 9, 10, 11, 12, 15, 16, 17, 18, 19, 22, 23, 24, 25, 26, 29, 30],
  '2025-10': [2, 3, 4, 6, 7, 8, 9, 10, 13, 14, 15, 16, 17, 20, 21, 22, 23, 24, 27, 28, 29, 30, 31],
};

async function main() {
  // Create data directory if not exists
  if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
  }

  // Generate direct URLs for all trading days
  const startUrls: any[] = [];

  for (const monthKey of ['2025-09', '2025-10']) {
    const tradingDays = TRADING_DAYS_CONFIG[monthKey];
    if (!tradingDays) continue;

    const [year, month] = monthKey.split('-');

    for (const day of tradingDays) {
      const dateStr = String(day).padStart(2, '0');
      const monthNum = month;
      const yearNum = year.slice(-2);

      const url = `https://www.hkex.com.hk/chi/stat/smstat/dayquot/d${yearNum}${monthNum}${dateStr}c.htm`;

      startUrls.push({
        url: url,
        userData: {
          dateNum: day,
          dateStr: `${year}-${month}-${dateStr}`
        }
      });
    }
  }

  console.log(`\n🚀 HKEX Top 10 Stocks Crawler`);
  console.log(`📅 Processing 9月 + 10月`);
  console.log(`📊 Created ${startUrls.length} direct URLs`);

  const crawler = new PlaywrightCrawler({
    requestHandler: async ({ request, page, log }) => {
      const userData = request.userData as any;
      const dateStr = userData?.dateStr;

      if (!dateStr) {
        log.error(`❌ No date info`);
        return;
      }

      log.info(`Processing: ${dateStr}`);

      try {
        await page.waitForTimeout(2000);

        // Extract both top 10 tables using REGEX
        const result = await page.evaluate(() => {
          const bodyText = document.body.innerText;
          const topByShares: any[] = [];
          const topByTurnover: any[] = [];

          // Extract SHARES section: "10 MOST ACTIVES (SHARES)" 后的10行数据
          const sharesPattern = /10 MOST ACTIVES \(SHARES\)([\s\S]*?)(?=---|$)/;
          const sharesMatch = bodyText.match(sharesPattern);
          if (sharesMatch) {
            const sharesText = sharesMatch[1];
            // 匹配数据行: CODE TICKER PRODUCT NAME CURRENCY SHARES TURNOVER HIGH LOW
            // 例如: 58048 UB#HSI RP2802W ... HKD 17,197,420,000 567,558,390 0.058 0.017
            const rowPattern = /(\d+)\s+([A-Z#]+)\s+([A-Z0-9]+)\s+(.+?)\s+(HKD|USD)\s+([\d,]+)\s+([\d,]+)\s+([\d.]+)\s+([\d.]+)/g;
            let rowMatch;
            while ((rowMatch = rowPattern.exec(sharesText)) && topByShares.length < 10) {
              topByShares.push({
                code: rowMatch[1],
                ticker: rowMatch[2],
                product: rowMatch[3],
                name_chi: rowMatch[4].trim(),
                currency: rowMatch[5],
                shares_traded: rowMatch[6],
                turnover: rowMatch[7],
                high: rowMatch[8],
                low: rowMatch[9]
              });
            }
          }

          // Extract DOLLARS section: "10 MOST ACTIVES (DOLLARS)" 后的10行数据
          const dollarsPattern = /10 MOST ACTIVES \(DOLLARS\)([\s\S]*?)(?=---|$)/;
          const dollarsMatch = bodyText.match(dollarsPattern);
          if (dollarsMatch) {
            const dollarsText = dollarsMatch[1];
            // 同样的模式
            const rowPattern = /(\d+)\s+([A-Z#]+)\s+([A-Z0-9]+)\s+(.+?)\s+(HKD|USD)\s+([\d,]+)\s+([\d,]+)\s+([\d.]+)\s+([\d.]+)/g;
            let rowMatch;
            while ((rowMatch = rowPattern.exec(dollarsText)) && topByTurnover.length < 10) {
              topByTurnover.push({
                code: rowMatch[1],
                ticker: rowMatch[2],
                product: rowMatch[3],
                name_chi: rowMatch[4].trim(),
                currency: rowMatch[5],
                shares_traded: rowMatch[6],
                turnover: rowMatch[7],
                high: rowMatch[8],
                low: rowMatch[9]
              });
            }
          }

          return { topByShares, topByTurnover };
        });

        log.info(`✓ ${dateStr}: Shares=${result.topByShares.length}, Turnover=${result.topByTurnover.length}`);

        // Write CSV files
        writeTopStocksCSV(dateStr, result.topByShares, 'by_shares');
        writeTopStocksCSV(dateStr, result.topByTurnover, 'by_turnover');

      } catch (error) {
        log.error(`Error processing ${dateStr}: ${error}`);
      }
    },
    maxRequestsPerCrawl: undefined,
    maxRequestRetries: 1,
    navigationTimeoutSecs: 30,
    maxCrawlDepth: 1,
    maxRequestsPerMinute: 20,
  });

  try {
    const startTime = Date.now();
    await crawler.run(startUrls);
    const duration = ((Date.now() - startTime) / 1000).toFixed(1);

    console.log(`\n✅ Crawler completed in ${duration} seconds!`);
    console.log(`📊 Output folder: ${DATA_DIR}`);

  } catch (error) {
    console.error('❌ Crawler error:', error);
  }
}

function writeTopStocksCSV(dateStr: string, stocks: any[], type: string) {
  const outputDir = DATA_DIR;
  const cleanNumber = (val: any) => String(val).replace(/,/g, '').trim();

  const header = 'Date,Rank,Code,Ticker,Product,Name_CHI,Currency,Shares_Traded,Turnover_HKD,High,Low\n';

  let csvContent = header;
  stocks.forEach((stock, index) => {
    const row = [
      dateStr,
      index + 1,
      stock.code,
      stock.ticker,
      stock.product,
      stock.name_chi,
      stock.currency,
      cleanNumber(stock.shares_traded),
      cleanNumber(stock.turnover),
      stock.high,
      stock.low
    ].join(',');
    csvContent += row + '\n';
  });

  // Write individual file
  const csvFile = path.join(outputDir, `top_stocks_${type}_${dateStr}.csv`);
  fs.writeFileSync(csvFile, csvContent);

  // Append to merged file
  const mergedFile = path.join(outputDir, `top_stocks_${type}_all.csv`);
  if (!fs.existsSync(mergedFile)) {
    fs.appendFileSync(mergedFile, header);
  }
  const rows = csvContent.split('\n').slice(1);
  rows.forEach(row => {
    if (row.trim()) {
      fs.appendFileSync(mergedFile, row + '\n');
    }
  });
}

main().catch(console.error);
