# GOV 爬蟲項目結構

## 完整目錄樹

```
gov_crawler/
│
├── README.md                      # 項目概述和說明文檔
├── QUICKSTART.md                  # 快速開始指南
├── INTEGRATION_GUIDE.md           # 與量化系統集成指南
├── PROJECT_STRUCTURE.md           # 本文件
│
├── requirements.txt               # 項目依賴列表
├── config.yaml                    # 爬蟲配置文件
│
├── main_crawler.py               # 主爬蟲程序入口
│
├── src/                          # 源代碼包
│   ├── __init__.py               # 包初始化文件
│   ├── utils.py                  # 工具函數模塊
│   ├── api_handler.py            # API 處理模塊
│   ├── data_processor.py         # 數據處理模塊
│   └── storage_manager.py        # 存儲管理模塊
│
├── tests/                        # 測試模塊
│   ├── __init__.py
│   └── test_crawler.py           # 單元測試文件
│
├── data/                         # 數據存儲目錄
│   ├── raw/                      # 原始數據（JSON 格式）
│   │   ├── gdp_20241021_120000.json
│   │   ├── property_market_20241021_120000.json
│   │   ├── retail_sales_20241021_120000.json
│   │   └── traffic_20241021_120000.json
│   │
│   ├── processed/                # 處理後的數據（CSV/JSON 格式）
│   │   ├── gdp_20241021_120000.csv
│   │   ├── gdp_20241021_120000.json
│   │   ├── property_market_20241021_120000.csv
│   │   ├── property_market_20241021_120000.json
│   │   ├── retail_sales_20241021_120000.csv
│   │   ├── retail_sales_20241021_120000.json
│   │   ├── traffic_20241021_120000.csv
│   │   └── traffic_20241021_120000.json
│   │
│   ├── metadata/                 # 數據元信息
│   │   ├── gdp_metadata.json
│   │   ├── property_market_metadata.json
│   │   ├── retail_sales_metadata.json
│   │   └── traffic_metadata.json
│   │
│   └── archive/                  # 存檔的舊數據
│       └── ...（超過 30 天的舊數據）
│
└── logs/                         # 日誌文件
    └── crawler.log               # 主爬蟲日誌
```

## 模塊說明

### 核心模塊

#### 1. `main_crawler.py` - 主爬蟲程序
**功能**: 爬蟲的入口點和調度器
**主要類**: `GovCrawler`
**主要方法**:
- `crawl_finance_data()` - 爬取財經數據
- `crawl_property_data()` - 爬取房產數據
- `crawl_retail_data()` - 爬取零售業數據
- `crawl_traffic_data()` - 爬取交通數據
- `crawl_all()` - 爬取所有數據
- `show_statistics()` - 顯示統計信息
- `cleanup()` - 清理過期數據

#### 2. `src/api_handler.py` - API 處理模塊
**功能**: 與香港政府開放數據 API 交互
**主要類**: `DataGovHKAPI`
**主要方法**:
- `fetch_finance_data()` - 獲取財經數據
- `fetch_property_market_data()` - 獲取物業市場數據
- `fetch_retail_sales_data()` - 獲取零售業數據
- `fetch_traffic_data()` - 獲取交通數據
- `fetch_gdp_data()` - 獲取 GDP 數據
- `search_datasets()` - 搜索數據集
- `list_datasets()` - 列出所有數據集

#### 3. `src/data_processor.py` - 數據處理模塊
**功能**: 數據清理、驗證和轉換
**主要類**: `DataProcessor`
**主要方法**:
- `process_finance_data()` - 處理財經數據
- `process_property_data()` - 處理房產數據
- `process_retail_data()` - 處理零售業數據
- `process_traffic_data()` - 處理交通數據
- `validate_data_quality()` - 驗證數據質量
- `calculate_statistics()` - 計算統計數據
- `merge_datasets()` - 合併數據集
- `normalize_columns()` - 標準化列名

#### 4. `src/storage_manager.py` - 存儲管理模塊
**功能**: 數據的保存、加載和管理
**主要類**: `StorageManager`
**主要方法**:
- `save_raw_data()` - 保存原始數據
- `save_processed_data()` - 保存處理後的數據
- `save_metadata()` - 保存元信息
- `load_metadata()` - 加載元信息
- `load_processed_data()` - 加載處理後的數據
- `list_files()` - 列出文件
- `get_storage_stats()` - 獲取存儲統計
- `archive_old_data()` - 存檔舊數據
- `cleanup_old_data()` - 清理舊數據

#### 5. `src/utils.py` - 工具函數模塊
**功能**: 通用工具函數
**主要函數**:
- `load_config()` - 加載配置文件
- `setup_logging()` - 設置日誌系統
- `create_directories()` - 創建目錄
- `save_json()` - 保存 JSON 文件
- `load_json()` - 加載 JSON 文件
- `validate_dataset_config()` - 驗證數據集配置

**主要類**:
- `ProgressTracker` - 進度跟蹤器

## 數據流

### 爬取流程
```
API 請求 → API 響應 → 原始數據存儲
           ↓
         數據處理 → 驗證 → 轉換 → 標準化
           ↓
      處理後數據存儲 → 元信息存儲
```

### 文件命名規則
- **原始數據**: `{dataset_name}_{timestamp}.json`
  - 例: `gdp_20241021_120000.json`
- **處理數據**: `{dataset_name}_{timestamp}.{format}`
  - 例: `gdp_20241021_120000.csv`
- **元信息**: `{dataset_name}_metadata.json`
  - 例: `gdp_metadata.json`

## 配置文件詳解

### config.yaml 結構

```yaml
crawler:
  base_url: "https://data.gov.hk/tc-data/dataset"  # 基礎 URL
  timeout: 30                                       # 超時時間（秒）
  retry_count: 3                                    # 重試次數
  log_level: "INFO"                                 # 日誌級別

datasets:
  finance:                                          # 財經數據配置
    enabled: true                                   # 是否啟用
    update_interval: 86400                          # 更新間隔（秒）
    api_endpoints: {...}                            # API 端點
    params: {...}                                   # API 參數

storage:
  raw_data_dir: "data/raw"                          # 原始數據目錄
  processed_data_dir: "data/processed"              # 處理數據目錄
  metadata_dir: "data/metadata"                     # 元信息目錄
  archive_dir: "data/archive"                       # 存檔目錄
```

## 測試框架

### 測試模塊 (`tests/test_crawler.py`)

**測試類**:
1. `TestUtils` - 工具函數測試
2. `TestDataProcessor` - 數據處理測試
3. `TestStorageManager` - 存儲管理測試

**測試覆蓋範圍**:
- 配置加載
- 進度跟蹤
- 數據清理
- 統計計算
- 數據驗證
- 文件存儲/加載
- 元信息管理

## 依賴包

### requirements.txt

```
requests==2.31.0              # HTTP 請求庫
beautifulsoup4==4.12.2        # HTML 解析
pandas==2.0.3                 # 數據處理
pyyaml==6.0.1                 # YAML 配置
python-dateutil==2.8.2        # 日期處理
urllib3==2.0.7                # HTTP 客戶端
lxml==4.9.3                   # XML 處理
aiohttp==3.9.0                # 異步 HTTP 客戶端
tenacity==8.2.3               # 重試機制
```

## 使用場景

### 場景 1: 完整爬蟲周期
```bash
python main_crawler.py
```
爬取所有啟用的數據集 → 處理 → 保存 → 顯示統計

### 場景 2: 單個數據集爬蟲
```bash
python main_crawler.py --dataset finance
```
只爬取財經數據

### 場景 3: 定期自動更新
配置 cron 任務或 Windows 計劃任務定期運行

### 場景 4: 與量化系統集成
在量化系統中導入 `GovDataAdapter`，直接從 `data/processed/` 讀取數據

## 性能指標

### 典型爬取時間
- 全量爬蟲: ~30-60 秒
- 單個數據集: ~5-15 秒
- 數據處理: ~2-5 秒

### 存儲需求
- 單月數據: ~50-100 MB
- 年度數據: ~0.5-1 GB
- 推薦保留期: 90 天

## 安全性考慮

1. **API 調用限制**: 已內置重試機制和超時控制
2. **數據驗證**: 所有數據都經過質量檢查
3. **錯誤處理**: 完善的異常捕獲和日誌記錄
4. **數據隱私**: 所有存儲都是本地的

## 擴展性

### 添加新數據源
1. 在 `config.yaml` 中添加新數據集配置
2. 在 `api_handler.py` 中添加 fetch 方法
3. 在 `data_processor.py` 中添加 process 方法
4. 在 `main_crawler.py` 中添加 crawl 方法

### 添加新處理邏輯
直接在 `data_processor.py` 中擴展 `DataProcessor` 類

## 故障排除

### 日誌位置
所有日誌都保存在 `logs/crawler.log`

### 常見問題
1. **連接超時**: 檢查網絡連接，增加 timeout 值
2. **數據缺失**: 檢查 API 是否可用，查看日誌
3. **存儲滿**: 運行 `cleanup` 清理舊數據

---

**最後更新**: 2024-10-21
**版本**: 1.0.0
