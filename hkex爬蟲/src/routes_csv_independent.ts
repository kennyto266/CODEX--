import { createPlaywrightRouter } from 'crawlee';
import fs from 'fs';
import path from 'path';

export const router = createPlaywrightRouter();

router.addDefaultHandler(async ({ request, page, log }) => {
    const userData = request.userData as any;
    const dateToClick = userData?.dateToClick;

    if (!dateToClick) {
        log.error(`❌ No date specified in userData`);
        return;
    }

    log.info(`Processing independent request for date: ${dateToClick}`);

    try {
        // Wait for page to load
        await page.waitForTimeout(2000);

        // Find and click the specific date
        let dateLocator = page.locator('table a').nth(dateToClick - 1);  // Adjust for 0-based index
        let dateText = await dateLocator.textContent();

        if (!dateText || dateText.trim() === '') {
            dateLocator = page.locator('a:has-text(/^\\d+$/)').nth(dateToClick - 1);
            dateText = await dateLocator.textContent();
        }

        const parsedDate = parseInt(dateText?.trim() || '0');

        if (parsedDate !== dateToClick) {
            log.info(`⚠️  Date mismatch: Expected ${dateToClick}, got ${parsedDate}`);
        }

        log.info(`Clicking date: ${dateText?.trim()}`);

        // Click the date link
        await dateLocator.click();

        // Wait for data to load
        await page.waitForTimeout(5000);

        // Try scrolling to see if data is below the fold
        await page.evaluate(() => window.scrollBy(0, 300));
        await page.waitForTimeout(1000);

        // Extract market data for this specific date
        const dailyMarketData = await page.evaluate(() => {
            const allData: any = {
                tableData: [],
                metrics: {},
                pageText: ""
            };

            // Get all text content
            const pageText = document.body.innerText;
            allData.pageText = pageText;

            // Find all tables on the page
            const tables = document.querySelectorAll('table');

            tables.forEach((table) => {
                const rows = table.querySelectorAll('tr');
                const tableRows: string[][] = [];

                rows.forEach(row => {
                    const cells = row.querySelectorAll('td, th');
                    const rowArray: string[] = [];

                    cells.forEach(cell => {
                        const text = cell.textContent?.trim() || '';
                        rowArray.push(text);
                    });

                    if (rowArray.some(cell => cell.length > 0)) {
                        tableRows.push(rowArray);
                    }
                });

                if (tableRows.length > 2) {
                    allData.tableData.push({
                        rowCount: tableRows.length,
                        columnCount: tableRows[0]?.length || 0,
                        rows: tableRows
                    });
                }
            });

            // Extract metrics from tables
            allData.tableData.forEach((table: any) => {
                table.rows.forEach((row: string[]) => {
                    const rowText = row.join('|');

                    if (rowText.includes('成交股份') || rowText.includes('Sec. Traded')) {
                        const match = rowText.match(/(\d+(?:[,，]?\d+)*)/);
                        if (match) allData.metrics.trading_volume = match[1];
                    }

                    if (rowText.includes('上升股份') || rowText.includes('Advanced')) {
                        const match = rowText.match(/(\d+(?:[,，]?\d+)*)/);
                        if (match) allData.metrics.advanced_stocks = match[1];
                    }

                    if (rowText.includes('下降股份') || rowText.includes('Declined')) {
                        const match = rowText.match(/(\d+(?:[,，]?\d+)*)/);
                        if (match) allData.metrics.declined_stocks = match[1];
                    }

                    if (rowText.includes('無變股份') || rowText.includes('Unchanged')) {
                        const match = rowText.match(/(\d+(?:[,，]?\d+)*)/);
                        if (match) allData.metrics.unchanged_stocks = match[1];
                    }

                    if (rowText.includes('成交金額') || rowText.includes('金額') || rowText.includes('Turnover')) {
                        const match = rowText.match(/(\d+(?:[,，]?\d+)*)/);
                        if (match) allData.metrics.turnover_hkd = match[1];
                    }

                    if (rowText.includes('宗數') || rowText.includes('Deals')) {
                        const match = rowText.match(/(\d+(?:[,，]?\d+)*)/);
                        if (match) allData.metrics.deals = match[1];
                    }
                });
            });

            return allData;
        });

        // Save debug HTML
        const debugHtmlFile = path.join('data', `debug_page_date_${dateToClick}.html`);
        fs.writeFileSync(debugHtmlFile, dailyMarketData.pageText);
        log.info(`📄 Debug HTML saved: ${debugHtmlFile}`);

        // Log metrics
        const metricsCount = Object.keys(dailyMarketData.metrics).length;
        log.info(`✓ Date ${dateToClick}: Tables=${dailyMarketData.tableData.length}, Metrics=${metricsCount}`);

        if (metricsCount === 0) {
            log.info(`⚠️  No market metrics found for date ${dateToClick}`);
        }

        // Generate CSV for this single date
        generateSingleDateCSV(dateToClick, dailyMarketData);

    } catch (error) {
        log.error(`Error processing date ${dateToClick}: ${error}`);
        throw error;
    }
});

function generateSingleDateCSV(dateNum: number, data: any) {
    const outputDir = 'data';
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }

    const dateStr = `2025-10-${String(dateNum).padStart(2, '0')}`;
    const metrics = data.metrics;

    const cleanNumber = (val: any) => {
        if (!val) return '';
        return String(val).replace(/,/g, '').replace(/，/g, '').trim();
    };

    // Create header
    const header = 'Date,Trading_Volume,Advanced_Stocks,Declined_Stocks,Unchanged_Stocks,Turnover_HKD,Deals,Morning_Close,Afternoon_Close,Change,Change_Percent\n';

    // Create row
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
