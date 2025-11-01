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

        // Extract all clickable date links (look for blue date numbers in calendar)
        // Try multiple selectors
        let dateLinksCount = await page.locator('table a').count();

        if (dateLinksCount === 0) {
            dateLinksCount = await page.locator('table td a').count();
        }

        if (dateLinksCount === 0) {
            // Try to find any clickable elements with numbers
            dateLinksCount = await page.locator('a:has-text(/^\\d+$/)').count();
        }

        log.info(`Found ${dateLinksCount} clickable date links`);

        // Click each date and extract data
        for (let i = 0; i < dateLinksCount; i++) {
            try {
                // Get fresh date links each iteration
                // Try to find the date link using different selectors
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

                // Store the daily data
                const dailyRecord = {
                    date: dateText?.trim() || `Date_${i + 1}`,
                    marketData: dailyMarketData.marketData,
                    tables: dailyMarketData.tables,
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

        // Save all daily data to JSON file
        const outputDir = 'data';
        if (!fs.existsSync(outputDir)) {
            fs.mkdirSync(outputDir, { recursive: true });
        }

        // Save complete daily data
        const outputFile = path.join(outputDir, `hkex_all_dates_${timestamp}.json`);
        fs.writeFileSync(outputFile, JSON.stringify(allDailyData, null, 2));
        log.info(`All daily data saved to ${outputFile}`);

        // Save summary
        const summaryFile = path.join(outputDir, `hkex_summary_${timestamp}.json`);
        const summary = {
            totalDatesProcessed: allDailyData.length,
            datesWithData: allDailyData.filter(d => d.marketData.length > 0).length,
            dates: allDailyData.map(d => ({
                date: d.date,
                marketDataTables: d.marketData.length,
                totalRows: d.marketData.reduce((sum: number, t: any) => sum + t.rowCount, 0)
            })),
            generatedAt: new Date().toISOString(),
            sourceUrl: 'https://www.hkex.com.hk/chi/stat/smstat/dayquot/qtn_c.asp'
        };
        fs.writeFileSync(summaryFile, JSON.stringify(summary, null, 2));
        log.info(`Summary saved to ${summaryFile}`);

        // Take a final screenshot
        const screenshotPath = path.join(outputDir, `hkex_final_${timestamp}.png`);
        await page.screenshot({ path: screenshotPath, fullPage: true });
        log.info(`Final screenshot saved to ${screenshotPath}`);

        // Push completion data
        await pushData({
            url: request.loadedUrl,
            timestamp: new Date().toISOString(),
            totalDatesProcessed: allDailyData.length,
            datesWithMarketData: allDailyData.filter(d => d.marketData.length > 0).length,
            totalRowsExtracted: allDailyData.reduce((sum, d) =>
                sum + d.marketData.reduce((s: number, t: any) => s + t.rowCount, 0), 0),
            outputFiles: {
                allData: outputFile,
                summary: summaryFile,
                screenshot: screenshotPath
            }
        });

        log.info(`Completed! Processed ${allDailyData.length} dates`);

    } catch (error) {
        log.error(`Error during scraping: ${error}`);
        throw error;
    }
});
