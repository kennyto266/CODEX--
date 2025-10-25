import { PlaywrightCrawler } from 'crawlee';
import fs from 'fs';
import path from 'path';
import { router } from './routes_csv_independent.js';

// Configuration
const DATA_DIR = 'data';

// Hong Kong holidays and non-trading days for October 2025
const HOLIDAYS_OCTOBER_2025 = [1]; // Oct 1 is National Day
const NON_TRADING_DAYS = [5, 11, 12, 18, 19, 25, 26]; // Sundays

const isHolidayOrNonTradingDay = (date: number): boolean => {
    return HOLIDAYS_OCTOBER_2025.includes(date) || NON_TRADING_DAYS.includes(date);
};

async function main() {
  // Create data directory if not exists
  if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
  }

  // Generate requests for FIRST 5 trading dates only (for quick testing)
  const startUrls: any[] = [];
  let count = 0;

  for (let dateNum = 1; dateNum <= 35 && count < 5; dateNum++) {
    if (!isHolidayOrNonTradingDay(dateNum)) {
      startUrls.push({
        url: 'https://www.hkex.com.hk/chi/stat/smstat/dayquot/qtn_c.asp',
        userData: {
          dateToClick: dateNum,
          singleDateMode: true
        }
      });
      count++;
    }
  }

  console.log(`🚀 Starting TEST with first ${startUrls.length} trading dates...`);

  const crawler = new PlaywrightCrawler({
    requestHandler: router,
    maxRequestsPerCrawl: undefined,
    maxRequestRetries: 0,
    navigationTimeoutSecs: 35,
    maxCrawlDepth: 1,
    maxRequestsPerMinute: 10,
  });

  try {
    const startTime = Date.now();
    await crawler.run(startUrls);
    const duration = ((Date.now() - startTime) / 1000).toFixed(1);
    console.log(`✅ Crawler completed in ${duration} seconds!`);

    // Show generated CSV files
    const csvFiles = fs.readdirSync(DATA_DIR).filter(f => f.startsWith('hkex_market_data_') && f.endsWith('.csv'));
    console.log(`📊 Generated ${csvFiles.length} CSV files`);

    if (fs.existsSync(path.join(DATA_DIR, 'hkex_all_market_data.csv'))) {
      const content = fs.readFileSync(path.join(DATA_DIR, 'hkex_all_market_data.csv'), 'utf-8');
      const lines = content.split('\n').filter(l => l.trim());
      console.log(`✅ Merged CSV with ${lines.length} rows (including header)`);
    }
  } catch (error) {
    console.error('❌ Crawler error:', error);
  }
}

main().catch(console.error);
