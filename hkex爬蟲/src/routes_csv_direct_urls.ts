import { createPlaywrightRouter } from 'crawlee';
import fs from 'fs';
import path from 'path';

export const router = createPlaywrightRouter();

router.addDefaultHandler(async ({ request, page, log }) => {
    const userData = request.userData as any;
    const dateNum = userData?.dateNum;
    const dateStr = userData?.dateStr;

    if (!dateNum || !dateStr) {
        log.error(`❌ No date info in userData`);
        return;
    }

    log.info(`Processing date: ${dateStr} (${dateNum})`);

    try {
        // Wait for page to load
        await page.waitForTimeout(2000);

        // Extract all text content
        const pageText = await page.textContent('body') || '';

        // Extract market data using regex patterns
        const marketData = await page.evaluate(() => {
            const data: any = {
                metrics: {},
                pageText: document.body.innerText
            };

            const bodyText = document.body.innerText;

            // Extract Trading Volume (成交股份 / Sec. Traded)
            // Pattern: "成交股份 Sec. Traded: 9026"
            let match = bodyText.match(/成交股份\s+Sec\.\s+Traded[:\s]+([0-9,]+)/);
            if (match) data.metrics.trading_volume = match[1];

            // Extract Advanced Stocks (上升股份 / Advanced)
            match = bodyText.match(/上升股份\s+Advanced\s*[:\s]+([0-9,]+)/);
            if (match) data.metrics.advanced_stocks = match[1];

            // Extract Declined Stocks (下降股份 / Declined)
            match = bodyText.match(/下降股份\s+Declined\s*[:\s]+([0-9,]+)/);
            if (match) data.metrics.declined_stocks = match[1];

            // Extract Unchanged Stocks (無變股份 / Unchanged)
            match = bodyText.match(/無變股份\s+Unchanged\s*[:\s]+([0-9,]+)/);
            if (match) data.metrics.unchanged_stocks = match[1];

            // Extract Turnover HKD (金額(HK$))
            match = bodyText.match(/金額\s*\(\s*HK\$\s*\)\s*[:\s]+([0-9,]+)/);
            if (match) data.metrics.turnover_hkd = match[1];

            // Extract Deals (宗數(Deals))
            match = bodyText.match(/宗數\s*\(\s*Deals\s*\)\s*[:\s]+([0-9,]+)/);
            if (match) data.metrics.deals = match[1];

            // Extract Hang Seng Index values
            // Morning Close: 27245.68, Afternoon Close: 27287.12
            match = bodyText.match(/恆生指數[\s\S]*?(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+([+\-]\d+\.\d+)/);
            if (match) {
                data.metrics.morning_close = match[1];
                data.metrics.afternoon_close = match[2];
                data.metrics.change = match[3];  // The point change
                data.metrics.change_percent = match[4];  // The percentage change
            }

            return data;
        });

        const metricsCount = Object.keys(marketData.metrics).length;
        log.info(`✓ Date ${dateStr}: Extracted ${metricsCount} metrics`);

        if (metricsCount > 0) {
            log.info(`  Metrics: ${JSON.stringify(marketData.metrics)}`);
        } else {
            log.info(`  ⚠️ No metrics found for date ${dateStr}`);
        }

        // Generate CSV for this single date
        generateSingleDateCSV(dateStr, marketData.metrics);

    } catch (error) {
        log.error(`Error processing date ${dateStr}: ${error}`);
        throw error;
    }
});

function generateSingleDateCSV(dateStr: string, metrics: any) {
    const outputDir = 'data';
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }

    const cleanNumber = (val: any) => {
        if (!val) return '';
        return String(val).replace(/,/g, '').replace(/，/g, '').trim();
    };

    // Create header
    const header = 'Date,Trading_Volume,Advanced_Stocks,Declined_Stocks,Unchanged_Stocks,Turnover_HKD,Deals,Morning_Close,Afternoon_Close,Change,Change_Percent\n';

    // Create row with data
    const row = [
        dateStr,
        cleanNumber(metrics.trading_volume),
        cleanNumber(metrics.advanced_stocks),
        cleanNumber(metrics.declined_stocks),
        cleanNumber(metrics.unchanged_stocks),
        cleanNumber(metrics.turnover_hkd),
        cleanNumber(metrics.deals),
        cleanNumber(metrics.morning_close),
        cleanNumber(metrics.afternoon_close),
        cleanNumber(metrics.change),
        cleanNumber(metrics.change_percent)
    ].join(',');

    // Write individual CSV
    const csvFile = path.join(outputDir, `hkex_market_data_${dateStr}.csv`);
    fs.writeFileSync(csvFile, header + row + '\n');

    // Append to merged CSV
    const mergedFile = path.join(outputDir, 'hkex_all_market_data.csv');
    if (!fs.existsSync(mergedFile)) {
        // First time - write header
        fs.appendFileSync(mergedFile, header);
    }
    // Append row
    fs.appendFileSync(mergedFile, row + '\n');
}
