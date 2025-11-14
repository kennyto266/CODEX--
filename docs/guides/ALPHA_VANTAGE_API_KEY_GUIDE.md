# Alpha Vantage API 免費密鑰申請指南

## 📋 概述

**Alpha Vantage** 提供免費的金融市場數據API，包括：
- 股票價格和技術指標
- 外匯匯率數據
- 加密貨幣數據
- 經濟指標
- 基金和期貨數據

**免費版限制**:
- 每日500次請求
- 每分鐘最多5次請求
- 僅支持基本數據類型

## 🚀 申請步驟 (僅需20秒)

### Step 1: 訪問申請頁面
打開瀏覽器，訪問：
```
https://www.alphavantage.co/support/#api-key
```

### Step 2: 填寫信息
在申請表單中填寫：
- **Email地址**: 使用有效的郵箱地址
- **使用目的**: 填寫 "Quantitative trading research"
- **公司/組織**: 可選，填寫 "Personal Project"

### Step 3: 提交申請
點擊 **"Get Free API Key"** 按鈕

### Step 4: 檢查郵箱
申請提交後，檢查您的郵箱：
- 收件箱中會收到確認郵件
- 郵件包含您的API密鑰
- 格式類似: `abcd1234efgh5678ijkl9012mnop3456`

### Step 5: 保存密鑰
**重要**: 保存好API密鑰，用於後續配置

## 🔑 配置API密鑰

### 方法1: 環境變量 (推薦)
```bash
# Linux/Mac
export ALPHAVANTAGE_API_KEY=your_api_key_here

# Windows
set ALPHAVANTAGE_API_KEY=your_api_key_here
```

### 方法2: 配置文件
在項目根目錄創建 `.env` 文件：
```bash
# .env 文件
ALPHAVANTAGE_API_KEY=your_api_key_here
```

## 📊 可用的數據類型

### 1. 外匯數據 (FX)
```python
# 示例: 獲取 USD/HKD 匯率
import requests

url = "https://www.alphavantage.co/query"
params = {
    "function": "CURRENCY_EXCHANGE_RATE",
    "from_currency": "USD",
    "to_currency": "HKD",
    "apikey": "YOUR_API_KEY"
}

response = requests.get(url, params=params)
data = response.json()
```

### 2. 股票數據 (Time Series)
```python
# 示例: 獲取騰訊 (0700.HK) 股價
params = {
    "function": "TIME_SERIES_DAILY",
    "symbol": "0700.HK",
    "apikey": "YOUR_API_KEY"
}
```

### 3. 技術指標
```python
# 示例: 計算 RSI
params = {
    "function": "RSI",
    "symbol": "0700.HK",
    "interval": "daily",
    "time_period": 14,
    "series_type": "close",
    "apikey": "YOUR_API_KEY"
}
```

## 🔧 在項目中集成

### 1. 創建AlphaVantageAdapter
```python
# src/data_adapters/alpha_vantage_adapter.py
import os
import aiohttp
import asyncio
from datetime import datetime, timedelta
import pandas as pd

class AlphaVantageAdapter:
    def __init__(self):
        self.api_key = os.getenv('ALPHAVANTAGE_API_KEY')
        if not self.api_key:
            raise ValueError("請設置 ALPHAVANTAGE_API_KEY 環境變量")

        self.base_url = "https://www.alphavantage.co/query"
        self.session = None

    async def fetch_fx_rate(self, from_currency: str, to_currency: str) -> float:
        """獲取外匯匯率"""
        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": from_currency,
            "to_currency": to_currency,
            "apikey": self.api_key
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, params=params) as response:
                data = await response.json()

                # 解析響應
                key = f"Realtime Currency Exchange Rate"
                if key in data:
                    rate = float(data[key]["5. Exchange Rate"])
                    return rate
                else:
                    raise Exception("無法獲取匯率數據")
```

### 2. 在宏觀指標服務中註冊
```python
# src/services/indicators/macro_indicator_service.py
# 在 get_latest_indicators() 方法中添加:
from src.data_adapters.alpha_vantage_adapter import AlphaVantageAdapter

# ...其他代碼...

# 添加匯率指標
try:
    fx_adapter = AlphaVantageAdapter()
    usd_hkd_rate = await fx_adapter.fetch_fx_rate("USD", "HKD")
    indicators.append({
        "name": "usd_hkd_rate",
        "value": usd_hkd_rate,
        "category": "fx",
        "source": "Alpha Vantage",
        "is_real_data": True
    })
except Exception as e:
    logger.warning(f"無法獲取USD/HKD匯率: {e}")
```

## ⚠️ 注意事項

### 1. 請求限制
- **免費版**: 每日500次，每分鐘5次
- **建議**: 實現緩存機制，避免重複請求
- **監控**: 跟蹤剩餘請求數量

### 2. 數據質量
- 延遲: 可能有15-20分鐘延遲
- 準確性: 來自多個數據源聚合
- 覆蓋: 主要市場較完整

### 3. 錯誤處理
```python
# 處理常見錯誤
try:
    rate = await fx_adapter.fetch_fx_rate("USD", "HKD")
except Exception as e:
    if "rate limit" in str(e).lower():
        print("API請求超限，請稍後重試")
    elif "invalid" in str(e).lower():
        print("API密鑰無效")
    else:
        print(f"其他錯誤: {e}")
```

## 🧪 測試API密鑰

### 快速測試腳本
```python
# test_alpha_vantage.py
import asyncio
import aiohttp

async def test():
    api_key = input("請輸入您的Alpha Vantage API密鑰: ")

    url = "https://www.alphavantage.co/query"
    params = {
        "function": "CURRENCY_EXCHANGE_RATE",
        "from_currency": "USD",
        "to_currency": "HKD",
        "apikey": api_key
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            data = await response.json()

            if "Error Message" in data:
                print(f"[ERROR] API錯誤: {data['Error Message']}")
            else:
                print("[OK] API密鑰有效!")
                print(f"USD/HKD匯率: {data['Realtime Currency Exchange Rate']['5. Exchange Rate']}")

asyncio.run(test())
```

## 🔄 升級選項

### 付費版功能
- 更多API請求
- 更快的數據更新
- 更多數據類型
- 技術支持

### 申請付費版
訪問: https://www.alphavantage.co/support/#paid

## ❓ 常見問題

### Q: 申請後多久生效？
A: 立即生效，無需等待

### Q: 可以更換API密鑰嗎？
A: 可以，每個郵箱可以申請多個密鑰

### Q: 數據覆蓋哪些市場？
A: 全球主要市場，包括港股、美股、A股等

### Q: 如何查看剩餘請求數？
A: API響應中不直接顯示，需要自己記錄

## 📞 技術支持

### 文檔
- 官方文檔: https://www.alphavantage.co/documentation/
- 示例代碼: https://github.com/AlphaVantage

### 社區
- 論壇: https://www.alphavantage.co/forum/
- GitHub: https://github.com/AlphaVantage

### 聯繫
- 郵箱: support@alphavantage.co

---

**申請時間**: 20秒
**生效時間**: 即時
**維護成本**: 極低
**數據質量**: 高

**立即行動**: https://www.alphavantage.co/support/#api-key
