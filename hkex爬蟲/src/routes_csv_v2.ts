import { createPlaywrightRouter } from 'crawlee';
import fs from 'fs';
import path from 'path';

export const router = createPlaywrightRouter();

router.addDefaultHandler(async ({ request, page, log, pushData }) => {
    log.info(`Scraping HKEX Daily Market Statistics - All Dates`);

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

        log.info(`Found ${dateLinksCount} clickable date links`);

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

                log.info(`[${i + 1}/${dateLinksCount}] Clicking date: ${dateText?.trim()}`);

                // Click the date link
                await dateLocator.click();

                // Wait for data to load
                await page.waitForTimeout(2500);

                // Extract market data for this specific date
                const dailyMarketData = await page.evaluate(() => {
                    const allData: any = {
                        tables: [],
                        marketData: [],
                        pageText: "",
                        extractionTime: new Date().toISOString()
                    };

                    // Get all text content
                    const pageText = document.body.innerText;
                    allData.pageText = pageText.substring(0, 5000);

                    // Find all tables on the page
                    const tables = document.querySelectorAll('table');

                    tables.forEach((table, tableIndex) => {
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
                            const tableInfo = {
                                tableIndex,
                                rowCount: tableRows.length,
                                columnCount: tableRows[0]?.length || 0,
                                rows: tableRows
                            };

                            // Check for numeric data (market statistics)
                            const hasNumericData = tableRows.some(row =>
                                row.some(cell => /[0-9]/.test(cell) && cell.length > 0)
                            );

                            if (hasNumericData) {
                                allData.marketData.push(tableInfo);
                            } else {
                                allData.tables.push(tableInfo);
                            }
                        }
                    });

                    return allData;
                });

                // Extract metrics from the market data tables
                const metrics = extractMetricsFromTables(dailyMarketData.marketData);

                // Store the daily data
                const dailyRecord = {
                    date: dateText?.trim() || `Date_${i + 1}`,
                    marketData: dailyMarketData.marketData,
                    tables: dailyMarketData.tables,
                    metrics: metrics,
                    pageText: dailyMarketData.pageText,
                    extractedAt: dailyMarketData.extractionTime
                };

                allDailyData.push(dailyRecord);

                log.info(`✓ Successfully extracted data for: ${dateText?.trim()}`);

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

        log.info(`Completed! Processed ${allDailyData.length} dates`);

        // Push completion data
        await pushData({
            url: request.loadedUrl,
            timestamp: new Date().toISOString(),
            totalDatesProcessed: allDailyData.length,
            datesWithMarketData: allDailyData.filter(d => d.marketData.length > 0).length,
            totalRowsExtracted: allDailyData.reduce((sum, d) =>
                sum + d.marketData.reduce((s: number, t: any) => s + t.rowCount, 0), 0)
        });

    } catch (error) {
        log.error(`Error during scraping: ${error}`);
        throw error;
    }
});

function extractMetricsFromTables(marketData: any[]): any {
    const metrics: any = {
        trading_volume: '',
        advanced_stocks: '',
        declined_stocks: '',
        unchanged_stocks: '',
        turnover_hkd: '',
        deals: '',
        morning_close: '',
        afternoon_close: '',
        change: '',
        change_percent: ''
    };

    marketData.forEach((table) => {
        table.rows.forEach((row: string[]) => {
            const rowText = row.join('|');

            if (rowText.includes('成交股份') || rowText.includes('Sec. Traded')) {
                const match = rowText.match(/(\d+(?:[,，]?\d+)*)/);
                if (match) metrics.trading_volume = match[1];
            }

            if (rowText.includes('上升股份') || rowText.includes('Advanced')) {
                const match = rowText.match(/(\d+(?:[,，]?\d+)*)/);
                if (match) metrics.advanced_stocks = match[1];
            }

            if (rowText.includes('下降股份') || rowText.includes('Declined')) {
                const match = rowText.match(/(\d+(?:[,，]?\d+)*)/);
                if (match) metrics.declined_stocks = match[1];
            }

            if (rowText.includes('無變股份') || rowText.includes('Unchanged')) {
                const match = rowText.match(/(\d+(?:[,，]?\d+)*)/);
                if (match) metrics.unchanged_stocks = match[1];
            }

            if (rowText.includes('成交金額') || rowText.includes('金額') || rowText.includes('Turnover')) {
                const match = rowText.match(/(\d+(?:[,，]?\d+)*)/);
                if (match) metrics.turnover_hkd = match[1];
            }

            if (rowText.includes('宗數') || rowText.includes('Deals')) {
                const match = rowText.match(/(\d+(?:[,，]?\d+)*)/);
                if (match) metrics.deals = match[1];
            }
        });
    });

    return metrics;
}

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
