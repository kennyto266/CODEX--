# GOV 爬蟲系統 (GOV Crawler System)

香港政府開放數據爬蟲系統，用於為量化交易項目收集替代數據。

## 功能特性

- **自動數據下載** - 從香港政府開放數據平台爬取多個數據集
- **多數據源支持** - 財經、地產、工商業、交通等數據
- **API 集成** - 支持直接 API 調用和數據解析
- **數據存儲** - 本地 CSV/JSON 存儲
- **定時更新** - 支持自動定時更新機制
- **數據驗證** - 內置數據質量檢查

## 項目結構

```
gov_crawler/
├── README.md
├── requirements.txt
├── config.yaml
├── main_crawler.py
├── src/
│   ├── __init__.py
│   ├── api_handler.py
│   ├── data_processor.py
│   ├── storage_manager.py
│   └── utils.py
├── data/
│   ├── raw/
│   ├── processed/
│   └── metadata/
├── logs/
└── tests/
    └── test_crawler.py
```

## 安裝

```bash
# 創建虛擬環境
python -m venv .venv
.venv\Scripts\activate  # Windows

# 安裝依賴
pip install -r requirements.txt
```

## 快速開始

```bash
# 運行爬蟲
python main_crawler.py

# 運行特定數據集爬蟲
python main_crawler.py --dataset finance

# 查看幫助
python main_crawler.py --help
```

## 支持的數據集

### 1. 財經數據 (Finance)
- 香港銀行同業拆息 (HIBOR)
- 本地生產總值 (GDP)
- 政府財務狀況數據

### 2. 地產數據 (Real Estate)
- 物業市場統計資料
- 房屋交易記錄
- 樓宇信息

### 3. 工商業數據 (Business)
- 零售業銷貨額統計
- 酒店入住率
- 商業數據

### 4. 地理數據 (Geography)
- 地形圖
- 建築物資料
- 土地用途統計

### 5. 運輸數據 (Transport)
- 交通流量統計
- 港鐵實時數據
- 巴士實時數據

## 配置

編輯 `config.yaml` 配置爬蟲參數：

```yaml
crawler:
  base_url: "https://data.gov.hk/tc-data/dataset"
  timeout: 30
  retry_count: 3
  log_level: "INFO"

datasets:
  finance:
    enabled: true
    update_interval: 86400  # 每天更新

  real_estate:
    enabled: true
    update_interval: 604800  # 每週更新
```

## 數據輸出

爬取的數據存儲在 `data/` 目錄中：

- **raw/** - 原始數據（JSON/CSV格式）
- **processed/** - 處理後的數據（統一格式）
- **metadata/** - 數據元信息和更新記錄

## 日誌

日誌文件位於 `logs/` 目錄，記錄所有爬蟲活動和錯誤。

## 與量化交易系統集成

數據可直接集成到 `src/data_adapters/` 作為替代數據源使用。

## 許可証

MIT License
