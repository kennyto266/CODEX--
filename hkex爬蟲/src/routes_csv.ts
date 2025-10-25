import { createPlaywrightRouter } from 'crawlee';
import fs from 'fs';
import path from 'path';

export const router = createPlaywrightRouter();

// Hong Kong holidays and non-trading days for October 2025
const HOLIDAYS_OCTOBER_2025 = [1]; // Oct 1 is National Day
const NON_TRADING_DAYS = [5, 11, 12, 18, 19, 25, 26]; // Sundays

const isHolidayOrNonTradingDay = (date: number): boolean => {
    return HOLIDAYS_OCTOBER_2025.includes(date) || NON_TRADING_DAYS.includes(date);
};

router.addDefaultHandler(async ({ request, page, log }) => {
    log.info(`Scraping HKEX Daily Market Statistics - ALL Trading Days (Skipping holidays/weekends)`);

    try {
        // Wait for the page to fully load
        await page.waitForTimeout(3000);

        // Store all daily data
        const allDailyData: any[] = [];
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');

        // Extract all clickable date links
        let dateLinksCount = await page.locator('table a').count();

        if (dateLinksCount === 0) {
            dateLinksCount = await page.locator('table td a').count();
        }

        if (dateLinksCount === 0) {
            dateLinksCount = await page.locator('a:has-text(/^\\d+$/)').count();
        }

        log.info(`Found ${dateLinksCount} clickable date links - will extract trading days only (skip holidays/weekends)`);

        // Click each date and extract data
        for (let i = 0; i < dateLinksCount; i++) {
            try {
                // Get fresh date links each iteration
                let dateLocator = page.locator('table a').nth(i);
                let dateText = await dateLocator.textContent();

                if (!dateText || dateText.trim() === '') {
                    dateLocator = page.locator('a:has-text(/^\\d+$/)').nth(i);
                    dateText = await dateLocator.textContent();
                }

                const dateNum = parseInt(dateText?.trim() || '0');

                // Skip holidays and non-trading days
                if (isHolidayOrNonTradingDay(dateNum)) {
                    log.info(`⏭️  [${i + 1}/${dateLinksCount}] Skipping date ${dateNum} (holiday/non-trading day)`);
                    continue;
                }

                log.info(`[${i + 1}/${dateLinksCount}] Clicking date: ${dateText?.trim()}`);

                // Click the date link
                await dateLocator.click();

                // Wait for data to load - try longer wait
                await page.waitForTimeout(5000);

                // Try scrolling to see if data is below the fold
                await page.evaluate(() => window.scrollBy(0, 300));
                await page.waitForTimeout(1000);

                // Extract market data for this specific date
                const dailyMarketData = await page.evaluate(() => {
                    const allData: any = {
                        tableData: [],
                        metrics: {},
                        pageText: "",
                        allTableContents: []  // 保存所有表格內容用於調試
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
                                const match = rowText.match(/(\\d+(?:[,，]?\\d+)*)/);
                                if (match) allData.metrics.trading_volume = match[1];
                            }

                            if (rowText.includes('上升股份') || rowText.includes('Advanced')) {
                                const match = rowText.match(/(\\d+(?:[,，]?\\d+)*)/);
                                if (match) allData.metrics.advanced_stocks = match[1];
                            }

                            if (rowText.includes('下降股份') || rowText.includes('Declined')) {
                                const match = rowText.match(/(\\d+(?:[,，]?\\d+)*)/);
                                if (match) allData.metrics.declined_stocks = match[1];
                            }

                            if (rowText.includes('無變股份') || rowText.includes('Unchanged')) {
                                const match = rowText.match(/(\\d+(?:[,，]?\\d+)*)/);
                                if (match) allData.metrics.unchanged_stocks = match[1];
                            }

                            if (rowText.includes('成交金額') || rowText.includes('金額') || rowText.includes('Turnover')) {
                                const match = rowText.match(/(\\d+(?:[,，]?\\d+)*)/);
                                if (match) allData.metrics.turnover_hkd = match[1];
                            }

                            if (rowText.includes('宗數') || rowText.includes('Deals')) {
                                const match = rowText.match(/(\\d+(?:[,，]?\\d+)*)/);
                                if (match) allData.metrics.deals = match[1];
                            }
                        });
                    });

                    return allData;
                });

                // Store the daily data
                const dateStr = dateText?.trim() || `Date_${i + 1}`;
                const dailyRecord = {
                    date: dateStr,
                    dateIndex: i + 1,  // 索引號
                    metrics: dailyMarketData.metrics,
                    tableCount: dailyMarketData.tableData.length
                };

                allDailyData.push(dailyRecord);

                log.info(`✓ Date ${i + 1}/35: "${dateStr}" - Tables found: ${dailyMarketData.tableData.length}, Metrics: ${Object.keys(dailyMarketData.metrics).length}`);

                // 在交易日時保存HTML以供調試
                if (!isHolidayOrNonTradingDay(parseInt(dateStr))) {
                    const debugHtmlFile = path.join('data', `debug_page_date_${dateStr}.html`);
                    fs.writeFileSync(debugHtmlFile, dailyMarketData.pageText);
                    log.info(`  📄 Debug: Saved page HTML to ${debugHtmlFile}`);

                    // 同時也打印出所有表格的第一行內容（用於調試）
                    if (dailyMarketData.tableData.length > 0) {
                        log.info(`  📋 Tables summary:`);
                        dailyMarketData.tableData.forEach((table: any, idx: number) => {
                            if (table.rows.length > 0) {
                                const firstRow = table.rows[0].slice(0, 5).join(' | ');
                                log.info(`     Table ${idx + 1}: ${firstRow}...`);
                            }
                        });
                    }
                }

                if (Object.keys(dailyMarketData.metrics).length > 0) {
                    log.info(`  ✓ Successfully extracted data for date: ${dateStr}`);
                } else {
                    log.info(`  ⚠ No market data found in tables for date: ${dateStr}`);
                }

            } catch (dateError) {
                log.info(`Failed to process date ${i + 1}: ${dateError}`);
            }

            // Navigate back to the calendar
            if (i < dateLinksCount - 1) {
                try {
                    await page.goBack();
                    await page.waitForTimeout(1500);
                } catch (navError) {
                    log.info(`Navigation error: ${navError}`);
                }
            }
        }

        // Save data to CSV files
        const outputDir = 'data';
        if (!fs.existsSync(outputDir)) {
            fs.mkdirSync(outputDir, { recursive: true });
        }

        // Generate CSV from extracted data
        generateCSVFromData(allDailyData, outputDir);

        log.info(`✅ Completed! Processed ${allDailyData.length} dates`);

    } catch (error) {
        log.error(`Error during scraping: ${error}`);
        throw error;
    }
});

function generateCSVFromData(allDailyData: any[], outputDir: string) {
    const header = 'Date,Trading_Volume,Advanced_Stocks,Declined_Stocks,Unchanged_Stocks,Turnover_HKD,Deals,Morning_Close,Afternoon_Close,Change,Change_Percent\n';
    let csvContent = header;

    allDailyData.forEach((record) => {
        const metrics = record.metrics;
        const cleanNumber = (val: any) => {
            if (!val) return '';
            return String(val).replace(/,/g, '').replace(/，/g, '').trim();
        };

        const row = [
            record.date,
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

        csvContent += row + '\n';
    });

    const csvFile = path.join(outputDir, 'hkex_all_market_data.csv');
    fs.writeFileSync(csvFile, csvContent);
    console.log(`✅ CSV saved to ${csvFile}`);
}
