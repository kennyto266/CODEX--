# LIHKG 財經台爬蟲與散戶情緒分析

## 概述

LIHKG 財經台爬蟲系統，用於爬取 LIHKG 討論區的財經討論內容，並進行情緒分析。支援爬取股票板塊 (category/2) 和期貨板塊 (category/15)，提取散戶情緒指標和熱門股票資訊。

## 功能特性

- **LIHKG 爬取**: 支援爬取財經台股票和期貨板塊
- **情緒分析**: 基於中文關鍵詞的情緒分析
- **股票代碼識別**: 自動識別討論中的股票代碼 (XXXX.HK)
- **數據存儲**: SQLite 資料庫持久化存儲
- **API 服務**: FastAPI 提供 RESTful API
- **Chrome MCP 整合**: 支援瀏覽器自動化

## 目錄結構

```
lihkg_scraper/
├── core/                  # 核心模塊
│   ├── chrome_controller.py  # Chrome MCP 控制器
│   ├── scraper.py            # 爬蟲引擎
│   ├── parser.py             # 帖子解析器
│   ├── sentiment.py          # 情緒分析
│   └── storage.py            # 數據存儲
├── api/                    # API 模塊
│   ├── __init__.py
│   └── routes.py             # API 路由
├── data/                   # 數據目錄
├── logs/                   # 日誌目錄
├── tests/                  # 測試文件
├── main.py                 # 主程序
├── run_api.py              # API 啟動腳本
└── README.md               # 說明文檔
```

## 安裝依賴

```bash
pip install fastapi uvicorn sqlite3 asyncio logging
```

## 使用方法

### 1. 運行爬蟲

```bash
cd lihkg_scraper
python main.py
```

這將會：
- 爬取股票板塊 (category/2) 前 5 頁
- 爬取期貨板塊 (category/15) 前 5 頁
- 進行情緒分析
- 保存到 SQLite 資料庫

### 2. 啟動 API 服務

```bash
python run_api.py
```

API 服務將在 http://localhost:8000 啟動

### 3. API 端點

#### 獲取帖子列表
```
GET /api/lihkg/posts?category=2&limit=100
```

#### 獲取情緒分析
```
GET /api/lihkg/sentiment?category=2&days=7
```

#### 獲取熱門股票
```
GET /api/lihkg/stocks?category=2&days=7&limit=20
```

#### 獲取特定股票討論
```
GET /api/lihkg/stock/0700.HK?days=7
```

#### 獲取統計數據
```
GET /api/lihkg/statistics
```

#### API 文檔
訪問 http://localhost:8000/docs 查看完整的 API 文檔

## 數據結構

### 帖子數據
```json
{
  "post_id": "帖子唯一 ID",
  "category": 2,
  "title": "帖子標題",
  "content": "帖子內容摘要",
  "author": "發帖者",
  "replies": 25,
  "views": 1520,
  "likes": 10,
  "post_time": "2025-10-27T19:30:00",
  "tags": ["討論"],
  "sentiment_score": 0.5,
  "sentiment_label": "positive",
  "stock_mentions": ["0700.HK", "0388.HK"],
  "created_at": "2025-10-27T19:35:00"
}
```

### 情緒分析結果
```json
{
  "sentiment_score": 0.5,
  "sentiment_label": "positive",
  "confidence": 0.8,
  "intensity": 0.6,
  "positive_words": ["漲", "看好"],
  "negative_words": [],
  "analyzed_at": "2025-10-27T19:35:00"
}
```

## Chrome MCP 整合

### 測試 Chrome MCP 功能

```python
from core.chrome_controller import LIHKGChromeController

async def test_chrome():
    controller = LIHKGChromeController()
    await controller.initialize()
    await controller.navigate_to_category(2)
    posts = await controller.extract_post_list()
    await controller.close()
```

### Chrome MCP 功能

1. **頁面導航**: 自動導航到指定板塊
2. **元素定位**: 自動檢測頁面元素和 CSS 選擇器
3. **動態內容**: 處理 JavaScript 動態載入
4. **錯誤檢測**: 自動檢測頁面結構變化

## 情緒分析

### 分析原理

1. **關鍵詞匹配**: 使用中文情緒關鍵詞庫
2. **情緒強度**: 基於回復數、查看數、點贊數計算
3. **情緒分數**: -1 (負面) 到 1 (正面)

### 情緒分類

- **positive**: 正向情緒 (分數 > 0)
- **negative**: 負向情緒 (分數 < 0)
- **neutral**: 中性情緒 (分數 = 0)

## 股票代碼識別

### 識別規則

- 格式: XXXX.HK (4 位數字 + .HK)
- 匹配範圍: 標題和內容
- 統計: 計算被提及次數和情緒

### 示例

輸入: "討論 0700.HK 騰訊的表現"
輸出: ["0700.HK"]

## 配置參數

### 爬蟲配置

```python
# 爬取頁數
max_pages = 10

# 速率限制 (每分鐘請求數)
requests_per_minute = 60

# 資料庫路徑
db_path = 'data/lihkg.db'
```

### API 配置

```python
# 服務器配置
host = "0.0.0.0"
port = 8000

# 請求限制
max_limit = 1000
default_limit = 100
```

## 日誌

日誌文件位置: `logs/lihkg_scraper.log`

日誌級別:
- INFO: 一般信息
- WARNING: 警告信息
- ERROR: 錯誤信息
- DEBUG: 調試信息

## 注意事項

1. **合規性**: 僅用於學術研究和內部分析
2. **速率限制**: 避免過於頻繁的請求
3. **數據隱私**: 不存儲個人身份信息
4. **版權聲明**: 帖子內容受版權保護

## 故障排除

### 常見問題

1. **Chrome 驅動問題**
   - 確保已安裝 Chrome 瀏覽器
   - 檢查 Chrome MCP 連接

2. **數據庫錯誤**
   - 確保 `data/` 目錄存在
   - 檢查資料庫文件權限

3. **API 連接失敗**
   - 檢查端口是否被佔用
   - 確認防火牆設置

## 技術棧

- **Python 3.10+**: 主要編程語言
- **FastAPI**: Web API 框架
- **SQLite**: 數據庫
- **Chrome DevTools MCP**: 瀏覽器自動化
- **Asyncio**: 異步編程
- **Logging**: 日誌記錄

## 作者

**Claude Code**  
創建日期: 2025-10-27  
版本: 1.0.0

## 許可證

本項目僅用於學術研究和教育目的。使用者需自行承擔使用風險，並遵守相關網站的服務條款。
