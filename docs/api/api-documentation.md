# API文檔 - 港股量化交易系統

## 概述

系統提供完整的RESTful API和WebSocket接口，支持量化交易的所有功能。

## RESTful API端點

### 基礎信息
- 基礎URL: http://localhost:8001
- API版本: v1
- 格式: JSON
- 認證: API Key

### 主要端點

#### 1. 市場數據 API

**獲取歷史數據**


**獲取實時數據**


#### 2. 策略 API

**獲取所有策略**


**創建策略**


**執行策略回測**


#### 3. Agent API

**列出所有Agent**


**獲取Agent狀態**


**啟動Agent**


**停止Agent**


#### 4. 回測 API

**提交回測任務**


**獲取回測結果**


**獲取回測列表**


#### 5. 性能 API

**獲取策略性能**


**獲取投資組合性能**


**獲取風險指標**


## WebSocket API

### 連接


### 支持的事件

#### 客戶端發送
- subscribe_market_data: 訂閱市場數據
- subscribe_signals: 訂閱交易信號
- subscribe_agents: 訂閱Agent狀態

#### 服務端推送
- market_data_update: 市場數據更新
- trading_signal: 交易信號
- agent_status_update: Agent狀態更新
- backtest_progress: 回測進度
- error_alert: 錯誤告警

### WebSocket示例



## 數據格式

### 市場數據


### 交易信號


### 回測結果


## 錯誤處理

### 錯誤碼
- 400: 請求參數錯誤
- 401: 未授權
- 403: 禁止訪問
- 404: 資源不存在
- 429: 請求過於頻繁
- 500: 服務器內部錯誤

### 錯誤響應格式


## 認證

### API Key認證

在請求頭中包含API Key：



或在查詢參數中：



## 限制

### 請求頻率限制
- 默認: 100 requests/minute
- 實時數據: 60 requests/minute
- 回測: 10 requests/minute

### 分頁


## SDK

### Python SDK



最後更新: 2025-11-03
