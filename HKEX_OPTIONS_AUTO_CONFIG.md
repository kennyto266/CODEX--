# HKEX 期權自動化爬取配置文件

**版本**: 1.0
**創建日期**: 2025-10-18
**用途**: 自動化爬取HKEX期權數據配置和規則

---

## 配置結構

```yaml
# ============================================
# HKEX 期權自動化爬取配置
# ============================================

system:
  version: "1.0"
  created_date: "2025-10-18"
  last_updated: "2025-10-18"
  status: "active"
  auto_interval_hours: 24
  run_time: "16:15"  # 每個交易日 16:15 執行

endpoints:
  base_url: "https://www.hkex.com.hk/Market-Data/Statistics/Derivatives-Market/Daily-Statistics"
  lang: "zh-HK"
  timeout_seconds: 30

# ============================================
# 期權類別定義 (已爬取)
# ============================================

options_classes:
  - id: "HSI_TECH"
    name_zh: "恒生科技指數期權"
    name_en: "HSI Tech Index Options"
    url_param: "select1=23&selection=%E6%81%92%E7%94%9F%E7%A7%91%E6%8A%80%E6%8C%87%E6%95%B8%E6%9C%9F%E6%AC%8A"
    symbol: "HSI_Tech"
    status: "✅ verified"
    first_crawl: "2025-10-18"

    # HTML 選擇器
    selectors:
      page_title: "3_195"  # uid
      link_target: "3_196"
      table_container: "xpath: //table[@role='table']"
      header_row: "tr:first-child"
      data_rows: "tbody tr"

      # 列位置 (0-based)
      columns:
        date: 0
        call_volume: 1
        put_volume: 2
        total_volume: 3
        call_oi: 4
        put_oi: 5
        total_oi: 6

    # 數據驗證規則
    validation:
      date_format: "YYYY MM DD"
      call_volume_min: 0
      call_volume_max: 999999
      total_volume_max: 999999
      put_call_ratio_min: 0.1
      put_call_ratio_max: 10.0

    # 數據轉換規則
    transformations:
      remove_thousand_separator: true
      timezone: "HKT"
      trading_hours: "09:30-16:00"

# ============================================
# 期權類別模板 (待爬取)
# ============================================

options_templates:

  # 恒生指數期權
  - id: "HSI"
    name_zh: "恒生指數期權"
    name_en: "HSI Index Options"
    status: "📋 pending"
    priority: 1
    url_param: "待配置"

  # 恒生中國企業指數期權
  - id: "HSI_CHINA"
    name_zh: "恒生中國企業指數期權"
    name_en: "HSI China Enterprises Options"
    status: "📋 pending"
    priority: 2
    url_param: "待配置"

  # 股票期權 - 騰訊
  - id: "TENCENT_0700"
    name_zh: "騰訊股票期權"
    name_en: "Tencent Stock Options"
    status: "📋 pending"
    priority: 3
    url_param: "待配置"

  # 股票期權 - 比亞迪
  - id: "BYD_1211"
    name_zh: "比亞迪股票期權"
    name_en: "BYD Stock Options"
    status: "📋 pending"
    priority: 4
    url_param: "待配置"

  # 股票期權 - 泡泡瑪特 (新)
  - id: "POP_9612"
    name_zh: "泡泡瑪特股票期權"
    name_en: "Pop Mart Stock Options (New)"
    status: "📋 pending"
    priority: 5
    url_param: "待配置"

# ============================================
# 爬取規則
# ============================================

crawling_rules:

  # 連接規則
  connection:
    method: "GET"
    headers:
      User-Agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
      Accept-Language: "zh-HK,zh;q=0.9"
      Referer: "https://www.hkex.com.hk"
    cookies_required: false
    javascript_required: true
    wait_selector: "成交"
    wait_timeout_ms: 10000

  # 數據解析規則
  parsing:
    format: "HTML_TABLE"
    encoding: "UTF-8"
    parser: "BeautifulSoup"

    table_structure:
      has_header: true
      header_row_index: 0
      data_start_row: 1
      date_column: 0
      separators: [","]

    # 數據清理
    cleaning:
      strip_whitespace: true
      remove_parentheses: false
      convert_numbers: true
      handle_missing_values: "skip"

  # 重試規則
  retry:
    max_retries: 3
    retry_delay_seconds: 5
    backoff_multiplier: 2
    retry_on_status: [429, 500, 502, 503, 504]

  # 錯誤處理
  error_handling:
    log_level: "INFO"
    alert_on_failure: true
    fallback_to_cache: true
    cache_days: 7

# ============================================
# 存儲配置
# ============================================

storage:

  # 主存儲
  primary:
    type: "CSV"
    location: "data/hkex_options/"
    filename_pattern: "{options_id}_{date}.csv"
    encoding: "UTF-8"
    backup_enabled: true

  # 備份
  backup:
    type: "JSON"
    location: "data/backup/hkex_options/"
    retention_days: 90

  # 數據庫
  database:
    enabled: true
    type: "SQLite"
    path: "data/hkex_options.db"

  # 版本控制
  versioning:
    enabled: true
    keep_versions: 30
    compression: "gzip"

# ============================================
# 通知配置
# ============================================

notifications:

  success:
    enabled: true
    channels: ["log"]
    message: "Successfully crawled {options_id} options data for {date}"

  failure:
    enabled: true
    channels: ["log", "email"]
    recipients: ["admin@example.com"]
    message: "Failed to crawl {options_id}: {error}"

  warning:
    enabled: true
    channels: ["log"]
    message: "Data quality warning for {options_id}"

# ============================================
# 性能配置
# ============================================

performance:
  max_concurrent_crawls: 3
  rate_limit_requests_per_minute: 10
  timeout_seconds: 30
  connection_pool_size: 10

# ============================================
# 日誌配置
# ============================================

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  location: "logs/hkex_options_crawler.log"
  rotation:
    max_size_mb: 100
    backup_count: 10
```

---

## 已爬取數據記錄

```yaml
# ============================================
# 已爬取數據索引
# ============================================

crawled_data:

  # 恒生科技指數期權
  HSI_TECH:
    status: "✅ COMPLETE"
    first_crawl_date: "2025-10-18"
    last_crawl_date: "2025-10-18"
    data_points: 238
    date_range: "2025-09-01 to 2025-10-17"
    records_per_day: 7

    # 統計信息
    statistics:
      call_volume:
        min: 0
        max: 8538
        avg: 2367.65
        latest: 5678
      put_volume:
        min: 5
        max: 6788
        avg: 3136.47
        latest: 6588
      total_volume:
        min: 6
        max: 12615
        avg: 5504.12
        latest: 12266
      call_oi:
        min: 32133
        max: 52710
        avg: 40951.35
        latest: 41716
      put_oi:
        min: 52799
        max: 79420
        avg: 66686.76
        latest: 74202
      total_oi:
        min: 86542
        max: 132130
        avg: 107638.11
        latest: 115918

    # 數據質量
    quality_metrics:
      completeness: "100%"
      validity: "100%"
      consistency: "100%"
      timeliness: "real-time"

    # 文件位置
    files:
      csv: "data/hkex_options/HSI_TECH_latest.csv"
      json: "data/backup/hkex_options/HSI_TECH_latest.json"
      db: "data/hkex_options.db"

    # 數據可用性
    availability:
      format: "CSV, JSON, SQLite"
      update_frequency: "Daily"
      next_update: "2025-10-19 16:15"
```

---

## 自動化爬取計劃

```yaml
# ============================================
# 自動化爬取計劃
# ============================================

automation_schedule:

  # Phase 1: 已完成
  phase_1:
    status: "✅ COMPLETED"
    date: "2025-10-18"
    target: "HSI_TECH"
    result: "238 records extracted"

  # Phase 2: 進行中
  phase_2:
    status: "🔄 IN_PROGRESS"
    planned_date: "2025-10-19"
    targets:
      - "HSI"
      - "HSI_CHINA"
    expected_records: "1000+"

  # Phase 3: 計劃中
  phase_3:
    status: "📋 PLANNED"
    planned_date: "2025-10-20"
    targets:
      - "TENCENT_0700"
      - "BYD_1211"
      - "POP_9612"
    expected_records: "1500+"

  # Phase 4: 計劃中
  phase_4:
    status: "📋 PLANNED"
    planned_date: "2025-10-25"
    target: "All options classes"
    action: "Consolidate and verify all data"
    expected_records: "5000+"

# ============================================
# 日程表
# ============================================

daily_schedule:

  # 交易日 (周一至周五)
  trading_days:

    # 日間爬取
    intraday:
      enabled: true
      time: "13:00"  # 午市開始後
      targets: ["all"]
      frequency: "every 4 hours"

    # 收盤爬取 (重要)
    closing:
      enabled: true
      time: "16:15"  # 收市後15分鐘
      targets: ["all"]
      frequency: "daily"
      priority: "HIGH"

    # 夜盤爬取
    after_hours:
      enabled: false
      time: "19:00"
      targets: []

  # 非交易日
  non_trading_days:
    enabled: false
    targets: []

# ============================================
# 監控和告警
# ============================================

monitoring:

  health_check:
    enabled: true
    interval_minutes: 60
    checks:
      - crawl_success_rate > 95%
      - data_freshness < 24 hours
      - error_rate < 5%

  alerts:
    - name: "Crawl Failure"
      condition: "success_rate < 95%"
      action: "send_email"

    - name: "Data Stale"
      condition: "data_age > 48 hours"
      action: "send_alert"

    - name: "High Error Rate"
      condition: "error_rate > 10%"
      action: "pause_crawling"
```

---

## 使用說明

### 1. 查看已爬取數據
```bash
# 查看恒生科技指數期權數據
cat data/hkex_options/HSI_TECH_latest.csv

# 查看統計信息
grep -A 20 "HSI_TECH:" HKEX_OPTIONS_AUTO_CONFIG.md
```

### 2. 新增期權類別
```yaml
# 在 options_templates 中添加新類別:
- id: "NEW_OPTIONS_ID"
  name_zh: "新期權名稱"
  name_en: "New Options Name"
  status: "📋 pending"
  priority: 6
  url_param: "需從頁面獲取"
```

### 3. 運行自動爬取
```bash
# 爬取指定期權類別
python auto_crawler.py --options_id HSI_TECH --date 2025-10-19

# 爬取所有計劃的類別
python auto_crawler.py --crawl_all

# 查看爬取狀態
python auto_crawler.py --status
```

### 4. 數據驗證
```bash
# 驗證數據完整性
python data_validator.py --options_id HSI_TECH

# 生成質量報告
python data_validator.py --report daily
```

---

## 文件結構

```
hkex_options/
├── HKEX_OPTIONS_AUTO_CONFIG.md          # 本配置文件
├── data/
│   ├── hkex_options/
│   │   ├── HSI_TECH_latest.csv         # 最新數據
│   │   ├── HSI_TECH_2025-10-17.csv     # 歷史數據
│   │   ├── HSI_TECH_2025-10-16.csv
│   │   └── ...
│   ├── backup/
│   │   └── hkex_options/
│   │       ├── HSI_TECH_latest.json.gz
│   │       └── ...
│   └── hkex_options.db                 # SQLite 數據庫
├── logs/
│   └── hkex_options_crawler.log        # 爬取日誌
└── scripts/
    ├── auto_crawler.py                 # 自動爬取腳本
    ├── data_validator.py               # 數據驗證腳本
    └── scheduler.py                    # 計劃調度器
```

---

## 數據格式示例

### CSV 格式
```csv
trading_date,call_volume,put_volume,total_volume,call_oi,put_oi,total_oi,sentiment
2025-10-17,5678,6588,12266,41716,74202,115918,bearish
2025-10-16,1402,1406,2808,40983,75329,116312,neutral
2025-10-15,2136,4116,6252,40036,74270,114306,bearish
```

### JSON 格式
```json
{
  "options_id": "HSI_TECH",
  "name_zh": "恒生科技指數期權",
  "data": [
    {
      "trading_date": "2025-10-17",
      "trading_volume": {
        "call": 5678,
        "put": 6588,
        "total": 12266
      },
      "open_interest": {
        "call": 41716,
        "put": 74202,
        "total": 115918
      },
      "metrics": {
        "put_call_ratio": 1.16,
        "trading_oi_ratio": 0.106,
        "sentiment": "bearish"
      }
    }
  ],
  "metadata": {
    "crawl_date": "2025-10-18",
    "records": 238,
    "date_range": "2025-09-01 to 2025-10-17"
  }
}
```

### SQLite Schema
```sql
CREATE TABLE hkex_options_daily (
  id INTEGER PRIMARY KEY,
  options_id TEXT NOT NULL,
  trading_date DATE NOT NULL,
  call_volume INTEGER,
  put_volume INTEGER,
  total_volume INTEGER,
  call_oi INTEGER,
  put_oi INTEGER,
  total_oi INTEGER,
  put_call_ratio REAL,
  trading_oi_ratio REAL,
  sentiment TEXT,
  crawl_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(options_id, trading_date)
);

CREATE INDEX idx_options_date ON hkex_options_daily(options_id, trading_date);
CREATE INDEX idx_trading_date ON hkex_options_daily(trading_date);
```

---

## 擴展指南

### 添加新期權類別步驟：

1. **識別期權頁面**
   - 在HKEX網站找到期權類別
   - 記錄URL和選擇器

2. **更新配置文件**
   - 在 `options_templates` 中添加新類別
   - 配置 `selectors` 和 `validation` 規則

3. **測試爬取**
   - 手動測試一次爬取
   - 驗證數據完整性

4. **納入自動化**
   - 添加到 `daily_schedule`
   - 設置爬取頻率和優先級

---

## 版本歷史

```
v1.0 (2025-10-18)
- Initial release
- HSI_TECH options data: 238 records
- Configuration framework established
- 5 additional options classes planned
```

---

**狀態**: ✅ Active
**維護者**: Auto Crawler System
**最後更新**: 2025-10-18 16:30 HKT
**下次更新**: 2025-10-19 16:15 HKT

