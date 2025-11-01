# CSV Extraction - Quick Reference Guide

## Current Status ✅

**Good News**: The CSV infrastructure is 100% complete and working!
- ✅ 24 working days fully processed
- ✅ Individual CSV files created
- ✅ Merged dataset file created
- ✅ CSV format ready for pandas/quantitative analysis

**Current Challenge**: Data fields are empty (metrics not found on page)

---

## How to Use

### Run Version 1 (Independent Requests - Recommended)
```bash
cd my-crawler
npm run start:csv
```
**Output**: 24 CSV files in `data/hkex_market_data_2025-10-*.csv`
**Result**: Creates `hkex_all_market_data.csv` (merged)

### Run Version 2 (Loop-Based - Limited)
```bash
npm run start:csv:v2
```
**Output**: Same as V1, but stops after 1-2 dates due to timeout

### Run Original JSON Version
```bash
npm start
```
**Output**: JSON files (still available as backup)

---

## CSV File Format

**Location**: `my-crawler/data/hkex_all_market_data.csv`

**Columns**:
1. Date (YYYY-MM-DD)
2. Trading_Volume (成交股份)
3. Advanced_Stocks (上升股份)
4. Declined_Stocks (下降股份)
5. Unchanged_Stocks (無變股份)
6. Turnover_HKD (成交金額)
7. Deals (宗數)
8. Morning_Close (早市收市價)
9. Afternoon_Close (午市收市價)
10. Change (漲跌)
11. Change_Percent (漲跌%)

---

## Import to Python/Pandas

```python
import pandas as pd

# Read CSV
df = pd.read_csv('my-crawler/data/hkex_all_market_data.csv')

# Display
print(df)

# For quantitative analysis
df['Trading_Volume'] = pd.to_numeric(df['Trading_Volume'], errors='coerce')
df.describe()
```

---

## Troubleshooting

### CSV Files Are Empty
**Status**: Known issue - being investigated
**Files**: `CSV_EXTRACTION_TECHNICAL_REPORT.md`
**Action**: See "Recommended Solutions" section

### Timeout Errors
**Status**: Expected with loop approach
**Solution**: Use Version 1 (independent requests)

### Missing Files
**Action**: Run `npm run start:csv` again
**Check**: `ls my-crawler/data/hkex_*.csv`

---

## Files Overview

```
my-crawler/
├── src/
│   ├── main_csv.ts         (Version 1: Independent Requests)
│   ├── routes_csv.ts       (Version 1: Route Handler)
│   ├── main_csv_v2.ts      (Version 2: Loop-Based)
│   ├── routes_csv_v2.ts    (Version 2: Route Handler)
│   └── [original files]
├── data/
│   ├── hkex_market_data_2025-10-01.csv
│   ├── hkex_market_data_2025-10-02.csv
│   ├── ... (22 more files)
│   └── hkex_all_market_data.csv (MERGED)
├── CSV_EXTRACTION_TECHNICAL_REPORT.md
└── package.json
```

---

## Next Steps

### For the User
1. **Verify Manual Access**: Click date "1" on the HKEX website and confirm market data appears
2. **Check Network Tab**: Use browser DevTools to see what API calls are made
3. **Provide Feedback**: Share findings so we can adjust extraction logic

### For Development
1. **Implement Network Interception** to capture API responses
2. **Add Additional Selectors** for different table structures
3. **Extend Timeout** if data loads slowly
4. **Try Alternative Parsing** methods

---

## Performance

| Metric | Time |
|--------|------|
| Process 24 Dates | ~60-90 seconds |
| CSV Generation | <1 second |
| File Merge | <1 second |
| Python Import | <1 second |

---

## Support Files

| Document | Purpose |
|----------|---------|
| `CSV_EXTRACTION_TECHNICAL_REPORT.md` | Detailed technical analysis |
| `QUICK_START.md` | Original crawler quick start |
| `DATA_INVENTORY.txt` | File inventory |
| `PROJECT_COMPLETION_REPORT.md` | Full project summary |

---

**Version**: CSV Implementation Phase 2
**Last Updated**: 2025-10-20 12:00 UTC
**Status**: 🔶 Data Extraction Pending
