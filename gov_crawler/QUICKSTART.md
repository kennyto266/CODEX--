# GOV 爬蟲 - 快速開始指南

## 安裝步驟

### 1. 創建虛擬環境
```bash
cd gov_crawler
python -m venv .venv
.venv\Scripts\activate  # Windows
# 或
source .venv/bin/activate  # Linux/Mac
```

### 2. 安裝依賴
```bash
pip install -r requirements.txt
```

### 3. 驗證安裝
```bash
python main_crawler.py --help
```

## 基本使用

### 運行所有爬蟲
```bash
python main_crawler.py
```

這將爬取所有啟用的數據集並保存到 `data/` 目錄。

### 運行特定數據集爬蟲

#### 財經數據
```bash
python main_crawler.py --dataset finance
```
爬取 GDP、政府財務等經濟指標數據。

#### 物業市場數據
```bash
python main_crawler.py --dataset property
```
爬取房屋銷售、租金、交易量等數據。

#### 零售業數據
```bash
python main_crawler.py --dataset retail
```
爬取零售銷售額等商業指標。

#### 交通數據
```bash
python main_crawler.py --dataset traffic
```
爬取交通流量和運輸相關數據。

## 高級操作

### 查看存儲統計
```bash
python main_crawler.py --stats
```

查看已下載的數據大小、數量等統計信息。

### 清理過期數據
```bash
python main_crawler.py --cleanup
```

存檔30天以上的舊數據，刪除90天以上的數據。

### 使用自定義配置
```bash
python main_crawler.py --config custom_config.yaml
```

## 數據輸出結構

```
data/
├── raw/              # 原始 JSON 數據
│   ├── gdp_*.json
│   ├── property_market_*.json
│   ├── retail_sales_*.json
│   └── traffic_*.json
│
├── processed/        # 處理後的數據
│   ├── gdp_*.csv
│   ├── gdp_*.json
│   ├── property_market_*.csv
│   ├── property_market_*.json
│   ├── retail_sales_*.csv
│   ├── retail_sales_*.json
│   ├── traffic_*.csv
│   └── traffic_*.json
│
├── metadata/         # 數據元信息
│   ├── gdp_metadata.json
│   ├── property_market_metadata.json
│   ├── retail_sales_metadata.json
│   └── traffic_metadata.json
│
└── archive/          # 存檔的舊數據
```

## 配置文件說明

### 啟用/禁用特定爬蟲

編輯 `config.yaml`，修改各數據集的 `enabled` 字段：

```yaml
datasets:
  finance:
    enabled: true      # 啟用財經爬蟲

  real_estate:
    enabled: false     # 禁用房產爬蟲
```

### 調整更新間隔

單位：秒

```yaml
datasets:
  finance:
    update_interval: 86400    # 每24小時更新一次

  real_estate:
    update_interval: 604800   # 每7天更新一次
```

## 常見問題

### Q: 數據下載很慢？
A: 這可能是由於網絡連接問題或政府API響應慢。可以嘗試：
1. 檢查網絡連接
2. 等待數分鐘後重試
3. 檢查政府網站是否可訪問

### Q: 如何集成到量化交易系統？
A: 數據保存在 `data/processed/` 目錄中，可直接使用 pandas 加載：
```python
import pandas as pd

# 加載最新的 GDP 數據
df = pd.read_csv('data/processed/gdp_*.csv')
```

### Q: 如何自動定期運行爬蟲？

#### Windows 計劃任務
1. 打開任務計劃程序
2. 創建基本任務
3. 設置觸發器（每日/每週）
4. 設置操作為：`python main_crawler.py`

#### Linux/Mac (cron)
```bash
# 編輯 crontab
crontab -e

# 每天凌晨2點運行爬蟲
0 2 * * * cd /path/to/gov_crawler && python main_crawler.py >> logs/cron.log 2>&1
```

## 運行測試

```bash
cd tests
python test_crawler.py
```

## 日誌查看

主日誌文件位於 `logs/crawler.log`，可實時查看爬蟲操作記錄。

## 與量化交易系統集成

### 基本整合方式

```python
import sys
from pathlib import Path

# 添加 GOV 爬蟲路徑
sys.path.insert(0, str(Path(__file__).parent / 'gov_crawler'))

from gov_crawler.main_crawler import GovCrawler

# 初始化爬蟲
crawler = GovCrawler('gov_crawler/config.yaml')

# 爬取特定數據
crawler.crawl_finance_data()
crawler.crawl_property_data()

# 加載處理後的數據
import pandas as pd

gdp_data = pd.read_csv('gov_crawler/data/processed/gdp_*.csv')
property_data = pd.read_csv('gov_crawler/data/processed/property_market_*.csv')

# 用於策略開發
print(f"GDP 數據行數: {len(gdp_data)}")
print(f"房產數據行數: {len(property_data)}")
```

## 支持和反饋

遇到問題或有建議？請查看 `logs/` 目錄中的日誌文件以診斷問題。

---

更詳細的文檔請參考 README.md
