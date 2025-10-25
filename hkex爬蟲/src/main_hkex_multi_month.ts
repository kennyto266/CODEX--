import { PlaywrightCrawler } from 'crawlee';
import fs from 'fs';
import path from 'path';
import { router } from './routes_csv_direct_urls.js';

// Configuration
const DATA_DIR = 'data';

// Trading days configuration: month -> trading days
// 2025年9月 (September 2025): 1-30, excluding Sundays and holidays
// 2025年10月 (October 2025): 1-31, excluding Sundays and holidays
const TRADING_DAYS_CONFIG: { [key: string]: number[] } = {
  '2025-09': [1, 2, 3, 4, 5, 8, 9, 10, 11, 12, 15, 16, 17, 18, 19, 22, 23, 24, 25, 26, 29, 30],
  // Note: 9/6-7 = weekend, 9/13-14 = weekend, 9/20-21 = weekend, 9/27-28 = weekend
  '2025-10': [2, 3, 4, 6, 7, 8, 9, 10, 13, 14, 15, 16, 17, 20, 21, 22, 23, 24, 27, 28, 29, 30, 31],
  // Note: 10/1 = Holiday (National Day), 10/5,12,19,26 = Sundays, 10/11 = Holiday (Mid-Autumn day after)
};

interface CrawlerOptions {
  months?: string[];  // e.g., ['2025-09', '2025-10']
  clearData?: boolean; // clear existing data before crawling
}

async function main(options: CrawlerOptions = {}) {
  const { months = ['2025-09', '2025-10'], clearData = true } = options;

  // Create data directory if not exists
  if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
  }

  // Clear existing data if requested
  if (clearData) {
    const existingFiles = fs.readdirSync(DATA_DIR);
    for (const file of existingFiles) {
      if (file.startsWith('hkex_market_data_') || file === 'hkex_all_market_data.csv') {
        fs.unlinkSync(path.join(DATA_DIR, file));
      }
    }
    console.log('🗑️  Cleared existing data files');
  }

  // Generate direct URLs for all trading days
  const startUrls: any[] = [];

  for (const monthKey of months) {
    const tradingDays = TRADING_DAYS_CONFIG[monthKey];
    if (!tradingDays) {
      console.warn(`⚠️  Month ${monthKey} not configured`);
      continue;
    }

    const [year, month] = monthKey.split('-');

    for (const day of tradingDays) {
      const dateStr = String(day).padStart(2, '0');
      const monthNum = month;
      const yearNum = year.slice(-2); // Get last 2 digits of year (25 for 2025)

      // URL pattern: d251002c.htm (25 = year 2025, 10 = month, 02 = day, c = main board)
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

  console.log(`\n🚀 HKEX Multi-Month Crawler`);
  console.log(`📅 Months: ${months.join(', ')}`);
  console.log(`📊 Created ${startUrls.length} direct URLs for trading days`);
  console.log(`⏱️  Each request gets 30 seconds timeout`);
  console.log(`🔗 Request rate: 20 requests/minute\n`);

  const crawler = new PlaywrightCrawler({
    requestHandler: router,
    maxRequestsPerCrawl: undefined,  // Process all requests
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

    // Show generated CSV files
    const csvFiles = fs.readdirSync(DATA_DIR).filter(f => f.startsWith('hkex_market_data_') && f.endsWith('.csv'));
    console.log(`📊 Generated ${csvFiles.length} individual CSV files`);

    if (fs.existsSync(path.join(DATA_DIR, 'hkex_all_market_data.csv'))) {
      const content = fs.readFileSync(path.join(DATA_DIR, 'hkex_all_market_data.csv'), 'utf-8');
      const lines = content.split('\n').filter(l => l.trim());
      console.log(`📈 Merged CSV with ${lines.length} rows (including header)`);
      console.log(`💾 File: ${path.join(DATA_DIR, 'hkex_all_market_data.csv')}`);
    }
  } catch (error) {
    console.error('❌ Crawler error:', error);
  }
}

// Parse command line arguments
const args = process.argv.slice(2);
const options: CrawlerOptions = {
  months: ['2025-09', '2025-10'],
  clearData: true
};

// Support: npm run start:hkex -- --months 2025-09,2025-10 --no-clear
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--months' && i + 1 < args.length) {
    options.months = args[i + 1].split(',');
  }
  if (args[i] === '--no-clear') {
    options.clearData = false;
  }
}

main(options).catch(console.error);
