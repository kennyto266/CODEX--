# HKEX CSV Data Extraction - Technical Report

**Date**: 2025-10-20
**Status**: 🔶 In Progress - Data Extraction Challenge Identified
**Framework**: Crawlee + Playwright
**Target URL**: https://www.hkex.com.hk/chi/stat/smstat/dayquot/qtn_c.asp

---

## Executive Summary

We successfully built a Crawlee-based crawler that:
- ✅ Processes all 24 working days in October 2025
- ✅ Generates CSV files with proper structure
- ✅ Merges individual daily CSVs into consolidated dataset
- ⚠️ **Issue**: Market data metrics not being extracted (metrics are empty)

The root cause is that **clicking date links in the calendar doesn't reliably display the market data table** that the page.evaluate() can extract.

---

## Files Created

### Version 1: Independent Requests Approach (main_csv.ts + routes_csv.ts)
**Status**: Processes all 24 dates but data extraction fails
- `main_csv.ts`: Creates 24 independent requests (one per working day)
- `routes_csv.ts`: Handles individual date requests
- **Result**: Creates 24 CSV files + merged file, but all data fields are empty

### Version 2: Single-Handler Loop Approach (main_csv_v2.ts + routes_csv_v2.ts)
**Status**: Timeout after 1-2 dates due to 60-second handler limit
- `main_csv_v2.ts`: Single request, loops through all dates
- `routes_csv_v2.ts`: Original routes.ts logic adapted for CSV output
- **Result**: Successfully processes date 1 but hits timeout on date 2, browser closes

---

## Technical Issues Identified

### Issue 1: Timeout in Loop-Based Extraction
**Problem**: When clicking through many dates in a single handler, Crawlee's 60-second timeout fires
- **Symptom**: "requestHandler timed out after 60 seconds"
- **Cause**: ~2-3 sec per date × 35 dates = ~105 seconds needed
- **Solution**: Use independent requests approach (Version 1)

### Issue 2: Browser Closing After Timeout
**Problem**: When handler timeout fires, Crawlee closes the browser context
- **Symptom**: "Target page, context or browser has been closed"
- **Cause**: Crawlee's safety mechanism
- **Impact**: All subsequent date processing fails
- **Solution**: Limit loop iterations or use independent requests

### Issue 3: Data Extraction Failure (Core Issue)
**Problem**: Market data table NOT appearing after clicking date link
- **Symptom**: `page.evaluate()` finds 0 tables with numeric data
- **Evidence**: Debug screenshots show only calendar, no market data table
- **Root Cause**: The date click might be navigating to a different page or data loads via AJAX
- **Impact**: All metrics fields remain empty in CSV

---

## Debug Screenshots Analysis

### Screenshot After Clicking Date "1"
- Shows: Only the calendar layout and navigation
- Missing: Market statistics table (成交股份, 上升股份, etc.)
- Conclusion: Either:
  1. Date click navigates to new page (need to wait longer for page load)
  2. Market data loads via AJAX in hidden div
  3. Data requires additional interaction or scroll
  4. The calendar link is not the correct trigger

---

## CSV Output Structure

**Current Output** (Empty Data):
```csv
Date,Trading_Volume,Advanced_Stocks,Declined_Stocks,Unchanged_Stocks,Turnover_HKD,Deals,Morning_Close,Afternoon_Close,Change,Change_Percent
2025-10-01,,,,,,,,,,
2025-10-02,,,,,,,,,,
...
```

**Expected Output** (With Data):
```csv
Date,Trading_Volume,Advanced_Stocks,Declined_Stocks,Unchanged_Stocks,Turnover_HKD,Deals,Morning_Close,Afternoon_Close,Change,Change_Percent
2025-10-01,123456789,654,123,45,12345678900,98765,17234.56,17289.34,+54.78,+0.32%
2025-10-02,234567890,732,145,67,23456789012,109876,17289.34,17345.67,-12.45,-0.07%
...
```

---

## Attempted Solutions

| Approach | Result | Issue |
|----------|--------|-------|
| **Single Request Loop** | Fails after 2 dates | 60-second timeout |
| **Independent Requests** | All 24 dates process | Data extraction fails |
| **Scrolling After Click** | Page still shows calendar | No data appears |
| **Extended Wait Times** | No improvement | Data never appears |
| **Multiple Selectors** | Found 35 date links | Clicking doesn't reveal data |

---

## Recommended Solutions

### Option 1: Direct API/XHR Interception (Recommended)
Use Playwright to intercept network requests:
```typescript
await page.on('response', (response) => {
    if (response.url().includes('api') || response.url().includes('data')) {
        // Extract market data directly from API response
        const data = await response.json();
    }
});
```
**Pros**: Get data directly from source
**Cons**: Requires identifying correct API endpoint

### Option 2: Alternative Data Source
Use HKEX's alternative data endpoints:
- Bloomberg Terminal API
- Yahoo Finance API (if available for HK stocks)
- Official HKEX API (if documented)

**Pros**: May have better structure
**Cons**: May require authentication

### Option 3: Refined Page Interaction
```typescript
// After clicking date:
await page.waitForTimeout(5000);
await page.waitForSelector('table.market-data', { timeout: 10000 });
await page.bringToFront();
// Then extract
```

### Option 4: Use Puppeteer Instead of Playwright
Puppeteer may handle dynamic content differently:
- Different DOM manipulation
- Different waiting mechanisms
- May reveal data that Playwright misses

**Pros**: Different engine, might work
**Cons**: Rewrite required

---

## Files Status

| File | Status | Purpose |
|------|--------|---------|
| `src/main.ts` | ✅ Working | Original JSON extractor |
| `src/routes.ts` | ✅ Working | Original data extraction logic |
| `src/main_csv.ts` | ⚠️ Partial | Independent requests approach |
| `src/routes_csv.ts` | ⚠️ Partial | CSV extraction (v1) |
| `src/main_csv_v2.ts` | ⚠️ Partial | Loop-based approach |
| `src/routes_csv_v2.ts` | ⚠️ Partial | CSV extraction (v2) |
| `package.json` | ✅ Updated | Added npm scripts |

---

## Next Steps

### Immediate Actions
1. **Investigate Network Requests**: Use Chrome DevTools to see what happens when clicking a date
2. **Verify HKEX Website Update**: The website structure might have changed
3. **Manual Browser Testing**: Verify that market data actually appears in a real browser

### For User
1. Can you confirm the market data table appears when you manually click a date in your browser?
2. What does the URL change to when you click a date?
3. Are there any API calls in the Network tab when clicking dates?

### Technical Implementation
1. **Implement Network Interception** to capture the actual data source
2. **Add Request/Response Logging** to debug what's being received
3. **Try Different Selectors** with increased specificity
4. **Implement Fallback Mechanism** if data isn't found in page text

---

## Performance Metrics

| Metric | Value |
|--------|-------|
| CSV Files Generated | 24 |
| Merged CSV File | ✅ Created |
| Total Processing Time | ~1-2 minutes |
| Timeout Issues | Yes (after ~2 dates in loop) |
| Data Extraction Rate | 0% (no data extracted) |

---

## Conclusion

The CSV infrastructure is **100% ready and working**. The architecture correctly:
- ✅ Generates unique requests for all dates
- ✅ Creates individual CSV files
- ✅ Merges datasets into single file
- ✅ Formats data with proper headers

The **only remaining issue** is identifying where the market data resides after clicking a date. Once the data source is located, integrating it into the CSV generation will be straightforward.

**Next Session**: Focus on debugging the date-click mechanism and data source location.

---

**Generated**: 2025-10-20 12:00 UTC
**Framework**: Crawlee 3.x + Playwright Latest
**Node.js**: 14+
**TypeScript**: 5.x
