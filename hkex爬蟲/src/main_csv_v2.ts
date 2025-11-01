import { PlaywrightCrawler } from 'crawlee';
import fs from 'fs';
import path from 'path';
import { router } from './routes_csv_v2.js';

// Configuration
const DATA_DIR = 'data';

async function main() {
  // Create data directory if not exists
  if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
  }

  const startUrls = [{
    url: 'https://www.hkex.com.hk/chi/stat/smstat/dayquot/qtn_c.asp'
  }];

  console.log(`🚀 Starting crawler to extract all dates...`);

  const crawler = new PlaywrightCrawler({
    requestHandler: router,
    maxRequestsPerCrawl: 1,
    maxRequestRetries: 2,
    navigationTimeoutSecs: 120,  // Longer timeout for clicking through many dates
  });

  try {
    await crawler.run(startUrls);
    console.log('✅ Crawler completed!');
  } catch (error) {
    console.error('❌ Crawler error:', error);
  }
}

main().catch(console.error);
