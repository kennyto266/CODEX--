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

  // Generate requests for all trading dates (skip holidays)
  const startUrls: any[] = [];

  for (let dateNum = 1; dateNum <= 35; dateNum++) {
    if (!isHolidayOrNonTradingDay(dateNum)) {
      startUrls.push({
        url: `https://www.hkex.com.hk/chi/stat/smstat/dayquot/qtn_c.asp?date=${dateNum}`,  // Unique URL for each date
        userData: {
          dateToClick: dateNum,  // Tell router which date to click
          singleDateMode: true
        },
        uniqueKey: `hkex-date-${dateNum}`  // Explicit unique key
      });
    }
  }

  console.log(`🚀 Starting independent requests crawler...`);
  console.log(`📅 Created ${startUrls.length} independent requests (skipped ${8} holidays/non-trading days)`);
  console.log(`⏱️  Each request gets 30 seconds timeout (safe from 60-second limit)`);

  const crawler = new PlaywrightCrawler({
    requestHandler: router,
    maxRequestsPerCrawl: undefined,  // Process all requests
    maxRequestRetries: 1,
    navigationTimeoutSecs: 35,  // 35 seconds per date - safe margin
    maxCrawlDepth: 1,
    maxRequestsPerMinute: 15,  // Rate limiting to avoid overload
  });

  try {
    await crawler.run(startUrls);
    console.log('✅ Crawler completed!');

    // Show generated CSV files
    const csvFiles = fs.readdirSync(DATA_DIR).filter(f => f.startsWith('hkex_market_data_') && f.endsWith('.csv'));
    console.log(`📊 Generated ${csvFiles.length} individual CSV files`);

    // Check if merged file exists
    const mergedFile = path.join(DATA_DIR, 'hkex_all_market_data.csv');
    if (fs.existsSync(mergedFile)) {
      console.log(`✅ Merged CSV: hkex_all_market_data.csv`);
    }
  } catch (error) {
    console.error('❌ Crawler error:', error);
  }
}

main().catch(console.error);
