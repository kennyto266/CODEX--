import { PlaywrightCrawler } from 'crawlee';
import fs from 'fs';
import path from 'path';
import { router } from './routes_csv.js';

// Configuration
const DATA_DIR = 'data';

async function main() {
  // Create data directory if not exists
  if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
  }

  // 單一請求，會自動偵測所有可點擊的日期
  const startUrls = [{
    url: 'https://www.hkex.com.hk/chi/stat/smstat/dayquot/qtn_c.asp',
    userData: {
      extractAllDates: true  // 告訴 router 要提取所有日期
    }
  }];

  console.log(`🚀 Starting crawler to extract ALL clickable dates...`);

  const crawler = new PlaywrightCrawler({
    requestHandler: router,
    maxRequestsPerCrawl: 1,
    maxRequestRetries: 0,
    navigationTimeoutSecs: 180,  // 3分鐘超時
  });

  try {
    await crawler.run(startUrls);
    console.log('✅ Crawler completed!');

    // 顯示生成的CSV文件
    const csvFiles = fs.readdirSync(DATA_DIR).filter(f => f.startsWith('hkex_market_data_') && f.endsWith('.csv'));
    console.log(`📊 Generated ${csvFiles.length} CSV files`);
  } catch (error) {
    console.error('❌ Crawler error:', error);
  }
}

main().catch(console.error);
