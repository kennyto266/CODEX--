import { PlaywrightCrawler } from 'crawlee';
import fs from 'fs';
import path from 'path';
import { router } from './routes_csv_direct_urls.js';

// Configuration
const DATA_DIR = 'data';

// October 2025 - All trading days (skip holidays and Sundays)
// Oct 1 = Holiday (National Day)
// Oct 5, 12, 19, 26 = Sundays
// Trading days: 2, 3, 4, 6, 7, 8, 9, 10, 13, 14, 15, 16, 17, 20, 21, 22, 23, 24, 27, 28, 29, 30, 31
const TRADING_DAYS_OCTOBER = [2, 3, 4, 6, 7, 8, 9, 10, 13, 14, 15, 16, 17, 20, 21, 22, 23, 24, 27, 28, 29, 30, 31];

async function main() {
  // Create data directory if not exists
  if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
  }

  // Generate direct URLs for all trading days
  const startUrls: any[] = [];

  for (const day of TRADING_DAYS_OCTOBER) {
    // URL pattern: d251002c.htm (25 = year 2025, 10 = October, 02 = day, c = main board)
    const dateStr = String(day).padStart(2, '0');
    const url = `https://www.hkex.com.hk/chi/stat/smstat/dayquot/d2510${dateStr}c.htm`;

    startUrls.push({
      url: url,
      userData: {
        dateNum: day,
        dateStr: `2025-10-${dateStr}`
      }
    });
  }

  console.log(`🚀 Starting direct URL crawler...`);
  console.log(`📅 Created ${startUrls.length} direct URLs for trading days`);
  console.log(`⏱️  Each request gets 30 seconds timeout`);

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
