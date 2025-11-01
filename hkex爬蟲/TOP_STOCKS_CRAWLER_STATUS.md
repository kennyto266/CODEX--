# Top Stocks Crawler - Status Report

**Date:** 2025-10-20
**Status:** ⚠️ **Partial Implementation - Data Extraction Issue**

---

## Summary

The top stocks crawler has been created and is successfully:
- ✅ Processing all 45 trading dates (September + October 2025)
- ✅ Creating output CSV files for both tables
- ✅ Running without errors (45/45 requests successful)
- ✅ Generating proper CSV headers

However:
- ❌ Data extraction is returning 0 stocks per date instead of 10

---

## Current Implementation

### Files Created
- **src/main_top_stocks.ts** - Main crawler entry point
- **package.json** - Updated with `start:top-stocks` script

### Crawler Configuration
```
Request Duration: 135 seconds for 45 dates
Success Rate: 100% (45/45)
URL Pattern: https://www.hkex.com.hk/chi/stat/smstat/dayquot/d{YY}{MM}{DD}c.htm
Output: data/top_stocks/
```

### Output Structure
```
data/top_stocks/
├── top_stocks_by_shares_2025-09-01.csv      (header only)
├── top_stocks_by_shares_2025-09-02.csv
├── ... (45 files total)
├── top_stocks_by_shares_all.csv             (merged - header only)
├── top_stocks_by_turnover_2025-09-01.csv
├── ... (45 files total)
└── top_stocks_by_turnover_all.csv           (merged - header only)
```

### CSV Headers
```
Date,Rank,Code,Ticker,Product,Name_CHI,Currency,Shares_Traded,Turnover_HKD,High,Low
```

---

## Root Cause Analysis

### Issue
The page text extraction via `page.textContent()` is not finding:
- "10 MOST ACTIVES (SHARES)" section
- "10 MOST ACTIVES (DOLLARS)" section

### Investigation Results
From curl inspection of the HTML source, the sections DO exist on the HKEX page:
```
10 MOST ACTIVES (DOLLARS)
CODE | CUR | TURNOVER ($) | SHARES TRADED | HIGH | LOW
 9988 BABA-W ...
 2800 TRACKER FUND ...
 ...
```

```
10 MOST ACTIVES (SHARES)
CODE | CUR | SHARES TRADED | TURNOVER ($) | HIGH | LOW
58048 UB#HSI RP2802W ...
57406 SG#HSI RP2804K ...
...
```

### Possible Causes

1. **Playwright Text Extraction Issue**
   - Page encoding is Big5 (not UTF-8)
   - Playwright's `textContent()` might not preserve the exact formatting
   - Formatting characters may be different than expected

2. **Section Header Format**
   - The headers might not appear exactly as "10 MOST ACTIVES (SHARES)" in extracted text
   - The text might have extra whitespace or special characters
   - Line breaks might be inserted differently

3. **Line Splitting Issue**
   - The `split('\n')` might not correctly identify line boundaries
   - Multi-line entries or special formatting might be breaking the logic

---

## Next Steps to Fix

### Option 1: Use Regex Patterns (Recommended)
Instead of looking for exact header text, use regex patterns to find the table data:

```typescript
// More flexible pattern matching
const sharesPattern = /(\d+)\s+([A-Z#]+)\s+([A-Z0-9]+)\s+(.+?)\s+(HKD|USD)\s+([\d,]+)\s+([\d,]+)\s+([\d.]+)\s+([\d.]+)/g;
```

### Option 2: Extract HTML Instead of Text
Use `page.content()` to get raw HTML, then parse with a proper HTML parser:

```typescript
const htmlContent = await page.content();
// Parse with cheerio or similar library
```

### Option 3: Debug Current Text Extraction
Create a debug output to see exactly what text Playwright extracts:

```bash
npm run start:dev -- src/debug_text_extraction.ts > debug_output.txt
```

This will show:
- Exact line content around "MOST ACTIVES"
- Whether the sections are found
- What the extracted text looks like

---

## Files to Update

### Primary Fix Location
`src/main_top_stocks.ts` - Lines 66-168 (the `page.evaluate()` function)

### Testing Command
```bash
npm run start:top-stocks
```

### Verification
Check output files:
```bash
head -5 data/top_stocks/top_stocks_by_shares_2025-09-01.csv
```

Should show data rows, not just the header.

---

## Quick Reference

### Current Output (Empty)
```
Date,Rank,Code,Ticker,Product,Name_CHI,Currency,Shares_Traded,Turnover_HKD,High,Low
```

### Expected Output
```
Date,Rank,Code,Ticker,Product,Name_CHI,Currency,Shares_Traded,Turnover_HKD,High,Low
2025-09-01,1,9988,BABA-W,普通,中文名,HKD,96036992,17573327509,185.00,179.10
2025-09-01,2,2800,TRACKER FUND,普通,中文名,HKD,465975893,13007849213,28.04,27.52
```

---

## Related Files

- **Documentation:** `HKEX_CRAWLER_GUIDE.md`
- **Market Data Crawler:** `src/main_hkex_multi_month.ts` (working ✅)
- **Package Scripts:** `npm run start:top-stocks`

---

## Notes

- The main market data crawler (`npm run start:hkex`) works successfully with similar extraction patterns
- The difference suggests the page structure or formatting differs between the two data sources
- The encoding difference (Big5 vs UTF-8) may play a role
- Consider if the top stocks data might be in a different location or loaded via JavaScript

